# Design record: target-instrument-single-melody-arrangement

_Last review: 2026-08-21 UTC - reviewed commit `4596f80183d01ea5be2bb53f859d662f7de72c4e` - approved plan revision `27b34ff1-30ab-4cfd-b63b-c0a7b8a47d49` - board interaction `ab9e9fce-464c-4882-891d-bbe18a28dd51`_

Verdict: **cleared for build with required design constraints**. No production code is written by this review. The approved spec is buildable only as the first target-instrument arrangement contract for a clean single-melody, non-transposing, sounded-pitch range-only profile. The only supported pitch repair in this slice is one score-wide octave shift; if no single shift fits the whole melody, the result must be REVIEW or FAIL rather than accepted sheet music.

## Decision log (append-only - newest first)

### 2026-08-21 - round 1 - first review after answered design questions
- **Changed:** First design gate record for `target-instrument-single-melody-arrangement`; the build is cleared only if it introduces an explicit target profile contract, a distinct arranged score artifact, a single-global-octave-shift arrangement policy, arranged MusicXML export, arrangement evaluation metrics, and stage-specific profile/arrangement failure reasons.
- **Supersedes:** N/A - first review for this build.
- **Carried over:** The certified clean monophonic MP3/MP4, `NoteEvents`, `TimeMap`, source `ScoreIR`, measured MusicXML, evaluation, and non-acceptance contracts remain active. Mixed/polyphonic recordings, stem separation, YouTube ingestion, GUI/web UI, PDF/TAB rendering, manual correction, rich difficulty optimization, subjective musicality, transposing/written-pitch instruments, per-note octave wrapping, and multi-instrument orchestration remain outside this round.
- **Driver provenance:** artifact-verified @ Paperclip [AIM-10](/AIM/issues/AIM-10#document-plan) plan revision `27b34ff1-30ab-4cfd-b63b-c0a7b8a47d49`; artifact-verified @ repository commit `4596f80183d01ea5be2bb53f859d662f7de72c4e`; user-confirmed @ Paperclip interaction `ab9e9fce-464c-4882-891d-bbe18a28dd51`, result summary: "MVP decision: use one real non-transposing sounding-pitch range-only profile. Permit only one score-wide octave shift; if no single shift fits the entire melody, return REVIEW/FAIL. Defer transposing/written-pitch semantics and per-note octave wrapping."

## Design Review

**Triage:** structural. This slice crosses the public request contract, target profile semantics, source `ScoreIR` handoff, arrangement transformation policy, artifact contracts, MusicXML export, status/acceptance policy, evaluation, and cross-round regression boundaries.

**Elicit:** prior record loaded: no `docs/decisions/` directory exists, and no prior `design-review.md` exists for this build. The current decision memory is README, detailed design, target explore/spec artifacts, research notes, registry, prior design-review records, and prior independent review artifacts. Intent, boundary, and invariant gaps were walked. A prior `ask_user_questions` interaction was posted for the two load-bearing user-owned product choices and is now answered. No further blocking user-owned ambiguity remains for this design gate; exact first profile id/name/range, schema field names, status category names, and numeric evaluation thresholds are build-owned if they meet the constraints in this record.

**Reframe:** the system is protecting user trust in instrument-specific playability, not merely adding an instrument label to a generic melody part. The mis-framing risk is treating range-fitted or MusicXML-consistent output as an arrangement while ignoring pitch-domain semantics, contour-preserving shift policy, source traceability, or stage-specific failure reasons. A user learns target arrangement failure through REVIEW/FAIL with an instrument-profile or arrangement reason; maintainers learn corpus failures through range-fit and rhythm-preservation metrics in `EvaluationReport`. Green tests could still miss a false promise where the accepted score is only renamed, uses written/transposing pitch semantics not supported by this slice, or uses per-note octave wrapping that keeps every note in range while damaging the melody contour.

## Purpose

Advance from a generic beat-aware single-melody score to the first inspectable target-instrument arrangement loop: a declared supported profile constrains the source `ScoreIR`, produces a traceable arranged score, and exports MusicXML for that arranged score while refusing unsupported or unarrangeable target requests.

## Boundary Conditions

- The approved build is `target-instrument-single-melody-arrangement`, plan revision `27b34ff1-30ab-4cfd-b63b-c0a7b8a47d49`, and approved planning commit `4596f80183d01ea5be2bb53f859d662f7de72c4e`. [artifact-verified @ Paperclip [AIM-10](/AIM/issues/AIM-10#document-plan) document fetched 2026-08-21; artifact-verified @ `git rev-parse HEAD`, 2026-08-21 UTC]
- The repository `HEAD` is exactly the approved planning commit, and the target spec has no diff from that commit. [artifact-verified @ `git rev-parse HEAD`; artifact-verified @ `git diff --exit-code 4596f80183d01ea5be2bb53f859d662f7de72c4e -- docs/reviewspec/target-instrument-single-melody-arrangement/spec.md`, 2026-08-21 UTC]
- The spec validator passed for `docs/reviewspec/target-instrument-single-melody-arrangement/spec.md`. [artifact-verified @ `python .../reviewspec-core--fca75830e7/scripts/validate_spec.py docs/reviewspec/target-instrument-single-melody-arrangement/spec.md`, 2026-08-21 UTC]
- The approved spec adds the first target-instrument arrangement contract for a supported single-melody profile and excludes mixed recordings, stem separation, YouTube ingestion, manual correction, PDF/TAB export, rich difficulty reduction, subjective musicality, and multi-instrument orchestration. [artifact-verified @ `docs/reviewspec/target-instrument-single-melody-arrangement/spec.md:1-2`; artifact-verified @ [AIM-11](/AIM/issues/AIM-11) issue description]
- The completed result must identify the requested supported profile and include an arranged score artifact citing source job, source media, source `ScoreIR`, and timing artifacts. [artifact-verified @ `docs/reviewspec/target-instrument-single-melody-arrangement/spec.md:4-8`]
- Arranged notes must cite source score-note identities, keep the source measure, beat, and notated-duration sequence, expose pitch transformations, and stay inside the target profile range. [artifact-verified @ `docs/reviewspec/target-instrument-single-melody-arrangement/spec.md:10-14`]
- Delivered MusicXML must be parseable as one part for the requested instrument and must match the arranged score's part name, note count, pitch order, measure positions, durations, and range constraints. [artifact-verified @ `docs/reviewspec/target-instrument-single-melody-arrangement/spec.md:16-20`]
- Unsupported or unarrangeable target requests must return REVIEW or FAIL with an instrument-profile or arrangement reason instead of accepted sheet music. [artifact-verified @ `docs/reviewspec/target-instrument-single-melody-arrangement/spec.md:22-26`]
- The fixed corpus must report arrangement PASS/REVIEW/FAIL with target profile, source `ScoreIR`, arranged score, MusicXML versions, range-fit results, and rhythm-preservation results. [artifact-verified @ `docs/reviewspec/target-instrument-single-melody-arrangement/spec.md:28-32`]
- This slice's pitch semantics are non-transposing and sounded-pitch range-only; transposing or written-pitch profiles are deferred and must be rejected or unsupported in this build. [user-confirmed @ Paperclip interaction `ab9e9fce-464c-4882-891d-bbe18a28dd51`, answer `profile_pitch_semantics=non_transposing_sounding_range_only`, resolved 2026-08-21]
- This slice's octave movement policy is one score-wide octave shift. Per-note octave wrapping is deferred; if no single global shift fits the whole melody, return REVIEW or FAIL. [user-confirmed @ Paperclip interaction `ab9e9fce-464c-4882-891d-bbe18a28dd51`, answer `octave_transform_policy=single_global_octave_shift`, resolved 2026-08-21]
- The broader architecture separates faithful transcription and instrument arrangement after song/score understanding; `InstrumentProfile` is the target instrument constraint artifact, `ScoreIR` is the core score model, and MusicXML/MIDI are adapters rather than core models. [artifact-verified @ `README.md:10-15`; artifact-verified @ `README.md:73-87`; artifact-verified @ `docs/superpowers/specs/2026-08-20-audio-to-instrument-score-design.md:17`; artifact-verified @ `docs/superpowers/specs/2026-08-20-audio-to-instrument-score-design.md:80-94`]
- The current certified code produces source `ScoreIR` after `TimeMap`, then exports MusicXML from that source `ScoreIR`; it has no target profile, arrangement stage, arranged score artifact, or target-aware CLI request surface. [artifact-verified @ `ai_music_to_sheet/pipeline.py:144-160`; artifact-verified @ `ai_music_to_sheet/__main__.py:10-18`; artifact-verified @ `rg -n "arrang|instrument|profile|target" ai_music_to_sheet`, 2026-08-21 UTC]
- Current stage/category constants separate media, decode, scope, transcription, note events, time map, quantization, source `ScoreIR`, MusicXML, evaluation, and delivery failures; there are not yet profile or arrangement categories. [artifact-verified @ `ai_music_to_sheet/contracts.py:19-43`]
- Current evaluation covers transcription and timing metrics; arrangement range-fit and rhythm-preservation metrics must extend the evaluation/report contract rather than creating a parallel status vocabulary. [artifact-verified @ `ai_music_to_sheet/evaluation.py:53-76`; artifact-verified @ `ai_music_to_sheet/evaluation.py:119-134`; artifact-verified @ `docs/reviewspec/target-instrument-single-melody-arrangement/spec.md:28-32`]
- The active registry lists ten prior certified intents that must continue to have passing guarding tests unless formally superseded. [artifact-verified @ `docs/reviewspec/REGISTRY.md:6-21`]
- Research keeps stem separation, vendor APIs, mixed-audio benchmarking, and predicted-MIDI-only correctness claims out of this slice. [artifact-verified @ `docs/research/audio-stem-separation-options-2026-08.md:1-10`; artifact-verified @ `docs/research/mature-stem-separation-products-2026-08.md:21-22`; artifact-verified @ `docs/research/midi-ground-truth-benchmarks-2026-08.md:48-50`]

## Invariants / Cautions

- Never promote a target-instrument result to accepted sheet music if the target "arrangement" is only a renamed generic melody part. The arranged score must be a distinct artifact with target profile, source score references, and pitch transformation traceability. [artifact-verified @ `docs/reviewspec/target-instrument-single-melody-arrangement/spec.md:4-18`; user-confirmed @ interaction `ab9e9fce-464c-4882-891d-bbe18a28dd51`]
- Never overwrite or mutate the source `ScoreIR` to make an arranged score. Preserve source `ScoreIR` and create a separate arranged score that cites it. [artifact-verified @ `docs/reviewspec/target-instrument-single-melody-arrangement/explore.md:18-24`; artifact-verified @ `ai_music_to_sheet/pipeline.py:150-160`]
- Never allow per-note octave wrapping in this slice. Every accepted arranged note must have the same score-wide octave shift value; if no single shift places all sounded pitches inside range, the target request is unarrangeable in this round. [user-confirmed @ interaction `ab9e9fce-464c-4882-891d-bbe18a28dd51`]
- Never accept transposing or written-pitch profile semantics under a range-only non-transposing contract. Those requests must be unsupported instead of silently interpreted as sounding pitch. [user-confirmed @ interaction `ab9e9fce-464c-4882-891d-bbe18a28dd51`]
- Never apply range constraints only in MusicXML. The arranged score is the canonical arranged artifact; MusicXML parse-back proves the adapter mirrors that artifact, not that the arrangement policy is correct. [artifact-verified @ `docs/superpowers/specs/2026-08-20-audio-to-instrument-score-design.md:94`; artifact-verified @ `docs/reviewspec/target-instrument-single-melody-arrangement/explore.md:19`]
- Never collapse source timing/quantization failure, unsupported profile failure, no-global-shift feasibility failure, arranged-score contract failure, MusicXML export failure, and evaluation failure into one opaque target error. The operator actions differ. [artifact-verified @ prior caution `docs/reviewspec/beat-aware-single-melody-score/design-review.md:87-105`; artifact-verified @ `docs/reviewspec/target-instrument-single-melody-arrangement/spec.md:22-32`]
- Never treat range-fit, MusicXML consistency, or self-consistency among generated artifacts as proof of transcription or musical correctness. Evaluation must keep range-fit and rhythm preservation scoped to arrangement quality. [artifact-verified @ `docs/research/midi-ground-truth-benchmarks-2026-08.md:48-50`; artifact-verified @ `docs/reviewspec/target-instrument-single-melody-arrangement/explore.md:24`]
- Never expand this round into expressive idiom, fingering, articulations, rhythm simplification, subjective musicality, PDF/TAB rendering, stem separation, or multi-instrument orchestration. [artifact-verified @ `docs/reviewspec/target-instrument-single-melody-arrangement/spec.md:2`; artifact-verified @ `docs/reviewspec/target-instrument-single-melody-arrangement/explore.md:20-25`]
- Never drop cross-round registry coverage. The prior ten active intents remain binding unless formally amended. [artifact-verified @ `docs/reviewspec/REGISTRY.md:6-21`]

## Failure Map

```
Public CLI / processing entrypoint / evaluation runner
  -> Existing media, decode, scope, transcription, NoteEvents, TimeMap, source ScoreIR
  -> Target request and profile selector
  -> InstrumentProfile registry / contract validator
  -> Source ScoreIR handoff
  -> Arrangement feasibility and global-shift selector
  -> Arranged score writer and validator
  -> MusicXML exporter and parser
  -> Arrangement evaluation scorer
  -> Status publisher and artifact delivery
```

| Component | Depends on / path broken | Block vs report | Rollback need | Half-broken behavior | Surviving repair entry point |
|---|---|---|---|---|---|
| Public entrypoint / evaluation runner | User target request, fixed corpus cases, and prior media pipeline | Block accepted target output if target profile is absent/unsupported or any required arranged artifact gate fails; preserve prior media failure policy | Do not publish accepted result until source and arranged bundles both pass | Result says `ACCEPTED` but lacks target profile or arranged score artifact | Inspect `result.json`, stage list, and artifact manifest without rerunning media intake |
| Existing source score path | Media/decode/scope/transcription/`NoteEvents`/`TimeMap`/source `ScoreIR` | Preserve prior stage REVIEW/FAIL categories; do not relabel source timing or transcription failure as arrangement failure | Keep source artifacts unchanged | Source `ScoreIR` is partially written or replaced by arranged notes | Existing validators and prior registry tests inspect source artifacts |
| Target request and profile selector | CLI/API target profile id, supported profile registry | Unsupported or absent target profile is a profile/request REVIEW/FAIL; do not fall back to generic melody as accepted target score | Do not create arranged score until a supported profile is selected | Generic default part name is accepted despite a target request | Request/profile validator reports requested id and supported ids |
| InstrumentProfile registry / contract validator | Profile id/name, sounded pitch range, voice count, pitch-domain policy, support label | Invalid, transposing, written-pitch, multi-voice, or missing range profile blocks arrangement for this slice | Reject profile before any arranged artifact is written | Range constants exist in tests/exporter but not in the profile artifact | Profile contract validator reads one canonical registry entry |
| Source `ScoreIR` handoff | Source score notes, time signature, tempo, measure/beat/duration fields, source note ids | Missing or invalid source `ScoreIR` is a source score/timing failure, not arrangement | Preserve source `ScoreIR` and timing artifacts | Arranger consumes source notes but loses source artifact version | Handoff validator compares source `ScoreIR` version and note ids |
| Arrangement feasibility / global-shift selector | Source pitches plus profile sounded range and allowed global octave shifts | REVIEW/FAIL if no single score-wide octave shift fits all notes; never per-note wrap | Do not emit accepted arranged score for infeasible targets | Individual notes are shifted differently but all are in range | Feasibility diagnostic lists profile range, candidate shifts, and blocking notes |
| Arranged score writer / validator | Source `ScoreIR`, target profile, chosen shift, transformation trace | Internal FAIL if identity, rhythm sequence, part identity, global-shift uniformity, or range invariant is broken | Do not replace source `ScoreIR`; write arranged artifact only after validation | Arranged score has in-range notes but missing source score-note ids or durations changed | Arranged-score validator reads source and arranged artifacts side by side |
| MusicXML exporter / parser | Arranged score canonical artifact | Export FAIL if parsed MusicXML part name, note count, pitch order, measure positions, durations, or range does not match arranged score | Do not publish target MusicXML until parse-back passes | XML mirrors source `ScoreIR` rather than arranged score | Export diagnostic compares parsed XML to arranged score, not source score |
| Arrangement evaluation scorer | Fixed corpus truth, target profile, source `ScoreIR`, arranged score, MusicXML versions | Block auto-accept/release on missing versions or range/rhythm REVIEW/FAIL; keep arrangement status separate from transcription/timing | Preserve prior report and failed report | Report says PASS but lacks target profile, arranged score version, or range/rhythm metrics | Offline scorer reruns from fixtures and saved artifacts |
| Status publisher / artifact delivery | Stage/category values, result acceptance, artifact bundle | Accepted only after profile, source score, arrangement, export, and evaluation gates pass | Promote accepted bundle atomically | `COMPLETED`/`ACCEPTED` appears after arrangement/profile failure | Status audit checks stages, reason category, and required artifacts |

## Tabletop Scenarios

| Scenario | System observes | System returns / does | Operator next step | Working prior state preserved? |
|---|---|---|---|---|
| A user requests a transposing or written-pitch profile | Target profile exists or is requested, but its pitch-domain policy is outside `non_transposing_sounding_range_only` | REVIEW/FAIL with instrument-profile/request category; no arranged score or accepted MusicXML is published | Choose a supported non-transposing sounded-range profile or defer to a later transposition slice | Yes; source media pipeline is not rerun or relabeled as bad |
| Source melody could fit only by shifting some notes up and others down | Profile range and source pitches show no single score-wide octave shift fits all notes, even though per-note wrapping could make every note in range | REVIEW/FAIL with arrangement feasibility/range reason and candidate-shift diagnostics; no accepted target score | Inspect blocking note ids and profile range; choose another profile or wait for future richer arrangement policy | Yes; source `ScoreIR`, target profile, and failed feasibility report remain inspectable |
| Arranger accidentally applies per-note octave wrapping | Arranged notes are in range and MusicXML could be valid, but pitch transformations are not one uniform global shift | Arranged-score contract FAIL before export acceptance | Fix arrangement policy; do not loosen the design to accept contour-changing per-note repair | Yes; source `ScoreIR` and rejected arranged draft remain diagnostics |
| Arranged artifact loses source identity or rhythm while fitting range | In-range pitches exist, but source score-note ids, measure/beat sequence, or notated durations differ from source `ScoreIR` | Arranged-score contract FAIL; MusicXML is not accepted as target output | Inspect source-vs-arranged comparison by note id and rhythm fields | Yes; source `ScoreIR` is canonical and remains unchanged |
| MusicXML is parseable but mirrors the wrong artifact | XML is one part and valid, but part name, pitch order, measure positions, durations, or range match source/generic score instead of arranged score | MusicXML export FAIL with adapter mismatch; do not relabel as profile or arrangement feasibility failure | Fix exporter source selection and parse-back comparison | Yes; arranged score remains the diagnostic source |

## Failure-Policy Families

| Family | Operations | Failure policy |
|---|---|---|
| Prior source pipeline failures | Media, decode, scope, transcription, note events, time map, source `ScoreIR`, source MusicXML for prior rounds | Preserve existing REVIEW/FAIL semantics and prior registry behavior; do not call these target arrangement failures |
| Target profile request failures | Missing target request, unknown profile id, unsupported profile, transposing/written-pitch profile, invalid profile schema | REVIEW/FAIL with instrument-profile/request category; do not fall back to accepted generic melody |
| Arrangement feasibility failures | No single global octave shift can fit all source notes in the sounded range | REVIEW/FAIL with arrangement/range reason and diagnostics; preserve source score and profile |
| Arranged score contract failures | Missing source score-note id, changed rhythm sequence, multiple shifts, out-of-range note, invalid part/profile metadata | Internal FAIL before export acceptance; keep arranged artifact distinct from source `ScoreIR` |
| Export consistency failures | MusicXML parse failure or mismatch against arranged score part name, note count, pitch order, positions, durations, or range | Export FAIL; do not blame source timing/profile unless evidence points there |
| Arrangement evaluation failures | Missing target/source/arranged/MusicXML versions, range-fit REVIEW/FAIL, rhythm-preservation REVIEW/FAIL | Evaluation REVIEW/FAIL blocks auto-accept/release; preserve per-case attribution |
| Delivery/status failures | Missing artifacts, inconsistent stages, accepted state after any target arrangement gate failed | Delivery/status FAIL; accepted result is promoted only after required bundle passes |

Merge reductio:
- If profile validation and arrangement feasibility share one error, an unsupported transposing profile can be "fixed" by widening octave-shift search, or an infeasible non-transposing melody can be misreported as unsupported profile data.
- If source `ScoreIR` and arranged score are merged, the system can pass target tests by mutating the source score and silently break prior beat-aware registry contracts.
- If range checking and MusicXML export share one path, a MusicXML-only patch can hide that the canonical arranged artifact is out of range or missing source traceability.
- If per-note wrapping and global shifting share one transformation label, a fake-green implementation can keep every note in range while violating the board-approved contour-preserving policy.
- If arrangement evaluation and source transcription/timing evaluation share one PASS/REVIEW/FAIL bucket without stage/category data, operators cannot tell whether to re-record, fix timing, choose another profile, or fix the arranger/exporter.

## Fitness Tests

These are architecture-shape tests for the build. They prevent regression to already-identified bad shapes; they do not prove the architecture catches novel mis-framings.

1. **Profile contract single source:** the supported target profile is represented in one canonical registry/contract with id, display/part name, sounded MIDI range, non-transposing pitch-domain flag, `voice_count: 1`, support/difficulty metadata, schema/generator version, and no duplicated authoritative range constants in the exporter or tests.
2. **Unsupported pitch-domain sentinel:** a transposing or written-pitch profile request must return REVIEW/FAIL with an instrument-profile/request reason and `NOT_ACCEPTED`; it must not be interpreted as sounded pitch.
3. **Source score preservation:** source `score_ir` remains present and unchanged; `arranged_score` is a separate artifact that cites source job, source media, source `ScoreIR` version, `TimeMap` version, target profile version, and every source score-note id.
4. **Rename-only trap:** include a fixture where the accepted target arrangement must visibly differ from the generic source score by the chosen global octave shift; part renaming alone must fail INT-1/INT-3 coverage.
5. **Global-shift invariant:** every accepted arranged note carries the same `global_octave_shift` or equivalent pitch transformation value, and every pitch equals source pitch plus that shift in semitones.
6. **No per-note wrapping sentinel:** a fixture that can fit by per-note octave wrapping but not by one global shift must return REVIEW/FAIL with an arrangement/range reason and `NOT_ACCEPTED`.
7. **Range contract:** corrupt one arranged pitch outside profile range after arrangement; arranged-score validation or export/evaluation must fail before accepted delivery.
8. **Rhythm and identity preservation:** corrupt a source score-note id, measure, beat, or notated duration in the arranged artifact; the arranged-score contract must fail before MusicXML can be accepted.
9. **MusicXML mirrors arranged score:** mutate XML part name, pitch, measure, or duration while leaving source and arranged score valid; parse-back must fail against arranged score, not source `ScoreIR`.
10. **Status orthogonality:** source media/decode/scope/transcription/timing, target profile, arrangement feasibility, arranged-score contract, MusicXML export, evaluation, and delivery failures each produce distinct machine-readable stage/category values and never enter the accepted passing state.
11. **Arrangement evaluation citations:** arrangement corpus reports cannot PASS unless every case cites target profile, source `ScoreIR`, arranged score, MusicXML versions, range-fit result, rhythm-preservation result, and arrangement PASS/REVIEW/FAIL.
12. **Cross-round registry guard:** all ten active prior registry intents continue to have passing guarding tests in addition to the new target-arrangement tests.

## Independent Review

An independent read-only subagent reviewed framing and converged on the narrow scope: this is a single-melody, profile-constrained octave arrangement, not general musical arranging. It also converged on the insertion point after valid source `ScoreIR` and before target MusicXML/status, and on the prior warning that self-consistent artifacts are not correctness proof.

The independent pass diverged usefully by sharpening three risks. First, the board-resolved rules are not present in the repo spec text; the spec phrase "exposes any pitch transformation applied to each note" could otherwise permit per-note octave repair. Second, INT-4's prose fuses unsupported profile, invalid profile, no global shift, arranged contract failure, and export mismatch under one broad reason. Third, the target profile and evaluation contracts can drift if profile semantics or arrangement metrics are duplicated across registry, arranger, exporter, tests, and reports.

No new blocker remains after incorporating those divergences. They are adopted as hard design constraints and fitness tests above: non-transposing sounded-pitch range-only support, single global octave shift only, profile/arrangement/export/evaluation stage separation, one canonical profile source, arranged score as the canonical target artifact, and evaluation metrics in the existing report contract.

## Code Plan

For the build agent, in order:

1. Preserve the current clean monophonic media-to-source-`ScoreIR` path and accumulated registry tests. Extend the pipeline only after valid source `ScoreIR` and `TimeMap` exist.
2. Add a target request surface to the public entrypoint/CLI and evaluation cases. Unsupported or absent target profile requests for this slice must produce profile/request REVIEW or FAIL rather than generic accepted sheet music.
3. Define the smallest repository-native `InstrumentProfile` contract/registry for one real non-transposing sounded-pitch range-only profile: id, display/part name, sounded MIDI range, `voice_count: 1`, pitch-domain/transposition policy, support/difficulty metadata, schema/generator version.
4. Add profile validation before arrangement. Reject invalid, unknown, transposing, written-pitch, or multi-voice profiles with a profile category distinct from media, transcription, timing, arrangement, export, and evaluation.
5. Add a distinct arranged score artifact after source `ScoreIR` and before target MusicXML export. It must cite source job/media, source `ScoreIR` version, `TimeMap` version, target profile version, and every source score-note id.
6. Implement arrangement feasibility using only a single score-wide octave shift for sounded MIDI pitches. Shift `0` is allowed; if no single shift fits the entire melody range, return REVIEW/FAIL with arrangement/range diagnostics and do not emit accepted target output.
7. Validate arranged score contract separately: one part, target profile metadata, source note identity, same note count/order, same measure/beat/notated-duration sequence, uniform global shift trace, and all sounded pitches within range.
8. Export MusicXML from arranged score as canonical target output. Parse it back and compare part name, note count, pitch order, measure positions, durations, and sounded range against arranged score.
9. Extend the existing `EvaluationReport` path with arrangement metrics and citations: target profile, source `ScoreIR`, arranged score, MusicXML versions, range-fit, rhythm-preservation, and arrangement PASS/REVIEW/FAIL.
10. Keep status publication stage-specific. A passing arrangement is accepted only when source, profile, arrangement, export, and applicable evaluation gates pass; every failure path must preserve diagnostics and `NOT_ACCEPTED`.
11. Add tests derived from the reviewspec risk rule: INT-1, INT-3, and INT-4 are Critical because they are user-visible core promises; INT-2 and INT-5 are Core because breakage hurts the feature even though the supporting artifacts/reports are not directly user-visible. Add the fitness tests above and run the accumulated registry suite.

## Facts Relied On

- The board-approved plan revision under review is `27b34ff1-30ab-4cfd-b63b-c0a7b8a47d49`. [artifact-verified @ Paperclip [AIM-10](/AIM/issues/AIM-10#document-plan) document fetched 2026-08-21]
- The approved planning commit and reviewed repository `HEAD` are `4596f80183d01ea5be2bb53f859d662f7de72c4e`. [artifact-verified @ Paperclip [AIM-10](/AIM/issues/AIM-10#document-plan); artifact-verified @ `git rev-parse HEAD`, 2026-08-21 UTC]
- The target spec passed the Reviewspec validator and matches the reviewed commit. [artifact-verified @ `python .../validate_spec.py docs/reviewspec/target-instrument-single-melody-arrangement/spec.md`; artifact-verified @ `git diff --exit-code 4596f80183d01ea5be2bb53f859d662f7de72c4e -- docs/reviewspec/target-instrument-single-melody-arrangement/spec.md`, 2026-08-21 UTC]
- The board answered that the MVP uses one real non-transposing sounded-pitch range-only profile, one score-wide octave shift, REVIEW/FAIL when no single shift fits, and defers transposing/written-pitch semantics and per-note octave wrapping. [user-confirmed @ Paperclip interaction `ab9e9fce-464c-4882-891d-bbe18a28dd51` result summary, resolved 2026-08-21]
- No `docs/decisions/` directory exists, so design memory is README, detailed design, research notes, registry, and prior review artifacts. [artifact-verified @ `find docs -maxdepth 2 -type d -print`, 2026-08-21 UTC; artifact-verified @ `docs/reviewspec/target-instrument-single-melody-arrangement/explore.md:7`]
- The current implementation has source `ScoreIR`, `TimeMap`, MusicXML export, evaluation, and stage/status contracts but no target profile or arrangement artifact. [artifact-verified @ `ai_music_to_sheet/pipeline.py:144-160`; artifact-verified @ `ai_music_to_sheet/contracts.py:19-43`; artifact-verified @ `rg -n "arrang|instrument|profile|target" ai_music_to_sheet`, 2026-08-21 UTC]
- The current CLI accepts only media path and output directory. [artifact-verified @ `ai_music_to_sheet/__main__.py:10-18`]
- The first-slice and beat-aware code reviews passed at commits `4d5c05263c0c4f4eb819e0a2900e9cd7bac4b4e0` and `f2c089748d4ffac83edae4902901b6b65d20ac0d`; the registry now lists ten active prior intents. [artifact-verified @ `docs/reviewspec/first-verified-monophonic-score/review.md:1-18`; artifact-verified @ `docs/reviewspec/beat-aware-single-melody-score/review.md:1-20`; artifact-verified @ `docs/reviewspec/REGISTRY.md:6-21`]
- The broader project architecture requires staged, replayable artifacts with provenance/version/confidence and treats MusicXML/MIDI as adapters, not the core model. [artifact-verified @ `README.md:17-24`; artifact-verified @ `docs/superpowers/specs/2026-08-20-audio-to-instrument-score-design.md:7-17`; artifact-verified @ `docs/superpowers/specs/2026-08-20-audio-to-instrument-score-design.md:94`]
- Accuracy claims require ground truth; comparing generated predictions or internally consistent artifacts measures agreement, not correctness. [artifact-verified @ `docs/research/midi-ground-truth-benchmarks-2026-08.md:48-50`; artifact-verified @ `docs/reviewspec/beat-aware-single-melody-score/design-review.md:21`]

## Links

- README: `README.md`
- Detailed design: `docs/superpowers/specs/2026-08-20-audio-to-instrument-score-design.md`
- Explore: `docs/reviewspec/target-instrument-single-melody-arrangement/explore.md`
- Spec: `docs/reviewspec/target-instrument-single-melody-arrangement/spec.md`
- Prior registry: `docs/reviewspec/REGISTRY.md`
- Prior design review: `docs/reviewspec/beat-aware-single-melody-score/design-review.md`
- Prior code review: `docs/reviewspec/beat-aware-single-melody-score/review.md`
- Ground-truth research: `docs/research/midi-ground-truth-benchmarks-2026-08.md`
- Stem-separation research: `docs/research/audio-stem-separation-options-2026-08.md`, `docs/research/mature-stem-separation-products-2026-08.md`
- Board interaction: `ab9e9fce-464c-4882-891d-bbe18a28dd51` on [AIM-11](/AIM/issues/AIM-11)

## Open Questions

No blocking user-owned questions remain for this design gate. The following are intentionally build-owned within the approved scope and must be made explicit in build artifacts/tests:

- Exact first supported profile id, instrument name, and sounded MIDI range, as long as it is one real non-transposing range-only profile with one voice.
- Exact module/file layout for the profile registry, arranged score schema, and status category names.
- Exact numeric candidate shifts and tie-breaking order for selecting the single global octave shift.
- Exact REVIEW vs FAIL split for unsupported profile, invalid profile, no-global-shift feasibility, arranged contract failure, export mismatch, and evaluation failure.
- Exact range-fit/rhythm-preservation thresholds and fixture count for the arrangement evaluation corpus.
