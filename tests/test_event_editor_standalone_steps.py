import os
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5.QtWidgets import QApplication

from dialogue.data_normalizer import normalize_dialogue_data
from dialogue.dialogue_loader import DialogueLoader
from dialogue.ir_builder import build_ir_from_normalized
from dialogue.ir_model import STANDALONE_STEP_MARKER
from dialogue.scenario_manager import advance_dialogue_ir
from event_editor import EventEditorGUI, StepEditorDialog


APP = QApplication.instance() or QApplication([])


def test_bgm_can_be_marked_as_a_dialogue_free_standalone_step():
    source = "\n".join(
        [
            '[bgm bgm="BGM_TITLE" volume="0.5" loop="true"]',
            STANDALONE_STEP_MARKER,
            "//A//",
            "「line」",
        ]
    )

    editor_steps = EventEditorGUI._parse_steps_from_ks_text(None, source)
    assert len(editor_steps) == 2
    assert editor_steps[0]["standalone"] is True
    assert editor_steps[0]["body"] == ""
    assert editor_steps[1]["body"] == "line"

    raw = DialogueLoader()._parse_ks_content(source)
    ir = build_ir_from_normalized(normalize_dialogue_data(raw))
    assert ir["steps"][0]["standalone"] is True
    assert ir["steps"][0]["actions"][0]["action"] == "bgm_play"
    assert ir["steps"][1]["text"]["body"] == "line"


def test_same_bgm_without_marker_stays_attached_to_dialogue():
    source = "\n".join(
        [
            '[bgm bgm="BGM_TITLE" volume="0.5" loop="true"]',
            "//A//",
            "「line」",
        ]
    )
    ir = build_ir_from_normalized(
        normalize_dialogue_data(DialogueLoader()._parse_ks_content(source))
    )

    assert len(ir["steps"]) == 1
    assert "standalone" not in ir["steps"][0]
    assert ir["steps"][0]["text"]["body"] == "line"


def test_step_editor_round_trip_preserves_standalone_marker():
    source = f'[fadeout color="black" time="1.0"]\n{STANDALONE_STEP_MARKER}'
    step = EventEditorGUI._parse_steps_from_ks_text(None, source)[0]

    updated = EventEditorGUI._build_step_update_text(
        None,
        source,
        step,
        "",
        "",
        False,
        False,
        ['fadeout color="black" time="1.0"'],
        standalone=True,
    )

    assert updated.splitlines() == [
        '[fadeout color="black" time="1.0"]',
        STANDALONE_STEP_MARKER,
    ]


def test_standalone_action_step_waits_for_the_next_advance():
    class TextRenderer:
        def __init__(self):
            self.calls = []

        def set_dialogue(self, *args, **kwargs):
            self.calls.append((args, kwargs))

    renderer = TextRenderer()
    game_state = {
        "ir_data": {
            "steps": [
                {"id": "step_0001", "actions": [{"action": "noop"}], "standalone": True},
                {"id": "step_0002", "text": {"speaker": "A", "body": "next"}},
            ]
        },
        "ir_step_index": -1,
        "text_renderer": renderer,
        "active_characters": [],
    }

    assert advance_dialogue_ir(game_state) is True
    assert game_state["ir_step_index"] == 0
    assert renderer.calls[-1][0][0:2] == ("", "")


def test_step_editor_exposes_standalone_control_only_for_supported_actions():
    step = {"step_index": 0, "speaker": "", "body": "", "standalone": True}
    image_manager = SimpleNamespace(
        image_paths={
            key: {}
            for key in ("bg", "torso", "brow", "cheek", "eye", "mouth", "accessory", "effect")
        }
    )
    dialog = StepEditorDialog(
        None,
        step,
        actions=['se se="door" volume="0.5"'],
        all_steps=[step],
        all_step_actions=[['se se="door" volume="0.5"']],
        step_index=0,
        image_manager=image_manager,
    )

    assert dialog.standalone_checkbox.isEnabled()
    assert dialog.standalone_checkbox.isChecked()
    dialog.body_input.setText("dialogue")
    assert not dialog.standalone_checkbox.isEnabled()
    assert not dialog.standalone_checkbox.isChecked()
    dialog.close()


def test_sestop_can_be_marked_as_a_dialogue_free_standalone_step():
    step = {"step_index": 0, "speaker": "", "body": "", "standalone": True}
    image_manager = SimpleNamespace(
        image_paths={
            key: {}
            for key in ("bg", "torso", "brow", "cheek", "eye", "mouth", "accessory", "effect")
        }
    )
    dialog = StepEditorDialog(
        None,
        step,
        actions=["sestop"],
        all_steps=[step],
        all_step_actions=[["sestop"]],
        step_index=0,
        image_manager=image_manager,
    )

    assert dialog.standalone_checkbox.isEnabled()
    assert dialog.standalone_checkbox.isChecked()
    dialog.close()
