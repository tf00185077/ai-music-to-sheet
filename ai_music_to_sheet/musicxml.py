from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional

from .contracts import CATEGORY_MUSICXML_EXPORT, PipelineError, STAGE_MUSICXML


DIVISIONS = 1000
PITCH_CLASS_TO_STEP = {
    0: ("C", 0),
    1: ("C", 1),
    2: ("D", 0),
    3: ("D", 1),
    4: ("E", 0),
    5: ("F", 0),
    6: ("F", 1),
    7: ("G", 0),
    8: ("G", 1),
    9: ("A", 0),
    10: ("A", 1),
    11: ("B", 0),
}
STEP_TO_PITCH_CLASS = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def export_musicxml(
    note_events_artifact: Dict[str, object],
    output_path: Path,
    score_ir_artifact: Optional[Dict[str, object]] = None,
) -> Dict[str, object]:
    if score_ir_artifact is not None:
        return export_score_ir_musicxml(score_ir_artifact, output_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    notes = note_events_artifact["notes"]

    root = ET.Element("score-partwise", {"version": "3.1"})
    movement_title = ET.SubElement(root, "movement-title")
    movement_title.text = "First Verified Monophonic Score"
    identification = ET.SubElement(root, "identification")
    encoding = ET.SubElement(identification, "encoding")
    software = ET.SubElement(encoding, "software")
    software.text = str(note_events_artifact["generator_version"])

    part_list = ET.SubElement(root, "part-list")
    score_part = ET.SubElement(part_list, "score-part", {"id": "P1"})
    part_name = ET.SubElement(score_part, "part-name")
    part_name.text = str(part_ir["name"])

    part = ET.SubElement(root, "part", {"id": "P1"})
    measure = ET.SubElement(part, "measure", {"number": "1"})
    attributes = ET.SubElement(measure, "attributes")
    divisions = ET.SubElement(attributes, "divisions")
    divisions.text = str(DIVISIONS)
    key = ET.SubElement(attributes, "key")
    fifths = ET.SubElement(key, "fifths")
    fifths.text = "0"
    time = ET.SubElement(attributes, "time")
    beats = ET.SubElement(time, "beats")
    beats.text = "4"
    beat_type = ET.SubElement(time, "beat-type")
    beat_type.text = "4"
    clef = ET.SubElement(attributes, "clef")
    sign = ET.SubElement(clef, "sign")
    sign.text = "G"
    line = ET.SubElement(clef, "line")
    line.text = "2"

    for event in notes:
        note = ET.SubElement(measure, "note")
        pitch = ET.SubElement(note, "pitch")
        step, alter = _pitch_to_step(int(event["pitch"]))
        step_node = ET.SubElement(pitch, "step")
        step_node.text = step
        if alter:
            alter_node = ET.SubElement(pitch, "alter")
            alter_node.text = str(alter)
        octave = ET.SubElement(pitch, "octave")
        octave.text = str(int(event["pitch"]) // 12 - 1)
        duration = ET.SubElement(note, "duration")
        duration.text = str(max(1, int(round(float(event["duration"]) * DIVISIONS))))
        voice = ET.SubElement(note, "voice")
        voice.text = "1"
        note_type = ET.SubElement(note, "type")
        note_type.text = "quarter"

    tree = ET.ElementTree(root)
    tree.write(output_path, encoding="utf-8", xml_declaration=True)
    parsed_pitches = parse_musicxml_pitches(output_path)
    expected_pitches = [int(note["pitch"]) for note in notes]
    if parsed_pitches != expected_pitches:
        raise PipelineError(
            CATEGORY_MUSICXML_EXPORT,
            STAGE_MUSICXML,
            "MusicXML pitch sequence does not match note events",
        )
    return {
        "path": str(output_path),
        "part_count": 1,
        "note_count": len(parsed_pitches),
        "pitch_sequence": parsed_pitches,
    }


def export_score_ir_musicxml(score_ir_artifact: Dict[str, object], output_path: Path) -> Dict[str, object]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    part_ir = score_ir_artifact["parts"][0]
    notes = list(part_ir["notes"])
    time_signature = score_ir_artifact["time_signature"]

    root = ET.Element("score-partwise", {"version": "3.1"})
    movement_title = ET.SubElement(root, "movement-title")
    movement_title.text = "Beat-Aware Single Melody Score"
    identification = ET.SubElement(root, "identification")
    encoding = ET.SubElement(identification, "encoding")
    software = ET.SubElement(encoding, "software")
    software.text = str(score_ir_artifact["generator_version"])

    part_list = ET.SubElement(root, "part-list")
    score_part = ET.SubElement(part_list, "score-part", {"id": str(part_ir["id"])})
    part_name = ET.SubElement(score_part, "part-name")
    part_name.text = str(part_ir["name"])

    part = ET.SubElement(root, "part", {"id": str(part_ir["id"])})
    measures = part_ir.get("measures") or [{"number": note["measure"]} for note in notes]
    for measure_info in measures:
        measure_number = int(measure_info["number"])
        measure = ET.SubElement(part, "measure", {"number": str(measure_number)})
        if measure_number == 1:
            _write_attributes(measure, time_signature)

        measure_start = (measure_number - 1) * int(time_signature["beats_per_measure"])
        measure_end = measure_start + int(time_signature["beats_per_measure"])
        cursor = float(measure_start)
        measure_notes = sorted(
            [note for note in notes if int(note["measure"]) == measure_number],
            key=lambda note: float(note["absolute_beat"]),
        )
        for score_note in measure_notes:
            start = float(score_note["absolute_beat"])
            if start > cursor + 1e-6:
                _add_rest(measure, start - cursor)
            _add_pitched_note(measure, score_note)
            cursor = max(cursor, start + float(score_note["duration_beats"]))
        if cursor < measure_end - 1e-6:
            _add_rest(measure, measure_end - cursor)

    tree = ET.ElementTree(root)
    tree.write(output_path, encoding="utf-8", xml_declaration=True)

    parsed_notes = parse_musicxml_score_notes(output_path)
    expected_notes = [
        {
            "measure": int(note["measure"]),
            "pitch": int(note["pitch"]),
            "duration": int(note["notated_duration"]["divisions"]),
            "type": str(note["notated_duration"]["name"]),
        }
        for note in notes
    ]
    if parsed_notes != expected_notes:
        raise PipelineError(
            CATEGORY_MUSICXML_EXPORT,
            STAGE_MUSICXML,
            "MusicXML measure, pitch, or duration sequence does not match ScoreIR",
        )

    return {
        "path": str(output_path),
        "part_count": 1,
        "measure_count": len(measures),
        "note_count": len(parsed_notes),
        "pitch_sequence": [note["pitch"] for note in parsed_notes],
        "time_signature": time_signature,
    }


def export_arranged_score_musicxml(arranged_score_artifact: Dict[str, object], output_path: Path) -> Dict[str, object]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    part_ir = arranged_score_artifact["parts"][0]
    notes = list(part_ir["notes"])
    time_signature = arranged_score_artifact["time_signature"]
    profile = arranged_score_artifact["target_profile"]
    min_pitch = int(profile["sounded_midi_range"]["min"])
    max_pitch = int(profile["sounded_midi_range"]["max"])

    root = ET.Element("score-partwise", {"version": "3.1"})
    movement_title = ET.SubElement(root, "movement-title")
    movement_title.text = "Target Instrument Arrangement"
    identification = ET.SubElement(root, "identification")
    encoding = ET.SubElement(identification, "encoding")
    software = ET.SubElement(encoding, "software")
    software.text = str(arranged_score_artifact["generator_version"])

    part_list = ET.SubElement(root, "part-list")
    score_part = ET.SubElement(part_list, "score-part", {"id": str(part_ir["id"])})
    part_name = ET.SubElement(score_part, "part-name")
    part_name.text = str(part_ir["name"])

    part = ET.SubElement(root, "part", {"id": str(part_ir["id"])})
    measures = part_ir.get("measures") or [{"number": note["measure"]} for note in notes]
    for measure_info in measures:
        measure_number = int(measure_info["number"])
        measure = ET.SubElement(part, "measure", {"number": str(measure_number)})
        if measure_number == 1:
            _write_attributes(measure, time_signature)

        measure_start = (measure_number - 1) * int(time_signature["beats_per_measure"])
        measure_end = measure_start + int(time_signature["beats_per_measure"])
        cursor = float(measure_start)
        measure_notes = sorted(
            [note for note in notes if int(note["measure"]) == measure_number],
            key=lambda note: float(note["absolute_beat"]),
        )
        for arranged_note in measure_notes:
            start = float(arranged_note["absolute_beat"])
            if start > cursor + 1e-6:
                _add_rest(measure, start - cursor)
            _add_pitched_note(measure, arranged_note)
            cursor = max(cursor, start + float(arranged_note["duration_beats"]))
        if cursor < measure_end - 1e-6:
            _add_rest(measure, measure_end - cursor)

    tree = ET.ElementTree(root)
    tree.write(output_path, encoding="utf-8", xml_declaration=True)

    parsed_notes = parse_musicxml_score_notes(output_path)
    expected_notes = [
        {
            "measure": int(note["measure"]),
            "pitch": int(note["pitch"]),
            "duration": int(note["notated_duration"]["divisions"]),
            "type": str(note["notated_duration"]["name"]),
        }
        for note in notes
    ]
    if parsed_notes != expected_notes:
        raise PipelineError(
            CATEGORY_MUSICXML_EXPORT,
            STAGE_MUSICXML,
            "MusicXML measure, pitch, or duration sequence does not match arranged score",
        )
    parsed_part_name = parse_musicxml_part_name(output_path)
    if parsed_part_name != str(part_ir["name"]):
        raise PipelineError(CATEGORY_MUSICXML_EXPORT, STAGE_MUSICXML, "MusicXML part name does not match arranged score")
    out_of_range = [note["pitch"] for note in parsed_notes if int(note["pitch"]) < min_pitch or int(note["pitch"]) > max_pitch]
    if out_of_range:
        raise PipelineError(CATEGORY_MUSICXML_EXPORT, STAGE_MUSICXML, "MusicXML contains pitches outside target profile range")

    return {
        "path": str(output_path),
        "part_count": 1,
        "part_name": parsed_part_name,
        "measure_count": len(measures),
        "note_count": len(parsed_notes),
        "pitch_sequence": [note["pitch"] for note in parsed_notes],
        "time_signature": time_signature,
        "target_profile": {"id": profile["id"], "version": profile["version"]},
    }


def parse_musicxml_part_name(path: Path) -> Optional[str]:
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as error:
        raise PipelineError(CATEGORY_MUSICXML_EXPORT, STAGE_MUSICXML, f"MusicXML is not parseable: {error}")
    return root.findtext("./part-list/score-part/part-name")


def parse_musicxml_pitches(path: Path) -> List[int]:
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as error:
        raise PipelineError(CATEGORY_MUSICXML_EXPORT, STAGE_MUSICXML, f"MusicXML is not parseable: {error}")

    pitches = []
    for note in root.findall(".//note"):
        pitch = note.find("pitch")
        if pitch is None:
            continue
        step = pitch.findtext("step")
        octave = pitch.findtext("octave")
        if step is None or octave is None:
            raise PipelineError(CATEGORY_MUSICXML_EXPORT, STAGE_MUSICXML, "MusicXML note is missing pitch fields")
        alter = int(pitch.findtext("alter", default="0"))
        pitches.append((int(octave) + 1) * 12 + STEP_TO_PITCH_CLASS[step] + alter)
    return pitches


def parse_musicxml_score_notes(path: Path) -> List[Dict[str, object]]:
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as error:
        raise PipelineError(CATEGORY_MUSICXML_EXPORT, STAGE_MUSICXML, f"MusicXML is not parseable: {error}")

    parsed = []
    for measure in root.findall("./part/measure"):
        measure_number = int(measure.attrib["number"])
        for note in measure.findall("./note"):
            pitch = note.find("pitch")
            if pitch is None:
                continue
            step = pitch.findtext("step")
            octave = pitch.findtext("octave")
            if step is None or octave is None:
                raise PipelineError(CATEGORY_MUSICXML_EXPORT, STAGE_MUSICXML, "MusicXML note is missing pitch fields")
            alter = int(pitch.findtext("alter", default="0"))
            parsed.append(
                {
                    "measure": measure_number,
                    "pitch": (int(octave) + 1) * 12 + STEP_TO_PITCH_CLASS[step] + alter,
                    "duration": int(note.findtext("duration")),
                    "type": note.findtext("type"),
                }
            )
    return parsed


def _pitch_to_step(pitch: int):
    return PITCH_CLASS_TO_STEP[pitch % 12]


def _write_attributes(measure, time_signature: Dict[str, object]) -> None:
    attributes = ET.SubElement(measure, "attributes")
    divisions = ET.SubElement(attributes, "divisions")
    divisions.text = str(DIVISIONS)
    key = ET.SubElement(attributes, "key")
    fifths = ET.SubElement(key, "fifths")
    fifths.text = "0"
    time = ET.SubElement(attributes, "time")
    beats = ET.SubElement(time, "beats")
    beats.text = str(time_signature["beats_per_measure"])
    beat_type = ET.SubElement(time, "beat-type")
    beat_type.text = str(time_signature["beat_unit"])
    clef = ET.SubElement(attributes, "clef")
    sign = ET.SubElement(clef, "sign")
    sign.text = "G"
    line = ET.SubElement(clef, "line")
    line.text = "2"


def _add_pitched_note(measure, score_note: Dict[str, object]) -> None:
    note = ET.SubElement(measure, "note")
    pitch = ET.SubElement(note, "pitch")
    step, alter = _pitch_to_step(int(score_note["pitch"]))
    step_node = ET.SubElement(pitch, "step")
    step_node.text = step
    if alter:
        alter_node = ET.SubElement(pitch, "alter")
        alter_node.text = str(alter)
    octave = ET.SubElement(pitch, "octave")
    octave.text = str(int(score_note["pitch"]) // 12 - 1)
    duration = ET.SubElement(note, "duration")
    duration.text = str(int(score_note["notated_duration"]["divisions"]))
    voice = ET.SubElement(note, "voice")
    voice.text = "1"
    note_type = ET.SubElement(note, "type")
    note_type.text = str(score_note["notated_duration"]["name"])


def _add_rest(measure, duration_beats: float) -> None:
    note = ET.SubElement(measure, "note")
    ET.SubElement(note, "rest")
    duration = ET.SubElement(note, "duration")
    duration.text = str(max(1, int(round(duration_beats * DIVISIONS))))
    voice = ET.SubElement(note, "voice")
    voice.text = "1"
    note_type = ET.SubElement(note, "type")
    note_type.text = _rest_type(duration_beats)


def _rest_type(duration_beats: float) -> str:
    rounded = round(duration_beats, 6)
    if rounded == 0.5:
        return "eighth"
    if rounded == 1.0:
        return "quarter"
    if rounded == 2.0:
        return "half"
    if rounded == 4.0:
        return "whole"
    return "quarter"
