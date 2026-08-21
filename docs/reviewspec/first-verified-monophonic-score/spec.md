# Spec: first-verified-monophonic-score
Context: First verified delivery slice for ai-music-to-sheet. It covers clean monophonic MP3/MP4 media through machine-checkable note and score artifacts; mixed recordings, stem separation, arrangement, PDF/TAB export, and manual correction are outside this round.

## INT-1: Supported MP3/MP4 media completes
- intent: A user can provide a clean monophonic melody as either an MP3 or MP4 file and receive a completed processing result instead of a format-specific failure.
- observable: From the product's public entrypoint, the same supported melody encoded as MP3 and MP4 reaches a completed state with produced artifacts and source metadata identifying the input format.
- user_visible: yes
- sensitivity: core-promise

## INT-2: Note events are produced
- intent: The completed result includes the melody as ordered note events with pitch, onset, offset or duration, and confidence sufficient for downstream notation.
- observable: The returned or saved note-event artifact lists notes in time order, retains source/job identity, and contains no overlapping notes for the supported monophonic input.
- user_visible: no
- sensitivity: core-promise

## INT-3: A notation artifact is delivered
- intent: The same melody is represented as a single-part score artifact that a user can download or import for preview and editing.
- observable: The result includes a parseable MusicXML file whose note sequence matches the note-event artifact for pitch order and total note count.
- user_visible: yes
- sensitivity: core-promise

## INT-4: Ground-truth runs produce quality reports
- intent: When reference note data is available for an input, the run produces an evaluation report with pass, review, or fail status and note-accuracy metrics against that reference.
- observable: Running the fixed evaluation corpus creates an EvaluationReport that names each case, cites the source artifact versions, includes pitch/onset and duration/offset scoring, and marks the overall result PASS, REVIEW, or FAIL.
- user_visible: no
- sensitivity: core-promise

## INT-5: Unsupported or low-confidence results are not auto-accepted
- intent: Inputs outside the supported clean-monophonic scope or results below the quality threshold are not presented as automatically accepted sheet music.
- observable: The processing result exposes REVIEW or FAIL with a reason and does not place that output in the same completed/accepted state as passing fixture cases.
- user_visible: yes
- sensitivity: core-promise
