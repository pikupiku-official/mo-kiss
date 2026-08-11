"""play_e002_e006.py のタイトル選択とモックUIショートカットの回帰テスト。"""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
import pytest

from play_e002_e006 import (
    AlternatingScenarioApplication,
    EVENT_FILES,
    IDLE_AWAIT_TIMEOUT_MS,
    IDLE_AWAIT_VISIBLE_MS,
    MOCK_AWAIT_FRAMES,
    TITLE_PROMPT,
    TimedTitleSubsystem,
)


@pytest.fixture
def idle_title(monkeypatch):
    monkeypatch.setattr(pygame.time, "get_ticks", lambda: 1_000)
    title = TimedTitleSubsystem.__new__(TimedTitleSubsystem)
    title._idle_started_at = 1_000
    return title


@pytest.mark.parametrize(
    ("key", "expected"),
    [
        (pygame.K_2, "play_e002"),
        (pygame.K_KP2, "play_e002"),
        (pygame.K_6, "play_e006"),
        (pygame.K_KP6, "play_e006"),
    ],
)
def test_title_number_keys_select_scenario(idle_title, key, expected):
    event = pygame.event.Event(pygame.KEYDOWN, key=key)
    assert idle_title.handle_events([event]) == expected


@pytest.mark.parametrize(
    "event",
    [
        pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN),
        pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE),
        pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(0, 0)),
    ],
)
def test_title_ignores_other_input(idle_title, event):
    assert idle_title.handle_events([event]) is None


def test_title_prompt_describes_available_keys():
    assert TITLE_PROMPT == "PRESS 2: E002 / 6: E006"


def make_idle_app(last_activity_at=1_000):
    app = AlternatingScenarioApplication.__new__(AlternatingScenarioApplication)
    app.current_mode = "dialogue"
    app.current_subsystem = object()
    app.current_overlay = None
    app._last_activity_at_ms = last_activity_at
    app._idle_await_overlay = None
    return app


def test_idle_await_timeout_is_five_seconds():
    assert IDLE_AWAIT_TIMEOUT_MS == 5_000


def test_idle_await_visible_time_is_two_seconds():
    assert IDLE_AWAIT_VISIBLE_MS == 2_000


@pytest.mark.parametrize(
    ("now", "should_show"),
    [
        (5_999, False),
        (6_000, True),
    ],
)
def test_idle_await_appears_after_five_seconds(monkeypatch, now, should_show):
    monkeypatch.setattr(pygame.time, "get_ticks", lambda: now)
    app = make_idle_app()
    watch_overlay = object()
    app.show_mock_await = lambda: setattr(app, "current_overlay", watch_overlay)

    app._update_idle_await([])

    assert (app.current_overlay is watch_overlay) is should_show
    if should_show:
        assert app._idle_await_overlay is watch_overlay


def test_idle_await_does_not_interrupt_demo_video(monkeypatch):
    monkeypatch.setattr(pygame.time, "get_ticks", lambda: 10_000)
    app = make_idle_app()
    app.current_mode = "video"
    shown = []
    app.show_mock_await = lambda: shown.append(True)

    app._update_idle_await([])

    assert shown == []


def test_idle_await_does_not_appear_on_title(monkeypatch):
    monkeypatch.setattr(pygame.time, "get_ticks", lambda: 10_000)
    app = make_idle_app()
    app.current_mode = "title"
    shown = []
    app.show_mock_await = lambda: shown.append(True)

    app._update_idle_await([])

    assert shown == []


def test_activity_resets_idle_await_timer(monkeypatch):
    monkeypatch.setattr(pygame.time, "get_ticks", lambda: 8_000)
    app = make_idle_app()
    event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE)

    app._update_idle_await([event])

    assert app._last_activity_at_ms == 8_000
    assert app.current_overlay is None


def test_activity_closes_automatically_shown_watch(monkeypatch):
    monkeypatch.setattr(pygame.time, "get_ticks", lambda: 8_000)
    app = make_idle_app()

    class ClosingOverlay:
        closing = False

        def start_close(self):
            self.closing = True

    watch_overlay = ClosingOverlay()
    app.current_overlay = watch_overlay
    app._idle_await_overlay = watch_overlay
    events = [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE)]

    app._update_idle_await(events)

    assert watch_overlay.closing is True
    assert events == []


