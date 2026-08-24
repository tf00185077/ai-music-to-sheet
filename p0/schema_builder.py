from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, Mapping, Sequence

from p0.contracts import ARTIFACT_TYPES


DRAFT = "https://json-schema.org/draft/2020-12/schema"
COMMON_REQUIRED = [
    "artifact_type",
    "artifact_id",
    "content_hash",
    "schema_version",
    "source_artifact_ids",
    "source_artifacts",
    "generator",
    "created_at",
    "environment",
    "status",
    "confidence",
    "failure",
    "human_correction",
    "migration",
    "payload",
]


def _object(required: Sequence[str], properties: Mapping[str, Any], additional: bool = True) -> Dict[str, Any]:
    return {
        "type": "object",
        "required": list(required),
        "properties": dict(properties),
        "additionalProperties": additional,
    }


FACT = _object(
    ("state", "value", "confidence"),
    {
        "state": {"enum": ["known", "unknown", "low_confidence"]},
        "value": {},
        "confidence": {"type": ["number", "null"], "minimum": 0, "maximum": 1},
    },
)
FACT["allOf"] = [
    {
        "if": {"properties": {"state": {"const": "unknown"}}},
        "then": {"properties": {"value": {"type": "null"}, "confidence": {"type": "null"}}},
    },
    {
        "if": {"properties": {"state": {"enum": ["known", "low_confidence"]}}},
        "then": {"properties": {"value": {"not": {"type": "null"}}, "confidence": {"type": "number", "minimum": 0, "maximum": 1}}},
    },
]


def _payloads() -> Dict[str, Dict[str, Any]]:
    event_base = {
        "type": "object",
        "required": ["event_id", "onset_seconds", "velocity", "confidence"],
        "properties": {
            "event_id": {"type": "string", "minLength": 1},
            "onset_seconds": {"type": "number", "minimum": 0},
            "offset_seconds": {"type": "number", "minimum": 0},
            "velocity": {"type": "integer", "minimum": 1, "maximum": 127},
            "pitch": {"type": "integer", "minimum": 0, "maximum": 127},
            "confidence": FACT,
            "evidence": {"type": "array", "minItems": 1},
            "arrangement_decision": _object(("rule", "reason"), {"rule": {"type": "string"}, "reason": {"type": "string"}}),
            "drum_class": {"type": "string"},
            "technique": FACT,
            "voice": {"type": "integer", "minimum": 1},
            "hand": FACT,
            "pedal": FACT,
            "string": FACT,
            "fret": FACT,
            "tuning": {"type": "array", "minItems": 6, "maxItems": 6, "items": FACT},
            "capo": FACT,
        },
        "additionalProperties": True,
        "allOf": [
            {
                "if": {"properties": {"status": {"const": "success"}}},
                "then": {"properties": {"failure": {"type": "null"}}},
                "else": {
                    "properties": {
                        "failure": {
                            "type": "object",
                            "required": ["family", "code", "reason"],
                        }
                    }
                },
            }
        ],
    }
    return {
        "SourceMedia": _object(
            ("file_format", "media_sha256", "byte_size", "track_count", "source_identifier", "usage_rights"),
            {
                "file_format": {"type": "string"},
                "media_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                "byte_size": {"type": "integer", "minimum": 1},
                "track_count": {"type": "integer", "minimum": 1},
                "source_identifier": {"type": "string"},
                "usage_rights": {"type": "object"},
            },
        ),
        "CanonicalAudio": _object(
            ("sample_rate", "channel_layout", "sample_format", "duration_seconds", "audio_sha256"),
            {
                "sample_rate": {"type": "integer", "minimum": 1, "maximum": 384000},
                "channel_layout": {"type": "array", "minItems": 1, "items": {"type": "string"}},
                "sample_format": {"enum": ["pcm_s16le", "pcm_s24le", "float32"]},
                "duration_seconds": {"type": "number", "exclusiveMinimum": 0},
                "audio_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
            },
        ),
        "SongAnalysis": _object(
            ("tempo_map", "beats", "downbeats", "meter", "key", "sections"),
            {
                "tempo_map": {"type": "array", "minItems": 1},
                "beats": {"type": "array"},
                "downbeats": {"type": "array"},
                "meter": FACT,
                "key": FACT,
                "sections": {"type": "array"},
            },
        ),
        "StemSet": _object(
            ("taxonomy_version", "stems"),
            {
                "taxonomy_version": {"type": "string"},
                "stems": {"type": "array", "minItems": 1, "items": {"type": "object"}},
            },
        ),
        "TrackIR": _object(
            ("instrument", "mode", "instrument_presence", "events"),
            {
                "instrument": {"enum": ["drums", "piano", "guitar"]},
                "mode": {"enum": ["transcription", "arrangement"]},
                "instrument_presence": FACT,
                "events": {"type": "array", "minItems": 1, "items": event_base},
            },
        ),
        "NotationIR": _object(
            ("track_mode", "instrument", "measures", "staff", "ties", "instrument_notation"),
            {
                "track_mode": {"enum": ["transcription", "arrangement"]},
                "instrument": {"enum": ["drums", "piano", "guitar"]},
                "measures": {"type": "array", "minItems": 1},
                "staff": {"type": "array", "minItems": 1},
                "ties": {"type": "array"},
                "instrument_notation": {"type": "object"},
            },
        ),
        "EvaluationReport": _object(
            ("run_id", "dataset_version", "evaluated_artifact_ids", "evaluator", "metrics", "thresholds", "artifact_paths", "process_test_report_id"),
            {
                "run_id": {"type": "string"},
                "dataset_version": {"type": "string"},
                "evaluated_artifact_ids": {"type": "array", "minItems": 1},
                "evaluator": {"type": "object"},
                "metrics": {"type": "object"},
                "thresholds": {"type": "object"},
                "artifact_paths": {"type": "array", "minItems": 1},
                "process_test_report_id": {"type": "string"},
            },
        ),
        "ProcessTestReport": _object(
            (
                "run_id",
                "test_case_id",
                "input_checksum",
                "dataset_version",
                "stages",
                "versions",
                "timing",
                "execution_environment",
                "artifact_paths",
                "log_references",
                "checks",
                "evaluation_reports",
                "automatic_benchmark",
                "expected_checks",
                "executed_checks",
                "candidate_sha",
                "dirty_tree_before_run",
            ),
            {
                "run_id": {"type": "string"},
                "test_case_id": {"type": "string"},
                "input_checksum": {"type": "string"},
                "dataset_version": {"type": "string"},
                "stages": {"type": "array"},
                "versions": {"type": "object"},
                "timing": {"type": "object"},
                "execution_environment": {"type": "object"},
                "artifact_paths": {"type": "array"},
                "log_references": {"type": "array"},
                "checks": {"type": "array", "minItems": 1},
                "evaluation_reports": {"type": "array"},
                "automatic_benchmark": {"type": "boolean"},
                "expected_checks": {"type": "array"},
                "executed_checks": {"type": "array"},
                "candidate_sha": {"type": "string"},
                "dirty_tree_before_run": {"type": "boolean"},
            },
        ),
    }


