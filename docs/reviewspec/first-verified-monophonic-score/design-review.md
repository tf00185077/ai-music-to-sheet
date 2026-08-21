# Design record: first-verified-monophonic-score

_Last review: 2026-08-21 - reviewed commit `99ce86212137c3b2ddd9e4a14af3c477793601e2` - approved plan revision `05afc95a-a773-4c6d-b451-11e1a15ee1a7`_

Verdict: **cleared for build with required design constraints**. No production code is written by this review. The approved spec is narrow enough to build, but the build must preserve separate contracts for ingestion, scope eligibility, transcription quality, export validity, artifact delivery, and offline evaluation. A self-consistent MusicXML file is not proof of transcription correctness.

## Decision log (append-only - newest first)

### 2026-08-21 - round 1 - first review
- **Changed:** First design gate record for `first-verified-monophonic-score`; the spec is cleared only if the implementation keeps `completed`, `accepted`, `REVIEW`, and `FAIL` semantics stage-scoped and machine-readable.
- **Supersedes:** N/A - first review.
- **Carried over:** The approved scope remains clean monophonic MP3/MP4 to note events, MusicXML, and evaluation reports; mixed recordings, stem separation, arrangement, PDF/TAB export, and manual correction remain outside this round.
- **Driver provenance:** user-confirmed @ AIM-3 assignment and artifact-verified @ Paperclip AIM-2 `plan` document revision `05afc95a-a773-4c6d-b451-11e1a15ee1a7`; artifact-verified @ repository commit `99ce86212137c3b2ddd9e4a14af3c477793601e2`.

## Design Review

**Triage:** structural. This slice crosses public media input, artifact contracts, transcription, notation export, quality/status policy, and offline evaluation.

**Elicit:** prior record loaded: no prior `docs/decisions/` directory and no prior `design-review.md` for this build. Intent gap, boundary gap, and invariant gap were walked. No `ask_user_questions` interaction was posted because no unresolved user-owned product decision is required to clear this design gate: exact fixture content, schemas, threshold constants, storage layout, and transcription implementation remain build-owned choices as long as they satisfy the approved observable spec and this review's constraints. Future broader product questions in README remain out of scope for this slice.

**Reframe:** the system is protecting trust in a first media-to-notation loop, not merely proving a decoder or AI model can emit notes. The mis-framing risk is treating "MusicXML matches generated notes" as "the melody was correctly transcribed". The user learns per-job failures through a status/reason and artifacts; maintainers learn release/corpus failures through `EvaluationReport`. Green unit tests could still miss a real-world false accept where a clipped, polyphonic, or shifted melody yields parseable MusicXML and is shown as accepted.

## Purpose

Prove a narrow, inspectable path from supported user media to notation while making failures attributable by stage before expanding into mixed recordings, source separation, arrangement, manual correction, or broader export formats.

## Boundary Conditions

- MP3 and MP4 are supported only as media/container inputs for the same clean monophonic melody; format metadata must be preserved with source/job identity. [artifact-verified @ `docs/reviewspec/first-verified-monophonic-score/spec.md:4-8`]
- This round excludes mixed recordings, stem separation, arrangement, PDF/TAB export, and manual correction. [artifact-verified @ `docs/reviewspec/first-verified-monophonic-score/spec.md:2`]
- `NoteEvents` must be ordered, traceable to source/job identity, and non-overlapping for supported monophonic input. [artifact-verified @ `docs/reviewspec/first-verified-monophonic-score/spec.md:10-14`]
- MusicXML is the required notation artifact for this slice and must be parseable; its sequence must match the note-event artifact for pitch order and total note count. This is an exporter consistency check, not a correctness claim against audio. [artifact-verified @ `docs/reviewspec/first-verified-monophonic-score/spec.md:16-20`]
- Ground-truth evaluation must name cases, cite artifact versions, score pitch/onset and duration/offset, and produce PASS, REVIEW, or FAIL. [artifact-verified @ `docs/reviewspec/first-verified-monophonic-score/spec.md:22-26`]
- Unsupported or low-confidence results must not share the completed/accepted state used by passing fixture cases. [artifact-verified @ `docs/reviewspec/first-verified-monophonic-score/spec.md:28-32`]
- The broader architecture intentionally uses staged artifacts with source, version, uncertainty, confidence, and machine-verifiable reports; this slice may stay minimal but must not collapse into an opaque black box. [artifact-verified @ `README.md:17-24`; artifact-verified @ `docs/superpowers/specs/2026-08-20-audio-to-instrument-score-design.md:7-17`]
- Machine verification against unknown songs cannot strictly prove every note is correct; ground truth is required for accuracy claims. [artifact-verified @ `README.md:89-113`; artifact-verified @ `docs/superpowers/specs/2026-08-20-audio-to-instrument-score-design.md:120-129`; artifact-verified @ `docs/research/midi-ground-truth-benchmarks-2026-08.md:48-50`]

