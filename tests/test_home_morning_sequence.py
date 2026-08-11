import os
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from home.morning_sequence import MORNING_DIALOGUE_RESULT, MorningSequence


def _advance_event():
    return pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)


def test_news_auto_advances_after_four_seconds_and_frames_last_300_ms():
    now = [1_000]
    sequence = MorningSequence("1999-06-01", clock_ms=lambda: now[0])

    assert sequence.phase == MorningSequence.NEWS
    assert sequence.background_key == "home03"

    now[0] = 4_999
    sequence.update()
    assert sequence.phase == MorningSequence.NEWS

    now[0] = 5_000
    sequence.update()
    assert sequence.phase == MorningSequence.PULLBACK

    expected_frames = (
        (0, "home03"),
        (299, "home03"),
        (300, "home02"),
        (600, "home01"),
        (900, "home00"),
    )
    for elapsed, expected in expected_frames:
        now[0] = 5_000 + elapsed
        sequence.update()
        assert sequence.background_key == expected

    now[0] = 6_200
    sequence.update()
    assert sequence.phase == MorningSequence.DIALOGUE_READY
    assert sequence.background_key == "home00"
    assert sequence.handle_events([]) == MORNING_DIALOGUE_RESULT


def test_news_input_does_not_skip_the_four_second_display():
    now = [0]
    sequence = MorningSequence("1999-06-01", clock_ms=lambda: now[0])

    sequence.handle_events([_advance_event()])

    assert sequence.phase == MorningSequence.NEWS
    assert sequence.background_key == "home03"


def test_delayed_news_update_does_not_skip_pullback_frames():
    now = [0]
    sequence = MorningSequence("1999-06-01", clock_ms=lambda: now[0])

    # 会話の事前読み込み等で更新が遅れても、home03から引きを開始する。
    now[0] = 7_000
    sequence.update()
    assert sequence.phase == MorningSequence.PULLBACK
    assert sequence.background_key == "home03"

    now[0] = 7_300
    sequence.update()
    assert sequence.background_key == "home02"


def test_placeholder_news_renders():
    pygame.font.init()
    screen = pygame.Surface((1_440, 1_080))
    content_rect = screen.get_rect()
    font = pygame.font.Font(None, 48)
    large_font = pygame.font.Font(None, 64)
    sequence = MorningSequence("1999-06-01")

    sequence.render_overlay(screen, content_rect, font, large_font)
    assert screen.get_bounding_rect().width > 0


def test_sleep_advances_date_once_and_starts_morning_sequence(monkeypatch):
    import home.home as home_module

    class FakeTimeManager:
        def __init__(self):
            self.morning_calls = 0

        def set_to_morning(self):
            self.morning_calls += 1

        def get_date_string(self):
            return "1999-06-01"

    fake_time = FakeTimeManager()
    monkeypatch.setattr(home_module, "get_time_manager", lambda: fake_time)

    home = home_module.HomeModule.__new__(home_module.HomeModule)
    home.morning_sequence = None
    home.save_mode = None
    home.choices = [{"text": "寝る", "action": "sleep"}]
    home.selected_choice = 0

    assert home.handle_events([_advance_event()]) is None
    assert fake_time.morning_calls == 1
    assert home.morning_sequence.phase == MorningSequence.NEWS

    # 朝演出中のEnterでは、4秒表示も日付も進めない。
    assert home.handle_events([_advance_event()]) is None
    assert fake_time.morning_calls == 1
    assert home.morning_sequence.phase == MorningSequence.NEWS


def test_home_preloads_dialogue_after_first_morning_frame_is_presented():
    from home.morning_flow import MorningFlow

    preload_calls = []
    flow = MorningFlow(
        None,
        dialogue_factory=lambda screen, event_file: preload_calls.append(event_file),
    )
    flow.sequence = MorningSequence("1999-06-01", clock_ms=lambda: 0)

    flow.update()
    assert preload_calls == []

    flow.frame_presented = True
    flow.update()
    assert preload_calls == ["events/HOME_MORNING_DEPARTURE.ks"]


