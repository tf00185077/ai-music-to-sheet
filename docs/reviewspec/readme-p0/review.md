# Review: README P0 verifiable MVP (G5 independent gate)

Verdict: PASS

- Reviewer: AIM-4 independent Reviewspec Code Reviewer (agent 03193d7f), independent of the Build author.
- Reviewed build: `docs/reviewspec/readme-p0/` (spec.md / manifest.md), README.md, `p0/`, `tests/`, `scripts/`, `contracts/`, `fixtures/`, `.github/`.
- Branch: `v2/autonomous/paperclip`.
- Starting SHA (pre-build): `f4ff4de0e6afaf3e82698afa97d20ef7c73a8e92`.
- **Candidate SHA (exact): `52273eb416af7cb6c49b0807645cc1d594456bad`** — resolved as the branch HEAD, cross-checked against the runtime `payload.candidate_sha` recorded by the canonical command. The manifest's non-self-referential SHA mechanism (a commit cannot embed its own hash; the SHA is captured at runtime via `git rev-parse HEAD`) is sound and its recorded value equals HEAD.
- Review method: a fresh isolated `git clone` of the repo checked out at the exact candidate SHA (never the concurrently-mutated shared worktree, which AIM-3 holds). All commands, tests, and break-tests below were run in that isolated clean checkout. No production code was modified in the shared worktree; all reviewer mutations were applied only in the throwaway clone and reverted immediately (`git status` verified 0 dirty files after every revert).

## Scope of this gate (what a human may skip / must still check)

P0 validates **deterministic artifact contracts, provenance/integrity, evaluator correctness, fixtures, and the one-command verification gate** — NOT real-model transcription/arrangement quality. The manifest's `scope_boundary` explicitly disclaims any holdout, real-song, unseen-song, separation, or perceptual-quality claim, and no such claim is made anywhere in the evidence. This is honest: the pipeline uses deterministic stubs and transparent synthetic fixtures. Confirmed **no fixture, report, or metric is misrepresented as holdout or as model-quality evidence.** A human still owns external correctness (whether these contracts are the *right* contracts) and all future P1 model-quality work.

## Re-derived risk tiers (independent, from spec — not trusting the manifest)

Every intent INT-1…INT-10 has `user_visible: no`. The Critical tier requires `user_visible AND sensitivity ∈ {money,data-loss,security,core-promise}`; with `user_visible: no`, **none are Critical**. All ten are important logic whose breakage damages the P0 contract baseline → **Core**. Required scrutiny for Core: integration/unit against real deps at the boundary **+ break-testing**. This matches the manifest's self-tier (`Core` for all ten; unit for INT-7, integration for the rest) — no tier dispute. E2E is therefore not mandated; trust is bought by break-test survival, which was performed below.

## Canonical command evidence

Command (run in the isolated clean checkout at the candidate SHA):

```
./scripts/verify-p0 --output artifacts/p0/latest
```

- Exit code: **0**. Output: `P0 PASS: 7/7 groups, 32/32 checks`, `candidate_sha=52273eb…`.
- `process-test-report.json`: `status=success`, `candidate_sha=52273eb…`, `dirty_tree_before_run=false`, `automatic_benchmark=true`.
- Coverage integrity: `expected_checks == executed_checks`, **32 == 32, no skips, no empty groups**; all 7 acceptance groups A–G `passed=true`.
- Both legal modes present: 2 EvaluationReports (`evaluation-transcription.json`, `evaluation-arrangement.json`).
- Named outputs all emitted: `process-test-report.json`, `provenance-index.json` (root = aggregate ProcessTestReport, **15-artifact traceable lineage**), `verify.log`, `samples/{source-media,transcription-track-ir,arrangement-track-ir}.json`, `artifact-store/`.
- Full accumulated suite (all 7 test modules): **34/34 tests OK** (32 gate checks + 2 CLI meta-tests, the latter excluded from `TEST_MODULES` to avoid subprocess recursion).
- Spec structural validation (`validate_spec.py`): **PASS**, structurally valid.

## Fail-closed behavior independently confirmed

