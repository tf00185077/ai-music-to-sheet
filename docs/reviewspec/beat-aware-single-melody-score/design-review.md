# Design record: beat-aware-single-melody-score

_Last review: 2026-08-21 - reviewed commit `1e6f256a8c3b31cab8a5ec629437ec733ac26319` - approved plan revision `2a8c726d-ffe8-4842-bd26-096e2b80dd70`_

Verdict: **cleared for build with required design constraints**. No production code is written by this review. The approved spec is narrow enough to build, but the build must keep musical timing, quantization, export consistency, timing evaluation, and user-visible acceptance as separate contracts. A self-consistent `TimeMap` + `ScoreIR` + MusicXML bundle is not proof that the selected beat grid is musically correct.

## Decision log (append-only - newest first)

### 2026-08-21 - round 1 - first review
- **Changed:** First design gate record for `beat-aware-single-melody-score`; the build is cleared only if it introduces explicit `TimeMap` and `ScoreIR` artifacts and keeps timing/quantization failure separate from transcription, export, and delivery failure.
- **Supersedes:** N/A - first review for this build.
- **Carried over:** The certified first slice remains active: clean monophonic MP3/MP4 intake, ordered `NoteEvents`, parseable single-part MusicXML, ground-truth evaluation, and non-acceptance for unsupported or low-confidence results. Mixed recordings, stem separation, arrangement, PDF/TAB export, manual correction, YouTube ingestion, arbitrary beat tracking, and vendor/model choices remain outside this round.
- **Driver provenance:** artifact-verified @ Paperclip AIM-7 heartbeat context fetched 2026-08-21; artifact-verified @ repository commit `1e6f256a8c3b31cab8a5ec629437ec733ac26319`.

## Design Review

**Triage:** structural. This slice crosses artifact contracts, timing analysis, quantization policy, notation export, status/acceptance policy, and offline evaluation.

**Elicit:** prior record loaded: no `docs/decisions/` directory exists, and no prior `design-review.md` exists for this build. The current memory is README, detailed design, research notes, `docs/reviewspec/REGISTRY.md`, and the certified `first-verified-monophonic-score` artifacts. Intent, boundary, and invariant gaps were walked. No `ask_user_questions` interaction was posted because no unresolved load-bearing user-owned product decision is needed to clear this gate: exact fixture count, schema field names beyond approved observables, quantization tolerance constants, duration vocabulary, and whether the first `TimeMap` is fixture-backed or deterministically derived are build-owned as long as the approved observables and this review's constraints are met.

**Reframe:** the system is protecting user trust in rhythm-aware sheet music, not merely converting second durations into MusicXML ticks. The mis-framing risk is treating an internally consistent beat grid as musical truth. A user learns timing failure through `REVIEW`/`FAIL` with a timing or quantization reason; maintainers learn corpus failures through timing metrics in `EvaluationReport`. Green tests could still miss a false promise where every artifact agrees on the wrong tempo, beat offset, or measure boundary and the output is accepted as sheet music.

## Purpose

Turn the first certified clean monophonic media-to-note loop into a measure-aware notation loop for simple metered melodies, while preserving stage diagnostics and avoiding any claim of arbitrary beat tracking or mixed-audio transcription.

## Boundary Conditions

