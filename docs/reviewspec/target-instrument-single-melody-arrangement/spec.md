# Spec: target-instrument-single-melody-arrangement
Context: Third verified delivery slice for ai-music-to-sheet. It builds on the certified clean monophonic MP3/MP4 and beat-aware ScoreIR path by adding the first target-instrument arrangement contract for a supported single-melody profile; mixed recordings, stem separation, YouTube ingestion, manual correction, PDF/TAB export, rich difficulty reduction, and subjective musicality remain outside this round.

## INT-1: Target instrument requests are represented
- intent: A supported clean single-melody run can be requested for a declared target instrument profile instead of only producing a generic melody score.
- observable: The completed result identifies the requested supported profile and includes an arranged score artifact that cites the source job, source media, source ScoreIR, and timing artifacts used to create the target-instrument output.
- user_visible: yes
- sensitivity: core-promise

## INT-2: Arranged notes fit the profile
- intent: The arranged melody is transformed only within the supported monophonic arrangement envelope so its notes are playable for the target profile while retaining source traceability and rhythm.
- observable: The arranged score artifact cites source score-note identities, keeps the source measure, beat, and notated-duration sequence, exposes any pitch transformation applied to each note, and contains only pitches within the target profile's declared range.
- user_visible: no
- sensitivity: core-promise

## INT-3: Delivered MusicXML matches the arrangement
- intent: The downloadable score artifact presents the target-instrument arrangement rather than the unarranged generic melody.
- observable: The MusicXML artifact is parseable as one part for the requested instrument and its part name, note count, pitch order, measure positions, and notated durations match the arranged score artifact, with all sounded pitches inside the target profile's declared range.
- user_visible: yes
- sensitivity: core-promise

## INT-4: Unarrangeable requests are not auto-accepted
- intent: A target instrument request that is unsupported or cannot produce a playable arranged score within the supported envelope is not presented as accepted sheet music.
- observable: The processing result exposes REVIEW or FAIL with an instrument-profile or arrangement reason and does not place that output in the same completed/accepted state as passing arranged fixture cases.
- user_visible: yes
- sensitivity: core-promise

## INT-5: Arrangement quality is evaluated
- intent: Ground-truth runs report whether the target-instrument arrangement preserved the melody structure while satisfying the profile constraints.
- observable: Running the fixed evaluation corpus creates an EvaluationReport that names each arranged case, cites the target profile, source ScoreIR, arranged score, and MusicXML artifact versions, includes range-fit and rhythm-preservation results, and marks the arrangement result PASS, REVIEW, or FAIL.
- user_visible: no
- sensitivity: core-promise
