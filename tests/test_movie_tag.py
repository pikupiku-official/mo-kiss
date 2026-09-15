from dialogue.data_normalizer import normalize_dialogue_data
from dialogue.dialogue_loader import DialogueLoader
from dialogue.ir_builder import build_ir_from_normalized
from dialogue.scenario_manager import _ir_get_action_duration_ms
from dialogue.scenario_manager import _ir_handle_haze_show


def test_movie_tags_keep_overlay_attributes_through_ir():
    raw = DialogueLoader().parse_ks_script(
        '[movie_show file="heavy_rain.mp4" loop="true" opacity="0.55" fade="0.8" mode="alpha" fit="cover"]\n'
        '[movie_hide fade="0.6"]'
    )

    normalized = normalize_dialogue_data(raw)
    ir = build_ir_from_normalized(normalized)
    actions = [action for step in ir["steps"] for action in step.get("actions", [])]

    assert [action["action"] for action in actions] == ["movie_show", "movie_hide"]
    assert actions[0]["params"]["file"] == "heavy_rain.mp4"
    assert actions[0]["params"]["opacity"] == 0.55
    assert actions[0]["params"]["mode"] == "alpha"
    assert actions[0]["params"]["fit"] == "cover"
    assert actions[1]["params"]["fade"] == 0.6


def test_movie_fade_duration_is_configurable():
    assert _ir_get_action_duration_ms("movie_show", {"fade": 0.8}) == 800
    assert _ir_get_action_duration_ms("movie_hide", {"fade": 0.6}) == 600


def test_legacy_background_tag_is_emitted_as_a_runtime_action():
    raw = DialogueLoader().parse_ks_script(
        '[bg storage="通学路①"]\n'
        '「雨」'
    )
    normalized = normalize_dialogue_data(raw)
    ir = build_ir_from_normalized(normalized)
    actions = [action for step in ir["steps"] for action in step.get("actions", [])]

    assert any(
        action["action"] == "bg_show"
        and action["params"].get("storage") == "通学路①"
        for action in actions
    )


def test_background_is_applied_before_adjacent_movie_show():
    raw = [
        {"type": "movie_show", "file": "heavy_rain.mp4"},
        {"type": "background", "value": "通学路①"},
    ]
    normalized = normalize_dialogue_data(raw)
    ir = build_ir_from_normalized(normalized)
    actions = [action for step in ir["steps"] for action in step.get("actions", [])]

    assert [action["action"] for action in actions] == ["bg_show", "movie_show"]


def test_leading_rain_scene_setup_is_committed_in_one_initial_step():
    raw = [
        {"type": "background", "value": "BG_TEST"},
        {"type": "movie_show", "file": "heavy_rain.mp4"},
        {"type": "rain_sound", "preset": "heavy"},
        {"type": "haze_show", "opacity": 0.75, "fade": 0.8},
    ]

    normalized = normalize_dialogue_data(raw)
    ir = build_ir_from_normalized(normalized)

    assert len(ir["steps"]) == 1
    assert [
        action["action"] for action in ir["steps"][0]["actions"]
    ] == ["bg_show", "movie_show", "rain_sound", "haze_show"]


def test_initial_haze_setup_skips_fade_until_first_frame(monkeypatch):
    class FakeHazeManager:
        def __init__(self):
            self.params = None

        def show(self, params):
            self.params = params

    manager = FakeHazeManager()
    monkeypatch.setattr(
        "dialogue.haze_manager.get_haze_manager",
        lambda _game_state: manager,
    )
    _ir_handle_haze_show(
        {"ir_step_index": 0},
        {"opacity": 0.75, "fade": 0.8},
    )

    assert manager.params["fade"] == 0.0


def test_legacy_background_storage_with_underscore_is_not_truncated():
    raw = [{"type": "background", "value": "BG_TEST"}]
    normalized = normalize_dialogue_data(raw)
    ir = build_ir_from_normalized(normalized)
    actions = [action for step in ir["steps"] for action in step.get("actions", [])]

    assert actions[0]["action"] == "bg_show"
    assert actions[0]["params"]["storage"] == "BG_TEST"


def test_rain_sound_and_haze_are_independent_ir_actions():
    raw = DialogueLoader().parse_ks_script(
        '[rain_sound preset="heavy" volume="0.32" fade="0.8"]\n'
        '[haze_show color="218,226,232" opacity="0.16" fade="0.8"]\n'
        '[rain_sound_stop fade="0.6"]\n'
        '[haze_hide fade="0.6"]'
    )
    normalized = normalize_dialogue_data(raw)
    ir = build_ir_from_normalized(normalized)
    actions = [action for step in ir["steps"] for action in step.get("actions", [])]

    assert [action["action"] for action in actions] == [
        "rain_sound", "haze_show", "rain_sound_stop", "haze_hide",
    ]
    assert actions[0]["params"] == {"preset": "heavy", "volume": 0.32, "fade": 0.8}
    assert actions[1]["params"]["opacity"] == 0.16
