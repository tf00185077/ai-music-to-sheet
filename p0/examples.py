from __future__ import annotations

from typing import Any, Dict

from p0.contracts import (
    artifact_id_for,
    create_artifact,
    known_fact,
    low_confidence_fact,
    source_reference,
    unknown_fact,
)


ZERO_HASH = "0" * 64
ONE_HASH = "1" * 64


def _track_event(instrument: str, mode: str, stem_id: str) -> Dict[str, Any]:
    event: Dict[str, Any] = {
        "event_id": "%s-event-1" % instrument,
        "onset_seconds": 0.05,
        "offset_seconds": 0.075,
        "velocity": 96,
        "confidence": known_fact(0.99),
    }
    if mode == "transcription":
        event["evidence"] = [
            {
                "artifact_id": stem_id,
                "stem_instrument": instrument,
                "start_seconds": 0.04,
                "end_seconds": 0.08,
            }
        ]
    else:
        event["arrangement_decision"] = {
            "rule": "p0-fixed-pattern/1.0.0",
            "reason": "deterministic arrangement fixture",
        }

    if instrument == "drums":
        event.update({"drum_class": "kick", "technique": known_fact("normal")})
    elif instrument == "piano":
        event.update(
            {
                "pitch": 60,
                "voice": 1,
                "hand": known_fact("right"),
                "pedal": unknown_fact(),
            }
        )
    elif instrument == "guitar":
        event.update(
            {
                "pitch": 64,
                "string": unknown_fact(),
                "fret": unknown_fact(),
                "tuning": [known_fact(value) for value in (40, 45, 50, 55, 59, 64)],
                "capo": unknown_fact(),
                "technique": low_confidence_fact("normal", 0.55),
            }
        )
    else:
        raise ValueError("unsupported instrument %s" % instrument)
    return event


