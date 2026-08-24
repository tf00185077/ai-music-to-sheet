# P0 artifact contracts

The versioned JSON Schemas are indexed by
`contracts/schemas/1.0.0/index.json`. The dependency-free reference validator is
`p0.contracts.validate_artifact`; it enforces the cross-artifact and integrity rules that JSON
Schema alone cannot resolve.

## Common envelope

Every artifact contains:

- `artifact_type`, `artifact_id`, `content_hash`, and semantic `schema_version`;
- ordered `source_artifact_ids` plus typed `source_artifacts` references containing the recorded
  upstream hash and validity key;
- generator name, program/code/model versions, parameters, and seed;
- UTC creation time and runtime/OS/architecture environment;
- one of `success`, `low_confidence`, `failed`, or `needs_human_confirmation`;
- explicit artifact confidence, structured failure detail, human-correction taint, migration
  metadata, and a typed payload.

`content_hash` covers the complete serialized artifact except the hash field itself. The artifact
ID is stable for one logical product; replacement under the same ID changes the content hash and
is detected by downstream references. A downstream validity key hashes the full tuple
`{payload content hash, model name+version, parameters, schema_version, mode}`. Using payload
content alone, or relying on the full-envelope integrity hash where model metadata changes it
implicitly, is invalid: every tuple component is independently load-bearing and tested.

Non-success upstream state propagates fail-closed. Human correction is a transitive lineage taint:
an automatic benchmark cannot consume any descendant of a corrected artifact.

## Payload boundaries

| Artifact | Payload boundary |
| --- | --- |
| `SourceMedia` | media format/hash/size, track count, source identity, and usage rights |
| `CanonicalAudio` | sample rate, channel layout, sample format, duration, and audio hash |
| `SongAnalysis` | tempo map, beats/downbeats, meter, key, sections, and per-fact confidence |
| `StemSet` | taxonomy, stem path/hash, target presence state, and confidence |
| `TrackIR` | mode, instrument, explicit presence, and instrument-specific events |
| `NotationIR` | measures, voices, staff, meter, tempo, ties, and instrument notation |
| `EvaluationReport` | scored artifact provenance, evaluator definition/tolerance, metrics, thresholds, and its process-report cross-link |
| `ProcessTestReport` | run-level inputs, versions, stages, timings, environment, evidence/log references, checks, thresholds, expected/executed coverage, status/reason, candidate SHA, and evaluation-report cross-links |

Transcription events require resolvable stem/audio span evidence. P0 proves presence, resolution,
and bounds only; it does not prove the evidence is musically faithful. Arrangement events require
a rule and reason and cannot carry transcription evidence. Drum events preserve drum class,
onset, velocity, and technique. Piano events preserve pitch, onset/offset, voice, hand, pedal, and
velocity. Guitar events preserve pitch, onset/offset, string, fret, tuning, capo, technique, and
velocity. Unknown facts are `{state: "unknown", value: null, confidence: null}`; concealed defaults
are invalid.

## Compatibility and migration

Readers accept additive optional fields within schema major `1`. Any other major is a structured
`unsupported_major` rejection. Frozen non-vacuous vectors live in
`contracts/compatibility-vectors.json`.

The legacy `0.9.0` migration adapter does not overwrite its source. It mints a new artifact ID,
embeds the original snapshot and its ID/version, records an empty allowed-difference list, and is
accepted only when the single normalized musical-semantic comparator reports equality.

## Normalized musical semantics

`p0.contracts.semantic_view` is the single comparator used by round trips, migrations, and reruns.
It compares the artifact type and every payload field recursively. Absolute path prefixes are
normalized; relative evidence paths remain. Envelope identity, integrity, version, provenance,
generator, creation time, and execution environment are validated independently and are not
musical payload. Thus a musical-field mutation turns equality red, while creation-time,
environment, or absolute-root changes do not manufacture a musical difference.

## Failure families

Machine reports keep six responses distinguishable:

1. `contract_malformation`
2. `integrity_tamper_stale`
3. `evaluator_numeric`
4. `reproducibility_cross_run`
5. `coverage_skip_gate`
6. `contamination_taint`

These families share a nonzero gate result but require different operator actions and therefore
must never collapse into one opaque error.