## Invariants / Cautions

- Never promote a job to accepted sheet music solely because media decoded and MusicXML parses; acceptance requires the relevant quality gate to pass. [artifact-verified @ `docs/reviewspec/first-verified-monophonic-score/spec.md:28-32`]
- Never use MusicXML-vs-NoteEvents self-consistency as a substitute for ground-truth transcription scoring. [artifact-verified @ `docs/research/midi-ground-truth-benchmarks-2026-08.md:48-50`]
- Never let an unsupported-scope input, a low-confidence in-scope result, and an internal artifact failure collapse into one opaque error. Their operator actions differ.
- Never overwrite or hide intermediate artifacts needed to diagnose the failed stage; staged artifacts are part of the project design. [artifact-verified @ `README.md:19-24`; artifact-verified @ `docs/superpowers/specs/2026-08-20-audio-to-instrument-score-design.md:9-15`]
- Never introduce a stem-separation or vendor dependency as a required path for this slice; the approved plan keeps those decisions for later. [artifact-verified @ `docs/reviewspec/first-verified-monophonic-score/explore.md:13-14`; artifact-verified @ `docs/reviewspec/first-verified-monophonic-score/spec.md:2`]

## Failure Map

```
Public entrypoint
  -> Media intake / source metadata
  -> Decode and canonical audio metadata
  -> Scope and audio-quality gate
  -> Monophonic transcription
  -> NoteEvents contract writer
  -> MusicXML exporter and parser
  -> Evaluation corpus / scorer
  -> Status publisher and artifact delivery
```

| Component | Depends on / path broken | Block vs report | Rollback need | Half-broken behavior | Surviving repair entry point |
|---|---|---|---|---|---|
| Public entrypoint | User job submission and result retrieval | Block only invalid request shape; report stage failures with job id | Do not create accepted result before job exists | Job exists but no stage event | Operator can inspect persisted job record and artifacts |
| Media intake / source metadata | Format acceptance, source/job identity | Block unsupported extension/container or missing source | Remove or quarantine partial upload metadata | Source exists without format metadata | Metadata validator can run without transcription |
| Decode / canonical audio | MP3/MP4 decoding, duration, channels, sample rate | Block corrupt, empty, unreadable, or unusable audio | Do not promote canonical audio until decode metadata validates | Audio file decoded but duration/clipping/silence facts absent | Decode report and raw source remain inspectable |
| Scope and audio-quality gate | Clean monophonic eligibility and usable signal | Block out-of-scope; REVIEW degraded but usable audio | Do not pass ambiguous scope as accepted transcription | Gate emits only low confidence without reason | Scope report lists reason independent of MusicXML |
| Transcription | Target signal to pitch/onset/offset/confidence | REVIEW/FAIL based on quality threshold and invariant violations | Keep previous stage artifacts; do not emit accepted score | Notes emitted without confidence or source identity | NoteEvents validator and evaluation runner inspect artifact directly |
| NoteEvents contract | Ordered, non-overlapping note artifact | Block invalid artifact before export | Do not write final note artifact until schema/invariants pass | Partial notes or overlaps exist | Schema/invariant validator reports note indexes and fields |
| MusicXML export / parse | Single-part notation delivery | Block invalid or mismatched MusicXML | Do not publish downloadable accepted MusicXML until parse/round-trip passes | File exists but parser cannot read or sequence mismatches | Exporter diagnostics read NoteEvents and produced XML |
| Evaluation corpus / scorer | Fixed cases and reference note data | Block release/auto-accept policy for corpus regression; do not relabel user decode failures | Preserve prior benchmark report/version | Report lacks case names, versions, or metric dimensions | Offline scorer can run from fixture references and saved artifacts |
| Status publisher / artifact delivery | User-visible state and downloads | Report precise current/final state; block accepted state if any required gate failed | Promote result bundle atomically after required artifacts pass | Status says complete but artifact missing | Artifact manifest and status audit identify missing stage |

## Tabletop Scenarios