- The approved build is `beat-aware-single-melody-score`, plan revision `2a8c726d-ffe8-4842-bd26-096e2b80dd70`, and approved planning commit `1e6f256a8c3b31cab8a5ec629437ec733ac26319`. [artifact-verified @ Paperclip AIM-7 heartbeat context fetched 2026-08-21; artifact-verified @ `git rev-parse HEAD`, 2026-08-21]
- The repository `HEAD` is exactly the approved planning commit, and `docs/reviewspec/beat-aware-single-melody-score/spec.md` has no diff from that commit. [artifact-verified @ `git rev-parse HEAD`; artifact-verified @ `git diff --exit-code 1e6f256a8c3b31cab8a5ec629437ec733ac26319 -- docs/reviewspec/beat-aware-single-melody-score/spec.md`, 2026-08-21]
- The approved spec adds beat, measure, and quantized score structure for simple metered melodies and excludes mixed recordings, stem separation, arrangement, PDF/TAB export, manual correction, YouTube ingestion, and arbitrary beat tracking. [artifact-verified @ `docs/reviewspec/beat-aware-single-melody-score/spec.md:2`]
- `TimeMap` must connect source seconds to beat and measure positions and must carry source/job identity, tempo, time signature, anchors, and reversible mapping for the supported fixture. [artifact-verified @ `docs/reviewspec/beat-aware-single-melody-score/spec.md:4-8`]
- `ScoreIR` must preserve `NoteEvents` pitch order, cite source note-event identity, and express measure, beat position, and notated duration without overlaps in the supported single voice. [artifact-verified @ `docs/reviewspec/beat-aware-single-melody-score/spec.md:10-14`]
- MusicXML must be parseable as one part with expected time signature, measure boundaries, note count, pitch order, and note durations matching `ScoreIR`. [artifact-verified @ `docs/reviewspec/beat-aware-single-melody-score/spec.md:16-20`]
- Timing evaluation must name cases, cite `TimeMap` and `ScoreIR` artifact versions, score beat position and notated duration, and return PASS, REVIEW, or FAIL. [artifact-verified @ `docs/reviewspec/beat-aware-single-melody-score/spec.md:22-26`]
- Unquantizable timing must expose REVIEW or FAIL with a timing/quantization reason and must not share the completed/accepted state used by passing beat-aware fixtures. [artifact-verified @ `docs/reviewspec/beat-aware-single-melody-score/spec.md:28-32`]
- The current code has source, canonical audio, `NoteEvents`, MusicXML, result, and evaluation artifacts, but no `TimeMap` or `ScoreIR`; MusicXML currently emits one 4/4 measure, turns seconds into durations, and labels every note as quarter. [artifact-verified @ `docs/reviewspec/beat-aware-single-melody-score/explore.md:18-19`; artifact-verified @ `ai_music_to_sheet/musicxml.py:45-80`]
- The broader project design requires stage artifacts with source, version, confidence/uncertainty, and machine-readable validation rather than an opaque audio-to-score black box. [artifact-verified @ `README.md:17-24`; artifact-verified @ `docs/superpowers/specs/2026-08-20-audio-to-instrument-score-design.md:7-17`]
- MusicXML and MIDI are adapters, not core models; the core model for this slice is `ScoreIR` backed by `TimeMap` and `NoteEvents`. [artifact-verified @ `docs/superpowers/specs/2026-08-20-audio-to-instrument-score-design.md:80-94`]
- Accuracy claims require ground truth; comparing internally generated predictions measures agreement, not correctness. [artifact-verified @ `README.md:89-113`; artifact-verified @ `docs/superpowers/specs/2026-08-20-audio-to-instrument-score-design.md:120-129`; artifact-verified @ `docs/research/midi-ground-truth-benchmarks-2026-08.md:48-50`]

## Invariants / Cautions

- Never promote a beat-aware score to accepted sheet music solely because `TimeMap`, `ScoreIR`, and MusicXML agree with each other; timing acceptance requires the relevant timing/quantization quality gate. [artifact-verified @ `docs/reviewspec/beat-aware-single-melody-score/spec.md:22-32`]
- Never let arbitrary beat tracking enter the required path for this slice. A fixture-backed or deterministic simple-meter `TimeMap` is acceptable; the artifact must disclose its source/provenance so later arbitrary tracking can be added without masquerading as already solved. [artifact-verified @ `docs/reviewspec/beat-aware-single-melody-score/spec.md:2`; artifact-verified @ `docs/reviewspec/beat-aware-single-melody-score/explore.md:20-21`]
- Never collapse note-event seconds, beat positions, quantized durations, and exported MusicXML divisions into one unversioned representation. They fail for different reasons and must be diagnosable independently. [artifact-verified @ `README.md:19-24`; artifact-verified @ `docs/superpowers/specs/2026-08-20-audio-to-instrument-score-design.md:9-15`]
- Never allow a quantizer to silently repair drift by changing pitch order, source note identity, or overlap policy; `ScoreIR` must remain traceable to `NoteEvents`. [artifact-verified @ `docs/reviewspec/beat-aware-single-melody-score/spec.md:10-14`]
- Never treat MusicXML parseability or measure count as proof of rhythmic accuracy; exporter consistency and ground-truth timing scoring are separate gates. [artifact-verified @ `docs/reviewspec/beat-aware-single-melody-score/spec.md:16-26`; artifact-verified @ `docs/research/midi-ground-truth-benchmarks-2026-08.md:48-50`]
- Never drop first-slice regression coverage. The registry lists five active prior intents that must retain passing guarding tests unless formally superseded. [artifact-verified @ `docs/reviewspec/REGISTRY.md:6-16`]

