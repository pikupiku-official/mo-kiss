"""Answer prompts must hold their source step until the player submits."""
from types import SimpleNamespace

import pytest

from dialogue import controller2, scenario_manager


@pytest.mark.parametrize("mode", ["auto_mode", "skip_mode"])
def test_opening_seed_answer_stops_automatic_playback(monkeypatch, mode):
    renderer = SimpleNamespace(auto_mode=False, skip_mode=False, timer_resets=0)
    setattr(renderer, mode, True)

    def reset_timer():
        renderer.timer_resets += 1

    renderer.reset_auto_timer = reset_timer
    monkeypatch.setattr(
        "dialogue.seed_answer_overlay.SeedAnswerOverlay",
        lambda *args, **kwargs: SimpleNamespace(initial_text=kwargs["initial_text"]),
    )
    gs = {
        "screen": object(),
        "seed_manager": object(),
        "text_renderer": renderer,
        "current_paragraph": 10,
        "ir_step_index": 8,
    }

    assert scenario_manager._handle_seed_answer(
        gs, {"turning_point_id": "MOMOKO_GD_MONEY"}
    )

    assert renderer.auto_mode is False
    assert renderer.skip_mode is False
    assert renderer.timer_resets == 1
    assert gs["seed_answer_overlay"] is not None
    assert gs["last_seed_answer_source_index"] == 10


@pytest.mark.parametrize("mode", ["auto_mode", "skip_mode"])
def test_ready_auto_and_finished_animation_cannot_leave_pending_answer(monkeypatch, mode):
    # Even stale readiness or a later mode change must not consume the if
    # blocks while their result flag is absent (or left over from a retry).
    renderer = SimpleNamespace(
        auto_mode=False,
        skip_mode=False,
        update=lambda: None,
        is_ready_for_auto_advance=lambda: True,
        reset_auto_timer=lambda: None,
    )
    setattr(renderer, mode, True)
    for name in (
        "setup_text_renderer_settings",
        "update_character_animations", "update_background_animation",
        "update_cg_animation", "update_fade_animation",
    ):
        monkeypatch.setattr(controller2, name, lambda gs: None)
    monkeypatch.setattr("dialogue.movie_manager.update_movie", lambda gs: None)
    monkeypatch.setattr("dialogue.rain_manager.update_rain", lambda gs: None)
    monkeypatch.setattr("dialogue.haze_manager.update_haze", lambda gs: None)
    advances = []
    monkeypatch.setattr(controller2, "advance_dialogue", lambda gs: advances.append(True) or True)
    gs = {
        "text_renderer_initialized": True,
        "text_renderer": renderer,
        "choice_renderer": SimpleNamespace(is_choice_showing=lambda: False),
        "backlog_manager": SimpleNamespace(is_showing_backlog=lambda: False),
        "use_ir": True,
        "ir_waiting_for_anim": True,
        "seed_answer_overlay": object(),
        "current_paragraph": 10,
        "ir_step_index": 8,
        "dialogue_data": [],
    }

    controller2.update_game(gs)

    assert advances == []
    assert (gs["current_paragraph"], gs["ir_step_index"]) == (10, 8)
    assert not gs.get("ks_finished")


def test_progression_resumes_after_answer_overlay_closes(monkeypatch):
    advances = []
    monkeypatch.setattr(controller2, "advance_dialogue", lambda gs: advances.append(True) or True)
    gs = {
        "seed_answer_overlay": None,
        "current_paragraph": 0,
        "dialogue_data": [object(), object()],
    }

    assert controller2.advance_to_next_dialogue(gs)
    assert advances == [True]


@pytest.mark.parametrize("mode", ["auto_mode", "skip_mode"])
def test_automatic_playback_marks_the_last_paragraph_finished(monkeypatch, mode):
    renderer = SimpleNamespace(
        auto_mode=False, skip_mode=False, debug=False,
        update=lambda: None, is_ready_for_auto_advance=lambda: True,
        reset_auto_timer=lambda: None,
    )
    setattr(renderer, mode, True)
    for name in ("setup_text_renderer_settings", "update_character_animations", "update_background_animation",
                 "update_cg_animation", "update_fade_animation"):
        monkeypatch.setattr(controller2, name, lambda gs: None)
    monkeypatch.setattr("dialogue.movie_manager.update_movie", lambda gs: None)
    monkeypatch.setattr("dialogue.rain_manager.update_rain", lambda gs: None)
    monkeypatch.setattr("dialogue.haze_manager.update_haze", lambda gs: None)
    gs = {
        "text_renderer_initialized": True, "text_renderer": renderer,
        "choice_renderer": SimpleNamespace(is_choice_showing=lambda: False),
        "backlog_manager": SimpleNamespace(is_showing_backlog=lambda: False),
        "current_paragraph": 0, "dialogue_data": [{}],
    }
    controller2.update_game(gs)
    assert gs.get("ks_finished") is True
    assert not renderer.auto_mode and not renderer.skip_mode
