from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List

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


def export_musicxml(note_events_artifact: Dict[str, object], output_path: Path) -> Dict[str, object]:
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
    part_name.text = "Melody"

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


def _pitch_to_step(pitch: int):
    return PITCH_CLASS_TO_STEP[pitch % 12]
