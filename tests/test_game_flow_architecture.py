import csv
import os
import types

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from core.flow.event_progress import EventProgress
from core.flow.game_flow import (
    DialogueEnded,
    GameFlowController,
    Navigate,
    Scene,
    StartDialogue,
    normalize_flow_request,
)
from core.ui.option_overlay import OptionImageOverlay
from core.ui.option_subsystem import OptionAction, OptionSubsystem
from core.flow.scene_manager import SceneManager
from home.morning_flow import MorningFlow


class FakeTimeManager:
    def __init__(self, after_school=False):
        self.after_school = after_school
        self.advances = 0

    def get_full_time_string(self):
        return "1999-06-01 朝"

    def get_current_period(self):
        return "放課後" if self.after_school else "朝"

    def is_after_school(self):
        return self.after_school

    def advance_period(self):
        self.advances += 1


def _write_events_csv(root, event_id="E123"):
    events_dir = root / "events"
    events_dir.mkdir()
    with (events_dir / "events.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["イベントID"])
        writer.writeheader()
        writer.writerow({"イベントID": event_id})


def test_event_progress_records_and_advances_regular_event(tmp_path):
    _write_events_csv(tmp_path)
    time_manager = FakeTimeManager()
    progress = EventProgress(
        project_root=str(tmp_path),
        time_manager_getter=lambda: time_manager,
    )

    decision = progress.complete_dialogue("E123")

    assert decision.next_mode == "map"
    assert decision.time_advanced is True
    assert time_manager.advances == 1
    completed = tmp_path / "data" / "current_state" / "completed_events.csv"
    rows = list(csv.DictReader(completed.open(encoding="utf-8")))
    assert rows[0]["イベントID"] == "E123"
    assert rows[0]["実行回数"] == "1"


def test_event_progress_routes_after_school_to_home(tmp_path):
    _write_events_csv(tmp_path)
    progress = EventProgress(
        project_root=str(tmp_path),
        time_manager_getter=lambda: FakeTimeManager(after_school=True),
    )

    assert progress.complete_dialogue("E123").next_mode == "home"


def test_game_flow_accepts_typed_and_legacy_requests():
    assert normalize_flow_request("go_to_map") == Navigate(Scene.MAP)
    typed = StartDialogue("events/E123.ks")
    assert normalize_flow_request(typed) is typed
    assert normalize_flow_request("skip_time") is None


def test_dialogue_completion_uses_event_progress_decision():
    progress = types.SimpleNamespace(
        complete_dialogue=lambda event_id: types.SimpleNamespace(next_mode="home")
    )
    app = types.SimpleNamespace(
        dialogue_completion_result=None,
        current_event_id="E123",
        switch_to_home=lambda: calls.append("home"),
        switch_to_map=lambda: calls.append("map"),
        switch_to_menu=lambda: calls.append("menu"),
    )
    calls = []
    flow = GameFlowController(app, event_progress=progress)

    flow.handle(DialogueEnded())

    assert calls == ["home"]
    assert app.current_event_id is None


def test_option_subsystem_owns_input_and_overlay_only_holds_visual_state(monkeypatch):
    now = [1_000]
    monkeypatch.setattr(pygame.time, "get_ticks", lambda: now[0])
    screen = pygame.Surface((1_440, 1_080))
    monkeypatch.setattr(
        OptionImageOverlay,
        "_load_images",
        lambda self: {
            number: pygame.Surface((640, 602), pygame.SRCALPHA)
            for number in range(1, 7)
        },
    )
    subsystem = OptionSubsystem.image_option(screen)

    result = subsystem.handle_events(
        [
            pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RIGHT),
            pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN),
        ]
    )

    assert subsystem.overlay.selected_number == 2
    assert result is None
    assert subsystem.overlay.is_move_animating is True

    now[0] += 100
    result = subsystem.handle_events(
        [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)]
    )
    assert result is OptionAction.GO_TO_MENU


def test_option_cursor_move_consumes_shortcuts_without_switching_overlay(monkeypatch):
    monkeypatch.setattr(
        OptionImageOverlay,
        "_load_images",
        lambda self: {
            number: pygame.Surface((640, 602), pygame.SRCALPHA)
            for number in range(1, 7)
        },
    )
    subsystem = OptionSubsystem.image_option(pygame.Surface((1_440, 1_080)))
    subsystem.handle_events([
        pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RIGHT),
    ])
    original_overlay = subsystem.overlay
    events = [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_F7)]

    assert subsystem.poll_mock_shortcuts(events) is True
    assert events == []
    assert subsystem.overlay is original_overlay


