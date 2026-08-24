from __future__ import annotations

import copy
import datetime as dt
import math
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Sequence

from p0.contracts import (
    ContractError,
    artifact_id_for,
    create_artifact,
    default_generator,
    runtime_environment,
    source_reference,
    validate_artifact,
)
from p0.provenance import ArtifactStore, IntegrityError


FAILURE_FAMILIES = (
    "contract_malformation",
    "integrity_tamper_stale",
    "evaluator_numeric",
    "reproducibility_cross_run",
    "coverage_skip_gate",
    "contamination_taint",
)


class ReportError(ValueError):
    def __init__(self, code: str, detail: str) -> None:
        self.code = code
        self.detail = detail
        super().__init__("%s: %s" % (code, detail))

    def as_dict(self) -> Dict[str, Any]:
        return {"family": "contract_malformation", "code": self.code, "detail": self.detail}


def _normalize_check(check: Mapping[str, Any]) -> Dict[str, Any]:
    normalized = copy.deepcopy(dict(check))
    normalized.setdefault("numerator", 1 if normalized.get("passed") else 0)
    normalized.setdefault("denominator", 1)
    normalized.setdefault("metric_version", "p0-gate/1.0.0")
    normalized.setdefault("tolerance", 0.0)
    return normalized


def build_process_report(
    run_id: str,
    evaluation_reports: Sequence[Mapping[str, Any]],
    store: ArtifactStore,
    checks: Sequence[Mapping[str, Any]],
    status: str,
    failure_family: Optional[str] = None,
    failure_reason: Optional[str] = None,
    candidate_sha: str = "not-official-run",
    dirty_tree_before_run: bool = False,
    test_case_id: str = "p0-deterministic-flow",
    input_checksum: str = "0" * 64,
    expected_checks: Optional[Sequence[str]] = None,
    executed_checks: Optional[Sequence[str]] = None,
    artifact_paths: Optional[Sequence[str]] = None,
    log_references: Optional[Sequence[Mapping[str, Any]]] = None,
    created_at: str = "2000-01-01T00:00:01Z",
) -> Dict[str, Any]:
    if failure_family is not None and failure_family not in FAILURE_FAMILIES:
        raise ReportError("unknown_failure_family", failure_family)
    normalized_checks = [_normalize_check(check) for check in checks]
    check_ids = [check["id"] for check in normalized_checks]
    expected = list(expected_checks if expected_checks is not None else check_ids)
    executed = list(executed_checks if executed_checks is not None else check_ids)
    process_id = artifact_id_for("ProcessTestReport", run_id)
    for evaluation in evaluation_reports:
        if evaluation["payload"].get("process_test_report_id") != process_id:
            raise ReportError(
                "crosslink",
                "evaluation %s links %s instead of %s"
                % (evaluation["artifact_id"], evaluation["payload"].get("process_test_report_id"), process_id),
            )
        if evaluation["payload"].get("run_id") != run_id:
            raise ReportError("crosslink", "evaluation and process report run_id differ")
    failure = None
    if status != "success":
        if not failure_family or not failure_reason:
            raise ReportError("missing_failure_reason", "failed report needs family and reason")
        failure = {"family": failure_family, "code": "gate_failed", "reason": failure_reason}
    payload = {
        "run_id": run_id,
        "test_case_id": test_case_id,
        "input_checksum": input_checksum,
        "dataset_version": "p0-fixtures/1.0.0",
        "stages": ["source", "canonical", "analysis", "stems", "track", "notation", "evaluation", "gate"],
        "versions": {
            "fixture": "p0-fixtures/1.0.0",
            "schema": "1.0.0",
            "evaluator": "p0-event-metrics/1.0.0",
            "program": "p0-verifier/1.0.0",
            "model": "deterministic-no-model/stub-1.0.0",
            "parameters": "seed=20260824;quantization=none",
            "seed": 20260824,
        },
        "timing": {"started_at": "2000-01-01T00:00:00Z", "ended_at": created_at},
        "execution_environment": runtime_environment(),
        "artifact_paths": list(artifact_paths or ["process-test-report.json"]),
        "log_references": [copy.deepcopy(dict(item)) for item in (log_references or [])],
        "checks": normalized_checks,
        "evaluation_reports": [source_reference(item) for item in evaluation_reports],
        "automatic_benchmark": True,
        "expected_checks": expected,
        "executed_checks": executed,
        "candidate_sha": candidate_sha,
        "dirty_tree_before_run": bool(dirty_tree_before_run),
    }
    return create_artifact(
        "ProcessTestReport",
        payload,
        source_artifacts=tuple(evaluation_reports),
        status=status,
        failure=failure,
        generator=default_generator(),
        created_at=created_at,
        environment=runtime_environment(),
        logical_key=run_id,
        artifact_id=process_id,
    )


