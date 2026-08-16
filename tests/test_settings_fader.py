import json
import os
import tempfile
import unittest
from unittest import mock

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from core.services.settings_manager import DEFAULT_SETTINGS, SettingsManager
from core.ui.option_overlay import OptionImageOverlay, SettingsFaderOverlay
from core.ui.option_subsystem import OptionSubsystem


class SettingsManagerTests(unittest.TestCase):
    def test_defaults_and_text_speed_preserve_existing_delay(self):
        with tempfile.TemporaryDirectory() as directory:
            manager = SettingsManager(os.path.join(directory, "settings.json"))

        self.assertEqual(manager.get("master_volume"), 1.0)
        self.assertEqual(manager.get("music_volume"), 1.0)
        self.assertEqual(manager.get("se_volume"), 1.0)
        self.assertEqual(manager.get("voice_volume"), 1.0)
        self.assertEqual(manager.text_delay_ms(), 110)
        self.assertFalse(manager.get("fullscreen"))

    def test_only_settings_are_persisted_and_reset(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "settings.json")
            manager = SettingsManager(path)
            manager.set("music_volume", 0.42)
            manager.set("voice_volume", 0.25)

            with open(path, "r", encoding="utf-8") as handle:
                saved = json.load(handle)
            self.assertEqual(set(saved), set(DEFAULT_SETTINGS))
            self.assertEqual(saved["music_volume"], 0.42)

            manager.reset()
            self.assertEqual(manager.values, DEFAULT_SETTINGS)


class SettingsFaderOverlayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1, 1))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_fader_top_and_bottom_map_to_one_and_zero(self):
        with tempfile.TemporaryDirectory() as directory:
            manager = SettingsManager(os.path.join(directory, "settings.json"))
            now = [0]
            with mock.patch(
                "core.ui.option_overlay.get_settings_manager",
                return_value=manager,
            ), mock.patch.object(pygame.time, "get_ticks", side_effect=lambda: now[0]):
                overlay = SettingsFaderOverlay(pygame.Surface((1440, 1080)))
                now[0] = 400

                self.assertTrue(overlay.begin_drag((107 * 2.25, 230 * 2.25)))
                overlay.end_drag()
                self.assertEqual(manager.get("master_volume"), 1.0)

                self.assertTrue(overlay.begin_drag((107 * 2.25, 327 * 2.25)))
                overlay.end_drag()
                self.assertEqual(manager.get("master_volume"), 0.0)

    def test_fullscreen_fader_is_discrete_and_uses_callback(self):
        with tempfile.TemporaryDirectory() as directory:
            manager = SettingsManager(os.path.join(directory, "settings.json"))
            callback = mock.Mock()
            now = [0]
            with mock.patch(
                "core.ui.option_overlay.get_settings_manager",
                return_value=manager,
            ), mock.patch.object(pygame.time, "get_ticks", side_effect=lambda: now[0]):
                overlay = SettingsFaderOverlay(
                    pygame.Surface((1440, 1080)),
                    fullscreen_callback=callback,
                )
                now[0] = 400
                overlay.begin_drag((529 * 2.25, 230 * 2.25))

            self.assertTrue(manager.get("fullscreen"))
            callback.assert_called_once_with(True)

    def test_close_animation_runs_two_one_zero_before_resume(self):
        with tempfile.TemporaryDirectory() as directory:
            manager = SettingsManager(os.path.join(directory, "settings.json"))
            now = [400]
            with mock.patch(
                "core.ui.option_overlay.get_settings_manager",
                return_value=manager,
            ), mock.patch.object(pygame.time, "get_ticks", side_effect=lambda: now[0]):
                overlay = SettingsFaderOverlay(pygame.Surface((1440, 1080)))
                overlay.start_close()
                self.assertIs(overlay._current_frame(), overlay._frames[2])
                now[0] += 120
                self.assertIs(overlay._current_frame(), overlay._frames[1])
                now[0] += 120
                self.assertIs(overlay._current_frame(), overlay._frames[0])
                now[0] += 120
                self.assertTrue(overlay.is_close_animation_finished())

    def test_sixth_phone_option_opens_fader_settings(self):
        now = [1_000]
        images = {
            number: pygame.Surface((640, 602), pygame.SRCALPHA)
            for number in range(1, 7)
        }
        with mock.patch.object(
            OptionImageOverlay, "_load_images", return_value=images
        ), mock.patch.object(pygame.time, "get_ticks", side_effect=lambda: now[0]):
            subsystem = OptionSubsystem.image_option(pygame.Surface((1440, 1080)))
            subsystem.overlay.selected_number = 6
            result = subsystem.handle_events(
                [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)]
            )

        self.assertIsNone(result)
        self.assertIsInstance(subsystem.overlay, SettingsFaderOverlay)


if __name__ == "__main__":
    unittest.main()
