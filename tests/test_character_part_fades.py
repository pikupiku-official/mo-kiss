import pygame

from dialogue.character_manager import (
    _begin_character_fade_on_first_render,
    _begin_character_transition_on_first_render,
    draw_character_transition,
    render_face_parts,
    start_character_part_fade,
    update_character_transitions,
    update_character_fades,
)
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


def test_normalized_partial_chara_shift_preserves_each_characters_parts():
    raw = [
        {
            "type": "character",
            "name": "alice",
            "torso": "A_T00",
            "eye": "A_EYE01",
            "mouth": "A_MOUTH01",
            "brow": "A_BROW01",
            "cheek": "A_CHEEK01",
            "effect": "A_EFFECT01",
            "accessory": "A_ACCESSORY01",
        },
        {
            "type": "character",
            "name": "bob",
            "torso": "B_T00",
            "eye": "B_EYE01",
            "mouth": "B_MOUTH01",
            "brow": "B_BROW01",
            "cheek": "B_CHEEK01",
            "effect": "B_EFFECT01",
            "accessory": "B_ACCESSORY01",
        },
        {"type": "chara_shift", "name": "alice", "eye": "A_EYE02"},
    ]

    ir = build_ir_from_normalized(normalize_dialogue_data(raw))
    shift_action = ir["steps"][0]["actions"][2]

    assert shift_action["target"] == "alice"
    assert shift_action["params"] == {
        "torso": "A_T00",
        "eye": "A_EYE02",
        "mouth": "A_MOUTH01",
        "brow": "A_BROW01",
        "cheek": "A_CHEEK01",
    }


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


def test_character_fade_does_not_expire_before_first_render(monkeypatch):
    monkeypatch.setattr(pygame.time, "get_ticks", lambda: 1000)
    game_state = {"character_part_fades": {}}

    start_character_part_fade(
        game_state, "momoko", "eye", "EYE01", "EYE02", 150
    )

    # Simulate a slow preview setup before the first character frame.
    monkeypatch.setattr(pygame.time, "get_ticks", lambda: 1300)
    update_character_fades(game_state)
    assert "eye" in game_state["character_part_fades"]["momoko"]

    _begin_character_fade_on_first_render(game_state, "momoko", 1300)
    assert game_state["character_part_fades"]["momoko"]["eye"]["start_time"] == 1300

    monkeypatch.setattr(pygame.time, "get_ticks", lambda: 1449)
    update_character_fades(game_state)
    assert "momoko" in game_state["character_part_fades"]

    monkeypatch.setattr(pygame.time, "get_ticks", lambda: 1450)
    update_character_fades(game_state)
    assert "momoko" not in game_state["character_part_fades"]


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


def test_chara_shift_torso_crossfade_defaults_to_300ms(monkeypatch):
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

    duration = _ir_handle_character_shift(
        game_state, "momoko", {"torso": "T01"}
    )

    assert duration == 300
    assert game_state["character_transitions"]["momoko"]["duration"] == 300
    assert game_state["character_part_fades"]["momoko"]["torso"]["duration"] == 300


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


def test_torso_shift_uses_one_full_body_crossfade(monkeypatch):
    monkeypatch.setattr(pygame.time, "get_ticks", lambda: 1000)
    old_torso = pygame.Surface((100, 200), pygame.SRCALPHA)
    new_torso = pygame.Surface((100, 200), pygame.SRCALPHA)
    manager = DummyImageManager(
        {
            ("torso", "T00"): old_torso,
            ("torso", "T01"): new_torso,
        }
    )
    game_state = {
        "active_characters": ["momoko"],
        "character_pos": {"momoko": [100, 100]},
        "character_zoom": {"momoko": 1.0},
        "character_torso": {"momoko": "T00"},
        "character_expressions": {"momoko": {"eye": "EYE01"}},
        "character_part_fades": {},
        "image_manager": manager,
    }

    duration = _ir_handle_character_shift(
        game_state, "momoko", {"torso": "T01", "fade": 0.3}
    )

    assert duration == 300
    transition = game_state["character_transitions"]["momoko"]
    assert transition["mode"] == "crossfade"
    assert transition["pending_render"] is True
    assert transition["from_surface"] is not None
    assert transition["to_surface"] is not None
    assert game_state["character_torso"]["momoko"] == "T01"


def test_missing_shift_torso_keeps_the_last_drawable_body(monkeypatch):
    monkeypatch.setattr(pygame.time, "get_ticks", lambda: 1000)
    torso = pygame.Surface((100, 200), pygame.SRCALPHA)
    eye_old = pygame.Surface((10, 10), pygame.SRCALPHA)
    eye_new = pygame.Surface((10, 10), pygame.SRCALPHA)
    manager = DummyImageManager(
        {
            ("torso", "T00"): torso,
            ("eye", "EYE01"): eye_old,
            ("eye", "EYE02"): eye_new,
        }
    )
    game_state = {
        "active_characters": ["momoko"],
        "character_pos": {"momoko": [100, 100]},
        "character_zoom": {"momoko": 1.0},
        "character_torso": {"momoko": "T00"},
        "character_expressions": {"momoko": {"eye": "EYE01"}},
        "character_part_fades": {},
        "character_transitions": {},
        "image_manager": manager,
    }

    _ir_handle_character_shift(
        game_state,
        "momoko",
        {"torso": "MISSING_T02", "eye": "EYE02", "fade": 0.3},
    )

    assert game_state["character_torso"]["momoko"] == "T00"
    assert game_state["character_transitions"] == {}
    assert game_state["character_part_fades"]["momoko"]["eye"] == {
        "from": "EYE01",
        "to": "EYE02",
        "start_time": 1000,
        "duration": 300,
    }


