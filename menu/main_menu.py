"""Door-based main menu shown immediately after the title screen."""

from __future__ import annotations

import os

import pygame

from core.path_utils import get_project_root
from core.runtime.subsystem_base import SubsystemBase
from core.services.save_manager import get_save_manager
from dialogue.choice_renderer import ChoiceRenderer
from dialogue.name_manager import get_name_manager
from menu.dialogue_choice_list import DialogueChoiceList, draw_dialogue_text_centered
from menu.ui_components import TextInput


DOOR_FRAME_DURATION_MS = 150
MENU_LABELS = ("はじめから", "つづきから", "設定", "終了", "家", "マップ")
MENU_ACTIONS = ("new_game", "load", "settings", "quit_confirm", "home", "map")


class MainMenu(SubsystemBase):
    MENU = "menu"
    ANIMATING = "animating"
    NAME_INPUT = "name_input"
    QUIT_CONFIRM = "quit_confirm"

    def __init__(self, screen=None, *, text_input_rect_transform=None):
        if screen is None:
            from core.config import init_game

            screen = init_game()
        super().__init__(screen)
        pygame.font.init()
        self.renderer = ChoiceRenderer(screen)
        self._door_frames = self._load_door_frames()
        self.state = self.MENU
        self._animation_started_at = None
        self._pending_action = None
        self._name_error = ""

        self.menu_choices = DialogueChoiceList(
            screen,
            MENU_LABELS,
            center_y=screen.get_height() // 2,
            row_spacing=92,
            renderer=self.renderer,
        )
        self.name_choices = DialogueChoiceList(
            screen,
            ("決定", "戻る"),
            center_y=int(screen.get_height() * 0.76),
            row_spacing=78,
            renderer=self.renderer,
        )
        self.quit_choices = DialogueChoiceList(
            screen,
            ("はい", "いいえ"),
            center_y=int(screen.get_height() * 0.58),
            row_spacing=88,
            renderer=self.renderer,
        )

        input_font = self.renderer.pygame_fonts["text"]
        input_width = 300
        input_height = 62
        input_x = screen.get_width() // 2 - input_width // 2
        self.text_inputs = {
            "surname": TextInput(
                input_x,
                int(screen.get_height() * 0.35),
                input_width,
                input_height,
                input_font,
                max_length=3,
                placeholder="苗字",
                input_rect_transform=text_input_rect_transform,
            ),
            "name": TextInput(
                input_x,
                int(screen.get_height() * 0.49),
                input_width,
                input_height,
                input_font,
                max_length=3,
                placeholder="名前",
                input_rect_transform=text_input_rect_transform,
            ),
        }

    def _load_door_frames(self):
        frames = []
        root = get_project_root()
        for index in range(4):
            path = os.path.join(root, "images", "UI", "menu", f"door{index}.png")
            try:
                image = pygame.image.load(path).convert()
            except Exception as error:
                print(f"[MAIN_MENU] 扉画像の読み込みに失敗: {path}: {error}")
                image = pygame.Surface(self.screen.get_size())
                image.fill((0, 0, 0))
            if image.get_size() != self.screen.get_size():
                image = pygame.transform.smoothscale(image, self.screen.get_size())
            frames.append(image)
        return frames

    def on_enter(self):
        self._show_menu()

    def cleanup(self):
        self._clear_input_focus()

    def _clear_input_focus(self):
        for text_input in self.text_inputs.values():
            text_input.clear_focus()

    def _show_menu(self):
        self._clear_input_focus()
        self.state = self.MENU
        self._animation_started_at = None
        self._pending_action = None
        self.menu_choices.selected_index = 0

    def _start_animation(self, action):
        if self.state != self.MENU:
            return
        self.state = self.ANIMATING
        self._pending_action = action
        self._animation_started_at = pygame.time.get_ticks()

    def _finish_animation_if_ready(self):
        if self.state != self.ANIMATING:
            return None
        elapsed = pygame.time.get_ticks() - self._animation_started_at
        if elapsed < DOOR_FRAME_DURATION_MS * 3:
            return None

        action = self._pending_action
        self._animation_started_at = None
        self._pending_action = None
        if action == "new_game":
            self._open_name_input()
            return None
        if action == "quit_confirm":
            self.state = self.QUIT_CONFIRM
            self.quit_choices.selected_index = 0
            return None
        if action == "settings":
            self._show_menu()
            return "show_settings"
        if action == "load":
            return "go_to_load"
        if action == "home":
            return "go_to_home"
        if action == "map":
            return "go_to_map"
        return None

    def _open_name_input(self):
        self.state = self.NAME_INPUT
        self._name_error = ""
        manager = get_name_manager()
        self.text_inputs["surname"].set_text(manager.get_surname())
        self.text_inputs["name"].set_text(manager.get_name())
        self.name_choices.selected_index = 0
        self._focus_input("surname")

    def _focus_input(self, name):
        for text_input in self.text_inputs.values():
            text_input.clear_focus()
        self.text_inputs[name].focus()

    def _name_length_error(self):
        for key, label in (("surname", "苗字"), ("name", "名前")):
            text_input = self.text_inputs[key]
            if len(text_input.get_text().strip()) > text_input.max_length:
                return f"{label}は{text_input.max_length}文字以内で入力してください"
        return ""

    def _confirm_new_game(self):
        surname = self.text_inputs["surname"].get_text().strip()
        name = self.text_inputs["name"].get_text().strip()
        if not surname or not name:
            self._name_error = "苗字と名前を入力してください"
            return None
        self._name_error = self._name_length_error()
        if self._name_error:
            return None
        if not get_save_manager().reset_current_state():
            self._name_error = "ゲームの初期化に失敗しました"
            return None
        get_name_manager().set_names(surname, name)
        self._clear_input_focus()
        return "new_game"

    def _activate_menu_choice(self, index):
        if 0 <= index < len(MENU_ACTIONS):
            self._start_animation(MENU_ACTIONS[index])

    def _activate_name_choice(self, index):
        if index == 0:
            return self._confirm_new_game()
        if index == 1:
            self._show_menu()
        return None

    def _activate_quit_choice(self, index):
        if index == 0:
            return "quit"
        if index == 1:
            self._show_menu()
        return None

    def handle_events(self, events=None):
        result = self._finish_animation_if_ready()
        if result is not None:
            return result
        if self.state == self.ANIMATING:
            return None

        events = pygame.event.get() if events is None else events
        for event in events:
            if event.type == pygame.QUIT:
                return "quit"
            if self.state == self.MENU:
                result = self._handle_menu_event(event)
            elif self.state == self.NAME_INPUT:
                result = self._handle_name_event(event)
            else:
                result = self._handle_quit_event(event)
            if result is not None:
                return result
        return self._finish_animation_if_ready()

    def _handle_menu_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.menu_choices.update_hover(event.pos)
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self._activate_menu_choice(self.menu_choices.choice_at(event.pos))
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.menu_choices.move(-1)
            elif event.key == pygame.K_DOWN:
                self.menu_choices.move(1)
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self._activate_menu_choice(self.menu_choices.activate())
            elif event.key == pygame.K_ESCAPE:
                self.state = self.QUIT_CONFIRM
                self.quit_choices.selected_index = 0
        return None

    def _handle_name_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if any(field.is_composing for field in self.text_inputs.values()):
                for field in self.text_inputs.values():
                    field.handle_event(event)
            else:
                self._show_menu()
            return None
        if event.type == pygame.KEYDOWN and event.key == pygame.K_TAB:
            target = "name" if self.text_inputs["surname"].is_focused else "surname"
            self._focus_input(target)
            return None

        focused_before = next(
            (key for key, field in self.text_inputs.items() if field.is_focused), None
        )
        if event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
            fields_to_handle = list(self.text_inputs.items())
        elif focused_before is not None:
            fields_to_handle = [(focused_before, self.text_inputs[focused_before])]
        else:
            fields_to_handle = []
        for key, text_input in fields_to_handle:
            field_result = text_input.handle_event(event)
            if field_result == "focus":
                for other_key, other in self.text_inputs.items():
                    if other_key != key:
                        other.clear_focus()
            elif field_result == "enter":
                if key == "surname":
                    self._focus_input("name")
                else:
                    self.name_choices.selected_index = 0
            elif field_result == "text_changed":
                self._name_error = self._name_length_error()

        if event.type == pygame.MOUSEMOTION:
            self.name_choices.update_hover(event.pos)
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            return self._activate_name_choice(self.name_choices.choice_at(event.pos))
        elif event.type == pygame.KEYDOWN and focused_before is None:
            if event.key == pygame.K_UP:
                self.name_choices.move(-1)
            elif event.key == pygame.K_DOWN:
                self.name_choices.move(1)
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                return self._activate_name_choice(self.name_choices.activate())
        return None

    def _handle_quit_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.quit_choices.update_hover(event.pos)
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            return self._activate_quit_choice(self.quit_choices.choice_at(event.pos))
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.quit_choices.move(-1)
            elif event.key == pygame.K_DOWN:
                self.quit_choices.move(1)
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                return self._activate_quit_choice(self.quit_choices.activate())
            elif event.key == pygame.K_ESCAPE:
                self._show_menu()
        return None

    def update(self):
        pass

    def draw(self):
        self.render()

    def render(self):
        if self.state == self.MENU:
            self.screen.blit(self._door_frames[0], (0, 0))
            self.menu_choices.render()
        elif self.state == self.ANIMATING:
            elapsed = pygame.time.get_ticks() - self._animation_started_at
            frame_index = min(3, elapsed // DOOR_FRAME_DURATION_MS + 1)
            self.screen.blit(self._door_frames[frame_index], (0, 0))
        elif self.state == self.NAME_INPUT:
            self._render_name_input()
        else:
            self._render_quit_confirm()

    def _render_name_input(self):
        self.screen.fill((0, 0, 0))
        draw_dialogue_text_centered(
            self.screen, self.renderer, "主人公の名前を入力してください", int(self.screen.get_height() * 0.19)
        )
        draw_dialogue_text_centered(
            self.screen, self.renderer, "苗字", int(self.screen.get_height() * 0.32)
        )
        draw_dialogue_text_centered(
            self.screen, self.renderer, "名前", int(self.screen.get_height() * 0.46)
        )
        for text_input in self.text_inputs.values():
            text_input.draw(self.screen)
        self.name_choices.render()
        if self._name_error:
            draw_dialogue_text_centered(
                self.screen,
                self.renderer,
                self._name_error,
                int(self.screen.get_height() * 0.91),
                color=self.renderer.highlight_color,
            )

    def _render_quit_confirm(self):
        self.screen.fill((0, 0, 0))
        draw_dialogue_text_centered(
            self.screen, self.renderer, "終了しますか？", int(self.screen.get_height() * 0.36)
        )
        self.quit_choices.render()


def main():
    menu = MainMenu()
    clock = pygame.time.Clock()
    running = True
    while running:
        result = menu.handle_events()
        if result == "quit":
            running = False
        menu.update()
        menu.render()
        pygame.display.flip()
        clock.tick(60)
    menu.cleanup()
    pygame.quit()


if __name__ == "__main__":
    main()
