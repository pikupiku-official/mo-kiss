"""Clue provenance, fixed layout, scene flow and transformed input regression."""

import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pygame
import pytest

from core.services.seed_manager import SeedCatalogError, SeedManager
from dialogue.dialogue_subsystem import DialogueSubsystem
from dialogue.text_renderer import TextRenderer
from home.corkboard import CorkboardView
from home.home import HomeModule


def make_manager(tmp_path):
    data = tmp_path / "data"
    data.mkdir()
    categories = [
        {"id": "family", "group": "momoko", "title": "両親について", "position": [80, 80]},
        {"id": "recent", "group": "momoko", "title": "近況について", "position": [80, 440]},
        {"id": "other", "group": "other", "title": "近況について", "position": [900, 80]},
        {"id": "sister", "group": "sanako", "title": "妹について", "position": [900, 440]},
    ]
    seeds = []
    for i, (category, phase) in enumerate([
        ("family", "before_tp1"), ("recent", "after_tp1"),
        ("other", "before_tp1"), ("sister", "after_tp1"), ("family", "before_tp1"),
    ], 1):
        seeds.append({"id": f"S{i}", "turning_point_id": "TP1", "parents": [],
                      "journal_text": f"タネ{i}の要約。家族についての手掛かり。",
                      "journal_location": {"page": 1, "slot": i},
                      "corkboard": {"category_id": category, "phase": phase,
                                    "position": [380 if i == 5 else 0, 0]}})
    (data / "seed_catalog.json").write_text(json.dumps({"seeds": seeds, "board_categories": categories}), encoding="utf-8")
    (data / "turning_points.json").write_text(json.dumps({"turning_points": [{"id": "TP1"}]}), encoding="utf-8")
    return SeedManager(str(tmp_path))


def collect(manager, ids=("S1", "S2", "S3", "S4")):
    manager.begin_event("E")
    for seed_id in ids:
        manager.encounter("E", seed_id, speaker="別の話者", text=f"「{seed_id}の元のセリフ。」")
    manager.complete_event("E", "1999-06-01")
    manager.finalize_day("1999-06-01")


@pytest.fixture
def renderer(monkeypatch):
    from core import config

    pygame.init()
    pygame.display.set_mode((1, 1))
    monkeypatch.setattr(config, "OFFSET_X", 0)
    monkeypatch.setattr(config, "OFFSET_Y", 0)
    monkeypatch.setattr(config, "SCALE", 1.0)
    renderer = TextRenderer(pygame.Surface((1440, 1080)))
    renderer.name_manager = SimpleNamespace(substitute_variables=lambda text: text.replace("{苗字}", "試験"))
    return renderer


def motion(position, rel=(0, 0)):
    return pygame.event.Event(pygame.MOUSEMOTION, pos=position, rel=rel, buttons=(0, 0, 0))


def click(position):
    return pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=position)


def test_actual_rendered_source_is_captured_without_optional_branch(tmp_path, renderer):
    manager = make_manager(tmp_path)
    manager.begin_event("E")
    renderer.configure_seed_context(manager, "E", {"S1": [{"speaker": "未閲覧", "text": "読んでいない補足"}]})
    line = '「{苗字}、[seed id="S1"]家族のこと[/seed]は話したくない。」'
    renderer.set_dialogue(line, "{苗字}")
    assert manager.state["acquired"] == {}
    manager.complete_event("E", "1999-06-01")
    source = manager.state["acquired"]["S1"]["source_dialogue"]
    assert source["speaker"] == "試験"
    assert source["text"] == line.replace("{苗字}", "試験")
    assert "読んでいない補足" not in json.dumps(manager.state, ensure_ascii=False)
    assert "S2" not in manager.state["acquired"]
    assert manager.board_entries() == []  # Board publishing waits until evening.
    manager.finalize_day("1999-06-01")
    board = CorkboardView(renderer.screen, manager, renderer)
    board.quote_id = "S1"
    assert board._quote()[:2] == ("試験", "「試験、家族のことは話したくない。」")


