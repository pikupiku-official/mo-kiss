"""Small extensible in-game diagnostics HUD."""

from __future__ import annotations

import pygame

from core.config import SEED_INPUT_CONFIG


class DebugHud:
    def __init__(self):
        self.enabled = False

    def toggle(self):
        self.enabled = not self.enabled
        return self.enabled

    def lines_for(self, application):
        lines = []
        subsystem = getattr(application, "current_subsystem", None)
        game_state = getattr(subsystem, "game_state", None)
        if not isinstance(game_state, dict):
            return lines
        try:
            from dialogue.controller2 import is_input_blocked

            lines.append(f"INPUT BLOCKED  {str(is_input_blocked(game_state)).lower()}")
        except Exception:
            pass
        overlay = game_state.get("seed_answer_overlay")
        if overlay is not None and hasattr(overlay, "debug_lines"):
            lines.extend(overlay.debug_lines())
        else:
            seed_manager = game_state.get("seed_manager")
            if seed_manager is not None and hasattr(seed_manager, "model_status"):
                lines.append(f"MODEL          {seed_manager.model_status()}")
        return lines

    def render(self, surface, application):
        if not self.enabled:
            return
        lines = self.lines_for(application)
        if not lines:
            return
        font = pygame.font.Font(None, 25)
        color = SEED_INPUT_CONFIG["debug_color"]
        y = 10
        for line in lines:
            rendered = font.render(str(line), True, color)
            surface.blit(rendered, (10, y))
            y += rendered.get_height() + 2


_debug_hud = DebugHud()


def get_debug_hud():
    return _debug_hud
