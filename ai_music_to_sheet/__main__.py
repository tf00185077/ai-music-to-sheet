from __future__ import annotations

import argparse
import json
import sys

from .contracts import (
    ACCEPTED,
    CATEGORY_DELIVERY,
    COMPLETED,
    FAIL,
    NOT_ACCEPTED,
    PASS,
    PIPELINE_VERSION,
    STAGE_DELIVERY,
    utc_now,
)
from .pipeline import process_media_file


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Process a clean monophonic MP3/MP4 into NoteEvents and MusicXML.")
    parser.add_argument("media_path", help="Input MP3 or MP4 file")
    parser.add_argument("output_dir", help="Directory where artifacts will be written")
    parser.add_argument("--target-profile", dest="target_profile_id", help="Supported target instrument profile id")
    args = parser.parse_args(argv)

    try:
        result = process_media_file(args.media_path, args.output_dir, target_profile_id=args.target_profile_id)
    except Exception as error:
        result = _unexpected_failure(args, error)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if _accepted(result) else 1


def _accepted(result) -> bool:
    return (
        result.get("acceptance") == ACCEPTED
        and result.get("job_state") == COMPLETED
        and result.get("quality_status") == PASS
    )


def _unexpected_failure(args, error: Exception):
    message = str(error) or error.__class__.__name__
    return {
        "schema_version": "processing-result/v1",
        "generator_version": PIPELINE_VERSION,
        "created_at": utc_now(),
        "job_id": None,
        "run_id": None,
        "job_state": FAIL,
        "quality_status": FAIL,
        "acceptance": NOT_ACCEPTED,
        "reason": {
            "category": CATEGORY_DELIVERY,
            "stage": STAGE_DELIVERY,
            "message": message,
        },
        "source": {
            "source_path": args.media_path,
            "input_format": "",
        },
        "artifacts": {},
        "stages": [
            {
                "stage": STAGE_DELIVERY,
                "status": FAIL,
                "category": CATEGORY_DELIVERY,
                "message": message,
                "created_at": utc_now(),
            }
        ],
    }


if __name__ == "__main__":
    sys.exit(main())
