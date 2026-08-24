# Spec: README P0 verifiable MVP
Context: Establish the repository's executable artifact-contract and validation baseline before any P1 feature work. P0 validates deterministic contracts and evaluators, not real-model transcription quality.

## INT-1: Versioned artifact contracts
- intent: Consumers can exchange SourceMedia, CanonicalAudio, SongAnalysis, StemSet, TrackIR, NotationIR, EvaluationReport, and ProcessTestReport artifacts whose version, identity, content integrity, upstream sources, generator provenance, creation context, and confidence or failure state are explicit.
- observable: Published schemas and examples expose the required metadata, valid artifacts preserve their musical meaning after serialization and deserialization, and malformed or unsupported artifacts return structured rejection details.
- user_visible: no
- sensitivity: core-promise

## INT-2: Truthful mode and instrument boundaries
- intent: Every TrackIR states transcription or arrangement truthfully, preserves the required audio evidence or arrangement-decision provenance, represents unknown or low-confidence facts explicitly, and retains the distinct drum, piano, or guitar semantics required by its instrument.
- observable: A consumer can distinguish both modes and all three instrument event shapes from the artifact alone, while invented transcription evidence, concealed defaults, incompatible instrument data, and cross-mode use are rejected.
- user_visible: no
- sensitivity: core-promise

## INT-3: Compatible evolution with traceable migration
- intent: Supported compatible schema evolution remains readable, unsupported major versions fail explicitly, and migrations create a new traceable artifact without changing musical meaning except for documented allowances.
- observable: Version-combination and migration results show supported reads succeeding, unsupported reads rejecting, and every migrated artifact retaining its original artifact and migration source chain.
- user_visible: no
- sensitivity: core-promise

## INT-4: Immutable and complete fixture manifests
- intent: A fixed-version fixture manifest identifies legally usable synthetic, rendered ground-truth, isolated-stem, annotated-mix, absent-instrument, low-volume, partial-presence, and masking cases with their checksums, annotations, taxonomy, coordinate conventions, and permitted purpose.
- observable: A consumer can resolve every fixture and ground truth by unique ID and version, while missing files, checksum changes, incompatible annotations, or in-place changes to a published dataset make validation fail.
- user_visible: no
- sensitivity: core-promise

## INT-5: End-to-end provenance and cache integrity
- intent: Every final artifact can be traced through the complete SourceMedia-to-report graph, and changes or corruption in any upstream content, model, parameter, identity, or mode invalidate affected downstream artifacts.
- observable: Provenance lookup returns every direct and indirect ancestor with matching content hashes; replacement, deletion, forgery, stale-cache reuse, or mode mislabeling is detected rather than reported as valid.
- user_visible: no
- sensitivity: core-promise

## INT-6: Reproducible validation inputs and artifacts
- intent: Repeating validation with the same fixture, program and model versions, parameters, and seed produces musically equivalent artifacts, and incomplete or damaged validation inputs cannot be skipped into a passing run.
- observable: Repeated-run comparisons report semantic equality, and every deliberately missing, damaged, or incompatible fixture terminates the affected benchmark with an explicit failure.
- user_visible: no
- sensitivity: core-promise

## INT-7: Evaluators that score controlled answers correctly
- intent: Metric evaluators respond correctly to perfect answers, out-of-tolerance shifts, omissions, insertions, wrong pitches or drum classes, empty inputs, tolerance boundaries, and competing event matches under documented per-class, micro, and macro definitions.
- observable: Control-answer reports reach the theoretical optimum or the expected directional and numeric result within declared tolerance, never double-count a match, and never emit an unhandled NaN, Infinity, crash, or divide-by-zero result.
- user_visible: no
- sensitivity: core-promise

## INT-8: Truthful machine-readable process reports
- intent: Successful and failed validation runs both emit a machine-readable ProcessTestReport that links exact inputs, fixtures, stages, schemas, programs, models, parameters, environment, artifacts, logs, metrics, thresholds, timing, and reasons, while isolating automatic results from human-corrected results.
- observable: Referenced evidence exists and matches its checksum, below-threshold or incomplete results are marked failed with a reason, and missing required report facts or mixed human corrections make the report invalid.
- user_visible: no
- sensitivity: core-promise

## INT-9: Deterministic two-mode P0 pipeline
- intent: A versioned fixture can traverse the complete artifact pipeline with deterministic stubs for both transcription and arrangement, while absent instruments, failed or unresolved upstream states, cross-mode misuse, and stale downstream artifacts stop at the correct boundary.
- observable: Both legal mode runs produce NotationIR, EvaluationReport, ProcessTestReport, and a complete traceable lineage; each required negative run terminates without a formally successful incompatible downstream artifact.
- user_visible: no
- sensitivity: core-promise

## INT-10: One-command clean verification evidence
- intent: The entire P0 baseline can be verified from a clean repository state through one documented command that cannot pass with failed, missing, corrupted, or silently skipped required checks.
- observable: A complete run exits zero and preserves its machine-readable report plus key artifacts; any required check failure exits nonzero, and CI exposes the exact command result and retained evidence.
- user_visible: no
- sensitivity: core-promise
