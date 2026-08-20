from types import SimpleNamespace

import pygame

from dialogue import scenario_manager
from dialogue.dialogue_subsystem import DialogueSubsystem


def test_runtime_sestop_and_bgmend_call_audio_managers():
    calls = []
    game_state = {
        "se_manager": SimpleNamespace(stop_all_se=lambda: calls.append("se_stop")),
        "bgm_manager": SimpleNamespace(
            fade_out=lambda seconds: calls.append(("bgm_fade", seconds)),
            stop_bgm=lambda: calls.append("bgm_stop"),
        ),
    }

    scenario_manager._ir_handle_se_stop(game_state)
    scenario_manager._ir_handle_bgm_end(game_state, {"fade_time": 2.0})
    scenario_manager._ir_handle_bgm_end(game_state, {"fade_time": 0})

    assert calls == ["se_stop", ("bgm_fade", 2.0), "bgm_stop"]


def test_loop_mode_change_restarts_same_busy_bgm(monkeypatch):
    played = []
    manager = SimpleNamespace(
        current_bgm="theme.ogg",
        current_loop=False,
        get_bgm_for_scene=lambda filename: filename,
        play_bgm=lambda *args, **kwargs: played.append((args, kwargs)),
    )
    monkeypatch.setattr(pygame.mixer.music, "get_busy", lambda: True)

    scenario_manager._ir_handle_bgm_play(
        {"bgm_manager": manager},
        {"file": "theme.ogg", "volume": 0.5, "loop": "true", "fade_time": 1.0},
    )

    assert played == [(('theme.ogg', 0.5, True), {"fade_time": 1.0})]


def test_script_end_waits_for_bgm_fade_before_returning(monkeypatch):
    fades = []
    bgm = SimpleNamespace(
        current_bgm="theme.ogg",
        fade_out=lambda seconds: fades.append(seconds),
    )
    subsystem = SimpleNamespace(
        _ending_bgm_deadline=None,
        _last_saved_paragraph=-1,
        game_state={"bgm_manager": bgm, "current_paragraph": -1},
        screen=None,
        _save_dialogue_state=lambda paragraph: None,
    )
    monkeypatch.setattr(pygame.event, "get", lambda *args: [])
    ticks = iter((100, 500, 1100))
    monkeypatch.setattr(pygame.time, "get_ticks", lambda: next(ticks))
    monkeypatch.setattr("dialogue.controller2.handle_events", lambda *args: False)

    assert DialogueSubsystem.handle_events(subsystem, []) is None
    assert fades == [1.0]
    assert DialogueSubsystem.handle_events(subsystem, []) is None
    assert DialogueSubsystem.handle_events(subsystem, []) == "dialogue_ended"
