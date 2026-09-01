import json
import os
from types import SimpleNamespace

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from core.flow.game_flow import GameFlowController
from core.flow.scene_manager import SceneManager
from core.services.save_manager import SaveManager
from dialogue.dialogue_subsystem import DialogueSubsystem
from menu.load_screen import SaveSlotScreen


class _SlotManager:
    def __init__(self, existing=()):
        self.existing = set(existing)
        self.save_dir = "missing"

    def has_save(self, slot_name):
        return slot_name in self.existing

    def get_save_metadata(self, slot_name):
        return {"player_name": "主人公", "game_time": "5月1日 朝"}


def test_option_actions_open_manual_slot_screen():
    opened = []
    app = SimpleNamespace(show_slot_screen=opened.append)
    flow = GameFlowController(app)

    flow.handle_option_action("save")
    flow.handle_option_action("load")

    assert opened == ["save", "load"]


def test_save_screen_selects_first_empty_and_confirms_overwrite():
    pygame.init()
    screen = pygame.display.set_mode((1440, 1080))
    manager = _SlotManager({"saveslot_01"})
    saved = []
    slot_screen = SaveSlotScreen(
        screen,
        mode="save",
        save_manager=manager,
        save_callback=lambda slot: saved.append(slot) or True,
    )

    assert slot_screen.choice_list.selected_index == 1
    assert slot_screen._activate_choice(0) is None
    assert slot_screen.pending_overwrite_index == 0
    assert slot_screen.confirm_choices.selected_index == 1
    assert slot_screen._confirm_overwrite(1) is None
    assert saved == []

    slot_screen._activate_choice(0)
    assert slot_screen._confirm_overwrite(0) == "save_complete:saveslot_01"
    assert saved == ["saveslot_01"]


def test_save_manager_copies_resume_state_and_uses_clean_thumbnail(tmp_path):
    pygame.init()
    pygame.display.set_mode((16, 16))
    manager = SaveManager(project_root=str(tmp_path))
    for filename in manager.state_files:
        path = tmp_path / "data" / "current_state" / filename
        if filename.endswith(".json"):
            path.write_text("{}", encoding="utf-8")
        else:
            path.write_text("event_id,date,count,flags\n", encoding="utf-8")
    resume = {"version": 1, "mode": "dialogue", "dialogue": {"event_id": "E001"}}
    assert manager.write_resume_state(resume)
    clean_frame = pygame.Surface((32, 24))
    clean_frame.fill((12, 34, 56))

    assert manager.save_game("saveslot_01", thumbnail_surface=clean_frame)

    saved_resume = json.loads(
        (tmp_path / "data" / "save" / "saveslot_01" / "resume_state.json").read_text(
            encoding="utf-8"
        )
    )
    thumbnail = pygame.image.load(
        tmp_path / "data" / "save" / "saveslot_01" / "thumbnail.png"
    )
    assert saved_resume == resume
    assert thumbnail.get_width() * 3 == thumbnail.get_height() * 4
    assert thumbnail.get_at((10, 10))[:3] == (12, 34, 56)


