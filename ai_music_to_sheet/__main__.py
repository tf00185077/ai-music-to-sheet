from __future__ import annotations

import argparse
import json
import sys

from .pipeline import process_media_file


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Process a clean monophonic MP3/MP4 into NoteEvents and MusicXML.")
    parser.add_argument("media_path", help="Input MP3 or MP4 file")
    parser.add_argument("output_dir", help="Directory where artifacts will be written")
    args = parser.parse_args(argv)

    result = process_media_file(args.media_path, args.output_dir)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["job_state"] in {"COMPLETED", "REVIEW"} else 1


if __name__ == "__main__":
    sys.exit(main())

