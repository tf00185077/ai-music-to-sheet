from __future__ import annotations

import math
from typing import Dict, Iterable, List, Tuple

from .contracts import (
    CATEGORY_QUANTIZATION,
    CATEGORY_SCORE_IR_CONTRACT,
    CATEGORY_TIMEMAP,
    PIPELINE_VERSION,
    PipelineError,
    STAGE_QUANTIZATION,
    STAGE_SCORE_IR,
    STAGE_TIME_MAP,
    utc_now,
)


TIME_MAP_SCHEMA_VERSION = "time-map/v1"
SCORE_IR_SCHEMA_VERSION = "score-ir/v1"
BEATS_PER_MEASURE = 4
BEAT_UNIT = 4
BEAT_POSITION_TOLERANCE = 0.15
DURATION_TOLERANCE_BEATS = 0.12
POSITION_GRID_BEATS = 0.5
MIN_SUPPORTED_BEAT_SECONDS = 0.20
MAX_SUPPORTED_BEAT_SECONDS = 2.0

DURATION_VOCABULARY = [
    ("eighth", 0.5),
    ("quarter", 1.0),
    ("dotted-quarter", 1.5),
    ("half", 2.0),
    ("dotted-half", 3.0),
    ("whole", 4.0),
]


def build_time_map(note_events: Dict[str, object], canonical_audio: Dict[str, object]) -> Dict[str, object]:
    notes = list(note_events.get("notes", []))
    if not notes:
        raise PipelineError(CATEGORY_TIMEMAP, STAGE_TIME_MAP, "TimeMap requires at least one note event")

    duration_seconds = float(canonical_audio.get("duration_seconds") or 0.0)
    if duration_seconds <= 0:
        duration_seconds = max(float(note["offset"]) for note in notes)
    beat_seconds = duration_seconds / len(notes)
    if not MIN_SUPPORTED_BEAT_SECONDS <= beat_seconds <= MAX_SUPPORTED_BEAT_SECONDS:
        raise PipelineError(
            CATEGORY_TIMEMAP,
            STAGE_TIME_MAP,
            "Input is outside the deterministic simple-meter timing envelope",
        )

    anchor_seconds = float(notes[0]["onset"])
    tempo_bpm = round(60.0 / beat_seconds, 6)
    mappings = []
    for note in notes:
        onset = float(note["onset"])
        offset = float(note["offset"])
        raw_start = _seconds_to_absolute_beat(onset, anchor_seconds, beat_seconds)
        raw_end = _seconds_to_absolute_beat(offset, anchor_seconds, beat_seconds)
        round_trip = _absolute_beat_to_seconds(raw_start, anchor_seconds, beat_seconds)
        mappings.append(
            {
                "note_event_id": str(note["id"]),
                "onset_seconds": round(onset, 6),
                "offset_seconds": round(offset, 6),
                "duration_seconds": round(offset - onset, 6),
                "duration_beats": round(raw_end - raw_start, 6),
                "position": _position_from_absolute_beat(raw_start),
                "end_position": _position_from_absolute_beat(raw_end),
                "round_trip_onset_seconds": round(round_trip, 6),
                "onset_round_trip_delta_seconds": round(round_trip - onset, 9),
            }
        )

    return {
        "schema_version": TIME_MAP_SCHEMA_VERSION,
        "generator_version": PIPELINE_VERSION,
        "created_at": utc_now(),
        "job_id": note_events["job_id"],
        "source_id": note_events["source_id"],
        "source_path": note_events.get("source_path", ""),
        "input_format": note_events.get("input_format", ""),
        "note_events_version": note_events["generator_version"],
        "tempo": {"bpm": tempo_bpm, "beat_seconds": round(beat_seconds, 6), "beat_unit": BEAT_UNIT},
        "time_signature": {"beats_per_measure": BEATS_PER_MEASURE, "beat_unit": BEAT_UNIT},
        "support": {
            "mode": "deterministic-simple-meter",
            "anchor_source": "canonical-duration-and-note-count",
            "arbitrary_beat_tracking": False,
        },
        "tolerances": {
            "beat_position": BEAT_POSITION_TOLERANCE,
            "duration_beats": DURATION_TOLERANCE_BEATS,
            "position_grid_beats": POSITION_GRID_BEATS,
        },
        "anchors": [
            {
                "source_seconds": round(anchor_seconds, 6),
                "absolute_beat": 0.0,
                "measure": 1,
                "beat": 1.0,
                "provenance": "first-note-onset",
            }
        ],
        "note_mappings": mappings,
    }


