"""Persistent player settings shared by every game subsystem."""

from __future__ import annotations

import json
import os
import weakref
from copy import deepcopy

import pygame

from core.path_utils import get_project_root


DEFAULT_SETTINGS = {
    "master_volume": 1.0,
    "music_volume": 1.0,
    "se_volume": 1.0,
    "voice_volume": 1.0,
    # 0 = slowest, 1 = fastest. 0.5 preserves the former 110 ms default.
    "text_speed": 0.5,
    "fullscreen": False,
}

_VOLUME_KEYS = {
    "master_volume",
    "music_volume",
    "se_volume",
    "voice_volume",
}
_TEXT_DELAY_SLOWEST_MS = 205
_TEXT_DELAY_FASTEST_MS = 15


class SettingsManager:
    def __init__(self, settings_path: str | None = None):
        self.settings_path = settings_path or os.path.join(
            get_project_root(), "data", "settings.json"
        )
        self.values = deepcopy(DEFAULT_SETTINGS)
        self._text_renderers: weakref.WeakSet = weakref.WeakSet()
        self._current_bgm_source_volume = 1.0
        self.load()

    def load(self):
        try:
            with open(self.settings_path, "r", encoding="utf-8") as handle:
                loaded = json.load(handle)
        except (OSError, ValueError, TypeError):
            loaded = {}

        for key, default in DEFAULT_SETTINGS.items():
            value = loaded.get(key, default)
            if key in _VOLUME_KEYS or key == "text_speed":
                try:
                    value = max(0.0, min(1.0, float(value)))
                except (TypeError, ValueError):
                    value = default
            elif key == "fullscreen":
                value = bool(value)
            self.values[key] = value
        return self.values.copy()

    def save(self):
        try:
            os.makedirs(os.path.dirname(self.settings_path), exist_ok=True)
            temp_path = self.settings_path + ".tmp"
            with open(temp_path, "w", encoding="utf-8") as handle:
                json.dump(self.values, handle, ensure_ascii=False, indent=2)
            os.replace(temp_path, self.settings_path)
        except OSError as exc:
            print(f"[SETTINGS] save failed: {exc}")

    def get(self, key: str):
        return self.values[key]

    def set(self, key: str, value, *, persist: bool = True):
        if key not in DEFAULT_SETTINGS:
            raise KeyError(key)
        if key in _VOLUME_KEYS or key == "text_speed":
            value = max(0.0, min(1.0, float(value)))
        elif key == "fullscreen":
            value = bool(value)

        if self.values[key] == value:
            if persist:
                self.save()
            return

        self.values[key] = value
        self._apply_runtime_change(key)
        if persist:
            self.save()

    def reset(self):
        self.values = deepcopy(DEFAULT_SETTINGS)
        self._apply_runtime_change("master_volume")
        self._apply_runtime_change("text_speed")
        self.save()

    @property
    def music_scale(self) -> float:
        return self.values["master_volume"] * self.values["music_volume"]

    @property
    def se_scale(self) -> float:
        return self.values["master_volume"] * self.values["se_volume"]

    def text_delay_ms(self) -> int:
        span = _TEXT_DELAY_SLOWEST_MS - _TEXT_DELAY_FASTEST_MS
        return round(_TEXT_DELAY_SLOWEST_MS - span * self.values["text_speed"])

    def apply_bgm_volume(self, source_volume: float, *, remember: bool = True) -> float:
        source_volume = max(0.0, min(1.0, float(source_volume)))
        if remember:
            self._current_bgm_source_volume = source_volume
        applied = source_volume * self.music_scale
        if pygame.mixer.get_init():
            pygame.mixer.music.set_volume(applied)
        return applied

    def apply_se_channel_volume(self, channel):
        if channel is not None:
            channel.set_volume(self.se_scale)

    def register_text_renderer(self, renderer):
        self._text_renderers.add(renderer)
        renderer.set_char_delay(self.text_delay_ms())

    def _apply_runtime_change(self, key: str):
        if key in {"master_volume", "music_volume"}:
            self.apply_bgm_volume(self._current_bgm_source_volume, remember=False)
        if key in {"master_volume", "se_volume"} and pygame.mixer.get_init():
            for index in range(pygame.mixer.get_num_channels()):
                pygame.mixer.Channel(index).set_volume(self.se_scale)
        if key == "text_speed":
            delay = self.text_delay_ms()
            for renderer in list(self._text_renderers):
                renderer.set_char_delay(delay)


_settings_manager: SettingsManager | None = None


def get_settings_manager() -> SettingsManager:
    global _settings_manager
    if _settings_manager is None:
        _settings_manager = SettingsManager()
    return _settings_manager