The gate cannot pass on a bad run. Verified by direct reproduction in clean synthetic committed repos:
- **Corrupted fixture** → nonzero, `status=failed` (caught redundantly by dirty-tree guard, fixture checksum/size gate, and the in-suite `test_d` sentinel).
- **Missing `expected-checks.json`** → nonzero (`_load_expected` raises).
- **Forced low evaluator score** (`P0_FORCE_LOW_SCORE=1`) → nonzero, `failure.family=evaluator_numeric` (the env var poisons the in-suite pipeline tests, which the gate surfaces).
- **Dirty tree** → nonzero, "official verification requires a clean checkout".

## Break-testing (the teeth of the gate)

For each intent I introduced the smallest production mutation that should violate the observable, ran a semantically-related test, and confirmed it went **red**, then reverted (tree clean after each). All mutations were single-line unless noted.

| intent | production mutation (in isolated clone) | sentinel test | result |
|--------|------------------------------------------|---------------|--------|
| INT-1 | drop `state_transition` fail-closed raise (`contracts._validate_common`) | `test_a_state_transitions_and_numeric_bounds_fail_closed` | RED ✓ |
| INT-2 | drop `mode_provenance` raise for missing transcription evidence (`contracts._validate_track_ir`) | `test_mode_and_instrument_shapes_are_distinct_and_truthful` | RED ✓ |
| INT-3 | drop `unsupported_major` raise (`contracts._validate_common`) | `test_b_same_major_extension_reads_and_unsupported_major_rejects` | RED ✓ |
| INT-4 | disable fixture `checksum_mismatch` gate (`fixtures.validate_fixture_dataset`) | `test_d_missing_or_corrupt_fixture_stops_validation` | RED ✓ |
| INT-5 | disable `missing_upstream` detection in `ArtifactStore.get` | `test_c_delete_replace_and_forge_are_detected` | RED ✓ |
| INT-6 | make `semantically_equal` always return `True` (`contracts`) | `test_semantic_comparator_detects_musical_change_and_allows_nonsemantic_change` | RED ✓ |
| INT-7 | change tolerance from inclusive `<= t+ε` to exclusive `< t-ε` (`evaluator._match`) | `test_e_tolerance_boundary_is_inclusive_and_one_to_one` | RED ✓ |
| INT-8 | drop `below_threshold_false_pass` raise (`reporting.validate_process_report`) | `test_f_missing_fact_low_score_changed_reference_and_manual_mix_fail` | RED ✓ |
| INT-9 | disable cross-mode boundary stop (`pipeline.run_mode_pipeline`) | `test_g_absent_unresolved_cross_mode_and_stale_flows_stop_at_boundary` | RED ✓ |
| INT-10 | skip `provenance-index.json` emission on the clean run (`verifier.run`) | `test_g_clean_checkout_command_writes_complete_evidence` | RED ✓ |

**All ten intents survive** (i.e. their tests genuinely catch the break). No sentinel stayed green when its behavior was broken.

