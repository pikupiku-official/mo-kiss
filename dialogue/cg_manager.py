"""CG scene state, transitions, and rendering helpers.

CG assets use the legacy project naming convention ``MMK_nn_nnn`` where the
middle token identifies a CG set and the final token identifies a variant.
The renderer intentionally treats the whole storage value as the public asset
ID while keeping the image centered and cropped to the game's 4:3 viewport.
"""

from __future__ import annotations

import re

import pygame

from core.config import VIRTUAL_HEIGHT, VIRTUAL_WIDTH, SCALE, scale_pos
from .character_manager import _blit_crossfade, get_scaled_image


CG_STORAGE_RE = re.compile(r"^[A-Z]{3}_\d{2}_\d{3}$", re.IGNORECASE)
DEFAULT_CG_FADE_MS = 300
DEFAULT_CG_MOVE_MS = 600
MIN_CG_ZOOM = 0.1
MAX_CG_ZOOM = 4.0


def _to_float(value, default):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _to_int(value, default):
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _state(game_state):
    return game_state.setdefault(
        "cg_state",
        {
            "storage": None,
            "offset_x": 0.0,
            "offset_y": 0.0,
            "zoom": 1.0,
            "transition": None,
        },
    )


def _image_manager(game_state):
    return game_state.get("image_manager")


def _has_asset(game_state, storage):
    if not storage:
        return False
    manager = _image_manager(game_state)
    if not manager:
        return False
    return manager.get_image("cg", storage) is not None


def _current_values(game_state):
    state = _state(game_state)
    transition = state.get("transition")
    if not transition:
        return (
            state.get("storage"),
            float(state.get("offset_x", 0.0)),
            float(state.get("offset_y", 0.0)),
            float(state.get("zoom", 1.0)),
        )

    now = pygame.time.get_ticks()
    duration = max(int(transition.get("duration", 0)), 0)
    if duration <= 0:
        progress = 1.0
    else:
        progress = max(
            0.0,
            min(1.0, (now - transition.get("start_time", now)) / duration),
        )

    # A new command can interrupt a running transition.  There is no single
    # storage ID for a partially blended frame, so use the incoming asset once
    # its blend has crossed the midpoint and the outgoing one before then.
    storage = (
        transition.get("to_storage")
        if progress >= 0.5
        else transition.get("from_storage")
    )
    return (
        storage,
        transition["from_offset_x"]
        + (transition["to_offset_x"] - transition["from_offset_x"]) * progress,
        transition["from_offset_y"]
        + (transition["to_offset_y"] - transition["from_offset_y"]) * progress,
        transition["from_zoom"]
        + (transition["to_zoom"] - transition["from_zoom"]) * progress,
    )


def _image_size(game_state, storage):
    manager = _image_manager(game_state)
    image = manager.get_image("cg", storage) if manager and storage else None
    if image is None:
        return 720, 480
    return image.get_size()


def _offset_limits(game_state, storage, zoom):
    width, height = _image_size(game_state, storage)
    scaled_height = VIRTUAL_HEIGHT * max(float(zoom), MIN_CG_ZOOM)
    scaled_width = scaled_height * width / max(height, 1)
    viewport_width = VIRTUAL_WIDTH
    viewport_height = VIRTUAL_HEIGHT
    return (
        max(0.0, (scaled_width - viewport_width) / 2.0),
        max(0.0, (scaled_height - viewport_height) / 2.0),
    )


def _clamp_offset(game_state, storage, offset_x, offset_y, zoom):
    max_x, max_y = _offset_limits(game_state, storage, zoom)
    return (
        max(-max_x, min(max_x, float(offset_x))),
        max(-max_y, min(max_y, float(offset_y))),
    )


def _fade_ms(params):
    if "fade" in params:
        return max(0, int(_to_float(params.get("fade"), 0.3) * 1000))
    return DEFAULT_CG_FADE_MS