| Scenario | System observes | System returns / does | Operator next step | Working prior state preserved? |
|---|---|---|---|---|
| Corrupt MP4 with valid extension | Intake accepts extension, decode cannot produce valid canonical audio | `FAIL` with media/decode category, source metadata, and decode reason; no transcription or MusicXML accepted | Inspect decode diagnostic, ask for a new file or supported codec | Yes; no accepted artifact bundle is promoted |
| MP3 decodes but is silent, clipped, or truncated | Canonical audio exists, quality metadata indicates unusable or degraded signal | `FAIL` if unusable; `REVIEW` only if degraded but still processable, with audio-quality reason | Inspect canonical audio metrics and decide whether to re-record or review | Yes; source and decode report remain available |
| Polyphonic or mixed recording simplified into one non-overlapping melody | Transcriber can emit a monophonic note list, but scope gate flags unsupported input | Unsupported-scope `REVIEW`/`FAIL`; not accepted as passing sheet music | Inspect scope reason and route to future mixed/stem workflow | Yes; no accepted score replaces the failed job state |
| All generated notes are shifted late, and MusicXML matches those shifted notes | Exporter round-trip passes pitch order/count, but ground-truth scoring fails onset/duration thresholds | Evaluation report marks REVIEW or FAIL for accuracy; exporter consistency remains a separate passed check | Inspect scoring report and stage attribution; fix transcription/timing, not exporter | Yes; prior benchmark artifacts and failed report are retained |
| NoteEvents are valid but MusicXML is malformed or missing a note | NoteEvents invariant passes; parser or sequence comparison fails | Export/notation `FAIL`; no accepted downloadable score | Inspect exporter diagnostic against saved NoteEvents and XML | Yes; NoteEvents remain as diagnostic artifact, accepted score is not promoted |

## Failure-Policy Families

| Family | Operations | Failure policy |
|---|---|---|
| Media ingestion terminal failures | Unsupported container, corrupt file, unreadable audio | Refuse early with media category; retry only with different input or codec support |
| Signal quality and scope eligibility | Silence, clipping, polyphony, mixed recordings, non-monophonic sources | Refuse or REVIEW with reason; do not auto-heal into an accepted melody |
| Artifact contract failures | Missing source/job identity, unordered/overlapping notes, invalid schema | Internal FAIL; block downstream artifact promotion |
| Transcription quality failures | Low confidence or poor ground-truth pitch/onset/duration score | REVIEW or FAIL with metric/stage reasons; keep diagnostics |
| Export consistency failures | Invalid MusicXML or mismatch against NoteEvents | Export FAIL; do not blame media or transcription unless evidence points there |
| Evaluation/release gate failures | Fixed corpus regression, missing case/version/metric data | Block release or auto-accept policy; do not relabel individual user jobs |
| Artifact delivery failures | Missing download, inconsistent status, partial bundle publish | Report delivery failure and preserve intermediate artifacts; promote atomically only after required bundle exists |

Merge reductio:
- If media decode and low transcription confidence share one failure path, a valid but hard melody can be misreported as a bad file, or a corrupt file can be sent to musical review.
- If exporter consistency and ground-truth scoring merge, a globally shifted melody can pass because XML faithfully reproduces wrong notes.
- If unsupported polyphony and low confidence merge, the system can suggest manual review for a product capability that this round explicitly does not support.
- If offline corpus regression and per-user job status merge, one benchmark failure can make unrelated user files look corrupt, or user failures can be hidden as release-only issues.

## Fitness Tests

These are architecture-shape tests for the build. They prevent regression to already-identified bad shapes; they do not prove the architecture catches novel mis-framings.

1. **Status orthogonality:** decode failure, out-of-scope polyphony, low-confidence monophonic transcription, invalid NoteEvents, invalid MusicXML, and benchmark regression each produce distinct machine-readable category values and the correct external response.
2. **Atomic accepted bundle:** no job can enter the accepted/completed-passing state until required source metadata, canonical audio metadata, NoteEvents, MusicXML parse/round-trip, and applicable evaluation status are present and valid.
3. **Self-consistency trap:** intentionally shift all NoteEvents while generating matching MusicXML; exporter consistency may pass, but ground-truth pitch/onset/duration scoring must fail or mark review.
4. **Monophonic sentinel:** a polyphonic fixture that can be simplified into non-overlapping NoteEvents must still be blocked from auto-acceptance by scope/status policy.
5. **Scoped status semantics:** product job status, artifact contract status, export status, and offline evaluation/release status must be represented separately or include an explicit `scope`/`stage` field.
6. **Provenance completeness:** all emitted artifacts used for acceptance include job id, source id or source path, input format, generator/version identifier, and creation time or run id.
7. **No stem/vendor dependency:** this build's required processing path must not import or require stem-separation providers, commercial vendor APIs, arrangement modules, PDF/TAB export, or manual correction components.
8. **Diagnostic survivability:** validation/scoring tools can inspect saved source metadata, NoteEvents, MusicXML, and EvaluationReport without the public upload path being healthy.

## Independent Review

An independent read-only subagent reviewed framing and converged on the staged-artifact approach, the clean monophonic boundary, and the need for ground-truth accuracy claims. It diverged by sharpening three risks that this record adopts as required constraints: MusicXML sequence matching is not correctness proof, PASS/REVIEW/FAIL semantics can drift across scopes, and INT-5 covers failure modes whose responses must stay distinct.

No divergence requires changing the approved spec before code. The divergences become build constraints and fitness tests above.