def test_missing_shift_expression_keeps_the_last_drawable_part(monkeypatch):
    monkeypatch.setattr(pygame.time, "get_ticks", lambda: 1000)
    torso = pygame.Surface((100, 200), pygame.SRCALPHA)
    eye_old = pygame.Surface((10, 10), pygame.SRCALPHA)
    manager = DummyImageManager(
        {
            ("torso", "T00"): torso,
            ("eye", "EYE01"): eye_old,
        }
    )
    game_state = {
        "active_characters": ["momoko"],
        "character_pos": {"momoko": [100, 100]},
        "character_zoom": {"momoko": 1.0},
        "character_torso": {"momoko": "T00"},
        "character_expressions": {"momoko": {"eye": "EYE01"}},
        "character_part_fades": {},
        "character_transitions": {},
        "image_manager": manager,
    }

    _ir_handle_character_shift(
        game_state,
        "momoko",
        {"eye": "MISSING_EYE", "fade": 0.3},
    )

    assert game_state["character_expressions"]["momoko"]["eye"] == "EYE01"
    assert game_state.get("character_part_fades", {}) == {}


def test_position_shift_crossfades_without_a_zero_alpha_handoff(monkeypatch):
    ticks = {"value": 1000}
    monkeypatch.setattr(pygame.time, "get_ticks", lambda: ticks["value"])
    torso = pygame.Surface((100, 200), pygame.SRCALPHA)
    manager = DummyImageManager({("torso", "T00"): torso})
    game_state = {
        "active_characters": ["momoko"],
        "character_pos": {"momoko": [100, 100]},
        "character_zoom": {"momoko": 1.0},
        "character_torso": {"momoko": "T00"},
        "character_expressions": {"momoko": {}},
        "character_part_fades": {},
        "image_manager": manager,
    }

    duration = _ir_handle_character_shift(
        game_state,
        "momoko",
        {"x": 0.75, "fade": 0.15},
    )
    transition = game_state["character_transitions"]["momoko"]
    assert duration == 300
    assert transition["mode"] == "crossfade"
    assert transition["phase"] == "blend"
    assert game_state["character_pos"]["momoko"] == [100, 100]

    _begin_character_transition_on_first_render(game_state, "momoko", 1000)
    ticks["value"] = 1149
    update_character_transitions(game_state)
    assert game_state["character_pos"]["momoko"] == [100, 100]
    assert "momoko" in game_state["character_transitions"]

    ticks["value"] = 1150
    update_character_transitions(game_state)
    assert transition["phase"] == "blend"
    assert game_state["character_pos"]["momoko"] == [100, 100]

    ticks["value"] = 1300
    update_character_transitions(game_state)
    assert "momoko" not in game_state["character_transitions"]
    assert game_state["character_pos"]["momoko"] != [100, 100]


def test_position_shift_draws_during_the_old_fo_fi_handoff(monkeypatch):
    ticks = {"value": 1000}
    monkeypatch.setattr(pygame.time, "get_ticks", lambda: ticks["value"])
    old_torso = pygame.Surface((10, 20), pygame.SRCALPHA)
    old_torso.fill((255, 0, 0, 255))
    new_torso = pygame.Surface((10, 20), pygame.SRCALPHA)
    new_torso.fill((0, 0, 255, 255))
    manager = DummyImageManager(
        {
            ("torso", "T00"): old_torso,
            ("torso", "T01"): new_torso,
        }
    )
    game_state = {
        "active_characters": ["momoko"],
        "character_pos": {"momoko": [100, 100]},
        "character_zoom": {"momoko": 1.0},
        "character_torso": {"momoko": "T00"},
        "character_expressions": {"momoko": {}},
        "character_part_fades": {},
        "image_manager": manager,
    }

    _ir_handle_character_shift(
        game_state,
        "momoko",
        {"torso": "T01", "x": 0.75, "fade": 0.15},
    )
    _begin_character_transition_on_first_render(game_state, "momoko", 1000)

    # This is exactly the former FO -> FI handoff frame. It must still contain
    # character pixels instead of exposing the background for one frame.
    ticks["value"] = 1150
    update_character_transitions(game_state)
    screen = pygame.Surface((1440, 1080), pygame.SRCALPHA)
    screen.fill((0, 0, 0, 255))
    draw_character_transition(game_state, "momoko", screen, current_time=1150)

    transition = game_state["character_transitions"]["momoko"]
    from_rect = transition["from_surface"].get_bounding_rect(min_alpha=1).move(
        transition["from_surface_pos"]
    )
    to_rect = transition["to_surface"].get_bounding_rect(min_alpha=1).move(
        transition["to_surface_pos"]
    )
    probe_rect = from_rect.union(to_rect)
    assert any(
        screen.get_at((x, y))[:3] != (0, 0, 0)
        for x in range(probe_rect.left, probe_rect.right)
        for y in range(probe_rect.top, probe_rect.bottom)
    )
