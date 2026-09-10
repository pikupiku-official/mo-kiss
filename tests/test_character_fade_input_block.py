import pygame

from dialogue.controller2 import (
    _discard_blocked_gameplay_events,
    handle_enter_key,
    is_character_image_fading,
    is_ir_idle,
    is_input_blocked,
)
from dialogue.character_manager import _begin_character_fade_on_first_render
from dialogue.scenario_manager import _ir_default_on_advance


def test_blocked_advance_events_are_discarded_until_keyup():
    game_state = {
        "character_transitions": {"momoko": {"pending_render": True}},
    }
    events = [
        pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN, repeat=False),
        pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(10, 10)),
        pygame.event.Event(pygame.KEYUP, key=pygame.K_RETURN),
        pygame.event.Event(pygame.KEYDOWN, key=pygame.K_b, repeat=False),
    ]

    filtered = _discard_blocked_gameplay_events(game_state, events)

    assert [event.key for event in filtered if event.type == pygame.KEYDOWN] == [
        pygame.K_b
    ]
    assert game_state["_advance_key_held"] is False

    game_state["character_transitions"].clear()
    fresh_enter = pygame.event.Event(
        pygame.KEYDOWN, key=pygame.K_RETURN, repeat=False
    )
    assert _discard_blocked_gameplay_events(game_state, [fresh_enter]) == [
        fresh_enter
    ]


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


def test_pending_first_render_keeps_step_non_idle(monkeypatch):
    game_state = _game_state_with_fade()
    game_state["character_part_fades"]["momoko"]["torso"]["duration"] = 150
    game_state["character_fade_pending_render"] = {"momoko": {"torso"}}

    monkeypatch.setattr(pygame.time, "get_ticks", lambda: 1200)
    assert is_character_image_fading(game_state)
    assert not is_ir_idle(game_state)


def test_first_render_retimes_ir_step_guard(monkeypatch):
    game_state = _game_state_with_fade()
    game_state["character_part_fades"]["momoko"]["torso"]["duration"] = 150
    game_state["character_fade_pending_render"] = {"momoko": {"torso"}}
    game_state["ir_active_anims"][0]["end_time"] = 1150

    _begin_character_fade_on_first_render(game_state, "momoko", 2000)

    assert game_state["character_part_fades"]["momoko"]["torso"]["start_time"] == 2000
    assert game_state["ir_active_anims"][0]["end_time"] == 2150


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