def _add_track_conditions(payload: Dict[str, Any]) -> None:
    payload["allOf"] = [
        {
            "if": {"properties": {"mode": {"const": "transcription"}}},
            "then": {"properties": {"events": {"items": {"required": ["evidence"], "not": {"required": ["arrangement_decision"]}}}}},
        },
        {
            "if": {"properties": {"mode": {"const": "arrangement"}}},
            "then": {"properties": {"events": {"items": {"required": ["arrangement_decision"], "not": {"required": ["evidence"]}}}}},
        },
        {
            "if": {"properties": {"instrument": {"const": "drums"}}},
            "then": {"properties": {"events": {"items": {"required": ["drum_class", "technique"]}}}},
        },
        {
            "if": {"properties": {"instrument": {"const": "piano"}}},
            "then": {"properties": {"events": {"items": {"required": ["pitch", "voice", "hand", "pedal"]}}}},
        },
        {
            "if": {"properties": {"instrument": {"const": "guitar"}}},
            "then": {"properties": {"events": {"items": {"required": ["pitch", "string", "fret", "tuning", "capo", "technique"]}}}},
        },
    ]


def generate(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    common = {
        "$schema": DRAFT,
        "$id": "https://ai-music-to-sheet.invalid/contracts/1.0.0/common.schema.json",
        "title": "P0 artifact envelope",
        "type": "object",
        "required": COMMON_REQUIRED,
        "properties": {
            "artifact_type": {"enum": list(ARTIFACT_TYPES)},
            "artifact_id": {"type": "string", "minLength": 1},
            "content_hash": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
            "schema_version": {"type": "string", "pattern": "^1\\.[0-9]+\\.[0-9]+$"},
            "source_artifact_ids": {"type": "array", "items": {"type": "string"}, "uniqueItems": True},
            "source_artifacts": {"type": "array", "items": {"type": "object"}},
            "generator": {"type": "object"},
            "created_at": {"type": "string", "format": "date-time"},
            "environment": {"type": "object"},
            "status": {"enum": ["success", "low_confidence", "failed", "needs_human_confirmation"]},
            "confidence": FACT,
            "failure": {"type": ["object", "null"]},
            "human_correction": {"type": "boolean"},
            "migration": {"type": ["object", "null"]},
            "payload": {"type": "object"},
        },
        "additionalProperties": True,
    }
    (root / "common.schema.json").write_text(json.dumps(common, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    payloads = _payloads()
    _add_track_conditions(payloads["TrackIR"])
    index = {"schema_version": "1.0.0", "artifacts": {}}
    for artifact_type in ARTIFACT_TYPES:
        filename = artifact_type + ".schema.json"
        schema = {
            "$schema": DRAFT,
            "$id": "https://ai-music-to-sheet.invalid/contracts/1.0.0/%s" % filename,
            "title": artifact_type,
            "description": "Versioned README P0 contract for %s" % artifact_type,
            "x-schema-version": "1.0.0",
            "x-common-required": COMMON_REQUIRED,
            "allOf": [
                {"$ref": "common.schema.json"},
                {
                    "type": "object",
                    "properties": {
                        "artifact_type": {"const": artifact_type},
                        "payload": payloads[artifact_type],
                    },
                },
            ],
        }
        (root / filename).write_text(json.dumps(schema, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        index["artifacts"][artifact_type] = filename
    (root / "index.json").write_text(json.dumps(index, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def main(argv: Sequence[str]) -> int:
    if len(argv) != 2:
        print("usage: schema_builder OUTPUT_ROOT", file=sys.stderr)
        return 2
    generate(Path(argv[1]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
