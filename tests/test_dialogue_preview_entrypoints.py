import inspect
import sys
from types import SimpleNamespace

from tools import dialogue_preview_player
from tools import dialogue_snapshot_renderer
from tools import preview_dialogue
from tools.preview_dialogue import preview_step_image, start_preview_at_step
from event_editor import EventEditorGUI


def test_snapshot_renderer_and_player_have_separate_entrypoints():
    assert dialogue_snapshot_renderer.main is not dialogue_preview_player.main
    assert hasattr(dialogue_snapshot_renderer, "run_snapshot_server")
    assert not hasattr(dialogue_preview_player, "run_snapshot_server")


def test_snapshot_defaults_to_settled_transition():
    signature = inspect.signature(preview_step_image)
    assert signature.parameters["transition_progress"].default == 1.0


def test_interactive_player_forwards_requested_start_step(monkeypatch, tmp_path):
    ks_file = tmp_path / "event.ks"
    ks_file.write_text("", encoding="utf-8")
    calls = []
    monkeypatch.setattr(
        dialogue_preview_player,
        "preview_ks_file",
        lambda path, start_step=1: calls.append((path, start_step)) or True,
    )
    monkeypatch.setattr(
        sys,
        "argv",
        ["dialogue_preview_player.py", str(ks_file), "--step", "4"],
    )

    assert dialogue_preview_player.main() == 0
    assert calls == [(str(ks_file), 4)]


def test_start_preview_at_step_settles_prior_state_then_runs_target(monkeypatch):
    dispatched = []
    monkeypatch.setattr(
        preview_dialogue,
        "_ir_dispatch_action",
        lambda game_state, action: dispatched.append(action["action"]),
    )
    monkeypatch.setattr(preview_dialogue, "settle_step_preview_animations", lambda state: None)

    class TextRenderer:
        def __init__(self):
            self.calls = []

        def set_dialogue(self, *args, **kwargs):
            self.calls.append((args, kwargs))

    renderer = TextRenderer()
    state = {
        "use_ir": True,
        "ir_data": {
            "steps": [
                {"id": "step_0001", "actions": [{"action": "bg_show"}]},
                {"id": "step_0002", "text": {"speaker": "B", "body": "target"}},
            ]
        },
        "ir_step_index": -1,
        "ir_active_anims": [],
        "text_renderer": renderer,
        "active_characters": [],
    }

    assert start_preview_at_step(state, 2) is True
    assert dispatched == ["bg_show"]
    assert state["ir_step_index"] == 1
    assert renderer.calls[-1][0][0:2] == ("target", "B")


def test_event_editor_preview_command_contains_selected_step():
    editor = SimpleNamespace(current_file_path="event.ks")

    command = EventEditorGUI._preview_player_command(editor, "player.py", 7)

    assert command == [sys.executable, "player.py", "event.ks", "--step", "7"]


def test_snapshot_rejects_invalid_transition_progress(tmp_path):
    try:
        preview_step_image(
            "unused.ks",
            1,
            str(tmp_path / "unused.png"),
            transition_progress=1.5,
        )
    except ValueError as exc:
        assert "between 0.0 and 1.0" in str(exc)
    else:
        raise AssertionError("invalid transition progress was accepted")


def test_snapshot_server_forces_utf8_stdio(monkeypatch):
    class FakeStream:
        def __init__(self):
            self.calls = []

        def reconfigure(self, **kwargs):
            self.calls.append(kwargs)

    streams = [FakeStream(), FakeStream(), FakeStream()]
    monkeypatch.setattr(dialogue_snapshot_renderer.sys, "stdin", streams[0])
    monkeypatch.setattr(dialogue_snapshot_renderer.sys, "stdout", streams[1])
    monkeypatch.setattr(dialogue_snapshot_renderer.sys, "stderr", streams[2])

    dialogue_snapshot_renderer.configure_utf8_stdio()

    for stream in streams:
        assert stream.calls == [{"encoding": "utf-8", "errors": "strict"}]
