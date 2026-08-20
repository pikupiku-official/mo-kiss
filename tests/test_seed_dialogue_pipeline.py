from __future__ import annotations

import csv
import datetime
from pathlib import Path

import pygame
import pytest

from core.flow.event_progress import EventProgress
from core.services.save_manager import SaveManager
from dialogue.data_normalizer import normalize_dialogue_data
from dialogue.dialogue_loader import DialogueLoader
from dialogue.ir_builder import build_ir_from_normalized
from dialogue.seed_answer_overlay import SeedAnswerOverlay


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_seed_answer_and_event_control_survive_loader_normalizer_and_ir(tmp_path):
    ks_path = tmp_path / "seed.ks"
    ks_path.write_text(
        '[seed_answer turning_point="MASUDA_TP1"]\n'
        '[event_control unlock="NEXT" lock="CURRENT"]\n',
        encoding="utf-8",
    )

    raw = DialogueLoader(debug=False).load_dialogue_from_ks(str(ks_path))
    assert raw == [
        {"type": "seed_answer", "turning_point_id": "MASUDA_TP1"},
        {"type": "event_control", "unlock": ["NEXT"], "lock": ["CURRENT"]},
    ]
    normalized = normalize_dialogue_data(raw)
    assert normalized == raw

    ir = build_ir_from_normalized(normalized)
    actions = [step["actions"][0]["action"] for step in ir["steps"]]
    assert actions == ["seed_answer", "event_control"]


def test_tutorial_ks_files_form_explicit_authored_event_sequence():
    expected = [
        ("TANE_MASUDA_01.ks", "MASUDA_TP1_001", "TANE_MASUDA_02"),
        ("TANE_MASUDA_02.ks", "MASUDA_TP1_002", "TANE_MASUDA_03"),
        ("TANE_MASUDA_03.ks", "MASUDA_TP1_003", "TANE_MASUDA_TP1"),
    ]
    for filename, seed_id, next_event in expected:
        text = (PROJECT_ROOT / "events" / filename).read_text(encoding="utf-8")
        assert f'[seed id="{seed_id}"]' in text
        assert f'unlock="{next_event}"' in text
        assert f'lock="{filename.removesuffix(".ks")}"' in text

    turning_point = (
        PROJECT_ROOT / "events" / "TANE_MASUDA_TP1.ks"
    ).read_text(encoding="utf-8")
    assert '[seed_answer turning_point="MASUDA_TP1"]' in turning_point
    assert 'MASUDA_TP1_RESULT==correct' in turning_point
    assert 'MASUDA_TP1_RESULT==incorrect' in turning_point
    assert "増田は真性包茎なんだ" in turning_point


def test_tutorial_events_are_registered_for_map_and_masuda_has_an_icon_slot():
    events_csv = (PROJECT_ROOT / "events" / "events.csv").read_text(encoding="utf-8")
    for event_id in (
        "TANE_MASUDA_01",
        "TANE_MASUDA_02",
        "TANE_MASUDA_03",
        "TANE_MASUDA_TP1",
    ):
        assert f"{event_id},5月31日の朝,6月30日の放課後" in events_csv
    map_source = (PROJECT_ROOT / "map" / "map.py").read_text(encoding="utf-8")
    assert 'Character("増田",' in map_source

    from map.map import GameEvent

    event = GameEvent(
        "TANE_MASUDA_01",
        "5月31日の朝",
        "6月30日の放課後",
        "朝;昼;放課後;夜",
        "増田",
        "教室",
        "タネチュートリアル",
    )
    assert event.is_in_time_period(datetime.date(1999, 5, 31), "朝") is True
    assert event.is_in_time_period(datetime.date(1999, 6, 30), "夜") is True


class _FakeTimeManager:
    current_year = 1999
    current_month = 6
    current_day = 2

    def __init__(self):
        self.advanced = False

    def get_full_time_string(self):
        return "1999-06-02 朝"

    def get_current_period(self):
        return "朝"

    def is_after_school(self):
        return False

    def advance_period(self):
        self.advanced = True


