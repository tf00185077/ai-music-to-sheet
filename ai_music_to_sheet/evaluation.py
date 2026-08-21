from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, List, Optional

from .arrangement import score_arrangement_quality
from .contracts import FAIL, PASS, PIPELINE_VERSION, REVIEW, normalized_notes, utc_now, write_json
from .timing import BEATS_PER_MEASURE, DURATION_TOLERANCE_BEATS, DURATION_VOCABULARY


ONSET_TOLERANCE_SECONDS = 0.12
OFFSET_TOLERANCE_SECONDS = 0.12
DURATION_TOLERANCE_SECONDS = 0.12
PASS_THRESHOLD = 0.95
REVIEW_THRESHOLD = 0.80


def score_notes_against_reference(
    *,
    predicted_notes: Iterable[Dict[str, object]],
    reference_notes: Iterable[Dict[str, object]],
    case_name: str,
    artifact_versions: Dict[str, object],
    score_ir: Optional[Dict[str, object]] = None,
    time_map: Optional[Dict[str, object]] = None,
    arranged_score: Optional[Dict[str, object]] = None,
    musicxml_summary: Optional[Dict[str, object]] = None,
) -> Dict[str, object]:
    predicted_source = list(predicted_notes)
    reference_source = list(reference_notes)
    predicted = normalized_notes(predicted_source)
    reference = normalized_notes(reference_source)
    denominator = max(len(reference), 1)
    paired = list(zip(predicted, reference))

    pitch_matches = 0
    onset_matches = 0
    duration_matches = 0
    offset_matches = 0
    exact_matches = 0
    for predicted_note, reference_note in paired:
        pitch_ok = predicted_note["pitch"] == reference_note["pitch"]
        onset_ok = abs(predicted_note["onset"] - reference_note["onset"]) <= ONSET_TOLERANCE_SECONDS
        duration_ok = (
            abs(predicted_note["duration"] - reference_note["duration"]) <= DURATION_TOLERANCE_SECONDS
            and abs(predicted_note["offset"] - reference_note["offset"]) <= OFFSET_TOLERANCE_SECONDS
        )
        offset_ok = abs(predicted_note["offset"] - reference_note["offset"]) <= OFFSET_TOLERANCE_SECONDS

        pitch_matches += int(pitch_ok)
        onset_matches += int(pitch_ok and onset_ok)
        duration_matches += int(pitch_ok and duration_ok)
        offset_matches += int(pitch_ok and offset_ok)
        exact_matches += int(pitch_ok and onset_ok and duration_ok and offset_ok)

    metrics = {
        "reference_notes": len(reference),
        "predicted_notes": len(predicted),
        "matched_notes": exact_matches,
        "pitch_accuracy": round(pitch_matches / denominator, 6),
        "onset_accuracy": round(onset_matches / denominator, 6),
        "duration_accuracy": round(duration_matches / denominator, 6),
        "offset_accuracy": round(offset_matches / denominator, 6),
        "onset_tolerance_seconds": ONSET_TOLERANCE_SECONDS,
        "duration_tolerance_seconds": DURATION_TOLERANCE_SECONDS,
        "offset_tolerance_seconds": OFFSET_TOLERANCE_SECONDS,
    }
    if score_ir is not None and time_map is not None:
        metrics.update(_timing_metrics(score_ir, reference_source, time_map))
    status = _status_for_metrics(metrics)
    arrangement_report = None
    if arranged_score is not None and score_ir is not None and musicxml_summary is not None:
        arrangement_report = score_arrangement_quality(
            arranged_score=arranged_score,
            source_score_ir=score_ir,
            musicxml_summary=musicxml_summary,
        )
        status = _worst_status([status, arrangement_report["status"]])
    report = {
        "schema_version": "evaluation-case/v1",
        "generator_version": PIPELINE_VERSION,
        "created_at": utc_now(),
        "case_name": case_name,
        "status": status,
        "metrics": metrics,
        "artifact_versions": artifact_versions,
    }
    if arrangement_report is not None:
        report["arrangement"] = arrangement_report
    return report


def build_runtime_validation_report(
    *,
    case_name: str,
    artifact_versions: Dict[str, object],
    note_events: Dict[str, object],
    score_ir: Dict[str, object],
    time_map: Dict[str, object],
    musicxml_summary: Dict[str, object],
    arranged_score: Optional[Dict[str, object]] = None,
) -> Dict[str, object]:
    checks = [
        {
            "name": "note_events_present",
            "status": PASS if note_events.get("notes") else FAIL,
            "message": "NoteEvents artifact contains note events",
        },
        {
            "name": "time_map_traceable",
            "status": PASS if time_map.get("note_mappings") else FAIL,
            "message": "TimeMap cites source note mappings",
        },
        {
            "name": "score_ir_traceable",
            "status": PASS if score_ir.get("parts") else FAIL,
            "message": "ScoreIR contains a single melody part",
        },
        {
            "name": "musicxml_parseback",
            "status": PASS if musicxml_summary.get("note_count") else FAIL,
            "message": "MusicXML exporter parsed the written score artifact",
        },
    ]
    arrangement_report = None
    if arranged_score is not None:
        arrangement_report = score_arrangement_quality(
            arranged_score=arranged_score,
            source_score_ir=score_ir,
            musicxml_summary=musicxml_summary,
        )
        checks.append(
            {
                "name": "arrangement_runtime_validation",
                "status": arrangement_report["status"],
                "message": "Arranged score fits target range and matches target MusicXML",
            }
        )

    status = _worst_status(check["status"] for check in checks)
    metrics = {
        "note_count": len(note_events.get("notes", [])),
        "score_part_count": len(score_ir.get("parts", [])),
        "musicxml_note_count": int(musicxml_summary.get("note_count") or 0),
        "time_map_note_mappings": len(time_map.get("note_mappings", [])),
        "average_confidence": round(float(note_events.get("average_confidence", 0.0)), 6),
    }
    report = {
        "schema_version": "evaluation-report/v1",
        "generator_version": PIPELINE_VERSION,
        "created_at": utc_now(),
        "case_name": case_name,
        "mode": "runtime_validation",
        "reference_available": False,
        "status": status,
        "metrics": metrics,
        "checks": checks,
        "artifact_versions": artifact_versions,
    }
    if arrangement_report is not None:
        report["arrangement"] = arrangement_report
    return report


