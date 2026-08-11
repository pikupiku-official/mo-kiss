import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

from unittest import mock

import pygame

from core import config
from core.runtime.window_controller import WindowController


def test_normalize_event_converts_position_and_relative_motion(monkeypatch):
    controller = WindowController(pygame.Surface((100, 100)), pygame.Surface((100, 100)))
    monkeypatch.setattr(config, "window_to_virtual_pos", lambda pos: (12, 34))
    monkeypatch.setattr(config, "WINDOW_CONTENT_WIDTH", config.VIRTUAL_WIDTH // 2)
    monkeypatch.setattr(config, "WINDOW_CONTENT_HEIGHT", config.VIRTUAL_HEIGHT // 2)
    event = pygame.event.Event(
        pygame.MOUSEMOTION,
        pos=(6, 17),
        rel=(10, 8),
        buttons=(0, 0, 0),
    )

    normalized = controller.normalize_event(event)

    assert normalized.pos == (12, 34)
    assert normalized.rel == (20, 16)


def test_gather_events_consumes_f11_and_toggles_once(monkeypatch):
    controller = WindowController(pygame.Surface((100, 100)), pygame.Surface((100, 100)))
    controller.toggle_fullscreen = mock.Mock()
    ordinary_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_a)
    monkeypatch.setattr(
        pygame.event,
        "get",
        lambda: [
            pygame.event.Event(pygame.KEYDOWN, key=pygame.K_F11, repeat=False),
            ordinary_event,
        ],
    )

    events = controller.gather_normalized_events()

    controller.toggle_fullscreen.assert_called_once_with()
    assert events == [ordinary_event]


def test_present_virtual_screen_letterboxes_content(monkeypatch):
    window = pygame.Surface((200, 200))
    virtual = pygame.Surface((100, 100))
    virtual.fill((255, 0, 0))
    controller = WindowController(window, virtual)
    monkeypatch.setattr(config, "WINDOW_CONTENT_WIDTH", 100)
    monkeypatch.setattr(config, "WINDOW_CONTENT_HEIGHT", 100)
    monkeypatch.setattr(config, "WINDOW_OFFSET_X", 50)
    monkeypatch.setattr(config, "WINDOW_OFFSET_Y", 50)

    controller.present_virtual_screen()

    assert window.get_at((0, 0))[:3] == (0, 0, 0)
    assert window.get_at((50, 50))[:3] == (255, 0, 0)