## Failure Map

```
Public entrypoint / evaluation runner
  -> Media intake, decode, scope gate, transcription, NoteEvents
  -> TimeMap producer / loader
  -> Time-to-score mapper
  -> Quantization and measure validator
  -> ScoreIR contract writer
  -> MusicXML exporter and parser
  -> Timing evaluation scorer
  -> Status publisher and artifact delivery
```

| Component | Depends on / path broken | Block vs report | Rollback need | Half-broken behavior | Surviving repair entry point |
|---|---|---|---|---|---|
| Public entrypoint / evaluation runner | User jobs and fixed corpus runs | Report stage status; block accepted state if any required timing gate fails | Do not promote accepted result before all required artifacts exist | Result says complete but lacks timing artifact | Inspect result manifest and persisted artifacts directly |
| Existing media/decode/scope/transcription path | Certified clean monophonic MP3/MP4 to `NoteEvents` | Preserve first-slice failure policy; do not blame timing for media/transcription failures | Keep previous stage artifacts | `NoteEvents` missing after timing stage starts | Re-run first-slice validators and tests without TimeMap |
| TimeMap producer / loader | Tempo, time signature, beat or measure anchors, source/job identity | REVIEW/FAIL if absent, inconsistent, unsupported, or outside simple-meter support | Do not write final TimeMap until anchor/schema checks pass | Tempo exists but anchors or provenance missing | TimeMap validator reads source metadata and anchor list |
| Time-to-score mapper | Reversible mapping from note-event seconds to beat/measure positions | Block/REVIEW if seconds cannot map monotonically or reversibly within tolerance | Preserve original `NoteEvents`; do not overwrite note seconds | Some notes mapped, others orphaned or duplicated | Mapper diagnostic names note ids, seconds, expected beat range |
| Quantization and measure validator | Beat positions to notated durations and measure totals | REVIEW for near-boundary ambiguity; FAIL for impossible measure structure | Do not write accepted `ScoreIR` until no overlaps and measure totals validate | Measures exist but totals do not sum, rests are implicit, or overlaps appear | Contract validator reads `TimeMap` + draft `ScoreIR` |
| ScoreIR contract writer | Traceable quantized notes, source note ids, measure/beat/duration | Internal FAIL on missing traceability or invalid schema; block export | Do not let partial `ScoreIR` replace prior artifacts | Score notes have durations but no source event identity | ScoreIR validator reports note index and source id failures |
| MusicXML exporter and parser | `ScoreIR` to one-part measured MusicXML | Export FAIL for parse or mismatch; do not relabel as timing failure unless evidence points there | Do not publish accepted download until parsed XML matches `ScoreIR` | XML has correct pitches but wrong measure divisions/types | Export diagnostic compares parsed XML with `ScoreIR` |
| Timing evaluation scorer | Fixed corpus truth, TimeMap/ScoreIR versions, beat-position and duration metrics | Block auto-accept/release on REVIEW/FAIL; preserve per-case attribution | Preserve prior corpus report and failed report | Report lacks artifact versions or only scores seconds | Offline scorer reruns from fixtures and saved artifacts |
| Status publisher / artifact delivery | Machine-readable stage reasons and artifact bundle | User-visible REVIEW/FAIL for timing/quantization; accepted only for passing fixtures | Promote accepted result atomically after all required artifacts pass | Status says accepted while TimeMap/ScoreIR missing or failed | Artifact manifest/status audit identifies missing gate |

## Tabletop Scenarios

