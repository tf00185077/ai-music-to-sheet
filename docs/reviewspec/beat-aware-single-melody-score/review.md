# Review: beat-aware-single-melody-score

Verdict: PASS

Reviewer: AI Music Reviewspec Code Reviewer  
Spec: `docs/reviewspec/beat-aware-single-melody-score/spec.md`  
Manifest: `docs/reviewspec/beat-aware-single-melody-score/manifest.md`  
Reviewed commit: `f2c089748d4ffac83edae4902901b6b65d20ac0d`

## Independent Answer Key

Derived before reading the manifest or tests.

| intent | derived tier | required observable behavior |
|---|---|---|
| INT-1 | Core | A completed supported clean monophonic run persists a TimeMap with job/source identity, tempo, time signature, beat or measure anchors, and note-event mappings that round-trip between source seconds and musical positions. |
| INT-2 | Core | A persisted ScoreIR represents the same melody as quantized single-voice score notes, preserves NoteEvents pitch order, cites source note-event ids, includes measure/beat/duration fields, and has no overlaps. |
| INT-3 | Critical | The delivered MusicXML is parseable as one part and exposes measured sheet structure with the expected time signature, measure boundaries, note count, pitch order, and durations matching ScoreIR. |
| INT-4 | Core | The fixed evaluation corpus writes an EvaluationReport that names each case, cites TimeMap and ScoreIR artifact versions, includes beat-position and notated-duration scoring, and reports PASS, REVIEW, or FAIL timing status. |
| INT-5 | Critical | Timing that cannot be coherently quantized exposes REVIEW or FAIL with a timing or quantization reason and is not promoted to the completed/accepted passing state. |

## Test Run

`python3 -m unittest discover -s tests -p 'test_*.py' -v` returned OK after all break-test mutations were reverted: 11 tests passed.

`python3 /Users/tf00185088/.paperclip/instances/default/companies/0d1b8931-30d8-4820-941e-b9ae5541da25/codex-home/skills/reviewspec-core--fca75830e7/scripts/validate_spec.py docs/reviewspec/beat-aware-single-melody-score/spec.md` returned PASS.

`PYTHONPYCACHEPREFIX="$PAPERCLIP_RUN_SCRATCH_DIR/pycache" python3 -m compileall -q ai_music_to_sheet tests` returned OK.

## Manifest Audit

The manifest tiers match the independently derived tiers: INT-3 and INT-5 are Critical because they are user-visible core-promise behavior; INT-1, INT-2, and INT-4 are Core because they are feature-critical but not directly user-visible.

The claimed real boundaries are supported by the code and tests: the tests create real WAV fixtures, transcode them with `/opt/homebrew/bin/ffmpeg`, inspect/decode through production `ffprobe`/`ffmpeg` subprocess paths, write JSON and MusicXML files to temporary directories, and parse the delivered MusicXML with `xml.etree.ElementTree`. `rg -n "mock|patch|MagicMock|unittest\\.mock|monkeypatch" tests ai_music_to_sheet` found no mock or patch usage.

## Coverage Audit

| intent | coverage finding |
|---|---|
| INT-1 | Covered by `test_int1_time_map_exposes_reversible_musical_time`; it drives generated MP3 through `process_media_file`, reads persisted TimeMap and NoteEvents JSON, and asserts job/source identity, 120 BPM, 4/4, support mode, anchors, mapping note ids, and round-trip onset deltas. |
| INT-2 | Covered by `test_int2_score_ir_preserves_traceable_quantized_single_voice_notes`; it reads persisted ScoreIR and NoteEvents JSON and asserts pitch order, source note-event ids, measure/beat positions, quarter-note durations, and non-overlap. |
| INT-3 | Covered by `test_int3_musicxml_measure_structure_matches_score_ir`; it parses the delivered MusicXML file and compares time signature, one-part structure, measure boundary, pitch order, measures, divisions, and note types against ScoreIR. |
| INT-4 | Covered by `test_int4_evaluation_report_scores_timing_and_cites_artifact_versions`; it runs generated MP3 and MP4 corpus cases through `run_evaluation_corpus`, checks case names and PASS status, and asserts TimeMap/ScoreIR version citations plus beat-position and notated-duration metrics. |
| INT-5 | Covered by `test_int5_unquantizable_timing_is_not_auto_accepted`; it processes a real irregular MP3 fixture and asserts REVIEW/FAIL state, NOT_ACCEPTED, and timing/timemap/quantization reason category. |

## Break-Testing Evidence

All temporary production-code mutations were reverted before the final green suite.

