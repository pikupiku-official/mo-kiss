import os
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5.QtWidgets import (
    QApplication,
    QComboBox,
    QDoubleSpinBox,
    QPushButton,
    QSlider,
)

import event_editor
from event_editor import StepEditorDialog


APP = QApplication.instance() or QApplication([])


def _image_manager():
    return SimpleNamespace(
        image_paths={
            "bg": {"classroom": "classroom.webp", "street": "street.webp"},
            **{
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
            },
        }
    )


def _dialog(action, manager=None):
    steps = [{"step_index": 0}]
    return StepEditorDialog(
        None,
        steps[0],
        actions=[action],
        all_steps=steps,
        all_step_actions=[[action]],
        step_index=0,
        image_manager=manager or _image_manager(),
    )


def test_background_storage_uses_editable_asset_dropdown():
    dialog = _dialog('bg_show storage="classroom"')
    field = dialog.custom_fields["storage"]

    assert isinstance(field, QComboBox)
    assert field.isEditable()
    assert [field.itemText(i) for i in range(field.count())] == [
        "",
        "classroom",
        "street",
    ]


def test_se_uses_dropdown_and_preview_buttons(monkeypatch, tmp_path):
    se_dir = tmp_path / "sounds" / "ses"
    se_dir.mkdir(parents=True)
    (se_dir / "door_open.wav").write_bytes(b"test")
    (se_dir / "ignore.txt").write_text("x", encoding="utf-8")
    monkeypatch.setattr(event_editor, "project_root", str(tmp_path))
    dialog = _dialog('se se="door_open.wav" volume="0.7"')
    field = dialog.custom_fields["se"]

    assert isinstance(field, QComboBox)
    assert "door_open.wav" in [field.itemText(i) for i in range(field.count())]
    play_button = dialog.findChild(QPushButton, "sePreviewButton")
    stop_button = dialog.findChild(QPushButton, "sePreviewStopButton")
    assert play_button is not None
    assert stop_button is not None
    assert play_button.parentWidget() is field.parentWidget()
    assert stop_button.parentWidget() is field.parentWidget()

    calls = []
    preview_manager = SimpleNamespace(
        stop_all_se=lambda: calls.append(("stop",)),
        play_se=lambda filename, volume, frequency: calls.append(
            ("play", filename, volume, frequency)
        ) or True,
        set_current_volume=lambda volume: calls.append(("volume", volume)),
    )
    dialog._se_preview_manager = preview_manager
    field.setCurrentText("door_open.wav")
    dialog._preview_selected_se()

    assert calls == [
        ("stop",),
        ("play", "door_open.wav", 0.7, 1),
    ]

    volume_field = dialog.custom_fields["volume"]
    volume_slider = dialog.findChild(QSlider, "volumeSlider")
    assert isinstance(volume_field, QDoubleSpinBox)
    assert volume_slider is not None
    volume_slider.setValue(35)
    assert volume_field.value() == 0.35
    assert calls[-1] == ("volume", 0.35)
    assert dict(dialog._collect_custom_params())["volume"] == "0.35"


def test_bgm_uses_dropdown_and_inline_preview_buttons(monkeypatch, tmp_path):
    bgm_dir = tmp_path / "sounds" / "bgms"
    bgm_dir.mkdir(parents=True)
    (bgm_dir / "school_daily_loop.ogg").write_bytes(b"test")
    (bgm_dir / "ignore.txt").write_text("x", encoding="utf-8")
    monkeypatch.setattr(event_editor, "project_root", str(tmp_path))
    dialog = _dialog(
        'bgm bgm="school_daily_loop.ogg" volume="0.6" loop="false" fade="1.2"'
    )
    field = dialog.custom_fields["bgm"]

    assert isinstance(field, QComboBox)
    assert field.isEditable()
    assert "school_daily_loop.ogg" in [
        field.itemText(i) for i in range(field.count())
    ]
    play_button = dialog.findChild(QPushButton, "bgmPreviewButton")
    stop_button = dialog.findChild(QPushButton, "bgmPreviewStopButton")
    assert play_button is not None
    assert stop_button is not None
    assert play_button.parentWidget() is field.parentWidget()
    assert stop_button.parentWidget() is field.parentWidget()

    calls = []
    preview_manager = SimpleNamespace(
        stop_bgm=lambda: calls.append(("stop",)),
        play_bgm=lambda *args, **kwargs: calls.append(("play", args, kwargs)) or True,
        set_volume=lambda volume: calls.append(("volume", volume)),
    )
    dialog._bgm_preview_manager = preview_manager
    dialog._preview_selected_bgm()

    assert calls == [
        ("stop",),
        (
            "play",
            ("school_daily_loop.ogg", 0.6, False),
            {"fade_time": 1.2},
        ),
    ]

    volume_field = dialog.custom_fields["volume"]
    volume_slider = dialog.findChild(QSlider, "volumeSlider")
    assert isinstance(volume_field, QDoubleSpinBox)
    assert volume_slider is not None
    volume_field.setValue(0.42)
    assert volume_slider.value() == 42
    assert calls[-1] == ("volume", 0.42)
    assert dict(dialog._collect_custom_params())["volume"] == "0.42"
