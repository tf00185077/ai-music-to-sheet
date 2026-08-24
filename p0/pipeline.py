from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, Mapping, Optional

from p0.contracts import (
    artifact_id_for,
    create_artifact,
    known_fact,
    low_confidence_fact,
    runtime_environment,
    source_reference,
    unknown_fact,
)
from p0.evaluator import evaluate_events
from p0.examples import artifact_examples
from p0.fixtures import file_sha256, load_fixture_manifest, validate_fixture_dataset
from p0.provenance import ArtifactStore, IntegrityError
from p0.reporting import build_process_report, validate_process_report


class PipelineBoundaryError(ValueError):
    def __init__(self, code: str, family: str, detail: str) -> None:
        self.code = code
        self.family = family
        self.detail = detail
        super().__init__("%s: %s" % (code, detail))

    def as_dict(self) -> Dict[str, Any]:
        return {"family": self.family, "code": self.code, "detail": self.detail}


def _stop(error: PipelineBoundaryError, store: ArtifactStore, expect_failure: bool) -> Dict[str, Any]:
    if not expect_failure:
        raise error
    return {"failure": error, "store": store}


def _write_alias(path: Path, artifact: Mapping[str, Any]) -> None:
    path.write_text(json.dumps(artifact, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def run_mode_pipeline(
    fixture_root: Path,
    output_root: Path,
    mode: str,
    instrument: str,
    target_presence: str = "present",
    upstream_status: str = "success",
    consumer_mode: Optional[str] = None,
    human_correction: bool = False,
    evaluation_category: str = "automatic",
    expect_failure: bool = False,
    candidate_sha: str = "not-official-run",
    dirty_tree_before_run: bool = False,
) -> Dict[str, Any]:
    if mode not in ("transcription", "arrangement"):
        raise PipelineBoundaryError("invalid_mode", "contract_malformation", mode)
    if instrument not in ("drums", "piano", "guitar"):
        raise PipelineBoundaryError("invalid_instrument", "contract_malformation", instrument)
    validation = validate_fixture_dataset(fixture_root)
    output_root = Path(output_root)
    output_root.mkdir(parents=True, exist_ok=True)
    store = ArtifactStore(output_root / "artifact-store")
    fixture_manifest = load_fixture_manifest(fixture_root)
    annotated = next(item for item in fixture_manifest["fixtures"] if item["category"] == "annotated_mix")
    media_path = Path(fixture_root) / next(item["path"] for item in annotated["files"] if item["path"].endswith(".wav"))

    source = create_artifact(
        "SourceMedia",
        {
            "file_format": "wav",
            "media_sha256": file_sha256(media_path),
            "byte_size": media_path.stat().st_size,
            "track_count": 1,
            "source_identifier": annotated["fixture_id"],
            "usage_rights": annotated["license"],
        },
        logical_key="%s:source" % mode,
        environment=runtime_environment(),
    )
    store.put(source)
    canonical = create_artifact(
        "CanonicalAudio",
        {
            "sample_rate": fixture_manifest["conventions"]["wave_format"]["sample_rate"],
            "channel_layout": ["mono"],
            "sample_format": fixture_manifest["conventions"]["wave_format"]["sample_format"],
            "duration_seconds": 0.25,
            "audio_sha256": file_sha256(media_path),
        },
        source_artifacts=(source,),
        logical_key="%s:canonical" % mode,
        environment=runtime_environment(),
    )
    store.put(canonical)
    analysis = create_artifact(
        "SongAnalysis",
        {
            "tempo_map": [{"time_seconds": 0.0, "bpm": 120.0, "confidence": known_fact(1.0)}],
            "beats": [{"time_seconds": 0.0, "confidence": known_fact(1.0)}, {"time_seconds": 0.125, "confidence": known_fact(1.0)}],
            "downbeats": [{"time_seconds": 0.0, "confidence": known_fact(1.0)}],
            "meter": known_fact({"numerator": 4, "denominator": 4}),
            "key": unknown_fact(),
            "sections": [{"label": "A", "start_seconds": 0.0, "end_seconds": 0.25, "confidence": known_fact(1.0)}],
        },
        source_artifacts=(canonical,),
        logical_key="%s:analysis" % mode,
        environment=runtime_environment(),
    )
    store.put(analysis)
    stem_records = []
    for stem_instrument in ("drums", "piano", "guitar"):
        fixture = next(item for item in fixture_manifest["fixtures"] if item["category"] == "isolated_%s" % stem_instrument)
        path_record = next(item for item in fixture["files"] if item["path"].endswith(".wav"))
        presence = target_presence if stem_instrument == instrument else "present"
        confidence = low_confidence_fact(presence, 0.4) if presence in ("low_volume", "masked") else known_fact(presence)
        stem_records.append(
            {
                "instrument": stem_instrument,
                "path": path_record["path"],
                "sha256": path_record["sha256"],
                "presence": presence,
                "confidence": confidence,
            }
        )
    stem_failure = None
    stem_confidence = known_fact(1.0)
    if upstream_status != "success":
        stem_failure = {
            "family": "contract_malformation",
            "code": "upstream_%s" % upstream_status,
            "reason": "deliberate negative-flow upstream state",
        }
        stem_confidence = low_confidence_fact("unresolved", 0.2)
    stems = create_artifact(
        "StemSet",
        {"taxonomy_version": "p0-instruments/1.0.0", "stems": stem_records},
        source_artifacts=(canonical,),
        status=upstream_status,
        confidence=stem_confidence,
        failure=stem_failure,
        logical_key="%s:stems:%s:%s" % (mode, instrument, target_presence),
        environment=runtime_environment(),
    )
    store.put(stems)
    if mode == "transcription" and target_presence == "absent":
        return _stop(
            PipelineBoundaryError("target_absent", "contract_malformation", "formal transcription TrackIR is forbidden"),
            store,
            expect_failure,
        )
    if upstream_status != "success":
        return _stop(
            PipelineBoundaryError("unresolved_upstream", "contract_malformation", upstream_status),
            store,
            expect_failure,
        )

    event = copy.deepcopy(artifact_examples(track_instrument=instrument, track_mode=mode)["TrackIR"]["payload"]["events"][0])
    if mode == "transcription":
        event["evidence"][0]["artifact_id"] = stems["artifact_id"]
    track = create_artifact(
        "TrackIR",
        {
            "instrument": instrument,
            "mode": mode,
            "instrument_presence": known_fact(target_presence),
            "events": [event],
        },
        source_artifacts=(analysis, stems),
        human_correction=human_correction,
        logical_key="%s:track:%s" % (mode, instrument),
        environment=runtime_environment(),
    )
    store.put(track)
    accepted_mode = consumer_mode or mode
    if accepted_mode != mode:
        return _stop(
            PipelineBoundaryError("cross_mode", "contract_malformation", "%s consumer received %s" % (accepted_mode, mode)),
            store,
            expect_failure,
        )
    notation_payload = copy.deepcopy(artifact_examples(track_instrument=instrument, track_mode=mode)["NotationIR"]["payload"])
    notation = create_artifact(
        "NotationIR",
        notation_payload,
        source_artifacts=(track,),
        logical_key="%s:notation:%s" % (mode, instrument),
        environment=runtime_environment(),
    )
    store.put(notation)
    run_id = "p0-%s-%s" % (mode, instrument)
    process_id = artifact_id_for("ProcessTestReport", run_id)
    reference = [{"onset_seconds": event["onset_seconds"], "class": event.get("drum_class", str(event.get("pitch")))}]
    prediction = copy.deepcopy(reference)
    if os.environ.get("P0_FORCE_LOW_SCORE") == "1":
        prediction[0]["onset_seconds"] += 0.051
    metrics = evaluate_events(reference, prediction, tolerance_seconds=0.05)
    evaluation = create_artifact(
        "EvaluationReport",
        {
            "run_id": run_id,
            "dataset_version": validation.dataset_version,
            "evaluated_artifact_ids": [track["artifact_id"]],
            "evaluator": {
                "name": "p0-event-evaluator",
                "version": metrics["metric_version"],
                "tolerance_seconds": metrics["tolerance_seconds"],
                "tolerance_rule": metrics["tolerance_rule"],
                "matching_rule": metrics["matching_rule"],
                "empty_set_policy": metrics["empty_set_policy"],
            },
            "metrics": {"precision": metrics["precision"], "recall": metrics["recall"], "f1": metrics["f1"], "class_f1": metrics["class_f1"]},
            "thresholds": {"f1": 1.0},
            "artifact_paths": ["evaluation-%s.json" % mode],
            "process_test_report_id": process_id,
            "evaluation_category": evaluation_category,
        },
        source_artifacts=(notation,),
        logical_key="%s:evaluation:%s" % (mode, instrument),
        environment=runtime_environment(),
    )
    store.put(evaluation)
    if evaluation_category == "automatic":
        try:
            store.assert_automatic_lineage(evaluation["artifact_id"])
        except IntegrityError as error:
            return _stop(
                PipelineBoundaryError("human_correction_taint", "contamination_taint", str(error)),
                store,
                expect_failure,
            )

    log_path = output_root / "verify.log"
    log_path.write_text("run=%s\nmode=%s\ninstrument=%s\n" % (run_id, mode, instrument), encoding="utf-8")
    score = metrics["f1"]
    passed = score >= 1.0
    process = build_process_report(
        run_id=run_id,
        evaluation_reports=(evaluation,),
        store=store,
        checks=[{"id": "pipeline-%s" % mode, "actual": score, "threshold": 1.0, "passed": passed}],
        status="success" if passed else "failed",
        failure_family=None if passed else "evaluator_numeric",
        failure_reason=None if passed else "score %.6f is below threshold 1.0" % score,
        candidate_sha=candidate_sha,
        dirty_tree_before_run=dirty_tree_before_run,
        input_checksum=source["payload"]["media_sha256"],
        artifact_paths=["process-test-report.json", "evaluation-%s.json" % mode],
        log_references=[{"path": "verify.log", "sha256": file_sha256(log_path)}],
    )
    store.put(process)
    _write_alias(output_root / ("evaluation-%s.json" % mode), evaluation)
    _write_alias(output_root / "process-test-report.json", process)
    validate_process_report(process, store)
    return {
        "source_media": source,
        "canonical_audio": canonical,
        "song_analysis": analysis,
        "stem_set": stems,
        "track_ir": track,
        "notation_ir": notation,
        "evaluation_report": evaluation,
        "process_report": process,
        "store": store,
        "metrics": metrics,
    }