def artifact_examples(track_instrument: str = "drums", track_mode: str = "transcription") -> Dict[str, Dict[str, Any]]:
    source = create_artifact(
        "SourceMedia",
        {
            "file_format": "wav",
            "media_sha256": ZERO_HASH,
            "byte_size": 9644,
            "track_count": 1,
            "source_identifier": "fixture:annotated-mix",
            "usage_rights": {"spdx": "CC0-1.0", "owner": "project-generated"},
        },
        logical_key="example-source",
    )
    canonical = create_artifact(
        "CanonicalAudio",
        {
            "sample_rate": 48000,
            "channel_layout": ["mono"],
            "sample_format": "pcm_s16le",
            "duration_seconds": 0.1,
            "audio_sha256": ONE_HASH,
        },
        source_artifacts=(source,),
        logical_key="example-canonical",
    )
    analysis = create_artifact(
        "SongAnalysis",
        {
            "tempo_map": [{"time_seconds": 0.0, "bpm": 120.0, "confidence": known_fact(1.0)}],
            "beats": [{"time_seconds": 0.0, "confidence": known_fact(1.0)}],
            "downbeats": [{"time_seconds": 0.0, "confidence": known_fact(1.0)}],
            "meter": known_fact({"numerator": 4, "denominator": 4}),
            "key": unknown_fact(),
            "sections": [{"label": "A", "start_seconds": 0.0, "end_seconds": 0.1, "confidence": known_fact(1.0)}],
        },
        source_artifacts=(canonical,),
        logical_key="example-analysis",
    )
    stem = create_artifact(
        "StemSet",
        {
            "taxonomy_version": "p0-instruments/1.0.0",
            "stems": [
                {
                    "instrument": instrument,
                    "path": "audio/isolated-%s.wav" % instrument,
                    "sha256": ZERO_HASH,
                    "presence": "present",
                    "confidence": known_fact(1.0),
                }
                for instrument in ("drums", "piano", "guitar")
            ],
        },
        source_artifacts=(canonical,),
        logical_key="example-stems",
    )
    track = create_artifact(
        "TrackIR",
        {
            "instrument": track_instrument,
            "mode": track_mode,
            "instrument_presence": known_fact("present"),
            "events": [_track_event(track_instrument, track_mode, stem["artifact_id"])],
        },
        source_artifacts=(analysis, stem),
        logical_key="example-track:%s:%s" % (track_instrument, track_mode),
    )
    notation = create_artifact(
        "NotationIR",
        {
            "track_mode": track_mode,
            "instrument": track_instrument,
            "measures": [
                {
                    "number": 1,
                    "meter": {"numerator": 4, "denominator": 4},
                    "tempo": {"bpm": 120.0},
                    "voices": [{"voice": 1, "events": [track["payload"]["events"][0]["event_id"]]}],
                }
            ],
            "staff": [{"number": 1, "kind": "percussion" if track_instrument == "drums" else "standard"}],
            "ties": [],
            "instrument_notation": {"semantic_type": track_instrument},
        },
        source_artifacts=(track,),
        logical_key="example-notation:%s:%s" % (track_instrument, track_mode),
    )
    run_id = "example-run"
    process_id = artifact_id_for("ProcessTestReport", run_id)
    evaluation = create_artifact(
        "EvaluationReport",
        {
            "run_id": run_id,
            "dataset_version": "p0-fixtures/1.0.0",
            "evaluated_artifact_ids": [track["artifact_id"]],
            "evaluator": {
                "name": "p0-event-evaluator",
                "version": "1.0.0",
                "tolerance_seconds": 0.05,
                "tolerance_rule": "inclusive",
                "matching_rule": "nearest-one-to-one",
                "empty_set_policy": "empty/empty=1; prediction-empty precision=1 recall=0",
            },
            "metrics": {"precision": 1.0, "recall": 1.0, "f1": 1.0},
            "thresholds": {"f1": 1.0},
            "artifact_paths": ["evaluation-example.json"],
            "process_test_report_id": process_id,
            "evaluation_category": "automatic",
        },
        source_artifacts=(notation,),
        logical_key="example-evaluation:%s:%s" % (track_instrument, track_mode),
    )
    process = create_artifact(
        "ProcessTestReport",
        {
            "run_id": run_id,
            "test_case_id": "example-success",
            "input_checksum": source["payload"]["media_sha256"],
            "dataset_version": "p0-fixtures/1.0.0",
            "stages": ["source", "canonical", "analysis", "stems", "track", "notation", "evaluation"],
            "versions": {
                "fixture": "1.0.0",
                "schema": "1.0.0",
                "evaluator": "1.0.0",
                "program": "1.0.0",
                "model": "stub-1.0.0",
                "parameters": "sha256:" + ZERO_HASH,
                "seed": 20260824,
            },
            "timing": {"started_at": "2000-01-01T00:00:00Z", "ended_at": "2000-01-01T00:00:01Z"},
            "execution_environment": {"runtime": "python-stdlib", "os": "portable", "architecture": "unknown"},
            "artifact_paths": ["process-test-report.json", "evaluation-example.json"],
            "log_references": [{"path": "verify.log", "sha256": ZERO_HASH}],
            "checks": [
                {
                    "id": "example-check",
                    "actual": 1.0,
                    "threshold": 1.0,
                    "passed": True,
                    "numerator": 1,
                    "denominator": 1,
                    "metric_version": "p0-gate/1.0.0",
                    "tolerance": 0.0,
                }
            ],
            "evaluation_reports": [source_reference(evaluation)],
            "automatic_benchmark": True,
            "expected_checks": ["example-check"],
            "executed_checks": ["example-check"],
            "candidate_sha": "example-candidate-sha",
            "dirty_tree_before_run": False,
        },
        source_artifacts=(evaluation,),
        logical_key=run_id,
        artifact_id=process_id,
    )
    return {
        "SourceMedia": source,
        "CanonicalAudio": canonical,
        "SongAnalysis": analysis,
        "StemSet": stem,
        "TrackIR": track,
        "NotationIR": notation,
        "EvaluationReport": evaluation,
        "ProcessTestReport": process,
    }
