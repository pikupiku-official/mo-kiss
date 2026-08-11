import os
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from home.home import HomeModule, _ImageTransition


def test_diary_ks_has_requested_speaker_line_and_background():
    text = Path("events/HOME_DIARY.ks").read_text(encoding="utf-8")

    assert '[bg_show storage="homedesk3"' in text
    assert "//{苗字}//" in text
    assert "「今日もいろんなことがあったな・・・。」" in text


def test_all_home_assets_exist():
    expected = {
        "home.png",
        "bed1.png",
        "bed2.png",
        "bed3.png",
        "desk1.png",
        "desk2.png",
        "desk3.png",
        "corkboard1.png",
        "corkboard2.png",
        "corkboard3.png",
        "PHS.png",
    }

    assert expected <= {path.name for path in Path("images/UI/home").glob("*.png")}


def test_scene_animation_uses_150_ms_frames_and_locks_until_complete():
    transition = _ImageTransition(("bed1", "bed2", "bed3"), 150, "bed", 1_000)

    assert transition.frame_key(1_000) == "bed1"
    assert transition.frame_key(1_149) == "bed1"
    assert transition.frame_key(1_150) == "bed2"
    assert transition.frame_key(1_300) == "bed3"
    assert not transition.is_finished(1_449)
    assert transition.is_finished(1_450)


def test_phone_reuses_f6_opening_frames_and_reverses_when_closing():
    assert HomeModule.ENTRY_FRAMES[HomeModule.PHONE] == (
        "phone1",
        "phone2",
        "phone3",
    )
    assert HomeModule.PHONE_OPEN_FRAME_MS == 100
    assert HomeModule.PHONE_CLOSE_FRAME_MS == 50
    assert HomeModule.PHONE_Y_OFFSETS == {
        "phone1": 760,
        "phone2": 260,
        "phone3": 0,
    }

    home = HomeModule.__new__(HomeModule)
    home._choice_renderer = None
    home._choice_actions = ()
    home._clock_ms = lambda: 500
    home._transition = None
    home._hide_choices = lambda: None
    home._start_return_transition(HomeModule.PHONE)

    assert home._transition.frames == ("phone3", "phone2", "phone1", "home")


def test_sleep_is_only_available_from_bed():
    assert HomeModule.SUBMENU_CHOICES[HomeModule.BED] == (
        ("寝る", "sleep"),
        ("戻る", "back"),
    )
    assert HomeModule.SUBMENU_CHOICES[HomeModule.DESK] == (("戻る", "back"),)
    assert HomeModule.SUBMENU_CHOICES[HomeModule.CORKBOARD] == (("戻る", "back"),)
    assert HomeModule.SUBMENU_CHOICES[HomeModule.PHONE] == (("戻る", "back"),)


def test_enter_activates_current_dialogue_style_choice(monkeypatch):
    pygame.init()
    activated = []

    class FakeRenderer:
        hovered_choice = 2

    home = HomeModule.__new__(HomeModule)
    home._phase = HomeModule.MAIN
    home._transition = None
    home._diary_active = False
    home._choice_renderer = FakeRenderer()
    home._get_choice_renderer = lambda: home._choice_renderer
    home._activate_choice = lambda index: activated.append(index)
    home.morning_flow = type("Flow", (), {"active": False})()

    home.handle_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)])

    assert activated == [2]


def test_diary_finishing_enter_immediately_opens_free_choices():
    pygame.init()
    opened = []

    class FakeDiary:
        def __init__(self):
            self.game_state = {"ks_finished": False}

        def handle_events(self):
            self.game_state["ks_finished"] = True
            return None

    home = HomeModule.__new__(HomeModule)
    home._phase = HomeModule.DIARY
    home._diary_active = True
    home._diary_dialogue = FakeDiary()
    home.morning_flow = type("Flow", (), {"active": False})()
    home._finish_diary_dialogue = lambda: opened.append("finished")
    home._show_main_choices = lambda: opened.append("choices")

    home.handle_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)])

    assert opened == ["finished", "choices"]
