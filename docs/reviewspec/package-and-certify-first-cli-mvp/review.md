# Review: package-and-certify-first-cli-mvp

Reviewed build commit: `f10b9b1b84b8dc321a08f7d573b378fa1e97f9b1`

Verdict: PASS

## Independent Answer Key

| intent | derived tier | observable behavior reviewed |
|--------|--------------|------------------------------|
| INT-1 | Critical | The documented public CLI accepts real MP3 and MP4 inputs plus an output directory, writes the output bundle, emits parseable job status, and exits 0 only for accepted output. |
| INT-2 | Critical | Accepted clean single-melody output contains parseable MusicXML, result manifest, EvaluationReport, source/timing traceability, and target-profile artifacts for a supported target request. |
| INT-3 | Critical | Non-accepted CLI paths for invalid media, missing dependencies, unsupported formats/scope, low confidence, unsupported profile, and unarrangeable target exit non-zero with `REVIEW` or `FAIL`, `NOT_ACCEPTED`, and actionable diagnostics. |
| INT-4 | Critical | README documents install, exact MP3/MP4 commands, target usage, artifacts, status/exit semantics, troubleshooting, and first-MVP limitations without relying on Reviewspec docs. |
| INT-5 | Core | Certification is reproducible from the exact committed tree with the full deterministic suite, all spec validators, compile check, registry build, and real ffmpeg/ffprobe MP3 plus MP4 CLI smoke. |

## Manifest And Boundary Audit

The manifest claims matched the inspected tests and code. The package tests execute `python -m ai_music_to_sheet` in subprocesses, generate real MP3/MP4 media through `ffmpeg`, inspect real filesystem artifacts, parse JSON and MusicXML from disk, and exercise the public CLI exit/status boundary. `rg -n "mock|patch|MonkeyPatch|substitute|fake" tests ai_music_to_sheet scripts` returned no test or implementation mock boundary hits.

Reviewer-owned `INT-3` edge probes also passed for missing file, corrupt `.mp3`, unsupported polyphonic scope, and missing `ffmpeg` with `ffprobe` still available. Each returned non-zero with `NOT_ACCEPTED`, `REVIEW`/`FAIL`, and the expected stage/category diagnostics.

## Break-Testing

All mutations below were temporary and reverted immediately. The worktree was clean after reverts.

| intent | temporary mutation | command | red evidence |
|--------|--------------------|---------|--------------|
| INT-1 | Forced accepted CLI results to return exit code 1. | `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_package_and_certify_first_cli_mvp.py' -k test_int1_readme_mp3_and_mp4_commands_run_through_documented_cli -v` | FAILED for both MP3 and MP4 accepted subtests because return code was 1 instead of 0. |
| INT-2 | Hid `evaluation_report` from the output artifact manifest. | `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_package_and_certify_first_cli_mvp.py' -k test_int2_accepted_cli_bundle_contains_parseable_traceable_artifacts -v` | FAILED with non-zero CLI output and delivery reason `missing required artifact evaluation_report`. |
| INT-3 | Changed CLI mapping so `REVIEW` states returned exit code 0. | `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_package_and_certify_first_cli_mvp.py' -k test_int3_non_accepted_cli_paths_exit_nonzero_with_machine_readable_diagnostics -v` | FAILED on low-confidence, unsupported-profile, and unarrangeable-target cases because non-accepted `REVIEW` returned 0. |
| INT-4 | Changed README accepted-status wording from `Exit code \`0\`` to `Exit code \`zero\``. | `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_package_and_certify_first_cli_mvp.py' -k test_int4_readme_documents_mvp_operation_statuses_and_limits -v` | FAILED on missing README fragment `Exit code \`0\``. |
| INT-5 | Changed `scripts/smoke_cli_mvp.py` success summary from `PASS` to `FAIL`. | `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_package_and_certify_first_cli_mvp.py' -k test_int5_certification_smoke_support_runs_from_clean_checkout_inputs -v` | FAILED because the smoke payload reported `status: FAIL` instead of `PASS`. |

## Verification

- Clean-tree certification at reviewed build commit: `PYTHONDONTWRITEBYTECODE=1 REVIEWSPEC_CORE=/Users/tf00185088/.paperclip/instances/default/companies/0d1b8931-30d8-4820-941e-b9ae5541da25/codex-home/skills/reviewspec-core--fca75830e7 scripts/certify_first_cli_mvp.sh` -> 21 tests passed, 4 specs valid, compile passed, registry rebuilt with 15 active prior intents, MP3/MP4 CLI smoke returned `status: PASS`, and `git status --short` was clean.
- Post-break-test full suite: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v` -> 21 tests passed.
- Spec validator: `python3 /Users/tf00185088/.paperclip/instances/default/companies/0d1b8931-30d8-4820-941e-b9ae5541da25/codex-home/skills/reviewspec-core--fca75830e7/scripts/validate_spec.py docs/reviewspec` -> 4 specs valid.
- Compile check: `PYTHONPYCACHEPREFIX="$PAPERCLIP_RUN_SCRATCH_DIR/pycache-review" python3 -m compileall -q ai_music_to_sheet tests scripts` -> passed.
- Real CLI smoke: `PYTHONDONTWRITEBYTECODE=1 python3 scripts/smoke_cli_mvp.py` -> `status: PASS`; MP3 and MP4 cases returned 0 with `ACCEPTED`, `COMPLETED`, `PASS`, parseable `score.musicxml`, and `evaluation_report.json`.

## Coverage (registry-readable)

| intent | tier | guarding_test | status |
|--------|------|---------------|--------|
| INT-1 | Critical | tests/test_package_and_certify_first_cli_mvp.py::PackageAndCertifyFirstCliMvpTests::test_int1_readme_mp3_and_mp4_commands_run_through_documented_cli | active |
| INT-2 | Critical | tests/test_package_and_certify_first_cli_mvp.py::PackageAndCertifyFirstCliMvpTests::test_int2_accepted_cli_bundle_contains_parseable_traceable_artifacts | active |
| INT-3 | Critical | tests/test_package_and_certify_first_cli_mvp.py::PackageAndCertifyFirstCliMvpTests::test_int3_non_accepted_cli_paths_exit_nonzero_with_machine_readable_diagnostics | active |
| INT-4 | Critical | tests/test_package_and_certify_first_cli_mvp.py::PackageAndCertifyFirstCliMvpTests::test_int4_readme_documents_mvp_operation_statuses_and_limits | active |
| INT-5 | Core | tests/test_package_and_certify_first_cli_mvp.py::PackageAndCertifyFirstCliMvpTests::test_int5_certification_smoke_support_runs_from_clean_checkout_inputs | active |

## Not Covered / Deliberately Unverified

Mixed/polyphonic commercial recordings beyond the unsupported-scope gate, stem separation, YouTube ingestion, GUI/web UI, PDF/TAB rendering, manual correction, rich arrangement optimization, transposing or written-pitch semantics, per-note octave wrapping, and multi-instrument orchestration remain outside this approved MVP slice.

The smoke media is deterministic generated clean single-melody MP3/MP4 coverage. It is not a claim that arbitrary noisy real-world recordings transcribe accurately without human review.
