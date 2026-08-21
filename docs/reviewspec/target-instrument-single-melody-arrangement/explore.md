# Explore · target-instrument-single-melody-arrangement

## Real goal (not just the stated solution)

Advance from "the system can make a generic beat-aware single-melody score" to "the user can ask for a supported target instrument and receive sheet music that is playable for that instrument." The value is not rich artistic arranging yet; it is the first verifiable arrangement contract between the source melody, an instrument profile, a transformed score, and the delivered MusicXML.

The fixed product goal remains MP3/MP4-to-sheet-music for a user-selected instrument. The current certified surface can process clean monophonic MP3/MP4 into `NoteEvents`, `TimeMap`, `ScoreIR`, and measured MusicXML, but it still names the part generically as melody and does not apply any target instrument constraints. No `docs/decisions/` directory exists, so the available decision memory is README, the detailed design document, research notes, registry, and prior review artifacts.

## Candidate directions (2-4, each with a one-line trade-off)

1. Add a minimal `InstrumentProfile` and arranged `ScoreIR` path for one monophonic target instrument profile. Trade-off: smallest user-visible arrangement step, but it only proves range-aware single-line arranging rather than stylistic rearrangement.
2. Add PDF export for the already-certified MusicXML score. Trade-off: more directly downloadable for users, but it does not advance the "specified instrument playable" part of the goal and may add toolchain friction before arrangement semantics exist.
3. Start mixed-audio main-melody extraction or stem separation. Trade-off: closer to real songs, but current research shows vendor/model/dataset choices are a larger bounded round and would be easy to make unverifiable without first-class benchmark scaffolding.
4. Add manual correction markers for low-confidence or timing-risk spans. Trade-off: useful product loop, but the current CLI/batch surface has no product editing path, and it would not by itself create target-instrument output.

## Integration points / hidden complexity noticed

- `process_media_file` already produces `ScoreIR` and MusicXML after `TimeMap`; arrangement should sit after valid source `ScoreIR` and before the user-facing export/status decision.
- `ScoreIR` is the canonical score-level representation; MusicXML is an adapter. The next round should avoid making MusicXML the place where instrument constraints are applied.
- A first `InstrumentProfile` can be small: declared instrument identity, range, transposition/octave policy, voice count, and difficulty/support label. The observable outcome is profile-constrained output, not a broad taxonomy of instruments.
- "Playable" must be machine-checkable in the first round. Range and single-voice constraints are suitable; expressive idiom, fingering, articulations, PDF layout, and musical taste are not yet suitable.
- Octave transposition is the narrowest useful transformation for monophonic melody: it can preserve contour and rhythm while bringing notes into a declared range. It also creates break-testable failure modes when no supported transposition can fit the melody.
- The status model must distinguish arrangement/profile failure from media, transcription, timing, quantization, and MusicXML export failures so users do not see an unplayable arrangement as accepted sheet music.
- Evaluation should cite source `ScoreIR`, target profile, arranged score, and MusicXML/export versions. As prior reviews warned, self-consistent artifacts prove internal agreement, not transcription or musical correctness.
- Existing research keeps stem separation and real-mix benchmarking out of this slice; using a vendor API here would duplicate unsolved research choices and expand the round beyond the smallest arrangement step.

## Open questions to resolve in phase 2

- Should the next spec require a supported target instrument profile generically, or name the first profile? Sensible default: require a declared supported profile and leave the exact first profile build-owned.
- What is the minimal proof of "arranged" rather than "renamed"? Sensible default: require range-constrained note output with traceability to source `ScoreIR`, and require a fixture where the arranged score differs by octave or fails safely when it cannot fit.
- Is difficulty part of this slice? Sensible default: include difficulty/support metadata only, not rhythmic simplification or stylistic reduction.
- Which artifacts should be user-visible? Sensible default: the delivered MusicXML and processing result are user-visible; `InstrumentProfile`, arranged `ScoreIR`, and evaluation reports are machine-visible support artifacts.
