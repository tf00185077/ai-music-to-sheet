from __future__ import annotations

import copy
import datetime as dt
import hashlib
import json
import math
import platform
import re
import uuid
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, MutableMapping, Optional, Sequence, Tuple


ARTIFACT_TYPES: Tuple[str, ...] = (
    "SourceMedia",
    "CanonicalAudio",
    "SongAnalysis",
    "StemSet",
    "TrackIR",
    "NotationIR",
    "EvaluationReport",
    "ProcessTestReport",
)
SUPPORTED_SCHEMA_MAJOR = 1
STATUSES = ("success", "low_confidence", "failed", "needs_human_confirmation")
FACT_STATES = ("known", "unknown", "low_confidence")
MODES = ("transcription", "arrangement")
INSTRUMENTS = ("drums", "piano", "guitar")
_SEMVER = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_NAMESPACE = uuid.UUID("a7b95ec4-62fd-4b66-a7da-9bbeb743c7ac")


class ContractError(ValueError):
    def __init__(
        self,
        code: str,
        field: str,
        expected: Any,
        observed: Any,
        message: Optional[str] = None,
    ) -> None:
        self.code = code
        self.field = field
        self.expected = expected
        self.observed = observed
        super().__init__(message or "%s at %s: expected %r, observed %r" % (code, field, expected, observed))

    def as_dict(self) -> Dict[str, Any]:
        return {
            "family": "contract_malformation",
            "code": self.code,
            "field": self.field,
            "expected": self.expected,
            "observed": self.observed,
            "message": str(self),
        }


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_json(value: Any) -> str:
    return sha256_bytes(canonical_json(value).encode("utf-8"))


def artifact_id_for(artifact_type: str, logical_key: str) -> str:
    if artifact_type not in ARTIFACT_TYPES:
        raise ContractError("enum", "artifact_type", ARTIFACT_TYPES, artifact_type)
    return "%s:%s" % (artifact_type.lower(), uuid.uuid5(_NAMESPACE, "%s:%s" % (artifact_type, logical_key)))


def runtime_environment() -> Dict[str, str]:
    return {
        "runtime": "python-%s" % platform.python_version(),
        "os": platform.system() or "unknown",
        "architecture": platform.machine() or "unknown",
    }


def default_generator() -> Dict[str, Any]:
    return {
        "name": "p0-deterministic-stub",
        "program_version": "1.0.0",
        "code_version": "runtime-git-sha",
        "model_name": "deterministic-no-model",
        "model_version": "stub-1.0.0",
        "parameters": {"seed": 20260824, "quantization": "none"},
    }


def known_fact(value: Any, confidence: float = 1.0) -> Dict[str, Any]:
    return {"state": "known", "value": value, "confidence": confidence}


def unknown_fact() -> Dict[str, Any]:
    return {"state": "unknown", "value": None, "confidence": None}


def low_confidence_fact(value: Any, confidence: float) -> Dict[str, Any]:
    return {"state": "low_confidence", "value": value, "confidence": confidence}


def _integrity_material(artifact: Mapping[str, Any]) -> Dict[str, Any]:
    material = copy.deepcopy(dict(artifact))
    material.pop("content_hash", None)
    return material


def refresh_integrity(artifact: MutableMapping[str, Any]) -> MutableMapping[str, Any]:
    artifact["content_hash"] = sha256_json(_integrity_material(artifact))
    return artifact


def _cache_key(artifact: Mapping[str, Any]) -> str:
    generator = artifact.get("generator", {})
    payload = artifact.get("payload", {})
    return sha256_json(
        {
            "content_hash": sha256_json(payload),
            "model": [generator.get("model_name"), generator.get("model_version")],
            "parameters": generator.get("parameters"),
            "schema_version": artifact.get("schema_version"),
            "mode": payload.get("mode", payload.get("track_mode")),
        }
    )


def source_reference(artifact: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "artifact_id": artifact["artifact_id"],
        "artifact_type": artifact["artifact_type"],
        "content_hash": artifact["content_hash"],
        "validity_key": _cache_key(artifact),
    }


