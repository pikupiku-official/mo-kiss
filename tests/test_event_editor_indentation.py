import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5.QtCore import QEvent, Qt
from PyQt5.QtGui import QKeyEvent, QTextCursor
from PyQt5.QtWidgets import QApplication

from event_editor import EventEditorGUI, KSTextEditor


APP = QApplication.instance() or QApplication([])


def _app():
    return APP


def _press_tab(editor):
    event = QKeyEvent(QEvent.KeyPress, Qt.Key_Tab, Qt.NoModifier)
    editor.keyPressEvent(event)


def test_tab_indents_every_line_touched_by_selection_and_keeps_selection():
    _app()
    editor = KSTextEditor()
    editor.setPlainText("alpha\nbeta\ngamma")
    cursor = editor.textCursor()
    cursor.setPosition(2)
    cursor.setPosition(9, QTextCursor.KeepAnchor)
    editor.setTextCursor(cursor)

    _press_tab(editor)

    assert editor.toPlainText() == "\talpha\n\tbeta\ngamma"
    assert editor.textCursor().hasSelection()
    assert editor.textCursor().selectionStart() == 3
    assert editor.textCursor().selectionEnd() == 11

    _press_tab(editor)
    assert editor.toPlainText() == "\t\talpha\n\t\tbeta\ngamma"


def test_tab_does_not_indent_line_at_exclusive_selection_end():
    _app()
    editor = KSTextEditor()
    editor.setPlainText("alpha\nbeta\ngamma")
    cursor = editor.textCursor()
    cursor.setPosition(0)
    cursor.setPosition(editor.document().findBlockByNumber(2).position(), QTextCursor.KeepAnchor)
    editor.setTextCursor(cursor)

    _press_tab(editor)

    assert editor.toPlainText() == "\talpha\n\tbeta\ngamma"


def test_adding_action_preserves_speaker_and_dialogue_tab_indent():
    source = '\t//momoko//\n\t「こんにちは」\n'
    step = EventEditorGUI._parse_steps_from_ks_text(None, source)[0]

    updated = EventEditorGUI._build_step_update_text(
        None,
        source,
        step,
        "momoko",
        "こんにちは",
        False,
        False,
        ['chara_show name="momoko"'],
    )

    assert updated.splitlines() == [
        '[chara_show name="momoko"]',
        '\t//momoko//',
        '\t「こんにちは」',
    ]