def test_mid_event_save_keeps_earlier_sources_and_excludes_aborted_routes(tmp_path, renderer):
    manager = make_manager(tmp_path)
    manager.begin_event("E")
    renderer.configure_seed_context(manager, "E")
    renderer.set_dialogue('[seed id="S1"]過去に通った発言[/seed]', "話者一")
    renderer.set_dialogue("今表示しているタネなしの発言", "話者二")
    shell = DialogueSubsystem.__new__(DialogueSubsystem)
    shell.event_file, shell.current_event_id, shell.seed_manager = "events/E.ks", "E", manager
    shell.game_state = {"text_renderer": renderer, "dialogue_data": [[None] * 14]}
    snapshot = json.loads(json.dumps(shell.export_save_state()))
    manager.begin_event("E")
    manager.encounter("E", "S2", speaker="破棄した分岐", text="残してはいけない")
    shell.restore_save_state(snapshot)
    assert manager.complete_event("E", "1999-06-01") == ["S1"]
    assert manager.state["acquired"]["S1"]["source_dialogue"]["speaker"] == "話者一"
    loaded = SeedManager(str(tmp_path))
    assert loaded.state == manager.state


def test_source_is_discarded_on_event_restart(tmp_path):
    manager = make_manager(tmp_path)
    manager.begin_event("E")
    manager.encounter("E", "S1", text="中断したイベントの発言")
    manager.begin_event("E")
    assert manager.complete_event("E", "1999-06-01") == []


def test_fixed_positions_and_phases_survive_acquisition_order_and_late_collection(tmp_path):
    manager = make_manager(tmp_path)
    collect(manager, ("S3", "S2", "S1"))
    before = {entry["id"]: (entry["position"], entry["phase"]) for entry in manager.board_entries()}
    manager.state["turning_point_results"]["TP1"] = {"result": "correct"}
    manager.save()
    collect(manager, ("S4",))
    reloaded = SeedManager(str(tmp_path))
    after = {entry["id"]: (entry["position"], entry["phase"]) for entry in reloaded.board_entries()}
    assert all(after[key] == value for key, value in before.items())
    assert before["S1"][1] == "before_tp1"
    assert before["S2"][1] == "after_tp1"
    assert reloaded.finalize_day("1999-06-01") == []


def test_tabs_show_only_collected_seeds_by_subject_not_speaker(tmp_path, renderer):
    manager = make_manager(tmp_path)
    collect(manager)
    board = CorkboardView(renderer.screen, manager, renderer)
    assert {e["id"] for e in board.visible_entries()} == {"S1", "S2", "S3", "S4"}
    for tab, expected in (("momoko", {"S1", "S2"}), ("sanako", {"S4"}), ("other", {"S3"})):
        board.handle_events([click(board.tab_rects[tab].center)])
        assert {e["id"] for e in board.visible_entries()} == expected
    assert "S5" not in board.entries


@pytest.mark.parametrize("skip_event", [click((40, 130)), pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)])
def test_skipping_is_visibility_only_and_does_not_also_exit(tmp_path, renderer, skip_event):
    manager = make_manager(tmp_path)
    collect(manager)
    saved = json.dumps(manager.state, sort_keys=True)
    now = [0]
    animated = CorkboardView(renderer.screen, manager, renderer, ["S1", "S2", "S3"], lambda: now[0])
    animated.update()
    assert animated.is_animating
    assert {e["id"] for e in animated.visible_entries()} == {"S1", "S4"}
    assert animated.handle_events([skip_event]) is None
    assert not animated.is_animating
    natural = CorkboardView(renderer.screen, manager, renderer, ["S1", "S2", "S3"], lambda: now[0])
    now[0] = 10000
    natural.update()
    assert {e["id"] for e in animated.visible_entries()} == {e["id"] for e in natural.visible_entries()}
    assert animated.zoom == natural.zoom
    assert animated.offset == natural.offset
    assert json.dumps(manager.state, sort_keys=True) == saved
    assert animated.handle_events([click(animated.buttons["back"].center)]) == "back"


def test_transformed_hover_and_long_quote_paging_do_not_replay_dialogue(tmp_path, renderer):
    manager = make_manager(tmp_path)
    collect(manager, ("S1",))
    long_line = "「" + "長い発言の全文を記録して確認する。" * 20 + "」"
    manager.state["acquired"]["S1"]["source_dialogue"]["text"] = long_line
    board = CorkboardView(renderer.screen, manager, renderer)
    entry = board.entries["S1"]
    center = board.screen_rect(entry).center
    board.zoom_at(1.5, center)
    blank = (board.viewport.left + 5, board.viewport.top + 5)
    board.handle_events([motion(blank), click(blank), motion((blank[0] + 65, blank[1] + 30), (65, 30)),
                         pygame.event.Event(pygame.MOUSEBUTTONUP, button=1, pos=blank)])
    transformed = board.screen_rect(entry).center
    board.handle_events([motion(transformed)])
    assert board.hovered_id == "S1"
    assert board.quote_id is None
    board.handle_events([click(transformed)])
    assert board._quote()[1] == long_line
    assert len(board.quote_pages()) > 1
    board.handle_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RIGHT)])
    assert board.quote_page == 1
    before = manager.export_pending_event("E")
    board.render()
    assert manager.export_pending_event("E") == before


