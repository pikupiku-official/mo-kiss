import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

from unittest import mock

import pygame

from core import config
from core.runtime.window_controller import WindowController


def test_native_ime_candidate_ui_is_enabled():
    assert os.environ["SDL_IME_SHOW_UI"] == "1"


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


def test_virtual_to_window_rect_uses_current_letterbox_metrics(monkeypatch):
    monkeypatch.setattr(config, "WINDOW_CONTENT_WIDTH", 720)
    monkeypatch.setattr(config, "WINDOW_CONTENT_HEIGHT", 540)
    monkeypatch.setattr(config, "WINDOW_OFFSET_X", 25)
    monkeypatch.setattr(config, "WINDOW_OFFSET_Y", 40)

    actual = config.virtual_to_window_rect(pygame.Rect(200, 300, 300, 60))

    assert actual == pygame.Rect(125, 190, 150, 30)


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
    controller.pointer_image = None
    monkeypatch.setattr(config, "WINDOW_CONTENT_WIDTH", 100)
    monkeypatch.setattr(config, "WINDOW_CONTENT_HEIGHT", 100)
    monkeypatch.setattr(config, "WINDOW_OFFSET_X", 50)
    monkeypatch.setattr(config, "WINDOW_OFFSET_Y", 50)

    controller.present_virtual_screen()

    assert window.get_at((0, 0))[:3] == (0, 0, 0)
    assert window.get_at((50, 50))[:3] == (255, 0, 0)


def test_pointer_scales_but_keeps_hotspot_on_real_mouse_position(monkeypatch):
    window = pygame.Surface((800, 600))
    virtual = pygame.Surface((100, 100))
    controller = WindowController(window, virtual)
    pointer = pygame.Surface((10, 20), pygame.SRCALPHA)
    pointer.fill((0, 255, 0, 255))
    controller.pointer_image = pointer
    controller.POINTER_HOTSPOT = (2, 4)
    controller._scaled_pointer_key = None

    monkeypatch.setattr(config, "WINDOW_CONTENT_WIDTH", 720)
    monkeypatch.setattr(config, "WINDOW_CONTENT_HEIGHT", 540)
    monkeypatch.setattr(config, "WINDOW_OFFSET_X", 0)
    monkeypatch.setattr(config, "WINDOW_OFFSET_Y", 0)
    monkeypatch.setattr(pygame.mouse, "get_pos", lambda: (100, 100))

    controller.present_virtual_screen()

    assert controller._scaled_pointer.get_size() == (5, 10)
    assert window.get_at((99, 98))[:3] == (0, 255, 0)
    assert window.get_at((98, 98))[:3] == (0, 0, 0)


def test_pointer_fades_out_after_mouse_stops(monkeypatch):
    window = pygame.Surface((200, 200))
    virtual = pygame.Surface((100, 100))
    controller = WindowController(window, virtual)
    pointer = pygame.Surface((10, 10), pygame.SRCALPHA)
    pointer.fill((0, 255, 0, 255))
    controller.pointer_image = pointer
    controller.POINTER_HOTSPOT = (0, 0)
    controller._scaled_pointer_key = None
    controller._pointer_last_position = (100, 100)
    controller._pointer_last_activity_ms = 1_000

    monkeypatch.setattr(config, "WINDOW_CONTENT_WIDTH", config.VIRTUAL_WIDTH)
    monkeypatch.setattr(config, "WINDOW_CONTENT_HEIGHT", config.VIRTUAL_HEIGHT)
    monkeypatch.setattr(config, "WINDOW_OFFSET_X", 0)
    monkeypatch.setattr(config, "WINDOW_OFFSET_Y", 0)
    monkeypatch.setattr(pygame.mouse, "get_pos", lambda: (100, 100))

    monkeypatch.setattr(pygame.time, "get_ticks", lambda: 1_900)
    controller._draw_pointer()
    assert controller._scaled_pointer.get_alpha() in (127, 128)

    window.fill((0, 0, 0))
    monkeypatch.setattr(pygame.time, "get_ticks", lambda: 2_100)
    controller._draw_pointer()
    assert window.get_at((100, 100))[:3] == (0, 0, 0)