def test_f7_still_controls_automatically_shown_watch(monkeypatch):
    monkeypatch.setattr(pygame.time, "get_ticks", lambda: 8_000)
    app = make_idle_app()
    watch_overlay = object()
    app.current_overlay = watch_overlay
    app._idle_await_overlay = watch_overlay
    events = [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_F7)]

    app._update_idle_await(events)

    assert events[0].key == pygame.K_F7


def test_manual_f7_watch_closes_two_seconds_after_opening(monkeypatch):
    from core.ui.option_overlay import MockOptionOverlay

    now = [1_000]
    monkeypatch.setattr(pygame.time, "get_ticks", lambda: now[0])
    monkeypatch.setattr(
        MockOptionOverlay,
        "_load_frames",
        lambda self: [pygame.Surface((1, 1)) for _ in self.frame_names],
    )
    app = make_idle_app(last_activity_at=1_000)
    app.screen = pygame.Surface((1, 1))
    events = [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_F7)]

    app._poll_mock_overlay_shortcuts(events)
    watch_overlay = app.current_overlay
    assert isinstance(watch_overlay, MockOptionOverlay)

    now[0] = 2_999
    app._update_idle_await([])
    assert watch_overlay._closing_started_at_ms is None

    now[0] = 3_000
    app._update_idle_await([])
    assert watch_overlay._closing_started_at_ms == 3_000

    now[0] = 3_150
    result = watch_overlay.handle_events([])
    assert result == "resume"
    app._handle_overlay_result(result)
    assert app.current_overlay is None
    assert app._last_activity_at_ms == 3_150


def test_idle_await_repeats_five_seconds_after_it_closes(monkeypatch):
    from core.ui.option_overlay import MockOptionOverlay

    now = [6_000]
    monkeypatch.setattr(pygame.time, "get_ticks", lambda: now[0])
    monkeypatch.setattr(
        MockOptionOverlay,
        "_load_frames",
        lambda self: [pygame.Surface((1, 1)) for _ in self.frame_names],
    )
    app = make_idle_app()
    app.screen = pygame.Surface((1, 1))

    shown = []

    def show_watch():
        overlay = MockOptionOverlay(app.screen, MOCK_AWAIT_FRAMES)
        shown.append(overlay)
        app.current_overlay = overlay

    app.show_mock_await = show_watch
    app._update_idle_await([])
    first_watch = shown[0]

    now[0] = 7_999
    app._update_idle_await([])
    assert first_watch._closing_started_at_ms is None

    now[0] = 8_000
    app._update_idle_await([])
    assert first_watch._closing_started_at_ms == 8_000

    now[0] = 8_150
    app._handle_overlay_result("resume")
    assert app.current_overlay is None

    now[0] = 13_149
    app._update_idle_await([])
    assert len(shown) == 1

    now[0] = 13_150
    app._update_idle_await([])
    assert len(shown) == 2


@pytest.mark.parametrize(
    ("result", "expected_file"),
    [
        ("play_e002", EVENT_FILES[0]),
        ("play_e006", EVENT_FILES[1]),
    ],
)
def test_title_transition_opens_selected_event(result, expected_file):
    app = AlternatingScenarioApplication.__new__(AlternatingScenarioApplication)
    app.current_mode = "title"
    opened = []
    app.switch_to_dialogue = opened.append

    app._handle_transition(result)

    assert opened == [expected_file]


@pytest.mark.parametrize(
    ("key", "show_method"),
    [
        (pygame.K_F6, "show_mock_option"),
        (pygame.K_F7, "show_mock_await"),
    ],
)
def test_dedicated_player_uses_main_mock_ui_shortcuts(key, show_method):
    app = AlternatingScenarioApplication.__new__(AlternatingScenarioApplication)
    app.current_overlay = None
    shown = []
    app.show_mock_option = lambda: shown.append("show_mock_option")
    app.show_mock_await = lambda: shown.append("show_mock_await")
    events = [pygame.event.Event(pygame.KEYDOWN, key=key)]

    assert app._poll_mock_overlay_shortcuts(events) is True
    assert shown == [show_method]
    assert events == []
