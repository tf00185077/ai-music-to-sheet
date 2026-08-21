# Claims Manifest: package-and-certify-first-cli-mvp

Spec: `docs/reviewspec/package-and-certify-first-cli-mvp/spec.md`
Design review: `docs/reviewspec/package-and-certify-first-cli-mvp/design-review.md`
Build commit: recorded in the final issue update after commit creation.

## Behavior Claims

| behavior | test_layer | real_environment | self_tier |
|---|---|---|---|
| INT-1 | integration | `tests/test_package_and_certify_first_cli_mvp.py::PackageAndCertifyFirstCliMvpTests::test_int1_readme_mp3_and_mp4_commands_run_through_documented_cli` runs the documented `python -m ai_music_to_sheet` command in a subprocess from the repo root, generates real MP3 and MP4 inputs through ffmpeg, and inspects real output directories and `result.json`. No mocks. | Critical |
| INT-2 | integration | `tests/test_package_and_certify_first_cli_mvp.py::PackageAndCertifyFirstCliMvpTests::test_int2_accepted_cli_bundle_contains_parseable_traceable_artifacts` runs the CLI with the supported target profile, inspects real JSON artifacts on disk, parses delivered MusicXML with `xml.etree.ElementTree`, and verifies no-reference EvaluationReport provenance. No mocks. | Critical |
| INT-3 | integration | `tests/test_package_and_certify_first_cli_mvp.py::PackageAndCertifyFirstCliMvpTests::test_int3_non_accepted_cli_paths_exit_nonzero_with_machine_readable_diagnostics` runs the CLI subprocess against real generated media, unsupported file format, PATH-based missing ffprobe environment, unsupported target profile, low-confidence input, and unarrangeable target input, then asserts non-zero exit and machine-readable NOT_ACCEPTED diagnostics. No mocks. | Critical |
| INT-4 | integration | `tests/test_package_and_certify_first_cli_mvp.py::PackageAndCertifyFirstCliMvpTests::test_int4_readme_documents_mvp_operation_statuses_and_limits` reads the committed README and asserts user-facing prerequisites, setup, commands, artifacts, statuses, troubleshooting, and first-MVP limitations. No mocks. | Critical |
| INT-5 | integration | `tests/test_package_and_certify_first_cli_mvp.py::PackageAndCertifyFirstCliMvpTests::test_int5_certification_smoke_support_runs_from_clean_checkout_inputs` executes `scripts/smoke_cli_mvp.py`, which generates real MP3/MP4 fixtures in scratch/temp storage, invokes the documented CLI, parses stdout JSON, and verifies persisted MusicXML and EvaluationReport artifacts. No committed media fixtures or caches required. | Core |

## Red Before Green

Initial package-round test run before implementation:

`python3 -m unittest discover -s tests -p 'test_package_and_certify_first_cli_mvp.py' -v` -> FAILED.

Observed red signals:

- INT-1 and INT-4: README did not contain the documented MP3/MP4 CLI commands or operational status/output guidance.
- INT-2: accepted no-reference CLI bundle did not expose `evaluation_report`.
- INT-3: `REVIEW` results returned exit code 0.
- INT-5: `scripts/smoke_cli_mvp.py` did not exist.

## Self Break-Testing

All temporary mutations below were reverted before the final green runs.

