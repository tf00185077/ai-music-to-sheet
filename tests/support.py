from __future__ import annotations

import copy
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, Iterator


REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = REPO_ROOT / "fixtures" / "p0" / "v1"


def changed(value: Dict[str, Any], *path: str, replacement: Any) -> Dict[str, Any]:
    result = copy.deepcopy(value)
    cursor: Any = result
    for key in path[:-1]:
        cursor = cursor[key]
    cursor[path[-1]] = replacement
    return result


def read_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def temporary_directory() -> Iterator[Path]:
    return tempfile.TemporaryDirectory(prefix="p0-test-")


def clone_committed_repo(destination: Path) -> Path:
    checkout = destination / "checkout"
    shutil.copytree(
        REPO_ROOT,
        checkout,
        ignore=shutil.ignore_patterns(".git", "artifacts", "__pycache__", "*.pyc"),
    )
    commands = (
        ["git", "init", "--quiet"],
        ["git", "config", "user.name", "P0 Test"],
        ["git", "config", "user.email", "p0-test@example.invalid"],
        ["git", "add", "."],
        ["git", "commit", "--quiet", "-m", "synthetic clean test candidate"],
    )
    for command in commands:
        subprocess.run(command, cwd=str(checkout), check=True, capture_output=True, text=True)
    return checkout


def copy_fixture_dataset(destination: Path) -> Path:
    target = destination / "v1"
    shutil.copytree(FIXTURE_ROOT, target)
    shutil.copy2(FIXTURE_ROOT.parent / "manifest-lock.json", destination / "manifest-lock.json")
    return target


def clean_process_environment() -> Dict[str, str]:
    environment = dict(os.environ)
    environment.pop("P0_FORCE_LOW_SCORE", None)
    return environment
