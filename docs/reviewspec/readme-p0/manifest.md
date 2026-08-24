# Claims manifest: README P0 verifiable MVP

- candidate_sha: the canonical command records the exact clean-checkout `git rev-parse HEAD` in
  `artifacts/p0/latest/process-test-report.json` at `payload.candidate_sha`; the same literal SHA is
  recorded in the AIM-3 handoff comment. A commit cannot truthfully embed its own not-yet-created
  SHA, so this runtime field is the non-self-referential source of truth.
- evidence_paths: `artifacts/p0/latest/process-test-report.json`,
  `artifacts/p0/latest/evaluation-transcription.json`,
  `artifacts/p0/latest/evaluation-arrangement.json`,
  `artifacts/p0/latest/provenance-index.json`, `artifacts/p0/latest/verify.log`, and
  `artifacts/p0/latest/samples/`.
- scope_boundary: transparent deterministic contract/evaluator fixtures only; no holdout,
  real-song, unseen-song, separation, transcription, arrangement, or perceptual-quality claim.

## INT-1
- behavior: INT-1 — all eight versioned contracts publish JSON Schemas and real-file semantic round trips; malformed, unsupported, incompatible, and stale-checksum cases return structured rejection details in `tests.test_contracts.SchemaContractTests`.
- test_layer: integration
- real_environment: Python 3.9+ standard-library JSON serialization against real temporary files and committed schemas; no filesystem or serializer mock.
- self_tier: Core

## INT-2
- behavior: INT-2 — transcription evidence and arrangement decisions remain non-interchangeable, unknowns are explicit, and drums/piano/guitar retain distinct event fields in `test_mode_and_instrument_shapes_are_distinct_and_truthful` and pipeline cross-mode negatives.
- test_layer: integration
- real_environment: Real serialized TrackIR artifacts and lineage-resolved evidence IDs in an on-disk ArtifactStore; no provenance mock.
- self_tier: Core

## INT-3
- behavior: INT-3 — committed compatibility vectors prove additive same-major reads, explicit unsupported-major failure, and source-preserving new-ID migration with equal normalized musical semantics.
- test_layer: integration
- real_environment: Real JSON vector file, migration snapshot, contract validator, and serialized artifact structures; no version adapter mock.
- self_tier: Core

## INT-4
- behavior: INT-4 — the immutable `p0-fixtures/1.0.0` manifest covers every README fixture category with CC0 provenance, truth, conventions, file checksums, and an external tamper lock; missing, corrupt, annotation-incompatible, and coordinated under-version edits fail.
- test_layer: integration
- real_environment: Real committed WAV/JSON bytes, filesystem deletion/mutation, SHA-256 streaming, manifest, and external lock; no data or checksum mock.
- self_tier: Core

## INT-5
- behavior: INT-5 — final reports traverse every ancestor and detect deletion, replacement, forgery, stale recorded hashes, and content/model/parameter/schema/mode cache-key drift in `tests.test_provenance` and stale pipeline negatives.
- test_layer: integration
- real_environment: Real on-disk artifact graph with real JSON content hashes and recursive resolution; no store, hash, or cache mock.
- self_tier: Core

## INT-6
- behavior: INT-6 — identical fixture/version/program/model/parameter/seed runs are semantically equal, while missing/corrupt/incompatible fixtures terminate instead of being skipped into green.
- test_layer: integration
- real_environment: Two independently written temporary artifact stores plus real committed fixture bytes and the single production semantic comparator.
- self_tier: Core

## INT-7
- behavior: INT-7 — evaluator controls pin perfect, shifted, deleted, inserted, wrong-class, empty, inclusive tolerance-boundary, competing-match, per-class, micro, macro, and finite-result behavior in `tests.test_evaluators`.
- test_layer: unit
- real_environment: Production evaluator with real numeric inputs and no mocked matcher; evaluator version/tolerance/policies are serialized into EvaluationReport.
- self_tier: Core

## INT-8
- behavior: INT-8 — distinct cross-linked EvaluationReport and ProcessTestReport artifacts cover success and failure, reject low-score false passes, missing facts, changed evidence/log checksums, and transitive human-correction contamination, with six machine-distinct failure families.
- test_layer: integration
- real_environment: Real report JSON, log files, artifact-store checksums, recursive lineage, and automatic-category taint inspection; no report or evidence mock.
- self_tier: Core

## INT-9
- behavior: INT-9 — deterministic transcription and arrangement flows reach complete report lineage, while absent target, failed/low-confidence/needs-human upstream, cross-mode consumer, and stale-downstream flows stop at the declared boundary.
- test_layer: integration
- real_environment: Real fixture files and on-disk SourceMedia→CanonicalAudio→SongAnalysis/StemSet→TrackIR→NotationIR→EvaluationReport→ProcessTestReport graphs.
- self_tier: Core

## INT-10
- behavior: INT-10 — `./scripts/verify-p0 --output artifacts/p0/latest` requires exact expected/discovered execution, a clean SHA, all A–G groups, both legal modes, outputs, and thresholds; clean subprocess succeeds while corruption, missing check manifest, and forced low score exit nonzero with retained failure reports.
- test_layer: integration
- real_environment: Real clean temporary Git repositories, executable POSIX script, Python subprocess exit codes, committed CI workflow, and real output files; no Git, subprocess, or CI-command mock.
- self_tier: Core
