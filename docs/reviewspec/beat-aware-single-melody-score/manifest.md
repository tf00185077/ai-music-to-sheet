# Claims manifest: beat-aware-single-melody-score

## Build scope

- Spec: `docs/reviewspec/beat-aware-single-melody-score/spec.md`
- Design gate: `docs/reviewspec/beat-aware-single-melody-score/design-review.md`
- Coding role only: this manifest records implementation claims for independent review; it is not an approval.

## Red/green evidence

- Red before implementation: `python3 -m unittest discover -s tests -p 'test_beat_aware_single_melody_score.py' -v` produced failing coverage for all five new intents: missing `time_map`, missing `score_ir`, missing timing artifact version citations, and irregular timing incorrectly accepted.
- Green after implementation: `python3 -m unittest discover -s tests -p 'test_*.py' -v` passed 11 tests.
- Compile check: `PYTHONPYCACHEPREFIX="$PAPERCLIP_RUN_SCRATCH_DIR/pycache" python3 -m compileall -q ai_music_to_sheet tests` passed.

## Claims

| behavior | self_tier | test_layer | real_environment | guarding tests | break-test evidence |
|---|---|---|---|---|---|
| `INT-1` | Core | integration | Public `process_media_file` path with generated real MP3 input, ffmpeg/ffprobe decode/inspect, real filesystem JSON artifacts, no mocked timing boundary. | `tests/test_beat_aware_single_melody_score.py::BeatAwareSingleMelodyScoreTests.test_int1_time_map_exposes_reversible_musical_time` | Temporarily changed TimeMap support mode to `broken-simple-meter`; the test failed on the expected `deterministic-simple-meter` artifact contract. |
| `INT-2` | Core | integration | Public media pipeline plus real `NoteEvents` artifact feeding `ScoreIR` quantization, no mocked note-event or score boundary. | `tests/test_beat_aware_single_melody_score.py::BeatAwareSingleMelodyScoreTests.test_int2_score_ir_preserves_traceable_quantized_single_voice_notes` | Temporarily corrupted `source_note_event_id`; the test failed on source note traceability. |
| `INT-3` | Critical | integration against real artifact boundary | Public pipeline writes real MusicXML, parses it with `xml.etree.ElementTree`, and compares parsed measure/pitch/duration/type values to real `ScoreIR`; no mocked exporter/parser boundary. | `tests/test_beat_aware_single_melody_score.py::BeatAwareSingleMelodyScoreTests.test_int3_musicxml_measure_structure_matches_score_ir` | Temporarily wrote `broken-duration` note types in MusicXML; exporter parse-back rejected the artifact and the guarding test went red. |
| `INT-4` | Core | integration | `run_evaluation_corpus` processes real generated MP3/MP4 cases through the public pipeline and writes real evaluation report files; no mocked corpus, artifact, or scorer boundary. | `tests/test_beat_aware_single_melody_score.py::BeatAwareSingleMelodyScoreTests.test_int4_evaluation_report_scores_timing_and_cites_artifact_versions` | Temporarily renamed the `score_ir` artifact version citation; the test failed on missing `score_ir` in each case report. |
| `INT-5` | Critical | integration against real status/artifact boundary | Public `process_media_file` path with a real irregular MP3 fixture, real quantization gate, result JSON status, and artifact set; no mocked user-visible status boundary. | `tests/test_beat_aware_single_melody_score.py::BeatAwareSingleMelodyScoreTests.test_int5_unquantizable_timing_is_not_auto_accepted` | Temporarily weakened duration tolerance to `1.0` beat; the irregular fixture became `COMPLETED`/`ACCEPTED`, and the test failed. |

## Regression coverage

- Active prior `first-verified-monophonic-score` intents remain guarded by `tests/test_first_verified_monophonic_score.py`.
- Full accumulated suite evidence: `python3 -m unittest discover -s tests -p 'test_*.py' -v` passed 11 tests after all temporary break-test changes were reverted.

## Residual risk

- The TimeMap producer is intentionally deterministic-simple-meter only; it does not claim arbitrary beat tracking.
- The first quantizer supports a small duration vocabulary and rejects unsupported cross-measure notes instead of emitting ties.
