from __future__ import annotations

import argparse
import copy
import json
import os
import shutil
import subprocess
import sys
import traceback
import unittest
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Set, Tuple

from p0.contracts import (
    artifact_id_for,
    create_artifact,
    refresh_integrity,
    runtime_environment,
)
from p0.fixtures import file_sha256
from p0.pipeline import run_mode_pipeline
from p0.provenance import ArtifactStore
from p0.reporting import FAILURE_FAMILIES, build_process_report, validate_process_report


TEST_MODULES = (
    "tests.test_contracts",
    "tests.test_fixtures",
    "tests.test_provenance",
    "tests.test_evaluators",
    "tests.test_pipeline_reports",
    "tests.test_delivery",
)
GROUP_NAMES = tuple("ABCDEFG")


def _git(command: Sequence[str], root: Path) -> str:
    result = subprocess.run(["git"] + list(command), cwd=str(root), capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError("git %s failed: %s" % (" ".join(command), result.stderr.strip()))
    return result.stdout.strip()


def _flatten_suite(suite: unittest.TestSuite) -> List[unittest.TestCase]:
    tests: List[unittest.TestCase] = []
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            tests.extend(_flatten_suite(item))
        else:
            tests.append(item)
    return tests


def _load_expected(root: Path) -> Tuple[List[Dict[str, Any]], List[str]]:
    path = root / "p0" / "expected-checks.json"
    value = json.loads(path.read_text(encoding="utf-8"))
    records = value.get("checks")
    if not isinstance(records, list) or not records:
        raise ValueError("expected-check manifest is empty")
    identifiers = [item.get("id") for item in records]
    if any(not isinstance(identifier, str) or not identifier for identifier in identifiers):
        raise ValueError("expected-check manifest contains an invalid ID")
    if len(set(identifiers)) != len(identifiers):
        raise ValueError("expected-check manifest contains duplicate IDs")
    groups = {item.get("group") for item in records}
    if groups != set(GROUP_NAMES):
        raise ValueError("expected-check manifest groups must be exactly A-G; observed %r" % groups)
    return records, sorted(identifiers)


def _failed_test_ids(result: unittest.TestResult) -> Set[str]:
    identifiers = {test.id() for test, _ in result.failures}
    identifiers.update(test.id() for test, _ in result.errors)
    identifiers.update(test.id() for test, _ in result.skipped)
    identifiers.update(test.id() for test in result.expectedFailures)
    identifiers.update(test.id() for test in result.unexpectedSuccesses)
    return identifiers


def _group_checks(records: Sequence[Mapping[str, Any]], failed: Set[str]) -> List[Dict[str, Any]]:
    checks = []
    for group in GROUP_NAMES:
        identifiers = [item["id"] for item in records if item["group"] == group]
        passed_count = sum(identifier not in failed for identifier in identifiers)
        denominator = len(identifiers)
        checks.append(
            {
                "id": "acceptance-group-%s" % group,
                "actual": float(passed_count) / float(denominator) if denominator else 0.0,
                "threshold": 1.0,
                "passed": denominator > 0 and passed_count == denominator,
                "numerator": passed_count,
                "denominator": denominator if denominator else 1,
                "metric_version": "p0-gate/1.0.0",
                "tolerance": 0.0,
            }
        )
    return checks


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def _failure_report(
    output: Path,
    candidate_sha: str,
    dirty: bool,
    family: str,
    reason: str,
    checks: Sequence[Mapping[str, Any]],
    expected: Sequence[str],
    executed: Sequence[str],
    log_path: Path,
) -> Dict[str, Any]:
    if family not in FAILURE_FAMILIES:
        family = "contract_malformation"
    safe_checks = list(checks) or [
        {
            "id": "gate-initialization",
            "actual": 0.0,
            "threshold": 1.0,
            "passed": False,
            "numerator": 0,
            "denominator": 1,
            "metric_version": "p0-gate/1.0.0",
            "tolerance": 0.0,
        }
    ]
    payload = {
        "run_id": "p0-full-verification",
        "test_case_id": "p0-full-gate-failure",
        "input_checksum": "0" * 64,
        "dataset_version": "p0-fixtures/1.0.0",
        "stages": ["gate"],
        "versions": {
            "fixture": "p0-fixtures/1.0.0",
            "schema": "1.0.0",
            "evaluator": "p0-event-metrics/1.0.0",
            "program": "p0-verifier/1.0.0",
            "model": "deterministic-no-model/stub-1.0.0",
            "parameters": "seed=20260824;quantization=none",
            "seed": 20260824,
        },
        "timing": {"started_at": "2000-01-01T00:00:00Z", "ended_at": "2000-01-01T00:00:01Z"},
        "execution_environment": runtime_environment(),
        "artifact_paths": ["process-test-report.json"],
        "log_references": [{"path": "verify.log", "sha256": file_sha256(log_path)}],
        "checks": safe_checks,
        "evaluation_reports": [],
        "automatic_benchmark": True,
        "expected_checks": list(expected) or ["expected-check-manifest-present"],
        "executed_checks": list(executed),
        "candidate_sha": candidate_sha,
        "dirty_tree_before_run": dirty,
    }
    report = create_artifact(
        "ProcessTestReport",
        payload,
        source_artifacts=(),
        status="failed",
        failure={"family": family, "code": "gate_failed", "reason": reason},
        environment=runtime_environment(),
        logical_key="p0-full-verification",
        artifact_id=artifact_id_for("ProcessTestReport", "p0-full-verification"),
    )
    _write_json(output / "process-test-report.json", report)
    return report


def run(output: Path) -> int:
    root = Path.cwd().resolve()
    output = output.resolve()
    candidate_sha = "unresolved"
    dirty = True
    output.mkdir(parents=True, exist_ok=True)
    log_path = output / "verify.log"
    records: List[Dict[str, Any]] = []
    expected_ids: List[str] = []
    discovered_ids: List[str] = []
    executed_ids: List[str] = []
    checks: List[Dict[str, Any]] = []
    try:
        candidate_sha = _git(("rev-parse", "HEAD"), root)
        dirty = bool(_git(("status", "--porcelain"), root))
    except Exception as error:
        log_path.write_text("candidate provenance failed: %s\n" % error, encoding="utf-8")
        _failure_report(output, candidate_sha, dirty, "integrity_tamper_stale", str(error), [], [], [], log_path)
        print("P0 FAIL: candidate provenance unavailable", file=sys.stderr)
        return 1

    try:
        records, expected_ids = _load_expected(root)
        suite = unittest.defaultTestLoader.loadTestsFromNames(TEST_MODULES)
        discovered_ids = sorted(test.id() for test in _flatten_suite(suite))
        with log_path.open("w", encoding="utf-8") as log:
            log.write("candidate_sha=%s\ndirty_tree_before_run=%s\n" % (candidate_sha, str(dirty).lower()))
            if expected_ids != discovered_ids:
                raise ValueError("expected checks differ from discovered checks")
            result = unittest.TextTestRunner(stream=log, verbosity=2).run(suite)
        failed_ids = _failed_test_ids(result)
        skipped_ids = {test.id() for test, _ in result.skipped}
        executed_ids = sorted(set(discovered_ids) - skipped_ids)
        checks = _group_checks(records, failed_ids)
        if dirty:
            raise RuntimeError("official verification requires a clean checkout")
        if expected_ids != discovered_ids:
            raise RuntimeError("expected/discovered mismatch")
        if skipped_ids:
            raise RuntimeError("required checks skipped: %s" % sorted(skipped_ids))
        if failed_ids or not result.wasSuccessful():
            raise RuntimeError("required checks failed: %s" % sorted(failed_ids))

        fixture_root = root / "fixtures" / "p0" / "v1"
        mode_results = []
        for mode in ("transcription", "arrangement"):
            mode_results.append(
                run_mode_pipeline(
                    fixture_root,
                    output / "modes" / mode,
                    mode,
                    "drums",
                    candidate_sha=candidate_sha,
                    dirty_tree_before_run=dirty,
                )
            )
        aggregate_store = ArtifactStore(output / "artifact-store")
        for mode_result in mode_results:
            for artifact in mode_result["store"].all():
                if artifact["artifact_type"] not in ("EvaluationReport", "ProcessTestReport"):
                    aggregate_store.put(artifact)
        aggregate_run_id = "p0-full-verification"
        aggregate_process_id = artifact_id_for("ProcessTestReport", aggregate_run_id)
        evaluations = []
        for mode_result in mode_results:
            evaluation = copy.deepcopy(mode_result["evaluation_report"])
            mode = mode_result["track_ir"]["payload"]["mode"]
            evaluation["artifact_id"] = artifact_id_for("EvaluationReport", "%s:%s" % (aggregate_run_id, mode))
            evaluation["payload"]["run_id"] = aggregate_run_id
            evaluation["payload"]["process_test_report_id"] = aggregate_process_id
            evaluation["payload"]["artifact_paths"] = ["evaluation-%s.json" % mode]
            refresh_integrity(evaluation)
            aggregate_store.put(evaluation)
            _write_json(output / ("evaluation-%s.json" % mode), evaluation)
            evaluations.append(evaluation)
        if os.environ.get("P0_FORCE_LOW_SCORE") == "1":
            checks[4]["actual"] = 0.0
            checks[4]["passed"] = False
            checks[4]["numerator"] = 0
            raise RuntimeError("forced evaluator score below threshold")

        final_report = build_process_report(
            run_id=aggregate_run_id,
            evaluation_reports=tuple(evaluations),
            store=aggregate_store,
            checks=checks,
            status="success",
            candidate_sha=candidate_sha,
            dirty_tree_before_run=dirty,
            test_case_id="p0-full-clean-gate",
            input_checksum=mode_results[0]["source_media"]["payload"]["media_sha256"],
            expected_checks=expected_ids,
            executed_checks=executed_ids,
            artifact_paths=[
                "process-test-report.json",
                "evaluation-transcription.json",
                "evaluation-arrangement.json",
                "provenance-index.json",
                "samples/source-media.json",
                "samples/transcription-track-ir.json",
                "samples/arrangement-track-ir.json",
            ],
            log_references=[{"path": "verify.log", "sha256": file_sha256(log_path)}],
        )
        aggregate_store.put(final_report)
        _write_json(output / "process-test-report.json", final_report)
        samples = {
            "source-media.json": mode_results[0]["source_media"],
            "transcription-track-ir.json": mode_results[0]["track_ir"],
            "arrangement-track-ir.json": mode_results[1]["track_ir"],
        }
        for name, artifact in samples.items():
            _write_json(output / "samples" / name, artifact)
        lineage = aggregate_store.validate_lineage(final_report["artifact_id"])
        provenance_index = {
            "candidate_sha": candidate_sha,
            "root_artifact_id": final_report["artifact_id"],
            "artifacts": [
                {
                    "artifact_id": artifact_id,
                    "artifact_type": artifact["artifact_type"],
                    "content_hash": artifact["content_hash"],
                    "source_artifact_ids": artifact["source_artifact_ids"],
                    "store_path": str(aggregate_store.path_for(artifact_id).relative_to(output)),
                }
                for artifact_id, artifact in sorted(lineage.items())
            ],
        }
        _write_json(output / "provenance-index.json", provenance_index)
        validate_process_report(final_report, aggregate_store)
        print("P0 PASS: 7/7 groups, %d/%d checks" % (len(discovered_ids), len(expected_ids)))
        print("candidate_sha=%s" % candidate_sha)
        print("process_report=%s" % (output / "process-test-report.json"))
        print("provenance_index=%s" % (output / "provenance-index.json"))
        return 0
    except Exception as error:
        family = "contract_malformation"
        if os.environ.get("P0_FORCE_LOW_SCORE") == "1":
            family = "evaluator_numeric"
        elif not expected_ids or expected_ids != discovered_ids:
            family = "coverage_skip_gate"
        elif "fixture" in str(error).lower() or "checksum" in str(error).lower() or dirty:
            family = "integrity_tamper_stale"
        with log_path.open("a", encoding="utf-8") as log:
            log.write("\nGATE FAILURE\n%s\n" % traceback.format_exc())
        _failure_report(
            output,
            candidate_sha,
            dirty,
            family,
            str(error),
            checks,
            expected_ids,
            executed_ids,
            log_path,
        )
        print("P0 FAIL: %s" % error, file=sys.stderr)
        print("failure_report=%s" % (output / "process-test-report.json"), file=sys.stderr)
        return 1


def main(argv: Sequence[str] = ()) -> int:
    parser = argparse.ArgumentParser(description="Verify the README P0 contract baseline")
    parser.add_argument("--output", required=True, type=Path)
    arguments = parser.parse_args(list(argv) if argv else None)
    return run(arguments.output)


if __name__ == "__main__":
    raise SystemExit(main())
