#!/usr/bin/env python3
"""Normalize speaker and dialogue indentation in events/*.ks files."""

from __future__ import annotations

import argparse
import difflib
import re
import sys
from pathlib import Path


BOM = b"\xef\xbb\xbf"
SPEAKER_RE = re.compile(
    r"^[\s\u3000]*(?P<markers>//[^/\r\n]*//(?:[\s\u3000]+//[^/\r\n]*//)*)[\s\u3000]*$"
)
SPEAKER_NAME_RE = re.compile(r"//(?P<name>[^/\r\n]*)//")
LEADING_INDENT_RE = re.compile(r"^[\t \u3000]+")
DISALLOWED_NAME_CHARS = set("。、「」『』【】[]（）()：:=|＠@；;＊*")
SCENE_PREFIXES = ("ーー", "――", "——", "---", "・・・", "……", "…")


def split_ending(line: str) -> tuple[str, str]:
    if line.endswith("\r\n"):
        return line[:-2], "\r\n"
    if line.endswith(("\n", "\r")):
        return line[:-1], line[-1]
    return line, ""


def first_content(text: str) -> str:
    return LEADING_INDENT_RE.sub("", text)


def is_dialogue(text: str) -> bool:
    return first_content(text).startswith("「")


def bare_speaker_candidate(text: str, next_text: str | None) -> str | None:
    if next_text is None or not is_dialogue(next_text):
        return None

    candidate = text.strip("\t \u3000")
    if not candidate or len(candidate) > 40:
        return None
    if SPEAKER_RE.fullmatch(text) or "//" in candidate:
        return None
    if candidate.startswith(("[", ";", "*", "@", "#")):
        return None
    if candidate.startswith(SCENE_PREFIXES):
        return None
    if any(char in DISALLOWED_NAME_CHARS for char in candidate):
        return None
    return candidate


def normalize_text(
    text: str, next_text: str | None
) -> tuple[str, str | None, str | None]:
    marker = SPEAKER_RE.fullmatch(text)
    if marker:
        names = [
            match.group("name").strip("\t \u3000")
            for match in SPEAKER_NAME_RE.finditer(marker.group("markers"))
        ]
        markers = " ".join(f"//{name}//" for name in names)
        return "\t" + markers, None, None

    if is_dialogue(text):
        return "\t" + first_content(text), None, None

    candidate = bare_speaker_candidate(text, next_text)
    if candidate is not None:
        if re.search(r"[\t \u3000]", candidate):
            return text, None, candidate
        return f"\t//{candidate}//", candidate, None

    return text, None, None


def transform(
    source: str,
) -> tuple[str, list[tuple[int, str]], list[tuple[int, str]]]:
    lines = source.splitlines(keepends=True)
    inferred: list[tuple[int, str]] = []
    ambiguous: list[tuple[int, str]] = []
    output: list[str] = []

    for index, line in enumerate(lines):
        text, ending = split_ending(line)
        next_text = None
        if index + 1 < len(lines):
            next_text, _ = split_ending(lines[index + 1])
        normalized, inferred_name, ambiguous_name = normalize_text(text, next_text)
        if inferred_name is not None:
            inferred.append((index + 1, inferred_name))
        if ambiguous_name is not None:
            ambiguous.append((index + 1, ambiguous_name))
        output.append(normalized + ending)

    return "".join(output), inferred, ambiguous


def read_utf8(path: Path) -> tuple[str, bool]:
    raw = path.read_bytes()
    has_bom = raw.startswith(BOM)
    payload = raw[len(BOM) :] if has_bom else raw
    try:
        return payload.decode("utf-8"), has_bom
    except UnicodeDecodeError as exc:
        raise ValueError(f"not valid UTF-8: {exc}") from exc


def encoded(text: str, has_bom: bool) -> bytes:
    return (BOM if has_bom else b"") + text.encode("utf-8")


def collect_files(targets: list[str]) -> list[Path]:
    files: set[Path] = set()
    for raw_target in targets or ["events"]:
        target = Path(raw_target)
        if not target.exists():
            raise FileNotFoundError(raw_target)
        if target.is_file():
            if target.suffix.lower() != ".ks":
                raise ValueError(f"not a .ks file: {target}")
            files.add(target)
        else:
            files.update(path for path in target.rglob("*.ks") if path.is_file())
    return sorted(files, key=lambda path: str(path).lower())


def show_diff(path: Path, before: str, after: str) -> None:
    diff = difflib.unified_diff(
        before.splitlines(keepends=True),
        after.splitlines(keepends=True),
        fromfile=str(path),
        tofile=str(path),
    )
    sys.stdout.writelines(diff)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Normalize KS speaker wrappers and one-tab dialogue indentation."
    )
    parser.add_argument("targets", nargs="*", help="KS files or directories (default: events)")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true", help="write reviewed changes")
    mode.add_argument("--check", action="store_true", help="exit 1 if formatting changes are needed")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        files = collect_files(args.targets)
    except (FileNotFoundError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    changed = 0
    unresolved = 0
    for path in files:
        try:
            before, has_bom = read_utf8(path)
        except ValueError as exc:
            print(f"error: {path}: {exc}", file=sys.stderr)
            return 2

        after, inferred, ambiguous = transform(before)
        for line_number, name in inferred:
            print(f"candidate speaker: {path}:{line_number}: {name}", file=sys.stderr)
        for line_number, name in ambiguous:
            unresolved += 1
            print(
                f"ambiguous speaker: {path}:{line_number}: {name}", file=sys.stderr
            )

        if after == before:
            continue

        changed += 1

        if args.write:
            path.write_bytes(encoded(after, has_bom))
            print(f"formatted: {path}")
        elif not args.check:
            show_diff(path, before, after)

    if args.check and (changed or unresolved):
        print(
            f"formatting needed: {changed} file(s); "
            f"unresolved speaker lines: {unresolved}",
            file=sys.stderr,
        )
        return 1
    if args.write:
        print(f"changed {changed} file(s)")
        if unresolved:
            print(
                f"unresolved speaker lines: {unresolved}", file=sys.stderr
            )
            return 1
    elif not args.check and not changed and not unresolved:
        print("no formatting changes needed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