def test_hover_only_highlights_and_click_opens_switches_and_closes_quote(tmp_path, renderer, monkeypatch):
    manager = make_manager(tmp_path)
    collect(manager, ("S1", "S2"))
    board = CorkboardView(renderer.screen, manager, renderer)
    full_viewport = board.viewport.copy()
    assert full_viewport.bottom > board.quote_rect.top
    rendered_quotes = []
    monkeypatch.setattr(board, "_render_quote", lambda: rendered_quotes.append(board.quote_id))
    first = board.screen_rect(board.entries["S1"]).center
    board.handle_events([motion(first)])
    assert board.hovered_id == "S1"
    assert board.quote_id is None
    board.render()
    assert rendered_quotes == []
    assert board.viewport == full_viewport
    board.handle_events([click(first)])
    assert board.quote_id == "S1"
    assert board.viewport.bottom < board.quote_rect.top
    board.render()
    assert rendered_quotes == ["S1"]
    second = board.screen_rect(board.entries["S2"]).clip(board.viewport).center
    board.handle_events([motion(second)])
    assert board.hovered_id == "S2"
    assert board.quote_id == "S1"  # Hover must not replace the selected speech.
    board.handle_events([click(second)])
    assert board.quote_id == "S2"
    board.handle_events([click(board.close_quote_rect.center)])
    assert board.quote_id is None
    assert board.viewport == full_viewport
    board.render()
    assert rendered_quotes == ["S1"]
    board.open_quote("S1")
    board.handle_events([click(board.tab_rects["other"].center)])
    assert board.quote_id is None
    assert board.viewport == full_viewport


def test_notes_in_lower_board_can_be_clicked_when_quote_is_hidden(tmp_path, renderer):
    manager = make_manager(tmp_path)
    collect(manager, ("S1",))
    board = CorkboardView(renderer.screen, manager, renderer)
    entry = board.entries["S1"]
    board.focus(entry)
    board.offset.y += board.quote_rect.top + 60 - board.screen_rect(entry).centery
    center = board.screen_rect(entry).center
    assert board.quote_rect.collidepoint(center)
    assert board.viewport.collidepoint(center)
    board.handle_events([motion(center), click(center)])
    assert board.quote_id == "S1"
    assert board.viewport.contains(board.screen_rect(entry))
    blank = (board.viewport.left + 3, board.viewport.top + 3)
    board.handle_events([click(blank)])
    assert board.quote_id is None


@pytest.mark.parametrize("text", ["家族について。", "桃子は家族の話題を避けている。",
                                  "長い要約でも、付箋の外にはみ出さないように折り返す。" * 30],
                         ids=("short", "normal", "long"))
def test_larger_note_text_stays_inside_paper(tmp_path, renderer, text):
    manager = make_manager(tmp_path)
    collect(manager, ("S1",))
    board = CorkboardView(renderer.screen, manager, renderer)
    entry = dict(board.entries["S1"], text=text)
    surface = board._note_surface(entry)
    pixels = pygame.surfarray.array3d(surface)
    paper = board._note_surface(dict(entry, id="blank-note", text=""))
    ink = (pixels != pygame.surfarray.array3d(paper)).any(axis=2)
    xs, ys = ink.nonzero()
    assert len(xs) > 0
    assert xs.min() >= 21 and xs.max() < board.NOTE_SIZE[0] - 21
    assert ys.min() >= 39 and ys.max() < board.NOTE_SIZE[1] - 28
    if len(text) < 30:
        font, lines, _ = board._note_text_layout(text)
        assert font.get_height() > board._font(26).get_height()
        assert lines[-1] != "。"


def test_old_save_without_source_keeps_note_and_does_not_invent_speech(tmp_path, renderer):
    manager = make_manager(tmp_path)
    manager.state["acquired"]["S1"] = {"journaled_game_date": "1999-06-01"}
    board = CorkboardView(renderer.screen, manager, renderer)
    board.quote_id = "S1"
    assert len(board.entries) == 1
    assert board._quote()[0] == ""
    assert "元の発言は記録されていません" in board._quote()[1]