def test_morning_ks_uses_fullname_tag_for_speaker():
    from dialogue.dialogue_loader import DialogueLoader
    from dialogue.name_manager import NameManager

    loader = DialogueLoader.__new__(DialogueLoader)
    loader.debug = False
    loader.disable_scroll_continue = False
    loader.max_chars_per_line = 26
    ks_text = Path("events/HOME_MORNING_DEPARTURE.ks").read_text(encoding="utf-8")
    raw = loader._parse_ks_content(ks_text)
    dialogue = next(entry for entry in raw if entry.get("type") == "dialogue")

    assert dialogue["character"] == "{フルネーム}"
    assert dialogue["text"] == "行ってきま～す。"

    names = NameManager.__new__(NameManager)
    names.surname = "山田"
    names.name = "太郎"
    names.dialogue_loader = None
    assert names.substitute_variables(dialogue["character"]) == "山田太郎"


def test_morning_sequence_uses_dedicated_dialogue_switch():
    from main import GameApplication

    app = GameApplication.__new__(GameApplication)
    called = []
    app.start_morning_dialogue = lambda: called.append("morning")

    GameApplication._handle_transition(app, MORNING_DIALOGUE_RESULT)

    assert called == ["morning"]


def test_preloaded_morning_dialogue_switches_without_loading_screen():
    from main import GameApplication
    import home.home as home_module

    dialogue = object()
    home = home_module.HomeModule.__new__(home_module.HomeModule)
    home._preloaded_morning_dialogue = dialogue

    app = GameApplication.__new__(GameApplication)
    app.current_subsystem = home
    app.home_module = home
    switched = []
    app.switch_to = lambda subsystem, mode: switched.append((subsystem, mode))
    app.switch_to_dialogue = lambda *args, **kwargs: (_ for _ in ()).throw(
        AssertionError("事前読み込み済みなら通常の読み込み経路を通してはいけない")
    )

    GameApplication.switch_to_morning_dialogue(app)

    assert switched == [(dialogue, "dialogue")]
    assert app.current_event_id == "HOME_MORNING_DEPARTURE"
    from core.flow.game_flow import Navigate, Scene
    assert app.dialogue_completion_result == Navigate(Scene.MAP)
    assert home._preloaded_morning_dialogue is None


def test_morning_dialogue_fallback_also_hides_loading_screen():
    from main import GameApplication
    import home.home as home_module

    home = home_module.HomeModule.__new__(home_module.HomeModule)
    home._preloaded_morning_dialogue = None

    app = GameApplication.__new__(GameApplication)
    app.current_subsystem = home
    app.home_module = home
    called = []
    app.start_dialogue = called.append

    GameApplication.switch_to_morning_dialogue(app)

    from core.flow.game_flow import Navigate, Scene, StartDialogue
    assert called == [StartDialogue(
        event_file="events/HOME_MORNING_DEPARTURE.ks",
        completion=Navigate(Scene.MAP),
        display_loading=False,
    )]


def test_regular_dialogue_keeps_loading_screen(monkeypatch):
    import main as main_module

    app = main_module.GameApplication.__new__(main_module.GameApplication)
    app.screen = object()
    app.virtual_screen = object()
    app.window_surface = object()
    app.current_event_id = None
    app.dialogue_completion_result = None
    switched = []
    loading_calls = []

    monkeypatch.setattr(main_module, "show_loading", lambda text, screen: loading_calls.append("show"))
    monkeypatch.setattr(main_module, "hide_loading", lambda: loading_calls.append("hide"))
    monkeypatch.setattr(main_module, "DialogueSubsystem", lambda *args: "dialogue")
    app.switch_to = lambda subsystem, mode: switched.append((subsystem, mode))

    main_module.GameApplication.switch_to_dialogue(app, "events/E001.ks")

    assert loading_calls == ["show", "hide"]
    assert switched == [("dialogue", "dialogue")]


def test_morning_dialogue_completion_does_not_record_or_advance_event():
    from main import GameApplication

    app = GameApplication.__new__(GameApplication)
    app.dialogue_completion_result = "go_to_map"
    app.current_event_id = "HOME_MORNING_DEPARTURE"
    app.mark_current_event_as_completed = lambda: (_ for _ in ()).throw(
        AssertionError("朝の一言会話を通常イベントとして記録してはいけない")
    )
    switched = []
    app.switch_to_map = lambda: switched.append("map")

    GameApplication._handle_transition(app, "dialogue_ended")

    assert switched == ["map"]
    assert app.current_event_id is None
    assert app.dialogue_completion_result is None
