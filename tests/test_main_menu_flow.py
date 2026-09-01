"""Door main menu, name entry, reusable load screen, and settings routing."""

import os
import unittest
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from core.flow.game_flow import Navigate, Scene, ShowSettings, normalize_flow_request
from core.ui.option_subsystem import OptionAction, OptionSubsystem
from menu.load_screen import LoadScreen
from menu.main_menu import DOOR_FRAME_DURATION_MS, MENU_LABELS, MainMenu
from menu.ui_components import TextInput


class MainMenuFlowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        cls.screen = pygame.display.set_mode((1440, 1080))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def setUp(self):
        self.menu = MainMenu(self.screen)
        self.menu.on_enter()

    def tearDown(self):
        self.menu.cleanup()

    def test_six_choices_are_one_centered_column(self):
        self.assertEqual(self.menu.menu_choices.choices, list(MENU_LABELS))
        self.assertTrue(
            all(rect.centerx == self.screen.get_width() // 2 for rect in self.menu.menu_choices.rects)
        )
        centers = [rect.centery for rect in self.menu.menu_choices.rects]
        self.assertEqual(centers, sorted(centers))

    def test_door_animation_locks_input_and_routes_after_450_ms(self):
        with patch("pygame.time.get_ticks", return_value=1000):
            self.menu._start_animation("load")
        self.assertEqual(self.menu.state, MainMenu.ANIMATING)

        with patch(
            "pygame.time.get_ticks",
            return_value=1000 + DOOR_FRAME_DURATION_MS * 3 - 1,
        ):
            self.assertIsNone(
                self.menu.handle_events(
                    [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)]
                )
            )
            self.assertEqual(self.menu.state, MainMenu.ANIMATING)

        with patch(
            "pygame.time.get_ticks",
            return_value=1000 + DOOR_FRAME_DURATION_MS * 3,
        ):
            self.assertEqual(self.menu.handle_events([]), "go_to_load")

    def test_escape_opens_black_quit_confirmation(self):
        self.menu.handle_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)])
        self.assertEqual(self.menu.state, MainMenu.QUIT_CONFIRM)
        self.assertEqual(self.menu.quit_choices.choices, ["はい", "いいえ"])

    def test_name_confirmation_resets_state_before_saving_name(self):
        calls = []

        class FakeSaveManager:
            def reset_current_state(self):
                calls.append("reset")
                return True

        class FakeNameManager:
            def set_names(self, surname, name):
                calls.append(("set_names", surname, name))

        self.menu.text_inputs["surname"].set_text("山田")
        self.menu.text_inputs["name"].set_text("太郎")
        with patch("menu.main_menu.get_save_manager", return_value=FakeSaveManager()), patch(
            "menu.main_menu.get_name_manager", return_value=FakeNameManager()
        ):
            self.assertEqual(self.menu._confirm_new_game(), "new_game")
        self.assertEqual(calls, ["reset", ("set_names", "山田", "太郎")])

    def test_text_input_commits_ime_textinput_and_clears_composition(self):
        field = TextInput(0, 0, 300, 60, pygame.font.Font(None, 40), max_length=3)
        field.is_focused = True
        field.is_composing = True
        field.composition_text = "山田"
        result = field.handle_event(pygame.event.Event(pygame.TEXTINPUT, text="山田"))
        self.assertEqual(result, "text_changed")
        self.assertEqual(field.get_text(), "山田")
        self.assertFalse(field.is_composing)
        self.assertEqual(field.composition_text, "")

    def test_text_input_keeps_long_uncommitted_ime_composition(self):
        field = TextInput(0, 0, 300, 60, pygame.font.Font(None, 40), max_length=3)
        field.is_focused = True

        result = field.handle_event(
            pygame.event.Event(
                pygame.TEXTEDITING,
                text="わたなべ",
                start=4,
                length=0,
            )
        )

        self.assertIsNone(result)
        self.assertEqual(field.composition_text, "わたなべ")
        self.assertTrue(field.is_composing)
        self.assertEqual(field.get_text(), "")

    def test_text_input_leaves_composition_editing_keys_to_ime(self):
        for key in (pygame.K_BACKSPACE, pygame.K_RETURN, pygame.K_KP_ENTER):
            with self.subTest(key=key):
                field = TextInput(
                    0,
                    0,
                    300,
                    60,
                    pygame.font.Font(None, 40),
                    max_length=3,
                )
                field.is_focused = True
                field.is_composing = True
                field.composition_text = "わたなべ"

                result = field.handle_event(
                    pygame.event.Event(pygame.KEYDOWN, key=key)
                )

                self.assertIsNone(result)
                self.assertTrue(field.is_focused)
                self.assertTrue(field.is_composing)
                self.assertEqual(field.composition_text, "わたなべ")

    def test_text_input_accepts_overlong_commit_without_truncating(self):
        field = TextInput(0, 0, 300, 60, pygame.font.Font(None, 40), max_length=3)
        field.is_focused = True
        field.is_composing = True
        field.composition_text = "ながいなまえ"

        result = field.handle_event(
            pygame.event.Event(pygame.TEXTINPUT, text="長い名前")
        )

        self.assertEqual(result, "text_changed")
        self.assertEqual(field.get_text(), "長い名前")
        self.assertFalse(field.is_composing)
        self.assertEqual(field.composition_text, "")

    def test_set_text_keeps_overlong_value_until_confirmation(self):
        field = TextInput(0, 0, 300, 60, pygame.font.Font(None, 40), max_length=3)

        field.set_text("長い名前")

        self.assertEqual(field.get_text(), "長い名前")

    def test_focusing_name_field_positions_ime_at_transformed_input_rect(self):
        transformed_rect = pygame.Rect(410, 320, 200, 42)
        menu = MainMenu(
            self.screen,
            text_input_rect_transform=lambda rect: transformed_rect,
        )
        try:
            calls = []
            with patch(
                "pygame.key.set_text_input_rect",
                side_effect=lambda rect: calls.append(("rect", rect)),
            ) as set_ime_rect, patch(
                "pygame.key.start_text_input",
                side_effect=lambda: calls.append(("start",)),
            ) as start_text_input:
                menu._focus_input("name")

            set_ime_rect.assert_called_once_with(transformed_rect)
            start_text_input.assert_called_once_with()
            self.assertEqual(calls, [("rect", transformed_rect), ("start",)])
        finally:
            menu.cleanup()

    def test_name_input_warns_but_keeps_accepting_overlong_text(self):
        self.menu.state = MainMenu.NAME_INPUT
        self.menu._focus_input("surname")

        self.menu.handle_events(
            [pygame.event.Event(pygame.TEXTINPUT, text="長い苗字名")]
        )
        self.menu.handle_events(
            [pygame.event.Event(pygame.TEXTINPUT, text="追加")]
        )
        self.menu.render()

        self.assertEqual(self.menu.text_inputs["surname"].get_text(), "長い苗字名追加")
        self.assertEqual(self.menu._name_error, "苗字は3文字以内で入力してください")

        self.menu.handle_events(
            [
                pygame.event.Event(pygame.KEYDOWN, key=pygame.K_BACKSPACE)
                for _ in range(4)
            ]
        )

        self.assertEqual(self.menu.text_inputs["surname"].get_text(), "長い苗")
        self.assertEqual(self.menu._name_error, "")

    def test_confirmation_warns_and_does_not_transition_for_overlong_name(self):
        for key, overlong_value, expected_error in (
            ("surname", "長い苗字名", "苗字は3文字以内で入力してください"),
            ("name", "長い名前", "名前は3文字以内で入力してください"),
        ):
            with self.subTest(key=key):
                self.menu.text_inputs["surname"].set_text("山田")
                self.menu.text_inputs["name"].set_text("太郎")
                self.menu.text_inputs[key].set_text(overlong_value)

                with patch("menu.main_menu.get_save_manager") as get_save_manager, patch(
                    "menu.main_menu.get_name_manager"
                ) as get_name_manager:
                    result = self.menu._confirm_new_game()

                self.assertIsNone(result)
                self.assertEqual(self.menu._name_error, expected_error)
                get_save_manager.assert_not_called()
                get_name_manager.assert_not_called()


class ReusableLoadScreenTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not pygame.get_init():
            pygame.init()
        cls.screen = pygame.display.set_mode((1440, 1080))

    def test_empty_slots_are_disabled_and_existing_slot_loads(self):
        class FakeSaveManager:
            def __init__(self):
                self.loaded = None

            def has_save(self, slot_name):
                return slot_name == "saveslot_02"

            def get_save_metadata(self, slot_name):
                return {
                    "player_name": "山田 太郎",
                    "game_time": "5月31日 朝",
                }

            def load_game(self, slot_name):
                self.loaded = slot_name
                return True

        manager = FakeSaveManager()
        load_screen = LoadScreen(self.screen, save_manager=manager)
        self.assertEqual(load_screen.choice_list.selected_index, 1)
        self.assertFalse(load_screen.choice_list.enabled[0])
        result = load_screen.handle_events(
            [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)]
        )
        self.assertEqual(result, "continue_game")
        self.assertEqual(manager.loaded, "saveslot_02")

    def test_flow_routes_are_reusable(self):
        self.assertEqual(normalize_flow_request("go_to_load"), Navigate(Scene.LOAD))
        self.assertIsInstance(normalize_flow_request("show_settings"), ShowSettings)

    def test_direct_settings_closes_back_to_its_base_screen(self):
        with patch("pygame.time.get_ticks", return_value=1000):
            settings = OptionSubsystem.settings(self.screen)
        with patch("pygame.time.get_ticks", return_value=1400):
            self.assertIsNone(
                settings.handle_events(
                    [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)]
                )
            )
        with patch("pygame.time.get_ticks", return_value=1760):
            self.assertEqual(settings.handle_events([]), OptionAction.RESUME)


if __name__ == "__main__":
    unittest.main()
