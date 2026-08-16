"""Reusable load-only save slot screen."""

from __future__ import annotations

import pygame

from core.runtime.subsystem_base import SubsystemBase
from core.services.save_manager import get_save_manager
from dialogue.choice_renderer import ChoiceRenderer
from menu.dialogue_choice_list import DialogueChoiceList, draw_dialogue_text_centered


class LoadScreen(SubsystemBase):
    """Load one of the ten standard slots and resume its saved base state."""

    def __init__(self, screen: pygame.Surface, save_manager=None):
        super().__init__(screen)
        pygame.font.init()
        self.save_manager = save_manager or get_save_manager()
        self.renderer = ChoiceRenderer(screen)
        self.slots = []
        self.choice_list = None
        self.message = ""
        self.refresh()

    def refresh(self):
        self.slots = []
        labels = []
        enabled = []
        for slot_number in range(1, 11):
            slot_name = f"saveslot_{slot_number:02d}"
            exists = self.save_manager.has_save(slot_name)
            metadata = self.save_manager.get_save_metadata(slot_name) if exists else {}
            player_name = metadata.get("player_name", "").replace(" ", "")
            if exists:
                suffix = f"　{player_name}" if player_name else ""
                label = f"スロット{slot_number:02d}{suffix}"
            else:
                label = f"スロット{slot_number:02d}　データなし"
            self.slots.append(
                {
                    "slot_name": slot_name,
                    "exists": exists,
                    "metadata": metadata,
                }
            )
            labels.append(label)
            enabled.append(exists)
        self.choice_list = DialogueChoiceList(
            self.screen,
            labels,
            center_y=int(self.screen.get_height() * 0.49),
            row_spacing=70,
            enabled=enabled,
            renderer=self.renderer,
        )
        self.message = "" if any(enabled) else "ロードできるデータがありません"

    def on_enter(self):
        self.refresh()

    def handle_events(self, events=None):
        events = pygame.event.get() if events is None else events
        for event in events:
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.MOUSEMOTION:
                self.choice_list.update_hover(event.pos)
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                result = self._load_choice(self.choice_list.choice_at(event.pos))
                if result:
                    return result
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    self.choice_list.move(-1)
                elif event.key == pygame.K_DOWN:
                    self.choice_list.move(1)
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    result = self._load_choice(self.choice_list.activate())
                    if result:
                        return result
                elif event.key == pygame.K_ESCAPE:
                    return "go_to_menu"
        return None

    def _load_choice(self, index):
        if not 0 <= index < len(self.slots) or not self.slots[index]["exists"]:
            return None
        slot_name = self.slots[index]["slot_name"]
        if self.save_manager.load_game(slot_name):
            return "continue_game"
        self.message = "ロードに失敗しました"
        return None

    def update(self):
        pass

    def render(self):
        self.screen.fill((0, 0, 0))
        draw_dialogue_text_centered(
            self.screen, self.renderer, "つづきから", int(self.screen.get_height() * 0.09)
        )
        self.choice_list.render()
        selected = self.choice_list.selected_index
        if 0 <= selected < len(self.slots):
            metadata = self.slots[selected]["metadata"]
            detail = metadata.get("game_time") or metadata.get("save_date") or ""
            if detail:
                draw_dialogue_text_centered(
                    self.screen, self.renderer, detail, int(self.screen.get_height() * 0.88)
                )
        if self.message:
            draw_dialogue_text_centered(
                self.screen,
                self.renderer,
                self.message,
                int(self.screen.get_height() * 0.94),
                color=self.renderer.highlight_color,
            )

