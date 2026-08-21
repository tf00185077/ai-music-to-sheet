from __future__ import annotations

import hashlib
import json
import math
import shutil
import struct
import subprocess
import wave
from pathlib import Path
from typing import Dict, List, Tuple

from .contracts import (
    CATEGORY_AUDIO_QUALITY,
    CATEGORY_MEDIA_DECODE,
    CATEGORY_UNSUPPORTED_FORMAT,
    PIPELINE_VERSION,
    PipelineError,
    STAGE_DECODE,
    STAGE_MEDIA,
    utc_now,
)


SUPPORTED_FORMATS = {
    ".mp3": "MP3",
    ".mp4": "MP4",
    ".m4a": "MP4",
}
TARGET_SAMPLE_RATE = 16_000


def inspect_source(media_path: Path, job_id: str) -> Dict[str, object]:
    media_path = Path(media_path)
    suffix = media_path.suffix.lower()
    input_format = SUPPORTED_FORMATS.get(suffix)
    if not input_format:
        raise PipelineError(
            CATEGORY_UNSUPPORTED_FORMAT,
            STAGE_MEDIA,
            f"Unsupported input format '{suffix}'. Supported formats are MP3 and MP4.",
        )
    if not media_path.exists() or not media_path.is_file():
        raise PipelineError(CATEGORY_MEDIA_DECODE, STAGE_MEDIA, f"Input file does not exist: {media_path}")
    if not shutil.which("ffprobe"):
        raise PipelineError(CATEGORY_MEDIA_DECODE, STAGE_MEDIA, "ffprobe is required to inspect media")

    digest = hashlib.sha256(media_path.read_bytes()).hexdigest()
    probe = _ffprobe(media_path)
    stream = _first_audio_stream(probe)
    return {
        "schema_version": "media-source/v1",
        "version": PIPELINE_VERSION,
        "created_at": utc_now(),
        "job_id": job_id,
        "source_id": digest[:16],
        "source_path": str(media_path),
        "input_format": input_format,
        "byte_size": media_path.stat().st_size,
        "sha256": digest,
        "container_format": probe.get("format", {}).get("format_name", ""),
        "audio_codec": stream.get("codec_name", ""),
        "duration_seconds": _float_or_none(probe.get("format", {}).get("duration")),
        "sample_rate": int(stream.get("sample_rate") or 0),
        "channels": int(stream.get("channels") or 0),
    }


def decode_to_canonical_wav(media_path: Path, output_dir: Path, source: Dict[str, object]) -> Dict[str, object]:
    if not shutil.which("ffmpeg"):
        raise PipelineError(CATEGORY_MEDIA_DECODE, STAGE_DECODE, "ffmpeg is required to decode media")

    wav_path = output_dir / "canonical.wav"
    command = [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(media_path),
        "-ac",
        "1",
        "-ar",
        str(TARGET_SAMPLE_RATE),
        "-f",
        "wav",
        str(wav_path),
    ]
    completed = subprocess.run(command, text=True, capture_output=True)
    if completed.returncode != 0:
        message = completed.stderr.strip() or "ffmpeg failed to decode media"
        raise PipelineError(CATEGORY_MEDIA_DECODE, STAGE_DECODE, message)

    samples, sample_rate = read_wav_samples(wav_path)
    if not samples:
        raise PipelineError(CATEGORY_AUDIO_QUALITY, STAGE_DECODE, "Decoded audio contained no samples")

    rms = math.sqrt(sum(sample * sample for sample in samples) / len(samples))
    peak = max(abs(sample) for sample in samples)
    duration = len(samples) / sample_rate
    silence = rms < 0.004 or peak < 0.01
    clipped = peak >= 0.995
    metadata = {
        "schema_version": "canonical-audio/v1",
        "version": PIPELINE_VERSION,
        "created_at": utc_now(),
        "job_id": source["job_id"],
        "source_id": source["source_id"],
        "input_format": source["input_format"],
        "wav_path": str(wav_path),
        "sample_rate": sample_rate,
        "channels": 1,
        "duration_seconds": round(duration, 6),
        "frame_count": len(samples),
        "rms": round(rms, 8),
        "peak": round(peak, 8),
        "silence": silence,
        "clipped": clipped,
    }
    if silence:
        raise PipelineError(CATEGORY_AUDIO_QUALITY, STAGE_DECODE, "Decoded audio is silent or too quiet")
    return metadata


def read_wav_samples(wav_path: Path) -> Tuple[List[float], int]:
    with wave.open(str(wav_path), "rb") as wav:
        channels = wav.getnchannels()
        sample_width = wav.getsampwidth()
        sample_rate = wav.getframerate()
        raw = wav.readframes(wav.getnframes())

    if sample_width != 2:
        raise PipelineError(CATEGORY_MEDIA_DECODE, STAGE_DECODE, "Canonical WAV must be 16-bit PCM")

    values = struct.unpack("<" + "h" * (len(raw) // 2), raw)
    if channels == 1:
        samples = [value / 32768.0 for value in values]
    else:
        samples = []
        for index in range(0, len(values), channels):
            samples.append(sum(values[index : index + channels]) / channels / 32768.0)
    return samples, sample_rate


def _ffprobe(media_path: Path) -> Dict[str, object]:
    command = [
        "ffprobe",
        "-v",
        "error",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        str(media_path),
    ]
    completed = subprocess.run(command, text=True, capture_output=True)
    if completed.returncode != 0:
        message = completed.stderr.strip() or "ffprobe could not read the media"
        raise PipelineError(CATEGORY_MEDIA_DECODE, STAGE_MEDIA, message)
    return json.loads(completed.stdout)


def _first_audio_stream(probe: Dict[str, object]) -> Dict[str, object]:
    for stream in probe.get("streams", []):
        if stream.get("codec_type") == "audio":
            return stream
    raise PipelineError(CATEGORY_MEDIA_DECODE, STAGE_MEDIA, "No audio stream found in media")


def _float_or_none(value):
    try:
        return round(float(value), 6)
    except (TypeError, ValueError):
        return None
