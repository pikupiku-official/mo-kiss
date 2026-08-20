import os
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5.QtCore import QPoint
from PyQt5.QtWidgets import QApplication, QPushButton

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