def create_artifact(
    artifact_type: str,
    payload: Mapping[str, Any],
    source_artifacts: Sequence[Mapping[str, Any]] = (),
    status: str = "success",
    confidence: Optional[Mapping[str, Any]] = None,
    failure: Optional[Mapping[str, Any]] = None,
    generator: Optional[Mapping[str, Any]] = None,
    created_at: str = "2000-01-01T00:00:00Z",
    environment: Optional[Mapping[str, str]] = None,
    human_correction: bool = False,
    logical_key: Optional[str] = None,
    schema_version: str = "1.0.0",
    migration: Optional[Mapping[str, Any]] = None,
    artifact_id: Optional[str] = None,
) -> Dict[str, Any]:
    logical_key = logical_key or sha256_json(payload)
    artifact: Dict[str, Any] = {
        "artifact_type": artifact_type,
        "artifact_id": artifact_id or artifact_id_for(artifact_type, logical_key),
        "content_hash": "",
        "schema_version": schema_version,
        "source_artifact_ids": [item["artifact_id"] for item in source_artifacts],
        "source_artifacts": [source_reference(item) for item in source_artifacts],
        "generator": copy.deepcopy(dict(generator or default_generator())),
        "created_at": created_at,
        "environment": copy.deepcopy(dict(environment or {"runtime": "python-stdlib", "os": "portable", "architecture": "unknown"})),
        "status": status,
        "confidence": copy.deepcopy(dict(confidence or known_fact(1.0))),
        "failure": copy.deepcopy(dict(failure)) if failure is not None else None,
        "human_correction": bool(human_correction),
        "migration": copy.deepcopy(dict(migration)) if migration is not None else None,
        "payload": copy.deepcopy(dict(payload)),
    }
    refresh_integrity(artifact)
    return artifact


def _require(mapping: Mapping[str, Any], key: str, field: str) -> Any:
    if key not in mapping:
        raise ContractError("required", "%s.%s" % (field, key) if field else key, "present", "missing")
    return mapping[key]


def _expect_type(value: Any, expected_type: Any, field: str) -> None:
    if expected_type is int:
        valid = isinstance(value, int) and not isinstance(value, bool)
    elif expected_type is float:
        valid = isinstance(value, (int, float)) and not isinstance(value, bool)
    else:
        valid = isinstance(value, expected_type)
    if not valid:
        name = expected_type.__name__ if hasattr(expected_type, "__name__") else str(expected_type)
        raise ContractError("type", field, name, type(value).__name__)


def _expect_enum(value: Any, choices: Iterable[Any], field: str) -> None:
    choices_tuple = tuple(choices)
    if value not in choices_tuple:
        raise ContractError("enum", field, choices_tuple, value)


def _expect_range(value: Any, minimum: float, maximum: float, field: str) -> None:
    _expect_type(value, float, field)
    if not math.isfinite(float(value)) or not minimum <= float(value) <= maximum:
        raise ContractError("range", field, "[%s, %s] finite" % (minimum, maximum), value)


def _parse_version(version: Any, field: str = "schema_version") -> Tuple[int, int, int]:
    _expect_type(version, str, field)
    match = _SEMVER.match(version)
    if not match:
        raise ContractError("format", field, "MAJOR.MINOR.PATCH", version)
    return tuple(int(part) for part in match.groups())  # type: ignore[return-value]


def _validate_fact(fact: Any, field: str) -> None:
    _expect_type(fact, dict, field)
    state = _require(fact, "state", field)
    _expect_enum(state, FACT_STATES, field + ".state")
    value = _require(fact, "value", field)
    confidence = _require(fact, "confidence", field)
    if state == "unknown":
        if value is not None or confidence is not None:
            raise ContractError("hidden_default", field, {"value": None, "confidence": None}, fact)
    else:
        if value is None:
            raise ContractError("required", field + ".value", "non-null", None)
        _expect_range(confidence, 0.0, 1.0, field + ".confidence")


