# Explore · first-verified-monophonic-score

## Real goal (not just the stated solution)

The fixed product goal is not "choose an AI model for transcription"; it is to build a usable and verifiable path from user-provided MP3/MP4 music toward playable sheet music. The first build should create a narrow end-to-end slice where failure can be localized and measured, while preserving architecture freedom for future stem separation, mixed-audio transcription, arrangement, preview, correction, and export work.

The repository currently contains architecture and research documents, not production code. The README and design spec both argue for staged artifacts, saved intermediate data, confidence, and machine-verifiable evaluation before chasing broad original-song support. The research notes reinforce that stem separation and vendor/model choice are unstable implementation decisions, while ground-truth evaluation has a clear near-term shape through small fixed datasets and explicit note-event metrics.

## Candidate directions (2-4, each with a one-line trade-off)

1. Artifact-and-evaluation foundation only: define minimal artifacts, fixture cases, and evaluation reports before any media processing; lowest risk, but not yet usable as an MP3/MP4-to-score experience.
2. Clean monophonic MP3/MP4 to note events and score artifact: a constrained real user flow with objective fixture verification; narrow musically, but it proves the first full path from media input to notation output.
3. Vendor-led melody/MIDI adapter spike: integrate a commercial API such as Music AI or Fadr for faster apparent output; faster breadth, but cost, data handling, and vendor quality become early blockers before internal verification exists.
4. Stem separation benchmark first: compare separation providers on MUSDB/Slakh before notation; valuable later, but it does not directly prove a sheet-music delivery loop.

## Integration points / hidden complexity noticed

- There is no existing implementation, so the first build must establish its own public entrypoint, artifact locations, and verification report while staying small enough for independent review.
- MP3 and MP4 are container/codec concerns before music concerns; media ingestion must prove accepted formats produce traceable normalized audio metadata before transcription output is trusted.
- The README separates `CanonicalAudio`, `NoteEvents`, `SongIR`, `ScoreIR`, `ValidatedScore`, and `EvaluationReport`; the first slice should avoid overbuilding every named artifact, but it should not collapse the whole pipeline into an uninspectable black box.
- Ground truth matters because comparing two generated MIDI files only proves agreement, not correctness. A fixed fixture corpus with known note events is needed for machine verification.
- Stem separation is a major future dependency, but first-round mixed-song/stem work would make failures ambiguous: media decode, source separation, pitch tracking, beat mapping, quantization, and notation could all fail at once.
- MusicXML/PDF/TAB are different delivery surfaces. MusicXML is the smallest notation artifact that can be parsed and checked automatically; PDF can come later.
- Confidence and failure states are part of usability. A first build should visibly refuse or mark unsupported/low-confidence inputs instead of presenting every output as correct.

## Open questions to resolve in phase 2

- Should the first build optimize for a pure evaluation foundation or include a narrow user-facing media-to-score path?
- Which input scope is small enough for reliable verification while still honoring the MP3/MP4 product goal?
- What is the smallest artifact set downstream agents can implement without freezing the final `SongIR` and `ScoreIR` architecture too early?
- Which observable promises belong in the spec, and which details should remain implementation choices for the coder?