def validate_process_report(report: Mapping[str, Any], store: ArtifactStore) -> Dict[str, Any]:
    payload = report.get("payload")
    if not isinstance(payload, dict):
        raise ReportError("missing_report_fact", "payload")
    required_check_fields = ("id", "actual", "threshold", "passed", "numerator", "denominator", "metric_version")
    checks = payload.get("checks")
    if not isinstance(checks, list) or not checks:
        raise ReportError("missing_report_fact", "checks must be non-empty")
    for index, check in enumerate(checks):
        for field in required_check_fields:
            if field not in check:
                raise ReportError("missing_report_fact", "checks[%d].%s" % (index, field))
        actual = check["actual"]
        threshold = check["threshold"]
        if not isinstance(actual, (int, float)) or not math.isfinite(float(actual)):
            raise ReportError("non_finite_metric", "checks[%d].actual" % index)
        if not isinstance(threshold, (int, float)) or not math.isfinite(float(threshold)):
            raise ReportError("non_finite_metric", "checks[%d].threshold" % index)
        if actual < threshold and check["passed"] is True:
            raise ReportError("below_threshold_false_pass", check["id"])
        if actual >= threshold and check["passed"] is False and report.get("status") == "success":
            raise ReportError("false_rejection", check["id"])
    expected = payload.get("expected_checks")
    executed = payload.get("executed_checks")
    if not isinstance(expected, list) or not expected:
        raise ReportError("empty_required_group", "expected_checks")
    if expected != executed:
        raise ReportError("coverage_mismatch", "expected=%r executed=%r" % (expected, executed))
    if report.get("status") == "success" and any(not check["passed"] for check in checks):
        raise ReportError("failed_check_false_pass", "successful report contains failed check")
    if report.get("status") != "success":
        failure = report.get("failure")
        if not isinstance(failure, dict) or not failure.get("reason") or failure.get("family") not in FAILURE_FAMILIES:
            raise ReportError("missing_failure_reason", repr(failure))

    output_root = store.root.parent
    for relative in payload.get("artifact_paths", []):
        target = output_root / relative
        if not target.is_file():
            raise ReportError("missing_evidence", str(target))
    for reference in payload.get("log_references", []):
        relative = reference.get("path")
        checksum = reference.get("sha256")
        if not isinstance(relative, str) or not isinstance(checksum, str):
            raise ReportError("missing_report_fact", "log reference path/checksum")
        target = output_root / relative
        if not target.is_file():
            raise ReportError("missing_evidence", str(target))
        from p0.fixtures import file_sha256

        observed = file_sha256(target)
        if observed != checksum:
            raise ReportError("evidence_checksum_mismatch", "%s recorded=%s observed=%s" % (relative, checksum, observed))

    registry = store.registry()
    try:
        validated = validate_artifact(report, registry=registry)
    except ContractError as error:
        if error.code == "checksum_mismatch":
            raise ReportError("evidence_checksum_mismatch", str(error))
        raise ReportError(error.code, str(error))
    for reference in payload["evaluation_reports"]:
        try:
            evaluation = store.get(reference["artifact_id"])
        except IntegrityError as error:
            raise ReportError("missing_evidence", str(error))
        if evaluation["content_hash"] != reference["content_hash"]:
            raise ReportError("evidence_checksum_mismatch", reference["artifact_id"])
        if payload["automatic_benchmark"]:
            try:
                store.assert_automatic_lineage(evaluation["artifact_id"])
            except IntegrityError as error:
                raise ReportError("human_correction_taint", str(error))
    return validated
