import os
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5.QtCore import QPoint
from PyQt5.QtWidgets import QApplication, QPushButton

import event_editor
from event_editor import CharaCompositePreviewDialog
from tools.event_editor_part_templates import CharaPartTemplateStore


APP = QApplication.instance() or QApplication([])


def _empty_image_manager():
    return SimpleNamespace(
        image_paths={
            key: {}
            for key in (
                "torso",
                "brow",
                "cheek",
                "eye",
                "mouth",
                "accessory",
                "effect",
            )
        }
    )


def test_part_template_store_filters_and_manages_character_templates(tmp_path):
    store = CharaPartTemplateStore(tmp_path / "templates.json")
    momoko = store.create(
        "笑顔・制服",
        "桃子",
        {"torso": "MMK_T00_ARM01_CLO00", "eye": "MMK_F00_EYE00_00"},
        blink=False,
    )
    store.create("別キャラ", "増田", {"torso": "MST_T00_ARM_0002"})

    visible = store.for_character("桃子")
    assert [item["name"] for item in visible] == ["笑顔・制服"]
    assert visible[0]["parts"]["torso"] == "MMK_T00_ARM01_CLO00"
    assert visible[0]["blink"] is False

    renamed = store.rename(momoko["id"], "笑顔")
    duplicate = store.duplicate(momoko["id"], "笑顔コピー")
    assert renamed["name"] == "笑顔"
    assert duplicate["id"] != momoko["id"]
    assert [item["name"] for item in store.for_character("桃子")] == [
        "笑顔",
        "笑顔コピー",
    ]

    assert store.delete(momoko["id"])
    assert [item["name"] for item in store.for_character("桃子")] == ["笑顔コピー"]


def test_part_template_store_finds_matching_drawable_pattern(tmp_path):
    store = CharaPartTemplateStore(tmp_path / "templates.json")
    original = store.create(
        "微笑",
        "桃子",
        {"torso": "T00", "eye": "EYE01", "mouth": "MOUTH01"},
        blink=False,
    )

    assert store.find_matching_parts(
        "桃子",
        {"torso": "T00", "eye": "EYE01", "mouth": "MOUTH01"},
        blink=False,
    ) == original
    assert store.find_matching_parts(
        "桃子",
        {"torso": "T00", "eye": "EYE02", "mouth": "MOUTH01"},
        blink=False,
    ) is None
    assert store.find_matching_parts(
        "別キャラ",
        {"torso": "T00", "eye": "EYE01", "mouth": "MOUTH01"},
        blink=False,
    ) is None


def test_part_template_dialog_blocks_saving_matching_pattern(tmp_path, monkeypatch):
    store = CharaPartTemplateStore(tmp_path / "templates.json")
    store.create(
        "微笑",
        "桃子",
        {"torso": "MMK_T00", "eye": "MMK_F00_EYE01"},
        blink=True,
    )
    dialog = CharaCompositePreviewDialog(
        None,
        _empty_image_manager(),
        {"torso": "MMK_T00", "eye": "MMK_F00_EYE01", "blink": "true"},
        char_name="桃子",
        template_store=store,
    )
    messages = []
    monkeypatch.setattr(
        event_editor.QMessageBox,
        "information",
        lambda _parent, title, message: messages.append((title, message)),
    )
    monkeypatch.setattr(
        event_editor.QInputDialog,
        "getText",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("duplicate pattern must be rejected before naming")
        ),
    )

    dialog._save_current_template()

    assert len(store.for_character("桃子")) == 1
    assert messages
    assert "微笑" in messages[0][1]
    assert "同じです" in messages[0][1]


def test_part_template_dialog_applies_parts_and_blink_without_position(tmp_path):
    store = CharaPartTemplateStore(tmp_path / "templates.json")
    store.create(
        "笑顔",
        "桃子",
        {
            "torso": "MMK_T00_ARM01_CLO00",
            "eye": "MMK_F00_EYE00_00",
            "mouth": "MMK_F00_MOU04_01",
        },
        blink=False,
    )
    dialog = CharaCompositePreviewDialog(
        None,
        _empty_image_manager(),
        {"torso": "", "blink": "true"},
        char_name="桃子",
        char_name_options=["桃子"],
        template_store=store,
    )

    assert dialog._template_combo.count() == 1
    dialog.show()
    APP.processEvents()
    load_button = dialog.findChild(QPushButton, "loadPartTemplateButton")
    save_button = dialog.findChild(QPushButton, "savePartTemplateButton")
    assert load_button.text() == "選択テンプレを呼び出し"
    assert save_button.text() == "現在のパーツを保存"
    assert save_button.mapTo(dialog, QPoint(0, 0)).y() < dialog._combos["torso"].mapTo(
        dialog, QPoint(0, 0)
    ).y()
    dialog._apply_selected_template()
    result = dialog.get_result_fields()

    assert result["name"] == "桃子"
    assert result["torso"] == "MMK_T00_ARM01_CLO00"
    assert result["eye"] == "MMK_F00_EYE00_00"
    assert result["blink"] == "false"
    assert "x" not in result
    assert "y" not in result
    assert "size" not in result
    assert "template" not in result


def test_shift_dialog_returns_name_of_explicitly_loaded_template(tmp_path):
    store = CharaPartTemplateStore(tmp_path / "templates.json")
    store.create(
        "微笑",
        "桃子",
        {"torso": "MMK_T00", "eye": "MMK_F00_EYE01"},
    )
    dialog = CharaCompositePreviewDialog(
        None,
        _empty_image_manager(),
        {"torso": "MMK_T01", "blink": "true"},
        char_name="桃子",
        is_shift=True,
        template_store=store,
    )

    dialog._apply_selected_template()
    result = dialog.get_result_fields()

    assert result["template"] == "微笑"
