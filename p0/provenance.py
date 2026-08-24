from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Mapping, MutableMapping, Optional, Set

from p0.contracts import (
    ContractError,
    canonical_json,
    sha256_json,
    source_reference,
    validate_artifact,
)


class IntegrityError(ValueError):
    def __init__(self, code: str, artifact_id: str, detail: str) -> None:
        self.code = code
        self.artifact_id = artifact_id
        self.detail = detail
        super().__init__("%s for %s: %s" % (code, artifact_id, detail))

    def as_dict(self) -> Dict[str, Any]:
        return {
            "family": "integrity_tamper_stale",
            "code": self.code,
            "artifact_id": self.artifact_id,
            "detail": self.detail,
        }


def cache_key(artifact: Mapping[str, Any]) -> str:
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


def source_ref(artifact: Mapping[str, Any]) -> Dict[str, Any]:
    return source_reference(artifact)


class ArtifactStore:
    def __init__(self, root: Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def path_for(self, artifact_id: str) -> Path:
        safe_name = artifact_id.replace(":", "__").replace("/", "_")
        return self.root / (safe_name + ".json")

    def put(self, artifact: Mapping[str, Any], replace: bool = False) -> Path:
        validate_artifact(artifact)
        path = self.path_for(artifact["artifact_id"])
        if path.exists() and not replace:
            existing = json.loads(path.read_text(encoding="utf-8"))
            if canonical_json(existing) != canonical_json(artifact):
                raise IntegrityError("identity_collision", artifact["artifact_id"], "different content already stored")
            return path
        path.write_text(
            json.dumps(artifact, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n",
            encoding="utf-8",
        )
        return path

    def get(self, artifact_id: str) -> Dict[str, Any]:
        path = self.path_for(artifact_id)
        if not path.is_file():
            raise IntegrityError("missing_upstream", artifact_id, "artifact file does not exist")
        try:
            artifact = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise IntegrityError("corrupt_serialization", artifact_id, str(error))
        try:
            validate_artifact(artifact)
        except ContractError as error:
            code = "recorded_hash_mismatch" if error.code == "checksum_mismatch" else error.code
            raise IntegrityError(code, artifact_id, str(error))
        return artifact

    def all(self):
        artifacts = []
        for path in sorted(self.root.glob("*.json")):
            try:
                artifacts.append(json.loads(path.read_text(encoding="utf-8")))
            except (OSError, json.JSONDecodeError) as error:
                raise IntegrityError("corrupt_serialization", path.name, str(error))
        return artifacts

    def registry(self) -> Dict[str, Dict[str, Any]]:
        return {artifact["artifact_id"]: artifact for artifact in self.all()}

    def lineage(self, artifact_id: str) -> Dict[str, Dict[str, Any]]:
        resolved: Dict[str, Dict[str, Any]] = {}
        visiting: Set[str] = set()

        def visit(current_id: str) -> None:
            if current_id in resolved:
                return
            if current_id in visiting:
                raise IntegrityError("cycle", current_id, "provenance graph contains a cycle")
            visiting.add(current_id)
            artifact = self.get(current_id)
            resolved[current_id] = artifact
            for source_id in artifact["source_artifact_ids"]:
                visit(source_id)
            visiting.remove(current_id)

        visit(artifact_id)
        return resolved

    def validate_lineage(self, artifact_id: str) -> Dict[str, Dict[str, Any]]:
        lineage = self.lineage(artifact_id)
        for current_id, artifact in lineage.items():
            try:
                validate_artifact(artifact, registry=lineage)
            except ContractError as error:
                if error.code == "checksum_mismatch":
                    code = "recorded_hash_mismatch"
                else:
                    code = error.code
                raise IntegrityError(code, current_id, str(error))
        return lineage

    def has_human_taint(self, artifact_id: str) -> bool:
        visited: Set[str] = set()

        def visit(current_id: str) -> bool:
            if current_id in visited:
                return False
            visited.add(current_id)
            artifact = self.get(current_id)
            if artifact.get("human_correction"):
                return True
            return any(visit(source_id) for source_id in artifact["source_artifact_ids"])

        return visit(artifact_id)

    def assert_automatic_lineage(self, artifact_id: str) -> None:
        if self.has_human_taint(artifact_id):
            raise IntegrityError(
                "human_correction_taint",
                artifact_id,
                "automatic benchmark lineage contains a human-corrected artifact",
            )
