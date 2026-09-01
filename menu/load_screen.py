"""Reusable save-slot screens for the main menu and OPTION modal."""

from __future__ import annotations

import os

import pygame

from core.runtime.subsystem_base import SubsystemBase
from core.services.save_manager import get_save_manager
from core.services.time_manager import to_zenkaku
from dialogue.choice_renderer import ChoiceRenderer
from menu.dialogue_choice_list import DialogueChoiceList, draw_dialogue_text_centered


class SaveSlotScreen(SubsystemBase):
    """Select one of the ten manual slots in save or load mode."""

    SLOT_COUNT = 10

    def __init__(
        self,
        screen: pygame.Surface,
        *,
        mode: str,
        save_manager=None,
        cancel_action: str = "go_to_menu",
        save_callback=None,
        load_callback=None,
    ):
        if mode not in {"save", "load"}:
            raise ValueError("mode must be 'save' or 'load'")
        super().__init__(screen)
        pygame.font.init()
        self.mode = mode
        self.save_manager = save_manager or get_save_manager()
        self.cancel_action = cancel_action
        self.save_callback = save_callback
        self.load_callback = load_callback
        self.renderer = ChoiceRenderer(screen)
        self.slots = []
        self.choice_list = None
        self.confirm_choices = None
        self.pending_overwrite_index = None
        self.message = ""
        self.refresh()

    def refresh(self, preferred_index: int | None = None):
        self.slots = []
        labels = []
        enabled = []
        first_empty = None
        for slot_number in range(1, self.SLOT_COUNT + 1):
            slot_name = f"saveslot_{slot_number:02d}"
            display_slot_number = to_zenkaku(f"{slot_number:02d}")
            exists = self.save_manager.has_save(slot_name)
            metadata = self.save_manager.get_save_metadata(slot_name) if exists else {}
            player_name = metadata.get("player_name", "").replace(" ", "")
            if exists:
                suffix = f"  {player_name}" if player_name else ""
                label = f"スロット{display_slot_number}{suffix}"
            else:
                label = f"スロット{display_slot_number}  データなし"
                if first_empty is None:
                    first_empty = slot_number - 1
            self.slots.append(
                {
                    "slot_name": slot_name,
                    "exists": exists,
                    "metadata": metadata,
                }
            )
            labels.append(label)
            enabled.append(self.mode == "save" or exists)

        self.choice_list = DialogueChoiceList(
            self.screen,
            labels,
            center_x=int(self.screen.get_width() * 0.31),
            center_y=int(self.screen.get_height() * 0.52),
            row_spacing=66,
            enabled=enabled,
            renderer=self.renderer,
        )
        if preferred_index is not None and 0 <= preferred_index < len(self.slots):
            if enabled[preferred_index]:
                self.choice_list.selected_index = preferred_index
        elif self.mode == "save":
            self.choice_list.selected_index = first_empty if first_empty is not None else 0
        self.confirm_choices = DialogueChoiceList(
            self.screen,
            ("はい", "いいえ"),
            center_x=int(self.screen.get_width() * 0.72),
            center_y=int(self.screen.get_height() * 0.75),
            row_spacing=72,
            renderer=self.renderer,
        )
        self.confirm_choices.selected_index = 1
        if not any(enabled):
            self.message = "ロードできるデータがありません"

    def on_enter(self):
        self.pending_overwrite_index = None
        self.refresh()

    def handle_events(self, events=None):
        events = pygame.event.get() if events is None else events
        for event in events:
            if event.type == pygame.QUIT:
                return "quit"
            if self.pending_overwrite_index is not None:
                result = self._handle_confirmation_event(event)
            else:
                result = self._handle_slot_event(event)
            if result:
                return result
        return None

    def _handle_slot_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.choice_list.update_hover(event.pos)
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            return self._activate_choice(self.choice_list.choice_at(event.pos))
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.choice_list.move(-1)
            elif event.key == pygame.K_DOWN:
                self.choice_list.move(1)
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                return self._activate_choice(self.choice_list.activate())
            elif event.key == pygame.K_ESCAPE:
                return self.cancel_action
        return None

    def _handle_confirmation_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.confirm_choices.update_hover(event.pos)
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            return self._confirm_overwrite(self.confirm_choices.choice_at(event.pos))
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.confirm_choices.move(-1)
            elif event.key == pygame.K_DOWN:
                self.confirm_choices.move(1)
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                return self._confirm_overwrite(self.confirm_choices.activate())
            elif event.key == pygame.K_ESCAPE:
                self.pending_overwrite_index = None
                self.confirm_choices.selected_index = 1
        return None

    def _activate_choice(self, index):
        if not 0 <= index < len(self.slots):
            return None
        slot = self.slots[index]
        if self.mode == "load":
            return self._load_choice(index)
        if slot["exists"]:
            self.pending_overwrite_index = index
            self.confirm_choices.selected_index = 1
            return None
        return self._save_choice(index)

    def _confirm_overwrite(self, confirmation_index):
        if confirmation_index == 0:
            index = self.pending_overwrite_index
            self.pending_overwrite_index = None
            return self._save_choice(index)
        if confirmation_index == 1:
            self.pending_overwrite_index = None
            self.confirm_choices.selected_index = 1
        return None

    def _save_choice(self, index):
        slot_name = self.slots[index]["slot_name"]
        saver = self.save_callback or self.save_manager.save_game
        if saver(slot_name):
            self.refresh(preferred_index=index)
            return f"save_complete:{slot_name}"
        self.message = "セーブに失敗しました"
        return None

    def _load_choice(self, index):
        if not 0 <= index < len(self.slots) or not self.slots[index]["exists"]:
            return None
        slot_name = self.slots[index]["slot_name"]
        loader = self.load_callback or self.save_manager.load_game
        if loader(slot_name):
            return f"load_complete:{slot_name}" if self.load_callback else "continue_game"
        self.message = "ロードに失敗しました"
        return None

    def update(self):
        pass

    def render(self):
        self.screen.fill((0, 0, 0))
        title = "セーブ" if self.mode == "save" else "ロード"
        draw_dialogue_text_centered(
            self.screen, self.renderer, title, int(self.screen.get_height() * 0.08)
        )
        self.choice_list.render()
        self._render_selected_details()
        if self.message:
            draw_dialogue_text_centered(
                self.screen,
                self.renderer,
                self.message,
                int(self.screen.get_height() * 0.94),
                color=self.renderer.highlight_color,
            )
        if self.pending_overwrite_index is not None:
            self._render_overwrite_confirmation()

    def _render_selected_details(self):
        selected = self.choice_list.selected_index
        if not 0 <= selected < len(self.slots):
            return
        slot = self.slots[selected]
        preview_rect = self._preview_rect()
        pygame.draw.rect(self.screen, (18, 18, 26), preview_rect)
        pygame.draw.rect(self.screen, (180, 180, 220), preview_rect, 2)
        thumbnail_path = os.path.join(
            self.save_manager.save_dir, slot["slot_name"], "thumbnail.png"
        )
        if slot["exists"] and os.path.exists(thumbnail_path):
            try:
                thumbnail = pygame.image.load(thumbnail_path).convert()
                thumbnail = pygame.transform.smoothscale(thumbnail, preview_rect.size)
                self.screen.blit(thumbnail, preview_rect.topleft)
            except pygame.error:
                pass
        metadata = slot["metadata"]
        detail_lines = [
            metadata.get("player_name", ""),
            metadata.get("game_year", ""),
            metadata.get("game_date_period", ""),
        ]
        if not any(detail_lines[1:]):
            detail_lines.append(metadata.get("game_time", ""))
        y = preview_rect.bottom + 54
        for detail in (line for line in detail_lines if line):
            self._draw_detail_centered(detail, preview_rect.centerx, y)
            y += 58

    def _preview_rect(self):
        preview_width = int(self.screen.get_width() * 0.34) // 4 * 4
        preview_height = preview_width * 3 // 4
        return pygame.Rect(
            int(self.screen.get_width() * 0.61),
            int(self.screen.get_height() * 0.18),
            preview_width,
            preview_height,
        )

    def _draw_detail_centered(self, text, center_x, center_y):
        surface = self.renderer._render_choice_with_grid_system(
            text, self.renderer.normal_color
        )
        bounds = DialogueChoiceList._visible_bounds(surface)
        self.screen.blit(
            surface,
            (
                center_x - bounds.width // 2 - bounds.x,
                center_y - bounds.height // 2 - bounds.y,
            ),
        )

    def _render_overwrite_confirmation(self):
        panel = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 190))
        self.screen.blit(panel, (0, 0))
        slot_number = self.pending_overwrite_index + 1
        display_slot_number = to_zenkaku(f"{slot_number:02d}")
        draw_dialogue_text_centered(
            self.screen,
            self.renderer,
            f"スロット{display_slot_number}に上書きしますか？",
            int(self.screen.get_height() * 0.60),
        )
        self.confirm_choices.render()


class LoadScreen(SaveSlotScreen):
    """Main-menu load screen kept as a compatibility entry point."""

    def __init__(self, screen: pygame.Surface, save_manager=None):
        super().__init__(
            screen,
            mode="load",
            save_manager=save_manager,
            cancel_action="go_to_menu",
        )


class SaveScreen(SaveSlotScreen):
    """Reusable manual save screen."""

    def __init__(self, screen: pygame.Surface, save_manager=None, **kwargs):
        super().__init__(screen, mode="save", save_manager=save_manager, **kwargs)