def run_evaluation_corpus(cases: List[Dict[str, object]], output_dir: Path) -> Dict[str, object]:
    from .pipeline import process_media_file

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    case_reports = []
    reference_versions = []
    for case in cases:
        case_name = str(case["name"])
        case_dir = output_dir / case_name
        result = process_media_file(
            case["media_path"],
            case_dir,
            reference_notes=case["reference_notes"],
            job_id=f"eval-{case_name}",
            target_profile_id=case.get("target_profile_id"),
        )
        case_report = result["evaluation_report"]
        case_report["case_name"] = case_name
        reference_version = str(case.get("reference_version", "reference-v1"))
        case_report["artifact_versions"]["reference"] = reference_version
        reference_versions.append(reference_version)
        write_json(case_dir / "evaluation_report.json", case_report)
        case_reports.append(case_report)

    overall_status = _worst_status(report["status"] for report in case_reports)
    corpus_report = {
        "schema_version": "evaluation-report/v1",
        "generator_version": PIPELINE_VERSION,
        "created_at": utc_now(),
        "overall_status": overall_status,
        "artifact_versions": {
            "pipeline": PIPELINE_VERSION,
            "reference": sorted(set(reference_versions)),
        },
        "cases": case_reports,
    }
    write_json(output_dir / "evaluation_report.json", corpus_report)
    return corpus_report


def _status_for_metrics(metrics: Dict[str, float]) -> str:
    values = [
        metrics["pitch_accuracy"],
        metrics["onset_accuracy"],
        metrics["duration_accuracy"],
        metrics["offset_accuracy"],
    ]
    if "beat_position_accuracy" in metrics:
        values.append(metrics["beat_position_accuracy"])
    if "notated_duration_accuracy" in metrics:
        values.append(metrics["notated_duration_accuracy"])
    if all(value >= PASS_THRESHOLD for value in values):
        return PASS
    if all(value >= REVIEW_THRESHOLD for value in values):
        return REVIEW
    return FAIL


def _timing_metrics(
    score_ir: Dict[str, object],
    reference_notes: Iterable[Dict[str, object]],
    time_map: Dict[str, object],
) -> Dict[str, float]:
    score_notes = list(score_ir["parts"][0]["notes"])
    reference = list(reference_notes)
    denominator = max(len(reference), 1)
    paired = list(zip(score_notes, reference))
    beat_matches = 0
    duration_matches = 0
    for score_note, reference_note in paired:
        expected_measure, expected_beat = _reference_position(reference_note, time_map)
        expected_duration_beats = _reference_duration_beats(reference_note, time_map)
        expected_duration_name = reference_note.get("notated_duration")
        if expected_duration_name is None:
            expected_duration_name = _duration_name_for_beats(expected_duration_beats)

        same_measure = int(score_note["measure"]) == expected_measure
        beat_ok = abs(float(score_note["beat"]) - expected_beat) <= float(time_map["tolerances"]["beat_position"])
        duration_ok = (
            abs(float(score_note["duration_beats"]) - expected_duration_beats) <= DURATION_TOLERANCE_BEATS
            and str(score_note["notated_duration"]["name"]) == str(expected_duration_name)
        )
        beat_matches += int(same_measure and beat_ok)
        duration_matches += int(duration_ok)

    return {
        "score_ir_notes": len(score_notes),
        "beat_position_accuracy": round(beat_matches / denominator, 6),
        "notated_duration_accuracy": round(duration_matches / denominator, 6),
        "beat_position_tolerance": float(time_map["tolerances"]["beat_position"]),
        "duration_tolerance_beats": DURATION_TOLERANCE_BEATS,
    }


def _reference_position(reference_note: Dict[str, object], time_map: Dict[str, object]):
    if "measure" in reference_note and "beat" in reference_note:
        return int(reference_note["measure"]), float(reference_note["beat"])
    absolute_beat = _reference_absolute_beat(float(reference_note["onset"]), time_map)
    measure = int(absolute_beat // BEATS_PER_MEASURE) + 1
    beat = absolute_beat - ((measure - 1) * BEATS_PER_MEASURE) + 1.0
    return measure, round(beat, 6)


def _reference_duration_beats(reference_note: Dict[str, object], time_map: Dict[str, object]) -> float:
    if "duration_beats" in reference_note:
        return float(reference_note["duration_beats"])
    duration = float(reference_note.get("duration", float(reference_note["offset"]) - float(reference_note["onset"])))
    return round(duration / float(time_map["tempo"]["beat_seconds"]), 6)


def _reference_absolute_beat(seconds: float, time_map: Dict[str, object]) -> float:
    anchor = float(time_map["anchors"][0]["source_seconds"])
    beat_seconds = float(time_map["tempo"]["beat_seconds"])
    return round((seconds - anchor) / beat_seconds, 6)


def _duration_name_for_beats(duration_beats: float) -> str:
    name, _beats = min(DURATION_VOCABULARY, key=lambda item: abs(item[1] - duration_beats))
    return name


def _worst_status(statuses: Iterable[str]) -> str:
    statuses = list(statuses)
    if FAIL in statuses:
        return FAIL
    if REVIEW in statuses:
        return REVIEW
    return PASS
