import os
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5.QtWidgets import QApplication, QMessageBox, QTextEdit

from event_editor import EventEditorGUI


APP = QApplication.instance() or QApplication([])


class _TimerStub:
    def __init__(self):
        self.stopped = 0

    def stop(self):
        self.stopped += 1


def test_step_editor_apply_marks_replaced_ks_text_unsaved():
    editor = QTextEdit()
    editor.setPlainText("before")
    editor.document().setModified(False)
    scheduled = []
    harness = SimpleNamespace(
        text_editor=editor,
        step_memos={},
        memos_modified=False,
        _build_step_update_text=lambda *args, **kwargs: "after",
        update_step_highlights=lambda: None,
        _schedule_realtime_save=lambda: scheduled.append(True),
    )

    EventEditorGUI._apply_step_update(
        harness,
        {"step_index": 0},
        "",
        "",
        False,
        False,
        [],
    )

    assert editor.toPlainText() == "after"
    assert editor.document().isModified()
    assert scheduled == [True]


def test_insert_step_reindexes_memos_and_marks_text_unsaved():
    editor = QTextEdit()
    editor.setPlainText('//A//\n「one」\n//B//\n「two」')
    editor.document().setModified(False)
    scheduled = []
    harness = SimpleNamespace(
        text_editor=editor,
        step_memos={0: "first memo", 1: "second memo"},
        memos_modified=False,
        update_step_highlights=lambda: None,
        _schedule_realtime_save=lambda: scheduled.append(True),
    )

    inserted_index = EventEditorGUI._insert_step_template(
        harness,
        {"step_index": 1, "start_line": 2, "end_line": 3},
        insert_before=True,
    )

    assert inserted_index == 1
    assert harness.step_memos == {0: "first memo", 2: "second memo"}
    assert "; --- new step ---" in editor.toPlainText()
    assert editor.document().isModified()
    assert scheduled == [True]


def test_file_switch_prompts_and_stays_on_current_file_when_save_fails(
    monkeypatch, tmp_path
):
    prompts = []
    loaded = []
    restored = []
    timer = _TimerStub()
    harness = SimpleNamespace(
        events_dir=str(tmp_path),
        current_file="old.ks",
        current_file_path=str(tmp_path / "old.ks"),
        realtime_save_timer=timer,
        _has_unsaved_changes=lambda: True,
        save_file=lambda: False,
        _restore_file_list_selection=lambda: restored.append(True),
        load_file=lambda path: loaded.append(path),
        load_event_metadata=lambda event_id: loaded.append(event_id),
    )
    item = SimpleNamespace(text=lambda: "new.ks")

    def answer(*args, **kwargs):
        prompts.append((args, kwargs))
        return QMessageBox.Save

    monkeypatch.setattr(QMessageBox, "question", answer)

    EventEditorGUI.on_file_select(harness, item)

    assert len(prompts) == 1
    assert timer.stopped == 1
    assert restored == [True]
    assert loaded == []


def test_file_select_loads_file_without_opening_step_editor(tmp_path):
    opened_steps = []
    first_step = {"step_index": 0, "speaker": "A", "body": "line"}
    loaded_metadata = []
    harness = SimpleNamespace(
        events_dir=str(tmp_path),
        current_file_path=None,
        realtime_save_timer=_TimerStub(),
        current_steps=[],
        _has_unsaved_changes=lambda: False,
        load_event_metadata=lambda event_id: loaded_metadata.append(event_id),
        open_step_editor=lambda step: opened_steps.append(step),
    )

    def load_file(filepath):
        harness.current_steps = [first_step]
        return True

    harness.load_file = load_file

    EventEditorGUI.on_file_select(harness, SimpleNamespace(text=lambda: "new.ks"))

    assert harness.current_steps == [first_step]
    assert loaded_metadata == ["new"]
    assert opened_steps == []
