import os
from types import SimpleNamespace

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pygame
import pytest

from dialogue import controller2
from dialogue.text_renderer import TextRenderer


def state():
    renderer = TextRenderer.__new__(TextRenderer)
    renderer.auto_mode = False
    renderer.skip_mode = True
    renderer.current_text = ""
    renderer.debug = False
    return {
        "text_renderer": renderer,
        "backlog_manager": SimpleNamespace(is_showing_backlog=lambda: False, handle_input=lambda e: None),
        "choice_renderer": SimpleNamespace(is_choice_showing=lambda: False),
        "character_transitions": {"momoko": {"pending_render": True}},
        "show_text": True,
        "images": {"ui": {"auto": pygame.Surface((40, 20)), "skip": pygame.Surface((40, 20))}},
    }


@pytest.mark.parametrize("key,mode,expected", [
    (pygame.K_a, "auto_mode", True),
    (pygame.K_SPACE, "skip_mode", False),
])
def test_keyboard_toggles_work_during_a_blocking_fade(key, mode, expected):
    gs = state()
    event = pygame.event.Event(pygame.KEYDOWN, key=key, repeat=False)
    assert controller2.handle_events(gs, None, events=[event])
    assert getattr(gs["text_renderer"], mode) is expected


def test_mouse_can_stop_skip_during_a_blocking_fade(monkeypatch):
    gs = state()
    gs["text_renderer"].seed_at = lambda pos: None
    monkeypatch.setattr(controller2, "get_ui_button_positions", lambda screen: {"auto": (0, 0), "skip": (100, 0)})
    controller2.handle_mouse_click(gs, (105, 5), None)
    assert gs["text_renderer"].skip_mode is False


def test_repeated_keydown_cannot_undo_a_toggle(monkeypatch):
    gs = state()
    gs["character_transitions"].clear()
    events = [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_a, repeat=repeat) for repeat in (False, True)]
    controller2.handle_events(gs, None, events=events)
    assert gs["text_renderer"].auto_mode is True


def test_active_button_is_visible_and_scaled_surfaces_are_reused(monkeypatch):
    gs = state()
    screen = pygame.Surface((200, 50))
    monkeypatch.setattr(controller2, "get_ui_button_positions", lambda screen: {"auto": (10, 10), "skip": (100, 10)})
    controller2.draw_playback_controls(gs, screen)
    cached = gs["_playback_button_surfaces"]["skip"][1]
    assert screen.get_at((98, 10))[:3] == (255, 220, 110)
    controller2.draw_playback_controls(gs, screen)
    assert gs["_playback_button_surfaces"]["skip"][1] is cached
