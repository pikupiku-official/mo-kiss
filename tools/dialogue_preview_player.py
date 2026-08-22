"""Interactive dialogue preview entry point.

Unlike the snapshot renderer, this launches the real-time preview loop and
lets character/background transitions advance over time.
"""

import argparse
import os
import sys


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from tools.preview_dialogue import preview_ks_file


def main():
    parser = argparse.ArgumentParser(
        description="Play a KS dialogue interactively in a preview window."
    )
    parser.add_argument("ks_file", help="KS file to play")
    parser.add_argument(
        "--step",
        type=int,
        default=1,
        help="1-based step number to start from",
    )
    args = parser.parse_args()

    if not os.path.exists(args.ks_file):
        parser.error(f"KS file does not exist: {args.ks_file}")

    return 0 if preview_ks_file(args.ks_file, start_step=args.step) else 1


if __name__ == "__main__":
    raise SystemExit(main())
