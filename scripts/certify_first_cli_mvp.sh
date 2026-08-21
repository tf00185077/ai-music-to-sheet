#!/usr/bin/env sh
set -eu

PYTHON_BIN="${PYTHON:-python3}"
if [ -z "${REVIEWSPEC_CORE:-}" ]; then
  echo "Set REVIEWSPEC_CORE to the reviewspec-core skill directory before running certification." >&2
  exit 2
fi

SCRATCH_ROOT="${PAPERCLIP_RUN_SCRATCH_DIR:-${TMPDIR:-/tmp}}"
PYCACHE_DIR="$SCRATCH_ROOT/ai-music-to-sheet-pycache"

PYTHONDONTWRITEBYTECODE=1 "$PYTHON_BIN" -m unittest discover -s tests
"$PYTHON_BIN" "$REVIEWSPEC_CORE/scripts/validate_spec.py" docs/reviewspec
PYTHONPYCACHEPREFIX="$PYCACHE_DIR" "$PYTHON_BIN" -m compileall -q ai_music_to_sheet tests scripts
"$PYTHON_BIN" "$REVIEWSPEC_CORE/scripts/build_registry.py"
"$PYTHON_BIN" scripts/smoke_cli_mvp.py
git diff --exit-code -- docs/reviewspec/REGISTRY.md
git status --short