def _validate_common(artifact: Mapping[str, Any]) -> None:
    for key in (
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
    ):
        _require(artifact, key, "")
    _expect_enum(artifact["artifact_type"], ARTIFACT_TYPES, "artifact_type")
    _expect_type(artifact["artifact_id"], str, "artifact_id")
    _expect_type(artifact["content_hash"], str, "content_hash")
    if artifact["content_hash"] and not _SHA256.match(artifact["content_hash"]):
        raise ContractError("format", "content_hash", "64 lowercase hex characters", artifact["content_hash"])
    major, _, _ = _parse_version(artifact["schema_version"])
    if major != SUPPORTED_SCHEMA_MAJOR:
        raise ContractError("unsupported_major", "schema_version", SUPPORTED_SCHEMA_MAJOR, major)
    _expect_type(artifact["source_artifact_ids"], list, "source_artifact_ids")
    _expect_type(artifact["source_artifacts"], list, "source_artifacts")
    _expect_type(artifact["generator"], dict, "generator")
    for field in ("name", "program_version", "code_version", "model_name", "model_version", "parameters"):
        _require(artifact["generator"], field, "generator")
    _expect_type(artifact["generator"]["parameters"], dict, "generator.parameters")
    _expect_type(artifact["created_at"], str, "created_at")
    try:
        dt.datetime.fromisoformat(artifact["created_at"].replace("Z", "+00:00"))
    except ValueError:
        raise ContractError("format", "created_at", "ISO-8601 timestamp", artifact["created_at"])
    _expect_type(artifact["environment"], dict, "environment")
    for field in ("runtime", "os", "architecture"):
        _require(artifact["environment"], field, "environment")
    _expect_enum(artifact["status"], STATUSES, "status")
    _validate_fact(artifact["confidence"], "confidence")
    _expect_type(artifact["human_correction"], bool, "human_correction")
    _expect_type(artifact["payload"], dict, "payload")
    if artifact["status"] == "success" and artifact["failure"] is not None:
        raise ContractError("state_transition", "failure", None, artifact["failure"])
    if artifact["status"] != "success" and artifact["failure"] is None:
        raise ContractError("state_transition", "failure", "structured reason for non-success state", None)
    if artifact["failure"] is not None:
        _expect_type(artifact["failure"], dict, "failure")
        _require(artifact["failure"], "family", "failure")
        _require(artifact["failure"], "code", "failure")
        _require(artifact["failure"], "reason", "failure")


def _validate_source_media(payload: Mapping[str, Any]) -> None:
    _expect_enum(_require(payload, "file_format", "payload"), ("wav", "flac", "mp3", "mp4", "midi-rendered-wav"), "payload.file_format")
    _expect_range(_require(payload, "byte_size", "payload"), 1, 10 ** 12, "payload.byte_size")
    _expect_range(_require(payload, "track_count", "payload"), 1, 1024, "payload.track_count")
    _expect_type(_require(payload, "source_identifier", "payload"), str, "payload.source_identifier")
    checksum = _require(payload, "media_sha256", "payload")
    _expect_type(checksum, str, "payload.media_sha256")
    if not _SHA256.match(checksum):
        raise ContractError("format", "payload.media_sha256", "sha256", checksum)


def _validate_canonical_audio(payload: Mapping[str, Any]) -> None:
    _expect_range(_require(payload, "sample_rate", "payload"), 1, 384000, "payload.sample_rate")
    channels = _require(payload, "channel_layout", "payload")
    _expect_type(channels, list, "payload.channel_layout")
    if not channels:
        raise ContractError("range", "payload.channel_layout", "at least one channel", channels)
    _expect_enum(_require(payload, "sample_format", "payload"), ("pcm_s16le", "pcm_s24le", "float32"), "payload.sample_format")
    _expect_range(_require(payload, "duration_seconds", "payload"), 0.000001, 10 ** 7, "payload.duration_seconds")


