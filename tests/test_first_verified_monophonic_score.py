import json
import math
import shutil
import struct
import subprocess
import tempfile
import unittest
import wave
import xml.etree.ElementTree as ET
from pathlib import Path


SAMPLE_RATE = 16_000
MELODY = [
    {"pitch": 60, "onset": 0.0, "offset": 0.42},
    {"pitch": 62, "onset": 0.42, "offset": 0.84},
    {"pitch": 64, "onset": 0.84, "offset": 1.26},
]
PITCH_STEPS = {
    "C": 0,
    "D": 2,
    "E": 4,
    "F": 5,
    "G": 7,
    "A": 9,
    "B": 11,
}


def require_ffmpeg():
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        raise AssertionError("ffmpeg and ffprobe are required for the media-boundary tests")


def midi_frequency(pitch):
    return 440.0 * (2 ** ((pitch - 69) / 12))


def write_wave(path, notes, *, secondary=None, amplitude=0.65):
    total_duration = max(note["offset"] for note in notes)
    frames = []
    for index in range(int(total_duration * SAMPLE_RATE)):
        time = index / SAMPLE_RATE
        sample = 0.0
        for note in notes:
            if note["onset"] <= time < note["offset"]:
                sample += amplitude * math.sin(2 * math.pi * midi_frequency(note["pitch"]) * time)
                if secondary:
                    sample += secondary["amplitude"] * math.sin(
                        2 * math.pi * midi_frequency(secondary["pitch"]) * time
                    )
        frames.append(max(-0.95, min(0.95, sample)))

    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(SAMPLE_RATE)
        wav.writeframes(b"".join(struct.pack("<h", int(sample * 32767)) for sample in frames))


def transcode(wav_path, target_path):
    require_ffmpeg()
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
    subprocess.run(command, check=True)


def build_media_fixture(directory, suffix, *, secondary=None):
    wav_path = directory / f"melody{suffix}.wav"
    media_path = directory / f"melody{suffix}"
    write_wave(wav_path, MELODY, secondary=secondary)
    transcode(wav_path, media_path)
    return media_path


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def musicxml_midi_pitches(path):
    root = ET.parse(path).getroot()
    pitches = []
    for note in root.findall(".//note"):
        pitch = note.find("pitch")
        if pitch is None:
            continue
        step = pitch.findtext("step")
        octave = int(pitch.findtext("octave"))
        alter = int(pitch.findtext("alter", default="0"))
        pitches.append((octave + 1) * 12 + PITCH_STEPS[step] + alter)
    return pitches


class FirstVerifiedMonophonicScoreTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)

    def tearDown(self):
        self.tempdir.cleanup()

    def test_supported_mp3_and_mp4_complete_from_public_entrypoint(self):
        from ai_music_to_sheet.pipeline import process_media_file

        for suffix, expected_format in [(".mp3", "MP3"), (".mp4", "MP4")]:
            media_path = build_media_fixture(self.root, suffix)
            output_dir = self.root / f"out-{expected_format.lower()}"

            result = process_media_file(media_path, output_dir, reference_notes=MELODY)

            self.assertEqual(result["job_state"], "COMPLETED", result)
            self.assertEqual(result["quality_status"], "PASS", result)
            self.assertEqual(result["acceptance"], "ACCEPTED", result)
            self.assertEqual(result["source"]["input_format"], expected_format)
            self.assertEqual(result["source"]["source_path"], str(media_path))
            for artifact_name in ["source", "canonical_audio", "note_events", "musicxml", "result"]:
                self.assertIn(artifact_name, result["artifacts"])
                self.assertTrue(Path(result["artifacts"][artifact_name]).exists())

    def test_note_events_are_ordered_traceable_and_non_overlapping(self):
        from ai_music_to_sheet.pipeline import process_media_file

        media_path = build_media_fixture(self.root, ".mp3")
        result = process_media_file(media_path, self.root / "out", reference_notes=MELODY)
        note_events = read_json(result["artifacts"]["note_events"])
        notes = note_events["notes"]

        self.assertEqual(note_events["job_id"], result["job_id"])
        self.assertEqual(note_events["source_id"], result["source"]["source_id"])
        self.assertEqual(note_events["input_format"], "MP3")
        self.assertEqual([note["pitch"] for note in notes], [60, 62, 64])
        self.assertEqual(notes, sorted(notes, key=lambda note: note["onset"]))
        for previous, current in zip(notes, notes[1:]):
            self.assertLessEqual(previous["offset"], current["onset"])
        for note in notes:
            self.assertGreater(note["offset"], note["onset"])
            self.assertAlmostEqual(note["duration"], note["offset"] - note["onset"], places=6)
            self.assertGreaterEqual(note["confidence"], 0.70)

    def test_musicxml_is_parseable_single_part_and_matches_note_events(self):
        from ai_music_to_sheet.pipeline import process_media_file

        media_path = build_media_fixture(self.root, ".mp3")
        result = process_media_file(media_path, self.root / "out", reference_notes=MELODY)
        note_events = read_json(result["artifacts"]["note_events"])
        root = ET.parse(result["artifacts"]["musicxml"]).getroot()

        self.assertEqual(root.tag, "score-partwise")
        self.assertEqual(len(root.findall("./part")), 1)
        self.assertEqual(
            musicxml_midi_pitches(result["artifacts"]["musicxml"]),
            [note["pitch"] for note in note_events["notes"]],
        )

    def test_fixed_evaluation_corpus_reports_versions_metrics_and_status(self):
        from ai_music_to_sheet.evaluation import run_evaluation_corpus

        mp3_path = build_media_fixture(self.root, ".mp3")
        mp4_path = build_media_fixture(self.root, ".mp4")
        report = run_evaluation_corpus(
            [
                {
                    "name": "clean-melody-mp3",
                    "media_path": str(mp3_path),
                    "reference_notes": MELODY,
                    "reference_version": "fixture-melody-v1",
                },
                {
                    "name": "clean-melody-mp4",
                    "media_path": str(mp4_path),
                    "reference_notes": MELODY,
                    "reference_version": "fixture-melody-v1",
                },
            ],
            self.root / "corpus",
        )

        self.assertEqual(report["overall_status"], "PASS", report)
        self.assertEqual([case["case_name"] for case in report["cases"]], ["clean-melody-mp3", "clean-melody-mp4"])
        self.assertEqual(report["artifact_versions"]["reference"], ["fixture-melody-v1"])
        for case in report["cases"]:
            self.assertEqual(case["status"], "PASS", case)
            self.assertIn("source", case["artifact_versions"])
            self.assertIn("note_events", case["artifact_versions"])
            self.assertIn("musicxml", case["artifact_versions"])
            for metric in ["pitch_accuracy", "onset_accuracy", "duration_accuracy", "offset_accuracy"]:
                self.assertIn(metric, case["metrics"])
                self.assertGreaterEqual(case["metrics"][metric], 0.95)

    def test_unsupported_and_low_confidence_results_are_not_auto_accepted(self):
        from ai_music_to_sheet.pipeline import process_media_file

        polyphonic_path = build_media_fixture(self.root, ".mp3", secondary={"pitch": 67, "amplitude": 0.70})
        polyphonic = process_media_file(polyphonic_path, self.root / "polyphonic-out")
        self.assertIn(polyphonic["job_state"], {"REVIEW", "FAIL"}, polyphonic)
        self.assertEqual(polyphonic["acceptance"], "NOT_ACCEPTED", polyphonic)
        self.assertEqual(polyphonic["reason"]["category"], "UNSUPPORTED_SCOPE", polyphonic)

        low_confidence_path = build_media_fixture(self.root, ".mp4", secondary={"pitch": 67, "amplitude": 0.45})
        low_confidence = process_media_file(low_confidence_path, self.root / "low-confidence-out")
        self.assertEqual(low_confidence["job_state"], "REVIEW", low_confidence)
        self.assertEqual(low_confidence["quality_status"], "REVIEW", low_confidence)
        self.assertEqual(low_confidence["acceptance"], "NOT_ACCEPTED", low_confidence)
        self.assertEqual(low_confidence["reason"]["category"], "TRANSCRIPTION_QUALITY", low_confidence)

    def test_self_consistent_shifted_notes_fail_ground_truth_scoring(self):
        from ai_music_to_sheet.evaluation import score_notes_against_reference

        shifted_notes = [
            {"pitch": note["pitch"], "onset": note["onset"] + 0.25, "offset": note["offset"] + 0.25}
            for note in MELODY
        ]
        report = score_notes_against_reference(
            predicted_notes=shifted_notes,
            reference_notes=MELODY,
            case_name="shifted-but-exportable",
            artifact_versions={"note_events": "shifted-fixture", "musicxml": "matching-shifted-fixture"},
        )

        self.assertEqual(report["status"], "FAIL", report)
        self.assertLess(report["metrics"]["onset_accuracy"], 0.95)
        self.assertLess(report["metrics"]["duration_accuracy"], 0.95)

