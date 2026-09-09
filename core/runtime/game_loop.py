"""Pygame frame orchestration for the game application."""

import traceback

import pygame

from core.config import DEBUG, SEED_INPUT_CONFIG, get_configured_key
from core.ui.debug_hud import get_debug_hud


class GameLoop:
    """Drive input, updates, rendering, and presentation for one application."""

    def __init__(self, application, *, dialogue_type):
        self.application = application
        self._dialogue_type = dialogue_type

    def run(self) -> None:
        while self.application.running:
            try:
                self.run_frame()
            except Exception as exc:
                print(f"❌ ゲームループエラー: {exc}")
                if DEBUG:
                    traceback.print_exc()
                break

    def run_frame(self) -> None:
        app = self.application
        events = app._gather_normalized_events()
        self._handle_debug_shortcut(events)
        self._handle_seed_list_shortcut(events)

        if getattr(app, "slot_screen", None):
            self._run_slot_frame(events)
        elif app.option_subsystem:
            self._run_option_frame(events)
        elif app.current_subsystem:
            if self._run_mock_shortcut_frame(events):
                return
            self._run_subsystem_frame(events)

        virtual_screen = getattr(app, "virtual_screen", None)
        if virtual_screen is not None:
            get_debug_hud().render(virtual_screen, app)
        app._present_virtual_screen()
        pygame.display.flip()
        has_modal = app.option_subsystem or getattr(app, "slot_screen", None)
        app.clock.tick(60 if has_modal else 30)

    def _handle_debug_shortcut(self, events) -> None:
        """F8 is global, except while an IME composition owns that key."""
        app = self.application
        subsystem = getattr(app, "current_subsystem", None)
        game_state = getattr(subsystem, "game_state", {})
        seed_input = (
            game_state.get("seed_answer_overlay")
            if isinstance(game_state, dict)
            else None
        )
        composing = bool(seed_input and getattr(seed_input, "is_composing", False))
        if (
            not composing
            and getattr(subsystem, "state", None)
            == getattr(subsystem, "NAME_INPUT", None)
        ):
            composing = any(
                field.is_composing
                for field in getattr(subsystem, "text_inputs", {}).values()
            )

        remaining = []
        for event in events:
            if (
                not composing
                and getattr(event, "type", None) == pygame.KEYDOWN
                and getattr(event, "key", None)
                == get_configured_key(SEED_INPUT_CONFIG['debug_toggle_key'])
                and not getattr(event, "repeat", False)
            ):
                get_debug_hud().toggle()
                continue
            remaining.append(event)
        events[:] = remaining

    def _handle_seed_list_shortcut(self, events) -> None:
        """Route F9 before the legacy Dialogue event queue can consume it."""
        app = self.application
        subsystem = getattr(app, "current_subsystem", None)
        game_state = getattr(subsystem, "game_state", None)
        if not isinstance(game_state, dict):
            return
        seed_list = game_state.get("seed_list_overlay")
        if seed_list is None:
            return
        seed_input = game_state.get("seed_answer_overlay")
        composing = bool(seed_input and getattr(seed_input, "is_composing", False))
        composing = composing or any(
            getattr(event, "type", None) == pygame.TEXTEDITING
            and bool(getattr(event, "text", ""))
            for event in events
        )
        remaining = []
        for event in events:
            if (
                not composing
                and getattr(event, "type", None) == pygame.KEYDOWN
                and getattr(event, "key", None)
                == get_configured_key(SEED_INPUT_CONFIG["seed_list_key"])
                and not getattr(event, "repeat", False)
            ):
                showing = seed_list.toggle()
                backlog = game_state.get("backlog_manager")
                if showing and backlog is not None and backlog.is_showing_backlog():
                    backlog.toggle_backlog()
                if seed_input is not None:
                    if showing:
                        seed_input.suspend()
                    elif not game_state.get("seed_system_message"):
                        seed_input.resume()
                continue
            remaining.append(event)
        events[:] = remaining

    def _run_slot_frame(self, events) -> None:
        app = self.application
        slot_result = app.slot_screen.handle_events(events)
        if slot_result:
            app._handle_slot_result(slot_result)

        if app.slot_screen:
            app.slot_screen.render()
        elif app.option_subsystem:
            self._render_option()
        elif app.current_subsystem:
            app.current_subsystem.render()

    def _run_option_frame(self, events) -> None:
        app = self.application
        app._poll_mock_overlay_shortcuts(events)
        # OPTION pauses subsystem updates while its BGM keeps playing.
        result = app.option_subsystem.handle_events(events)
        if result:
            app._handle_overlay_result(result)
        if app.current_subsystem:
            app.current_subsystem.render()
        if app.option_subsystem:
            app.option_subsystem.render_overlay()
            app._render_option_notice()

    def _render_option(self) -> None:
        app = self.application
        if app.current_subsystem:
            app.current_subsystem.render()
        app.option_subsystem.render_overlay()
        app._render_option_notice()

    def _run_mock_shortcut_frame(self, events) -> bool:
        app = self.application
        if not app._poll_mock_overlay_shortcuts(events):
            return False
        if app.current_subsystem:
            app.current_subsystem.render()
        if app.option_subsystem:
            app.option_subsystem.render_overlay()
        virtual_screen = getattr(app, "virtual_screen", None)
        if virtual_screen is not None:
            get_debug_hud().render(virtual_screen, app)
        app._present_virtual_screen()
        pygame.display.flip()
        app.clock.tick(60)
        return True

    def _run_subsystem_frame(self, events) -> None:
        app = self.application
        if isinstance(app.current_subsystem, self._dialogue_type):
            app._queue_events_for_dialogue(events)
            result = app.current_subsystem.handle_events()
        else:
            result = app.current_subsystem.handle_events(events)
        if result:
            app._handle_transition(result)
        if app.current_subsystem:
            app.current_subsystem.update()
        if app.current_subsystem:
            app.current_subsystem.render()
