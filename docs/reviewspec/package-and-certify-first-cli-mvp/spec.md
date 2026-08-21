# Spec: package-and-certify-first-cli-mvp
Context: Final first-MVP packaging and certification round for ai-music-to-sheet. It closes only the documented CLI delivery and clean-tree proof gaps after the certified clean monophonic MP3/MP4, beat-aware MusicXML, EvaluationReport, and target-instrument arrangement rounds; mixed/polyphonic recordings, stem separation, YouTube ingestion, GUI/web UI, PDF/TAB rendering, manual correction, rich arrangement optimization, and multi-instrument orchestration remain outside this MVP.

## INT-1: One documented CLI entry point works
- intent: A user can follow the repository documentation from a clean checkout and invoke one command-line entry point with a real local MP3 or MP4 input plus an output directory, without manually importing Python modules.
- observable: The documented MP3 and MP4 commands run through the public CLI surface, write their output bundle into the requested directory, print machine-readable job status, and use exit code 0 only for accepted successful output.
- user_visible: yes
- sensitivity: core-promise

## INT-2: Accepted output bundle is complete
- intent: A supported clean single-melody run delivers the first-MVP artifacts needed to inspect and reuse the result.
- observable: The accepted output directory contains a parseable MusicXML artifact, a machine-readable result manifest, a machine-readable EvaluationReport, source and timing traceability artifacts, and, when a supported target instrument is requested, target-profile and arranged-score artifacts with target-instrument MusicXML.
- user_visible: yes
- sensitivity: core-promise

## INT-3: Non-accepted paths fail clearly
- intent: Inputs or environments outside the first-MVP support envelope are not mistaken for successful sheet-music delivery.
- observable: Invalid files, missing media dependencies, unsupported media formats, unsupported musical input, low-confidence output, unsupported target profiles, and unarrangeable target requests exit non-zero through the CLI and expose concise actionable diagnostics with REVIEW or FAIL status and NOT_ACCEPTED result state rather than ACCEPTED.
- user_visible: yes
- sensitivity: core-promise

## INT-4: README describes the usable MVP
- intent: The repository documentation tells users how to install, run, inspect, and interpret the first CLI MVP without relying on internal Reviewspec artifacts.
- observable: README documents prerequisites, setup, exact MP3 and MP4 CLI commands, target-instrument usage, output files, ACCEPTED/REVIEW/FAIL interpretation, troubleshooting for common failures, and explicit first-MVP limitations.
- user_visible: yes
- sensitivity: core-promise

## INT-5: Certification evidence is clean-tree reproducible
- intent: The first CLI MVP can be independently certified against the exact reviewed repository state without hidden local artifacts.
- observable: The final review records the exact commit and shows the complete deterministic test suite, all Reviewspec spec validators, compile check, registry build, and real ffmpeg/ffprobe MP3 plus MP4 CLI smoke path passing from a clean committed tree with no required untracked fixtures, caches, or alternate worktree.
- user_visible: no
- sensitivity: core-promise
