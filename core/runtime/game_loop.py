"""Pygame frame orchestration for the game application."""

import traceback

import pygame

from core.config import DEBUG


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

        if getattr(app, "slot_screen", None):
            self._run_slot_frame(events)
        elif app.option_subsystem:
            self._run_option_frame(events)
        elif app.current_subsystem:
            if self._run_mock_shortcut_frame(events):
                return
            self._run_subsystem_frame(events)

        app._present_virtual_screen()
        pygame.display.flip()
        has_modal = app.option_subsystem or getattr(app, "slot_screen", None)
        app.clock.tick(60 if has_modal else 30)

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
