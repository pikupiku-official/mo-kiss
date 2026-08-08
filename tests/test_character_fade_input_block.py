import pygame

from dialogue.controller2 import (
    handle_enter_key,
    is_character_image_fading,
    is_input_blocked,
)
from dialogue.scenario_manager import _ir_default_on_advance


class DummyBacklogManager:
    def is_showing_backlog(self):
        return False


class DummyChoiceRenderer:
    def is_choice_showing(self):
        return False


class DummyTextRenderer:
    def __init__(self, displaying=True):
        self.displaying = displaying
        self.skip_calls = 0

    def is_displaying(self):
        return self.displaying

    def skip_text(self):
        self.skip_calls += 1


def _game_state_with_fade(text_renderer=None):
    return {
        "use_ir": True,
        "backlog_manager": DummyBacklogManager(),
        "choice_renderer": DummyChoiceRenderer(),
        "text_renderer": text_renderer or DummyTextRenderer(),
        "character_part_fades": {
            "momoko": {
                "torso": {
                    "from": "T00",
                    "to": "T01",
                    "start_time": 1000,
                    "duration": 300,
                }
            }
        },
        "character_hide_pending": {},
        "ir_anim_pending": True,
        "ir_active_anims": [
            {
                "action": "chara_shift",
                "target": "momoko",
                "on_advance": "complete",
                "end_time": 1300,
            }
        ],
    }


def test_character_image_fade_blocks_input_until_its_real_end(monkeypatch):
    game_state = _game_state_with_fade()

    monkeypatch.setattr(pygame.time, "get_ticks", lambda: 1299)
    assert is_character_image_fading(game_state)
    assert is_input_blocked(game_state)

    monkeypatch.setattr(pygame.time, "get_ticks", lambda: 1300)
    assert not is_character_image_fading(game_state)


def test_enter_cannot_skip_text_during_character_image_fade(monkeypatch):
    text_renderer = DummyTextRenderer(displaying=True)
    game_state = _game_state_with_fade(text_renderer)
    monkeypatch.setattr(pygame.time, "get_ticks", lambda: 1100)

    for _ in range(3):
        handle_enter_key(game_state)

    assert text_renderer.skip_calls == 0


def test_character_fades_default_to_blocking_advance():
    assert _ir_default_on_advance("chara_show") == "block"
    assert _ir_default_on_advance("chara_shift") == "block"
    assert _ir_default_on_advance("chara_hide") == "block"
    assert _ir_default_on_advance("chara_move") == "complete"
