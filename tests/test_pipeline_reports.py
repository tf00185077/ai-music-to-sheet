from __future__ import annotations

import copy
import json
import os
import tempfile
import unittest
from pathlib import Path

from p0.contracts import ContractError, refresh_integrity, validate_artifact
from p0.fixtures import validate_fixture_dataset
from p0.pipeline import PipelineBoundaryError, run_mode_pipeline
from p0.provenance import ArtifactStore, IntegrityError
from p0.reporting import ReportError, build_process_report, validate_process_report
from tests.support import FIXTURE_ROOT


class PipelineAndReportTests(unittest.TestCase):
    def test_f_success_and_failure_reports_are_distinct_crosslinked_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            successful = run_mode_pipeline(FIXTURE_ROOT, root / "success", "transcription", "drums")
            report = successful["process_report"]
            evaluation = successful["evaluation_report"]
            self.assertEqual(report["artifact_type"], "ProcessTestReport")
            self.assertEqual(evaluation["artifact_type"], "EvaluationReport")
            self.assertEqual(report["payload"]["evaluation_reports"][0]["artifact_id"], evaluation["artifact_id"])
            self.assertEqual(evaluation["payload"]["process_test_report_id"], report["artifact_id"])
            validate_process_report(report, successful["store"])

            inherited_force_low = os.environ.get("P0_FORCE_LOW_SCORE")
            os.environ["P0_FORCE_LOW_SCORE"] = "1"
            try:
                failed_result = run_mode_pipeline(FIXTURE_ROOT, root / "failed", "arrangement", "drums")
            finally:
                if inherited_force_low is None:
                    os.environ.pop("P0_FORCE_LOW_SCORE", None)
                else:
                    os.environ["P0_FORCE_LOW_SCORE"] = inherited_force_low
            failed = failed_result["process_report"]
            self.assertEqual(validate_process_report(failed, failed_result["store"]), failed)
            self.assertEqual(failed["status"], "failed")
            self.assertTrue(failed["failure"]["reason"])

    def test_f_missing_fact_low_score_changed_reference_and_manual_mix_fail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = run_mode_pipeline(FIXTURE_ROOT, Path(directory), "transcription", "drums")
            report = result["process_report"]
            store = result["store"]

            missing = copy.deepcopy(report)
            del missing["payload"]["checks"][0]["threshold"]
            refresh_integrity(missing)
            with self.assertRaises(ReportError) as incomplete:
                validate_process_report(missing, store)
            self.assertEqual(incomplete.exception.code, "missing_report_fact")

            false_pass = copy.deepcopy(report)
            false_pass["payload"]["checks"][0].update({"actual": 0.0, "threshold": 1.0, "passed": True})
            refresh_integrity(false_pass)
            with self.assertRaises(ReportError) as low:
                validate_process_report(false_pass, store)
            self.assertEqual(low.exception.code, "below_threshold_false_pass")

            log_path = Path(directory) / "verify.log"
            log_path.write_text(log_path.read_text(encoding="utf-8") + "tamper\n", encoding="utf-8")
            with self.assertRaises(ReportError) as bad_log:
                validate_process_report(report, store)
            self.assertEqual(bad_log.exception.code, "evidence_checksum_mismatch")

            evaluation_id = result["evaluation_report"]["artifact_id"]
            changed = copy.deepcopy(store.get(evaluation_id))
            changed["payload"]["metrics"]["f1"] = 0.0
            refresh_integrity(changed)
            store.put(changed, replace=True)
            with self.assertRaises(ReportError) as stale:
                validate_process_report(report, store)
            self.assertEqual(stale.exception.code, "evidence_checksum_mismatch")

        with tempfile.TemporaryDirectory() as directory:
            tainted = run_mode_pipeline(
                FIXTURE_ROOT,
                Path(directory),
                "transcription",
                "drums",
                human_correction=True,
                evaluation_category="automatic",
                expect_failure=True,
            )
            self.assertEqual(tainted["failure"].code, "human_correction_taint")

    def test_g_both_legal_modes_complete_with_full_lineage(self) -> None:
        for mode in ("transcription", "arrangement"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as directory:
                result = run_mode_pipeline(FIXTURE_ROOT, Path(directory), mode, "drums")
                self.assertEqual(result["process_report"]["status"], "success")
                lineage = result["store"].lineage(result["process_report"]["artifact_id"])
                types = {artifact["artifact_type"] for artifact in lineage.values()}
                self.assertEqual(
                    types,
                    {
                        "SourceMedia",
                        "CanonicalAudio",
                        "SongAnalysis",
                        "StemSet",
                        "TrackIR",
                        "NotationIR",
                        "EvaluationReport",
                        "ProcessTestReport",
                    },
                )

    def test_g_absent_unresolved_cross_mode_and_stale_flows_stop_at_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            absent = run_mode_pipeline(
                FIXTURE_ROOT,
                Path(directory),
                "transcription",
                "drums",
                target_presence="absent",
                expect_failure=True,
            )
            self.assertEqual(absent["failure"].code, "target_absent")
            self.assertNotIn("TrackIR", {item["artifact_type"] for item in absent["store"].all()})

        for status in ("failed", "low_confidence", "needs_human_confirmation"):
            with self.subTest(status=status), tempfile.TemporaryDirectory() as directory:
                stopped = run_mode_pipeline(
                    FIXTURE_ROOT,
                    Path(directory),
                    "transcription",
                    "drums",
                    upstream_status=status,
                    expect_failure=True,
                )
                self.assertEqual(stopped["failure"].code, "unresolved_upstream")

        with tempfile.TemporaryDirectory() as directory:
            crossed = run_mode_pipeline(
                FIXTURE_ROOT,
                Path(directory),
                "arrangement",
                "drums",
                consumer_mode="transcription",
                expect_failure=True,
            )
            self.assertEqual(crossed["failure"].code, "cross_mode")

        with tempfile.TemporaryDirectory() as directory:
            result = run_mode_pipeline(FIXTURE_ROOT, Path(directory), "transcription", "drums")
            source = result["source_media"]
            replacement = copy.deepcopy(source)
            replacement["payload"]["byte_size"] += 1
            refresh_integrity(replacement)
            result["store"].put(replacement, replace=True)
            with self.assertRaises(IntegrityError):
                result["store"].validate_lineage(result["process_report"]["artifact_id"])

    def test_failure_families_are_machine_distinguishable(self) -> None:
        expected = {
            "contract_malformation",
            "integrity_tamper_stale",
            "evaluator_numeric",
            "reproducibility_cross_run",
            "coverage_skip_gate",
            "contamination_taint",
        }
        from p0.reporting import FAILURE_FAMILIES

        self.assertEqual(set(FAILURE_FAMILIES), expected)


if __name__ == "__main__":
    unittest.main()
