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


@pytest.mark.parametrize("turning_point", ["MOMOKO_GD_MONEY", "MOMOKO_TORO"])
@pytest.mark.parametrize("answer", ["バナナ", "うんこ", "あいうえお", "こんにちは", "a", "123", "わからない", "今日はいい天気"])
def test_demo_rejects_unrelated_answers(manager, turning_point, answer):
    verdict = manager.judge_answer(turning_point, answer)
    assert verdict["result"] == "incorrect", (answer, verdict)
    assert verdict["reason_codes"] == ("missing_topic_anchor",)


@pytest.mark.parametrize("answer", [
    "桃子は家族とうまくいっていない", "家族と不仲", "家庭の問題",
    "お父さんとお母さんが喧嘩している", "家族のことで悩んでいるから帰りたくない",
    "家で両親がもめている",
])
def test_demo_accepts_family_problem_deductions(manager, answer):
    verdict = manager.judge_answer("MOMOKO_TORO", answer)
    assert verdict["result"] == "correct", (answer, verdict)


@pytest.mark.parametrize("answer", [
    "桃子は家族が好き", "家族と旅行に行きたい", "家族が病気になった",
    "両親が亡くなった", "家族と不仲なわけではない", "妹と遊びたい",
    "桃子の父は宇宙人", "家族はバナナ", "家族", "父", "妹",
])
def test_demo_retries_wrong_family_explanations(manager, answer):
    verdict = manager.judge_answer("MOMOKO_TORO", answer)
    assert verdict["result"] in ("incorrect", "borderline"), (answer, verdict)


@pytest.mark.parametrize("answer", ["お金はバナナ", "財布", "お金がある", "お金があります", "桃子は余裕がある"])
def test_demo_rejects_money_words_without_the_deduction(manager, answer):
    verdict = manager.judge_answer("MOMOKO_GD_MONEY", answer)
    assert verdict["result"] in ("incorrect", "borderline"), (answer, verdict)


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

    assert verdict["result"] == "correct", (answer, verdict)
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


@pytest.mark.parametrize(
    "answer",
    [
        "増田は包茎だ",
        "増田は包茎を隠している",
        "増田は真性包茎という言葉が嫌いだ",
        "増田は真性包茎の友達がいる",
        "増田は真性包茎の人を馬鹿にしている",
        "増田は真性包茎を治した",
        "真性包茎なのは純一だ",
    ],
)
def test_ruri_rejects_related_statements_that_do_not_make_the_deduction(
    manager, answer
):
    verdict = manager.judge_answer("MASUDA_TP1", answer)

    assert verdict["result"] == "incorrect", (answer, verdict)


@pytest.mark.parametrize(
    "answer",
    [
        "増田は真性包茎かもしれない",
        "増田は真性包茎の可能性がある",
        "増田が真性包茎かどうかは分からない",
        "増田はたぶん真性包茎だ",
        "増田は真性包茎の可能性が高い",
        "もしかすると増田は真性包茎だ",
        "増田は真性包茎なのかもしれません",
        "増田は真性包茎かどうか怪しい",
    ],
)
def test_ruri_keeps_uncertain_deductions_out_of_the_correct_branch(manager, answer):
    verdict = manager.judge_answer("MASUDA_TP1", answer)

    assert verdict["result"] != "correct", (answer, verdict)