| Scenario | System observes | System returns / does | Operator next step | Working prior state preserved? |
|---|---|---|---|---|
| Supported fixture has a 120 BPM 4/4 TimeMap, but first beat anchor is shifted by half a beat | `NoteEvents` map cleanly to a grid, MusicXML can be measured, but beat-position metrics miss the reference | `EvaluationReport` marks REVIEW or FAIL with timing metric reason; no accepted score | Inspect TimeMap anchor provenance and beat-position deltas; fix TimeMap generation/fixture metadata | Yes; source, NoteEvents, bad TimeMap, ScoreIR draft, and report remain inspectable |
| Note durations produce a measure total of 3.875 beats in a declared 4/4 measure | Quantizer can round locally but measure invariant fails | REVIEW if within explicit tolerance and diagnosable, otherwise FAIL; no accepted MusicXML | Inspect note ids around the deficit and quantizer diagnostics; adjust tolerance or fixture data only with evidence | Yes; original NoteEvents and failed quantization report remain |
| Tempo/time signature is missing or unsupported for an otherwise valid monophonic run | Media and NoteEvents pass, but no valid TimeMap can be produced in the supported simple-meter envelope | REVIEW/FAIL with `timing` or `timemap` reason; do not fall back to the old one-measure note list as accepted sheet music | Add fixture-backed TimeMap or route to future arbitrary beat tracking; do not change transcription | Yes; first-slice artifacts stay usable as diagnostics but are not accepted as beat-aware output |
| ScoreIR notes preserve pitch order but lose source note ids during quantization | Quantized measures appear valid, exporter can create MusicXML, but traceability is broken | Internal FAIL at ScoreIR contract stage; block export acceptance | Inspect ScoreIR contract errors and mapper note-id join | Yes; NoteEvents and TimeMap survive, no accepted ScoreIR is promoted |
| MusicXML has correct pitches and measures, but note types/durations differ from ScoreIR after export | Parser can read one part and pitch order, but duration/type comparison fails | Export FAIL with MusicXML/ScoreIR mismatch, not timing FAIL | Fix exporter duration/division mapping; timing artifacts are not blamed | Yes; ScoreIR remains canonical diagnostic source |

## Failure-Policy Families

| Family | Operations | Failure policy |
|---|---|---|
| Prior media/transcription failures | Unsupported format, decode/audio-quality, unsupported scope, low-confidence or invalid `NoteEvents` | Preserve first-slice REVIEW/FAIL semantics; do not enter timing/export acceptance |
| TimeMap availability and support | Missing tempo/time signature, unsupported meter, absent anchors, non-monotonic anchors | REVIEW/FAIL with timing/timemap reason; do not infer arbitrary beat tracking silently |
| Mapping failures | Note seconds cannot map reversibly or monotonically to beat/measure positions | REVIEW/FAIL with note ids and deltas; preserve `NoteEvents` |
| Quantization failures | Ambiguous boundary, unsupported note value, measure total mismatch, overlap after rounding | REVIEW for explicit near-tolerance ambiguity; FAIL for incoherent score; no accepted ScoreIR |
| ScoreIR contract failures | Missing source-note identity, missing measure/beat/duration, invalid schema | Internal FAIL; block export and accepted result |
| Export consistency failures | MusicXML parse, measure, time-signature, note count, pitch order, or duration mismatch | Export FAIL; do not relabel as timing quality failure |
| Timing evaluation failures | Corpus timing metrics below threshold or missing TimeMap/ScoreIR versions | Block auto-accept/release; keep per-case attribution |
| Delivery/status failures | Missing artifacts, inconsistent state, accepted state after a timing gate failed | Delivery/status FAIL; preserve artifact bundle for diagnosis |

Merge reductio:
- If TimeMap production and quantization share one error, a missing tempo can be "fixed" by changing duration tolerance, or a quantizer bug can be misreported as an unsupported meter.
- If quantization and export share one path, a wrong MusicXML duration can cause the builder to change ScoreIR instead of fixing the exporter.
- If exporter consistency and timing evaluation merge, an internally consistent but beat-shifted score can pass because MusicXML faithfully reproduces the wrong grid.
- If timing REVIEW and transcription REVIEW share one category, users and operators cannot tell whether to re-record, fix note detection, provide a TimeMap, or tune quantization.
- If fixture-backed TimeMap and arbitrary beat tracking share one capability flag, this slice can accidentally promise beat tracking for real recordings that the spec explicitly excludes.

## Fitness Tests

These are architecture-shape tests for the build. They prevent regression to already-identified bad shapes; they do not prove the architecture catches novel mis-framings.

