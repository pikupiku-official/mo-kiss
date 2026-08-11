"""Pygame window, viewport, and input-coordinate management."""

from __future__ import annotations

import pygame

from core import config


class WindowController:
    """Own the real window while presenting a fixed-size virtual screen."""

    def __init__(self, window_surface: pygame.Surface, virtual_screen: pygame.Surface):
        self.window_surface = window_surface
        self.virtual_screen = virtual_screen
        self.is_fullscreen = bool(window_surface.get_flags() & pygame.FULLSCREEN)
        self.windowed_size = None if self.is_fullscreen else window_surface.get_size()

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
            if event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                if not getattr(event, "repeat", False):
                    self.toggle_fullscreen()
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