def test_slot_metadata_uses_game_era_date_and_period(tmp_path):
    manager = SaveManager(project_root=str(tmp_path))
    slot_path = tmp_path / "data" / "save" / "saveslot_01"
    slot_path.mkdir(parents=True)
    (slot_path / "time_state.json").write_text(
        json.dumps(
            {"year": 1999, "month": 5, "day": 31, "weekday": 0, "period": "朝"},
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    metadata = manager.get_save_metadata("saveslot_01")

    assert metadata["game_year"] == "平成１１年"
    assert metadata["game_date_period"] == "５月３１日（月） 朝"
    assert metadata["game_time"] == "平成１１年 ５月３１日（月） 朝"


def test_slot_screen_uses_full_width_digits_for_display_labels():
    pygame.init()
    screen = pygame.display.set_mode((1440, 1080))
    slot_screen = SaveSlotScreen(screen, mode="save", save_manager=_SlotManager())

    assert slot_screen.choice_list.choices[0] == "スロット０１  データなし"
    assert slot_screen.choice_list.choices[9] == "スロット１０  データなし"


def test_slot_preview_keeps_four_by_three_aspect_ratio():
    pygame.init()
    screen = pygame.display.set_mode((1440, 1080))
    slot_screen = SaveSlotScreen(screen, mode="save", save_manager=_SlotManager())

    preview_rect = slot_screen._preview_rect()

    assert preview_rect.width * 3 == preview_rect.height * 4


class _Scroll:
    def __init__(self):
        self.scroll_mode = False
        self.scroll_lines = []
        self.all_scroll_text = []
        self.all_scroll_speakers = []
        self.all_scroll_force_female = []
        self.current_set_line_count = 0
        self.line_speakers = []
        self.line_is_first = []
        self.line_force_female = []
        self.current_speaker = None
        self.last_added_speaker = None

    def is_scroll_mode(self):
        return self.scroll_mode


class _TextRenderer:
    def __init__(self):
        self.current_text = "保存地点の台詞"
        self.current_character_name = "ヒロイン"
        self.current_force_female = True
        self.scroll_manager = _Scroll()
        self.auto_mode = True
        self.skip_mode = True
        self.is_ready_for_next = True
        self.backlog_added_for_current = False
        self.skipped = False

    def set_dialogue(self, text, speaker, **kwargs):
        self.current_text = text
        self.current_character_name = speaker
        self.current_force_female = kwargs.get("force_female", False)
        self.backlog_added_for_current = False

    def skip_text(self):
        self.skipped = True


class _Choices:
    def __init__(self, choices=None):
        self.choices = list(choices or [])
        self.showing = bool(self.choices)

    def is_choice_showing(self):
        return self.showing

    def hide_choices(self):
        self.choices = []
        self.showing = False

    def show_choices(self, choices):
        self.choices = list(choices)
        self.showing = True


def _dialogue_shell(*, choices=None):
    shell = DialogueSubsystem.__new__(DialogueSubsystem)
    shell.event_file = "events/E001.ks"
    shell.current_event_id = "E001"
    shell._last_saved_paragraph = -2
    shell._pending_resume_bgm = None
    shell.game_state = {
        "dialogue_data": [[None] * 14 for _ in range(20)],
        "current_paragraph": 7,
        "ir_data": {"steps": [{} for _ in range(10)]},
        "ir_step_index": 4,
        "background_state": {
            "current_bg": "school",
            "pos": [2, 3],
            "zoom": 1.0,
            "anim": {"target_x": 20, "target_y": 30, "target_zoom": 1.4},
        },
        "active_characters": ["ヒロイン"],
        "character_pos": {"ヒロイン": [10, 11]},
        "character_zoom": {"ヒロイン": 1.0},
        "character_anim": {
            "ヒロイン": {"target_x": 40, "target_y": 50, "target_zoom": 1.2}
        },
        "character_expressions": {"ヒロイン": {"eye": "eye01"}},
        "character_torso": {"ヒロイン": "body01"},
        "character_blink_enabled": {"ヒロイン": True},
        "character_hide_pending": {},
        "character_part_fades": {},
        "character_blink_state": {},
        "character_blink_timers": {},
        "fade_state": {
            "type": "fadein",
            "active": True,
            "alpha": 100,
            "color": (0, 0, 0),
            "start_time": 10,
            "duration": 1000,
        },
        "text_renderer": _TextRenderer(),
        "choice_renderer": _Choices(choices),
        "backlog_manager": SimpleNamespace(entries=[{"speaker": "A", "text": "B"}], is_showing=True),
        "bgm_manager": SimpleNamespace(current_bgm="theme.ogg", target_volume=0.3, current_loop=True),
    }
    return shell


def test_dialogue_snapshot_restores_settled_visual_and_choice_state():
    source = _dialogue_shell(choices=["選択肢A", "選択肢B"])
    snapshot = source.export_save_state()
    json.dumps(snapshot, ensure_ascii=False)
    target = _dialogue_shell()
    target.restore_save_state(snapshot)

    state = target.game_state
    assert state["current_paragraph"] == 7
    assert state["ir_step_index"] == 4
    assert state["background_state"]["pos"] == [20, 30]
    assert state["background_state"]["zoom"] == 1.4
    assert state["character_pos"]["ヒロイン"] == [40, 50]
    assert state["character_zoom"]["ヒロイン"] == 1.2
    assert state["character_anim"] == {}
    assert state["text_renderer"].current_text == "保存地点の台詞"
    assert state["text_renderer"].skipped is True
    assert state["text_renderer"].auto_mode is False
    assert state["text_renderer"].skip_mode is False
    assert state["choice_renderer"].choices == ["選択肢A", "選択肢B"]
    assert state["backlog_manager"].is_showing is False
    assert target._pending_resume_bgm["file"] == "theme.ogg"


def test_application_resumes_loaded_dialogue_snapshot(monkeypatch):
    import main

    restored = []
    snapshot = {
        "event_file": "events/E001.ks",
        "event_id": "E001",
        "paragraph_index": 7,
    }
    manager = SimpleNamespace(
        get_resume_state=lambda: {
            "mode": "dialogue",
            "dialogue": snapshot,
            "completion": {"type": "navigate", "scene": "map"},
        }
    )

    class FakeDialogue:
        def __init__(self, screen, virtual_screen, event_file):
            self.current_event_id = "E001"

        def restore_save_state(self, value):
            restored.append(value)

        def on_enter(self):
            restored.append("entered")

        def cleanup(self):
            pass

    app = main.GameApplication.__new__(main.GameApplication)
    app.scene_manager = SceneManager(initial_mode="menu")
    app.screen = pygame.Surface((1440, 1080))
    app.virtual_screen = app.screen
    app.window_surface = None
    app.map_system = None
    app.home_module = None
    app.dialogue_completion_result = None
    app.current_event_id = None
    app.reload_game_systems = lambda: None
    monkeypatch.setattr(main, "get_save_manager", lambda: manager)
    monkeypatch.setattr(main, "DialogueSubsystem", FakeDialogue)

    app.resume_loaded_state()

    assert restored == [snapshot, "entered"]
    assert app.current_mode == "dialogue"
    assert app.current_event_id == "E001"
    assert app.dialogue_completion_result.scene.value == "map"


def test_application_saves_dialogue_resume_state_with_pre_option_frame(
    tmp_path, monkeypatch
):
    import main

    manager = SaveManager(project_root=str(tmp_path))
    for filename in manager.state_files:
        path = tmp_path / "data" / "current_state" / filename
        if filename.endswith(".json"):
            path.write_text("{}", encoding="utf-8")
        else:
            path.write_text("event_id,date,count,flags\n", encoding="utf-8")

    class DialogueStub(DialogueSubsystem):
        def __init__(self):
            pass

        def export_save_state(self):
            return {
                "event_file": "events/E001.ks",
                "event_id": "E001",
                "paragraph_index": 7,
            }

    app = main.GameApplication.__new__(main.GameApplication)
    app.scene_manager = SceneManager(initial_mode="dialogue")
    app.current_subsystem = DialogueStub()
    app.dialogue_completion_result = None
    app._option_snapshot = pygame.Surface((40, 30))
    app._option_snapshot.fill((90, 80, 70))
    monkeypatch.setattr(main, "get_save_manager", lambda: manager)

    assert app._save_manual_slot("saveslot_01")

    resume_path = tmp_path / "data" / "save" / "saveslot_01" / "resume_state.json"
    resume = json.loads(resume_path.read_text(encoding="utf-8"))
    thumbnail = pygame.image.load(
        tmp_path / "data" / "save" / "saveslot_01" / "thumbnail.png"
    )
    assert resume["mode"] == "dialogue"
    assert resume["dialogue"]["paragraph_index"] == 7
    assert thumbnail.get_at((20, 20))[:3] == (90, 80, 70)
