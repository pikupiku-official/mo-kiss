"""Reuse HOME art/transitions, with only bed and sleep enabled."""

from home.home import HomeModule
from dialogue.choice_renderer import ChoiceRenderer


class _HomeChoices(ChoiceRenderer):
    """Keep HOME's exact choice layout while disabling selected entries."""

    def __init__(self, screen):
        self.enabled = []
        self.disabled_labels = set()
        super().__init__(screen)

    def _render_choice_with_grid_system(self, choice_text, color):
        if choice_text in self.disabled_labels:
            color = (105, 105, 105)
        return super()._render_choice_with_grid_system(choice_text, color)

    def handle_mouse_motion(self, pos):
        super().handle_mouse_motion(pos)
        if self.hovered_choice >= 0 and not self.enabled[self.hovered_choice]:
            self.hovered_choice = -1

    def handle_mouse_click(self, pos):
        for index, rect in enumerate(self.choice_rects):
            if rect.collidepoint(pos) and not self.enabled[index]:
                return -1
        return super().handle_mouse_click(pos)


class GDHome(HomeModule):
    def on_enter(self):
        self._transition = None
        self._show_main_choices()

    def _show_choices(self, choices):
        renderer = self._get_choice_renderer()
        renderer.enabled = [action in (self.BED, "sleep", "back") for _, action in choices]
        renderer.disabled_labels = {
            text for (text, _), enabled in zip(choices, renderer.enabled) if not enabled
        }
        super()._show_choices(choices)

    def _get_choice_renderer(self):
        if self._choice_renderer is None:
            self._choice_renderer = _HomeChoices(self.screen)
        return self._choice_renderer

    def _move_choice(self, key):
        if self._phase == self.MAIN:
            self._get_choice_renderer().hovered_choice = 0
            self.selected_choice = 0
        else:
            super()._move_choice(key)

    def _activate_choice(self, index):
        if not 0 <= index < len(self._choice_actions):
            return None
        action = self._choice_actions[index]
        if action not in (self.BED, "sleep", "back"):
            return None
        if action == "sleep":
            return "demo_next"
        return super()._activate_choice(index)