1. **TimeMap provenance and support boundary:** every passing beat-aware result has a persisted TimeMap with source/job identity, generator/version, tempo, time signature, anchor source/provenance, and an explicit support mode such as fixture-backed or deterministic-simple-meter; no required path imports stem separation, vendor APIs, arrangement, PDF/TAB, manual correction, YouTube, or arbitrary beat tracking.
2. **Seconds-to-music reversibility:** for each accepted fixture note, mapping NoteEvents seconds to measure/beat and back stays within the declared tolerance and preserves note identity.
3. **Quantization self-consistency trap:** create a TimeMap with a half-beat shifted anchor and generate matching ScoreIR/MusicXML; export consistency may pass, but beat-position scoring must REVIEW/FAIL.
4. **Measure-total invariant:** a fixture whose quantized durations do not fill declared measures must not be auto-accepted; the result names quantization/measure-total reason and keeps prior artifacts.
5. **ScoreIR traceability:** deleting or corrupting a source note-event id in ScoreIR must fail before MusicXML export can be accepted.
6. **MusicXML mirrors ScoreIR, not NoteEvents seconds:** mutate MusicXML note duration or measure assignment while keeping pitch order/count; parser/export check must fail against ScoreIR.
7. **Status orthogonality:** media/decode, scope/transcription, TimeMap, mapping, quantization, ScoreIR contract, MusicXML export, evaluation, and delivery failures each produce distinct machine-readable stage/category values and never enter the accepted passing state.
8. **Cross-round registry guard:** all five `first-verified-monophonic-score` registry intents continue to have passing guarding tests in addition to the new beat-aware tests.
9. **Artifact version citations:** timing evaluation reports cannot pass unless they cite TimeMap and ScoreIR artifact versions for every case and include beat-position plus notated-duration metrics.
10. **Diagnostic survivability:** TimeMap, ScoreIR, MusicXML, and EvaluationReport validators can inspect saved artifacts without the public upload path being healthy.

## Independent Review

An independent read-only subagent reviewed framing and converged on the scope boundary, the need for `TimeMap` and `ScoreIR`, and the prior warning that self-consistent artifacts are not correctness proof. It diverged by sharpening the circular-evidence risk: if TimeMap is inferred from NoteEvents and then used as the evidence that those same NoteEvents are rhythmically correct, the validator only proves internal agreement. It also highlighted drift risk around PASS/REVIEW/FAIL semantics, timing tolerances, "simple metered" support boundaries, TimeMap mapping math, ScoreIR duration vocabulary, MusicXML divisions, and artifact provenance.

No divergence requires changing the approved spec before code. The divergences are adopted as constraints and fitness tests above: independent timing references for evaluation, TimeMap anchor-shift break-testing, off-grid/rubato REVIEW or FAIL behavior, distinct machine-readable categories, and atomic accepted bundles.

## Code Plan

For the build agent, in order:

1. Keep the first-slice media/decode/scope/transcription and `NoteEvents` contracts intact; extend the pipeline only after valid `NoteEvents` exist.
2. Define the smallest repository-native `TimeMap` contract: schema/version, source/job identity, input/source link, tempo, time signature, beat or measure anchors, anchor/provenance mode, tolerance metadata, and second-to-position/position-to-second mapping behavior for note-event times.
3. Add a TimeMap producer/loader for supported simple-meter fixtures. The approved spec does not require arbitrary beat tracking; if derivation is implemented, keep it behind the same explicit support/provenance contract.
4. Define a minimal `ScoreIR` contract for one monophonic part: source/job identity, generator/version, source note-event id per note, pitch, measure number, beat position, quantized notated duration, optional rests if needed to satisfy measure totals, and no overlaps.
5. Implement mapping and quantization as separate stages with validators. Mapping errors should name note ids and second/beat deltas; quantization errors should name measure totals, unsupported values, or overlap causes.
6. Replace the old one-measure MusicXML export path for beat-aware results with an exporter that reads ScoreIR as canonical, emits the expected time signature and measure boundaries, parses back, and checks note count, pitch order, measure assignment, and durations against ScoreIR.
7. Extend the fixed evaluation corpus with simple-meter ground truth that includes note seconds, expected beat positions, expected notated durations, time signature, and TimeMap/ScoreIR version citations. Keep exact fixture count and tolerance constants build-owned but visible in the report.
8. Wire status publication so timing/TimeMap, mapping, quantization, ScoreIR, export, and evaluation failures remain distinct from first-slice transcription failures and all block accepted sheet-music state.
9. Add behavior tests derived from the reviewspec tier rule: INT-3 and INT-5 are Critical because they are user-visible core promises; INT-1, INT-2, and INT-4 are Core because they are not directly user-visible but are core to the feature. Add the fitness tests above, then run the accumulated first-slice registry tests.

