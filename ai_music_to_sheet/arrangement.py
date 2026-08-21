from __future__ import annotations

import copy
from typing import Dict, Iterable, List, Tuple

from .contracts import (
    CATEGORY_ARRANGED_SCORE_CONTRACT,
    CATEGORY_ARRANGEMENT_RANGE,
    CATEGORY_INSTRUMENT_PROFILE,
    FAIL,
    PASS,
    PIPELINE_VERSION,
    PipelineError,
    STAGE_ARRANGEMENT,
    STAGE_INSTRUMENT_PROFILE,
    utc_now,
)


ARRANGED_SCORE_SCHEMA_VERSION = "arranged-score/v1"
INSTRUMENT_PROFILE_SCHEMA_VERSION = "instrument-profile/v1"
SUPPORTED_PITCH_DOMAIN = "non_transposing_sounding_range_only"
SUPPORTED_PROFILE_ID = "beginner-soprano-recorder"
OCTAVE_SHIFT_CANDIDATES = (0, 1, -1, 2, -2, 3, -3, 4, -4, 5, -5)

SUPPORTED_INSTRUMENT_PROFILES: Dict[str, Dict[str, object]] = {
    SUPPORTED_PROFILE_ID: {
        "schema_version": INSTRUMENT_PROFILE_SCHEMA_VERSION,
        "id": SUPPORTED_PROFILE_ID,
        "version": "beginner-soprano-recorder/v1",
        "display_name": "Beginner Soprano Recorder",
        "part_name": "Beginner Soprano Recorder",
        "instrument_family": "recorder",
        "sounded_midi_range": {"min": 72, "max": 84},
        "pitch_domain": SUPPORTED_PITCH_DOMAIN,
        "transposition": {"written_pitch": False, "semitones": 0},
        "voice_count": 1,
        "support": {
            "status": "supported",
            "difficulty": "beginner",
            "policy": "single_global_octave_shift_only",
        },
        "generator_version": PIPELINE_VERSION,
    }
}


class ArrangementNotAccepted(Exception):
    def __init__(self, category: str, stage: str, message: str):
        super().__init__(message)
        self.category = category
        self.stage = stage
        self.message = message

    def reason(self) -> Dict[str, str]:
        return {"category": self.category, "stage": self.stage, "message": self.message}


def get_instrument_profile(profile_id: str) -> Dict[str, object]:
    profile = SUPPORTED_INSTRUMENT_PROFILES.get(str(profile_id))
    if profile is None:
        supported_ids = ", ".join(sorted(SUPPORTED_INSTRUMENT_PROFILES))
        raise ArrangementNotAccepted(
            CATEGORY_INSTRUMENT_PROFILE,
            STAGE_INSTRUMENT_PROFILE,
            f"Unsupported target profile '{profile_id}'. Supported profile ids: {supported_ids}.",
        )
    profile_copy = copy.deepcopy(profile)
    errors = validate_instrument_profile(profile_copy)
    if errors:
        raise PipelineError(CATEGORY_INSTRUMENT_PROFILE, STAGE_INSTRUMENT_PROFILE, "; ".join(errors))
    return profile_copy


def validate_instrument_profile(profile: Dict[str, object]) -> List[str]:
    errors: List[str] = []
    for field in [
        "schema_version",
        "id",
        "version",
        "display_name",
        "part_name",
        "sounded_midi_range",
        "pitch_domain",
        "voice_count",
        "support",
        "generator_version",
    ]:
        if not profile.get(field):
            errors.append(f"profile missing {field}")
    if profile.get("schema_version") != INSTRUMENT_PROFILE_SCHEMA_VERSION:
        errors.append("profile schema_version is unsupported")
    if profile.get("pitch_domain") != SUPPORTED_PITCH_DOMAIN:
        errors.append("profile pitch_domain is outside the non-transposing sounded-pitch slice")
    try:
        voice_count = int(profile.get("voice_count") or 0)
    except (TypeError, ValueError):
        errors.append("profile voice_count must be an integer")
    else:
        if voice_count != 1:
            errors.append("profile voice_count must be 1")
    range_info = profile.get("sounded_midi_range")
    if not isinstance(range_info, dict):
        errors.append("profile sounded_midi_range must be an object")
    else:
        try:
            min_pitch = int(range_info["min"])
            max_pitch = int(range_info["max"])
        except (KeyError, TypeError, ValueError):
            errors.append("profile sounded_midi_range must include integer min and max")
        else:
            if min_pitch < 0 or max_pitch > 127 or min_pitch > max_pitch:
                errors.append("profile sounded_midi_range is outside MIDI bounds")
    return errors


