import os

import pytest

pytest.importorskip("numpy")
pytest.importorskip("onnxruntime")
pytest.importorskip("sentencepiece")

from core.path_utils import get_project_root
from core.services.seed_manager import SeedManager


MODEL_PATH = os.path.join(
    get_project_root(), "models", "ruri-v3-30m-int8", "model_int8.onnx"
)
pytestmark = pytest.mark.skipif(
    not os.path.isfile(MODEL_PATH), reason="bundled semantic model is unavailable"
)


@pytest.fixture(scope="module")
def manager():
    return SeedManager()


@pytest.mark.parametrize(
    "answer",
    [
        "増田は真性包茎なんだ",
        "増田は真性の包茎を隠している",
        "増田が温泉を断るのは真性包茎を知られたくないからだ",
        "包皮を剥けないのを隠している",
    ],
)
def test_ruri_accepts_semantic_paraphrases(manager, answer):
    verdict = manager.judge_answer("MASUDA_TP1", answer)

    assert verdict["result"] == "correct"
    assert verdict["judge_version"].startswith("ruri-v3-30m-int8-")
    assert verdict["semantic_score"] >= 0.95


@pytest.mark.parametrize(
    "answer",
    [
        "増田は真性包茎じゃない",
        "増田は仮性の包茎だ",
        "あいつは仮性包茎らしい",
        "増田は裸を見せるのが恥ずかしいだけ",
        "増田は包茎の疑いがある",
        "増田は包茎を馬鹿にしている",
        "増田は真性包茎を治療した",
        "増田は真性包茎の友人がいる",
        "真性包茎なのは純一だ",
        "増田は体に傷がある",
    ],
)
def test_ruri_hard_negatives_do_not_false_accept(manager, answer):
    verdict = manager.judge_answer("MASUDA_TP1", answer)

    assert verdict["result"] == "incorrect"
    assert verdict["reason_codes"][0] in {
        "exact_hard_negative",
        "hard_negative_match",
        "hard_negative_nearer",
        "reject_pattern_match",
    }


def test_related_but_incomplete_answer_prefers_negative_anchor(manager):
    verdict = manager.judge_answer("MASUDA_TP1", "増田は温泉が嫌いだ")

    assert verdict["result"] == "incorrect"
    assert verdict["reason_codes"] == ("hard_negative_nearer",)