class _FakeSeedManager:
    def __init__(self):
        self.completed = []

    def complete_event(self, event_id, game_date):
        self.completed.append((event_id, game_date))
        return ["MASUDA_TP1_001"]


def test_regular_event_completion_commits_pending_seeds(tmp_path):
    events_dir = tmp_path / "events"
    state_dir = tmp_path / "data" / "current_state"
    events_dir.mkdir(parents=True)
    state_dir.mkdir(parents=True)
    (events_dir / "events.csv").write_text(
        "イベントID,イベント開始日時\nTANE_MASUDA_01,\n", encoding="utf-8"
    )
    (state_dir / "completed_events.csv").write_text(
        "イベントID,実行日時,実行回数,有効フラグ\n"
        "TANE_MASUDA_01,,0,TRUE\n",
        encoding="utf-8",
    )
    time_manager = _FakeTimeManager()
    seed_manager = _FakeSeedManager()
    progress = EventProgress(
        project_root=str(tmp_path),
        time_manager_getter=lambda: time_manager,
        seed_manager_getter=lambda: seed_manager,
    )

    decision = progress.complete_dialogue("TANE_MASUDA_01")

    assert seed_manager.completed == [("TANE_MASUDA_01", "1999-06-02")]
    assert decision.next_mode == "map"
    assert decision.time_advanced is True
    assert time_manager.advanced is True
    with (state_dir / "completed_events.csv").open(encoding="utf-8") as handle:
        row = next(csv.DictReader(handle))
    assert row["実行回数"] == "1"


def test_seed_save_failure_does_not_prevent_return_to_next_map_period(tmp_path):
    events_dir = tmp_path / "events"
    state_dir = tmp_path / "data" / "current_state"
    events_dir.mkdir(parents=True)
    state_dir.mkdir(parents=True)
    (events_dir / "events.csv").write_text(
        "イベントID,イベント開始日時\nTANE_MASUDA_01,\n", encoding="utf-8"
    )
    (state_dir / "completed_events.csv").write_text(
        "イベントID,実行日時,実行回数,有効フラグ\n"
        "TANE_MASUDA_01,,0,TRUE\n",
        encoding="utf-8",
    )
    time_manager = _FakeTimeManager()

    class BrokenSeeds:
        def complete_event(self, event_id, game_date):
            raise OSError("seed state is temporarily unavailable")

    progress = EventProgress(
        project_root=str(tmp_path),
        time_manager_getter=lambda: time_manager,
        seed_manager_getter=lambda: BrokenSeeds(),
    )

    decision = progress.complete_dialogue("TANE_MASUDA_01")

    assert decision.next_mode == "map"
    assert decision.time_advanced is True
    assert time_manager.advanced is True


def test_masuda_seed_click_annotations_are_embedded_in_each_ks_file():
    expected = (
        ("TANE_MASUDA_01.ks", "MASUDA_TP1_001"),
        ("TANE_MASUDA_02.ks", "MASUDA_TP1_002"),
        ("TANE_MASUDA_03.ks", "MASUDA_TP1_003"),
    )
    for filename, seed_id in expected:
        loader = DialogueLoader(debug=False)
        raw = loader.load_dialogue_from_ks(str(PROJECT_ROOT / "events" / filename))
        annotation = loader.seed_annotations[seed_id]
        assert len(annotation) == 2
        assert all(line["speaker"] and line["text"] for line in annotation)
        assert all(item.get("type") != "seed_dialogue" for item in raw)


