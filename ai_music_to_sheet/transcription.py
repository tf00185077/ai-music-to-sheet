from __future__ import annotations

import math
from pathlib import Path
from typing import Dict, List

from .contracts import normalized_notes
from .media import read_wav_samples


MIDI_MIN = 48
MIDI_MAX = 84
FRAME_SECONDS = 0.080
HOP_SECONDS = 0.040
MIN_NOTE_SECONDS = 0.120
SILENCE_RMS = 0.010
POLYPHONY_RATIO_THRESHOLD = 0.72
CONFIDENCE_REVIEW_THRESHOLD = 0.70


def transcribe_monophonic_wav(wav_path: Path) -> Dict[str, object]:
    samples, sample_rate = read_wav_samples(Path(wav_path))
    frame_size = max(64, int(FRAME_SECONDS * sample_rate))
    hop_size = max(32, int(HOP_SECONDS * sample_rate))
    frames = _analyze_frames(samples, sample_rate, frame_size, hop_size)
    if not frames:
        return {
            "notes": [],
            "average_confidence": 0.0,
            "average_secondary_ratio": 1.0,
            "max_secondary_ratio": 0.0,
            "frame_count": 0,
        }

    _smooth_single_frame_jumps(frames)
    notes = _frames_to_notes(frames, len(samples) / sample_rate)
    if not notes:
        return {
            "notes": [],
            "average_confidence": 0.0,
            "average_secondary_ratio": 1.0,
            "max_secondary_ratio": max(frame["secondary_ratio"] for frame in frames),
            "frame_count": len(frames),
        }

    average_confidence = sum(note["confidence"] for note in notes) / len(notes)
    return {
        "notes": notes,
        "average_confidence": round(average_confidence, 6),
        "average_secondary_ratio": round(1.0 - average_confidence, 6),
        "max_secondary_ratio": round(max(frame["secondary_ratio"] for frame in frames), 6),
        "frame_count": len(frames),
    }


def _analyze_frames(samples: List[float], sample_rate: int, frame_size: int, hop_size: int) -> List[Dict[str, float]]:
    window = _hann_window(frame_size)
    candidates = [(pitch, _midi_frequency(pitch)) for pitch in range(MIDI_MIN, MIDI_MAX + 1)]
    frames = []
    for start in range(0, max(0, len(samples) - frame_size + 1), hop_size):
        frame = samples[start : start + frame_size]
        rms = math.sqrt(sum(sample * sample for sample in frame) / frame_size)
        if rms < SILENCE_RMS:
            continue
        windowed = [sample * window[index] for index, sample in enumerate(frame)]
        powers = [(_goertzel_power(windowed, sample_rate, frequency), pitch) for pitch, frequency in candidates]
        powers.sort(reverse=True)
        top_power, top_pitch = powers[0]
        second_power = _strongest_non_adjacent_power(powers, top_pitch)
        secondary_ratio = second_power / top_power if top_power > 0 else 1.0
        confidence = max(0.0, min(1.0, 1.0 - secondary_ratio))
        frames.append(
            {
                "start": start / sample_rate,
                "end": min((start + frame_size) / sample_rate, len(samples) / sample_rate),
                "pitch": int(top_pitch),
                "confidence": confidence,
                "secondary_ratio": secondary_ratio,
                "rms": rms,
            }
        )
    return frames


def _frames_to_notes(frames: List[Dict[str, float]], audio_duration: float) -> List[Dict[str, float]]:
    groups = []
    current = [frames[0]]
    for frame in frames[1:]:
        if int(frame["pitch"]) == int(current[-1]["pitch"]):
            current.append(frame)
        else:
            groups.append(current)
            current = [frame]
    groups.append(current)

    notes = []
    for group in groups:
        onset = group[0]["start"]
        offset = group[-1]["start"] + HOP_SECONDS
        duration = offset - onset
        if duration < MIN_NOTE_SECONDS:
            continue
        confidence = sum(frame["confidence"] for frame in group) / len(group)
        notes.append(
            {
                "pitch": int(round(sum(frame["pitch"] for frame in group) / len(group))),
                "onset": round(onset, 6),
                "offset": round(min(offset, audio_duration), 6),
                "duration": round(min(offset, audio_duration) - onset, 6),
                "confidence": round(confidence, 6),
            }
        )
    return normalized_notes(notes)


def _smooth_single_frame_jumps(frames: List[Dict[str, float]]) -> None:
    for index in range(1, len(frames) - 1):
        previous_pitch = int(frames[index - 1]["pitch"])
        next_pitch = int(frames[index + 1]["pitch"])
        if previous_pitch == next_pitch and int(frames[index]["pitch"]) != previous_pitch:
            frames[index]["pitch"] = previous_pitch
            frames[index]["confidence"] = min(frames[index]["confidence"], frames[index - 1]["confidence"], frames[index + 1]["confidence"])


def _strongest_non_adjacent_power(powers, top_pitch: int) -> float:
    for power, pitch in powers[1:]:
        if abs(int(pitch) - int(top_pitch)) > 1:
            return power
    return powers[1][0] if len(powers) > 1 else 0.0


def _midi_frequency(pitch: int) -> float:
    return 440.0 * (2 ** ((pitch - 69) / 12))


def _hann_window(size: int) -> List[float]:
    if size <= 1:
        return [1.0]
    return [0.5 - 0.5 * math.cos(2 * math.pi * index / (size - 1)) for index in range(size)]


def _goertzel_power(samples: List[float], sample_rate: int, frequency: float) -> float:
    normalized = frequency / sample_rate
    coeff = 2.0 * math.cos(2.0 * math.pi * normalized)
    previous = 0.0
    previous2 = 0.0
    for sample in samples:
        current = sample + coeff * previous - previous2
        previous2 = previous
        previous = current
    return previous2 * previous2 + previous * previous - coeff * previous * previous2