def build_score_ir(note_events: Dict[str, object], time_map: Dict[str, object]) -> Dict[str, object]:
    notes = list(note_events.get("notes", []))
    mappings = {mapping["note_event_id"]: mapping for mapping in time_map.get("note_mappings", [])}
    score_notes = []
    for index, note in enumerate(notes):
        note_id = str(note["id"])
        mapping = mappings.get(note_id)
        if mapping is None:
            raise PipelineError(
                CATEGORY_SCORE_IR_CONTRACT,
                STAGE_SCORE_IR,
                f"ScoreIR note {index} has no TimeMap mapping for source note {note_id}",
            )

        raw_start = float(mapping["position"]["absolute_beat"])
        raw_duration = float(mapping["duration_beats"])
        start_beat = _quantize_to_grid(raw_start, POSITION_GRID_BEATS)
        start_delta = abs(start_beat - raw_start)
        if start_delta > BEAT_POSITION_TOLERANCE:
            raise PipelineError(
                CATEGORY_QUANTIZATION,
                STAGE_QUANTIZATION,
                f"Note {note_id} onset is off the supported beat grid by {start_delta:.3f} beats",
            )

        duration_name, duration_beats = _quantize_duration(note_id, raw_duration)
        position = _position_from_absolute_beat(start_beat)
        note_end = round(start_beat + duration_beats, 6)
        measure_end = (position["measure"] - 1) * BEATS_PER_MEASURE + BEATS_PER_MEASURE
        if note_end > measure_end + 1e-6:
            raise PipelineError(
                CATEGORY_QUANTIZATION,
                STAGE_QUANTIZATION,
                f"Note {note_id} crosses a measure boundary, which is outside this slice",
            )

        score_notes.append(
            {
                "id": f"score-note-{index + 1:04d}",
                "source_note_event_id": note_id,
                "pitch": int(note["pitch"]),
                "measure": position["measure"],
                "beat": position["beat"],
                "absolute_beat": round(start_beat, 6),
                "duration_beats": duration_beats,
                "notated_duration": {
                    "name": duration_name,
                    "beats": duration_beats,
                    "divisions": _duration_to_divisions(duration_beats),
                },
                "source_seconds": {
                    "onset": round(float(note["onset"]), 6),
                    "offset": round(float(note["offset"]), 6),
                },
            }
        )

    errors = validate_score_ir_notes(score_notes)
    if errors:
        raise PipelineError(CATEGORY_SCORE_IR_CONTRACT, STAGE_SCORE_IR, "; ".join(errors))

    measures = _build_measures(score_notes)
    return {
        "schema_version": SCORE_IR_SCHEMA_VERSION,
        "generator_version": PIPELINE_VERSION,
        "created_at": utc_now(),
        "job_id": note_events["job_id"],
        "source_id": note_events["source_id"],
        "source_note_events_version": note_events["generator_version"],
        "time_map_version": time_map["generator_version"],
        "time_signature": time_map["time_signature"],
        "tempo": time_map["tempo"],
        "quantization": {
            "duration_vocabulary": [
                {"name": name, "beats": beats, "divisions": _duration_to_divisions(beats)}
                for name, beats in DURATION_VOCABULARY
            ],
            "beat_position_tolerance": BEAT_POSITION_TOLERANCE,
            "duration_tolerance_beats": DURATION_TOLERANCE_BEATS,
        },
        "parts": [
            {
                "id": "P1",
                "name": "Melody",
                "voice_count": 1,
                "notes": score_notes,
                "measures": measures,
            }
        ],
    }


def validate_score_ir_notes(notes: Iterable[Dict[str, object]]) -> List[str]:
    errors = []
    previous_end = None
    seen_source_ids = set()
    for index, note in enumerate(notes):
        source_id = str(note.get("source_note_event_id", ""))
        if not source_id:
            errors.append(f"score note {index} missing source_note_event_id")
        if source_id in seen_source_ids:
            errors.append(f"score note {index} duplicate source_note_event_id {source_id}")
        seen_source_ids.add(source_id)
        for field in ["pitch", "measure", "beat", "absolute_beat", "duration_beats", "notated_duration"]:
            if field not in note:
                errors.append(f"score note {index} missing {field}")
        try:
            start = float(note["absolute_beat"])
            duration = float(note["duration_beats"])
        except (KeyError, TypeError, ValueError):
            errors.append(f"score note {index} has invalid timing fields")
            continue
        if previous_end is not None and start < previous_end - 1e-6:
            errors.append(f"score note {index} overlaps previous score note")
        previous_end = start + duration
    return errors


def _seconds_to_absolute_beat(seconds: float, anchor_seconds: float, beat_seconds: float) -> float:
    return round((seconds - anchor_seconds) / beat_seconds, 9)


def _absolute_beat_to_seconds(absolute_beat: float, anchor_seconds: float, beat_seconds: float) -> float:
    return anchor_seconds + absolute_beat * beat_seconds


def _position_from_absolute_beat(absolute_beat: float) -> Dict[str, float]:
    measure = int(math.floor(absolute_beat / BEATS_PER_MEASURE)) + 1
    beat = absolute_beat - ((measure - 1) * BEATS_PER_MEASURE) + 1.0
    return {
        "absolute_beat": round(absolute_beat, 6),
        "measure": measure,
        "beat": round(beat, 6),
    }


def _quantize_to_grid(value: float, grid: float) -> float:
    return round(round(value / grid) * grid, 6)


def _quantize_duration(note_id: str, raw_duration: float) -> Tuple[str, float]:
    name, beats = min(DURATION_VOCABULARY, key=lambda item: abs(item[1] - raw_duration))
    delta = abs(beats - raw_duration)
    if delta > DURATION_TOLERANCE_BEATS:
        raise PipelineError(
            CATEGORY_QUANTIZATION,
            STAGE_QUANTIZATION,
            f"Note {note_id} duration {raw_duration:.3f} beats is not an accepted note value",
        )
    return name, beats


def _duration_to_divisions(duration_beats: float) -> int:
    return int(round(duration_beats * 1000))


def _build_measures(notes: List[Dict[str, object]]) -> List[Dict[str, object]]:
    if not notes:
        return []
    measure_count = max(int(note["measure"]) for note in notes)
    measures = []
    for measure_number in range(1, measure_count + 1):
        measure_notes = [note for note in notes if int(note["measure"]) == measure_number]
        filled = round(sum(float(note["duration_beats"]) for note in measure_notes), 6)
        trailing_rest = max(0.0, round(BEATS_PER_MEASURE - filled, 6)) if measure_number == measure_count else 0.0
        measures.append(
            {
                "number": measure_number,
                "expected_beats": BEATS_PER_MEASURE,
                "pitched_note_beats": filled,
                "trailing_rest_beats": trailing_rest,
            }
        )
    return measures
