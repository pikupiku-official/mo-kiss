import pygame

from dialogue.character_manager import render_face_parts
from dialogue.data_normalizer import normalize_dialogue_data
from dialogue.dialogue_loader import DialogueLoader
from dialogue.ir_builder import build_ir_from_normalized
from dialogue.scenario_manager import (
    _ir_handle_character_hide,
    _ir_handle_character_shift,
    _ir_handle_character_show,
)


class DummyImageManager:
    def __init__(self, images):
        self.images = images
        self.requests = []

    def get_image(self, image_type, image_id):
        self.requests.append((image_type, image_id))
        return self.images.get((image_type, image_id))


def test_dialogue_loader_uses_chara_shift_own_fade_value():
    loader = DialogueLoader()
    entries = loader._parse_ks_content(
        '[chara_show name="momoko" torso="T00" fade="0.8"]\n'
        '[chara_shift name="momoko" eye="EYE02" fade="0.3"]'
    )

    shift = next(entry for entry in entries if entry.get("type") == "chara_shift")
    assert shift["fade"] == 0.3


def test_chara_shift_fade_survives_normalization_and_ir_build():
    loader = DialogueLoader()
    parsed = loader._parse_ks_content(
        '[chara_shift name="masuda" torso="T01" eye="EYE02" '
        'x="0.725" y="1.0" fade="0.3"]'
    )
    normalized = normalize_dialogue_data(parsed)
    ir = build_ir_from_normalized(normalized)

    action = ir["steps"][0]["actions"][0]
    assert action["action"] == "chara_shift"
    assert action["params"]["fade"] == 0.3
    assert action["params"]["x"] == 0.725
    assert action["params"]["y"] == 1.0


def test_chara_shift_accessory_does_not_capture_y_and_keeps_torso():
    loader = DialogueLoader()
    parsed = loader._parse_ks_content(
        '[chara_show name="momoko" torso="T00" fade="0"]\n'
        '[chara_shift name="momoko" torso="T01" eye="EYE02" '
        'accessory="ACC01" x="0.6" fade="0.3"]'
    )
    normalized = normalize_dialogue_data(parsed)
    ir = build_ir_from_normalized(normalized)

    shift = next(
        action
        for step in ir["steps"]
        for action in step.get("actions") or []
        if action.get("action") == "chara_shift"
    )
    assert shift["target"] == "momoko"
    assert shift["params"]["torso"] == "T01"
    assert shift["params"]["accessory"] == "ACC01"
    assert shift["params"]["x"] == 0.6
    assert "y" not in shift["params"]
    assert shift["params"]["fade"] == 0.3


def test_chara_shift_registers_crossfades_for_changed_and_cleared_parts(monkeypatch):
    monkeypatch.setattr(pygame.time, "get_ticks", lambda: 1000)
    torso = pygame.Surface((10, 20), pygame.SRCALPHA)
    manager = DummyImageManager(
        {
            ("torso", "T00"): torso,
            ("eye", "EYE02"): pygame.Surface((2, 2), pygame.SRCALPHA),
        }
    )
    game_state = {
        "active_characters": ["momoko"],
        "character_pos": {"momoko": [0, 0]},
        "character_zoom": {"momoko": 1.0},
        "character_torso": {"momoko": "T00"},
        "character_expressions": {
            "momoko": {
                "eye": "EYE01",
                "mouth": "MOUTH01",
                "brow": "",
                "cheek": "",
                "effect": "",
                "accessory": "",
            }
        },
        "character_part_fades": {},
        "image_manager": manager,
    }

    _ir_handle_character_shift(
        game_state,
        "momoko",
        {"eye": "EYE02", "mouth": "", "fade": 0.3},
    )

    fades = game_state["character_part_fades"]["momoko"]
    assert fades["eye"] == {
        "from": "EYE01",
        "to": "EYE02",
        "start_time": 1000,
        "duration": 300,
    }
    assert fades["mouth"]["from"] == "MOUTH01"
    assert fades["mouth"]["to"] == ""
    assert ("eye", "EYE02") in manager.requests


def test_chara_shift_registers_torso_crossfade(monkeypatch):
    monkeypatch.setattr(pygame.time, "get_ticks", lambda: 1000)
    old_torso = pygame.Surface((10, 20), pygame.SRCALPHA)
    new_torso = pygame.Surface((10, 20), pygame.SRCALPHA)
    manager = DummyImageManager(
        {
            ("torso", "T00"): old_torso,
            ("torso", "T01"): new_torso,
        }
    )
    game_state = {
        "active_characters": ["momoko"],
        "character_pos": {"momoko": [0, 0]},
        "character_zoom": {"momoko": 1.0},
        "character_torso": {"momoko": "T00"},
        "character_expressions": {"momoko": {}},
        "character_part_fades": {},
        "image_manager": manager,
    }

    _ir_handle_character_shift(
        game_state,
        "momoko",
        {"torso": "T01", "fade": 0.3},
    )

    assert game_state["character_torso"]["momoko"] == "T01"
    assert game_state["character_part_fades"]["momoko"]["torso"] == {
        "from": "T00",
        "to": "T01",
        "start_time": 1000,
        "duration": 300,
    }