def arrange_score_ir(
    score_ir: Dict[str, object],
    *,
    target_profile: Dict[str, object],
    source: Dict[str, object],
    source_artifact_path: str,
    score_ir_artifact_path: str,
    time_map: Dict[str, object],
    time_map_artifact_path: str,
) -> Dict[str, object]:
    source_part = score_ir["parts"][0]
    source_notes = list(source_part["notes"])
    octave_shift, candidates = _select_global_octave_shift(source_notes, target_profile)
    semitones = octave_shift * 12
    arranged_notes = []
    for index, source_note in enumerate(source_notes, start=1):
        source_pitch = int(source_note["pitch"])
        target_pitch = source_pitch + semitones
        arranged_note = {
            "id": f"arranged-note-{index:04d}",
            "source_score_note_id": str(source_note["id"]),
            "source_note_event_id": str(source_note["source_note_event_id"]),
            "pitch": target_pitch,
            "measure": int(source_note["measure"]),
            "beat": float(source_note["beat"]),
            "absolute_beat": float(source_note["absolute_beat"]),
            "duration_beats": float(source_note["duration_beats"]),
            "notated_duration": copy.deepcopy(source_note["notated_duration"]),
            "source_seconds": copy.deepcopy(source_note.get("source_seconds", {})),
            "pitch_transformation": {
                "type": "global_octave_shift",
                "global_octave_shift": octave_shift,
                "semitones": semitones,
                "source_pitch": source_pitch,
                "target_pitch": target_pitch,
            },
        }
        arranged_notes.append(arranged_note)

    arranged_score = {
        "schema_version": ARRANGED_SCORE_SCHEMA_VERSION,
        "generator_version": PIPELINE_VERSION,
        "created_at": utc_now(),
        "job_id": score_ir["job_id"],
        "source_id": score_ir["source_id"],
        "target_profile": copy.deepcopy(target_profile),
        "source": {
            "job_id": source["job_id"],
            "source_id": source["source_id"],
            "source_path": source["source_path"],
            "source_version": source["version"],
            "source_artifact": source_artifact_path,
            "score_ir_version": score_ir["generator_version"],
            "score_ir_artifact": score_ir_artifact_path,
            "time_map_version": time_map["generator_version"],
            "time_map_artifact": time_map_artifact_path,
        },
        "arrangement": {
            "policy": "single_global_octave_shift",
            "global_octave_shift": octave_shift,
            "semitones": semitones,
            "candidate_shifts": candidates,
            "status": PASS,
        },
        "time_signature": copy.deepcopy(score_ir["time_signature"]),
        "tempo": copy.deepcopy(score_ir["tempo"]),
        "parts": [
            {
                "id": str(source_part["id"]),
                "name": str(target_profile["part_name"]),
                "voice_count": 1,
                "notes": arranged_notes,
                "measures": copy.deepcopy(source_part.get("measures", [])),
            }
        ],
    }
    errors = validate_arranged_score_artifact(arranged_score, score_ir)
    if errors:
        raise PipelineError(CATEGORY_ARRANGED_SCORE_CONTRACT, STAGE_ARRANGEMENT, "; ".join(errors))
    return arranged_score


