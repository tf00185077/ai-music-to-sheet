from __future__ import annotations

import dataclasses
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Set


REQUIRED_CATEGORIES = {
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
SUPPORTED_ANNOTATION_MAJOR = 1


class FixtureError(ValueError):
    def __init__(self, code: str, fixture_id: str, detail: str) -> None:
        self.code = code
        self.fixture_id = fixture_id
        self.detail = detail
        super().__init__("%s for %s: %s" % (code, fixture_id, detail))

    def as_dict(self) -> Dict[str, Any]:
        return {
            "family": "integrity_tamper_stale",
            "code": self.code,
            "fixture_id": self.fixture_id,
            "detail": self.detail,
        }


@dataclasses.dataclass(frozen=True)
class FixtureValidationResult:
    dataset_version: str
    manifest_sha256: str
    categories: Set[str]
    checked_files: int
    manifest_files: int


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_fixture_manifest(root: Path) -> Dict[str, Any]:
    path = Path(root) / "manifest.json"
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise FixtureError("missing_manifest", "dataset", str(path))
    except json.JSONDecodeError as error:
        raise FixtureError("corrupt_manifest", "dataset", str(error))
    if not isinstance(value, dict):
        raise FixtureError("corrupt_manifest", "dataset", "manifest root must be an object")
    return value


def validate_fixture_dataset(root: Path, verify_lock: bool = True) -> FixtureValidationResult:
    root = Path(root)
    manifest_path = root / "manifest.json"
    manifest = load_fixture_manifest(root)
    dataset_version = manifest.get("dataset_version")
    if dataset_version != "p0-fixtures/1.0.0":
        raise FixtureError("unsupported_dataset_version", "dataset", str(dataset_version))
    if manifest.get("immutable") is not True:
        raise FixtureError("mutable_dataset", "dataset", "published version must declare immutable=true")
    manifest_hash = file_sha256(manifest_path)

    if verify_lock:
        lock_path = root.parent / "manifest-lock.json"
        try:
            lock = json.loads(lock_path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            raise FixtureError("missing_tamper_anchor", "dataset", str(lock_path))
        except json.JSONDecodeError as error:
            raise FixtureError("corrupt_tamper_anchor", "dataset", str(error))
        if lock.get("dataset_version") != dataset_version or lock.get("manifest_sha256") != manifest_hash:
            raise FixtureError(
                "immutable_version_drift",
                "dataset",
                "recorded %s/%s, observed %s/%s"
                % (lock.get("dataset_version"), lock.get("manifest_sha256"), dataset_version, manifest_hash),
            )

    conventions = manifest.get("conventions")
    if not isinstance(conventions, dict):
        raise FixtureError("missing_conventions", "dataset", "conventions object is required")
    for field in ("time_unit", "coordinate_origin", "pitch_standard", "instrument_taxonomy"):
        if field not in conventions:
            raise FixtureError("missing_conventions", "dataset", field)

    fixtures = manifest.get("fixtures")
    if not isinstance(fixtures, list) or not fixtures:
        raise FixtureError("empty_required_group", "dataset", "fixtures must be non-empty")
    identifiers = set()
    categories: Set[str] = set()
    checked_files = 0
    manifest_files = 0
    for fixture in fixtures:
        fixture_id = fixture.get("fixture_id")
        if not isinstance(fixture_id, str) or not fixture_id:
            raise FixtureError("missing_fixture_id", "dataset", repr(fixture_id))
        if fixture_id in identifiers:
            raise FixtureError("duplicate_fixture_id", fixture_id, "fixture IDs must be unique")
        identifiers.add(fixture_id)
        category = fixture.get("category")
        if category not in REQUIRED_CATEGORIES:
            raise FixtureError("unknown_category", fixture_id, repr(category))
        categories.add(category)
        annotation_version = fixture.get("annotation_version")
        try:
            annotation_major = int(str(annotation_version).split(".")[0])
        except (TypeError, ValueError):
            raise FixtureError("annotation_incompatible", fixture_id, repr(annotation_version))
        if annotation_major != SUPPORTED_ANNOTATION_MAJOR:
            raise FixtureError("annotation_incompatible", fixture_id, str(annotation_version))
        license_record = fixture.get("license")
        if not isinstance(license_record, dict) or not license_record.get("spdx") or not license_record.get("owner"):
            raise FixtureError("unlicensed", fixture_id, repr(license_record))
        for field in ("split", "purpose", "usage_restriction", "ground_truth"):
            if not fixture.get(field):
                raise FixtureError("missing_fixture_fact", fixture_id, field)
        files = fixture.get("files")
        if not isinstance(files, list) or not files:
            raise FixtureError("empty_required_group", fixture_id, "files")
        manifest_files += len(files)
        recorded_paths = set()
        for record in files:
            relative = record.get("path")
            if not isinstance(relative, str) or not relative or Path(relative).is_absolute() or ".." in Path(relative).parts:
                raise FixtureError("unsafe_path", fixture_id, repr(relative))
            if relative in recorded_paths:
                raise FixtureError("duplicate_file", fixture_id, relative)
            recorded_paths.add(relative)
            target = root / relative
            if not target.is_file():
                raise FixtureError("missing_file", fixture_id, relative)
            observed_hash = file_sha256(target)
            if observed_hash != record.get("sha256"):
                raise FixtureError(
                    "checksum_mismatch",
                    fixture_id,
                    "%s recorded=%s observed=%s" % (relative, record.get("sha256"), observed_hash),
                )
            if target.stat().st_size != record.get("bytes"):
                raise FixtureError("size_mismatch", fixture_id, relative)
            checked_files += 1
        ground_truth = fixture["ground_truth"]
        if not isinstance(ground_truth, dict) or ground_truth.get("path") not in recorded_paths:
            raise FixtureError("missing_ground_truth", fixture_id, repr(ground_truth))
    if categories != REQUIRED_CATEGORIES:
        raise FixtureError("missing_category", "dataset", "missing=%s" % sorted(REQUIRED_CATEGORIES - categories))
    return FixtureValidationResult(dataset_version, manifest_hash, categories, checked_files, manifest_files)