def _move_ms(params):
    return max(0, _to_int(params.get("time"), DEFAULT_CG_MOVE_MS))


def _start_transition(
    game_state,
    *,
    from_storage,
    to_storage,
    from_offset_x,
    from_offset_y,
    from_zoom,
    to_offset_x,
    to_offset_y,
    to_zoom,
    duration_ms,
):
    state = _state(game_state)
    duration_ms = max(int(duration_ms), 0)
    if duration_ms <= 0:
        state.update(
            {
                "storage": to_storage,
                "offset_x": to_offset_x,
                "offset_y": to_offset_y,
                "zoom": to_zoom,
                "transition": None,
            }
        )
        return 0

    state["transition"] = {
        "from_storage": from_storage,
        "to_storage": to_storage,
        "from_offset_x": from_offset_x,
        "from_offset_y": from_offset_y,
        "from_zoom": from_zoom,
        "to_offset_x": to_offset_x,
        "to_offset_y": to_offset_y,
        "to_zoom": to_zoom,
        "start_time": pygame.time.get_ticks(),
        "duration": duration_ms,
    }
    # Keep the outgoing image as the committed state until the transition is
    # complete.  This also keeps character suppression active during hide.
    state["storage"] = from_storage
    state["offset_x"] = from_offset_x
    state["offset_y"] = from_offset_y
    state["zoom"] = from_zoom
    return duration_ms


def show_cg(game_state, storage, params=None):
    """Show a CG, replacing any currently visible CG."""
    params = params or {}
    storage = str(storage or params.get("storage") or "").strip()
    if not storage or not _has_asset(game_state, storage):
        print(f"[CG] image not found: {storage}")
        return False

    current_storage, current_x, current_y, current_zoom = _current_values(game_state)
    fade_ms = _fade_ms(params)
    return _start_transition(
        game_state,
        from_storage=current_storage,
        to_storage=storage,
        from_offset_x=current_x,
        from_offset_y=current_y,
        from_zoom=current_zoom,
        to_offset_x=0.0,
        to_offset_y=0.0,
        to_zoom=1.0,
        duration_ms=fade_ms,
    )


def shift_cg(game_state, params=None):
    """Change a CG variant and/or move/zoom the current CG."""
    params = params or {}
    state = _state(game_state)
    current_storage, current_x, current_y, current_zoom = _current_values(game_state)
    if not current_storage:
        print("[CG] cg_shift ignored because no CG is visible")
        return False

    target_storage = str(params.get("storage") or current_storage).strip()
    if not _has_asset(game_state, target_storage):
        print(f"[CG] image not found: {target_storage}")
        return False

    target_zoom = (
        max(MIN_CG_ZOOM, min(MAX_CG_ZOOM, _to_float(params["zoom"], current_zoom)))
        if "zoom" in params
        else current_zoom
    )
    target_x = current_x + _to_float(params.get("left"), 0.0) * VIRTUAL_WIDTH
    target_y = current_y + _to_float(params.get("top"), 0.0) * VIRTUAL_HEIGHT
    target_x, target_y = _clamp_offset(
        game_state, target_storage, target_x, target_y, target_zoom
    )

    image_changed = target_storage != current_storage
    moved = (
        abs(target_x - current_x) > 0.001
        or abs(target_y - current_y) > 0.001
        or abs(target_zoom - current_zoom) > 0.001
    )
    if not image_changed and not moved:
        return 0

    fade_ms = _fade_ms(params) if image_changed else 0
    move_ms = _move_ms(params) if moved else 0
    return _start_transition(
        game_state,
        from_storage=current_storage,
        to_storage=target_storage,
        from_offset_x=current_x,
        from_offset_y=current_y,
        from_zoom=current_zoom,
        to_offset_x=target_x,
        to_offset_y=target_y,
        to_zoom=target_zoom,
        duration_ms=max(fade_ms, move_ms),
    )


