"""The GD005 turning point must use the bundled model for paraphrases."""

import pytest

from core.services.seed_manager import SeedManager


@pytest.fixture(scope="module")
def manager():
    manager = SeedManager()
    assert manager.requires_semantic_judge("MOMOKO_TP1")
    manager.preload_answer_model()
    manager._preload_thread.join(30)
    assert manager.model_status() == "ready"
    return manager


@pytest.mark.parametrize("answer,expected", [
    ("家族と折り合いが悪いから", "borderline"),
    ("両親の仲が悪くて家に帰りたくない", "correct"),
    ("家庭のトラブルを抱えている", "correct"),
    ("今月はお金が足りない", "incorrect"),
    ("部活の練習が長引いている", "incorrect"),
    ("家族とは仲良くやっている", "incorrect"),
    ("純一の両親が喧嘩している", "incorrect"),
])
def test_real_model_judges_demo_answers(manager, answer, expected):
    verdict = manager.judge_answer("MOMOKO_TP1", answer)
    assert verdict["judge_version"].startswith("ruri-v3-30m-int8-")
    assert verdict["result"] == expected, verdict