| intent | temporary mutation | expected red signal observed |
|---|---|---|
| INT-1 | Changed TimeMap `support.mode` from `deterministic-simple-meter` to `broken-simple-meter` in `ai_music_to_sheet/timing.py`. | Full suite failed only `test_int1_time_map_exposes_reversible_musical_time` on the support-mode artifact contract. |
| INT-2 | Changed ScoreIR `source_note_event_id` to `broken-{note_id}` in `ai_music_to_sheet/timing.py`. | Full suite failed only `test_int2_score_ir_preserves_traceable_quantized_single_voice_notes` on the source-note identity list. |
| INT-3 | Changed MusicXML beat type output from ScoreIR's `beat_unit` to `8` in `ai_music_to_sheet/musicxml.py`. | Full suite failed only `test_int3_musicxml_measure_structure_matches_score_ir` on parsed MusicXML `beat-type`. |
| INT-4 | Renamed the evaluation artifact-version key from `score_ir` to `score-ir` in `ai_music_to_sheet/pipeline.py`. | Full suite failed only `test_int4_evaluation_report_scores_timing_and_cites_artifact_versions` on the missing `score_ir` citation. |
| INT-5 | Weakened `DURATION_TOLERANCE_BEATS` from `0.12` to `1.0` in `ai_music_to_sheet/timing.py`. | Full suite failed only `test_int5_unquantizable_timing_is_not_auto_accepted`; the irregular fixture became `COMPLETED`/`PASS`/`ACCEPTED`. |

## Boundary Reality Audit

Critical INT-3 is verified against the real delivered artifact boundary: production writes a MusicXML file, the test parses that file, and assertions compare parsed sheet structure to persisted ScoreIR rather than a mocked exporter result.

Critical INT-5 is verified against the real processing-result boundary: production runs the media pipeline on a generated MP3 fixture, writes the result artifact, and the test checks the returned status/acceptance/reason values from the public entrypoint. The break-test proved the guard catches an actual promotion to `ACCEPTED`.

Core INT-1, INT-2, and INT-4 are also backed by real filesystem artifacts and public pipeline/evaluation entrypoints. No claimed real boundary is replaced by a mock.

## Cross-Round Regression

The full accumulated suite passed after all mutations were reverted. The five active prior registry intents from `first-verified-monophonic-score` kept passing guard tests:

| prior intent | guarding test observed green |
|---|---|
| first-verified-monophonic-score/INT-1 | `tests/test_first_verified_monophonic_score.py::FirstVerifiedMonophonicScoreTests::test_supported_mp3_and_mp4_complete_from_public_entrypoint` |
| first-verified-monophonic-score/INT-2 | `tests/test_first_verified_monophonic_score.py::FirstVerifiedMonophonicScoreTests::test_note_events_are_ordered_traceable_and_non_overlapping` |
| first-verified-monophonic-score/INT-3 | `tests/test_first_verified_monophonic_score.py::FirstVerifiedMonophonicScoreTests::test_musicxml_is_parseable_single_part_and_matches_note_events` |
| first-verified-monophonic-score/INT-4 | `tests/test_first_verified_monophonic_score.py::FirstVerifiedMonophonicScoreTests::test_self_consistent_shifted_notes_fail_ground_truth_scoring` |
| first-verified-monophonic-score/INT-5 | `tests/test_first_verified_monophonic_score.py::FirstVerifiedMonophonicScoreTests::test_unsupported_and_low_confidence_results_are_not_auto_accepted` |

## Coverage (registry-readable)

| intent | tier | guarding_test | status |
|--------|------|---------------|--------|
| INT-1 | Core | tests/test_beat_aware_single_melody_score.py::BeatAwareSingleMelodyScoreTests::test_int1_time_map_exposes_reversible_musical_time | active |
| INT-2 | Core | tests/test_beat_aware_single_melody_score.py::BeatAwareSingleMelodyScoreTests::test_int2_score_ir_preserves_traceable_quantized_single_voice_notes | active |
| INT-3 | Critical | tests/test_beat_aware_single_melody_score.py::BeatAwareSingleMelodyScoreTests::test_int3_musicxml_measure_structure_matches_score_ir | active |
| INT-4 | Core | tests/test_beat_aware_single_melody_score.py::BeatAwareSingleMelodyScoreTests::test_int4_evaluation_report_scores_timing_and_cites_artifact_versions | active |
| INT-5 | Critical | tests/test_beat_aware_single_melody_score.py::BeatAwareSingleMelodyScoreTests::test_int5_unquantizable_timing_is_not_auto_accepted | active |

## Covered Surface

Within this round, a human can skip manual verification for generated clean monophonic MP3/MP4 fixture coverage of TimeMap artifacts, ScoreIR quantized note traceability, ScoreIR-matching measured MusicXML, timing evaluation reports, and non-acceptance of unquantizable timing.

## Not Covered

Mixed recordings, stem separation, arrangement, PDF/TAB export, manual correction, YouTube ingestion, arbitrary beat tracking, and arbitrary real-world rhythm inference remain deliberately outside this round.
