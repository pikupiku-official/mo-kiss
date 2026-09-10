import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from core.services.image_manager import _classify_stem
from core.services.image_manager import ImageManager
from dialogue.cg_manager import hide_cg, shift_cg, show_cg, update_cg_animation
from dialogue.controller2 import is_input_blocked, is_ir_idle
from dialogue.data_normalizer import normalize_dialogue_data
from dialogue.dialogue_loader import DialogueLoader
from dialogue.ir_builder import build_ir_from_normalized
from dialogue.scenario_manager import _ir_default_on_advance
from tools.event_editor_scene import StepSceneStateBuilder
from tools.event_editor_cg import CgDiffBrowserDialog
from PyQt5.QtGui import QColor, QImage
from PyQt5.QtWidgets import QApplication


APP = QApplication.instance() or QApplication([])


class DummyImageManager:
    def __init__(self, images):
        self.images = images

    def get_image(self, image_type, image_key, size=None):
        return self.images.get((image_type, image_key))


def _loader():
    loader = DialogueLoader.__new__(DialogueLoader)
    loader.debug = False
    loader.disable_scroll_continue = False
    loader.max_chars_per_line = 26
    return loader


def _actions(ir):
    return [
        action
        for step in ir["steps"]
        for action in step.get("actions", [])
    ]


def test_legacy_cg_assets_are_classified_as_cg():
    assert _classify_stem("MMK_03_000") == "cg"
    assert _classify_stem("MMK_03_011") == "cg"


def test_real_cg_assets_are_discovered_in_the_cg_image_bucket():
    manager = ImageManager()
    manager.scan_image_paths(1440, 1080)
    assert manager.image_paths["cg"]["MMK_03_000"].endswith("MMK_03_000.png")


def test_cg_tags_parse_normalize_and_build_blocking_ir():
    raw = _loader()._parse_ks_content(
        '[cg_show storage="MMK_03_000" fade="0.3"]\n'
        '[cg_shift storage="MMK_03_001" left="0.02" top="0" zoom="1.1" time="600"]\n'
        '[cg_hide fade="0.2"]\n'
    )

    assert [entry["type"] for entry in raw] == ["cg_show", "cg_shift", "cg_hide"]
    normalized = normalize_dialogue_data(raw)
    actions = _actions(build_ir_from_normalized(normalized))
    assert [action["action"] for action in actions] == [
        "cg_show",
        "cg_shift",
        "cg_hide",
    ]
    assert actions[0]["params"] == {"storage": "MMK_03_000", "fade": 0.3}
    assert actions[1]["params"] == {
        "storage": "MMK_03_001",
        "left": 0.02,
        "top": 0.0,
        "zoom": 1.1,
        "time": 600.0,
    }
    assert all(action["animation"]["on_advance"] == "block" for action in actions)
    assert all(_ir_default_on_advance(action["action"]) == "block" for action in actions)


def test_cg_transition_changes_variant_and_restores_after_hide(monkeypatch):
    image = pygame.Surface((720, 480), pygame.SRCALPHA)
    manager = DummyImageManager({
        ("cg", "MMK_03_000"): image,
        ("cg", "MMK_03_001"): image.copy(),
    })
    game_state = {"image_manager": manager}
    now = [1000]
    monkeypatch.setattr(pygame.time, "get_ticks", lambda: now[0])

    assert show_cg(game_state, "MMK_03_000", {"fade": 0.3}) == 300
    assert is_input_blocked({**game_state, "use_ir": False})
    assert not is_ir_idle({**game_state, "use_ir": False})
    now[0] = 1300
    update_cg_animation(game_state)
    assert game_state["cg_state"]["storage"] == "MMK_03_000"
    assert game_state["cg_state"]["transition"] is None

    assert shift_cg(
        game_state,
        {"storage": "MMK_03_001", "left": 1.0, "time": 600},
    ) == 600
    assert game_state["cg_state"]["transition"]["to_storage"] == "MMK_03_001"
    assert game_state["cg_state"]["transition"]["to_offset_x"] == 90.0
    now[0] = 1900
    update_cg_animation(game_state)
    assert game_state["cg_state"]["storage"] == "MMK_03_001"
    assert game_state["cg_state"]["offset_x"] == 90.0

    assert hide_cg(game_state, {"fade": 0.2}) == 200
    assert game_state["cg_state"]["transition"]["to_storage"] is None
    now[0] = 2100
    update_cg_animation(game_state)
    assert game_state["cg_state"]["storage"] is None


def test_missing_cg_does_not_replace_current_asset():
    image = pygame.Surface((720, 480), pygame.SRCALPHA)
    manager = DummyImageManager({("cg", "MMK_03_000"): image})
    game_state = {"image_manager": manager}
    assert show_cg(game_state, "MMK_03_000", {"fade": 0}) == 0
    assert game_state["cg_state"]["storage"] == "MMK_03_000"
    assert shift_cg(game_state, {"storage": "MMK_03_999", "time": 0}) is False
    assert game_state["cg_state"]["storage"] == "MMK_03_000"


def test_scene_builder_replays_cg_and_suppresses_character_objects():
    def size_lookup(image_type, _key):
        return (720, 480) if image_type == "cg" else (500, 1000)

    builder = StepSceneStateBuilder(image_size_lookup=size_lookup)
    states = builder.build(
        [
            ['chara_show name="momoko" torso="MMK_T00"'],
            ['cg_show storage="MMK_03_000"'],
            ['cg_shift storage="MMK_03_001" left="0.02" zoom="1.1"'],
            ['cg_hide fade="0.3"'],
        ],
        2,
    )

    assert states["after"]["cg"]["storage"] == "MMK_03_001"
    assert states["after"]["cg"]["offset_x"] == 28.8
    assert states["after"]["cg"]["zoom"] == 1.1
    assert states["after"]["characters"]["momoko"]["torso"] == "MMK_T00"
    assert states["after"]["cg"]["origin"] == "modified"


def test_cg_diff_browser_groups_assets_and_decodes_only_a_scaled_preview(tmp_path):
    paths = {}
    for diff, color in (("000", QColor(220, 40, 40)), ("001", QColor(40, 80, 220))):
        path = tmp_path / f"MMK_03_{diff}.png"
        image = QImage(720, 480, QImage.Format_ARGB32)
        image.fill(color)
        assert image.save(str(path))
        paths[f"MMK_03_{diff}"] = str(path)

    manager = type("Manager", (), {"image_paths": {"cg": paths}})()
    dialog = CgDiffBrowserDialog(None, manager, "MMK_03_001")
    assert dialog.cg_combo.count() == 1
    assert dialog.diff_list.count() == 2
    assert dialog.selected_storage == "MMK_03_001"
    assert not dialog.preview.pixmap().isNull()
    dialog.close()
