# Explore · beat-aware-single-melody-score

## Real goal (not just the stated solution)

The fixed product goal is still MP3/MP4-to-sheet music that a user can inspect, correct, and download. The certified first round proved a narrow media-to-note-events-to-MusicXML loop for clean monophonic files, but its score artifact is still mostly a pitch sequence with second-based durations. The next goal is to make the delivered notation musically timed: beats, measures, and quantized note values need to be explicit enough that the output is recognizably sheet music rather than only a parseable note dump.

There is no `docs/decisions/` decision-memory file in the repository at this point. The controlling memory for this exploration is therefore README.md, `docs/superpowers/specs/2026-08-20-audio-to-instrument-score-design.md`, the research notes, the active intent registry, and the certified `first-verified-monophonic-score` artifacts.

## Candidate directions (2-4, each with a one-line trade-off)

1. Beat-aware TimeMap and single-melody ScoreIR: turns the existing clean monophonic path into measure-aware notation, which is user-visible and testable without adding mixed-audio ambiguity.
2. Stem-separation benchmark harness: prepares the later original-song path with research-backed datasets, but it does not yet improve the user-visible sheet artifact.
3. Upload/job progress shell: advances product-platform UX around processing state, but the core musical result would remain no more capable than the first round.
4. Hand-authored SongIR to simple instrument arrangement: starts the arrangement track early, but it bypasses the just-certified audio pipeline and depends on an `InstrumentProfile` shape not yet proven by audio-to-score needs.

## Integration points / hidden complexity noticed

- README and the design doc both name `TimeMap`, `SongIR`, `ScoreIR`, and `ValidatedScore` as intermediate artifacts. The current code has source, canonical audio, note events, MusicXML, result, and evaluation artifacts, but no beat/measure mapping or score-level IR.
- `ai_music_to_sheet/musicxml.py` currently emits one measure and labels every note as a quarter note even when duration is derived from seconds. That satisfies parseability and pitch correspondence, but not musical rhythm semantics.
- The first certified tests generate synthetic melodies with known note seconds. A next round can extend that fixture style with a known tempo and time signature, keeping the boundary real while avoiding model/vendor decisions.
- Beat inference from arbitrary audio is a hard research problem. A bounded slice can accept or derive a simple TimeMap for clean fixtures and reject or review inputs that cannot be quantized within tolerance, without claiming general beat tracking.
- Cross-round regression matters: all five first-round intents must remain active and guarded while the new slice adds `TimeMap`/`ScoreIR`/measure-aware MusicXML behavior.

## Open questions to resolve in phase 2

- Should this round require automatic beat/tempo inference, or is a fixture-backed TimeMap artifact enough for the smallest verified step?
- What is the minimum observable ScoreIR promise: measures and beat positions only, or also note/rest durations expressed as divisions?
- How should quantization failure surface to users: `REVIEW` with a timing/notation reason, or `FAIL` when no coherent measure structure can be produced?
- Should the MusicXML observable prove measure structure only, or also prove note type/duration values match ScoreIR exactly?
