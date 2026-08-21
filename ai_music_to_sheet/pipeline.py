from __future__ import annotations

import uuid
from pathlib import Path
from typing import Dict, Iterable, Optional

from .arrangement import ArrangementNotAccepted, arrange_score_ir, get_instrument_profile
from .contracts import (
    ACCEPTED,
    CATEGORY_EVALUATION,
    CATEGORY_NOTE_EVENTS_CONTRACT,
    CATEGORY_TRANSCRIPTION_QUALITY,
    CATEGORY_UNSUPPORTED_SCOPE,
    COMPLETED,
    FAIL,
    NOT_ACCEPTED,
    PASS,
    PIPELINE_VERSION,
    REVIEW,
    STAGE_DECODE,
    STAGE_DELIVERY,
    STAGE_EVALUATION,
    STAGE_ARRANGEMENT,
    STAGE_INSTRUMENT_PROFILE,
    STAGE_MEDIA,
    STAGE_MUSICXML,
    STAGE_NOTE_EVENTS,
    STAGE_QUANTIZATION,
    STAGE_SCOPE,
    STAGE_SCORE_IR,
    STAGE_TIME_MAP,
    STAGE_TRANSCRIPTION,
    PipelineError,
    utc_now,
    validate_note_events_artifact,
    write_json,
)
from .evaluation import score_notes_against_reference
from .media import decode_to_canonical_wav, inspect_source
from .musicxml import export_arranged_score_musicxml, export_musicxml
from .timing import build_score_ir, build_time_map
from .transcription import CONFIDENCE_REVIEW_THRESHOLD, POLYPHONY_RATIO_THRESHOLD, transcribe_monophonic_wav