def test_seed03_nested_quote_does_not_break_seed_markup():
    from dialogue.inline_markup import SeedSpan, parse_inline_markup

    raw = DialogueLoader(debug=False).load_dialogue_from_ks(
        str(PROJECT_ROOT / "events" / "TANE_MASUDA_03.ks")
    )
    seed_line = next(
        item["text"]
        for item in raw
        if item.get("type") == "dialogue" and "MASUDA_TP1_003" in item.get("text", "")
    )
    tokens = parse_inline_markup(seed_line)
    seed = next(token for token in tokens if isinstance(token, SeedSpan))

    assert seed.base == "下ネタに寛容な彼が『包茎』というワードには絶対に触れない"


def test_final_event_control_frame_is_safe_to_draw():
    from dialogue.character_manager import draw_characters

    draw_characters(
        {
            "dialogue_data": [{"type": "event_control"}],
            "current_paragraph": 0,
            "image_manager": None,
            "screen": pygame.Surface((16, 16)),
            "active_characters": [],
        }
    )


def test_ks_finished_on_enter_returns_dialogue_ended_in_same_frame(monkeypatch):
    from dialogue import controller2
    from dialogue.dialogue_subsystem import DialogueSubsystem

    subsystem = DialogueSubsystem.__new__(DialogueSubsystem)
    subsystem._ending_bgm_deadline = None
    subsystem._last_saved_paragraph = -1
    subsystem.game_state = {
        "ks_finished": False,
        "current_paragraph": 5,
        "bgm_manager": None,
    }
    subsystem._save_dialogue_state = lambda paragraph: None

    def finish_on_this_enter(game_state, screen):
        game_state["ks_finished"] = True
        return True

    monkeypatch.setattr(controller2, "handle_events", finish_on_this_enter)

    assert subsystem.handle_events() == "dialogue_ended"


def test_save_manager_includes_seed_state_and_old_save_fallback(tmp_path):
    for directory in (
        tmp_path / "data" / "current_state",
        tmp_path / "data" / "save" / "saveslot_01",
        tmp_path / "data" / "templates",
    ):
        directory.mkdir(parents=True)
    template = tmp_path / "data" / "templates" / "seed_state_template.json"
    template.write_text('{"schema_version": 1, "acquired": {}}\n', encoding="utf-8")
    completed_header = "イベントID,実行日時,実行回数,有効フラグ\n"
    (tmp_path / "data" / "templates" / "completed_events_template.csv").write_text(
        completed_header + "OLD,,0,TRUE\nTANE_MASUDA_01,,0,TRUE\n",
        encoding="utf-8",
    )
    (tmp_path / "data" / "save" / "saveslot_01" / "completed_events.csv").write_text(
        completed_header + "OLD,1999-06-01,1,FALSE\n",
        encoding="utf-8",
    )
    manager = SaveManager(project_root=str(tmp_path))

    assert "seed_state.json" in manager.state_files
    manager._reload_managers = lambda: None
    assert manager.load_game("saveslot_01") is True
    restored = tmp_path / "data" / "current_state" / "seed_state.json"
    assert restored.read_text(encoding="utf-8") == template.read_text(encoding="utf-8")
    completed = (
        tmp_path / "data" / "current_state" / "completed_events.csv"
    ).read_text(encoding="utf-8")
    assert "OLD,1999-06-01,1,FALSE" in completed
    assert "TANE_MASUDA_01,,0,TRUE" in completed


def test_seed_answer_uses_textinput_and_does_not_submit_plain_ime_enter():
    overlay = SeedAnswerOverlay.__new__(SeedAnswerOverlay)
    overlay.text = "増田は真性包茎である"
    overlay.composition = ""

    plain_enter = pygame.event.Event(
        pygame.KEYDOWN, {"key": pygame.K_RETURN, "mod": 0}
    )
    ctrl_enter = pygame.event.Event(
        pygame.KEYDOWN, {"key": pygame.K_RETURN, "mod": pygame.KMOD_CTRL}
    )

    assert overlay.handle_event(plain_enter) is None
    assert overlay.handle_event(ctrl_enter) == "増田は真性包茎である"


