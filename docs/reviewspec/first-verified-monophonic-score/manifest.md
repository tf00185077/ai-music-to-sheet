# Claims manifest: first-verified-monophonic-score

Coding agent: AI Music Reviewspec Coder  
Spec: `docs/reviewspec/first-verified-monophonic-score/spec.md`  
Design review: `docs/reviewspec/first-verified-monophonic-score/design-review.md`  
Implementation scope: minimal Python package under `ai_music_to_sheet/` plus intent tests under `tests/`.

## Gate Evidence

- Approved spec exists and was not edited by this build.
- Completed design-review artifact exists and was incorporated before code.
- Spec validation: `python3 /Users/tf00185088/.paperclip/instances/default/companies/0d1b8931-30d8-4820-941e-b9ae5541da25/codex-home/skills/reviewspec-core--fca75830e7/scripts/validate_spec.py docs/reviewspec/first-verified-monophonic-score/spec.md` returned PASS.
- Initial red run before production package existed: `python3 -m unittest discover -s tests -v` returned 6 errors, all `ModuleNotFoundError: No module named 'ai_music_to_sheet'`.
- Final accumulated suite: `python3 -m unittest discover -s tests -v` returned OK, 6 tests.

## Tier Derivation

| Intent | self_tier | Reason |
|---|---|---|
| `INT-1` | Critical | User-visible core promise: supported MP3/MP4 media must complete. |
| `INT-2` | Core | Non-user-visible artifact contract; breakage hurts the feature and downstream notation. |
| `INT-3` | Critical | User-visible core promise: downloadable/importable MusicXML notation. |
| `INT-4` | Core | Non-user-visible evaluation plane; breakage hurts release and acceptance decisions. |
| `INT-5` | Critical | User-visible core promise: unsupported or low-confidence results must not be auto-accepted. |

## Claims

| behavior | test_layer | real_environment | self_tier | Tests |
|---|---|---|---|---|
| `INT-1` | Integration/E2E at public Python entrypoint | Real `ffprobe` inspection, real `ffmpeg` decode of generated MP3 and MP4 containers, real filesystem artifacts | Critical | `test_supported_mp3_and_mp4_complete_from_public_entrypoint` |
| `INT-2` | Integration | Real decoded media path, real NoteEvents JSON artifact, contract validator, filesystem persistence | Core | `test_note_events_are_ordered_traceable_and_non_overlapping` |
| `INT-3` | Integration | Real MusicXML file, stdlib XML parser, exporter round-trip pitch/count comparison against NoteEvents | Critical | `test_musicxml_is_parseable_single_part_and_matches_note_events` |
| `INT-4` | Integration plus scoring unit | Real fixed corpus run through media pipeline; direct ground-truth scorer for shifted-note trap | Core | `test_fixed_evaluation_corpus_reports_versions_metrics_and_status`, `test_self_consistent_shifted_notes_fail_ground_truth_scoring` |
| `INT-5` | Integration/E2E at public Python entrypoint | Real MP3/MP4 fixtures for unsupported polyphony and low-confidence competing pitch energy; stage-aware result manifest | Critical | `test_unsupported_and_low_confidence_results_are_not_auto_accepted` |

## Break-Test Evidence

All temporary defects were reverted before the final green suite.

| Intent | Temporary defect | Targeted command result |
|---|---|---|
| `INT-1` | Removed `.mp4` support from `SUPPORTED_FORMATS`. | `test_supported_mp3_and_mp4_complete_from_public_entrypoint` failed with `UNSUPPORTED_FORMAT` for MP4. |
| `INT-2` | Blank `source_id` in the NoteEvents artifact. | `test_note_events_are_ordered_traceable_and_non_overlapping` went red because the validator blocked the artifact. |
| `INT-3` | Transposed exported MusicXML pitches by one semitone. | `test_musicxml_is_parseable_single_part_and_matches_note_events` went red because no valid MusicXML artifact was published. |
| `INT-4` | Forced evaluation status to always return `PASS`. | `test_self_consistent_shifted_notes_fail_ground_truth_scoring` failed on `PASS != FAIL` for shifted notes. |
| `INT-5` | Forced every result to `ACCEPTED`. | `test_unsupported_and_low_confidence_results_are_not_auto_accepted` failed on unsupported input being accepted. |

## Honest Limits

- The transcriber is a deterministic clean-monophonic baseline for this approved slice, not a general automatic music transcription model.
- Tests use generated clean sine-wave fixtures transcoded through real MP3/MP4 containers; they do not claim correctness on mixed commercial recordings.
- `ffmpeg` and `ffprobe` are required real boundaries for media decoding in this build.
- No stem separation, arrangement, PDF/TAB export, manual correction, YouTube ingestion, or vendor API path is implemented or claimed.
- This manifest is a coding-agent claim map only. It is not `review.md` and does not self-approve the build.

