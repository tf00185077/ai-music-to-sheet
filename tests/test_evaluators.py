from __future__ import annotations

import math
import unittest

from p0.evaluator import evaluate_events


GROUND_TRUTH = [
    {"onset_seconds": 0.0, "class": "kick"},
    {"onset_seconds": 0.5, "class": "snare"},
]


class EvaluatorTests(unittest.TestCase):
    def test_e_perfect_shift_delete_insert_and_wrong_class_controls(self) -> None:
        perfect = evaluate_events(GROUND_TRUTH, list(GROUND_TRUTH), tolerance_seconds=0.05)
        self.assertEqual((perfect["precision"], perfect["recall"], perfect["f1"]), (1.0, 1.0, 1.0))

        shifted = evaluate_events(
            GROUND_TRUTH,
            [{"onset_seconds": item["onset_seconds"] + 0.051, "class": item["class"]} for item in GROUND_TRUTH],
            tolerance_seconds=0.05,
        )
        self.assertLess(shifted["f1"], perfect["f1"])

        deleted = evaluate_events(GROUND_TRUTH, GROUND_TRUTH[:1], tolerance_seconds=0.05)
        self.assertEqual(deleted["precision"], 1.0)
        self.assertLess(deleted["recall"], 1.0)

        inserted = evaluate_events(
            GROUND_TRUTH,
            GROUND_TRUTH + [{"onset_seconds": 0.8, "class": "kick"}],
            tolerance_seconds=0.05,
        )
        self.assertLess(inserted["precision"], 1.0)
        self.assertEqual(inserted["recall"], 1.0)

        wrong = evaluate_events(
            GROUND_TRUTH,
            [{"onset_seconds": 0.0, "class": "snare"}, GROUND_TRUTH[1]],
            tolerance_seconds=0.05,
        )
        self.assertLess(wrong["class_f1"], 1.0)

    def test_e_tolerance_boundary_is_inclusive_and_one_to_one(self) -> None:
        reference = [{"onset_seconds": 1.0, "class": "kick"}]
        below = evaluate_events(reference, [{"onset_seconds": 1.049999, "class": "kick"}], 0.05)
        equal = evaluate_events(reference, [{"onset_seconds": 1.05, "class": "kick"}], 0.05)
        above = evaluate_events(reference, [{"onset_seconds": 1.050001, "class": "kick"}], 0.05)
        self.assertEqual((below["tp"], equal["tp"], above["tp"]), (1, 1, 0))
        self.assertEqual(equal["tolerance_rule"], "inclusive")

        competing = evaluate_events(
            reference,
            [
                {"onset_seconds": 0.99, "class": "kick"},
                {"onset_seconds": 1.01, "class": "kick"},
            ],
            0.05,
        )
        self.assertEqual((competing["tp"], competing["fp"], competing["fn"]), (1, 1, 0))

    def test_e_empty_sets_have_finite_documented_values(self) -> None:
        empty_empty = evaluate_events([], [], 0.05)
        self.assertEqual((empty_empty["precision"], empty_empty["recall"], empty_empty["f1"]), (1.0, 1.0, 1.0))
        empty_prediction = evaluate_events(GROUND_TRUTH, [], 0.05)
        self.assertEqual((empty_prediction["precision"], empty_prediction["recall"]), (1.0, 0.0))
        for report in (empty_empty, empty_prediction):
            for value in report.values():
                if isinstance(value, float):
                    self.assertTrue(math.isfinite(value))

    def test_e_per_class_micro_and_macro_share_documented_definitions(self) -> None:
        result = evaluate_events(
            GROUND_TRUTH,
            [{"onset_seconds": 0.0, "class": "kick"}, {"onset_seconds": 0.5, "class": "kick"}],
            0.05,
        )
        self.assertEqual(result["metric_version"], "p0-event-metrics/1.0.0")
        self.assertEqual(set(result["per_class"]), {"kick", "snare"})
        self.assertAlmostEqual(result["micro"]["f1"], result["class_f1"])
        expected_macro = sum(item["f1"] for item in result["per_class"].values()) / 2
        self.assertAlmostEqual(result["macro"]["f1"], expected_macro)
        self.assertEqual(result["empty_class_policy"], "classes in reference-or-prediction; empty/empty class omitted")


if __name__ == "__main__":
    unittest.main()
