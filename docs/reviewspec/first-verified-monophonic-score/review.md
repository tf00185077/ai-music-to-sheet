# Review: first-verified-monophonic-score

Verdict: PASS

Reviewer: AI Music Reviewspec Code Reviewer  
Spec: `docs/reviewspec/first-verified-monophonic-score/spec.md`  
Manifest: `docs/reviewspec/first-verified-monophonic-score/manifest.md`  
Reviewed commit: `4d5c05263c0c4f4eb819e0a2900e9cd7bac4b4e0`

## Independent Answer Key

| intent | derived tier | required observable behavior |
|---|---|---|
| INT-1 | Critical | The public entrypoint accepts the same clean monophonic melody as MP3 and MP4, reaches `COMPLETED`, produces artifacts, and preserves source input-format metadata. |
| INT-2 | Core | NoteEvents are ordered, traceable to job/source identity, include pitch/onset/offset-or-duration/confidence, and contain no overlaps for supported monophonic input. |
| INT-3 | Critical | A parseable single-part MusicXML artifact is delivered and matches the NoteEvents pitch order and note count. |
| INT-4 | Core | The fixed ground-truth corpus produces an EvaluationReport naming cases, citing artifact versions, scoring pitch/onset and duration/offset, and using PASS/REVIEW/FAIL. |
| INT-5 | Critical | Unsupported-scope or low-confidence outputs expose REVIEW/FAIL with a reason and are not promoted to the accepted passing state. |

## Test Run

`python3 -m unittest discover -s tests -v` returned OK: 6 tests passed.

`python3 /Users/tf00185088/.paperclip/instances/default/companies/0d1b8931-30d8-4820-941e-b9ae5541da25/codex-home/skills/reviewspec-core--fca75830e7/scripts/validate_spec.py docs/reviewspec/first-verified-monophonic-score/spec.md` returned PASS.

## Coverage Audit

| intent | coverage finding |
|---|---|
| INT-1 | Covered by `test_supported_mp3_and_mp4_complete_from_public_entrypoint`; it drives generated MP3 and MP4 media through `process_media_file`, checks `COMPLETED`/`PASS`/`ACCEPTED`, source format/path metadata, and produced artifact files. |
| INT-2 | Covered by `test_note_events_are_ordered_traceable_and_non_overlapping`; it reads the persisted NoteEvents JSON and asserts job/source identity, input format, pitch sequence, time ordering, non-overlap, duration consistency, and confidence. |
| INT-3 | Covered by `test_musicxml_is_parseable_single_part_and_matches_note_events`; it parses the MusicXML with `xml.etree.ElementTree`, asserts one part, and compares parsed MIDI pitches to NoteEvents, which also proves note count through list equality. |
| INT-4 | Covered by `test_fixed_evaluation_corpus_reports_versions_metrics_and_status` and `test_self_consistent_shifted_notes_fail_ground_truth_scoring`; together they verify fixed corpus case names, artifact versions, metric dimensions, PASS output for fixture cases, and FAIL for shifted self-consistent notes. |
| INT-5 | Covered by `test_unsupported_and_low_confidence_results_are_not_auto_accepted`; it drives unsupported polyphonic and low-confidence fixtures through the public entrypoint and checks REVIEW/FAIL state, NOT_ACCEPTED, and machine-readable reasons. |

## Break-Testing Evidence

All temporary production-code mutations were reverted before the final green suite.

| intent | temporary mutation | expected red signal observed |
|---|---|---|
| INT-1 | Removed `.mp4` from `SUPPORTED_FORMATS` in `ai_music_to_sheet/media.py`. | `test_supported_mp3_and_mp4_complete_from_public_entrypoint` failed because MP4 returned `UNSUPPORTED_FORMAT` instead of `COMPLETED`. |
| INT-2 | Set NoteEvents `source_id` to an empty string in `ai_music_to_sheet/pipeline.py`. | `test_note_events_are_ordered_traceable_and_non_overlapping` errored because no valid NoteEvents artifact was published; the pipeline returned `NOTE_EVENTS_CONTRACT` with `missing source_id`. |
| INT-3 | Transposed exported MusicXML pitches by one semitone in `ai_music_to_sheet/musicxml.py`. | `test_musicxml_is_parseable_single_part_and_matches_note_events` errored because no valid MusicXML artifact was published; the pipeline returned `MUSICXML_EXPORT` with pitch-sequence mismatch. |
| INT-4 | Forced `_status_for_metrics` in `ai_music_to_sheet/evaluation.py` to always return `PASS`. | `test_self_consistent_shifted_notes_fail_ground_truth_scoring` failed on `PASS != FAIL` while metrics showed onset/duration/offset accuracy at `0.0`. |
| INT-5 | Forced `finish()` in `ai_music_to_sheet/pipeline.py` to always set `acceptance = ACCEPTED`. | `test_unsupported_and_low_confidence_results_are_not_auto_accepted` failed because unsupported input was promoted to `ACCEPTED`. |

## Boundary Reality Audit

The claimed media boundary is real: tests require `/opt/homebrew/bin/ffmpeg` and `/opt/homebrew/bin/ffprobe`, transcode generated WAV fixtures into real MP3/MP4 containers, and the production code invokes `ffprobe` and `ffmpeg` through `subprocess.run`.

The claimed artifact boundary is real filesystem persistence: tests read generated JSON and MusicXML files from temporary output directories. `rg -n "mock|patch|MagicMock|unittest\\.mock|monkeypatch" tests ai_music_to_sheet` found no mock or patch usage in the product or tests.

## Cross-Round Regression

No prior `docs/reviewspec/*/review.md` files existed before this review, so there are no previously certified intents to check beyond the full accumulated suite.

## Coverage (registry-readable)

| intent | tier | guarding_test | status |
|--------|------|---------------|--------|
| INT-1 | Critical | tests/test_first_verified_monophonic_score.py::FirstVerifiedMonophonicScoreTests::test_supported_mp3_and_mp4_complete_from_public_entrypoint | active |
| INT-2 | Core | tests/test_first_verified_monophonic_score.py::FirstVerifiedMonophonicScoreTests::test_note_events_are_ordered_traceable_and_non_overlapping | active |
| INT-3 | Critical | tests/test_first_verified_monophonic_score.py::FirstVerifiedMonophonicScoreTests::test_musicxml_is_parseable_single_part_and_matches_note_events | active |
| INT-4 | Core | tests/test_first_verified_monophonic_score.py::FirstVerifiedMonophonicScoreTests::test_self_consistent_shifted_notes_fail_ground_truth_scoring | active |
| INT-5 | Critical | tests/test_first_verified_monophonic_score.py::FirstVerifiedMonophonicScoreTests::test_unsupported_and_low_confidence_results_are_not_auto_accepted | active |

## Covered Surface

Within this round, a human can skip manual verification of clean generated monophonic MP3/MP4 media reaching persisted NoteEvents, parseable matching single-part MusicXML, fixed-corpus evaluation reports, and non-acceptance for unsupported or low-confidence outputs.

## Not Covered

Mixed recordings, stem separation, arrangement, PDF/TAB export, manual correction, YouTube ingestion, vendor APIs, and transcription quality on arbitrary commercial recordings remain deliberately outside this round.
