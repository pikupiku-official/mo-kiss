"""Opt-in runtime trace for character image requests and presentation frames.

The trace is disabled unless ``DIALOGUE_RENDER_TRACE=1`` is set.  It is for
temporal rendering bugs that cannot be diagnosed from a single screenshot.
"""

import hashlib
import json
import os
import threading


_trace_lock = threading.Lock()
_trace_sequence = 0
_trace_event_count = 0
_trace_session_started = False


def trace_enabled():
    return os.environ.get("DIALOGUE_RENDER_TRACE", "").strip().lower() in {
        "1", "true", "yes", "on"
    }


def trace_light_enabled():
    """Use temporal/state logging without per-character full-surface diffs."""
    return trace_enabled() and os.environ.get(
        "DIALOGUE_RENDER_TRACE_LIGHT", ""
    ).strip().lower() in {"1", "true", "yes", "on"}


def _trace_path():
    return os.environ.get(
        "DIALOGUE_RENDER_TRACE_FILE",
        os.path.join("debug", "dialogue_render_trace.jsonl"),
    )


def trace_event(event, **payload):
    """Append one JSONL event and return its sequence number."""
    global _trace_sequence, _trace_event_count, _trace_session_started
    if not trace_enabled():
        return None

    try:
        max_events = int(os.environ.get("DIALOGUE_RENDER_TRACE_MAX", "20000"))
    except (TypeError, ValueError):
        max_events = 20000

    with _trace_lock:
        if max_events > 0 and _trace_event_count >= max_events:
            return None
        _trace_sequence += 1
        _trace_event_count += 1
        sequence = _trace_sequence
        path = _trace_path()
        parent = os.path.dirname(os.path.abspath(path))
        if parent:
            os.makedirs(parent, exist_ok=True)
        record = {
            "seq": sequence,
            "event": event,
            "ticks": payload.pop("ticks", None),
            **payload,
        }
        if not _trace_session_started:
            record["session_start"] = True
            _trace_session_started = True
        with open(path, "a", encoding="utf-8") as trace_file:
            trace_file.write(json.dumps(record, ensure_ascii=False, default=str))
            trace_file.write("\n")
        return sequence


def capture_surface_bytes(surface):
    """Return RGBA bytes for a Pygame surface, or ``None`` when unavailable."""
    if not trace_enabled() or surface is None:
        return None
    try:
        import pygame

        return pygame.image.tostring(surface, "RGBA")
    except (AttributeError, pygame.error):
        return None


def changed_pixel_count(before, after_surface):
    """Count pixels changed by one draw operation."""
    if before is None or after_surface is None:
        return None
    after = capture_surface_bytes(after_surface)
    if after is None or len(before) != len(after):
        return None
    return sum(
        before[offset:offset + 4] != after[offset:offset + 4]
        for offset in range(0, len(before), 4)
    )


def surface_summary(surface):
    """Return compact evidence for the exact surface presented this frame."""
    raw = capture_surface_bytes(surface)
    if raw is None:
        return None
    non_black = sum(
        raw[offset:offset + 3] != b"\x00\x00\x00"
        for offset in range(0, len(raw), 4)
    )
    return {
        "size": list(surface.get_size()),
        "non_black_pixels": non_black,
        "rgba_blake2b": hashlib.blake2b(raw, digest_size=8).hexdigest(),
    }