def test_chara_show_fades_in_all_supplied_layers(monkeypatch):
    monkeypatch.setattr(pygame.time, "get_ticks", lambda: 1000)
    torso = pygame.Surface((10, 20), pygame.SRCALPHA)
    manager = DummyImageManager(
        {
            ("torso", "T00"): torso,
            ("eye", "EYE01"): pygame.Surface((2, 2), pygame.SRCALPHA),
            ("effect", "FX01"): pygame.Surface((2, 2), pygame.SRCALPHA),
            ("accessory", "ACC01"): pygame.Surface((2, 2), pygame.SRCALPHA),
        }
    )
    game_state = {
        "active_characters": [],
        "character_pos": {},
        "character_zoom": {},
        "character_torso": {},
        "character_expressions": {},
        "character_part_fades": {},
        "character_hide_pending": {},
        "character_blink_enabled": {},
        "character_blink_state": {},
        "character_blink_timers": {},
        "image_manager": manager,
    }

    _ir_handle_character_show(
        game_state,
        "momoko",
        {
            "torso": "T00",
            "eye": "EYE01",
            "effect": "FX01",
            "accessory": "ACC01",
            "blink": False,
            "fade": 0.3,
        },
    )

    fades = game_state["character_part_fades"]["momoko"]
    assert fades["torso"]["from"] is None
    assert fades["torso"]["to"] == "T00"
    assert fades["eye"]["from"] is None
    assert fades["effect"]["from"] is None
    assert fades["accessory"]["from"] is None


def test_chara_show_replaces_stale_hide_or_shift_fades(monkeypatch):
    monkeypatch.setattr(pygame.time, "get_ticks", lambda: 1000)
    torso = pygame.Surface((10, 20), pygame.SRCALPHA)
    manager = DummyImageManager({("torso", "T00"): torso})
    game_state = {
        "active_characters": ["momoko"],
        "character_pos": {"momoko": [0, 0]},
        "character_zoom": {"momoko": 1.0},
        "character_torso": {"momoko": "OLD"},
        "character_expressions": {"momoko": {}},
        "character_part_fades": {
            "momoko": {
                "torso": {
                    "from": "OLD",
                    "to": None,
                    "start_time": 900,
                    "duration": 300,
                },
                "effect": {
                    "from": "FX01",
                    "to": None,
                    "start_time": 900,
                    "duration": 300,
                },
            }
        },
        "character_hide_pending": {"momoko": 1200},
        "character_blink_enabled": {},
        "character_blink_state": {},
        "character_blink_timers": {},
        "image_manager": manager,
    }

    _ir_handle_character_show(
        game_state,
        "momoko",
        {"torso": "T00", "blink": False, "fade": 0.3},
    )

    assert "momoko" not in game_state["character_hide_pending"]
    assert game_state["character_part_fades"]["momoko"] == {
        "torso": {
            "from": None,
            "to": "T00",
            "start_time": 1000,
            "duration": 300,
        }
    }


def test_chara_hide_fades_out_all_visible_layers(monkeypatch):
    monkeypatch.setattr(pygame.time, "get_ticks", lambda: 1000)
    game_state = {
        "active_characters": ["momoko"],
        "character_torso": {"momoko": "T00"},
        "character_expressions": {
            "momoko": {
                "brow": "BROW01",
                "eye": "EYE01",
                "mouth": "MOUTH01",
                "cheek": "CHEEK01",
                "effect": "FX01",
                "accessory": "ACC01",
            }
        },
        "character_part_fades": {},
        "character_hide_pending": {},
    }

    _ir_handle_character_hide(game_state, "momoko", {"fade": 0.3})

    fades = game_state["character_part_fades"]["momoko"]
    assert set(fades) == {
        "torso",
        "brow",
        "eye",
        "mouth",
        "cheek",
        "effect",
        "accessory",
    }
    for fade in fades.values():
        assert fade["to"] is None
        assert fade["duration"] == 300
    assert game_state["character_hide_pending"]["momoko"] == 1300


def test_render_face_parts_draws_both_crossfade_endpoints(monkeypatch):
    screen = pygame.Surface((6, 6), pygame.SRCALPHA)
    torso = pygame.Surface((2, 2), pygame.SRCALPHA)
    old_eye = pygame.Surface((2, 2), pygame.SRCALPHA)
    old_eye.fill((255, 0, 0, 255))
    new_eye = pygame.Surface((2, 2), pygame.SRCALPHA)
    new_eye.fill((0, 0, 255, 255))
    manager = DummyImageManager(
        {
            ("torso", "T00"): torso,
            ("eye", "EYE01"): old_eye,
            ("eye", "EYE02"): new_eye,
        }
    )
    game_state = {
        "screen": screen,
        "character_pos": {"momoko": [2, 2]},
        "character_torso": {"momoko": "T00"},
        "character_blink_state": {},
        "character_expressions": {"momoko": {"eye": "EYE02"}},
        "image_manager": manager,
    }
    fade_map = {
        "eye": {
            "from": "EYE01",
            "to": "EYE02",
            "start_time": 1000,
            "duration": 200,
        }
    }

    render_face_parts(
        game_state,
        "momoko",
        "",
        "EYE02",
        "",
        "",
        1.0,
        fade_map=fade_map,
        current_time=1100,
    )

    assert ("eye", "EYE01") in manager.requests
    assert ("eye", "EYE02") in manager.requests
    pixel = screen.get_at((3, 3))
    assert pixel.r > 0
    assert pixel.b > 0