def hide_cg(game_state, params=None):
    """Fade out the current CG and restore normal character rendering."""
    params = params or {}
    current_storage, current_x, current_y, current_zoom = _current_values(game_state)
    if not current_storage:
        print("[CG] cg_hide ignored because no CG is visible")
        return False
    return _start_transition(
        game_state,
        from_storage=current_storage,
        to_storage=None,
        from_offset_x=current_x,
        from_offset_y=current_y,
        from_zoom=current_zoom,
        to_offset_x=current_x,
        to_offset_y=current_y,
        to_zoom=current_zoom,
        duration_ms=_fade_ms(params),
    )


def update_cg_animation(game_state):
    state = _state(game_state)
    transition = state.get("transition")
    if not transition:
        return
    now = pygame.time.get_ticks()
    if now - transition.get("start_time", now) < max(0, transition.get("duration", 0)):
        return
    state.update(
        {
            "storage": transition.get("to_storage"),
            "offset_x": transition.get("to_offset_x", 0.0),
            "offset_y": transition.get("to_offset_y", 0.0),
            "zoom": transition.get("to_zoom", 1.0),
            "transition": None,
        }
    )


def is_cg_visible(game_state):
    state = _state(game_state)
    return bool(state.get("storage") or state.get("transition"))


def _scaled_cg_surface(image, zoom):
    if image is None:
        return None
    target_height = max(1, round(VIRTUAL_HEIGHT * max(float(zoom), MIN_CG_ZOOM) * SCALE))
    return get_scaled_image(image, target_height / max(image.get_height(), 1))


def _cg_surface_and_pos(game_state, storage, offset_x, offset_y, zoom):
    manager = _image_manager(game_state)
    image = manager.get_image("cg", storage) if manager and storage else None
    if image is None:
        return None, (0, 0)
    surface = _scaled_cg_surface(image, zoom)
    center_x, center_y = scale_pos(
        VIRTUAL_WIDTH / 2 + offset_x,
        VIRTUAL_HEIGHT / 2 + offset_y,
    )
    return surface, (
        round(center_x - surface.get_width() / 2),
        round(center_y - surface.get_height() / 2),
    )


def draw_cg(game_state):
    """Draw the CG between background and character/UI layers."""
    state = _state(game_state)
    transition = state.get("transition")
    screen = game_state.get("screen")
    if screen is None:
        return

    if transition:
        now = pygame.time.get_ticks()
        duration = max(int(transition.get("duration", 0)), 0)
        progress = (
            1.0
            if duration <= 0
            else max(0.0, min(1.0, (now - transition.get("start_time", now)) / duration))
        )
        from_surface, from_pos = _cg_surface_and_pos(
            game_state,
            transition.get("from_storage"),
            transition.get("from_offset_x", 0.0),
            transition.get("from_offset_y", 0.0),
            transition.get("from_zoom", 1.0),
        )
        to_surface, to_pos = _cg_surface_and_pos(
            game_state,
            transition.get("to_storage"),
            transition.get("to_offset_x", 0.0),
            transition.get("to_offset_y", 0.0),
            transition.get("to_zoom", 1.0),
        )
        _blit_crossfade(screen, from_surface, from_pos, to_surface, to_pos, progress)
        return

    surface, pos = _cg_surface_and_pos(
        game_state,
        state.get("storage"),
        state.get("offset_x", 0.0),
        state.get("offset_y", 0.0),
        state.get("zoom", 1.0),
    )
    if surface is not None:
        screen.blit(surface, pos)


def cg_transition_duration_ms(params, action_type):
    """Fallback duration used by IR before/without handler state."""
    params = params or {}
    if action_type in ("cg_show", "cg_hide"):
        return _fade_ms(params)
    if action_type == "cg_shift":
        fade_ms = _fade_ms(params) if params.get("storage") else 0
        move_keys = {"left", "top", "zoom"}
        move_ms = _move_ms(params) if move_keys.intersection(params) else 0
        return max(fade_ms, move_ms)
    return 0
