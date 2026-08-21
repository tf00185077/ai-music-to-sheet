import json
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from test_beat_aware_single_melody_score import BEAT_AWARE_MELODY, build_media_fixture, musicxml_pitched_notes


TARGET_PROFILE_ID = "beginner-soprano-recorder"
ARRANGEABLE_MELODY = BEAT_AWARE_MELODY
PER_NOTE_WRAP_ONLY_MELODY = [
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
        "pitch": 84,
        "onset": 0.5,
        "offset": 1.0,
        "duration": 0.5,
        "measure": 1,
        "beat": 2.0,
        "duration_beats": 1.0,
        "notated_duration": "quarter",
    },
]


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def musicxml_part_name(path):
    root = ET.parse(path).getroot()
    return root.findtext("./part-list/score-part/part-name")


class TargetInstrumentSingleMelodyArrangementTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)

    def tearDown(self):
        self.tempdir.cleanup()

    def test_int1_supported_target_request_delivers_traceable_arranged_score(self):
        from ai_music_to_sheet.pipeline import process_media_file

        media_path = build_media_fixture(self.root, "target-request", ARRANGEABLE_MELODY)
        result = process_media_file(
            media_path,
            self.root / "out",
            reference_notes=ARRANGEABLE_MELODY,
            target_profile_id=TARGET_PROFILE_ID,
        )

        self.assertEqual(result["job_state"], "COMPLETED", result)
        self.assertEqual(result["quality_status"], "PASS", result)
        self.assertEqual(result["acceptance"], "ACCEPTED", result)
        self.assertEqual(result["target_profile"]["id"], TARGET_PROFILE_ID)
        self.assertEqual(result["target_profile"]["pitch_domain"], "non_transposing_sounding_range_only")
        self.assertIn("arranged_score", result["artifacts"])
        self.assertIn("musicxml", result["artifacts"])

        arranged_score = read_json(result["artifacts"]["arranged_score"])
        score_ir = read_json(result["artifacts"]["score_ir"])
        time_map = read_json(result["artifacts"]["time_map"])

        self.assertEqual(arranged_score["schema_version"], "arranged-score/v1")
        self.assertEqual(arranged_score["job_id"], result["job_id"])
        self.assertEqual(arranged_score["target_profile"]["id"], TARGET_PROFILE_ID)
        self.assertEqual(arranged_score["target_profile"]["version"], result["target_profile"]["version"])
        self.assertEqual(arranged_score["source"]["job_id"], result["job_id"])
        self.assertEqual(arranged_score["source"]["source_id"], result["source"]["source_id"])
        self.assertEqual(arranged_score["source"]["source_path"], result["source"]["source_path"])
        self.assertEqual(arranged_score["source"]["score_ir_version"], score_ir["generator_version"])
        self.assertEqual(arranged_score["source"]["time_map_version"], time_map["generator_version"])
        self.assertEqual(arranged_score["source"]["score_ir_artifact"], result["artifacts"]["score_ir"])
        self.assertEqual(arranged_score["source"]["time_map_artifact"], result["artifacts"]["time_map"])

    def test_int2_arranged_notes_fit_profile_and_preserve_source_rhythm_identity(self):
        from ai_music_to_sheet.pipeline import process_media_file

        media_path = build_media_fixture(self.root, "profile-fit", ARRANGEABLE_MELODY)
        result = process_media_file(
            media_path,
            self.root / "out",
            reference_notes=ARRANGEABLE_MELODY,
            target_profile_id=TARGET_PROFILE_ID,
        )
        score_ir = read_json(result["artifacts"]["score_ir"])
        arranged_score = read_json(result["artifacts"]["arranged_score"])

        source_notes = score_ir["parts"][0]["notes"]
        arranged_notes = arranged_score["parts"][0]["notes"]
        profile_range = arranged_score["target_profile"]["sounded_midi_range"]
        min_pitch = int(profile_range["min"])
        max_pitch = int(profile_range["max"])

        self.assertEqual([note["pitch"] for note in source_notes], [60, 62, 64, 65])
        self.assertEqual(arranged_score["arrangement"]["global_octave_shift"], 1)
        self.assertEqual(arranged_score["arrangement"]["semitones"], 12)
        self.assertEqual(len(arranged_notes), len(source_notes))
        for source_note, arranged_note in zip(source_notes, arranged_notes):
            self.assertEqual(arranged_note["source_score_note_id"], source_note["id"])
            self.assertEqual(arranged_note["source_note_event_id"], source_note["source_note_event_id"])
            self.assertEqual(arranged_note["measure"], source_note["measure"])
            self.assertEqual(arranged_note["beat"], source_note["beat"])
            self.assertEqual(arranged_note["absolute_beat"], source_note["absolute_beat"])
            self.assertEqual(arranged_note["duration_beats"], source_note["duration_beats"])
            self.assertEqual(arranged_note["notated_duration"], source_note["notated_duration"])
            self.assertEqual(arranged_note["pitch"], source_note["pitch"] + 12)
            self.assertEqual(
                arranged_note["pitch_transformation"],
                {
                    "type": "global_octave_shift",
                    "global_octave_shift": 1,
                    "semitones": 12,
                    "source_pitch": source_note["pitch"],
                    "target_pitch": source_note["pitch"] + 12,
                },
            )
            self.assertGreaterEqual(arranged_note["pitch"], min_pitch)
            self.assertLessEqual(arranged_note["pitch"], max_pitch)

    def test_int3_musicxml_presents_requested_part_and_matches_arranged_score(self):
        from ai_music_to_sheet.pipeline import process_media_file

        media_path = build_media_fixture(self.root, "target-musicxml", ARRANGEABLE_MELODY)
        result = process_media_file(
            media_path,
            self.root / "out",
            reference_notes=ARRANGEABLE_MELODY,
            target_profile_id=TARGET_PROFILE_ID,
        )
        arranged_score = read_json(result["artifacts"]["arranged_score"])
        arranged_notes = arranged_score["parts"][0]["notes"]
        xml_notes = musicxml_pitched_notes(result["artifacts"]["musicxml"])

        self.assertEqual(musicxml_part_name(result["artifacts"]["musicxml"]), "Beginner Soprano Recorder")
        self.assertEqual(len(xml_notes), len(arranged_notes))
        self.assertEqual([note["pitch"] for note in xml_notes], [note["pitch"] for note in arranged_notes])
        self.assertEqual([note["measure"] for note in xml_notes], [note["measure"] for note in arranged_notes])
        self.assertEqual(
            [note["duration"] for note in xml_notes],
            [note["notated_duration"]["divisions"] for note in arranged_notes],
        )
        self.assertEqual([note["type"] for note in xml_notes], [note["notated_duration"]["name"] for note in arranged_notes])

    def test_int4_unsupported_and_unarrangeable_target_requests_are_not_accepted(self):
        from ai_music_to_sheet.pipeline import process_media_file

        supported_media = build_media_fixture(self.root, "unsupported-profile", ARRANGEABLE_MELODY)
        unsupported = process_media_file(
            supported_media,
            self.root / "unsupported-out",
            target_profile_id="transposing-b-flat-clarinet",
        )
        self.assertIn(unsupported["job_state"], {"REVIEW", "FAIL"}, unsupported)
        self.assertEqual(unsupported["acceptance"], "NOT_ACCEPTED", unsupported)
        self.assertEqual(unsupported["reason"]["category"], "INSTRUMENT_PROFILE", unsupported)
        self.assertEqual(unsupported["reason"]["stage"], "instrument_profile", unsupported)
        self.assertNotIn("arranged_score", unsupported["artifacts"])
        self.assertNotIn("musicxml", unsupported["artifacts"])

        wrap_only_media = build_media_fixture(self.root, "wrap-only", PER_NOTE_WRAP_ONLY_MELODY)
        unarrangeable = process_media_file(
            wrap_only_media,
            self.root / "wrap-only-out",
            reference_notes=PER_NOTE_WRAP_ONLY_MELODY,
            target_profile_id=TARGET_PROFILE_ID,
        )
        self.assertIn(unarrangeable["job_state"], {"REVIEW", "FAIL"}, unarrangeable)
        self.assertEqual(unarrangeable["acceptance"], "NOT_ACCEPTED", unarrangeable)
        self.assertEqual(unarrangeable["reason"]["category"], "ARRANGEMENT_RANGE", unarrangeable)
        self.assertEqual(unarrangeable["reason"]["stage"], "arrangement", unarrangeable)
        self.assertNotIn("arranged_score", unarrangeable["artifacts"])
        self.assertNotIn("musicxml", unarrangeable["artifacts"])

    def test_int5_evaluation_reports_arrangement_quality_and_artifact_versions(self):
        from ai_music_to_sheet.evaluation import run_evaluation_corpus

        mp3_path = build_media_fixture(self.root, "arranged-corpus-mp3", ARRANGEABLE_MELODY, ".mp3")
        mp4_path = build_media_fixture(self.root, "arranged-corpus-mp4", ARRANGEABLE_MELODY, ".mp4")
        report = run_evaluation_corpus(
            [
                {
                    "name": "arranged-mp3",
                    "media_path": str(mp3_path),
                    "reference_notes": ARRANGEABLE_MELODY,
                    "reference_version": "target-arrangement-reference-v1",
                    "target_profile_id": TARGET_PROFILE_ID,
                },
                {
                    "name": "arranged-mp4",
                    "media_path": str(mp4_path),
                    "reference_notes": ARRANGEABLE_MELODY,
                    "reference_version": "target-arrangement-reference-v1",
                    "target_profile_id": TARGET_PROFILE_ID,
                },
            ],
            self.root / "corpus",
        )

        self.assertEqual(report["overall_status"], "PASS", report)
        self.assertEqual([case["case_name"] for case in report["cases"]], ["arranged-mp3", "arranged-mp4"])
        for case in report["cases"]:
            self.assertEqual(case["status"], "PASS", case)
            self.assertEqual(case["arrangement"]["status"], "PASS", case)
            self.assertEqual(case["arrangement"]["target_profile"]["id"], TARGET_PROFILE_ID)
            self.assertEqual(case["arrangement"]["range_fit"]["status"], "PASS")
            self.assertEqual(case["arrangement"]["range_fit"]["out_of_range_notes"], [])
            self.assertEqual(case["arrangement"]["rhythm_preservation"]["status"], "PASS")
            self.assertEqual(case["arrangement"]["rhythm_preservation"]["mismatches"], [])
            for artifact_name in ["source", "time_map", "score_ir", "target_profile", "arranged_score", "musicxml"]:
                self.assertIn(artifact_name, case["artifact_versions"])
                self.assertTrue(case["artifact_versions"][artifact_name])