def validate_arranged_score_artifact(
    arranged_score: Dict[str, object],
    source_score_ir: Dict[str, object],
) -> List[str]:
    errors: List[str] = []
    if arranged_score.get("schema_version") != ARRANGED_SCORE_SCHEMA_VERSION:
        errors.append("arranged score schema_version is unsupported")
    profile = arranged_score.get("target_profile")
    if not isinstance(profile, dict):
        errors.append("arranged score missing target_profile")
        profile = {}
    errors.extend(validate_instrument_profile(profile))

    source_parts = source_score_ir.get("parts") or []
    arranged_parts = arranged_score.get("parts") or []
    if len(source_parts) != 1 or len(arranged_parts) != 1:
        errors.append("arranged score must compare one source part to one arranged part")
        return errors
    source_notes = list(source_parts[0].get("notes", []))
    arranged_notes = list(arranged_parts[0].get("notes", []))
    if len(source_notes) != len(arranged_notes):
        errors.append("arranged note count does not match source ScoreIR")
    if int(arranged_parts[0].get("voice_count") or 0) != 1:
        errors.append("arranged part voice_count must be 1")
    if str(arranged_parts[0].get("name")) != str(profile.get("part_name")):
        errors.append("arranged part name does not match target profile part_name")

    try:
        global_shift = int(arranged_score["arrangement"]["global_octave_shift"])
        semitones = int(arranged_score["arrangement"]["semitones"])
        min_pitch = int(profile["sounded_midi_range"]["min"])
        max_pitch = int(profile["sounded_midi_range"]["max"])
    except (KeyError, TypeError, ValueError):
        errors.append("arranged score missing valid arrangement shift or profile range")
        return errors
    if semitones != global_shift * 12:
        errors.append("arrangement semitones must equal global_octave_shift * 12")

    for index, (source_note, arranged_note) in enumerate(zip(source_notes, arranged_notes)):
        _validate_arranged_note_pair(errors, index, source_note, arranged_note, global_shift, semitones, min_pitch, max_pitch)
    return errors


def score_arrangement_quality(
    *,
    arranged_score: Dict[str, object],
    source_score_ir: Dict[str, object],
    musicxml_summary: Dict[str, object],
) -> Dict[str, object]:
    profile = arranged_score["target_profile"]
    min_pitch = int(profile["sounded_midi_range"]["min"])
    max_pitch = int(profile["sounded_midi_range"]["max"])
    source_notes = list(source_score_ir["parts"][0]["notes"])
    arranged_notes = list(arranged_score["parts"][0]["notes"])

    out_of_range_notes = [
        {
            "source_score_note_id": note.get("source_score_note_id"),
            "pitch": int(note["pitch"]),
        }
        for note in arranged_notes
        if int(note["pitch"]) < min_pitch or int(note["pitch"]) > max_pitch
    ]
    rhythm_mismatches = _rhythm_mismatches(source_notes, arranged_notes)
    xml_pitch_sequence = list(musicxml_summary.get("pitch_sequence", []))
    arranged_pitch_sequence = [int(note["pitch"]) for note in arranged_notes]
    xml_mismatches = []
    if xml_pitch_sequence != arranged_pitch_sequence:
        xml_mismatches.append("musicxml pitch sequence does not match arranged score")

    status = PASS if not out_of_range_notes and not rhythm_mismatches and not xml_mismatches else FAIL
    return {
        "status": status,
        "target_profile": {
            "id": profile["id"],
            "version": profile["version"],
            "part_name": profile["part_name"],
            "sounded_midi_range": copy.deepcopy(profile["sounded_midi_range"]),
        },
        "source_score_ir_version": source_score_ir["generator_version"],
        "arranged_score_version": arranged_score["generator_version"],
        "musicxml_version": PIPELINE_VERSION,
        "range_fit": {
            "status": PASS if not out_of_range_notes else FAIL,
            "min": min_pitch,
            "max": max_pitch,
            "out_of_range_notes": out_of_range_notes,
        },
        "rhythm_preservation": {
            "status": PASS if not rhythm_mismatches else FAIL,
            "checked_fields": ["source_score_note_id", "measure", "beat", "absolute_beat", "duration_beats", "notated_duration"],
            "mismatches": rhythm_mismatches,
        },
        "musicxml_consistency": {
            "status": PASS if not xml_mismatches else FAIL,
            "mismatches": xml_mismatches,
        },
    }


