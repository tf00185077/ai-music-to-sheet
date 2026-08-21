import json
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from test_first_verified_monophonic_score import PITCH_STEPS, transcode, write_wave


BEAT_AWARE_MELODY = [
    {
        "pitch": 60,
        "onset": 0.0,
        "offset": 0.5,
        "duration": 0.5,
        "measure": 1,
        "beat": 1.0,
        "duration_beats": 1.0,
        "notated_duration": "quarter",
    },
    {
        "pitch": 62,
        "onset": 0.5,
        "offset": 1.0,
        "duration": 0.5,
        "measure": 1,
        "beat": 2.0,
        "duration_beats": 1.0,
        "notated_duration": "quarter",
    },
    {
        "pitch": 64,
        "onset": 1.0,
        "offset": 1.5,
        "duration": 0.5,
        "measure": 1,
        "beat": 3.0,
        "duration_beats": 1.0,
        "notated_duration": "quarter",
    },
    {
        "pitch": 65,
        "onset": 1.5,
        "offset": 2.0,
        "duration": 0.5,
        "measure": 1,
        "beat": 4.0,
        "duration_beats": 1.0,
        "notated_duration": "quarter",
    },
]

UNQUANTIZABLE_MELODY = [
    {"pitch": 60, "onset": 0.0, "offset": 0.5},
    {"pitch": 62, "onset": 0.5, "offset": 0.84},
    {"pitch": 64, "onset": 0.84, "offset": 1.5},
]


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def build_media_fixture(directory, name, notes, suffix=".mp3"):
    wav_path = directory / f"{name}.wav"
    media_path = directory / f"{name}{suffix}"
    write_wave(wav_path, notes)
    transcode(wav_path, media_path)
    return media_path


def musicxml_pitched_notes(path):
    root = ET.parse(path).getroot()
    parsed = []
    for measure in root.findall("./part/measure"):
        measure_number = int(measure.attrib["number"])
        for note in measure.findall("./note"):
            pitch = note.find("pitch")
            if pitch is None:
                continue
            step = pitch.findtext("step")
            octave = int(pitch.findtext("octave"))
            alter = int(pitch.findtext("alter", default="0"))
            parsed.append(
                {
                    "measure": measure_number,
                    "pitch": (octave + 1) * 12 + PITCH_STEPS[step] + alter,
                    "duration": int(note.findtext("duration")),
                    "type": note.findtext("type"),
                }
            )
    return parsed


class BeatAwareSingleMelodyScoreTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)

    def tearDown(self):
        self.tempdir.cleanup()

    def test_int1_time_map_exposes_reversible_musical_time(self):
        from ai_music_to_sheet.pipeline import process_media_file

        media_path = build_media_fixture(self.root, "beat-aware", BEAT_AWARE_MELODY)
        result = process_media_file(media_path, self.root / "out", reference_notes=BEAT_AWARE_MELODY)

        self.assertEqual(result["job_state"], "COMPLETED", result)
        time_map = read_json(result["artifacts"]["time_map"])
        note_events = read_json(result["artifacts"]["note_events"])

        self.assertEqual(time_map["job_id"], result["job_id"])
        self.assertEqual(time_map["source_id"], result["source"]["source_id"])
        self.assertEqual(time_map["tempo"]["bpm"], 120.0)
        self.assertEqual(time_map["time_signature"], {"beats_per_measure": 4, "beat_unit": 4})
        self.assertEqual(time_map["support"]["mode"], "deterministic-simple-meter")
        self.assertGreaterEqual(len(time_map["anchors"]), 1)
        self.assertEqual(
            [mapping["note_event_id"] for mapping in time_map["note_mappings"]],
            [note["id"] for note in note_events["notes"]],
        )
        for mapping in time_map["note_mappings"]:
            self.assertLessEqual(abs(mapping["onset_round_trip_delta_seconds"]), 0.001, mapping)

    def test_int2_score_ir_preserves_traceable_quantized_single_voice_notes(self):
        from ai_music_to_sheet.pipeline import process_media_file

        media_path = build_media_fixture(self.root, "score-ir", BEAT_AWARE_MELODY)
        result = process_media_file(media_path, self.root / "out", reference_notes=BEAT_AWARE_MELODY)
        note_events = read_json(result["artifacts"]["note_events"])
        score_ir = read_json(result["artifacts"]["score_ir"])

        score_notes = score_ir["parts"][0]["notes"]
        self.assertEqual([note["pitch"] for note in score_notes], [note["pitch"] for note in note_events["notes"]])
        self.assertEqual(
            [note["source_note_event_id"] for note in score_notes],
            [note["id"] for note in note_events["notes"]],
        )
        self.assertEqual([(note["measure"], note["beat"]) for note in score_notes], [(1, 1.0), (1, 2.0), (1, 3.0), (1, 4.0)])
        self.assertEqual([note["notated_duration"]["name"] for note in score_notes], ["quarter"] * 4)
        for previous, current in zip(score_notes, score_notes[1:]):
            self.assertLessEqual(previous["absolute_beat"] + previous["duration_beats"], current["absolute_beat"])

    def test_int3_musicxml_measure_structure_matches_score_ir(self):
        from ai_music_to_sheet.pipeline import process_media_file

        media_path = build_media_fixture(self.root, "musicxml", BEAT_AWARE_MELODY)
        result = process_media_file(media_path, self.root / "out", reference_notes=BEAT_AWARE_MELODY)
        score_ir = read_json(result["artifacts"]["score_ir"])
        root = ET.parse(result["artifacts"]["musicxml"]).getroot()

        time = root.find("./part/measure/attributes/time")
        self.assertEqual(time.findtext("beats"), "4")
        self.assertEqual(time.findtext("beat-type"), "4")
        self.assertEqual(len(root.findall("./part")), 1)
        self.assertEqual([measure.attrib["number"] for measure in root.findall("./part/measure")], ["1"])

        xml_notes = musicxml_pitched_notes(result["artifacts"]["musicxml"])
        score_notes = score_ir["parts"][0]["notes"]
        self.assertEqual([note["pitch"] for note in xml_notes], [note["pitch"] for note in score_notes])
        self.assertEqual([note["measure"] for note in xml_notes], [note["measure"] for note in score_notes])
        self.assertEqual([note["duration"] for note in xml_notes], [note["notated_duration"]["divisions"] for note in score_notes])
        self.assertEqual([note["type"] for note in xml_notes], [note["notated_duration"]["name"] for note in score_notes])

    def test_int4_evaluation_report_scores_timing_and_cites_artifact_versions(self):
        from ai_music_to_sheet.evaluation import run_evaluation_corpus

        mp3_path = build_media_fixture(self.root, "corpus-mp3", BEAT_AWARE_MELODY, ".mp3")
        mp4_path = build_media_fixture(self.root, "corpus-mp4", BEAT_AWARE_MELODY, ".mp4")
        report = run_evaluation_corpus(
            [
                {
                    "name": "beat-aware-mp3",
                    "media_path": str(mp3_path),
                    "reference_notes": BEAT_AWARE_MELODY,
                    "reference_version": "beat-aware-reference-v1",
                },
                {
                    "name": "beat-aware-mp4",
                    "media_path": str(mp4_path),
                    "reference_notes": BEAT_AWARE_MELODY,
                    "reference_version": "beat-aware-reference-v1",
                },
            ],
            self.root / "corpus",
        )

        self.assertEqual(report["overall_status"], "PASS", report)
        self.assertEqual([case["case_name"] for case in report["cases"]], ["beat-aware-mp3", "beat-aware-mp4"])
        for case in report["cases"]:
            self.assertEqual(case["status"], "PASS", case)
            self.assertIn("time_map", case["artifact_versions"])
            self.assertIn("score_ir", case["artifact_versions"])
            self.assertGreaterEqual(case["metrics"]["beat_position_accuracy"], 0.95)
            self.assertGreaterEqual(case["metrics"]["notated_duration_accuracy"], 0.95)

    def test_int5_unquantizable_timing_is_not_auto_accepted(self):
        from ai_music_to_sheet.pipeline import process_media_file

        media_path = build_media_fixture(self.root, "unquantizable", UNQUANTIZABLE_MELODY)
        result = process_media_file(media_path, self.root / "out")

        self.assertIn(result["job_state"], {"REVIEW", "FAIL"}, result)
        self.assertIn(result["quality_status"], {"REVIEW", "FAIL"}, result)
        self.assertEqual(result["acceptance"], "NOT_ACCEPTED", result)
        self.assertIn(result["reason"]["category"], {"TIMING", "TIMEMAP", "QUANTIZATION"}, result)
