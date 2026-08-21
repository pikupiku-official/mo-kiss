import os
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5.QtCore import QPoint, Qt
from PyQt5.QtGui import QColor, QPalette
from PyQt5.QtWidgets import QApplication, QDialog, QStyleFactory

from event_editor import (
    EventEditorGUI,
    StepEditorDialog,
    Win2000FramelessMainWindow,
    apply_windows_2000_style,
)


APP = QApplication.instance() or QApplication([])


def test_windows_2000_style_uses_qt_classic_controls_and_palette():
    previous_style_name = APP.style().objectName()
    previous_palette = QPalette(APP.palette())
    try:
        has_windows_style = apply_windows_2000_style(APP)

        assert has_windows_style
        assert APP.style().objectName().lower() == "windows"
        palette = APP.palette()
        assert palette.color(QPalette.Active, QPalette.Window) == QColor(212, 208, 200)
        assert palette.color(QPalette.Active, QPalette.Highlight) == QColor(10, 36, 106)
        assert palette.color(QPalette.Disabled, QPalette.ButtonText) == QColor(128, 128, 128)
    finally:
        previous_style = QStyleFactory.create(previous_style_name)
        if previous_style is not None:
            APP.setStyle(previous_style)
        APP.setPalette(previous_palette)


def test_step_editor_uses_win2000_frame_and_caption_controls():
    manager = SimpleNamespace(
        image_paths={
            key: {}
            for key in (
                "bg", "torso", "brow", "cheek", "eye", "mouth",
                "accessory", "effect",
            )
        }
    )
    step = {"step_index": 0, "speaker": "A", "body": "line"}
    dialog = StepEditorDialog(
        None,
        step,
        actions=[],
        all_steps=[step],
        all_step_actions=[[]],
        step_index=0,
        image_manager=manager,
    )

    assert dialog.windowFlags() & Qt.FramelessWindowHint
    assert dialog.title_bar.title_label.text() == "step編集"
    assert dialog.title_bar.minimize_button.role == "minimize"
    assert dialog.title_bar.maximize_button.role == "maximize"
    assert dialog.title_bar.close_button.role == "close"
    assert dialog._resize_edges_at(QPoint(0, 0)) == (Qt.LeftEdge | Qt.TopEdge)

    dialog.show()
    APP.processEvents()
    dialog.title_bar.toggle_maximize()
    APP.processEvents()
    assert dialog.isMaximized()
    assert dialog.title_bar.maximize_button.role == "restore"
    assert dialog._frame_layout.contentsMargins().left() == 0

    dialog.title_bar.toggle_maximize()
    APP.processEvents()
    assert not dialog.isMaximized()
    assert dialog.title_bar.maximize_button.role == "maximize"
    assert dialog._frame_layout.contentsMargins().left() == dialog.FRAME_WIDTH
    dialog.title_bar.close_button.click()
    assert dialog.result() == QDialog.Rejected


def test_event_editor_main_window_uses_the_reusable_win2000_frame():
    assert issubclass(EventEditorGUI, Win2000FramelessMainWindow)

    window = Win2000FramelessMainWindow()
    window.setWindowTitle("KSファイル イベントエディタ")
    window.resize(800, 600)

    assert window.windowFlags() & Qt.FramelessWindowHint
    assert window.title_bar.title_label.text() == "KSファイル イベントエディタ"
    assert window._resize_edges_at(QPoint(799, 599)) == (
        Qt.RightEdge | Qt.BottomEdge
    )

    window.show()
    APP.processEvents()
    window.title_bar.toggle_maximize()
    APP.processEvents()
    assert window.isMaximized()
    assert window.title_bar.maximize_button.role == "restore"
    assert window.contentsMargins().left() == 0
    window.title_bar.close_button.click()
    APP.processEvents()
    assert not window.isVisible()
