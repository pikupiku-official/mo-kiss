"""Modal OPTION behavior separated from overlay rendering."""

from __future__ import annotations

from enum import Enum

import pygame

from core.ui.option_overlay import (
    MockOptionOverlay,
    OptionImageOverlay,
    OptionOverlay,
    SettingsFaderOverlay,
)


MOCK_AWAIT_FRAMES = ("UI_await01.png", "UI_await02.png", "UI_await03.png")
_DIRECTION_AMOUNTS = {
    pygame.K_RIGHT: 1,
    pygame.K_DOWN: 2,
    pygame.K_LEFT: -1,
    pygame.K_UP: -2,
}
_HELD_DIRECTION_INITIAL_DELAY_MS = 250
_HELD_DIRECTION_REPEAT_MS = 100


class OptionAction(str, Enum):
    RESUME = "resume"
    SAVE = "save"
    LOAD = "load"
    RETURN_TO_MORNING = "return_to_morning"
    GO_TO_MENU = "go_to_menu"
    QUIT = "quit"

    @classmethod
    def from_value(cls, value):
        if value is None or isinstance(value, cls):
            return value
        return cls(value)


class OptionSubsystem:
    """Own modal input/state while an overlay remains the visual frontend."""

    def __init__(self, screen, overlay, fullscreen_callback=None):
        self.screen = screen
        self.overlay = overlay
        self._fullscreen_callback = fullscreen_callback
        self._held_direction_key = None
        self._next_direction_repeat_at_ms = None

    @classmethod
    def standard(cls, screen, parent_mode):
        return cls(screen, OptionOverlay(screen, parent_mode))

    @classmethod
    def image_option(cls, screen, fullscreen_callback=None):
        return cls(
            screen,
            OptionImageOverlay(screen),
            fullscreen_callback=fullscreen_callback,
        )

    @classmethod
    def settings(cls, screen, fullscreen_callback=None):
        return cls(
            screen,
            SettingsFaderOverlay(
                screen,
                fullscreen_callback=fullscreen_callback,
            ),
            fullscreen_callback=fullscreen_callback,
        )

    @classmethod
    def await_sequence(cls, screen):
        return cls(screen, MockOptionOverlay(screen, MOCK_AWAIT_FRAMES))

    def handle_events(self, events) -> OptionAction | None:
        """Interpret modal input; overlays only expose visual hit/state helpers."""
        for event in events:
            if event.type == pygame.QUIT:
                return OptionAction.QUIT

        if isinstance(self.overlay, OptionOverlay):
            return self._handle_standard_option(events)
        if isinstance(self.overlay, OptionImageOverlay):
            return self._handle_image_option(events)
        if isinstance(self.overlay, SettingsFaderOverlay):
            return self._handle_settings_fader(events)
        if isinstance(self.overlay, MockOptionOverlay):
            if self.overlay.is_close_animation_finished():
                return OptionAction.RESUME
        return None

    def render_overlay(self):
        self.overlay.render_overlay()

    def poll_mock_shortcuts(self, events) -> bool:
        """Consume F6/F7 and switch the corresponding visual frontend."""
        if (
            isinstance(self.overlay, OptionImageOverlay)
            and self.overlay.is_move_animating
            and not self.overlay.finish_move_animation_if_elapsed()
        ):
            had_shortcut = any(
                event.type == pygame.KEYDOWN
                and event.key in (pygame.K_F6, pygame.K_F7)
                for event in events
            )
            events[:] = [
                event
                for event in events
                if not (
                    event.type == pygame.KEYDOWN
                    and event.key in (pygame.K_F6, pygame.K_F7)
                )
            ]
            return had_shortcut

        shortcut_key = None
        remaining_events = []
        for event in events:
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_F6, pygame.K_F7):
                shortcut_key = event.key
                continue
            remaining_events.append(event)
        events[:] = remaining_events

        if shortcut_key is None:
            return False

        if isinstance(self.overlay, OptionImageOverlay):
            if shortcut_key == pygame.K_F6:
                self._clear_held_direction()
                self.overlay.start_close()
            else:
                self._clear_held_direction()
                self.overlay = MockOptionOverlay(self.screen, MOCK_AWAIT_FRAMES)
            return True

        if isinstance(self.overlay, SettingsFaderOverlay):
            self.overlay.start_close()
            return True

        if isinstance(self.overlay, MockOptionOverlay):
            if shortcut_key == pygame.K_F7 and self.overlay.is_same_sequence(
                MOCK_AWAIT_FRAMES
            ):
                self.overlay.start_close()
            elif shortcut_key == pygame.K_F6:
                self._clear_held_direction()
                self.overlay = OptionImageOverlay(self.screen)
            else:
                self.overlay = MockOptionOverlay(self.screen, MOCK_AWAIT_FRAMES)
            return True

        return False

    def _handle_standard_option(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return OptionAction.RESUME
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                return OptionAction.from_value(self.overlay.action_at(event.pos))
        return None

    def _handle_image_option(self, events):
        now = pygame.time.get_ticks()

        focus_lost_type = getattr(pygame, "WINDOWFOCUSLOST", None)
        if focus_lost_type is not None and any(
            event.type == focus_lost_type for event in events
        ):
            self._clear_held_direction()
        self._sync_held_direction_with_keyboard()

        if (
            self.overlay.is_move_animating
            and not self.overlay.finish_move_animation_if_elapsed()
        ):
            # KEYUP is honored even while visual movement is locked. All
            # KEYDOWN events are discarded, so no input can be queued here.
            for event in events:
                if (
                    event.type == pygame.KEYUP
                    and event.key == self._held_direction_key
                ):
                    self._clear_held_direction()
            return None

        if self.overlay.is_closing:
            if self.overlay.is_close_animation_finished():
                return OptionAction.RESUME
            return None

        move_delta = 0
        has_move = False
        requested_action = None
        for event in events:
            if event.type == pygame.KEYUP:
                if event.key == self._held_direction_key:
                    self._clear_held_direction()
                continue
            if event.type != pygame.KEYDOWN:
                continue
            if event.key in _DIRECTION_AMOUNTS:
                if getattr(event, "repeat", False):
                    continue
                # Ignore OS-generated repeat KEYDOWNs. Held movement is driven
                # from the monotonic clock below, so it can never build a queue.
                if event.key == self._held_direction_key:
                    continue
                self._held_direction_key = event.key
                self._next_direction_repeat_at_ms = (
                    now + _HELD_DIRECTION_INITIAL_DELAY_MS
                )
                move_delta += _DIRECTION_AMOUNTS[event.key]
                has_move = True
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                if not has_move:
                    requested_action = self.overlay.activate_selection()
            elif event.key == pygame.K_ESCAPE:
                self._clear_held_direction()
                self.overlay.start_close()
                return None

        if has_move:
            # Independent taps collected in one frame are collapsed to their
            # final selection. Only one visual dip is started, so no backlog
            # can be replayed after the user releases the key.
            self.overlay.move_selection(move_delta)
            return None
        if requested_action is not None:
            if requested_action == "settings":
                self._clear_held_direction()
                self.overlay = SettingsFaderOverlay(
                    self.screen,
                    fullscreen_callback=self._fullscreen_callback,
                )
                return None
            return OptionAction.from_value(requested_action)

        if (
            self._held_direction_key is not None
            and self._next_direction_repeat_at_ms is not None
            and now >= self._next_direction_repeat_at_ms
        ):
            self.overlay.move_selection(
                _DIRECTION_AMOUNTS[self._held_direction_key]
            )
            # Schedule from now rather than catching up missed intervals. A
            # slow frame therefore causes at most one move, never a late burst.
            self._next_direction_repeat_at_ms = (
                now + _HELD_DIRECTION_REPEAT_MS
            )
        return None

    def _handle_settings_fader(self, events):
        if self.overlay.is_closing:
            if self.overlay.is_close_animation_finished():
                return OptionAction.RESUME
            return None

        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.overlay.start_close()
                continue
            if event.type == pygame.MOUSEMOTION:
                self.overlay.update_hover(event.pos)
                if self.overlay.dragging_fader is not None:
                    self.overlay.drag_to(event.pos)
                continue
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self.overlay.end_drag()
                continue
            if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
                continue

            action = self.overlay.action_at(event.pos)
            if action == "resume":
                self.overlay.start_close()
            elif action == "reset":
                self.overlay.reset_to_defaults()
            else:
                self.overlay.begin_drag(event.pos)
        return None

    def _clear_held_direction(self):
        self._held_direction_key = None
        self._next_direction_repeat_at_ms = None

    def _sync_held_direction_with_keyboard(self):
        """Use current physical state as the authority when the window is focused."""
        if self._held_direction_key is None or not pygame.key.get_focused():
            return
        pressed = pygame.key.get_pressed()
        if not pressed[self._held_direction_key]:
            self._clear_held_direction()