## Code Plan

For the build agent, in order:

1. Define the smallest repository-native contracts for job/source metadata, canonical audio metadata, NoteEvents, MusicXML output metadata, EvaluationCase, and EvaluationReport. Keep them minimal and versioned.
2. Implement one public entrypoint that accepts supported MP3 and MP4 files and writes a stage-aware result manifest. The exact interface is open, but the entrypoint must be observable from outside the product boundary.
3. Decode supported MP3/MP4 into a canonical audio artifact with source format, duration, sample rate/channel data, and failure reasons.
4. Add a scope/audio-quality gate before acceptance that separates unsupported scope from low-confidence in-scope transcription.
5. Produce ordered monophonic NoteEvents with pitch, onset, offset or duration, confidence, source/job identity, and contract validation before export.
6. Export a single-part MusicXML file, parse it back, and compare with NoteEvents for pitch order and note count at minimum.
7. Build a fixed evaluation corpus with reference note data, artifact version citations, pitch/onset and duration/offset metrics, and PASS/REVIEW/FAIL thresholds. Keep metric ownership in one EvaluationReport contract.
8. Wire status publication so accepted results, review results, failures, artifact contract failures, export failures, and corpus regressions remain distinguishable.
9. Add the architecture fitness tests above plus behavior tests derived from the reviewspec tier rule: INT-1, INT-3, and INT-5 are Critical because they are user-visible core promises; INT-2 and INT-4 are Core because breakage hurts the feature even though the artifacts are not directly user-visible.

## Facts Relied On

- The board-approved plan revision under review is `05afc95a-a773-4c6d-b451-11e1a15ee1a7`. [artifact-verified @ Paperclip AIM-2 `plan` document latestRevisionId, fetched 2026-08-21]
- The repository checkout reviewed was `99ce86212137c3b2ddd9e4a14af3c477793601e2`. [artifact-verified @ `git rev-parse HEAD`, 2026-08-21]
- The spec at `docs/reviewspec/first-verified-monophonic-score/spec.md` matches the committed file at `99ce86212137c3b2ddd9e4a14af3c477793601e2`. [artifact-verified @ `git diff --exit-code 99ce86212137c3b2ddd9e4a14af3c477793601e2 -- docs/reviewspec/first-verified-monophonic-score/spec.md`, 2026-08-21]
- The spec validator passed for the reviewed spec. [artifact-verified @ `python .../reviewspec-core--fca75830e7/scripts/validate_spec.py docs/reviewspec/first-verified-monophonic-score/spec.md`, 2026-08-21]
- The repository contains planning/research artifacts and no production implementation files at the reviewed commit. [artifact-verified @ `git ls-tree -r --name-only 99ce86212137c3b2ddd9e4a14af3c477793601e2`, 2026-08-21]
- The approved plan says the first build should prove a narrow path from user media to notation without choosing final architecture, stem-separation vendor, or arrangement strategy. [artifact-verified @ Paperclip AIM-2 `plan` document revision `05afc95a-a773-4c6d-b451-11e1a15ee1a7`]
- The README and detailed design require observable staged artifacts, provenance/version/confidence, and machine-verifiable reports. [artifact-verified @ `README.md:17-24`; artifact-verified @ `docs/superpowers/specs/2026-08-20-audio-to-instrument-score-design.md:9-17`]
- The detailed design explicitly treats MusicXML and MIDI as adapters rather than core models. [artifact-verified @ `docs/superpowers/specs/2026-08-20-audio-to-instrument-score-design.md:94`]
- Research states predicted MIDI-to-MIDI comparison measures agreement, not correctness; accuracy claims require note-event ground truth. [artifact-verified @ `docs/research/midi-ground-truth-benchmarks-2026-08.md:48-50`]

## Links

- README: `README.md`
- Detailed design: `docs/superpowers/specs/2026-08-20-audio-to-instrument-score-design.md`
- Explore: `docs/reviewspec/first-verified-monophonic-score/explore.md`
- Spec: `docs/reviewspec/first-verified-monophonic-score/spec.md`
- Ground-truth research: `docs/research/midi-ground-truth-benchmarks-2026-08.md`
- Stem-separation research: `docs/research/audio-stem-separation-options-2026-08.md`, `docs/research/mature-stem-separation-products-2026-08.md`

## Open Questions

No blocking user-owned questions remain for this design gate. The following are intentionally build-owned within the approved scope and must be recorded by the build artifact, not silently left implicit:

- Exact fixture/corpus content for the first clean monophonic melody set.
- Exact minimum/maximum duration, audio quality bounds, and transcriber support envelope for this slice.
- Exact numeric PASS/REVIEW/FAIL thresholds, as long as pitch/onset and duration/offset scoring exist and are reported.
- Exact minimal schema fields beyond those required by the spec and this design review.
