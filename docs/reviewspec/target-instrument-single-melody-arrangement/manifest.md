# Claims Manifest: target-instrument-single-melody-arrangement

Context: Coding-agent claims for the target-instrument single-melody arrangement build. This manifest does not approve the work; it lists what the independent reviewer should verify.

## Summary

- Red-before-green command: `python -m unittest discover -s tests -p 'test_target_instrument_single_melody_arrangement.py'`
- Red-before-green result before production implementation: `FAILED (errors=5)`. INT-1 through INT-4 failed because `process_media_file()` did not accept `target_profile_id`; INT-5 failed because corpus case reports had no `arrangement` section.
- Final accumulated suite: `python -m unittest discover -s tests` -> `Ran 16 tests in 2.321s`, `OK`.
- Spec validator: `python /Users/tf00185088/.paperclip/instances/default/companies/0d1b8931-30d8-4820-941e-b9ae5541da25/codex-home/skills/reviewspec-core--fca75830e7/scripts/validate_spec.py docs/reviewspec/target-instrument-single-melody-arrangement/spec.md` -> `PASS`, 1 file structurally valid.
- Registry guard: `python /Users/tf00185088/.paperclip/instances/default/companies/0d1b8931-30d8-4820-941e-b9ae5541da25/codex-home/skills/reviewspec-core--fca75830e7/scripts/build_registry.py` -> registry written, `Active intents: 10`, no structural problems.
- Compile check: `python -m compileall ai_music_to_sheet` -> completed successfully.

## INT-1

- behavior: `INT-1`
- self_tier: Critical
- test_layer: integration
- guarding_tests: `tests/test_target_instrument_single_melody_arrangement.py::TargetInstrumentSingleMelodyArrangementTests::test_int1_supported_target_request_delivers_traceable_arranged_score`
- real_environment: Generated MP3 fixture through the real media/decode/transcription/time-map/source-ScoreIR pipeline; real `target_profile.json`, `arranged_score.json`, source `score_ir.json`, `time_map.json`, and `result.json` files; no mocked artifact boundary.
- claim: A supported `beginner-soprano-recorder` request completes with `ACCEPTED`, identifies the target profile, and writes an arranged score citing source job, source media, source `ScoreIR`, and `TimeMap` artifacts and versions.
- break_test_evidence: Temporarily changed `arranged_score["source"]["score_ir_artifact"]` to `""`; running the guarding test failed with `AssertionError` because the arranged score no longer cited the source `ScoreIR` artifact path.

## INT-2

- behavior: `INT-2`
- self_tier: Core
- test_layer: integration
- guarding_tests: `tests/test_target_instrument_single_melody_arrangement.py::TargetInstrumentSingleMelodyArrangementTests::test_int2_arranged_notes_fit_profile_and_preserve_source_rhythm_identity`
- real_environment: Generated MP3 fixture through the real source pipeline and canonical in-repo arranger/profile registry; real arranged score artifact read from disk; no mocked profile, score, or timing boundary.
- claim: Accepted arranged notes use one score-wide octave shift, stay inside the target profile range, preserve source score-note identities, measure/beat/absolute-beat sequence, notated durations, and expose per-note pitch-transformation evidence.
- break_test_evidence: Temporarily changed arranged note `target_pitch` to equal the source pitch; running the guarding test failed with `KeyError: 'arranged_score'` because the arranged-score contract rejected the broken transformation before delivery.

## INT-3

- behavior: `INT-3`
- self_tier: Critical
- test_layer: integration
- guarding_tests: `tests/test_target_instrument_single_melody_arrangement.py::TargetInstrumentSingleMelodyArrangementTests::test_int3_musicxml_presents_requested_part_and_matches_arranged_score`
- real_environment: Generated MP3 fixture through the real pipeline and real MusicXML file written to disk, parsed with `xml.etree.ElementTree`; no mocked XML/export boundary.
- claim: Delivered MusicXML is a single target-instrument part named `Beginner Soprano Recorder`; parsed pitch order, measure positions, note count, and notated durations match the arranged score artifact.
- break_test_evidence: Temporarily changed the arranged MusicXML exporter to write part name `Melody`; running the guarding test failed with `KeyError: 'musicxml'` because export parse-back rejected the target XML before delivery.

## INT-4

- behavior: `INT-4`
- self_tier: Critical
- test_layer: integration
- guarding_tests: `tests/test_target_instrument_single_melody_arrangement.py::TargetInstrumentSingleMelodyArrangementTests::test_int4_unsupported_and_unarrangeable_target_requests_are_not_accepted`
- real_environment: Generated MP3 fixtures through the real pipeline, canonical profile registry, and arranger feasibility gate. The test covers an unsupported profile id and a fixture that can fit only with per-note wrapping, not one global shift.
- claim: Unsupported target profiles and no-global-shift arrangement requests return `REVIEW` or `FAIL`, `NOT_ACCEPTED`, stage-specific profile/arrangement reasons, and no delivered arranged score or target MusicXML artifact.
- break_test_evidence: Temporarily changed `ArrangementNotAccepted` handling to return `COMPLETED`/`PASS`; running the guarding test failed because an unsupported profile became `ACCEPTED`.

## INT-5

- behavior: `INT-5`
- self_tier: Core
- test_layer: integration
- guarding_tests: `tests/test_target_instrument_single_melody_arrangement.py::TargetInstrumentSingleMelodyArrangementTests::test_int5_evaluation_reports_arrangement_quality_and_artifact_versions`
- real_environment: Generated MP3 and MP4 corpus cases through the real `run_evaluation_corpus` path, real pipeline artifacts, real arranged score, and real MusicXML summary; no mocked evaluation boundary.
- claim: Arrangement corpus reports cite target profile, source `ScoreIR`, arranged score, MusicXML versions, range-fit result, rhythm-preservation result, and arrangement `PASS`/`REVIEW`/`FAIL` status.
- break_test_evidence: Temporarily removed the `arrangement` section from evaluation case reports; running the guarding test failed with `KeyError: 'arrangement'`.