def test_option_direction_hold_repeats_without_building_a_queue(monkeypatch):
    now = [1_000]
    monkeypatch.setattr(pygame.time, "get_ticks", lambda: now[0])
    monkeypatch.setattr(
        OptionImageOverlay,
        "_load_images",
        lambda self: {
            number: pygame.Surface((640, 602), pygame.SRCALPHA)
            for number in range(1, 7)
        },
    )
    subsystem = OptionSubsystem.image_option(pygame.Surface((1_440, 1_080)))

    subsystem.handle_events([
        pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RIGHT),
    ])
    assert subsystem.overlay.selected_number == 2

    now[0] = 1_249
    subsystem.handle_events([])
    assert subsystem.overlay.selected_number == 2

    now[0] = 1_250
    subsystem.handle_events([])
    assert subsystem.overlay.selected_number == 3

    now[0] = 1_350
    subsystem.handle_events([])
    assert subsystem.overlay.selected_number == 4

    now[0] = 1_351
    subsystem.handle_events([
        pygame.event.Event(pygame.KEYUP, key=pygame.K_RIGHT),
    ])
    now[0] = 2_000
    subsystem.handle_events([])
    assert subsystem.overlay.selected_number == 4


def test_option_release_discards_repeat_keydowns_without_late_movement(monkeypatch):
    now = [1_000]
    monkeypatch.setattr(pygame.time, "get_ticks", lambda: now[0])
    monkeypatch.setattr(
        OptionImageOverlay,
        "_load_images",
        lambda self: {
            number: pygame.Surface((640, 602), pygame.SRCALPHA)
            for number in range(1, 7)
        },
    )
    subsystem = OptionSubsystem.image_option(pygame.Surface((1_440, 1_080)))
    subsystem.handle_events([
        pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RIGHT),
    ])

    now[0] = 1_050
    subsystem.handle_events([
        pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RIGHT, repeat=True),
        pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RIGHT, repeat=True),
        pygame.event.Event(pygame.KEYUP, key=pygame.K_RIGHT),
    ])
    now[0] = 2_000
    subsystem.handle_events([])

    assert subsystem.overlay.selected_number == 2
    assert subsystem._held_direction_key is None
    assert subsystem._next_direction_repeat_at_ms is None


def test_option_physical_key_state_cancels_hold_when_keyup_is_delayed(monkeypatch):
    now = [1_000]
    pressed = {pygame.K_RIGHT: True}
    monkeypatch.setattr(pygame.time, "get_ticks", lambda: now[0])
    monkeypatch.setattr(pygame.key, "get_focused", lambda: True)
    monkeypatch.setattr(
        pygame.key,
        "get_pressed",
        lambda: pressed,
    )
    monkeypatch.setattr(
        OptionImageOverlay,
        "_load_images",
        lambda self: {
            number: pygame.Surface((640, 602), pygame.SRCALPHA)
            for number in range(1, 7)
        },
    )
    subsystem = OptionSubsystem.image_option(pygame.Surface((1_440, 1_080)))
    subsystem.handle_events([
        pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RIGHT),
    ])
    assert subsystem.overlay.selected_number == 2

    pressed[pygame.K_RIGHT] = False
    now[0] = 1_050
    subsystem.handle_events([])
    now[0] = 2_000
    subsystem.handle_events([])

    assert subsystem.overlay.selected_number == 2
    assert subsystem._held_direction_key is None


def test_option_independent_rapid_taps_collapse_to_final_selection(monkeypatch):
    now = [1_000]
    monkeypatch.setattr(pygame.time, "get_ticks", lambda: now[0])
    monkeypatch.setattr(
        OptionImageOverlay,
        "_load_images",
        lambda self: {
            number: pygame.Surface((640, 602), pygame.SRCALPHA)
            for number in range(1, 7)
        },
    )
    subsystem = OptionSubsystem.image_option(pygame.Surface((1_440, 1_080)))
    events = []
    for _ in range(4):
        events.extend(
            [
                pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RIGHT),
                pygame.event.Event(pygame.KEYUP, key=pygame.K_RIGHT),
            ]
        )

    subsystem.handle_events(events)

    assert subsystem.overlay.selected_number == 5
    assert subsystem.overlay.is_move_animating is True
    assert subsystem._held_direction_key is None

    now[0] += 100
    subsystem.handle_events([])
    assert subsystem.overlay.selected_number == 5
    assert subsystem.overlay.is_move_animating is False


def test_morning_flow_builds_explicit_no_loading_handoff():
    dialogue = object()
    flow = MorningFlow(None, dialogue_factory=lambda screen, event_file: dialogue)
    flow.preload_dialogue()

    request = flow.take_dialogue_request()

    assert request.event_file == MorningFlow.DIALOGUE_FILE
    assert request.preloaded_subsystem is dialogue
    assert request.display_loading is False
    assert request.completion == Navigate(Scene.MAP)


def test_scene_manager_cleans_up_before_entering_next_scene():
    calls = []
    first = types.SimpleNamespace(
        cleanup=lambda: calls.append("first.cleanup"),
        on_enter=lambda: calls.append("first.enter"),
    )
    second = types.SimpleNamespace(
        cleanup=lambda: calls.append("second.cleanup"),
        on_enter=lambda: calls.append("second.enter"),
    )
    manager = SceneManager()

    manager.switch_to(first, "first")
    manager.switch_to(second, "second")

    assert calls == ["first.enter", "first.cleanup", "second.enter"]
