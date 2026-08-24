from __future__ import annotations

import re
import stat
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class DeliveryContractTests(unittest.TestCase):
    def test_g_claims_manifest_covers_every_intent_with_exact_fields(self) -> None:
        path = ROOT / "docs" / "reviewspec" / "readme-p0" / "manifest.md"
        body = path.read_text(encoding="utf-8")
        self.assertIn("candidate_sha", body)
        self.assertIn("artifacts/p0/latest/process-test-report.json", body)
        headings = re.findall(r"^## (INT-[0-9]+)$", body, flags=re.MULTILINE)
        self.assertEqual(headings, ["INT-%d" % index for index in range(1, 11)])
        for index, intent in enumerate(headings):
            start = body.index("## %s" % intent)
            end = body.find("\n## INT-", start + 1)
            block = body[start:] if end == -1 else body[start:end]
            fields = re.findall(r"^- (behavior|test_layer|real_environment|self_tier):", block, flags=re.MULTILINE)
            self.assertEqual(fields, ["behavior", "test_layer", "real_environment", "self_tier"], intent)
            self.assertIn("- self_tier: Core", block)

    def test_g_ci_runs_canonical_command_and_always_retains_evidence(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "verify-p0.yml").read_text(encoding="utf-8")
        self.assertIn("./scripts/verify-p0 --output artifacts/p0/latest", workflow)
        self.assertIn("if: always()", workflow)
        self.assertIn("if-no-files-found: error", workflow)
        script = ROOT / "scripts" / "verify-p0"
        self.assertTrue(script.stat().st_mode & stat.S_IXUSR)


if __name__ == "__main__":
    unittest.main()
