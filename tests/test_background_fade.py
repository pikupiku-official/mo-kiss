import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from core.config import VIRTUAL_HEIGHT, VIRTUAL_WIDTH
from dialogue.background_manager import (
    draw_background,
    show_background,
    update_background_animation,
)
from dialogue.data_normalizer import normalize_dialogue_data
from dialogue.dialogue_loader import DialogueLoader
from dialogue.ir_builder import build_ir_from_normalized
from dialogue.scenario_manager import (
    _ir_default_on_advance,
    _ir_get_action_duration_ms,
)


class StubImageManager:
    def __init__(self, image):
        self.image = image

    def get_image(self, image_type, image_key):
        assert (image_type, image_key) == ("bg", "room")
        return self.image


def _loader():
    loader = DialogueLoader.__new__(DialogueLoader)
    loader.debug = False
    loader.disable_scroll_continue = False
    loader.max_chars_per_line = 26
    return loader


def _first_action(source):
    raw = _loader()._parse_ks_content(source)
    normalized = normalize_dialogue_data(raw)
    ir = build_ir_from_normalized(normalized)
    return ir["steps"][0]["actions"][0]


def test_bg_show_fade_reaches_blocking_ir():
    fade_action = _first_action('[bg_show storage="room" fade="0.4"]')

    assert fade_action["params"]["fade"] == 0.4
    assert fade_action["animation"]["on_advance"] == "block"
    assert _ir_default_on_advance("bg_show") == "block"
    assert _ir_get_action_duration_ms("bg_show", fade_action["params"]) == 400


def test_bg_show_fades_from_black_without_mutating_source(monkeypatch):
    source = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT))
    source.fill((200, 100, 50))
    source_alpha = source.get_alpha()
    screen = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT))
    state = {
        "screen": screen,
        "image_manager": StubImageManager(source),
        "background_state": {
            "current_bg": None,
            "zoom": 1.0,
            "pos": [0, 0],
            "anim": None,
            "fade": None,
        },
    }
    now = [1000]
    monkeypatch.setattr(pygame.time, "get_ticks", lambda: now[0])

    show_background(state, "room", 0.5, 0.5, 1.0, fade=1.0)
    draw_background(state)
    assert screen.get_at((VIRTUAL_WIDTH // 2, VIRTUAL_HEIGHT // 2))[:3] == (0, 0, 0)

    now[0] = 1500
    draw_background(state)
    halfway = screen.get_at((VIRTUAL_WIDTH // 2, VIRTUAL_HEIGHT // 2))[:3]
    assert all(20 < channel < original for channel, original in zip(halfway, (200, 100, 50)))

    now[0] = 2000
    update_background_animation(state)
    draw_background(state)
    assert screen.get_at((VIRTUAL_WIDTH // 2, VIRTUAL_HEIGHT // 2))[:3] == (200, 100, 50)
    assert state["background_state"]["fade"] is None
    assert source.get_alpha() == source_alpha

