import os
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5.QtWidgets import QApplication

from core.config import CHAR_CODE
from event_editor import CharaCompositePreviewDialog


APP = QApplication.instance() or QApplication([])


def test_new_character_names_resolve_to_their_image_codes():
    assert CHAR_CODE["直樹"] == "NOK"
    assert CHAR_CODE["静"] == "SZK"
    assert CHAR_CODE["杏"] == "ANZ"


def test_character_preview_filters_assets_by_the_resolved_code():
    image_manager = SimpleNamespace(
        image_paths={
            "torso": {
                "NOK_T00_ARM01_CLO00": "nok.webp",
                "SZK_T00_ARM01_CLO00": "szk.webp",
                "ANZ_T00_ARM01_CLO00": "anz.webp",
                "MMK_T00_ARM01_CLO00": "mmk.webp",
            }
        }
    )

    for name, expected in (
        ("直樹", "NOK_T00_ARM01_CLO00"),
        ("静", "SZK_T00_ARM01_CLO00"),
        ("杏", "ANZ_T00_ARM01_CLO00"),
    ):
        dialog = SimpleNamespace(
            _require_name=True,
            _char_name=name,
            _image_manager=image_manager,
        )
        options = CharaCompositePreviewDialog._get_char_options(dialog, "torso")
        assert options == [expected]


def test_character_preview_discards_parts_owned_by_other_characters():
    dialog = SimpleNamespace(_char_name="直樹")
    fields = {
        "torso": "MMK_T00_ARM01_CLO00",
        "eye": "MST_F00_EYE_01",
        "mouth": "NOK_F00_MOU_01",
        "effect": "",
    }

    sanitized = CharaCompositePreviewDialog._sanitize_fields_for_character(
        dialog, fields
    )

    assert sanitized == {
        "torso": "",
        "eye": "",
        "mouth": "NOK_F00_MOU_01",
        "effect": "",
    }


def test_character_preview_shows_the_current_unsaved_step_dialogue():
    image_manager = SimpleNamespace(
        image_paths={part: {} for part in CharaCompositePreviewDialog.LAYER_ORDER}
    )
    dialog = CharaCompositePreviewDialog(
        None,
        image_manager,
        {},
        char_name="",
        step_speaker="Yuki",
        step_body="Current draft line",
        step_force_female=True,
    )

    assert dialog.dialogue_speaker_label.text() == "Yuki"
    assert dialog.dialogue_body_label.text() == "Current draft line"
    assert "#d00070" in dialog.dialogue_body_label.styleSheet()
    dialog.close()
