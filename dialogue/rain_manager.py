"""Looping rain ambience for KS scenes.

Rain is kept on its own mixer channel so it never replaces the scene BGM or
one-shot SE.  The bundled sound files are deliberately small PCM loops, which
keeps playback reliable on machines without a video/audio codec pack.
"""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

import pygame


RAIN_PRESETS = {
    "normal": "normal_rain.wav",
    "light": "normal_rain.wav",
    "heavy": "heavy_rain.wav",
}


def _number(value: Any, default: float) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed == parsed else default


def _fade_seconds(params: Dict[str, Any]) -> float:
    return max(0.0, _number(params.get("fade", params.get("time")), 0.8))


class RainManager:
    """Play one looping rain bed without touching BGM/SE channels."""

    def __init__(self, screen: pygame.Surface, project_root: Optional[str] = None):
        self.screen = screen
        self.project_root = project_root or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.channel = None
        self.sound = None
        self.state: Dict[str, Any] = {
            "active": False,
            "preset": None,
            "file": None,
            "volume": 0.0,
            "target_volume": 0.0,
            "fade_started_at_ms": 0,
            "fade_from_volume": 0.0,
            "fade_duration_ms": 0,
            "error": None,
        }

    def _resolve_path(self, params: Dict[str, Any]) -> Optional[str]:
        requested = str(params.get("file") or "").strip()
        preset = str(params.get("preset") or params.get("mode") or "normal").strip().lower()
        filename = requested or RAIN_PRESETS.get(preset, RAIN_PRESETS["normal"])
        filename = os.path.basename(filename)
        if not filename.lower().endswith((".wav", ".ogg", ".mp3", ".m4a")):
            filename += ".wav"
        for subdir in ("ambience", "ses"):
            root = os.path.abspath(os.path.join(self.project_root, "sounds", subdir))
            candidate = os.path.abspath(os.path.join(root, filename))
            try:
                if os.path.commonpath((root, candidate)) != root:
                    continue
            except ValueError:
                continue
            if os.path.isfile(candidate):
                return candidate
        return None

    def _set_volume(self, volume: float) -> None:
        volume = max(0.0, min(1.0, float(volume)))
        self.state["volume"] = volume
        if self.channel is not None:
            self.channel.set_volume(volume)

    def _begin_fade(self, target: float, seconds: float) -> None:
        now = pygame.time.get_ticks()
        self.state["fade_from_volume"] = float(self.state.get("volume", 0.0))
        self.state["target_volume"] = max(0.0, min(1.0, float(target)))
        self.state["fade_started_at_ms"] = now
        self.state["fade_duration_ms"] = max(0, round(max(0.0, seconds) * 1000))
        if not self.state["fade_duration_ms"]:
            self._set_volume(self.state["target_volume"])

    def show(self, params: Optional[Dict[str, Any]] = None) -> bool:
        params = dict(params or {})
        self.stop()
        path = self._resolve_path(params)
        target_volume = max(0.0, min(1.0, _number(params.get("volume"), 0.32)))
        self.state.update(
            {
                "active": False,
                "preset": str(params.get("preset") or params.get("mode") or "normal"),
                "file": path,
                "volume": 0.0,
                "target_volume": target_volume,
                "error": None if path else "Rain sound file not found in sounds/ambience/.",
            }
        )
        if not path:
            return False
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            self.sound = pygame.mixer.Sound(path)
            self.channel = self.sound.play(loops=-1)
            if self.channel is None:
                raise RuntimeError("pygame could not allocate a rain channel")
            self.channel.set_volume(0.0)
            self.state["active"] = True
            self._begin_fade(target_volume, _fade_seconds(params))
            print(f"[RAIN] started file={os.path.basename(path)} volume={target_volume:.2f}")
            return True
        except Exception as exc:
            self.state["error"] = f"Rain sound could not start: {exc}"
            self.stop()
            self.state["error"] = f"Rain sound could not start: {exc}"
            return False

    def hide(self, params: Optional[Dict[str, Any]] = None) -> None:
        params = dict(params or {})
        if self.channel is None:
            self.stop()
            return
        duration = _fade_seconds(params)
        if duration <= 0:
            self.stop()
            return
        self._begin_fade(0.0, duration)

    def stop(self) -> None:
        if self.channel is not None:
            try:
                self.channel.stop()
            except Exception:
                pass
        self.channel = None
        self.sound = None
        self.state.update(
            {
                "active": False,
                "file": None,
                "volume": 0.0,
                "target_volume": 0.0,
                "fade_duration_ms": 0,
            }
        )

    def update(self) -> None:
        if self.channel is None:
            return
        duration = int(self.state.get("fade_duration_ms", 0))
        if duration <= 0:
            return
        now = pygame.time.get_ticks()
        progress = max(
            0.0,
            min(1.0, (now - self.state["fade_started_at_ms"]) / duration),
        )
        start = float(self.state.get("fade_from_volume", 0.0))
        target = float(self.state.get("target_volume", 0.0))
        self._set_volume(start + (target - start) * progress)
        if progress >= 1.0:
            self.state["fade_duration_ms"] = 0
            if target <= 0.0:
                self.stop()


def get_rain_manager(game_state: Dict[str, Any]) -> RainManager:
    manager = game_state.get("rain_manager")
    if manager is None:
        manager = RainManager(game_state["screen"])
        game_state["rain_manager"] = manager
    return manager


def update_rain(game_state: Dict[str, Any]) -> None:
    manager = game_state.get("rain_manager")
    if manager is not None:
        manager.update()

