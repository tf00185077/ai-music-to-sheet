from __future__ import annotations

import hashlib
import json
import math
import random
import struct
import sys
import wave
from pathlib import Path
from typing import Any, Dict, List, Sequence


SAMPLE_RATE = 8000
DURATION_SECONDS = 0.25
FRAME_COUNT = int(SAMPLE_RATE * DURATION_SECONDS)


def _tone(frequency: float, amplitude: float = 0.5) -> List[float]:
    return [amplitude * math.sin(2 * math.pi * frequency * index / SAMPLE_RATE) for index in range(FRAME_COUNT)]


def _clicks(amplitude: float = 0.8, partial: bool = False) -> List[float]:
    values = [0.0] * FRAME_COUNT
    positions = (0, FRAME_COUNT // 2) if not partial else (0,)
    for position in positions:
        for offset in range(24):
            if position + offset < FRAME_COUNT:
                values[position + offset] = amplitude * (1 - offset / 24.0)
    return values


def _noise(amplitude: float = 0.25) -> List[float]:
    randomizer = random.Random(20260824)
    return [amplitude * (randomizer.random() * 2 - 1) for _ in range(FRAME_COUNT)]


def _mix(*signals: Sequence[float]) -> List[float]:
    return [max(-1.0, min(1.0, sum(signal[index] for signal in signals))) for index in range(FRAME_COUNT)]


def _write_wave(path: Path, samples: Sequence[float]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(SAMPLE_RATE)
        frames = b"".join(struct.pack("<h", int(max(-1.0, min(1.0, value)) * 32767)) for value in samples)
        handle.writeframes(frames)


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def generate(root: Path) -> None:
    root = Path(root)
    audio = {
        "exact-synthetic": _tone(440.0),
        "rendered-events": _mix(_tone(261.63, 0.35), _clicks(0.25)),
        "isolated-drums": _mix(_clicks(0.85), _noise(0.08)),
        "isolated-piano": _mix(_tone(261.63, 0.4), _tone(523.25, 0.1)),
        "isolated-guitar": _mix(_tone(329.63, 0.35), _tone(659.25, 0.08)),
        "annotated-mix": _mix(_clicks(0.3), _tone(261.63, 0.2), _tone(329.63, 0.18)),
        "absent-target": _mix(_tone(261.63, 0.3), _tone(329.63, 0.2)),
        "low-volume": _mix(_tone(261.63, 0.35), _clicks(0.01)),
        "partial-presence": _mix(_tone(261.63, 0.3), _clicks(0.3, partial=True)),
        "masking": _mix(_tone(110.0, 0.8), _clicks(0.08)),
    }
    truth: Dict[str, Dict[str, Any]] = {
        "exact-synthetic": {"waveform": "sine", "frequency_hz": 440.0, "amplitude": 0.5},
        "rendered-events": {"events": [{"onset_seconds": 0.0, "pitch": 60}, {"onset_seconds": 0.125, "pitch": 60}]},
        "isolated-drums": {"instrument": "drums", "events": [{"onset_seconds": 0.0, "class": "kick"}, {"onset_seconds": 0.125, "class": "kick"}]},
        "isolated-piano": {"instrument": "piano", "events": [{"onset_seconds": 0.0, "pitch": 60, "offset_seconds": 0.25}]},
        "isolated-guitar": {"instrument": "guitar", "events": [{"onset_seconds": 0.0, "pitch": 64, "offset_seconds": 0.25}]},
        "annotated-mix": {
            "beats": [0.0, 0.125],
            "downbeats": [0.0],
            "meter": {"numerator": 4, "denominator": 4},
            "sections": [{"label": "A", "start_seconds": 0.0, "end_seconds": 0.25}],
            "instrument_presence": {"drums": "present", "piano": "present", "guitar": "present"},
        },
        "absent-target": {"target": "drums", "presence": "absent"},
        "low-volume": {"target": "drums", "presence": "low_volume", "relative_amplitude": 0.01},
        "partial-presence": {"target": "drums", "presence": "partial_presence", "spans": [[0.0, 0.003]]},
        "masking": {"target": "drums", "presence": "masked", "masker": "bass_sine"},
    }
    categories = {
        "exact-synthetic": "exact_synthetic",
        "rendered-events": "rendered_events",
        "isolated-drums": "isolated_drums",
        "isolated-piano": "isolated_piano",
        "isolated-guitar": "isolated_guitar",
        "annotated-mix": "annotated_mix",
        "absent-target": "absent_target",
        "low-volume": "low_volume",
        "partial-presence": "partial_presence",
        "masking": "masking",
    }
    fixtures = []
    for name in categories:
        wave_path = root / "audio" / (name + ".wav")
        truth_path = root / "truth" / (name + ".json")
        _write_wave(wave_path, audio[name])
        _write_json(truth_path, truth[name])
        records = []
        for path in (wave_path, truth_path):
            records.append(
                {
                    "path": str(path.relative_to(root)),
                    "sha256": _sha256(path),
                    "bytes": path.stat().st_size,
                }
            )
        fixtures.append(
            {
                "fixture_id": "p0-%s-v1" % name,
                "category": categories[name],
                "dataset_version": "p0-fixtures/1.0.0",
                "annotation_version": "1.0.0",
                "license": {"spdx": "CC0-1.0", "owner": "ai-music-to-sheet project", "provenance": "deterministically generated in-repository"},
                "split": "transparent-validation",
                "purpose": "README P0 contract and evaluator validation only",
                "usage_restriction": "No real-song, unseen-song, separation, transcription, arrangement, or perceptual-quality claim",
                "ground_truth": {"path": "truth/%s.json" % name, "kind": categories[name]},
                "files": records,
            }
        )
    manifest = {
        "dataset_version": "p0-fixtures/1.0.0",
        "immutable": True,
        "generated_by": "p0.fixture_builder/1.0.0",
        "seed": 20260824,
        "conventions": {
            "time_unit": "seconds",
            "coordinate_origin": 0,
            "pitch_standard": "MIDI note 0-127, A4=440Hz",
            "instrument_taxonomy": "p0-instruments/1.0.0: drums,piano,guitar,other",
            "wave_format": {"sample_rate": SAMPLE_RATE, "channels": 1, "sample_format": "pcm_s16le"},
        },
        "fixtures": fixtures,
    }
    manifest_path = root / "manifest.json"
    _write_json(manifest_path, manifest)
    _write_json(
        root.parent / "manifest-lock.json",
        {
            "dataset_version": "p0-fixtures/1.0.0",
            "manifest_sha256": _sha256(manifest_path),
            "policy": "Changing any file or manifest under v1 requires a new dataset version and lock entry",
        },
    )


def main(argv: Sequence[str]) -> int:
    if len(argv) != 2:
        print("usage: generate-p0-fixtures OUTPUT_ROOT", file=sys.stderr)
        return 2
    generate(Path(argv[1]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
