from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from p0.contracts import (
    ARTIFACT_TYPES,
    ContractError,
    create_artifact,
    migrate_legacy_artifact,
    read_artifact,
    refresh_integrity,
    semantic_view,
    semantically_equal,
    validate_artifact,
    write_artifact,
)
from p0.examples import artifact_examples


class SchemaContractTests(unittest.TestCase):
    def test_a_published_json_schemas_cover_every_artifact(self) -> None:
        schema_root = Path(__file__).resolve().parents[1] / "contracts" / "schemas" / "1.0.0"
        index = json.loads((schema_root / "index.json").read_text(encoding="utf-8"))
        self.assertEqual(index["schema_version"], "1.0.0")
        self.assertEqual(set(index["artifacts"]), set(ARTIFACT_TYPES))
        common_required = {
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
        }
        for artifact_type in ARTIFACT_TYPES:
            schema = json.loads((schema_root / (artifact_type + ".schema.json")).read_text(encoding="utf-8"))
            self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
            self.assertEqual(schema["title"], artifact_type)
            self.assertEqual(schema["x-schema-version"], "1.0.0")
            self.assertEqual(set(schema["x-common-required"]), common_required)

    def test_a_all_eight_artifacts_round_trip_on_real_files(self) -> None:
        examples = artifact_examples()
        self.assertEqual(set(ARTIFACT_TYPES), set(examples))
        with tempfile.TemporaryDirectory() as directory:
            registry = {artifact["artifact_id"]: artifact for artifact in examples.values()}
            for artifact_type, artifact in examples.items():
                path = Path(directory) / (artifact_type + ".json")
                write_artifact(path, artifact)
                loaded = read_artifact(path, registry=registry)
                self.assertTrue(semantically_equal(artifact, loaded), artifact_type)
                self.assertEqual(validate_artifact(loaded, registry=registry), loaded)

    def test_a_malformed_contracts_return_structured_rejections(self) -> None:
        base = artifact_examples()["CanonicalAudio"]
        cases = []
        missing = copy.deepcopy(base)
        del missing["generator"]
        cases.append((missing, "required"))
        wrong_type = copy.deepcopy(base)
        wrong_type["payload"]["sample_rate"] = "48000"
        cases.append((wrong_type, "type"))
        bad_enum = copy.deepcopy(base)
        bad_enum["status"] = "maybe"
        cases.append((bad_enum, "enum"))
        bad_range = copy.deepcopy(base)
        bad_range["payload"]["sample_rate"] = 0
        cases.append((bad_range, "range"))
        bad_major = copy.deepcopy(base)
        bad_major["schema_version"] = "2.0.0"
        cases.append((bad_major, "unsupported_major"))
        stale = copy.deepcopy(base)
        stale["payload"]["duration_seconds"] += 1
        cases.append((stale, "checksum_mismatch"))

        for artifact, expected_code in cases:
            with self.subTest(expected_code=expected_code):
                with self.assertRaises(ContractError) as raised:
                    validate_artifact(artifact)
                self.assertEqual(raised.exception.code, expected_code)
                self.assertTrue(raised.exception.field)
                self.assertIsNotNone(raised.exception.expected)

    def test_a_missing_and_incompatible_upstreams_are_rejected(self) -> None:
        examples = artifact_examples()
        canonical = examples["CanonicalAudio"]
        with self.assertRaises(ContractError) as missing:
            validate_artifact(canonical, registry={})
        self.assertEqual(missing.exception.code, "missing_upstream")

        wrong_source = copy.deepcopy(examples["SourceMedia"])
        wrong_source["artifact_id"] = canonical["source_artifact_ids"][0]
        wrong_source["artifact_type"] = "StemSet"
        registry = {wrong_source["artifact_id"]: wrong_source}
        with self.assertRaises(ContractError) as incompatible:
            validate_artifact(canonical, registry=registry)
        self.assertEqual(incompatible.exception.code, "incompatible_upstream")

        incomplete_track = create_artifact(
            "TrackIR",
            examples["TrackIR"]["payload"],
            source_artifacts=(examples["StemSet"],),
            logical_key="missing-song-analysis-upstream",
        )
        with self.assertRaises(ContractError) as incomplete:
            validate_artifact(incomplete_track)
        self.assertEqual(incomplete.exception.code, "missing_required_upstream")

    def test_a_state_transitions_and_numeric_bounds_fail_closed(self) -> None:
        example = artifact_examples()["TrackIR"]
        failed_without_reason = copy.deepcopy(example)
        failed_without_reason["status"] = "failed"
        with self.assertRaises(ContractError) as missing_reason:
            validate_artifact(failed_without_reason)
        self.assertEqual(missing_reason.exception.code, "state_transition")

        for field, value in (("confidence", 1.1), ("pitch", 128), ("onset_seconds", -0.01)):
            artifact = copy.deepcopy(example)
            if field == "confidence":
                artifact[field]["confidence"] = value
            else:
                artifact["payload"]["events"][0][field] = value
            with self.subTest(field=field):
                with self.assertRaises(ContractError) as raised:
                    validate_artifact(artifact)
                self.assertEqual(raised.exception.code, "range")

    def test_b_same_major_extension_reads_and_unsupported_major_rejects(self) -> None:
        examples = artifact_examples()
        artifact = examples["SongAnalysis"]
        compatible = copy.deepcopy(artifact)
        compatible["schema_version"] = "1.1.0"
        compatible["optional_future_field"] = {"ignored_by_1_0_reader": True}
        compatible = create_artifact(
            "SongAnalysis",
            compatible["payload"],
            source_artifacts=(examples["CanonicalAudio"],),
            schema_version="1.1.0",
            logical_key="compat-1.1",
        )
        compatible["optional_future_field"] = {"ignored_by_1_0_reader": True}
        from p0.contracts import refresh_integrity

        refresh_integrity(compatible)
        self.assertEqual(validate_artifact(compatible)["schema_version"], "1.1.0")

        incompatible = copy.deepcopy(compatible)
        incompatible["schema_version"] = "9.0.0"
        with self.assertRaises(ContractError) as raised:
            validate_artifact(incompatible)
        self.assertEqual(raised.exception.code, "unsupported_major")

    def test_b_migration_preserves_source_and_musical_semantics(self) -> None:
        legacy = {
            "artifact_type": "TrackIR",
            "artifact_id": "legacy-track-1",
            "schema_version": "0.9.0",
            "payload": artifact_examples()["TrackIR"]["payload"],
        }
        original = json.loads(json.dumps(legacy))
        migrated = migrate_legacy_artifact(legacy, target_version="1.0.0")
        self.assertEqual(legacy, original)
        self.assertNotEqual(migrated["artifact_id"], legacy["artifact_id"])
        self.assertEqual(migrated["migration"]["source_artifact_id"], legacy["artifact_id"])
        self.assertEqual(migrated["migration"]["source_snapshot"], legacy)
        self.assertEqual(semantic_view(migrated), semantic_view(legacy))
        self.assertEqual(validate_artifact(migrated), migrated)

    def test_b_frozen_compatibility_vectors_are_nonempty_and_exercised(self) -> None:
        path = Path(__file__).resolve().parents[1] / "contracts" / "compatibility-vectors.json"
        vectors = json.loads(path.read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(vectors["supported_same_major"]), 1)
        self.assertGreaterEqual(len(vectors["unsupported_major"]), 1)
        self.assertGreaterEqual(len(vectors["legacy_migrations"]), 1)
        self.assertTrue(all(vector["exercised_by"] for group in vectors.values() if isinstance(group, list) for vector in group))

    def test_mode_and_instrument_shapes_are_distinct_and_truthful(self) -> None:
        examples = artifact_examples()
        for instrument in ("drums", "piano", "guitar"):
            for mode in ("transcription", "arrangement"):
                artifact = artifact_examples(track_instrument=instrument, track_mode=mode)["TrackIR"]
                self.assertEqual(validate_artifact(artifact), artifact)
                event = artifact["payload"]["events"][0]
                self.assertIn("evidence", event if mode == "transcription" else {"evidence": True})
                self.assertIn("arrangement_decision", event if mode == "arrangement" else {"arrangement_decision": True})

        bad = copy.deepcopy(examples["TrackIR"])
        bad["payload"]["events"][0].pop("evidence")
        refresh_integrity(bad)
        with self.assertRaises(ContractError) as raised:
            validate_artifact(bad)
        self.assertEqual(raised.exception.code, "mode_provenance")

        incompatible_shape = copy.deepcopy(examples["TrackIR"])
        incompatible_shape["payload"]["events"][0]["pitch"] = 60
        incompatible_shape["payload"]["events"][0]["hand"] = {"state": "known", "value": "right", "confidence": 1.0}
        refresh_integrity(incompatible_shape)
        with self.assertRaises(ContractError) as incompatible:
            validate_artifact(incompatible_shape)
        self.assertEqual(incompatible.exception.code, "instrument_shape")

    def test_transcription_evidence_must_resolve_and_stay_in_audio_bounds(self) -> None:
        examples = artifact_examples()
        registry = {artifact["artifact_id"]: artifact for artifact in examples.values()}
        track = examples["TrackIR"]
        self.assertEqual(validate_artifact(track, registry=registry), track)

        missing = copy.deepcopy(track)
        missing["payload"]["events"][0]["evidence"][0]["artifact_id"] = "stemset:missing"
        refresh_integrity(missing)
        with self.assertRaises(ContractError) as unresolved:
            validate_artifact(missing, registry=registry)
        self.assertEqual(unresolved.exception.code, "missing_evidence")

        out_of_bounds = copy.deepcopy(track)
        out_of_bounds["payload"]["events"][0]["evidence"][0]["end_seconds"] = 1.1
        refresh_integrity(out_of_bounds)
        with self.assertRaises(ContractError) as bounds:
            validate_artifact(out_of_bounds, registry=registry)
        self.assertEqual(bounds.exception.code, "evidence_out_of_bounds")

    def test_semantic_comparator_detects_musical_change_and_allows_nonsemantic_change(self) -> None:
        original = artifact_examples(track_instrument="piano")["TrackIR"]
        musical_change = copy.deepcopy(original)
        musical_change["payload"]["events"][0]["pitch"] += 1
        refresh_integrity(musical_change)
        self.assertFalse(semantically_equal(original, musical_change))

        nonsemantic_change = copy.deepcopy(original)
        nonsemantic_change["created_at"] = "2001-01-01T00:00:00Z"
        nonsemantic_change["environment"]["os"] = "different-test-environment"
        refresh_integrity(nonsemantic_change)
        self.assertTrue(semantically_equal(original, nonsemantic_change))

    def test_unknown_facts_are_explicit_not_hidden_defaults(self) -> None:
        guitar = artifact_examples(track_instrument="guitar")["TrackIR"]
        string_fact = guitar["payload"]["events"][0]["string"]
        self.assertEqual(string_fact, {"state": "unknown", "value": None, "confidence": None})
        self.assertEqual(validate_artifact(guitar), guitar)


if __name__ == "__main__":
    unittest.main()