def process_media_file(
    media_path,
    output_dir,
    *,
    reference_notes: Optional[Iterable[Dict[str, object]]] = None,
    job_id: Optional[str] = None,
    run_id: Optional[str] = None,
    target_profile_id: Optional[str] = None,
) -> Dict[str, object]:
    """Process one clean monophonic MP3/MP4 file into NoteEvents and MusicXML artifacts."""

    media_path = Path(media_path)
    output_dir = Path(output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    job_id = job_id or f"job-{uuid.uuid4().hex[:12]}"
    stages = []
    artifacts: Dict[str, str] = {}
    source: Dict[str, object] = {
        "job_id": job_id,
        "source_path": str(media_path),
        "input_format": "",
    }
    evaluation_report = None
    target_profile = None
    arranged_score = None
    musicxml = None

    def finish(job_state: str, quality_status: str, reason=None) -> Dict[str, object]:
        acceptance = ACCEPTED if job_state == COMPLETED and quality_status == PASS and reason is None else NOT_ACCEPTED
        result = {
            "schema_version": "processing-result/v1",
            "generator_version": PIPELINE_VERSION,
            "created_at": utc_now(),
            "job_id": job_id,
            "run_id": run_id,
            "job_state": job_state,
            "quality_status": quality_status,
            "acceptance": acceptance,
            "reason": reason,
            "source": source,
            "artifacts": artifacts.copy(),
            "stages": stages.copy(),
        }
        if target_profile is not None:
            result["target_profile"] = target_profile
        if evaluation_report is not None:
            result["evaluation_report"] = evaluation_report
        result_path = output_dir / "result.json"
        write_json(result_path, result)
        result["artifacts"]["result"] = str(result_path)
        write_json(result_path, result)
        return result

    try:
        source = inspect_source(media_path, job_id)
        source_path = output_dir / "source.json"
        write_json(source_path, source)
        artifacts["source"] = str(source_path)
        _stage(stages, STAGE_MEDIA, PASS, "MEDIA_OK", "Source media accepted")

        canonical = decode_to_canonical_wav(media_path, output_dir, source)
        canonical_path = output_dir / "canonical_audio.json"
        write_json(canonical_path, canonical)
        artifacts["canonical_audio"] = str(canonical_path)
        _stage(stages, STAGE_DECODE, PASS, "DECODE_OK", "Media decoded to canonical mono PCM")

        transcription = transcribe_monophonic_wav(canonical["wav_path"])
        if transcription["average_secondary_ratio"] >= POLYPHONY_RATIO_THRESHOLD:
            reason = {
                "category": CATEGORY_UNSUPPORTED_SCOPE,
                "stage": STAGE_SCOPE,
                "message": "Input contains competing pitch energy outside the clean monophonic support envelope",
            }
            _stage(stages, STAGE_SCOPE, REVIEW, CATEGORY_UNSUPPORTED_SCOPE, reason["message"])
            return finish(REVIEW, REVIEW, reason)
        _stage(stages, STAGE_SCOPE, PASS, "SCOPE_OK", "Input fits the clean monophonic support envelope")

        if not transcription["notes"]:
            raise PipelineError(CATEGORY_TRANSCRIPTION_QUALITY, STAGE_TRANSCRIPTION, "No note events could be produced")
        _stage(stages, STAGE_TRANSCRIPTION, PASS, "TRANSCRIPTION_COMPLETE", "Monophonic note events produced")

        notes_with_ids = []
        for index, note in enumerate(transcription["notes"], start=1):
            note_with_id = dict(note)
            note_with_id["id"] = f"note-{index:04d}"
            notes_with_ids.append(note_with_id)

        note_events = {
            "schema_version": "note-events/v1",
            "generator_version": PIPELINE_VERSION,
            "created_at": utc_now(),
            "job_id": job_id,
            "source_id": source["source_id"],
            "source_path": source["source_path"],
            "input_format": source["input_format"],
            "average_confidence": transcription["average_confidence"],
            "average_secondary_ratio": transcription["average_secondary_ratio"],
            "max_secondary_ratio": transcription["max_secondary_ratio"],
            "notes": notes_with_ids,
        }
        errors = validate_note_events_artifact(note_events)
        if errors:
            raise PipelineError(CATEGORY_NOTE_EVENTS_CONTRACT, STAGE_NOTE_EVENTS, "; ".join(errors))
        note_events_path = output_dir / "note_events.json"
        write_json(note_events_path, note_events)
        artifacts["note_events"] = str(note_events_path)
        _stage(stages, STAGE_NOTE_EVENTS, PASS, "NOTE_EVENTS_VALID", "NoteEvents contract validated")

        time_map = build_time_map(note_events, canonical)
        time_map_path = output_dir / "time_map.json"
        write_json(time_map_path, time_map)
        artifacts["time_map"] = str(time_map_path)
        _stage(stages, STAGE_TIME_MAP, PASS, "TIME_MAP_VALID", "TimeMap contract validated")

        score_ir = build_score_ir(note_events, time_map)
        _stage(stages, STAGE_QUANTIZATION, PASS, "QUANTIZATION_VALID", "NoteEvents mapped to supported note values")
        score_ir_path = output_dir / "score_ir.json"
        write_json(score_ir_path, score_ir)
        artifacts["score_ir"] = str(score_ir_path)
        _stage(stages, STAGE_SCORE_IR, PASS, "SCORE_IR_VALID", "ScoreIR contract validated")

        if target_profile_id is not None:
            target_profile = get_instrument_profile(str(target_profile_id))
            target_profile_path = output_dir / "target_profile.json"
            write_json(target_profile_path, target_profile)
            artifacts["target_profile"] = str(target_profile_path)
            _stage(
                stages,
                STAGE_INSTRUMENT_PROFILE,
                PASS,
                "INSTRUMENT_PROFILE_VALID",
                "Supported target profile contract validated",
            )

            arranged_score = arrange_score_ir(
                score_ir,
                target_profile=target_profile,
                source=source,
                source_artifact_path=artifacts["source"],
                score_ir_artifact_path=artifacts["score_ir"],
                time_map=time_map,
                time_map_artifact_path=artifacts["time_map"],
            )
            arranged_score_path = output_dir / "arranged_score.json"
            write_json(arranged_score_path, arranged_score)
            artifacts["arranged_score"] = str(arranged_score_path)
            _stage(
                stages,
                STAGE_ARRANGEMENT,
                PASS,
                "ARRANGED_SCORE_VALID",
                "Arranged score contract validated for the target profile",
            )

            musicxml_path = output_dir / "score.musicxml"
            musicxml = export_arranged_score_musicxml(arranged_score, musicxml_path)
            artifacts["musicxml"] = str(musicxml_path)
            _stage(stages, STAGE_MUSICXML, PASS, "MUSICXML_VALID", "MusicXML parses and matches arranged score")
        else:
            musicxml_path = output_dir / "score.musicxml"
            musicxml = export_musicxml(note_events, musicxml_path, score_ir)
            artifacts["musicxml"] = str(musicxml_path)
            _stage(stages, STAGE_MUSICXML, PASS, "MUSICXML_VALID", "MusicXML parses and matches ScoreIR")

        quality_status = PASS
        reason = None
        if transcription["average_confidence"] < CONFIDENCE_REVIEW_THRESHOLD:
            quality_status = REVIEW
            reason = {
                "category": CATEGORY_TRANSCRIPTION_QUALITY,
                "stage": STAGE_TRANSCRIPTION,
                "message": "Average note confidence is below the automatic acceptance threshold",
            }
            _stage(stages, STAGE_TRANSCRIPTION, REVIEW, CATEGORY_TRANSCRIPTION_QUALITY, reason["message"])

        if reference_notes is not None:
            artifact_versions = {
                "source": source["version"],
                "canonical_audio": canonical["version"],
                "note_events": note_events["generator_version"],
                "time_map": time_map["generator_version"],
                "score_ir": score_ir["generator_version"],
                "musicxml": PIPELINE_VERSION,
            }
            if target_profile is not None and arranged_score is not None:
                artifact_versions["target_profile"] = target_profile["version"]
                artifact_versions["arranged_score"] = arranged_score["generator_version"]
            evaluation_report = score_notes_against_reference(
                predicted_notes=note_events["notes"],
                reference_notes=reference_notes,
                case_name=str(media_path.name),
                artifact_versions=artifact_versions,
                score_ir=score_ir,
                time_map=time_map,
                arranged_score=arranged_score,
                musicxml_summary=musicxml,
            )
            evaluation_path = output_dir / "evaluation_report.json"
            write_json(evaluation_path, evaluation_report)
            artifacts["evaluation_report"] = str(evaluation_path)
            _stage(
                stages,
                STAGE_EVALUATION,
                evaluation_report["status"],
                "EVALUATION_COMPLETE",
                "Ground-truth evaluation report produced",
            )
            if evaluation_report["status"] != PASS:
                quality_status = evaluation_report["status"]
                reason = {
                    "category": CATEGORY_EVALUATION,
                    "stage": STAGE_EVALUATION,
                    "message": "Ground-truth evaluation did not meet automatic acceptance thresholds",
                }

        _stage(stages, STAGE_DELIVERY, PASS, "ARTIFACTS_DELIVERED", "Result manifest and artifacts written")
        job_state = COMPLETED if quality_status == PASS else REVIEW
        return finish(job_state, quality_status, reason)

    except PipelineError as error:
        _stage(stages, error.stage, FAIL, error.category, error.message)
        return finish(FAIL, FAIL, error.reason())
    except ArrangementNotAccepted as error:
        _stage(stages, error.stage, REVIEW, error.category, error.message)
        return finish(REVIEW, REVIEW, error.reason())


def _stage(stages, stage, status, category, message) -> None:
    stages.append(
        {
            "stage": stage,
            "status": status,
            "category": category,
            "message": message,
            "created_at": utc_now(),
        }
    )
