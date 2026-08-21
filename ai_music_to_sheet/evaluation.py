from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, List

from .contracts import FAIL, PASS, PIPELINE_VERSION, REVIEW, normalized_notes, utc_now, write_json


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
) -> Dict[str, object]:
    predicted = normalized_notes(predicted_notes)
    reference = normalized_notes(reference_notes)
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
    status = _status_for_metrics(metrics)
    return {
        "schema_version": "evaluation-case/v1",
        "generator_version": PIPELINE_VERSION,
        "created_at": utc_now(),
        "case_name": case_name,
        "status": status,
        "metrics": metrics,
        "artifact_versions": artifact_versions,
    }


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
    if all(value >= PASS_THRESHOLD for value in values):
        return PASS
    if all(value >= REVIEW_THRESHOLD for value in values):
        return REVIEW
    return FAIL


def _worst_status(statuses: Iterable[str]) -> str:
    statuses = list(statuses)
    if FAIL in statuses:
        return FAIL
    if REVIEW in statuses:
        return REVIEW
    return PASS
