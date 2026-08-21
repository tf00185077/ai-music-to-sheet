# Spec: beat-aware-single-melody-score
Context: Second verified delivery slice for ai-music-to-sheet. It builds on the certified clean monophonic MP3/MP4 path by adding beat, measure, and quantized score structure for simple metered melodies; mixed recordings, stem separation, arrangement, PDF/TAB export, manual correction, YouTube ingestion, and arbitrary beat tracking remain outside this round.

## INT-1: Musical time is exposed
- intent: A supported clean monophonic run includes musical timing metadata that connects source seconds to beat and measure positions.
- observable: The completed result includes a TimeMap artifact with source/job identity, tempo and time-signature information, beat or measure anchors, and a reversible mapping between note-event seconds and musical positions for the supported fixture.
- user_visible: no
- sensitivity: core-promise

## INT-2: ScoreIR carries quantized notes
- intent: The melody is represented as score-level notes with measure position and quantized duration while retaining traceability to the transcribed note events.
- observable: The result includes a ScoreIR artifact whose notes preserve the NoteEvents pitch order, cite their source note-event identity, and express each note's measure, beat position, and notated duration without overlaps in the supported single-voice score.
- user_visible: no
- sensitivity: core-promise

## INT-3: Delivered MusicXML matches the score structure
- intent: The downloadable score artifact presents the same melody as measure-aware sheet music rather than an unmeasured note list.
- observable: The MusicXML artifact is parseable as one part with the expected time signature, measure boundaries, note count, pitch order, and note durations matching the ScoreIR artifact.
- user_visible: yes
- sensitivity: core-promise

## INT-4: Timing quality is evaluated
- intent: Ground-truth runs report whether musical timing and quantization are accurate enough to accept the generated score.
- observable: Running the fixed evaluation corpus creates an EvaluationReport that names each case, cites TimeMap and ScoreIR artifact versions, includes beat-position and notated-duration scoring, and marks the timing result PASS, REVIEW, or FAIL.
- user_visible: no
- sensitivity: core-promise

## INT-5: Unquantizable timing is not auto-accepted
- intent: A result whose timing cannot be mapped into coherent measures or acceptable note values is not presented as automatically accepted sheet music.
- observable: The processing result exposes REVIEW or FAIL with a timing or quantization reason and does not place that output in the same completed/accepted state as passing beat-aware fixture cases.
- user_visible: yes
- sensitivity: core-promise
