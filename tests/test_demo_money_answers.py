"""The GD001 tutorial accepts plain money-shortage answers in either spelling."""

from types import SimpleNamespace

import pytest

from core.services.seed_manager import SeedManager


@pytest.mark.parametrize("answer", [
    "桃子は金が無い", "お金が無い", "お金がない", "桃子はお金がない",
    "桃子はお金が無い", "桃子は金がない", "金が無い", "金がない",
])
def test_gd_money_accepts_plain_shortage_answers_without_inference(answer):
    manager = SeedManager()
    verdict = manager.judge_answer("MOMOKO_GD_MONEY", answer)
    assert verdict["result"] == "correct", (answer, verdict)
    assert verdict["reason_codes"] == ("exact_answer",)
    assert manager.model_status() == "not_loaded"


@pytest.mark.parametrize("answer", [
    "桃子はお金がないわけではない", "桃子は金欠じゃない",
    "桃子は借金でお金がない", "桃子はお金がないしディズニーも嫌い",
    "純一はお金がない", "桃子はお金がある",
])
def test_gd_money_still_rejects_wrong_reasons_and_negations(answer):
    manager = SeedManager()
    verdict = manager.judge_answer("MOMOKO_GD_MONEY", answer)
    assert verdict["result"] == "incorrect", (answer, verdict)


@pytest.mark.parametrize("answer", [
    "桃子は金が無い", "お金が無い", "お金がない", "桃子はお金がない",
])
def test_gd_money_input_sets_the_authored_correct_branch(answer, tmp_path, monkeypatch):
    import pygame
    from dialogue.controller2 import _submit_seed_answer
    from dialogue.data_normalizer import normalize_dialogue_data
    from dialogue.dialogue_loader import DialogueLoader
    from dialogue.scenario_manager import _handle_seed_answer
    from dialogue.seed_answer_overlay import SeedAnswerOverlay

    monkeypatch.setenv("MOKISS_PROFILE_ROOT", str(tmp_path))
    monkeypatch.setattr(SeedAnswerOverlay, "_start_text_input", lambda self: None)
    monkeypatch.setattr("core.services.time_manager.get_time_manager", lambda: SimpleNamespace(
        current_year=1999, current_month=5, current_day=31,
    ))
    manager = SeedManager()
    loader = DialogueLoader()
    data = normalize_dialogue_data(loader.load_dialogue_from_ks("events/GD001.ks"))
    source = next(i for i, item in enumerate(data)
                  if isinstance(item, dict) and item.get("type") == "seed_answer")
    branch = next(item for item in data[source + 1:]
                  if isinstance(item, dict) and item.get("type") == "if_start")
    echoes = []
    state = {
        "seed_manager": manager, "dialogue_loader": loader, "screen": None,
        "current_paragraph": source,
        "text_renderer": SimpleNamespace(set_dialogue=lambda *args: echoes.append(args)),
    }
    _handle_seed_answer(state, data[source])
    overlay = state["seed_answer_overlay"]
    try:
        # Conversion confirmation remains separate from answer submission.
        overlay.handle_event(pygame.event.Event(pygame.TEXTEDITING, text=answer, start=0, length=len(answer)))
        enter = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN, mod=0)
        assert overlay.handle_event(enter) is None
        overlay.handle_event(pygame.event.Event(pygame.TEXTINPUT, text=answer))
        submitted = overlay.handle_event(enter)
        assert submitted == answer
        _submit_seed_answer(state, submitted)
        assert overlay.last_verdict["result"] == "correct"
        assert state["seed_answer_overlay"] is None
        assert loader.check_condition(branch["condition"])
        assert manager.state["turning_point_results"][overlay.turning_point_id]["answer_text"] == answer
        assert echoes == [(answer, "純一")]
    finally:
        overlay.close()
