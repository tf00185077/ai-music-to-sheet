# Explore · README P0 verifiable MVP

## Real goal (not just the stated solution)

Give every later music-analysis and transcription milestone a shared, executable truth boundary: artifacts must be interoperable and traceable, fixtures must be intact and reproducible, evaluators must score known controls correctly, and a pipeline must be unable to report success when evidence is missing or invalid.

Repository evidence at starting SHA `f4ff4de0e6afaf3e82698afa97d20ef7c73a8e92` is deliberately thin: the tracked tree contains only `README.md`. There is no implementation, test harness, fixture, dataset, package manifest, CI configuration, prior Reviewspec artifact, or `docs/decisions` memory to treat as established behavior.

## Candidate directions (2-4, each with a one-line trade-off)

1. **Schemas first, then separate validators** — makes every artifact contract explicit early, but risks green component tests without proving that the whole provenance and reporting chain composes.
2. **One deterministic vertical slice first** — proves the complete artifact graph quickly, but can under-specify the full negative, compatibility, fixture, and evaluator surfaces if used alone.
3. **Evaluation harness first** — establishes scoring and reporting truth early, but evaluators have no trustworthy inputs until artifact, fixture, and provenance contracts exist.
4. **Contract-complete vertical slice** — couple versioned schemas, fixtures, controlled evaluators, provenance, reports, and a deterministic two-mode stub behind one verification entry point; it is the smallest direction that exercises every README P0 completion gate, at the cost of a broader initial design review.

## Integration points / hidden complexity noticed

- The README names both `EvaluationReport` and `ProcessTestReport`. They need an explicit relationship or distinct contracts so a run-level gate cannot be confused with a scored artifact.
- Content hashes, artifact IDs, source IDs, migrations, and cache invalidation form one integrity model; validating them independently would miss stale-but-well-formed downstream artifacts.
- Semantic round-trip and deterministic rerun equality must tolerate only documented non-semantic fields such as creation timestamps; byte equality is not automatically musical-semantic equality.
- Fixture scope spans synthetic truth, rendered event/MIDI truth, isolated stems, annotated mixes, and negative/edge cases, plus licensing and immutable versioning. No such data is present in the repository today.
- Evaluator controls require explicit onset-boundary inclusion, one-to-one matching, empty-set behavior, per-class/micro/macro definitions, tolerances, and protection against NaN/Infinity/division by zero.
- `transcription` and `arrangement` are provenance claims, not presentation labels. Instrument absence, low confidence, failed upstream state, invented evidence, and cross-mode use must fail closed.
- Drum, piano, and guitar events have different irreducible semantics; a generic event bag could validate structurally while discarding the information later milestones need.
- A single-command clean-environment gate must detect empty suites, skipped cases, corrupt fixtures, missing reports, threshold failures, and manual corrections mixed into automatic results.
- CI artifact retention is evidence only when the retained report identifies exact input, fixture, schema, evaluator, program/model/parameter versions, and artifact paths.

## Open questions to resolve in phase 2

- Treat `EvaluationReport` as the scored, provenance-bearing artifact and `ProcessTestReport` as the run-level machine-readable gate report; require both and link them rather than silently aliasing them.
- Define semantic equality through normalized contract fields, with any allowed non-semantic differences documented and excluded explicitly.
- Since the repository supplies no licensed dataset or hidden corpus, freeze a transparent fixture-manifest requirement but make no holdout or real-model-quality claim.
- Require a real filesystem/process boundary and reviewer break-testing for the contract harness; mocks cannot stand in for the files, checksums, serialization, command exit status, or report artifacts being claimed.
- Keep P0 as one coupled build: schema, fixture, evaluator, provenance, report, and deterministic stub are independently testable but do not deliver the README objective in isolation. Separate issues are justified only for independent Design Review, Build, and Independent Review ownership gates.
