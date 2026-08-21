from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


PIPELINE_VERSION = "target-instrument-single-melody-arrangement/v1"

PASS = "PASS"
REVIEW = "REVIEW"
FAIL = "FAIL"

COMPLETED = "COMPLETED"
ACCEPTED = "ACCEPTED"
NOT_ACCEPTED = "NOT_ACCEPTED"

STAGE_MEDIA = "media"
STAGE_DECODE = "decode"
STAGE_SCOPE = "scope"
STAGE_TRANSCRIPTION = "transcription"
STAGE_NOTE_EVENTS = "note_events"
STAGE_TIME_MAP = "time_map"
STAGE_QUANTIZATION = "quantization"
STAGE_SCORE_IR = "score_ir"
STAGE_INSTRUMENT_PROFILE = "instrument_profile"
STAGE_ARRANGEMENT = "arrangement"
STAGE_MUSICXML = "musicxml"
STAGE_EVALUATION = "evaluation"
STAGE_DELIVERY = "delivery"

CATEGORY_UNSUPPORTED_FORMAT = "UNSUPPORTED_FORMAT"
CATEGORY_MEDIA_DECODE = "MEDIA_DECODE"
CATEGORY_AUDIO_QUALITY = "AUDIO_QUALITY"
CATEGORY_UNSUPPORTED_SCOPE = "UNSUPPORTED_SCOPE"
CATEGORY_TRANSCRIPTION_QUALITY = "TRANSCRIPTION_QUALITY"
CATEGORY_NOTE_EVENTS_CONTRACT = "NOTE_EVENTS_CONTRACT"
CATEGORY_TIMEMAP = "TIMEMAP"
CATEGORY_TIMING = "TIMING"
CATEGORY_QUANTIZATION = "QUANTIZATION"
CATEGORY_SCORE_IR_CONTRACT = "SCORE_IR_CONTRACT"
CATEGORY_INSTRUMENT_PROFILE = "INSTRUMENT_PROFILE"
CATEGORY_ARRANGEMENT_RANGE = "ARRANGEMENT_RANGE"
CATEGORY_ARRANGED_SCORE_CONTRACT = "ARRANGED_SCORE_CONTRACT"
CATEGORY_MUSICXML_EXPORT = "MUSICXML_EXPORT"
CATEGORY_EVALUATION = "EVALUATION"
CATEGORY_DELIVERY = "DELIVERY"


class PipelineError(Exception):
    def __init__(self, category: str, stage: str, message: str):
        super().__init__(message)
        self.category = category
        self.stage = stage
        self.message = message

    def reason(self) -> Dict[str, str]:
        return {"category": self.category, "stage": self.stage, "message": self.message}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def note_duration(note: Dict[str, Any]) -> float:
    if "duration" in note:
        return float(note["duration"])
    return float(note["offset"]) - float(note["onset"])


def note_offset(note: Dict[str, Any]) -> float:
    if "offset" in note:
        return float(note["offset"])
    return float(note["onset"]) + note_duration(note)


def normalized_notes(notes: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    normalized = []
    for note in notes:
        onset = round(float(note["onset"]), 6)
        offset = round(note_offset(note), 6)
        normalized.append(
            {
                "pitch": int(note["pitch"]),
                "onset": onset,
                "offset": offset,
                "duration": round(offset - onset, 6),
                "confidence": round(float(note.get("confidence", 1.0)), 6),
            }
        )
    return sorted(normalized, key=lambda item: (item["onset"], item["offset"], item["pitch"]))


def validate_note_events_artifact(artifact: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    for field in ["job_id", "source_id", "input_format", "generator_version", "notes"]:
        if not artifact.get(field):
            errors.append(f"missing {field}")

    previous_offset: Optional[float] = None
    seen_ids = set()
    for index, note in enumerate(artifact.get("notes", [])):
        for field in ["pitch", "onset", "offset", "duration", "confidence"]:
            if field not in note:
                errors.append(f"note {index} missing {field}")
        if "id" in note:
            note_id = str(note["id"])
            if note_id in seen_ids:
                errors.append(f"note {index} duplicate id {note_id}")
            seen_ids.add(note_id)
        try:
            pitch = int(note["pitch"])
            onset = float(note["onset"])
            offset = float(note["offset"])
            duration = float(note["duration"])
            confidence = float(note["confidence"])
        except (KeyError, TypeError, ValueError):
            errors.append(f"note {index} has invalid numeric fields")
            continue

        if not 0 <= confidence <= 1:
            errors.append(f"note {index} confidence outside 0..1")
        if not 0 <= pitch <= 127:
            errors.append(f"note {index} pitch outside MIDI range")
        if offset <= onset:
            errors.append(f"note {index} offset must be after onset")
        if abs((offset - onset) - duration) > 1e-5:
            errors.append(f"note {index} duration does not match onset/offset")
        if previous_offset is not None and onset < previous_offset - 1e-6:
            errors.append(f"note {index} overlaps previous note")
        previous_offset = offset

    return errors
