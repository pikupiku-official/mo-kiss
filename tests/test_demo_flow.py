"""Demo sequence, real menu restrictions, PV lifecycle, and save isolation."""

import os
from pathlib import Path
import shutil
import subprocess
import time
from types import SimpleNamespace

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pygame
import pytest

from demo.flow import STAGES, DemoFlow, TITLE_IDLE_MS
from demo.GDhome import GDHome
from demo.GDmap import GDMap
from demo.movie import PVScreen
from demo.screens import ChoiceScreen
from core.path_utils import get_current_state_dir, get_story_flags_path


@pytest.fixture
def screen():
    pygame.init()
    surface = pygame.display.set_mode((1440, 1080))
    pygame.event.clear()
    yield surface
    pygame.quit()


def key(value):
    return pygame.event.Event(pygame.KEYDOWN, key=value)


def test_sequence_and_dates():
    flow = DemoFlow()
    stage = flow.start()
    visited = []
    while stage is not None:
        visited.append(stage.name)
        stage = flow.advance()
    assert visited == [
        "op", "morning", "before_map", "map", "noon", "evening", "home",
        "before_monologue", "monologue", "free_text", "ending",
    ]
    assert [(s.date, s.period) for s in STAGES[4:7]] == [
        ("1999-05-31", "昼"), ("1999-05-31", "放課後"), ("1999-05-31", "夜"),
    ]
    assert [(s.date, s.period) for s in STAGES[8:10]] == [
        ("1999-06-15", "朝"), ("1999-06-15", "昼"),
    ]
    assert TITLE_IDLE_MS == 20_000
    flow.reset()
    assert flow.stage is None


def test_map_and_pv_choices_use_real_input(screen):
    field = GDMap(screen)
    assert field.choices.choices == ["教室"]
    assert field.handle_events([key(pygame.K_RETURN)]) == "demo_next"
    choice = ChoiceScreen(screen, ("進む", "映像"), ("demo_next", "demo_pv"))
    assert choice.handle_events([key(pygame.K_DOWN), key(pygame.K_RETURN)]) == "demo_pv"
    assert choice.handle_events([key(pygame.K_ESCAPE)]) == "show_settings"


def test_home_disables_other_actions_and_sleep_never_advances_calendar(screen, monkeypatch):
    ticks = [1000]
    home = GDHome(screen, clock_ms=lambda: ticks[0])
    monkeypatch.setattr(home, "_start_diary", lambda: pytest.fail("demo must skip diary"))
    monkeypatch.setattr(home, "_start_morning", lambda: pytest.fail("demo must skip morning"))
    home.on_enter()
    home.render()
    choices = home._get_choice_renderer()
    assert choices.enabled == [True, False, False, False]
    for index in (1, 2, 3):
        pos = choices.choice_rects[index].center
        assert home.handle_events([pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, button=1, pos=pos,
        )]) is None
        assert home._phase == home.MAIN
        choices.hovered_choice = index
        assert home.handle_events([key(pygame.K_RETURN)]) is None
    choices.hovered_choice = 0
    home.handle_events([key(pygame.K_DOWN), key(pygame.K_RETURN)])
    assert home._transition.destination == home.BED
    ticks[0] += 450
    home.update()
    assert home._phase == home.BED
    assert home.handle_events([key(pygame.K_RETURN)]) == "demo_next"
    home.cleanup()


def test_profile_paths_and_actual_flag_writes_are_isolated(tmp_path, monkeypatch):
    monkeypatch.setenv("MOKISS_PROFILE_ROOT", str(tmp_path))
    state = tmp_path / "current_state"
    state.mkdir()
    assert get_current_state_dir() == str(state)
    assert get_story_flags_path() == str(state / "story_flags.json")
    from dialogue.dialogue_loader import DialogueLoader
    from core.services.seed_manager import SeedManager
    from core.services.time_manager import TimeManager
    from core.services.save_manager import SaveManager
    from dialogue.name_manager import NameManager
    loader = DialogueLoader()
    assert loader.story_flags == {}
    loader.set_story_flag("DEMO_TEST", 1)
    names = NameManager()
    names.set_names("久保田", "航輝")
    clock = TimeManager()
    clock.save_time_state()
    seeds = SeedManager()
    seeds.save()
    saves = SaveManager()
    assert Path(saves.current_state_dir) == state
    assert Path(saves.save_dir) == tmp_path / "save"
    assert {"story_flags.json", "player_name.json", "time_state.json", "seed_state.json"} <= {
        p.name for p in state.iterdir()
    }


def test_pv_missing_file_is_explicit_and_escape_returns_title(screen, tmp_path):
    pv = PVScreen(screen, "__missing_demo__.mp4", tmp_path)
    pv.on_enter()
    assert pv.error
    pv.render()
    assert pv.handle_events([key(pygame.K_ESCAPE)]) == "demo_title"
    pv.cleanup()