def _select_global_octave_shift(
    source_notes: Iterable[Dict[str, object]],
    target_profile: Dict[str, object],
) -> Tuple[int, List[Dict[str, object]]]:
    notes = list(source_notes)
    min_pitch = int(target_profile["sounded_midi_range"]["min"])
    max_pitch = int(target_profile["sounded_midi_range"]["max"])
    candidates = []
    for octave_shift in OCTAVE_SHIFT_CANDIDATES:
        semitones = octave_shift * 12
        transformed = [int(note["pitch"]) + semitones for note in notes]
        fits = all(min_pitch <= pitch <= max_pitch for pitch in transformed)
        candidates.append(
            {
                "global_octave_shift": octave_shift,
                "semitones": semitones,
                "min_pitch": min(transformed) if transformed else None,
                "max_pitch": max(transformed) if transformed else None,
                "fits": fits,
            }
        )
        if fits:
            return octave_shift, candidates
    blocking = [
        {
            "source_score_note_id": note.get("id"),
            "source_pitch": int(note["pitch"]),
        }
        for note in notes
    ]
    raise ArrangementNotAccepted(
        CATEGORY_ARRANGEMENT_RANGE,
        STAGE_ARRANGEMENT,
        "No single score-wide octave shift places every source note inside the target profile range "
        f"{min_pitch}..{max_pitch}; per-note octave wrapping is outside this slice. Blocking notes: {blocking}.",
    )


def _validate_arranged_note_pair(
    errors: List[str],
    index: int,
    source_note: Dict[str, object],
    arranged_note: Dict[str, object],
    global_shift: int,
    semitones: int,
    min_pitch: int,
    max_pitch: int,
) -> None:
    if str(arranged_note.get("source_score_note_id")) != str(source_note.get("id")):
        errors.append(f"arranged note {index} source_score_note_id does not match source ScoreIR")
    if str(arranged_note.get("source_note_event_id")) != str(source_note.get("source_note_event_id")):
        errors.append(f"arranged note {index} source_note_event_id does not match source ScoreIR")
    for field in ["measure", "beat", "absolute_beat", "duration_beats", "notated_duration"]:
        if arranged_note.get(field) != source_note.get(field):
            errors.append(f"arranged note {index} changed {field}")
    expected_pitch = int(source_note["pitch"]) + semitones
    if int(arranged_note.get("pitch", -1)) != expected_pitch:
        errors.append(f"arranged note {index} pitch does not equal source pitch plus global shift")
    pitch = int(arranged_note.get("pitch", -1))
    if pitch < min_pitch or pitch > max_pitch:
        errors.append(f"arranged note {index} pitch outside target profile range")
    transformation = arranged_note.get("pitch_transformation")
    expected_transformation = {
        "type": "global_octave_shift",
        "global_octave_shift": global_shift,
        "semitones": semitones,
        "source_pitch": int(source_note["pitch"]),
        "target_pitch": expected_pitch,
    }
    if transformation != expected_transformation:
        errors.append(f"arranged note {index} pitch_transformation does not match global shift policy")


def _rhythm_mismatches(source_notes: List[Dict[str, object]], arranged_notes: List[Dict[str, object]]) -> List[Dict[str, object]]:
    mismatches: List[Dict[str, object]] = []
    if len(source_notes) != len(arranged_notes):
        mismatches.append({"field": "note_count", "source": len(source_notes), "arranged": len(arranged_notes)})
    for index, (source_note, arranged_note) in enumerate(zip(source_notes, arranged_notes)):
        checks = {
            "source_score_note_id": (source_note.get("id"), arranged_note.get("source_score_note_id")),
            "measure": (source_note.get("measure"), arranged_note.get("measure")),
            "beat": (source_note.get("beat"), arranged_note.get("beat")),
            "absolute_beat": (source_note.get("absolute_beat"), arranged_note.get("absolute_beat")),
            "duration_beats": (source_note.get("duration_beats"), arranged_note.get("duration_beats")),
            "notated_duration": (source_note.get("notated_duration"), arranged_note.get("notated_duration")),
        }
        for field, (source_value, arranged_value) in checks.items():
            if source_value != arranged_value:
                mismatches.append(
                    {
                        "note_index": index,
                        "field": field,
                        "source": source_value,
                        "arranged": arranged_value,
                    }
                )
    return mismatches