def _validate_song_analysis(payload: Mapping[str, Any]) -> None:
    tempo_map = _require(payload, "tempo_map", "payload")
    _expect_type(tempo_map, list, "payload.tempo_map")
    if not tempo_map:
        raise ContractError("range", "payload.tempo_map", "non-empty", tempo_map)
    for index, tempo in enumerate(tempo_map):
        _expect_range(_require(tempo, "time_seconds", "tempo"), 0, 10 ** 7, "payload.tempo_map[%d].time_seconds" % index)
        _expect_range(_require(tempo, "bpm", "tempo"), 1, 1000, "payload.tempo_map[%d].bpm" % index)
        _validate_fact(_require(tempo, "confidence", "tempo"), "payload.tempo_map[%d].confidence" % index)
    for name in ("beats", "downbeats", "sections"):
        _expect_type(_require(payload, name, "payload"), list, "payload.%s" % name)
    _validate_fact(_require(payload, "meter", "payload"), "payload.meter")
    _validate_fact(_require(payload, "key", "payload"), "payload.key")


def _validate_stem_set(payload: Mapping[str, Any]) -> None:
    _expect_type(_require(payload, "taxonomy_version", "payload"), str, "payload.taxonomy_version")
    stems = _require(payload, "stems", "payload")
    _expect_type(stems, list, "payload.stems")
    if not stems:
        raise ContractError("range", "payload.stems", "non-empty", stems)
    for index, stem in enumerate(stems):
        _expect_enum(_require(stem, "instrument", "stem"), INSTRUMENTS + ("other",), "payload.stems[%d].instrument" % index)
        _expect_type(_require(stem, "path", "stem"), str, "payload.stems[%d].path" % index)
        checksum = _require(stem, "sha256", "stem")
        if not isinstance(checksum, str) or not _SHA256.match(checksum):
            raise ContractError("format", "payload.stems[%d].sha256" % index, "sha256", checksum)
        _expect_enum(
            _require(stem, "presence", "stem"),
            ("present", "absent", "low_volume", "partial_presence", "masked", "unknown"),
            "payload.stems[%d].presence" % index,
        )
        _validate_fact(_require(stem, "confidence", "stem"), "payload.stems[%d].confidence" % index)


def _validate_time_event(event: Mapping[str, Any], field: str) -> None:
    _expect_range(_require(event, "onset_seconds", field), 0, 10 ** 7, field + ".onset_seconds")
    if "offset_seconds" in event:
        _expect_range(event["offset_seconds"], 0, 10 ** 7, field + ".offset_seconds")
        if event["offset_seconds"] < event["onset_seconds"]:
            raise ContractError("range", field + ".offset_seconds", ">= onset_seconds", event["offset_seconds"])
    if "pitch" in event:
        _expect_range(event["pitch"], 0, 127, field + ".pitch")
    _expect_range(_require(event, "velocity", field), 1, 127, field + ".velocity")
    _validate_fact(_require(event, "confidence", field), field + ".confidence")


