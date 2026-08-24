from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests.support import clone_committed_repo, read_json


class VerifyCommandTests(unittest.TestCase):
    def run_verify(self, checkout: Path, extra_environment=None):
        environment = dict(os.environ)
        if extra_environment:
            environment.update(extra_environment)
        return subprocess.run(
            ["./scripts/verify-p0", "--output", "artifacts/p0/latest"],
            cwd=str(checkout),
            env=environment,
            capture_output=True,
            text=True,
        )

    def test_g_clean_checkout_command_writes_complete_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            checkout = clone_committed_repo(Path(directory))
            result = self.run_verify(checkout)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            output = checkout / "artifacts" / "p0" / "latest"
            report = read_json(output / "process-test-report.json")
            self.assertEqual(report["status"], "success")
            self.assertEqual(report["payload"]["expected_checks"], report["payload"]["executed_checks"])
            self.assertTrue(report["payload"]["candidate_sha"])
            self.assertFalse(report["payload"]["dirty_tree_before_run"])
            self.assertTrue((output / "provenance-index.json").is_file())
            self.assertGreaterEqual(len(list(output.glob("evaluation-*.json"))), 2)

    def test_g_corruption_missing_check_manifest_and_low_score_are_nonzero(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            checkout = clone_committed_repo(Path(directory))
            fixture = checkout / "fixtures" / "p0" / "v1" / "audio" / "exact-synthetic.wav"
            fixture.write_bytes(fixture.read_bytes() + b"damage")
            corrupt = self.run_verify(checkout)
            self.assertNotEqual(corrupt.returncode, 0)
            report = read_json(checkout / "artifacts" / "p0" / "latest" / "process-test-report.json")
            self.assertEqual(report["status"], "failed")

        with tempfile.TemporaryDirectory() as directory:
            checkout = clone_committed_repo(Path(directory))
            (checkout / "p0" / "expected-checks.json").unlink()
            missing = self.run_verify(checkout)
            self.assertNotEqual(missing.returncode, 0)

        with tempfile.TemporaryDirectory() as directory:
            checkout = clone_committed_repo(Path(directory))
            low = self.run_verify(checkout, {"P0_FORCE_LOW_SCORE": "1"})
            self.assertNotEqual(low.returncode, 0)
            report = read_json(checkout / "artifacts" / "p0" / "latest" / "process-test-report.json")
            self.assertEqual(report["failure"]["family"], "evaluator_numeric")


if __name__ == "__main__":
    unittest.main()
