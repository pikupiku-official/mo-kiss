"""Small demo screens using the existing dialogue choice typography."""

import pygame

from core.runtime.subsystem_base import SubsystemBase
from menu.dialogue_choice_list import DialogueChoiceList, draw_dialogue_text_centered


def is_activity(event):
    if event.type == pygame.MOUSEMOTION:
        return any(getattr(event, "rel", (0, 0)))
    return event.type in (
        pygame.KEYDOWN, pygame.KEYUP, pygame.MOUSEBUTTONDOWN,
        pygame.MOUSEBUTTONUP, pygame.MOUSEWHEEL, pygame.TEXTINPUT,
        pygame.JOYBUTTONDOWN, pygame.FINGERDOWN,
    )


def handle_choices(choices, events):
    for event in events:
        if event.type == pygame.QUIT:
            return "quit"
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return "show_settings"
            if event.key in (pygame.K_UP, pygame.K_LEFT):
                choices.move(-1)
            elif event.key in (pygame.K_DOWN, pygame.K_RIGHT):
                choices.move(1)
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                index = choices.activate()
                if index >= 0:
                    return index
        elif event.type == pygame.MOUSEMOTION:
            choices.update_hover(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            index = choices.choice_at(event.pos)
            if index >= 0:
                return index
    return None


class ChoiceScreen(SubsystemBase):
    def __init__(self, screen, labels, actions, prompt=""):
        super().__init__(screen)
        self.choices = DialogueChoiceList(screen, labels)
        self.actions = actions
        self.prompt = prompt

    def handle_events(self, events=None):
        result = handle_choices(self.choices, events or [])
        return self.actions[result] if isinstance(result, int) else result

    def render(self):
        self.screen.fill((0, 0, 0))
        if self.prompt:
            draw_dialogue_text_centered(
                self.screen, self.choices.renderer, self.prompt,
                int(self.screen.get_height() * 0.30),
            )
        self.choices.render()

    def update(self):
        pass
