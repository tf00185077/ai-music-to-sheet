from __future__ import annotations

import json
import math
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import wave
import xml.etree.ElementTree as ET
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SAMPLE_RATE = 16_000
MELODY = [
    {"pitch": 60, "onset": 0.0, "offset": 0.5},
    {"pitch": 62, "onset": 0.5, "offset": 1.0},
    {"pitch": 64, "onset": 1.0, "offset": 1.5},
    {"pitch": 65, "onset": 1.5, "offset": 2.0},
]


def main() -> int:
    try:
        summary = run_smoke()
    except Exception as error:
        print(
            json.dumps(
                {
                    "status": "FAIL",
                    "entrypoint": "python -m ai_music_to_sheet",
                    "error": str(error) or error.__class__.__name__,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 1

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


def run_smoke():
    require_media_tools()
    scratch_parent = Path(os.environ.get("PAPERCLIP_RUN_SCRATCH_DIR") or tempfile.gettempdir())
    scratch_parent.mkdir(parents=True, exist_ok=True)
    root = Path(tempfile.mkdtemp(prefix="ai-music-cli-smoke-", dir=str(scratch_parent)))
    cases = []
    for suffix, input_format in [(".mp3", "MP3"), (".mp4", "MP4")]:
        media_path = build_media_fixture(root, suffix)
        output_dir = root / f"out-{input_format.lower()}"
        command = [
            sys.executable,
            "-m",
            "ai_music_to_sheet",
            str(media_path),
            str(output_dir),
        ]
        completed = subprocess.run(command, cwd=REPO_ROOT, text=True, capture_output=True)
        payload = json.loads(completed.stdout)
        if completed.returncode != 0:
            raise RuntimeError(f"{input_format} CLI smoke returned {completed.returncode}: {payload}")
        if payload.get("acceptance") != "ACCEPTED":
            raise RuntimeError(f"{input_format} CLI smoke was not accepted: {payload}")
        musicxml = Path(payload["artifacts"]["musicxml"])
        evaluation_report = Path(payload["artifacts"]["evaluation_report"])
        ET.parse(musicxml)
        if not evaluation_report.exists():
            raise RuntimeError(f"{input_format} CLI smoke did not write evaluation_report.json")
        cases.append(
            {
                "format": input_format,
                "command": " ".join(["python", "-m", "ai_music_to_sheet", str(media_path), str(output_dir)]),
                "returncode": completed.returncode,
                "acceptance": payload["acceptance"],
                "job_state": payload["job_state"],
                "quality_status": payload["quality_status"],
                "musicxml": str(musicxml),
                "evaluation_report": str(evaluation_report),
                "result": payload["artifacts"]["result"],
            }
        )
    return {
        "status": "PASS",
        "entrypoint": "python -m ai_music_to_sheet",
        "workspace": str(root),
        "cases": cases,
    }


def require_media_tools() -> None:
    missing = [tool for tool in ["ffmpeg", "ffprobe"] if not shutil.which(tool)]
    if missing:
        raise RuntimeError(f"Missing required media tools: {', '.join(missing)}")


def build_media_fixture(directory: Path, suffix: str) -> Path:
    wav_path = directory / f"melody{suffix}.wav"
    media_path = directory / f"melody{suffix}"
    write_wave(wav_path, MELODY)
    transcode(wav_path, media_path)
    return media_path


def write_wave(path: Path, notes) -> None:
    total_duration = max(note["offset"] for note in notes)
    frames = []
    for index in range(int(total_duration * SAMPLE_RATE)):
        time = index / SAMPLE_RATE
        sample = 0.0
        for note in notes:
            if note["onset"] <= time < note["offset"]:
                sample += 0.65 * math.sin(2 * math.pi * midi_frequency(note["pitch"]) * time)
        frames.append(max(-0.95, min(0.95, sample)))

    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(SAMPLE_RATE)
        wav.writeframes(b"".join(struct.pack("<h", int(sample * 32767)) for sample in frames))


def transcode(wav_path: Path, target_path: Path) -> None:
    command = [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(wav_path),
    ]
    if target_path.suffix == ".mp4":
        command += ["-c:a", "aac", "-movflags", "+faststart"]
    elif target_path.suffix == ".mp3":
        command += ["-c:a", "libmp3lame", "-b:a", "128k"]
    command.append(str(target_path))
    completed = subprocess.run(command, text=True, capture_output=True)
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or f"ffmpeg failed for {target_path.suffix}")


def midi_frequency(pitch: int) -> float:
    return 440.0 * (2 ** ((pitch - 69) / 12))


if __name__ == "__main__":
    sys.exit(main())