| behavior | temporary mutation | command | red evidence |
|---|---|---|---|
| INT-1 | Changed the CLI to return exit code 1 even for accepted output. | `python3 -m unittest discover -s tests -p 'test_package_and_certify_first_cli_mvp.py' -k test_int1_readme_mp3_and_mp4_commands_run_through_documented_cli -v` | FAILED on MP3 and MP4 subtests because accepted CLI runs returned 1 instead of 0. |
| INT-2 | Removed `evaluation_report` from the result artifact manifest after writing the file. | `python3 -m unittest discover -s tests -p 'test_package_and_certify_first_cli_mvp.py' -k test_int2_accepted_cli_bundle_contains_parseable_traceable_artifacts -v` | FAILED because the bundle validator returned `DELIVERY` / `missing required artifact evaluation_report` and the CLI exited non-zero. |
| INT-3 | Restored the old CLI mapper where `REVIEW` returned exit code 0. | `python3 -m unittest discover -s tests -p 'test_package_and_certify_first_cli_mvp.py' -k test_int3_non_accepted_cli_paths_exit_nonzero_with_machine_readable_diagnostics -v` | FAILED on low-confidence, unsupported-profile, and unarrangeable-target `REVIEW` cases because they returned 0. |
| INT-4 | Changed README's accepted status wording from `Exit code \`0\`` to `Exit code \`zero\``. | `python3 -m unittest discover -s tests -p 'test_package_and_certify_first_cli_mvp.py' -k test_int4_readme_documents_mvp_operation_statuses_and_limits -v` | FAILED on the missing `Exit code \`0\`` fragment. |
| INT-5 | Changed `scripts/smoke_cli_mvp.py` success summary status from `PASS` to `FAIL`. | `python3 -m unittest discover -s tests -p 'test_package_and_certify_first_cli_mvp.py' -k test_int5_certification_smoke_support_runs_from_clean_checkout_inputs -v` | FAILED because the smoke payload reported `status: FAIL` instead of `PASS`. |

The INT-2 break-test initially exposed a real fallback bug: `pipeline.py` used `CATEGORY_DELIVERY` in the delivery-error path without importing it. That import was fixed, then INT-2 was break-tested again to the intended missing-artifact red signal above.

## Verification

Pre-commit verification after implementation and break-test reverts:

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v` -> `Ran 21 tests`, `OK`.
- `python3 /Users/tf00185088/.paperclip/instances/default/companies/0d1b8931-30d8-4820-941e-b9ae5541da25/codex-home/skills/reviewspec-core--fca75830e7/scripts/validate_spec.py docs/reviewspec` -> 4 spec files checked, all structurally valid.
- `PYTHONPYCACHEPREFIX="$PAPERCLIP_RUN_SCRATCH_DIR/pycache" python3 -m compileall -q ai_music_to_sheet tests scripts` -> passed.
- `python3 /Users/tf00185088/.paperclip/instances/default/companies/0d1b8931-30d8-4820-941e-b9ae5541da25/codex-home/skills/reviewspec-core--fca75830e7/scripts/build_registry.py` -> registry written, 15 active intents, no structural problems, no diff to `docs/reviewspec/REGISTRY.md`.
- `python3 scripts/smoke_cli_mvp.py` -> `status: PASS`, MP3 and MP4 cases returned 0 with `ACCEPTED`, `COMPLETED`, `PASS`, parseable `score.musicxml`, and `evaluation_report.json`.

## Implemented Surface

- One documented public CLI surface: `python -m ai_music_to_sheet`.
- Package metadata for editable installation from a clean checkout.
- CLI exit code 0 only for `ACCEPTED` + `COMPLETED` + `PASS`.
- Machine-readable stdout result for successful and non-accepted processing paths.
- No-reference runtime EvaluationReport for ordinary user runs, with `mode: runtime_validation` and `reference_available: false`.
- Accepted bundle validation for source, canonical audio metadata, note events, time map, ScoreIR, MusicXML, EvaluationReport, and target-profile artifacts where requested.
- README operating instructions and MVP limitations.
- Reproducible smoke/certification support using generated temporary media.

## Not Covered / Residual Risk

- Mixed or polyphonic commercial recordings, stem separation, YouTube ingestion, GUI/web UI, PDF/TAB rendering, manual correction, rich arrangement optimization, transposing/written-pitch semantics, per-note octave wrapping, and multi-instrument orchestration remain outside this approved slice.
- Smoke media is deterministic generated sine-wave melody coverage, not certification for arbitrary noisy real-world recordings.
- The full certification script expects the reviewer/agent environment to provide `REVIEWSPEC_CORE`; the standalone MP3/MP4 CLI smoke script does not require untracked repository fixtures.
