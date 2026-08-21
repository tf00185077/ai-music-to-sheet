# Design record: package-and-certify-first-cli-mvp

_Last review: 2026-08-21 UTC - reviewed commit `4c5f089b1d779c985b980074bd0bf68ccb5c7de8` - approved plan revision `b0ce81a9-2471-4fc4-9464-e41b26a731a0` - board interaction `9e1340c9-8f06-4606-b733-b4b285edac9b`_

Verdict: **cleared for build with required design constraints**. No production code is written by this review. The accepted spec is buildable as a final packaging and certification round only: expose and document one public CLI path, make shell success mean accepted output only, write a complete inspectable bundle, keep non-accepted paths stage-specific and machine-readable, and prove the result from a clean committed tree. This round must not add post-MVP product scope.

## Decision log (append-only - newest first)

### 2026-08-21 - round 1 - first review
- **Changed:** First design gate record for `package-and-certify-first-cli-mvp`; the build is cleared only if it packages the existing certified CLI MVP without changing product scope, maps CLI exit codes from acceptance state, emits no-reference validation evidence without pretending to have ground truth, and makes clean-tree certification executable.
- **Supersedes:** N/A - first review for this build.
- **Carried over:** The certified clean monophonic MP3/MP4, `NoteEvents`, `TimeMap`, source `ScoreIR`, measured MusicXML, EvaluationReport, target-profile, arranged-score, target MusicXML, and non-acceptance contracts remain active. Mixed/polyphonic recordings, stem separation, YouTube ingestion, GUI/web UI, PDF/TAB rendering, manual correction, rich arrangement optimization, transposing/written-pitch semantics, per-note octave wrapping, and multi-instrument orchestration remain outside this MVP.
- **Driver provenance:** artifact-verified @ Paperclip [AIM-14](/AIM/issues/AIM-14#document-plan) plan revision `b0ce81a9-2471-4fc4-9464-e41b26a731a0`; artifact-verified @ Paperclip interaction `9e1340c9-8f06-4606-b733-b4b285edac9b`, accepted `2026-08-21T17:41:49.692Z`; artifact-verified @ repository commit `4c5f089b1d779c985b980074bd0bf68ccb5c7de8`.

## Design Review

**Triage:** structural. This slice crosses the public CLI boundary, README/user contract, shell exit semantics, result/artifact bundle contract, runtime diagnostics, clean-tree certification evidence, and cross-round regression registry.

**Elicit:** prior record loaded: no `docs/decisions/` directory exists. Current decision memory is README, the detailed design document, research notes, `docs/reviewspec/REGISTRY.md`, prior design-review records, prior independent code reviews, the accepted [AIM-14](/AIM/issues/AIM-14#document-plan) plan, and this package spec. Intent, boundary, and invariant gaps were walked. No `ask_user_questions` interaction was posted because no genuine remaining load-bearing user-owned ambiguity blocks the design: the approved plan fixes the outcome and terminal scope; the exact CLI command name, packaging metadata shape, output filenames, report schema fields, fixture generation method, and status code numbers are build-owned if they satisfy this record.

**Reframe:** the system is protecting release trust in the first usable CLI MVP, not merely adding a help page or wrapper. The mis-framing risk is certifying internal Python pipeline behavior while users still cannot install, invoke, interpret, or independently reproduce the CLI from a clean checkout. A user learns failures through CLI JSON, exit code, result manifest, and artifact bundle; maintainers learn release failures through validators, registry rebuild, compile check, deterministic tests, and real ffmpeg/ffprobe MP3/MP4 smoke evidence. Green unit tests could still miss a release where `REVIEW` exits 0, README documents a command not exercised by tests, an accepted bundle lacks required artifacts, or final evidence depends on untracked local files.

## Purpose

Close the first MVP as a documented, command-line product surface that a user can run from a clean checkout and an independent reviewer can certify without hidden local state, while preserving all prior certified musical and target-instrument boundaries.

## Boundary Conditions

- The approved build is `package-and-certify-first-cli-mvp`, approved plan revision `b0ce81a9-2471-4fc4-9464-e41b26a731a0`, accepted board interaction `9e1340c9-8f06-4606-b733-b4b285edac9b`, explore commit `ad33ef0`, and spec commit `4c5f089b1d779c985b980074bd0bf68ccb5c7de8`. [artifact-verified @ Paperclip [AIM-15](/AIM/issues/AIM-15) heartbeat context; artifact-verified @ Paperclip [AIM-14](/AIM/issues/AIM-14#document-plan); artifact-verified @ `git rev-parse HEAD`]
- The repository `HEAD` is exactly `4c5f089b1d779c985b980074bd0bf68ccb5c7de8`, and the local package spec matches the accepted plan's embedded spec text except for a trailing blank line in the plan body extraction. [artifact-verified @ `git rev-parse HEAD`; artifact-verified @ `diff -u <accepted-plan-spec> docs/reviewspec/package-and-certify-first-cli-mvp/spec.md`, 2026-08-21 UTC]
- The package spec passed the Reviewspec structural validator. [artifact-verified @ `python3 .../reviewspec-core--fca75830e7/scripts/validate_spec.py docs/reviewspec/package-and-certify-first-cli-mvp/spec.md`, 2026-08-21 UTC]
- The accepted spec is a final first-MVP packaging/certification round and explicitly excludes mixed/polyphonic recordings, stem separation, YouTube ingestion, GUI/web UI, PDF/TAB rendering, manual correction, rich arrangement optimization, and multi-instrument orchestration. [artifact-verified @ `docs/reviewspec/package-and-certify-first-cli-mvp/spec.md:1-2`; artifact-verified @ `docs/reviewspec/package-and-certify-first-cli-mvp/explore.md:3-9`]
- One documented public CLI entry point must run real local MP3 and MP4 inputs into a requested output directory, print machine-readable job status, and use exit code 0 only for accepted successful output. [artifact-verified @ `docs/reviewspec/package-and-certify-first-cli-mvp/spec.md:4-8`]
- The accepted bundle must include parseable MusicXML, result manifest, EvaluationReport, source and timing traceability artifacts, and target-profile/arranged-score/target MusicXML artifacts when a supported target instrument is requested. [artifact-verified @ `docs/reviewspec/package-and-certify-first-cli-mvp/spec.md:10-14`]
- Invalid files, missing media dependencies, unsupported formats, unsupported musical input, low-confidence output, unsupported target profiles, and unarrangeable targets must exit non-zero with REVIEW or FAIL status and NOT_ACCEPTED result state rather than ACCEPTED. [artifact-verified @ `docs/reviewspec/package-and-certify-first-cli-mvp/spec.md:16-20`]
- README must become user-operational documentation for prerequisites, setup, exact MP3/MP4 CLI commands, target-instrument usage, output files, ACCEPTED/REVIEW/FAIL interpretation, troubleshooting, and first-MVP limitations. [artifact-verified @ `docs/reviewspec/package-and-certify-first-cli-mvp/spec.md:22-26`]
- Final certification evidence must record exact commit and show deterministic tests, all spec validators, compile check, registry build, and real ffmpeg/ffprobe MP3 plus MP4 CLI smoke path passing from a clean committed tree with no required untracked fixtures, caches, or alternate worktree. [artifact-verified @ `docs/reviewspec/package-and-certify-first-cli-mvp/spec.md:28-32`]
- Current `ai_music_to_sheet.__main__` already exposes a module CLI with positional media/output arguments and optional `--target-profile`, but it returns exit code 0 for both `COMPLETED` and `REVIEW`; this is the terminal-contract gap the build must close. [artifact-verified @ `ai_music_to_sheet/__main__.py:10-19`; artifact-verified @ `docs/reviewspec/package-and-certify-first-cli-mvp/explore.md:18-24`]
- Current `process_media_file()` writes staged artifacts and accepts an optional target profile; EvaluationReport is currently only written when reference notes are provided. [artifact-verified @ `ai_music_to_sheet/pipeline.py:45-96`; artifact-verified @ `ai_music_to_sheet/pipeline.py:220-262`; artifact-verified @ `docs/reviewspec/package-and-certify-first-cli-mvp/explore.md:20-24`]
- The active registry lists 15 prior certified intents that remain binding unless formally superseded. [artifact-verified @ `docs/reviewspec/REGISTRY.md:6-26`]
- The broader architecture requires staged, replayable artifacts with provenance/version/confidence and machine-readable validation, and warns that unknown-song machine validation cannot strictly prove every note without ground truth. [artifact-verified @ `README.md:17-24`; artifact-verified @ `docs/superpowers/specs/2026-08-20-audio-to-instrument-score-design.md:7-17`; artifact-verified @ `docs/superpowers/specs/2026-08-20-audio-to-instrument-score-design.md:120-129`]
- Target arrangement remains constrained to one real non-transposing sounded-pitch range-only profile and one score-wide octave shift; packaging must not redefine target support in README, CLI, tests, or smoke evidence. [artifact-verified @ `docs/reviewspec/target-instrument-single-melody-arrangement/design-review.md:3-13`; user-confirmed @ Paperclip interaction `ab9e9fce-464c-4882-891d-bbe18a28dd51`, cited in that prior design record]

## Invariants / Cautions

- Never let shell exit code 0 mean "the program ran" when the result is `REVIEW`, `FAIL`, or `NOT_ACCEPTED`; shell success must mean accepted sheet-music delivery. [artifact-verified @ `docs/reviewspec/package-and-certify-first-cli-mvp/spec.md:4-8`; artifact-verified @ `ai_music_to_sheet/__main__.py:17-19`]
- Never collapse CLI usage errors, invalid files, missing ffmpeg/ffprobe, unsupported media, unsupported musical scope, low confidence, unsupported target profile, unarrangeable target, artifact contract failure, export failure, evaluation failure, and delivery/write failure into one opaque CLI failure. Operator actions differ.
- Never make no-reference user runs claim ground-truth transcription accuracy. Ordinary user output may include an EvaluationReport/runtime validation report only if it explicitly distinguishes contract/risk validation from reference-scored accuracy. [artifact-verified @ `docs/superpowers/specs/2026-08-20-audio-to-instrument-score-design.md:120-129`; artifact-verified @ `docs/reviewspec/first-verified-monophonic-score/spec.md:22-26`]
- Never let README, CLI help, tests, and implementation define separate command, status, output-file, or target-profile contracts. The documented command must be the exercised command, and target support must come from the canonical profile contract. [artifact-verified @ `docs/reviewspec/package-and-certify-first-cli-mvp/spec.md:22-26`; artifact-verified @ `docs/reviewspec/target-instrument-single-melody-arrangement/design-review.md:120-131`]
- Never certify from review prose alone. The final review records evidence, but the evidence must come from executable clean-tree commands and inspectable artifacts.
- Never require committed generated media, an alternate worktree, local caches, or untracked fixtures to prove the final CLI smoke path. Smoke fixtures may be generated into a run/temp directory or committed deliberately as source fixtures, but the proof must be reproducible from the committed tree.
- Never add post-MVP scope while improving packaging: no UI, YouTube, stem separation, broader arrangements, PDF/TAB, manual correction, subjective musicality, or vendor/model selection. [artifact-verified @ `docs/reviewspec/package-and-certify-first-cli-mvp/spec.md:1-2`]
- Never drop cross-round registry coverage. The 15 active prior intents remain binding unless formally amended. [artifact-verified @ `docs/reviewspec/REGISTRY.md:6-26`]

## Failure Map

```
User shell / README command
  -> CLI parser and public entry point
  -> Environment prerequisites: Python import path/package metadata, ffmpeg, ffprobe
  -> Existing media/decode/scope/transcription/NoteEvents/TimeMap/source ScoreIR path
  -> Optional target-profile/arrangement path
  -> MusicXML/export and artifact bundle writer
  -> Runtime validation / EvaluationReport writer
  -> Result manifest, stdout JSON, stderr diagnostics, exit-code mapper
  -> Certification harness: tests, spec validators, registry build, compile, real CLI smoke, clean-tree check
```

| Component | Depends on / path broken | Block vs report | Rollback need | Half-broken behavior | Surviving repair entry point |
|---|---|---|---|---|---|
| README command | User installation/run path | Bad docs block usable MVP; fix docs or command before acceptance | Do not certify a command not executed in smoke | README command differs from tested command | CLI smoke script copies README command text or shares one canonical command constant |
| CLI parser / public entry point | Shell args, media path, output dir, optional target profile | Usage error exits non-zero before job success; structured diagnostic where possible | Do not create accepted result for invalid invocation | Some args parsed but target/profile ignored | `--help`, parser tests, and smoke command expose accepted surface |
| Environment prerequisites | Python package/import, ffmpeg, ffprobe, writable output dir | Missing dependency or unwritable output is environment/delivery failure, not musical REVIEW | Preserve any pre-failure diagnostic file; never accept partial bundle | ffprobe succeeds but ffmpeg missing, or output partially written | Dependency probe and result/stderr category name the missing tool/path |
| Existing source pipeline | Certified media, decode, scope, transcription, NoteEvents, TimeMap, source ScoreIR | Preserve prior REVIEW/FAIL categories and active registry tests | Keep already written artifacts; do not relabel as CLI failure | Source artifacts exist but CLI reports generic failure | Prior validators and stage list inspect saved artifacts |
| Optional target arrangement | Target profile, arrangement feasibility, arranged score | Unsupported/unarrangeable target is NOT_ACCEPTED; do not fall back to generic accepted melody | Preserve source artifacts; do not publish target bundle | Source score accepted but requested target failed | Result manifest lists source diagnostics and target failure stage |
| MusicXML/export and bundle writer | Source or arranged score to parseable MusicXML and manifest paths | Export/delivery failure blocks accepted state | Promote accepted bundle only after required files exist and parse | Result says ACCEPTED but artifact path missing | Bundle manifest validator checks path existence and parseability |
| Runtime validation / EvaluationReport | Contract checks, optional reference scoring, stage versions | Report validation evidence; ground-truth claims only with reference data | Preserve report mode and cited artifacts | No-reference report looks like PASS accuracy proof | EvaluationReport schema includes mode/reference availability and metrics provenance |
| Stdout/stderr/exit mapper | Result manifest, acceptance state, diagnostics | Exit 0 only for ACCEPTED; non-zero for REVIEW/FAIL/NOT_ACCEPTED | Do not let logging corrupt stdout JSON | stdout contains ffmpeg logs plus JSON or malformed status | CLI JSON parser test and stderr separation |
| Certification harness | Clean tree, deterministic suite, validators, registry, compile, real smoke | Blocks final review PASS when evidence missing/dirty | Generated smoke outputs go to temp/run dirs; clean tree remains clean | Final review cites commands but commands are not executable | Independent reviewer reruns exact commands from committed tree |

## Tabletop Scenarios

| Scenario | System observes | System returns / does | Operator next step | Working prior state preserved? |
|---|---|---|---|---|
| README documents `python -m ai_music_to_sheet`, but tests only call `process_media_file()` | Pipeline tests pass; public shell surface is unexercised | Design requires failure of CLI certification until the documented command is smoke-tested for MP3 and MP4 | Add a real CLI smoke using the documented command, then update README or test if they diverge | Yes; prior pipeline tests remain useful but insufficient for package certification |
| Clean MP3 produces low-confidence notes and result manifest says REVIEW | Existing pipeline can write artifacts, but acceptance is `NOT_ACCEPTED` | CLI prints machine-readable result and exits non-zero; result category remains `TRANSCRIPTION_QUALITY`, not success | Inspect notes/evaluation diagnostics or choose a clearer recording; do not treat shell success as delivery | Yes; diagnostic artifacts remain, no accepted output bundle is promoted |
| `ffprobe` is installed but `ffmpeg` is missing on a clean checkout | Source inspection may pass; decode cannot run | CLI exits non-zero with environment/decode diagnostic; no ACCEPTED bundle | Install documented prerequisite or fix PATH; rerun documented command | Yes if result/source diagnostics were written; no accepted score is created |
| Target profile request uses unsupported transposing/written-pitch semantics | Source score could be produced, but target profile is outside approved slice | Requested target job is REVIEW/FAIL and NOT_ACCEPTED with instrument-profile category; no generic score is passed off as target output | Choose `beginner-soprano-recorder` or defer to a later transposition slice | Yes; source artifacts can remain diagnostics but requested target output is not accepted |
| Accepted target run writes MusicXML but omits `arranged_score.json` or `target_profile.json` | MusicXML parses and result may look complete, but target traceability is missing | Bundle contract fails; CLI exits non-zero or final certification fails | Fix bundle writer/manifest, not the arranger | Yes; no accepted bundle until all required paths exist and validate |
| No-reference ordinary user run emits an `EvaluationReport` with `PASS` and accuracy-like fields | Runtime checks passed, but no ground truth was available | Design requires explicit no-reference/runtime-validation mode; cannot claim reference-scored accuracy | Adjust report schema/docs/tests to separate runtime contract validation from corpus scoring | Yes; user can inspect limitations instead of being misled |
| Final review command evidence passes only because generated fixtures/caches were left untracked | Local smoke succeeds, clean checkout cannot reproduce it | Certification gate fails INT-5; final review records dirty or missing evidence as a blocker | Generate fixtures in temp from committed code or commit intentional fixtures; rerun clean-tree proof | Yes; prior certified code remains but final package certification is not passed |

## Failure-Policy Families

| Family | Operations | Failure policy |
|---|---|---|
| CLI usage failures | Missing args, bad option shape, invalid target option syntax | Non-zero before accepted job; concise usage/JSON diagnostic; not a musical REVIEW |
| Environment failures | Missing ffmpeg/ffprobe, package import failure, unwritable output directory | Non-zero environment/decode/delivery category; operator repairs environment |
| Media/source failures | Missing file, unsupported extension/container, corrupt media, no audio stream | Non-zero media/decode category; user provides supported file or codec support changes |
| Musical support and quality failures | Unsupported scope, polyphony, low confidence, unquantizable timing | REVIEW/FAIL and NOT_ACCEPTED with stage-specific reason; preserve diagnostics |
| Target request/arrangement failures | Unsupported profile, transposing/written-pitch request, no single global shift | REVIEW/FAIL and NOT_ACCEPTED with profile/arrangement reason; no fallback to accepted generic melody |
| Artifact contract/export failures | Missing bundle files, invalid JSON, invalid MusicXML, path mismatch | Internal/export/delivery FAIL; block accepted state and final certification |
| Runtime validation vs reference evaluation | No-reference validation, fixed corpus scoring, target arrangement scoring | Keep modes and provenance distinct; only reference-backed reports claim accuracy metrics |
| Certification/release failures | Tests, validators, registry build, compile, CLI smoke, clean tree | Block final review PASS; record exact failing command and preserve prior certified scope |

Merge reductio:
- If `REVIEW` and accepted completion share exit code 0, shell automation cannot distinguish usable sheet music from a request needing human review.
- If missing ffmpeg and unsupported musical scope share one category, an operator may re-record a valid file when they only need to install a dependency, or debug PATH when the input is out of scope.
- If no-reference runtime validation and ground-truth EvaluationReport share one unqualified `PASS`, the MVP falsely claims transcription accuracy on arbitrary user media.
- If target-profile support is duplicated in README examples and arranger constants, documentation can advertise profiles the actual certified contract must reject.
- If final certification is only review text, a later reader cannot rerun the proof and hidden untracked fixtures can fake a green release.

## Fitness Tests

These are architecture-shape tests for the build. They prevent regression to already-identified bad shapes; they do not prove the architecture catches novel mis-framings.

1. **CLI acceptance exit contract:** the documented public CLI exits 0 only when the emitted result has `acceptance: ACCEPTED`, `job_state: COMPLETED`, and `quality_status: PASS`; low-confidence REVIEW, unsupported scope, unsupported profile, unarrangeable target, missing dependency, invalid input, and delivery failure all exit non-zero.
2. **Documented-command smoke:** README MP3 and MP4 commands are either executed verbatim by smoke tests or generated from the same canonical command definition that README uses; pipeline-only tests cannot satisfy INT-1.
3. **Machine-readable stdout boundary:** CLI stdout remains parseable JSON for success and non-accepted runs; stderr may carry human diagnostics, but ffmpeg/ffprobe logs must not corrupt stdout JSON.
4. **Bundle completeness contract:** accepted generic runs have source, canonical audio, note_events, time_map, score_ir, musicxml, result, and EvaluationReport/runtime validation artifacts whose manifest paths exist; accepted target runs additionally have target_profile, arranged_score, and target-instrument MusicXML evidence.
5. **Evaluation non-circularity:** no-reference user runs cannot emit reference-scored accuracy claims; reference/corpus runs must cite reference data and artifact versions, and shifted self-consistent artifacts still fail reference scoring.
6. **Status orthogonality matrix:** invalid file, missing ffprobe, missing ffmpeg, unsupported format, unsupported musical input, low confidence, unsupported target, unarrangeable target, invalid MusicXML, and unwritable output each produce distinct machine-readable stage/category values and never enter ACCEPTED.
7. **Target drift sentinel:** README/CLI-supported target ids are read from the canonical profile registry or checked against it; transposing/written-pitch and per-note-wrapping-only requests remain NOT_ACCEPTED.
8. **Clean-tree certification proof:** from a clean committed tree, deterministic tests, all reviewspec spec validators, compile check, registry build, and real ffmpeg/ffprobe MP3 plus MP4 CLI smoke run without required untracked fixtures, alternate worktrees, or pre-existing caches, and leave no dirty tracked files.
9. **Cross-round registry guard:** all 15 active prior registry intents continue to have passing guarding tests in addition to the new package/certification tests.
10. **Diagnostic survivability:** result bundle validators can inspect saved result, report, JSON artifacts, and MusicXML without invoking the same public CLI path being diagnosed.

## Independent Review

An independent read-only subagent reviewed problem framing and converged on the spec's scope: this is packaging/certification only, not new product scope, and it must preserve the 15 active prior intents. It also converged that prior rounds certified pipeline behavior but not clean-checkout CLI delivery, README install/run instructions, or real CLI smoke evidence.

The independent pass diverged usefully by sharpening five risks that this record adopts as constraints: `EvaluationReport` is overloaded unless no-reference/runtime validation is separated from reference scoring; INT-3's listed failures need distinct stage/category responses; shell exit, product status, acceptance, and release status need an explicit mapping; certification must be executable evidence rather than review text proving itself; and target-instrument rules can drift during README/CLI packaging if not tied to the canonical prior profile contract.

No divergence requires a spec amendment or user question before code. The accepted plan already fixes the terminal outcome: one documented CLI entry point, exit 0 only for accepted output, a complete bundle, README instructions, and clean-tree certification. The remaining choices are build-owned implementation details bounded by the constraints and fitness tests above.

## Implementation Plan

For the build agent, in order:

1. Preserve the existing source pipeline, target arrangement path, stage/category vocabulary, and all prior registry tests before adding package behavior.
2. Choose the smallest public CLI surface that satisfies the approved spec: module invocation is acceptable if documented and smoke-tested; a console script is also acceptable if implemented without creating a second command contract. Whichever surface README documents must be the surface tested.
3. Add or adjust packaging/setup documentation so a clean checkout user can install prerequisites, make the package importable, and run exact MP3 and MP4 commands with an output directory and optional supported target profile.
4. Change CLI exit mapping so only accepted successful output exits 0. REVIEW, FAIL, NOT_ACCEPTED, usage errors, environment failures, and delivery failures exit non-zero while preserving machine-readable diagnostics.
5. Ensure ordinary accepted output bundles include a machine-readable validation/EvaluationReport artifact that explicitly states whether reference data was available; do not claim ground-truth accuracy for no-reference user media.
6. Add bundle validation so accepted generic and target-profile runs cannot omit required source, timing, score, result, evaluation/validation, profile, arranged-score, or MusicXML artifacts.
7. Add real CLI smoke coverage for MP3 and MP4 using ffmpeg/ffprobe from a clean tree. Generate any smoke media from committed code into a temp directory or commit intentional fixtures; do not rely on untracked local files.
8. Update README to document prerequisites, setup, exact commands, target-profile use, output artifacts, ACCEPTED/REVIEW/FAIL and exit-code interpretation, troubleshooting, and first-MVP limitations without advertising post-MVP scope.
9. Add tests derived from the reviewspec risk rule: INT-1, INT-2, INT-3, and INT-4 are Critical because they are user-visible core promises; INT-5 is Core for users but certification-critical for release. Meet Critical scrutiny with real CLI/filesystem/media boundaries and break-testing.
10. Final reviewer evidence must include full deterministic suite, all spec validators, compile check, registry rebuild, real MP3/MP4 CLI smoke, exact commit, and clean worktree status after evidence generation.

## Facts Relied On

- The board-approved plan revision under review is `b0ce81a9-2471-4fc4-9464-e41b26a731a0`, accepted by interaction `9e1340c9-8f06-4606-b733-b4b285edac9b`. [artifact-verified @ Paperclip [AIM-14](/AIM/issues/AIM-14#document-plan) and interaction API, fetched 2026-08-21 UTC]
- The reviewed repository `HEAD` is `4c5f089b1d779c985b980074bd0bf68ccb5c7de8`, matching the spec commit named in [AIM-15](/AIM/issues/AIM-15). [artifact-verified @ `git rev-parse HEAD`, 2026-08-21 UTC]
- The package spec passed the Reviewspec validator. [artifact-verified @ `python3 .../validate_spec.py docs/reviewspec/package-and-certify-first-cli-mvp/spec.md`, 2026-08-21 UTC]
- The accepted plan's embedded package spec and the repository spec have the same substantive intent text; the only observed diff was a trailing blank line in the plan extraction. [artifact-verified @ `diff -u <accepted-plan-spec> docs/reviewspec/package-and-certify-first-cli-mvp/spec.md`, 2026-08-21 UTC]
- There is no `docs/decisions/` directory, so current design memory comes from README, detailed design, research notes, registry, and prior review artifacts. [artifact-verified @ `find docs -maxdepth 2 -type d -print`, 2026-08-21 UTC; artifact-verified @ `docs/reviewspec/package-and-certify-first-cli-mvp/explore.md:7-9`]
- The current CLI exists at `ai_music_to_sheet/__main__.py` and delegates to `process_media_file()` with optional `--target-profile`. [artifact-verified @ `ai_music_to_sheet/__main__.py:10-18`]
- The current CLI returns exit code 0 for `REVIEW`, which conflicts with the new accepted spec's exit-code observable and must be changed by the build. [artifact-verified @ `ai_music_to_sheet/__main__.py:17-19`; artifact-verified @ `docs/reviewspec/package-and-certify-first-cli-mvp/spec.md:4-8`]
- The current pipeline writes source, canonical audio, note events, TimeMap, ScoreIR, MusicXML, target profile, arranged score, result, and EvaluationReport conditionally based on processing path and reference data. [artifact-verified @ `ai_music_to_sheet/pipeline.py:98-262`]
- The current tests exercise real ffmpeg/ffprobe and filesystem artifacts through public Python pipeline/evaluation boundaries, but not the shell CLI as the documented command. [artifact-verified @ `tests/test_first_verified_monophonic_score.py:30-84`; artifact-verified @ `tests/test_target_instrument_single_melody_arrangement.py:53-224`; artifact-verified @ `rg -n "__main__|subprocess" tests ai_music_to_sheet`, 2026-08-21 UTC]
- The active registry has 15 prior certified intents. [artifact-verified @ `docs/reviewspec/REGISTRY.md:6-26`]
- The detailed design says unknown-song machine validation cannot strictly prove every note without reference truth; therefore no-reference CLI output must not pose as reference-scored accuracy. [artifact-verified @ `docs/superpowers/specs/2026-08-20-audio-to-instrument-score-design.md:120-129`; artifact-verified @ `docs/research/midi-ground-truth-benchmarks-2026-08.md:48-50`]

## Links

- README: `README.md`
- Detailed design: `docs/superpowers/specs/2026-08-20-audio-to-instrument-score-design.md`
- Explore: `docs/reviewspec/package-and-certify-first-cli-mvp/explore.md`
- Spec: `docs/reviewspec/package-and-certify-first-cli-mvp/spec.md`
- Registry: `docs/reviewspec/REGISTRY.md`
- Prior design reviews: `docs/reviewspec/first-verified-monophonic-score/design-review.md`, `docs/reviewspec/beat-aware-single-melody-score/design-review.md`, `docs/reviewspec/target-instrument-single-melody-arrangement/design-review.md`
- Prior independent reviews: `docs/reviewspec/first-verified-monophonic-score/review.md`, `docs/reviewspec/beat-aware-single-melody-score/review.md`, `docs/reviewspec/target-instrument-single-melody-arrangement/review.md`
- Ground-truth research: `docs/research/midi-ground-truth-benchmarks-2026-08.md`
- Stem-separation research used only as exclusion boundary: `docs/research/audio-stem-separation-options-2026-08.md`, `docs/research/mature-stem-separation-products-2026-08.md`

## Open Questions

No blocking user-owned questions remain for this design gate.

The following are intentionally build-owned within the approved spec and must be made explicit in build artifacts/tests:

- Exact CLI surface name: `python -m ai_music_to_sheet`, a console script, or both, as long as exactly the documented public entry point is smoke-tested and does not create conflicting contracts.
- Exact package metadata/install shape.
- Exact output filenames and report schema fields, as long as accepted bundle completeness and no-reference/reference provenance are machine-readable.
- Exact numeric non-zero exit codes for REVIEW, FAIL, usage, environment, and delivery failure, as long as 0 is reserved for accepted output.
- Exact smoke fixture generation strategy, as long as the proof is clean-tree reproducible without required untracked artifacts.
