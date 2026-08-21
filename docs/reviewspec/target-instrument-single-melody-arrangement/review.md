# Review: target-instrument-single-melody-arrangement

Reviewed commit: `5ac3612fb61ad96b5c52870e01a7a5ceee7aa283`
Reviewer: independent reviewspec code review
Spec: `docs/reviewspec/target-instrument-single-melody-arrangement/spec.md`
Manifest: `docs/reviewspec/target-instrument-single-melody-arrangement/manifest.md`

Verdict: PASS

## Independent Answer Key

This answer key was derived from the approved spec and design review before reading the build tests.

| intent | derived tier | observable behavior required |
|--------|--------------|------------------------------|
| INT-1 | Critical | A supported target-profile request completes as accepted target output, identifies the requested profile, and writes an arranged score artifact citing source job, media, ScoreIR, and timing artifacts. |
| INT-2 | Core | Arranged notes preserve source score-note identities, source note event ids, measure/beat/absolute-beat positions, notated durations, and expose uniform pitch-transformation evidence while all sounded pitches fit the target profile range. |
| INT-3 | Critical | Delivered MusicXML is one requested-instrument part whose part name, note count, pitch order, measure positions, and notated durations match the arranged score artifact and stay within the target range. |
| INT-4 | Critical | Unsupported target profiles and no-global-shift unarrangeable requests return REVIEW or FAIL with profile/arrangement reasons and are not delivered as accepted sheet music. |
| INT-5 | Core | The fixed evaluation corpus reports arrangement quality with target profile, source ScoreIR, arranged score, MusicXML artifact versions, range-fit, rhythm-preservation, and PASS/REVIEW/FAIL arrangement status. |

## Verification

- Full accumulated suite: `PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests` -> `Ran 16 tests`, `OK`.
- Spec validator: `python /Users/tf00185088/.paperclip/instances/default/companies/0d1b8931-30d8-4820-941e-b9ae5541da25/codex-home/skills/reviewspec-core--fca75830e7/scripts/validate_spec.py docs/reviewspec/target-instrument-single-melody-arrangement/spec.md` -> `PASS`, 1 file structurally valid.
- Compile check: `PYTHONPYCACHEPREFIX="$PAPERCLIP_RUN_SCRATCH_DIR/pycache" python -m compileall -q ai_music_to_sheet` -> passed.
- Boundary mock audit: `rg -n 'mock|patch|MagicMock|monkeypatch|unittest\.mock' tests ai_music_to_sheet` -> no matches.
- Cross-round guard audit: the pre-review registry listed 10 active prior intents; every listed guarding test still exists under `tests/` and passed in the full accumulated suite.
- Mutation cleanup audit: after break-test reverts, tracked production diff for `ai_music_to_sheet/arrangement.py`, `ai_music_to_sheet/musicxml.py`, `ai_music_to_sheet/pipeline.py`, and `ai_music_to_sheet/evaluation.py` was empty.

## Manifest And Boundary Audit

The manifest claims match the independently derived tiers: INT-1, INT-3, and INT-4 are Critical; INT-2 and INT-5 are Core. The claimed integration boundaries are real for this repository slice: the tests generate MP3/MP4 media fixtures through `ffmpeg`, execute the public pipeline/evaluation paths, run the actual profile registry and arranger, and inspect real JSON and MusicXML artifacts written to temporary directories. No test or production path uses mocks for the claimed artifact, media, profile, arranger, MusicXML, or evaluation boundaries.

## Break-Testing