def _validate_track_ir(
    payload: Mapping[str, Any],
    registry: Optional[Mapping[str, Mapping[str, Any]]] = None,
) -> None:
    mode = _require(payload, "mode", "payload")
    instrument = _require(payload, "instrument", "payload")
    _expect_enum(mode, MODES, "payload.mode")
    _expect_enum(instrument, INSTRUMENTS, "payload.instrument")
    events = _require(payload, "events", "payload")
    _expect_type(events, list, "payload.events")
    if not events:
        raise ContractError("range", "payload.events", "non-empty", events)
    _validate_fact(_require(payload, "instrument_presence", "payload"), "payload.instrument_presence")
    for index, event in enumerate(events):
        field = "payload.events[%d]" % index
        _validate_time_event(event, field)
        if mode == "transcription":
            evidence = event.get("evidence")
            if not isinstance(evidence, list) or not evidence:
                raise ContractError("mode_provenance", field + ".evidence", "non-empty audio/stem evidence", evidence)
            if "arrangement_decision" in event:
                raise ContractError("cross_mode", field, "transcription evidence only", "arrangement_decision")
            for evidence_index, item in enumerate(evidence):
                evidence_id = _require(item, "artifact_id", "evidence")
                _expect_type(evidence_id, str, "%s.evidence[%d].artifact_id" % (field, evidence_index))
                start = _require(item, "start_seconds", "evidence")
                end = _require(item, "end_seconds", "evidence")
                _expect_range(start, 0, 10 ** 7, "%s.evidence[%d].start_seconds" % (field, evidence_index))
                _expect_range(end, 0, 10 ** 7, "%s.evidence[%d].end_seconds" % (field, evidence_index))
                if end < start:
                    raise ContractError("range", "%s.evidence[%d]" % (field, evidence_index), "end >= start", item)
                if item.get("stem_instrument") != instrument:
                    raise ContractError("incompatible_evidence", "%s.evidence[%d].stem_instrument" % (field, evidence_index), instrument, item.get("stem_instrument"))
                if registry is not None:
                    if evidence_id not in registry:
                        raise ContractError("missing_evidence", "%s.evidence[%d].artifact_id" % (field, evidence_index), "resolvable CanonicalAudio or StemSet", evidence_id)
                    evidence_artifact = registry[evidence_id]
                    if evidence_artifact.get("artifact_type") not in ("CanonicalAudio", "StemSet"):
                        raise ContractError("incompatible_evidence", "%s.evidence[%d].artifact_type" % (field, evidence_index), ("CanonicalAudio", "StemSet"), evidence_artifact.get("artifact_type"))
                    canonical = evidence_artifact if evidence_artifact.get("artifact_type") == "CanonicalAudio" else None
                    if canonical is None:
                        for source_id in evidence_artifact.get("source_artifact_ids", []):
                            candidate = registry.get(source_id)
                            if candidate is not None and candidate.get("artifact_type") == "CanonicalAudio":
                                canonical = candidate
                                break
                    if canonical is None:
                        raise ContractError("missing_evidence", "%s.evidence[%d]" % (field, evidence_index), "StemSet with resolvable CanonicalAudio", evidence_id)
                    duration = canonical.get("payload", {}).get("duration_seconds")
                    if not isinstance(duration, (int, float)) or end > duration + 1e-12:
                        raise ContractError("evidence_out_of_bounds", "%s.evidence[%d].end_seconds" % (field, evidence_index), "<= %.9f" % float(duration or 0), end)
        else:
            decision = event.get("arrangement_decision")
            if not isinstance(decision, dict) or not decision.get("rule") or not decision.get("reason"):
                raise ContractError("mode_provenance", field + ".arrangement_decision", "rule and reason", decision)
            if "evidence" in event:
                raise ContractError("cross_mode", field, "arrangement decision only", "evidence")
        if instrument == "drums":
            forbidden = sorted(set(event) & {"pitch", "voice", "hand", "pedal", "string", "fret", "tuning", "capo"})
            if forbidden:
                raise ContractError("instrument_shape", field, "drums fields only", forbidden)
            _expect_enum(_require(event, "drum_class", field), ("kick", "snare", "closed_hihat", "open_hihat", "tom", "crash", "ride"), field + ".drum_class")
            _validate_fact(_require(event, "technique", field), field + ".technique")
        elif instrument == "piano":
            forbidden = sorted(set(event) & {"drum_class", "string", "fret", "tuning", "capo", "technique"})
            if forbidden:
                raise ContractError("instrument_shape", field, "piano fields only", forbidden)
            _expect_range(_require(event, "pitch", field), 0, 127, field + ".pitch")
            _expect_range(_require(event, "voice", field), 1, 32, field + ".voice")
            _validate_fact(_require(event, "hand", field), field + ".hand")
            _validate_fact(_require(event, "pedal", field), field + ".pedal")
        else:
            forbidden = sorted(set(event) & {"drum_class", "voice", "hand", "pedal"})
            if forbidden:
                raise ContractError("instrument_shape", field, "guitar fields only", forbidden)
            _expect_range(_require(event, "pitch", field), 0, 127, field + ".pitch")
            _validate_fact(_require(event, "string", field), field + ".string")
            _validate_fact(_require(event, "fret", field), field + ".fret")
            tuning = _require(event, "tuning", field)
            _expect_type(tuning, list, field + ".tuning")
            if len(tuning) != 6:
                raise ContractError("instrument_shape", field + ".tuning", "six strings", len(tuning))
            for tuning_index, fact in enumerate(tuning):
                _validate_fact(fact, "%s.tuning[%d]" % (field, tuning_index))
            _validate_fact(_require(event, "capo", field), field + ".capo")
            _validate_fact(_require(event, "technique", field), field + ".technique")


