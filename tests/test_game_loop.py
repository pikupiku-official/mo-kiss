from types import SimpleNamespace

import pygame

from core.runtime.game_loop import GameLoop
from core.ui.debug_hud import get_debug_hud


class _DialogueMarker:
    pass


class _Clock:
    def __init__(self, calls):
        self.calls = calls

    def tick(self, fps):
        self.calls.append(("tick", fps))


def _application(calls, subsystem):
    return SimpleNamespace(
        running=True,
        slot_screen=None,
        option_subsystem=None,
        current_subsystem=subsystem,
        clock=_Clock(calls),
        _gather_normalized_events=lambda: ["event"],
        _poll_mock_overlay_shortcuts=lambda events: False,
        _queue_events_for_dialogue=lambda events: calls.append(("queue", events)),
        _handle_transition=lambda result: calls.append(("transition", result)),
        _present_virtual_screen=lambda: calls.append("present"),
        _handle_slot_result=lambda result: None,
        _handle_overlay_result=lambda result: None,
        _render_option_notice=lambda: None,
    )


def test_normal_frame_dispatches_updates_and_presents(monkeypatch):
    calls = []

    class Subsystem:
        def handle_events(self, events):
            calls.append(("handle", events))
            return "go_to_map"

        def update(self):
            calls.append("update")

        def render(self):
            calls.append("render")

    app = _application(calls, Subsystem())
    monkeypatch.setattr(pygame.display, "flip", lambda: calls.append("flip"))

    GameLoop(app, dialogue_type=_DialogueMarker).run_frame()

    assert calls == [
        ("handle", ["event"]),
        ("transition", "go_to_map"),
        "update",
        "render",
        "present",
        "flip",
        ("tick", 30),
    ]


def test_frame_keeps_compatibility_when_slot_screen_was_never_initialized(
    monkeypatch,
):
    calls = []

    class Subsystem:
        def handle_events(self, events):
            return None

        def update(self):
            pass

        def render(self):
            pass

    app = _application(calls, Subsystem())
    del app.slot_screen
    monkeypatch.setattr(pygame.display, "flip", lambda: None)

    GameLoop(app, dialogue_type=_DialogueMarker).run_frame()

    assert calls[-1] == ("tick", 30)


def test_closing_option_still_renders_the_resulting_base_scene(monkeypatch):
    calls = []

    class Subsystem:
        def render(self):
            calls.append("base.render")

    class Option:
        def handle_events(self, events):
            calls.append(("option.handle", events))
            return "resume"

    app = _application(calls, Subsystem())
    app.option_subsystem = Option()

    def handle_option(result):
        calls.append(("option.result", result))
        app.option_subsystem = None

    app._handle_overlay_result = handle_option
    monkeypatch.setattr(pygame.display, "flip", lambda: calls.append("flip"))

    GameLoop(app, dialogue_type=_DialogueMarker).run_frame()

    assert "base.render" in calls
    assert "present" in calls
    assert calls[-1] == ("tick", 30)


def test_dialogue_frame_requeues_events_for_legacy_input(monkeypatch):
    calls = []

    class Dialogue(_DialogueMarker):
        def handle_events(self):
            calls.append("dialogue.handle")

        def update(self):
            calls.append("dialogue.update")

        def render(self):
            calls.append("dialogue.render")

    app = _application(calls, Dialogue())
    monkeypatch.setattr(pygame.display, "flip", lambda: None)

    GameLoop(app, dialogue_type=_DialogueMarker).run_frame()

    assert calls[:4] == [
        ("queue", ["event"]),
        "dialogue.handle",
        "dialogue.update",
        "dialogue.render",
    ]


def test_f8_toggles_global_debug_hud_and_is_consumed(monkeypatch):
    calls = []

    class Subsystem:
        def handle_events(self, events):
            calls.append(events)

        def update(self):
            pass

        def render(self):
            pass

    app = _application(calls, Subsystem())
    app._gather_normalized_events = lambda: [
        pygame.event.Event(pygame.KEYDOWN, key=pygame.K_F8, mod=0)
    ]
    hud = get_debug_hud()
    hud.enabled = False
    monkeypatch.setattr(pygame.display, "flip", lambda: None)

    GameLoop(app, dialogue_type=_DialogueMarker).run_frame()

    assert hud.enabled is True
    assert calls[0] == []
    hud.enabled = False


def test_f9_is_routed_before_dialogue_legacy_event_queue(monkeypatch):
    calls = []

    class SeedList:
        def __init__(self):
            self.is_showing = False

        def toggle(self):
            self.is_showing = not self.is_showing
            return self.is_showing

    class Dialogue(_DialogueMarker):
        def __init__(self):
            self.seed_list = SeedList()
            self.game_state = {"seed_list_overlay": self.seed_list}

        def handle_events(self):
            calls.append("dialogue.handle")

        def update(self):
            pass

        def render(self):
            pass

    app = _application(calls, Dialogue())
    app._gather_normalized_events = lambda: [
        pygame.event.Event(pygame.KEYDOWN, key=pygame.K_F9, mod=0)
    ]
    monkeypatch.setattr(pygame.display, "flip", lambda: None)

    GameLoop(app, dialogue_type=_DialogueMarker).run_frame()

    assert app.current_subsystem.seed_list.is_showing is True
    assert ("queue", []) in calls