def test_submitted_answer_is_echoed_by_protagonist_and_sets_result_flag(monkeypatch):
    from dialogue.controller2 import _submit_seed_answer

    class Overlay:
        turning_point_id = "MASUDA_TP1"

        def __init__(self):
            self.closed = False

        def close(self):
            self.closed = True

    class Seeds:
        def __init__(self):
            self.recorded = None

        def judge_answer(self, turning_point_id, answer):
            return {"result": "correct", "judge_version": "seed-rule-v1"}

        def record_turning_point_result(self, *args):
            self.recorded = args

    class Loader:
        def __init__(self):
            self.flag = None

        def set_story_flag(self, name, value):
            self.flag = (name, value)

    class Renderer:
        def __init__(self):
            self.dialogue = None

        def set_dialogue(self, text, speaker):
            self.dialogue = (text, speaker)

    fake_time = type(
        "FakeTime", (),
        {"current_year": 1999, "current_month": 6, "current_day": 2},
    )()
    monkeypatch.setattr(
        "core.services.time_manager.get_time_manager", lambda: fake_time
    )
    overlay = Overlay()
    seeds = Seeds()
    loader = Loader()
    renderer = Renderer()
    game_state = {
        "seed_answer_overlay": overlay,
        "seed_manager": seeds,
        "dialogue_loader": loader,
        "text_renderer": renderer,
    }

    _submit_seed_answer(game_state, "増田は真性包茎である")

    assert overlay.closed is True
    assert game_state["seed_answer_overlay"] is None
    assert loader.flag == ("MASUDA_TP1_RESULT", "correct")
    assert renderer.dialogue == ("増田は真性包茎である", "{苗字}")
    assert seeds.recorded[-1] == "1999-06-02"


@pytest.mark.parametrize("result", ["borderline", "error"])
def test_unresolved_semantic_answer_keeps_overlay_open(monkeypatch, result):
    from dialogue.controller2 import _submit_seed_answer

    class Overlay:
        turning_point_id = "MASUDA_TP1"

        def __init__(self):
            self.feedback = None
            self.closed = False

        def show_judge_feedback(self, verdict, message):
            self.feedback = (verdict, message)

        def close(self):
            self.closed = True

    class Seeds:
        def __init__(self):
            self.recorded = False

        def judge_answer(self, turning_point_id, answer):
            return {"result": result, "judge_version": "semantic-test-v1"}

        def record_turning_point_result(self, *args):
            self.recorded = True

    overlay = Overlay()
    seeds = Seeds()
    game_state = {
        "seed_answer_overlay": overlay,
        "seed_manager": seeds,
        "dialogue_loader": None,
        "text_renderer": None,
    }

    _submit_seed_answer(game_state, "惜しい推理")

    assert overlay.closed is False
    assert overlay.feedback[0] == result
    assert game_state["seed_answer_overlay"] is overlay
    assert seeds.recorded is False


def test_home_diary_adds_one_visible_line_per_new_seed(monkeypatch):
    from home.home import HomeModule

    base_line = ["desk", "", "", "", "", "", "元の日記", None, 0.5, True, "{苗字}", False, False]
    dialogue = type(
        "Dialogue",
        (),
        {"game_state": {"dialogue_data": [base_line], "use_ir": False}},
    )()
    home = HomeModule.__new__(HomeModule)
    home.journal_new_seed_ids = ["S1", "S2"]
    seed_manager = type(
        "Seeds",
        (),
        {
            "seeds": {
                "S1": {"journal_text": "一つ目"},
                "S2": {"journal_text": "二つ目"},
            }
        },
    )()
    monkeypatch.setattr(
        "core.services.seed_manager.get_seed_manager", lambda: seed_manager
    )

    home._append_new_seed_diary_lines(dialogue)

    lines = dialogue.game_state["dialogue_data"]
    assert [entry[6] for entry in lines] == [
        "元の日記",
        "今日の日記に、新しいタネを追記した。『一つ目』",
        "今日の日記に、新しいタネを追記した。『二つ目』",
    ]