def test_preview_launches_without_qt_windows_plugins(tmp_path):
    """Exercise the entrypoint, not a parent process already using offscreen Qt."""
    root = Path(__file__).resolve().parents[1]
    output = tmp_path / "preview.png"
    env = os.environ.copy()
    env.update(QT_QPA_PLATFORM="windows", QT_PLUGIN_PATH=str(tmp_path / "missing-qt"),
               QT_QPA_PLATFORM_PLUGIN_PATH=str(tmp_path / "missing-qt"),
               SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy", PYTHONIOENCODING="utf-8")
    result = subprocess.run(
        [sys.executable, str(root / "tools" / "preview_corkboard.py"), "--sample", "--snapshot", str(output)],
        cwd=root, env=env, capture_output=True, encoding="utf-8", timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert output.is_file()
    assert output.with_name("preview-window.png").is_file()
    assert "Could not find the Qt platform plugin" not in result.stderr


def test_home_automatically_opens_new_board_and_allows_manual_return(tmp_path, renderer, monkeypatch):
    manager = make_manager(tmp_path)
    collect(manager, ("S1", "S2"))
    monkeypatch.setattr("core.services.seed_manager.get_seed_manager", lambda: manager)
    home = HomeModule.__new__(HomeModule)
    home.screen = renderer.screen
    home._phase = home.DIARY
    home._clock_ms = lambda: 1000
    home._choice_renderer = None
    home._choice_actions = ()
    home._diary_dialogue = SimpleNamespace(game_state={"text_renderer": renderer})
    home._diary_active = False
    home.journal_new_seed_ids = ["S1", "S2"]
    home.morning_flow = SimpleNamespace(active=False)
    home._after_diary()
    assert home._transition.destination == home.CORKBOARD
    home._show_submenu_choices(home.CORKBOARD)
    assert home._corkboard.is_animating
    home.handle_events([click(home._corkboard.buttons["back"].center)])
    assert home._transition is None  # First click only skips animation.
    home.handle_events([click(home._corkboard.buttons["back"].center)])
    assert home._transition.destination == home.MAIN
    home._show_submenu_choices(home.CORKBOARD)
    assert not home._corkboard.is_animating
    assert len(home._corkboard.entries) == 2


def test_real_diary_input_transitions_to_board_then_home(tmp_path, renderer, monkeypatch):
    """Use the actual HOME_DIARY KS, scene images and production input path."""
    manager = make_manager(tmp_path)
    manager.begin_event("E")
    manager.encounter("E", "S1", speaker="純一", text="実際に通った会話")
    manager.complete_event("E", "1999-06-01")
    monkeypatch.setenv("MOKISS_PROFILE_ROOT", str(tmp_path / "profile"))
    (tmp_path / "profile" / "current_state").mkdir(parents=True)
    monkeypatch.setattr("core.services.seed_manager.get_seed_manager", lambda: manager)
    monkeypatch.setattr("home.home.get_time_manager", lambda: SimpleNamespace(
        current_year=1999, current_month=6, current_day=1))
    now = [0]
    home = HomeModule(renderer.screen, clock_ms=lambda: now[0])
    home.on_enter()
    assert home._diary_active, "The real diary must initialize successfully"
    for _ in range(30):
        text = home._diary_dialogue.game_state["text_renderer"]
        text.skip_text()
        home.handle_events([pygame.event.Event(pygame.KEYUP, key=pygame.K_RETURN),
                            pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)])
        if home._transition is not None:
            break
        home.update()
    assert home._transition is not None
    assert home._transition.destination == home.CORKBOARD
    now[0] = 1000
    home.update()
    assert home._phase == home.CORKBOARD
    assert home._corkboard.is_animating
    home.render()
    home.handle_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE)])
    assert not home._corkboard.is_animating
    assert home._corkboard.entries["S1"]["source"]["speaker"] == "純一"
    home.handle_events([click(home._corkboard.buttons["back"].center)])
    now[0] += 1000
    home.update()
    assert home._phase == home.MAIN
    home.cleanup()


@pytest.mark.parametrize("change", [
    lambda data: data["seeds"][0]["corkboard"].update(category_id="missing"),
    lambda data: data["seeds"][0]["corkboard"].update(phase="unknown"),
    lambda data: data["board_categories"][0].update(group="unknown"),
    lambda data: data["seeds"][0]["corkboard"].update(position=[float("nan"), 0]),
    lambda data: data["seeds"][4]["corkboard"].update(position=[0, 0]),
])
def test_invalid_authored_layout_is_reported(tmp_path, change):
    manager = make_manager(tmp_path)
    path = manager.catalog_path
    with open(path, encoding="utf-8") as handle:
        catalog = json.load(handle)
    change(catalog)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(catalog, handle)
    with pytest.raises(SeedCatalogError):
        SeedManager(str(tmp_path))
