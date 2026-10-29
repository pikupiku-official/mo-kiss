"""Regressions for ordered text input and advances buffered at scene endings."""

import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pygame
import pytest

from core.ui.text_edit import TextEditBuffer
from dialogue import controller2
from dialogue.dialogue_subsystem import DialogueSubsystem
from dialogue.seed_answer_overlay import SeedAnswerOverlay


@pytest.fixture
def scene():
    pygame.init()
    pygame.display.set_mode((100, 100))
    pygame.event.clear()
    scene = DialogueSubsystem.__new__(DialogueSubsystem)
    scene.screen = pygame.display.get_surface()
    scene._ending_bgm_deadline = None
    scene._last_saved_paragraph = 0
    scene.game_state = {"current_paragraph": 0}
    yield scene
    pygame.quit()


def key(kind, value):
    return pygame.event.Event(kind, key=value, mod=0)


def test_text_edit_and_submit_retain_event_order(scene, monkeypatch):
    overlay = SeedAnswerOverlay.__new__(SeedAnswerOverlay)
    overlay.editor = TextEditBuffer("", max_length=120)
    overlay.suspended = False
    overlay.last_verdict = None
    scene.game_state["seed_answer_overlay"] = overlay
    answers = []
    monkeypatch.setattr(controller2, "_submit_seed_answer", lambda gs, text: answers.append(text))
    for event in (
        pygame.event.Event(pygame.TEXTINPUT, text="a"),
        key(pygame.KEYDOWN, pygame.K_BACKSPACE),
        pygame.event.Event(pygame.TEXTINPUT, text="b"),
        key(pygame.KEYDOWN, pygame.K_RETURN),
    ):
        pygame.event.post(event)

    assert scene.handle_events() is None
    assert answers == ["b"]


def test_ime_confirmation_enter_does_not_submit_the_answer(scene, monkeypatch):
    overlay = SeedAnswerOverlay.__new__(SeedAnswerOverlay)
    overlay.editor = TextEditBuffer("", max_length=120)
    overlay.suspended = False
    overlay.last_verdict = None
    scene.game_state["seed_answer_overlay"] = overlay
    answers = []
    monkeypatch.setattr(controller2, "_submit_seed_answer", lambda gs, text: answers.append(text))
    for event in (
        pygame.event.Event(pygame.TEXTEDITING, text="ka", start=0, length=2),
        key(pygame.KEYDOWN, pygame.K_RETURN),
        pygame.event.Event(pygame.TEXTINPUT, text="a"),
        pygame.event.Event(pygame.TEXTEDITING, text="", start=0, length=0),
    ):
        pygame.event.post(event)
    assert scene.handle_events() is None
    assert overlay.text == "a"
    assert answers == []


def test_ending_fade_drains_advances_and_keeps_escape_available(scene, monkeypatch):
    monkeypatch.setattr(pygame.time, "get_ticks", lambda: 1000)
    scene._ending_bgm_deadline = 2000
    for _ in range(20):
        pygame.event.post(key(pygame.KEYDOWN, pygame.K_RETURN))
        pygame.event.post(key(pygame.KEYUP, pygame.K_RETURN))
    assert scene.handle_events() is None
    assert pygame.event.get() == []

    pygame.event.post(key(pygame.KEYDOWN, pygame.K_ESCAPE))
    assert scene.handle_events() == "show_option"
    assert pygame.event.get() == []


def test_escape_does_not_replay_other_input_into_settings(scene):
    pygame.event.post(key(pygame.KEYDOWN, pygame.K_ESCAPE))
    pygame.event.post(key(pygame.KEYDOWN, pygame.K_RETURN))
    pygame.event.post(key(pygame.KEYUP, pygame.K_RETURN))
    assert scene.handle_events() == "show_option"
    assert pygame.event.get() == []


def test_input_failure_cannot_complete_and_skip_the_scene(scene, monkeypatch):
    def fail(*args, **kwargs):
        raise RuntimeError("input failed")

    monkeypatch.setattr(controller2, "handle_events", fail)
    assert scene.handle_events() is None
    assert not scene.game_state.get("ks_finished", False)


def test_ending_deadline_drops_last_burst_before_transition(scene, monkeypatch):
    monkeypatch.setattr(pygame.time, "get_ticks", lambda: 2000)
    scene._ending_bgm_deadline = 2000
    pygame.event.post(key(pygame.KEYDOWN, pygame.K_RETURN))
    assert scene.handle_events() == "dialogue_ended"
    assert pygame.event.get() == []


def test_burst_of_complete_presses_is_one_advance_per_frame():
    state = {}
    burst = [event for _ in range(20) for event in (
        key(pygame.KEYDOWN, pygame.K_RETURN),
        key(pygame.KEYUP, pygame.K_RETURN),
    )]
    assert len(controller2._discard_blocked_gameplay_events(state, burst)) == 1
    assert controller2._discard_blocked_gameplay_events(state, []) == []
    assert len(controller2._discard_blocked_gameplay_events(
        state, [key(pygame.KEYDOWN, pygame.K_RETURN)]
    )) == 1