## Facts Relied On

- The board-approved plan revision under review is `2a8c726d-ffe8-4842-bd26-096e2b80dd70`. [artifact-verified @ Paperclip AIM-7 heartbeat context fetched 2026-08-21]
- The approved planning commit under review is `1e6f256a8c3b31cab8a5ec629437ec733ac26319`, and repository `HEAD` matches it. [artifact-verified @ Paperclip AIM-7 heartbeat context fetched 2026-08-21; artifact-verified @ `git rev-parse HEAD`, 2026-08-21]
- The spec validator passed for `docs/reviewspec/beat-aware-single-melody-score/spec.md`. [artifact-verified @ `python3 .../reviewspec-core--fca75830e7/scripts/validate_spec.py docs/reviewspec/beat-aware-single-melody-score/spec.md`, 2026-08-21]
- The spec at `docs/reviewspec/beat-aware-single-melody-score/spec.md` matches the reviewed commit. [artifact-verified @ `git diff --exit-code 1e6f256a8c3b31cab8a5ec629437ec733ac26319 -- docs/reviewspec/beat-aware-single-melody-score/spec.md`, 2026-08-21]
- There is no `docs/decisions/` directory in the repository, so design memory comes from README, the detailed design document, research notes, registry, and prior reviews. [artifact-verified @ `find docs -maxdepth 2 -type d -print`, 2026-08-21; artifact-verified @ `docs/reviewspec/beat-aware-single-melody-score/explore.md:7`]
- The current implementation is the first verified slice and does not yet contain TimeMap or ScoreIR contracts. [artifact-verified @ `docs/reviewspec/beat-aware-single-melody-score/explore.md:18`; artifact-verified @ `git ls-tree -r --name-only HEAD`, 2026-08-21]
- The first-slice pipeline currently publishes source, canonical audio, note events, MusicXML, result, evaluation report, stage status, quality status, and acceptance state. [artifact-verified @ `ai_music_to_sheet/pipeline.py:61-83`; artifact-verified @ `ai_music_to_sheet/pipeline.py:113-183`]
- The first-slice MusicXML exporter currently emits a single measure with hard-coded 4/4 and quarter note types while durations are derived from seconds. [artifact-verified @ `ai_music_to_sheet/musicxml.py:45-80`]
- The first-slice active registry has five intents that must continue to pass unless formally superseded. [artifact-verified @ `docs/reviewspec/REGISTRY.md:6-16`]
- Broader stem-separation/vendor/API research is relevant only as an exclusion boundary for this slice, not as a dependency. [artifact-verified @ `docs/research/audio-stem-separation-options-2026-08.md:1-3`; artifact-verified @ `docs/research/mature-stem-separation-products-2026-08.md:1-4`]

## Links

- README: `README.md`
- Detailed design: `docs/superpowers/specs/2026-08-20-audio-to-instrument-score-design.md`
- Explore: `docs/reviewspec/beat-aware-single-melody-score/explore.md`
- Spec: `docs/reviewspec/beat-aware-single-melody-score/spec.md`
- Prior registry: `docs/reviewspec/REGISTRY.md`
- Prior design review: `docs/reviewspec/first-verified-monophonic-score/design-review.md`
- Prior code review: `docs/reviewspec/first-verified-monophonic-score/review.md`
- Ground-truth research: `docs/research/midi-ground-truth-benchmarks-2026-08.md`
- Stem-separation research: `docs/research/audio-stem-separation-options-2026-08.md`, `docs/research/mature-stem-separation-products-2026-08.md`

## Open Questions

No blocking user-owned questions remain for this design gate. The following are intentionally build-owned within the approved scope and must be made explicit in build artifacts/tests:

- Exact simple-meter fixture set and whether the first TimeMap is fixture-backed, supplied, or deterministically derived.
- Exact numeric tolerances for second-to-beat mapping, beat-position scoring, measure-total rounding, and notated-duration acceptance.
- Exact ScoreIR duration vocabulary and rest representation, as long as exported MusicXML durations match ScoreIR.
- Exact REVIEW vs FAIL threshold split for ambiguous-but-diagnosable timing versus incoherent/unrepresentable timing.
- Exact schema field names beyond the approved observable fields and this review's provenance/diagnostic constraints.
