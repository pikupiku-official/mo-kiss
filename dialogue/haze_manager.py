"""Cheap screen-space haze veil for rainy scenes."""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

import pygame


def _number(value: Any, default: float) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed == parsed else default


def _color(value: Any, default: Tuple[int, int, int] = (218, 226, 232)) -> Tuple[int, int, int]:
    text = str(value or "").strip()
    if text.startswith("#") and len(text) == 7:
        try:
            return tuple(int(text[index:index + 2], 16) for index in (1, 3, 5))
        except ValueError:
            return default
    pieces = [piece.strip() for piece in text.split(",")]
    if len(pieces) == 3:
        try:
            return tuple(max(0, min(255, int(piece))) for piece in pieces)
        except ValueError:
            return default
    return default


def _fade_seconds(params: Dict[str, Any]) -> float:
    return max(0.0, _number(params.get("fade", params.get("time")), 0.8))


class HazeManager:
    """Draw a uniform translucent veil over the BG, below characters and UI."""

    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.state: Dict[str, Any] = {
            "active": False,
            "color": (218, 226, 232),
            "opacity": 0.0,
            "target_opacity": 0.0,
            # Kept in state for compatibility with existing KS files.  Haze
            # is intentionally uniform; it no longer uses banded drift.
            "drift": 0.25,
            "fade_started_at_ms": 0,
            "fade_from_opacity": 0.0,
            "fade_duration_ms": 0,
        }

    def _begin_fade(self, target: float, seconds: float) -> None:
        now = pygame.time.get_ticks()
        self.state["fade_from_opacity"] = float(self.state.get("opacity", 0.0))
        self.state["target_opacity"] = max(0.0, min(1.0, float(target)))
        self.state["fade_started_at_ms"] = now
        self.state["fade_duration_ms"] = max(0, round(max(0.0, seconds) * 1000))
        if not self.state["fade_duration_ms"]:
            self.state["opacity"] = self.state["target_opacity"]

    def show(self, params: Optional[Dict[str, Any]] = None) -> None:
        params = dict(params or {})
        self.state["active"] = True
        self.state["color"] = _color(params.get("color"), self.state["color"])
        opacity = _number(params.get("opacity"), 0.16)
        if opacity > 1.0:
            opacity /= 100.0
        self.state["drift"] = max(0.0, _number(params.get("drift"), 0.25))
        self._begin_fade(opacity, _fade_seconds(params))

    def hide(self, params: Optional[Dict[str, Any]] = None) -> None:
        params = dict(params or {})
        if not self.state.get("active") and self.state.get("opacity", 0.0) <= 0:
            return
        self._begin_fade(0.0, _fade_seconds(params))
        if not self.state["fade_duration_ms"]:
            self.state["active"] = False

    def stop(self) -> None:
        self.state.update({"active": False, "opacity": 0.0, "target_opacity": 0.0, "fade_duration_ms": 0})

    def update(self) -> None:
        duration = int(self.state.get("fade_duration_ms", 0))
        if duration <= 0:
            return
        now = pygame.time.get_ticks()
        progress = max(
            0.0,
            min(1.0, (now - self.state["fade_started_at_ms"]) / duration),
        )
        start = float(self.state.get("fade_from_opacity", 0.0))
        target = float(self.state.get("target_opacity", 0.0))
        self.state["opacity"] = start + (target - start) * progress
        if progress >= 1.0:
            self.state["fade_duration_ms"] = 0
            if target <= 0.0:
                self.state["active"] = False

    def render(self) -> None:
        opacity = max(0.0, min(1.0, float(self.state.get("opacity", 0.0))))
        if opacity <= 0.0:
            return
        width, height = self.screen.get_size()
        overlay = pygame.Surface((width, height), pygame.SRCALPHA)
        red, green, blue = self.state.get("color", (218, 226, 232))
        overlay.fill((red, green, blue, round(255 * opacity)))
        self.screen.blit(overlay, (0, 0))

    def apply_to_transparent_surface(
        self,
        surface: pygame.Surface,
        opacity_scale: float = 1.0,
    ) -> None:
        """Apply the haze veil to existing pixels while preserving alpha.

        Character layers are rendered onto transparent surfaces before being
        composited over the already-hazed background.  Source-over drawing a
        normal veil would also haze transparent pixels, so use RGB blend
        operations that keep each character pixel's original alpha intact.
        """
        base_opacity = max(
            0.0,
            min(1.0, float(self.state.get("opacity", 0.0))),
        )
        opacity = max(0.0, min(1.0, base_opacity * float(opacity_scale)))
        if opacity <= 0.0:
            return

        red, green, blue = self.state.get("color", (218, 226, 232))
        rgb_weight = round(255 * (1.0 - opacity))
        surface.fill(
            (rgb_weight, rgb_weight, rgb_weight, 255),
            special_flags=pygame.BLEND_RGBA_MULT,
        )
        surface.fill(
            (
                round(red * opacity),
                round(green * opacity),
                round(blue * opacity),
                0,
            ),
            special_flags=pygame.BLEND_RGBA_ADD,
        )


def get_haze_manager(game_state: Dict[str, Any]) -> HazeManager:
    manager = game_state.get("haze_manager")
    if manager is None:
        manager = HazeManager(game_state["screen"])
        game_state["haze_manager"] = manager
    return manager


def update_haze(game_state: Dict[str, Any]) -> None:
    manager = game_state.get("haze_manager")
    if manager is not None:
        manager.update()


def draw_haze(game_state: Dict[str, Any]) -> None:
    manager = game_state.get("haze_manager")
    if manager is not None:
        manager.render()