def _validate_notation_ir(payload: Mapping[str, Any]) -> None:
    _expect_enum(_require(payload, "track_mode", "payload"), MODES, "payload.track_mode")
    _expect_enum(_require(payload, "instrument", "payload"), INSTRUMENTS, "payload.instrument")
    measures = _require(payload, "measures", "payload")
    _expect_type(measures, list, "payload.measures")
    if not measures:
        raise ContractError("range", "payload.measures", "non-empty", measures)
    for index, measure in enumerate(measures):
        _expect_range(_require(measure, "number", "measure"), 1, 1000000, "payload.measures[%d].number" % index)
        _expect_type(_require(measure, "voices", "measure"), list, "payload.measures[%d].voices" % index)
        _expect_type(_require(measure, "meter", "measure"), dict, "payload.measures[%d].meter" % index)
        _expect_type(_require(measure, "tempo", "measure"), dict, "payload.measures[%d].tempo" % index)
    _expect_type(_require(payload, "staff", "payload"), list, "payload.staff")
    _expect_type(_require(payload, "ties", "payload"), list, "payload.ties")
    _expect_type(_require(payload, "instrument_notation", "payload"), dict, "payload.instrument_notation")


def _validate_evaluation_report(payload: Mapping[str, Any]) -> None:
    for field in ("run_id", "dataset_version", "evaluated_artifact_ids", "evaluator", "metrics", "thresholds", "artifact_paths", "process_test_report_id"):
        _require(payload, field, "payload")
    _expect_type(payload["evaluator"], dict, "payload.evaluator")
    for field in ("name", "version", "tolerance_seconds", "tolerance_rule", "matching_rule", "empty_set_policy"):
        _require(payload["evaluator"], field, "payload.evaluator")
    _expect_range(payload["evaluator"]["tolerance_seconds"], 0, 60, "payload.evaluator.tolerance_seconds")
    _expect_type(payload["metrics"], dict, "payload.metrics")
    for name, value in payload["metrics"].items():
        if isinstance(value, (int, float)) and not math.isfinite(float(value)):
            raise ContractError("non_finite", "payload.metrics.%s" % name, "finite", value)


def _validate_process_test_report(payload: Mapping[str, Any]) -> None:
    for field in (
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
    ):
        _require(payload, field, "payload")
    for name in ("stages", "artifact_paths", "log_references", "checks", "evaluation_reports", "expected_checks", "executed_checks"):
        _expect_type(payload[name], list, "payload.%s" % name)
    _expect_type(payload["versions"], dict, "payload.versions")
    _expect_type(payload["timing"], dict, "payload.timing")
    _expect_type(payload["execution_environment"], dict, "payload.execution_environment")
    _expect_type(payload["automatic_benchmark"], bool, "payload.automatic_benchmark")
    _expect_type(payload["dirty_tree_before_run"], bool, "payload.dirty_tree_before_run")
    for index, check in enumerate(payload["checks"]):
        for field in ("id", "actual", "threshold", "passed", "numerator", "denominator", "metric_version"):
            _require(check, field, "payload.checks[%d]" % index)
        if check["denominator"] <= 0:
            raise ContractError("empty_required_group", "payload.checks[%d].denominator" % index, "> 0", check["denominator"])


_PAYLOAD_VALIDATORS = {
    "SourceMedia": _validate_source_media,
    "CanonicalAudio": _validate_canonical_audio,
    "SongAnalysis": _validate_song_analysis,
    "StemSet": _validate_stem_set,
    "TrackIR": _validate_track_ir,
    "NotationIR": _validate_notation_ir,
    "EvaluationReport": _validate_evaluation_report,
    "ProcessTestReport": _validate_process_test_report,
}


_UPSTREAM_RULES = {
    "SourceMedia": set(),
    "CanonicalAudio": {"SourceMedia"},
    "SongAnalysis": {"CanonicalAudio"},
    "StemSet": {"CanonicalAudio"},
    "TrackIR": {"SongAnalysis", "StemSet"},
    "NotationIR": {"TrackIR"},
    "EvaluationReport": {"NotationIR"},
    "ProcessTestReport": {"EvaluationReport"},
}


