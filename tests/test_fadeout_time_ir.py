from dialogue.data_normalizer import normalize_dialogue_data
from dialogue.ir_builder import build_ir_from_normalized


def _fadeout_action(ir):
    return next(
        action
        for step in ir["steps"]
        for action in step.get("actions", [])
        if action["action"] == "fadeout"
    )


def test_fadeout_time_is_preserved_as_structured_ir_data():
    normalized = normalize_dialogue_data(
        [{"type": "fadeout", "color": "black", "time": 3.25}]
    )

    assert normalized[0][12] == {"color": "black", "time": 3.25}
    assert _fadeout_action(build_ir_from_normalized(normalized))["params"] == {
        "color": "black",
        "time": 3.25,
    }


def test_fadeout_ir_prefers_structured_time_over_legacy_command_text():
    normalized = [
        [None, None, None, None, None, None, "_FADEOUT_black_1.0",
         None, 0.5, True, None, False, {"color": "black", "time": 2.5}]
    ]

    assert _fadeout_action(build_ir_from_normalized(normalized))["params"]["time"] == 2.5
