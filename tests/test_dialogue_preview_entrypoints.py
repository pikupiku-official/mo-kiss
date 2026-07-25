import inspect

from tools import dialogue_preview_player
from tools import dialogue_snapshot_renderer
from tools.preview_dialogue import preview_step_image


def test_snapshot_renderer_and_player_have_separate_entrypoints():
    assert dialogue_snapshot_renderer.main is not dialogue_preview_player.main
    assert hasattr(dialogue_snapshot_renderer, "run_snapshot_server")
    assert not hasattr(dialogue_preview_player, "run_snapshot_server")


def test_snapshot_defaults_to_settled_transition():
    signature = inspect.signature(preview_step_image)
    assert signature.parameters["transition_progress"].default == 1.0


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
