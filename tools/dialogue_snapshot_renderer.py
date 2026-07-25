"""Deterministic dialogue step snapshot entry point.

This process is used by the event editor for thumbnails and screenshots. It
does not launch an interactive preview window. Normal snapshots render the
fully settled state after the selected step.
"""

import argparse
import json
import os
import sys


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import pygame

from tools.preview_dialogue import (
    create_step_preview_runtime,
    preview_step_image,
)


RESULT_MARKER = "@@PREVIEW@@"


def run_snapshot_server():
    """Serve JSON-line snapshot requests with a reusable image cache."""
    runtime = None
    try:
        runtime = create_step_preview_runtime()
        print(f'{RESULT_MARKER}{{"type":"ready"}}', flush=True)
        for line in sys.stdin:
            request = {}
            try:
                request = json.loads(line)
                success = preview_step_image(
                    request["source_path"],
                    int(request["step_index"]),
                    request["out_path"],
                    runtime=runtime,
                    output_size=request.get("output_size"),
                    transition_progress=float(
                        request.get("transition_progress", 1.0)
                    ),
                    event_id=request.get("event_id"),
                )
                result = {
                    "type": "result",
                    "request_id": request.get("request_id"),
                    "success": bool(success),
                    "out_path": request["out_path"],
                    "message": (
                        ""
                        if success
                        else "Snapshot renderer returned an error."
                    ),
                }
            except Exception as exc:
                result = {
                    "type": "result",
                    "request_id": request.get("request_id"),
                    "success": False,
                    "out_path": request.get("out_path", ""),
                    "message": f"Snapshot failed: {exc}",
                }
            print(
                RESULT_MARKER + json.dumps(result, ensure_ascii=False),
                flush=True,
            )
    finally:
        if runtime is not None:
            pygame.quit()


def main():
    parser = argparse.ArgumentParser(
        description="Render a deterministic PNG for one dialogue step."
    )
    parser.add_argument("ks_file", nargs="?", help="KS file to render")
    parser.add_argument("--step", type=int, help="1-based visible step index")
    parser.add_argument("--out", help="Output PNG path")
    parser.add_argument(
        "--transition-progress",
        type=float,
        default=1.0,
        help="Selected transition progress from 0.0 to 1.0 (default: settled)",
    )
    parser.add_argument(
        "--server",
        action="store_true",
        help="Serve JSON-line snapshot requests",
    )
    args = parser.parse_args()

    if args.server:
        run_snapshot_server()
        return 0

    if not args.ks_file or args.step is None or not args.out:
        parser.error("ks_file, --step, and --out are required")
    if not os.path.exists(args.ks_file):
        parser.error(f"KS file does not exist: {args.ks_file}")
    if not 0.0 <= args.transition_progress <= 1.0:
        parser.error("--transition-progress must be between 0.0 and 1.0")

    success = preview_step_image(
        args.ks_file,
        args.step,
        args.out,
        transition_progress=args.transition_progress,
    )
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