def _validate_sources(artifact: Mapping[str, Any], registry: Optional[Mapping[str, Mapping[str, Any]]]) -> None:
    ids = artifact["source_artifact_ids"]
    references = artifact["source_artifacts"]
    reference_ids = [reference.get("artifact_id") for reference in references]
    if ids != reference_ids:
        raise ContractError("source_index", "source_artifact_ids", reference_ids, ids)
    allowed = _UPSTREAM_RULES[artifact["artifact_type"]]
    migration_source = artifact.get("migration") is not None
    if migration_source:
        allowed = set(allowed) | {artifact["artifact_type"]}
    observed_types = {reference.get("artifact_type") for reference in references}
    if artifact["artifact_type"] == "SourceMedia" and references:
        raise ContractError("incompatible_upstream", "source_artifacts", [], references)
    if observed_types and not observed_types.issubset(allowed):
        raise ContractError("incompatible_upstream", "source_artifacts.artifact_type", sorted(allowed), sorted(observed_types))
    failed_process_report = artifact["artifact_type"] == "ProcessTestReport" and artifact["status"] != "success"
    if artifact["artifact_type"] != "SourceMedia" and not references and not failed_process_report:
        raise ContractError("required", "source_artifacts", "at least one compatible upstream", references)
    required_types = _UPSTREAM_RULES[artifact["artifact_type"]]
    if not migration_source and not failed_process_report and observed_types != required_types:
        raise ContractError(
            "missing_required_upstream",
            "source_artifacts.artifact_type",
            sorted(required_types),
            sorted(observed_types),
        )
    for index, reference in enumerate(references):
        for field in ("artifact_id", "artifact_type", "content_hash", "validity_key"):
            _require(reference, field, "source_artifacts[%d]" % index)
        if registry is None:
            continue
        source_id = reference["artifact_id"]
        if source_id not in registry:
            raise ContractError("missing_upstream", "source_artifacts[%d].artifact_id" % index, "resolvable ID", source_id)
        current = registry[source_id]
        if current.get("artifact_type") != reference["artifact_type"] or current.get("artifact_type") not in allowed:
            raise ContractError("incompatible_upstream", "source_artifacts[%d].artifact_type" % index, reference["artifact_type"], current.get("artifact_type"))
        observed_hash = sha256_json(_integrity_material(current))
        if observed_hash != current.get("content_hash"):
            raise ContractError("checksum_mismatch", "source_artifacts[%d].content_hash" % index, current.get("content_hash"), observed_hash)
        if reference["content_hash"] != current.get("content_hash"):
            raise ContractError("checksum_mismatch", "source_artifacts[%d].content_hash" % index, reference["content_hash"], current.get("content_hash"))
        current_key = _cache_key(current)
        if reference["validity_key"] != current_key:
            raise ContractError("stale_cache", "source_artifacts[%d].validity_key" % index, reference["validity_key"], current_key)


def _validate_crosslinks(artifact: Mapping[str, Any], registry: Optional[Mapping[str, Mapping[str, Any]]]) -> None:
    if registry is None:
        return
    if artifact["artifact_type"] == "ProcessTestReport":
        for index, reference in enumerate(artifact["payload"]["evaluation_reports"]):
            evaluation_id = reference.get("artifact_id")
            if evaluation_id not in registry:
                raise ContractError("missing_upstream", "payload.evaluation_reports[%d].artifact_id" % index, "resolvable EvaluationReport", evaluation_id)
            evaluation = registry[evaluation_id]
            if evaluation.get("artifact_type") != "EvaluationReport":
                raise ContractError("incompatible_upstream", "payload.evaluation_reports[%d]" % index, "EvaluationReport", evaluation.get("artifact_type"))
            if reference.get("content_hash") != evaluation.get("content_hash"):
                raise ContractError("checksum_mismatch", "payload.evaluation_reports[%d].content_hash" % index, reference.get("content_hash"), evaluation.get("content_hash"))
            if evaluation["payload"].get("process_test_report_id") != artifact["artifact_id"]:
                raise ContractError("crosslink", "payload.evaluation_reports[%d]" % index, artifact["artifact_id"], evaluation["payload"].get("process_test_report_id"))


