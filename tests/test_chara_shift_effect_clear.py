import pytest
from dialogue.dialogue_loader import DialogueLoader
from dialogue.ir_builder import build_ir_from_normalized
from dialogue.scenario_manager import _ir_handle_character_shift, _ir_update_expressions

def test_dialogue_loader_chara_shift_clears_effect():
    loader = DialogueLoader()
    lines = [
        '[chara_show name="桃子" torso="MMK_T01" eye="EYE01" effect="E01"]',
        '[chara_shift name="桃子" eye="EYE02"]'
    ]
    data = loader.parse_ks_script(lines)
    # 2番目のエントリは chara_shift
    shift_entry = data[1]
    assert shift_entry['type'] == 'chara_shift'
    assert shift_entry['effect'] == ""

def test_ir_builder_chara_shift_clears_effect():
    dialogue_data = [
        {'type': 'chara_show', 'name': '桃子', 'torso': 'MMK_T01', 'eye': 'EYE01', 'effect': 'E01'},
        {'type': 'chara_shift', 'name': '桃子', 'eye': 'EYE02'}
    ]
    ir = build_ir_from_normalized(dialogue_data)
    shift_action = ir['steps'][1]['actions'][0]
    assert shift_action['action'] == 'chara_shift'
    assert shift_action['params']['effect'] == ""

def test_scenario_manager_chara_shift_clears_effect():
    game_state = {
        "active_characters": ["桃子"],
        "character_expressions": {
            "桃子": {
                "eye": "EYE01",
                "mouth": "",
                "brow": "",
                "cheek": "",
                "effect": "E01",
                "accessory": ""
            }
        }
    }
    params = {"eye": "EYE02"}
    _ir_handle_character_shift(game_state, "桃子", params)
    expressions = game_state["character_expressions"]["桃子"]
    assert expressions["effect"] == ""
