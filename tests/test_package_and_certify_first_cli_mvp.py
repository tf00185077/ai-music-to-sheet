import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from test_beat_aware_single_melody_score import BEAT_AWARE_MELODY, build_media_fixture
from test_first_verified_monophonic_score import MELODY, transcode, write_wave
from test_target_instrument_single_melody_arrangement import (
    PER_NOTE_WRAP_ONLY_MELODY,
    TARGET_PROFILE_ID,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def run_cli(media_path, output_dir, *extra_args, env=None):
    command = [
        sys.executable,
        "-m",
        "ai_music_to_sheet",
        str(media_path),
        str(output_dir),
        *extra_args,
    ]
    completed = subprocess.run(
        command,
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        env=env,
    )
    payload = json.loads(completed.stdout)
    return completed, payload


class PackageAndCertifyFirstCliMvpTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)

    def tearDown(self):
        self.tempdir.cleanup()

    def test_int1_readme_mp3_and_mp4_commands_run_through_documented_cli(self):
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("python -m ai_music_to_sheet input.mp3 out/score-mp3", readme)
        self.assertIn("python -m ai_music_to_sheet input.mp4 out/score-mp4", readme)

        for suffix, expected_format in [(".mp3", "MP3"), (".mp4", "MP4")]:
            with self.subTest(suffix=suffix):
                media_path = build_media_fixture(self.root, f"documented{suffix}", BEAT_AWARE_MELODY, suffix)
                output_dir = self.root / f"out-{expected_format.lower()}"

                completed, payload = run_cli(media_path, output_dir)

                self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
                self.assertEqual(payload["job_state"], "COMPLETED", payload)
                self.assertEqual(payload["quality_status"], "PASS", payload)
                self.assertEqual(payload["acceptance"], "ACCEPTED", payload)
                self.assertEqual(payload["source"]["input_format"], expected_format, payload)
                self.assertEqual(read_json(output_dir / "result.json")["job_id"], payload["job_id"])

    def test_int2_accepted_cli_bundle_contains_parseable_traceable_artifacts(self):
        media_path = build_media_fixture(self.root, "accepted-bundle", BEAT_AWARE_MELODY, ".mp3")
        output_dir = self.root / "out"

        completed, payload = run_cli(media_path, output_dir, "--target-profile", TARGET_PROFILE_ID)

        self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
        self.assertEqual(payload["acceptance"], "ACCEPTED", payload)
        required = [
            "source",
            "canonical_audio",
            "note_events",
            "time_map",
            "score_ir",
            "musicxml",
            "evaluation_report",
            "target_profile",
            "arranged_score",
            "result",
        ]
        for artifact_name in required:
            with self.subTest(artifact_name=artifact_name):
                artifact_path = Path(payload["artifacts"][artifact_name])
                self.assertTrue(artifact_path.exists(), payload["artifacts"])
                self.assertTrue(str(artifact_path).startswith(str(output_dir.resolve())))

        ET.parse(payload["artifacts"]["musicxml"])
        evaluation = read_json(payload["artifacts"]["evaluation_report"])
        self.assertEqual(evaluation["schema_version"], "evaluation-report/v1", evaluation)
        self.assertEqual(evaluation["mode"], "runtime_validation", evaluation)
        self.assertFalse(evaluation["reference_available"], evaluation)
        self.assertNotIn("pitch_accuracy", evaluation.get("metrics", {}), evaluation)
        self.assertEqual(evaluation["status"], "PASS", evaluation)
        self.assertEqual(evaluation["artifact_versions"]["target_profile"], payload["target_profile"]["version"])
        self.assertIn("arranged_score", evaluation["artifact_versions"])

    def test_int3_non_accepted_cli_paths_exit_nonzero_with_machine_readable_diagnostics(self):
        cases = []
        unsupported_path = self.root / "melody.wav"
        write_wave(unsupported_path, MELODY)
        cases.append((unsupported_path, [], "UNSUPPORTED_FORMAT", "media"))

        low_confidence_wav = self.root / "low-confidence.wav"
        low_confidence_mp4 = self.root / "low-confidence.mp4"
        write_wave(low_confidence_wav, MELODY, secondary={"pitch": 67, "amplitude": 0.45})
        transcode(low_confidence_wav, low_confidence_mp4)
        cases.append((low_confidence_mp4, [], "TRANSCRIPTION_QUALITY", "transcription"))

        supported_media = build_media_fixture(self.root, "unsupported-profile", BEAT_AWARE_MELODY, ".mp3")
        cases.append(
            (
                supported_media,
                ["--target-profile", "transposing-b-flat-clarinet"],
                "INSTRUMENT_PROFILE",
                "instrument_profile",
            )
        )

        wrap_only_media = build_media_fixture(self.root, "wrap-only", PER_NOTE_WRAP_ONLY_MELODY, ".mp3")
        cases.append((wrap_only_media, ["--target-profile", TARGET_PROFILE_ID], "ARRANGEMENT_RANGE", "arrangement"))

        for media_path, extra_args, expected_category, expected_stage in cases:
            with self.subTest(expected_category=expected_category):
                completed, payload = run_cli(media_path, self.root / f"out-{expected_category}", *extra_args)

                self.assertNotEqual(completed.returncode, 0, payload)
                self.assertIn(payload["job_state"], {"REVIEW", "FAIL"}, payload)
                self.assertIn(payload["quality_status"], {"REVIEW", "FAIL"}, payload)
                self.assertEqual(payload["acceptance"], "NOT_ACCEPTED", payload)
                self.assertEqual(payload["reason"]["category"], expected_category, payload)
                self.assertEqual(payload["reason"]["stage"], expected_stage, payload)

        missing_dependency_env = os.environ.copy()
        missing_dependency_env["PATH"] = ""
        dependency_media = build_media_fixture(self.root, "missing-ffprobe", BEAT_AWARE_MELODY, ".mp3")
        completed, payload = run_cli(
            dependency_media,
            self.root / "out-missing-ffprobe",
            env=missing_dependency_env,
        )
        self.assertNotEqual(completed.returncode, 0, payload)
        self.assertEqual(payload["acceptance"], "NOT_ACCEPTED", payload)
        self.assertEqual(payload["reason"]["category"], "MEDIA_DECODE", payload)
        self.assertEqual(payload["reason"]["stage"], "media", payload)
        self.assertIn("ffprobe", payload["reason"]["message"])

    def test_int4_readme_documents_mvp_operation_statuses_and_limits(self):
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        required_fragments = [
            "ffmpeg",
            "ffprobe",
            "python -m pip install -e .",
            "python -m ai_music_to_sheet input.mp3 out/score-mp3",
            "python -m ai_music_to_sheet input.mp4 out/score-mp4",
            "--target-profile beginner-soprano-recorder",
            "result.json",
            "evaluation_report.json",
            "score.musicxml",
            "ACCEPTED",
            "REVIEW",
            "FAIL",
            "Exit code `0`",
            "mixed or polyphonic",
            "YouTube",
            "PDF",
            "TAB",
        ]
        for fragment in required_fragments:
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, readme)

    def test_int5_certification_smoke_support_runs_from_clean_checkout_inputs(self):
        smoke_script = REPO_ROOT / "scripts" / "smoke_cli_mvp.py"
        self.assertTrue(smoke_script.exists())
        self.assertTrue(shutil.which("ffmpeg"))
        self.assertTrue(shutil.which("ffprobe"))

        completed = subprocess.run(
            [sys.executable, str(smoke_script)],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["status"], "PASS", payload)
        self.assertEqual(payload["entrypoint"], "python -m ai_music_to_sheet", payload)
        self.assertEqual([case["format"] for case in payload["cases"]], ["MP3", "MP4"], payload)
        for case in payload["cases"]:
            self.assertEqual(case["acceptance"], "ACCEPTED", case)
            self.assertTrue(Path(case["musicxml"]).exists(), case)
            self.assertTrue(Path(case["evaluation_report"]).exists(), case)
