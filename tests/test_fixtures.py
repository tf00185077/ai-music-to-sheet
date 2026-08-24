from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from p0.fixtures import FixtureError, load_fixture_manifest, validate_fixture_dataset
from p0.contracts import semantically_equal
from p0.pipeline import run_mode_pipeline
from tests.support import FIXTURE_ROOT, copy_fixture_dataset


class FixtureTests(unittest.TestCase):
    def test_d_manifest_is_complete_lawful_and_checksummed(self) -> None:
        result = validate_fixture_dataset(FIXTURE_ROOT)
        required = {
            "exact_synthetic",
            "rendered_events",
            "isolated_drums",
            "isolated_piano",
            "isolated_guitar",
            "annotated_mix",
            "absent_target",
            "low_volume",
            "partial_presence",
            "masking",
        }
        self.assertEqual(result.categories, required)
        self.assertEqual(result.checked_files, result.manifest_files)
        self.assertGreater(result.checked_files, 0)
        manifest = load_fixture_manifest(FIXTURE_ROOT)
        for fixture in manifest["fixtures"]:
            self.assertEqual(fixture["license"]["spdx"], "CC0-1.0")
            self.assertEqual(fixture["split"], "transparent-validation")
            self.assertTrue(fixture["ground_truth"])
            self.assertIn("usage_restriction", fixture)
        self.assertEqual(manifest["conventions"]["time_unit"], "seconds")
        self.assertEqual(manifest["conventions"]["coordinate_origin"], 0)
        self.assertEqual(manifest["conventions"]["pitch_standard"], "MIDI note 0-127, A4=440Hz")

    def test_d_missing_or_corrupt_fixture_stops_validation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = copy_fixture_dataset(Path(directory))
            manifest = load_fixture_manifest(root)
            target = root / manifest["fixtures"][0]["files"][0]["path"]
            target.unlink()
            with self.assertRaises(FixtureError) as missing:
                validate_fixture_dataset(root)
            self.assertEqual(missing.exception.code, "missing_file")

        with tempfile.TemporaryDirectory() as directory:
            root = copy_fixture_dataset(Path(directory))
            manifest = load_fixture_manifest(root)
            target = root / manifest["fixtures"][0]["files"][0]["path"]
            target.write_bytes(target.read_bytes() + b"tamper")
            with self.assertRaises(FixtureError) as corrupt:
                validate_fixture_dataset(root)
            self.assertEqual(corrupt.exception.code, "checksum_mismatch")

    def test_d_manifest_and_file_edit_under_same_version_hits_external_lock(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = copy_fixture_dataset(Path(directory))
            manifest_path = root / "manifest.json"
            manifest = load_fixture_manifest(root)
            file_record = manifest["fixtures"][0]["files"][0]
            target = root / file_record["path"]
            target.write_bytes(target.read_bytes() + b"coordinated-edit")
            file_record["sha256"] = hashlib.sha256(target.read_bytes()).hexdigest()
            manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
            with self.assertRaises(FixtureError) as drift:
                validate_fixture_dataset(root)
            self.assertEqual(drift.exception.code, "immutable_version_drift")

    def test_d_incompatible_annotation_version_is_not_skipped(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = copy_fixture_dataset(Path(directory))
            manifest_path = root / "manifest.json"
            manifest = load_fixture_manifest(root)
            manifest["fixtures"][0]["annotation_version"] = "9.0.0"
            manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
            with self.assertRaises(FixtureError) as raised:
                validate_fixture_dataset(root, verify_lock=False)
            self.assertEqual(raised.exception.code, "annotation_incompatible")

    def test_d_same_inputs_versions_parameters_and_seed_are_reproducible(self) -> None:
        with tempfile.TemporaryDirectory() as first_directory, tempfile.TemporaryDirectory() as second_directory:
            first = run_mode_pipeline(FIXTURE_ROOT, Path(first_directory), "transcription", "drums")
            second = run_mode_pipeline(FIXTURE_ROOT, Path(second_directory), "transcription", "drums")
            for key in (
                "source_media",
                "canonical_audio",
                "song_analysis",
                "stem_set",
                "track_ir",
                "notation_ir",
                "evaluation_report",
                "process_report",
            ):
                self.assertTrue(semantically_equal(first[key], second[key]), key)


if __name__ == "__main__":
    unittest.main()