def validate_artifact(
    artifact: Mapping[str, Any],
    registry: Optional[Mapping[str, Mapping[str, Any]]] = None,
) -> Dict[str, Any]:
    _expect_type(artifact, dict, "artifact")
    _validate_common(artifact)
    if artifact["artifact_type"] == "TrackIR":
        _validate_track_ir(artifact["payload"], registry=registry)
    else:
        _PAYLOAD_VALIDATORS[artifact["artifact_type"]](artifact["payload"])
    _validate_sources(artifact, registry)
    _validate_crosslinks(artifact, registry)
    observed_hash = sha256_json(_integrity_material(artifact))
    if artifact["content_hash"] != observed_hash:
        raise ContractError("checksum_mismatch", "content_hash", artifact["content_hash"], observed_hash)
    return copy.deepcopy(dict(artifact))


def write_artifact(path: Path, artifact: Mapping[str, Any]) -> None:
    validate_artifact(artifact)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(artifact, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def read_artifact(path: Path, registry: Optional[Mapping[str, Mapping[str, Any]]] = None) -> Dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ContractError("serialization", str(path), "readable JSON", str(error))
    return validate_artifact(value, registry=registry)


def _strip_absolute_paths(value: Any) -> Any:
    if isinstance(value, dict):
        result = {}
        for key, item in value.items():
            if key in ("created_at", "environment"):
                continue
            if key == "path" or key.endswith("_path"):
                if isinstance(item, str) and Path(item).is_absolute():
                    result[key] = "<absolute-path>"
                else:
                    result[key] = item
            else:
                result[key] = _strip_absolute_paths(item)
        return result
    if isinstance(value, list):
        return [_strip_absolute_paths(item) for item in value]
    return value


def semantic_view(artifact: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "artifact_type": artifact.get("artifact_type"),
        "payload": _strip_absolute_paths(copy.deepcopy(artifact.get("payload", {}))),
    }


def semantically_equal(left: Mapping[str, Any], right: Mapping[str, Any]) -> bool:
    return canonical_json(semantic_view(left)) == canonical_json(semantic_view(right))


def migrate_legacy_artifact(legacy: Mapping[str, Any], target_version: str = "1.0.0") -> Dict[str, Any]:
    major, _, _ = _parse_version(legacy.get("schema_version"), "legacy.schema_version")
    if major != 0:
        raise ContractError("migration_source", "legacy.schema_version", "0.x legacy vector", legacy.get("schema_version"))
    artifact_type = legacy.get("artifact_type")
    if artifact_type not in ARTIFACT_TYPES:
        raise ContractError("enum", "legacy.artifact_type", ARTIFACT_TYPES, artifact_type)
    _parse_version(target_version, "target_version")
    migrated = create_artifact(
        artifact_type,
        legacy.get("payload", {}),
        source_artifacts=(),
        schema_version=target_version,
        logical_key="migration:%s:%s" % (legacy.get("artifact_id"), target_version),
        migration={
            "source_artifact_id": legacy.get("artifact_id"),
            "source_schema_version": legacy.get("schema_version"),
            "source_snapshot": copy.deepcopy(dict(legacy)),
            "allowed_semantic_differences": [],
        },
    )
    # Legacy migrations are a special source-preserving adapter. The original is
    # embedded in migration metadata rather than treated as a v1 graph edge.
    if artifact_type != "SourceMedia" and not migrated["source_artifacts"]:
        # Normal validation requires an upstream for generated v1 artifacts; a
        # migration source is the explicit upstream at this boundary.
        migrated["source_artifact_ids"] = [legacy.get("artifact_id")]
        migrated["source_artifacts"] = [
            {
                "artifact_id": legacy.get("artifact_id"),
                "artifact_type": artifact_type,
                "content_hash": sha256_json(legacy),
                "validity_key": sha256_json({"legacy": legacy}),
            }
        ]
    refresh_integrity(migrated)
    return migrated