| intent | temporary mutation | command | red evidence |
|--------|--------------------|---------|--------------|
| INT-1 | Set arranged-score `source.score_ir_artifact` to an empty string in `arrange_score_ir`. | `python -m unittest discover -s tests -p 'test_target_instrument_single_melody_arrangement.py' -k test_int1_supported_target_request_delivers_traceable_arranged_score` | Failed at `tests/test_target_instrument_single_melody_arrangement.py:85` because the arranged score no longer cited the source ScoreIR artifact path. |
| INT-2 | Set arranged `target_pitch` to the unshifted source pitch. | `python -m unittest discover -s tests -p 'test_target_instrument_single_melody_arrangement.py' -k test_int2_arranged_notes_fit_profile_and_preserve_source_rhythm_identity` | Failed with `KeyError: 'arranged_score'` at line 99 because the arranged-score contract rejected the broken transformation before accepted delivery. |
| INT-3 | Wrote MusicXML part name `Melody` from the arranged exporter instead of the target arranged part name. | `python -m unittest discover -s tests -p 'test_target_instrument_single_melody_arrangement.py' -k test_int3_musicxml_presents_requested_part_and_matches_arranged_score` | Failed with `KeyError: 'musicxml'` at line 145 because MusicXML parse-back rejected the target XML before delivery. |
| INT-4 | Promoted `ArrangementNotAccepted` handling to `COMPLETED`/`PASS`. | `python -m unittest discover -s tests -p 'test_target_instrument_single_melody_arrangement.py' -k test_int4_unsupported_and_unarrangeable_target_requests_are_not_accepted` | Failed at line 166 because an unsupported profile returned `COMPLETED`/`ACCEPTED` instead of REVIEW/FAIL and NOT_ACCEPTED. |
| INT-5 | Disabled emission of the evaluation report `arrangement` section. | `python -m unittest discover -s tests -p 'test_target_instrument_single_melody_arrangement.py' -k test_int5_evaluation_reports_arrangement_quality_and_artifact_versions` | Failed with `KeyError: 'arrangement'` at line 216 because arrangement quality was no longer reported. |

All temporary mutations were reverted before the final full-suite run.

## Coverage (registry-readable)

| intent | tier | guarding_test | status |
|--------|------|---------------|--------|
| INT-1 | Critical | tests/test_target_instrument_single_melody_arrangement.py::TargetInstrumentSingleMelodyArrangementTests::test_int1_supported_target_request_delivers_traceable_arranged_score | active |
| INT-2 | Core | tests/test_target_instrument_single_melody_arrangement.py::TargetInstrumentSingleMelodyArrangementTests::test_int2_arranged_notes_fit_profile_and_preserve_source_rhythm_identity | active |
| INT-3 | Critical | tests/test_target_instrument_single_melody_arrangement.py::TargetInstrumentSingleMelodyArrangementTests::test_int3_musicxml_presents_requested_part_and_matches_arranged_score | active |
| INT-4 | Critical | tests/test_target_instrument_single_melody_arrangement.py::TargetInstrumentSingleMelodyArrangementTests::test_int4_unsupported_and_unarrangeable_target_requests_are_not_accepted | active |
| INT-5 | Core | tests/test_target_instrument_single_melody_arrangement.py::TargetInstrumentSingleMelodyArrangementTests::test_int5_evaluation_reports_arrangement_quality_and_artifact_versions | active |

## Covered

- Supported clean single-melody target requests for `beginner-soprano-recorder`.
- Traceable arranged score artifact creation from the source ScoreIR and timing artifacts.
- Single-global-octave-shift pitch transformation with source identity and rhythm preservation.
- Arranged MusicXML delivery matching the arranged score artifact.
- Unsupported target-profile and no-global-shift unarrangeable rejection.
- Arrangement quality reporting in the fixed MP3/MP4 evaluation corpus.
- Prior certified active intents from the first verified monophonic score and beat-aware score rounds.

## Not Covered / Residual Risk

- Mixed/polyphonic recordings, stem separation, YouTube ingestion, GUI/web UI, PDF/TAB rendering, manual correction, rich difficulty optimization, subjective musicality, transposing/written-pitch semantics, per-note octave wrapping, and multi-instrument orchestration remain outside this approved slice.
- Evidence is based on deterministic generated media fixtures and one supported non-transposing sounded-pitch range-only profile; it does not certify noisy real-world recordings or additional instrument profiles.
