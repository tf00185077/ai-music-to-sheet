from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path

from p0.contracts import create_artifact, refresh_integrity
from p0.examples import artifact_examples
from p0.provenance import ArtifactStore, IntegrityError, cache_key, source_ref


class ProvenanceTests(unittest.TestCase):
    def test_c_final_artifact_resolves_every_direct_and_indirect_ancestor(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = ArtifactStore(Path(directory))
            examples = artifact_examples()
            for artifact in examples.values():
                store.put(artifact)
            lineage = store.lineage(examples["ProcessTestReport"]["artifact_id"])
            self.assertEqual(set(lineage), {artifact["artifact_id"] for artifact in examples.values()})
            store.validate_lineage(examples["ProcessTestReport"]["artifact_id"])

    def test_c_delete_replace_and_forge_are_detected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = ArtifactStore(Path(directory))
            examples = artifact_examples()
            for artifact in examples.values():
                store.put(artifact)
            source = examples["SourceMedia"]
            store.path_for(source["artifact_id"]).unlink()
            with self.assertRaises(IntegrityError) as deleted:
                store.validate_lineage(examples["ProcessTestReport"]["artifact_id"])
            self.assertEqual(deleted.exception.code, "missing_upstream")

        with tempfile.TemporaryDirectory() as directory:
            store = ArtifactStore(Path(directory))
            examples = artifact_examples()
            for artifact in examples.values():
                store.put(artifact)
            source = copy.deepcopy(examples["SourceMedia"])
            source["payload"]["byte_size"] += 1
            refresh_integrity(source)
            store.put(source, replace=True)
            with self.assertRaises(IntegrityError) as replaced:
                store.validate_lineage(examples["ProcessTestReport"]["artifact_id"])
            self.assertIn(replaced.exception.code, {"recorded_hash_mismatch", "stale_cache"})

    def test_c_cache_key_includes_content_model_parameter_schema_and_mode(self) -> None:
        base = artifact_examples()["TrackIR"]
        variants = []
        for mutation in ("content", "model", "parameter", "schema", "mode"):
            variant = copy.deepcopy(base)
            if mutation == "content":
                variant["payload"]["events"][0]["velocity"] -= 1
            elif mutation == "model":
                variant["generator"]["model_version"] = "stub-2"
            elif mutation == "parameter":
                variant["generator"]["parameters"]["quantization"] = "1/16"
            elif mutation == "schema":
                variant["schema_version"] = "1.1.0"
            else:
                variant["payload"]["mode"] = "arrangement"
                event = variant["payload"]["events"][0]
                event.pop("evidence")
                event["arrangement_decision"] = {"rule": "deterministic-test", "reason": "coverage"}
            refresh_integrity(variant)
            variants.append(variant)
        self.assertEqual(len({cache_key(base)} | {cache_key(item) for item in variants}), 6)

        downstream = create_artifact(
            "NotationIR",
            artifact_examples()["NotationIR"]["payload"],
            source_artifacts=(base,),
            logical_key="stale-check",
        )
        for variant in variants:
            registry = {variant["artifact_id"]: variant}
            with self.subTest(variant=variant["generator"].get("model_version")):
                from p0.contracts import ContractError, validate_artifact

                with self.assertRaises(ContractError) as raised:
                    validate_artifact(downstream, registry=registry)
                self.assertIn(raised.exception.code, {"checksum_mismatch", "stale_cache"})

    def test_f_human_correction_taint_is_transitive(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = ArtifactStore(Path(directory))
            examples = artifact_examples()
            track = copy.deepcopy(examples["TrackIR"])
            track["human_correction"] = True
            refresh_integrity(track)
            notation = create_artifact(
                "NotationIR",
                examples["NotationIR"]["payload"],
                source_artifacts=(track,),
                logical_key="tainted-notation",
            )
            evaluation = create_artifact(
                "EvaluationReport",
                examples["EvaluationReport"]["payload"],
                source_artifacts=(notation,),
                logical_key="tainted-evaluation",
            )
            for artifact in (track, notation, evaluation):
                store.put(artifact)
            self.assertTrue(store.has_human_taint(evaluation["artifact_id"]))
            with self.assertRaises(IntegrityError) as raised:
                store.assert_automatic_lineage(evaluation["artifact_id"])
            self.assertEqual(raised.exception.code, "human_correction_taint")


if __name__ == "__main__":
    unittest.main()
