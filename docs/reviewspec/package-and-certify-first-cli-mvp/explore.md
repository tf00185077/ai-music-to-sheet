# Explore · package-and-certify-first-cli-mvp

## Real goal (not just the stated solution)

Close the first MVP as something a user can invoke and an independent reviewer can certify from a clean checkout. The prior certified rounds prove the core clean monophonic MP3/MP4 pipeline, beat-aware MusicXML, EvaluationReport, and one target-instrument arrangement path. They do not yet prove the product can be installed or run through one documented CLI command with real local media, clear exit semantics, README instructions, and a clean-tree smoke path that does not rely on untracked artifacts.

This is the final bounded first-MVP round after the target-instrument arrangement PASS. It should package and certify the existing supported scope, not add mixed recordings, stem separation, YouTube ingestion, GUI/web UI, PDF/TAB, manual correction, rich arrangement optimization, or multi-instrument orchestration.

No `docs/decisions/` directory exists. Current decision memory is README.md, the 2026-08-20 design document, research notes, `docs/reviewspec/REGISTRY.md`, and the certified review artifacts for `first-verified-monophonic-score`, `beat-aware-single-melody-score`, and `target-instrument-single-melody-arrangement`.

## Candidate directions (2-4, each with a one-line trade-off)

1. Harden the existing `python -m ai_music_to_sheet` CLI as the documented MVP entry point. Trade-off: smallest implementation surface, but it must still make success, REVIEW, FAIL, and diagnostics unambiguous for shell users.
2. Add packaging metadata and a console-script command while preserving module invocation. Trade-off: better user ergonomics and installability, but a new packaging file must not distract from the certification evidence.
3. Add a deterministic real-MP3/MP4 smoke harness plus README commands that generate or consume local media in a clean tree. Trade-off: directly proves the terminal contract, but the harness must avoid committing generated media or depending on another worktree.
4. Expand beyond CLI into upload UI, stem separation, or broader arrangements. Trade-off: user-visible ambition, but it violates the first-MVP terminal contract and should be rejected for this round.

## Integration points / hidden complexity noticed

- `ai_music_to_sheet/__main__.py` already exposes a module CLI with positional input/output and optional `--target-profile`, but README.md does not document installation, prerequisites, exact MP3/MP4 commands, output files, status interpretation, or first-MVP limitations.
- The current CLI returns exit code 0 for both `COMPLETED` and `REVIEW`; the terminal contract requires unsupported or uncertain output to fail non-zero rather than being silently accepted as success.
- `process_media_file()` writes `result.json`, `evaluation_report.json` only when reference notes are provided, and arrangement artifacts only when a target profile is requested. The final certification must distinguish normal user output from evaluation/smoke evidence.
- Existing tests generate real MP3/MP4 through ffmpeg/ffprobe and exercise the public Python pipeline, but the final package proof needs one documented command-line entry point and real ffmpeg/ffprobe MP3+MP4 smoke coverage from a clean committed tree.
- There is no packaging metadata file in the repository, so install/setup documentation either needs to document module execution from the repo or the build needs a minimal package entry point.
- The registry currently tracks 15 active certified intents. The final round must keep all of them passing while adding only the packaging/CLI/documentation certification intents.

## Open questions to resolve in phase 2

- Should the approved entry point be only `python -m ai_music_to_sheet`, or should the MVP also expose an installed console command?
- What shell exit semantics should represent `REVIEW`: non-zero because the artifact is not accepted, or zero because processing completed with a reviewable result?
- Should the final smoke evidence be a dedicated committed test, a documented smoke script/command, or both?
- How should the README describe EvaluationReport generation for ordinary user commands versus ground-truth smoke/corpus runs without implying arbitrary real-world transcription accuracy?
