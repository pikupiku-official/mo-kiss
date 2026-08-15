"""Pygame window, viewport, and input-coordinate management."""

from __future__ import annotations

from pathlib import Path

import pygame

from core import config


class WindowController:
    """Own the real window while presenting a fixed-size virtual screen."""

    POINTER_PATH = Path(__file__).resolve().parents[2] / "images" / "UI" / "pointer.png"
    POINTER_HOTSPOT = (0, 0)
    POINTER_IDLE_DELAY_MS = 700
    POINTER_FADE_MS = 400

    def __init__(self, window_surface: pygame.Surface, virtual_screen: pygame.Surface):
        self.window_surface = window_surface
        self.virtual_screen = virtual_screen
        self.is_fullscreen = bool(window_surface.get_flags() & pygame.FULLSCREEN)
        self.windowed_size = None if self.is_fullscreen else window_surface.get_size()
        self.pointer_image = self._load_pointer_image()
        self._scaled_pointer = None
        self._scaled_pointer_key = None
        self._pointer_last_position = None
        self._pointer_last_activity_ms = pygame.time.get_ticks()
        if self.pointer_image is not None:
            try:
                pygame.mouse.set_visible(False)
            except pygame.error:
                pass

    def _load_pointer_image(self):
        """Load the pointer at full size, trimming only transparent padding."""
        try:
            source = pygame.image.load(str(self.POINTER_PATH))
            content_rect = source.get_bounding_rect(min_alpha=16)
            if content_rect.width <= 0 or content_rect.height <= 0:
                raise ValueError("pointer image has no visible pixels")
            cropped = source.subsurface(content_rect).copy()
            tip_pixels = [
                x
                for x in range(cropped.get_width())
                if cropped.get_at((x, 0)).a >= 16
            ]
            if tip_pixels:
                self.POINTER_HOTSPOT = (round(sum(tip_pixels) / len(tip_pixels)), 0)
            return cropped
        except (OSError, ValueError, pygame.error) as exc:
            print(f"[POINTER] failed to load {self.POINTER_PATH}: {exc}")
            return None

    def normalize_event(self, event):
        """Convert real-window mouse coordinates to virtual-screen coordinates."""
        if event.type not in (
            pygame.MOUSEMOTION,
            pygame.MOUSEBUTTONDOWN,
            pygame.MOUSEBUTTONUP,
        ):
            return event

        attrs = event.dict.copy()
        if "pos" in attrs:
            attrs["pos"] = config.window_to_virtual_pos(attrs["pos"])
        if event.type == pygame.MOUSEMOTION and "rel" in attrs:
            rel_x, rel_y = attrs["rel"]
            scale_x = (
                config.WINDOW_CONTENT_WIDTH / config.VIRTUAL_WIDTH
                if config.WINDOW_CONTENT_WIDTH
                else 1
            )
            scale_y = (
                config.WINDOW_CONTENT_HEIGHT / config.VIRTUAL_HEIGHT
                if config.WINDOW_CONTENT_HEIGHT
                else 1
            )
            attrs["rel"] = (
                int(rel_x / scale_x) if scale_x else 0,
                int(rel_y / scale_y) if scale_y else 0,
            )
        return pygame.event.Event(event.type, attrs)

    def gather_normalized_events(self):
        """Collect events and consume window-management shortcuts/events."""
        events = []
        for event in pygame.event.get():
            if event.type in (
                pygame.MOUSEMOTION,
                pygame.MOUSEBUTTONDOWN,
                pygame.MOUSEBUTTONUP,
                pygame.MOUSEWHEEL,
            ):
                self._mark_pointer_active(getattr(event, "pos", None))
            if event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                if not getattr(event, "repeat", False):
                    self.toggle_fullscreen()
                    from core.services.settings_manager import get_settings_manager
                    get_settings_manager().set("fullscreen", self.is_fullscreen)
                continue
            if event.type == pygame.VIDEORESIZE:
                self.handle_resize_event(event)
                continue
            events.append(self.normalize_event(event))
        return events

    def present_virtual_screen(self):
        """Scale and letterbox the virtual screen onto the real window."""
        self.window_surface.fill((0, 0, 0))
        scaled = pygame.transform.smoothscale(
            self.virtual_screen,
            (config.WINDOW_CONTENT_WIDTH, config.WINDOW_CONTENT_HEIGHT),
        )
        self.window_surface.blit(
            scaled,
            (config.WINDOW_OFFSET_X, config.WINDOW_OFFSET_Y),
        )
        self._draw_pointer()

    def _draw_pointer(self):
        """Draw the pointer with its fingertip fixed to the real mouse position."""
        if self.pointer_image is None:
            return

        mouse_position = pygame.mouse.get_pos()
        if mouse_position != self._pointer_last_position:
            self._mark_pointer_active(mouse_position)

        idle_ms = pygame.time.get_ticks() - self._pointer_last_activity_ms
        if idle_ms <= self.POINTER_IDLE_DELAY_MS:
            opacity = 255
        else:
            fade_elapsed = idle_ms - self.POINTER_IDLE_DELAY_MS
            opacity = max(
                0,
                round(255 * (1 - fade_elapsed / self.POINTER_FADE_MS)),
            )
        if opacity <= 0:
            return

        scale_x = config.WINDOW_CONTENT_WIDTH / config.VIRTUAL_WIDTH
        scale_y = config.WINDOW_CONTENT_HEIGHT / config.VIRTUAL_HEIGHT
        pointer_scale = max(0.01, min(scale_x, scale_y))
        source_width, source_height = self.pointer_image.get_size()
        pointer_size = (
            max(1, round(source_width * pointer_scale)),
            max(1, round(source_height * pointer_scale)),
        )

        if pointer_size != self._scaled_pointer_key:
            self._scaled_pointer = pygame.transform.smoothscale(
                self.pointer_image,
                pointer_size,
            )
            self._scaled_pointer_key = pointer_size
        self._scaled_pointer.set_alpha(opacity)

        mouse_x, mouse_y = mouse_position
        hotspot_x = round(self.POINTER_HOTSPOT[0] * pointer_scale)
        hotspot_y = round(self.POINTER_HOTSPOT[1] * pointer_scale)
        self.window_surface.blit(
            self._scaled_pointer,
            (mouse_x - hotspot_x, mouse_y - hotspot_y),
        )

    def _mark_pointer_active(self, position=None):
        """Make the pointer visible again after movement or a mouse click."""
        if position is not None:
            self._pointer_last_position = position
        self._pointer_last_activity_ms = pygame.time.get_ticks()

    def handle_resize_event(self, event):
        """Apply a resizable-window event without leaving fullscreen."""
        if self.is_fullscreen:
            width, height = self.window_surface.get_size()
            config._recalculate_screen_metrics(width, height)
            return

        config._recalculate_screen_metrics(event.w, event.h)
        self.window_surface = pygame.display.set_mode(
            (config.WINDOW_SURFACE_WIDTH, config.WINDOW_SURFACE_HEIGHT),
            pygame.RESIZABLE,
        )
        self.windowed_size = self.window_surface.get_size()
        print(
            f"[WINDOW] resized -> {config.WINDOW_SURFACE_WIDTH}x{config.WINDOW_SURFACE_HEIGHT} "
            f"(content {config.WINDOW_CONTENT_WIDTH}x{config.WINDOW_CONTENT_HEIGHT})"
        )

    def toggle_fullscreen(self):
        """Toggle fullscreen mode while remembering the windowed size."""
        if self.is_fullscreen:
            width, height = self.windowed_size or (
                config.WINDOW_WIDTH,
                config.WINDOW_HEIGHT,
            )
            self.window_surface = pygame.display.set_mode(
                (width, height),
                pygame.RESIZABLE,
            )
            self.is_fullscreen = False
        else:
            self.windowed_size = self.window_surface.get_size()
            self.window_surface = pygame.display.set_mode(
                (0, 0),
                pygame.FULLSCREEN,
            )
            self.is_fullscreen = True

        width, height = self.window_surface.get_size()
        config._recalculate_screen_metrics(width, height)
        mode = "fullscreen" if self.is_fullscreen else "windowed"
        print(f"[WINDOW] {mode} -> {width}x{height}")

    def set_fullscreen(self, enabled: bool):
        """Set an explicit display mode without toggling an already matching state."""
        if bool(enabled) != self.is_fullscreen:
            self.toggle_fullscreen()