### INT-10 defense-in-depth note (positive finding, not a defect)
While break-testing INT-10 I found the fail-closed observable is guarded by **multiple mutually-backstopping layers**: removing any single guard (the verifier's failed-check gate, the force-low-score block, the dirty-tree check, or the fixture checksum/size gates) still yields a nonzero exit because another layer catches the bad run — and the deepest backstop is an in-suite unit test that itself turns red (which the gate then reports). Producing a false green requires *also deleting the guarding unit test*, which is exactly the gaming the cross-round rules forbid and which this gate would catch. This is the opposite of fake-green: the behavior is hard to break, not easy to hide. The clean red recorded above breaks the positive evidence-emission path directly.

## Boundary reality audit (manifest claims vs. reality)

The manifest claims every layer runs against real boundaries with "no mock." Independently confirmed by reading the tests:
- Real on-disk JSON serialization to real `tempfile` directories and committed schemas (contracts).
- Real WAV/JSON bytes, real `hashlib.sha256` streaming, real filesystem deletion/mutation, real external manifest lock (fixtures).
- Real on-disk `ArtifactStore` graphs with real recursive content-hash resolution (provenance).
- Real production evaluator with real numeric inputs, no mocked matcher (evaluators).
- Real `subprocess` invocation of the executable POSIX `./scripts/verify-p0`, real clean synthetic **git** repos, real exit codes, real output files, committed CI workflow (CLI/delivery).

**No mock stands in for any claimed real boundary.** No fake-green patterns found (every negative path uses `assertRaises` on a specific error `code`; every positive path asserts observable values).

## Reproducibility

Two independent clean runs produce **semantically-equal** musical artifacts (both EvaluationReports semantic-equal; `test_d_same_inputs_versions_parameters_and_seed_are_reproducible` confirms the whole SourceMedia→…→ProcessTestReport pipeline chain is semantically equal across runs). The top-level aggregate `ProcessTestReport` differs between runs *only* because its `verify.log` embeds the unittest runner's wall-clock **timings**, changing that log's checksum — this is a run-timestamp wrapper, outside INT-6's "musically equivalent artifacts" scope, and is not a defect.

## Cross-round regression

`docs/reviewspec/` contains a single build folder (`readme-p0`); this is **round 1** with no prior certified intents and no pre-existing `REGISTRY.md`. There are therefore no prior guarding tests to regress. The registry is (re)built from this review below.

## CI / delivery

`.github/workflows/verify-p0.yml` runs the exact canonical command, retains `artifacts/p0/latest` with `if: always()` and `if-no-files-found: error`. The `verify-p0` script is executable. Matches `test_g_ci_runs_canonical_command_and_always_retains_evidence`. The manifest covers all 10 intents with the exact required fields (`test_g_claims_manifest_covers_every_intent_with_exact_fields` passes).

## Findings

No internal-defect findings. No spec-ambiguity findings. Every spec-listed intent is verified by a trustworthy test (covers the intent, survives break-testing, real boundary where claimed).

## Coverage map

**Covered (a human may skip manual testing within this scope):** INT-1…INT-10 — versioned artifact contracts + semantic round trips + structured rejections; truthful mode/instrument boundaries; compatible evolution + traceable migration; immutable licensed fixture manifests; end-to-end provenance & cache integrity; reproducible validation; evaluator control-answer correctness incl. numeric safety; truthful machine-readable success/failure reports with human-correction isolation; deterministic two-mode pipeline with correct negative-flow boundaries; one-command fail-closed verification with retained evidence and CI.

**Not covered / deliberately unverified (still needs human eyes):** real-model transcription/arrangement accuracy; real-song / unseen-song / holdout performance; source separation and perceptual quality; any P1 feature behavior. These are explicitly out of P0 scope and are NOT claimed by this PASS.

## Coverage (registry-readable)

| intent | tier | guarding_test | status |
|--------|------|---------------|--------|
| INT-1 | Core | tests/test_contracts.py::SchemaContractTests::test_a_state_transitions_and_numeric_bounds_fail_closed | active |
| INT-2 | Core | tests/test_contracts.py::SchemaContractTests::test_mode_and_instrument_shapes_are_distinct_and_truthful | active |
| INT-3 | Core | tests/test_contracts.py::SchemaContractTests::test_b_same_major_extension_reads_and_unsupported_major_rejects | active |
| INT-4 | Core | tests/test_fixtures.py::FixtureTests::test_d_missing_or_corrupt_fixture_stops_validation | active |
| INT-5 | Core | tests/test_provenance.py::ProvenanceTests::test_c_delete_replace_and_forge_are_detected | active |
| INT-6 | Core | tests/test_contracts.py::SchemaContractTests::test_semantic_comparator_detects_musical_change_and_allows_nonsemantic_change | active |
| INT-7 | Core | tests/test_evaluators.py::EvaluatorTests::test_e_tolerance_boundary_is_inclusive_and_one_to_one | active |
| INT-8 | Core | tests/test_pipeline_reports.py::PipelineAndReportTests::test_f_missing_fact_low_score_changed_reference_and_manual_mix_fail | active |
| INT-9 | Core | tests/test_pipeline_reports.py::PipelineAndReportTests::test_g_absent_unresolved_cross_mode_and_stale_flows_stop_at_boundary | active |
| INT-10 | Core | tests/test_verify_cli.py::VerifyCommandTests::test_g_clean_checkout_command_writes_complete_evidence | active |
