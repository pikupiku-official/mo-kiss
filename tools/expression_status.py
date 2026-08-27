"""Inspect and update KS-level expression-review status markers."""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path


STATUSES = ("initial", "ai_draft", "human_confirmed")
MARKER_PREFIX = ";@expression-status:"
MARKER_RE = re.compile(
    r"^;@expression-status:[ \t]*([^ \t\r\n;]+)[ \t]*(?=\r?$)", re.MULTILINE
)


def inspect_status_text(text: str) -> str:
    matches = MARKER_RE.findall(text)
    if not matches:
        return "initial"
    if len(matches) != 1:
        raise ValueError("expression status marker must occur at most once")
    status = matches[0]
    if status not in STATUSES:
        raise ValueError(f"unknown expression status: {status}")
    return status


def set_status_text(text: str, status: str) -> str:
    if status not in STATUSES:
        raise ValueError(f"unknown expression status: {status}")

    matches = list(MARKER_RE.finditer(text))
    if len(matches) > 1:
        raise ValueError("expression status marker must occur at most once")

    if status == "initial":
        if not matches:
            return text
        match = matches[0]
        end = match.end()
        if text[end : end + 2] == "\r\n":
            end += 2
        elif text[end : end + 1] == "\n":
            end += 1
        return text[: match.start()] + text[end:]

    marker = f"{MARKER_PREFIX} {status}"
    if matches:
        match = matches[0]
        return text[: match.start()] + marker + text[match.end() :]

    newline = "\r\n" if "\r\n" in text else "\n"
    start_match = re.search(r"^\*start[ \t]*(?=\r?$)", text, re.MULTILINE)
    if not start_match:
        raise ValueError("cannot add expression status: *start label not found")
    insert_at = start_match.end()
    return text[:insert_at] + newline + marker + text[insert_at:]


def _read_text(path: Path) -> tuple[str, bool]:
    data = path.read_bytes()
    has_bom = data.startswith(b"\xef\xbb\xbf")
    return data.decode("utf-8-sig"), has_bom


def read_status(path: Path) -> str:
    text, _ = _read_text(path)
    return inspect_status_text(text)


def write_status(path: Path, status: str) -> None:
    text, has_bom = _read_text(path)
    encoded = set_status_text(text, status).encode("utf-8")
    if has_bom:
        encoded = b"\xef\xbb\xbf" + encoded
    temporary = path.with_name(f".{path.name}.expression-status.tmp")
    temporary.write_bytes(encoded)
    os.replace(temporary, path)


def iter_ks_files(events_dir: Path):
    yield from sorted(events_dir.glob("*.ks"), key=lambda item: item.name.lower())


def _events_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "events"


def _resolve_event_path(value: str) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = Path.cwd() / path
    path = path.resolve()
    events_dir = _events_dir().resolve()
    if path.parent != events_dir or path.suffix.lower() != ".ks":
        raise ValueError("target must be a direct child KS file of events/")
    if not path.is_file():
        raise ValueError(f"KS file not found: {path}")
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    get_parser = subparsers.add_parser("get", help="print one KS status")
    get_parser.add_argument("path")
    set_parser = subparsers.add_parser("set", help="set one KS status")
    set_parser.add_argument("path")
    set_parser.add_argument("status", choices=STATUSES)
    list_parser = subparsers.add_parser("list", help="list KS statuses")
    list_parser.add_argument("--status", choices=STATUSES)
    subparsers.add_parser("validate", help="validate all explicit markers")
    args = parser.parse_args(argv)

    try:
        if args.command == "get":
            path = _resolve_event_path(args.path)
            print(read_status(path))
        elif args.command == "set":
            path = _resolve_event_path(args.path)
            write_status(path, args.status)
            print(f"{path.name}: {read_status(path)}")
        else:
            errors = []
            for path in iter_ks_files(_events_dir()):
                try:
                    status = read_status(path)
                    if args.command == "list" and (args.status is None or args.status == status):
                        print(f"{path.name}\t{status}")
                except ValueError as error:
                    errors.append(f"{path.name}: {error}")
            if errors:
                print("\n".join(errors), file=sys.stderr)
                return 1
    except ValueError as error:
        parser.error(str(error))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