def test_real_pv_audio_decode_letterbox_end_and_attract_cancel(screen, tmp_path, monkeypatch):
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        pytest.skip("ffmpeg is not installed")
    movies = tmp_path / "movies"
    movies.mkdir()
    sample = movies / "PV3min.mp4"
    subprocess.run([
        ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi",
        "-i", "color=c=red:s=320x180:r=30:d=0.8", "-f", "lavfi",
        "-i", "sine=frequency=440:duration=0.8", "-c:v", "mpeg4", "-c:a", "aac",
        "-shortest", str(sample),
    ], check=True, timeout=15, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    import demo.movie as movie_module
    monkeypatch.setattr(movie_module, "get_project_root", lambda: str(tmp_path))
    pv = PVScreen(screen, "PV3min.mp4", tmp_path)
    pv.movie.project_root = str(tmp_path)
    try:
        pv.on_enter()
        deadline = time.monotonic() + 10
        while not pv.started and not pv.error and time.monotonic() < deadline:
            pv.update()
            pygame.event.pump()
            time.sleep(0.01)
        assert not pv.error
        assert pv.started and pv.channel is not None
        pv.render()
        assert pv.canvas.get_size() == (1440, 810)
        assert screen.get_at((720, 20))[:3] == (0, 0, 0)
        assert screen.get_at((720, 540)).r > 200
        while not pv.finished and time.monotonic() < deadline:
            pv.update()
            pygame.event.pump()
            time.sleep(0.01)
        assert pv.finished
        assert pv.handle_events([]) == "demo_title"
    finally:
        pv.cleanup()
    assert not pv.channel.get_busy()
    attract = PVScreen(screen, "PV3min.mp4", tmp_path, attract=True)
    assert attract.handle_events([pygame.event.Event(
        pygame.MOUSEMOTION, pos=(10, 10), rel=(1, 0), buttons=(0, 0, 0),
    )]) == "demo_title"
    assert attract.handle_events([key(pygame.K_RETURN)]) == "demo_title"
    attract.cleanup()


def test_loading_is_presented_before_construction_and_drops_stale_input(screen, monkeypatch):
    import demo.application as module
    from core.ui import loading_screen

    # Use this test's actual display surface, independent of earlier tests.
    monkeypatch.setattr(loading_screen, "_loading_screen", None)
    monkeypatch.setattr(module, "get_time_manager", lambda: SimpleNamespace(save_time_state=lambda: None))
    app = module.DemoApplication()
    app.screen = app.virtual_screen = app.window_surface = screen
    screen.fill((255, 0, 0))
    observed = []

    class Scene:
        def __init__(self, surface):
            assert surface.get_at((0, 0))[:3] == (0, 0, 0)
            assert pygame.surfarray.array3d(surface).any(), "loading text was not painted"
            observed.append("constructed")
            pygame.event.post(key(pygame.K_RETURN))
            pygame.event.post(pygame.event.Event(pygame.QUIT))

        def on_enter(self):
            pygame.event.post(key(pygame.K_RETURN))

    monkeypatch.setattr(module, "GDMap", Scene)
    try:
        app.enter_stage(STAGES[3])
        assert observed == ["constructed"]
        assert app.current_mode == "demo_map"
        assert [e.type for e in pygame.event.get()] == [pygame.QUIT]
    finally:
        app.audio_cache.cleanup()


def test_morning_requires_answer_before_money_result_branches(screen, monkeypatch):
    import demo.application as module
    from dialogue.dialogue_loader import DialogueLoader
    from dialogue.data_normalizer import normalize_dialogue_data
    from dialogue.ir_builder import build_ir_from_normalized

    source = Path("events/GD001.ks")
    before = source.read_bytes()
    data = normalize_dialogue_data(DialogueLoader().load_dialogue_from_ks(str(source)))
    preloads = []
    scene = SimpleNamespace(
        game_state={"dialogue_data": data, "use_ir": True,
                    "ir_data": build_ir_from_normalized(data),
                    "text_renderer": SimpleNamespace(set_event_datetime=lambda value: None)},
        seed_manager=SimpleNamespace(preload_answer_model=lambda: preloads.append(True)),
        on_enter=lambda: None,
    )
    monkeypatch.setattr(module, "DialogueSubsystem", lambda *args: scene)
    monkeypatch.setattr(module, "get_time_manager", lambda: SimpleNamespace(save_time_state=lambda: None))
    app = module.DemoApplication()
    app.screen = app.virtual_screen = app.window_surface = screen
    try:
        app.enter_stage(STAGES[1])
        actions = [a for s in scene.game_state["ir_data"]["steps"] for a in s.get("actions", [])]
        question = next(i for i, a in enumerate(actions) if a["action"] == "seed_answer")
        branch = next(i for i, a in enumerate(actions)
                      if a["action"] == "if_start" and "MOMOKO_GD_MONEY_RESULT" in a["params"]["condition"])
        assert question < branch
        assert preloads == [True]
        assert source.read_bytes() == before
    finally:
        app.audio_cache.cleanup()
