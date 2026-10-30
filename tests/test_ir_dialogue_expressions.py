"""Dialogue-only speakers must not become visible character sprites."""

from pathlib import Path

import pytest

from dialogue.dialogue_loader import DialogueLoader
from dialogue.data_normalizer import normalize_dialogue_data
from dialogue.ir_builder import build_ir_from_normalized


ROOT = Path(__file__).resolve().parents[1]


def build_ir(content):
    raw = DialogueLoader()._parse_ks_content(content)
    return build_ir_from_normalized(normalize_dialogue_data(raw))


def character_actions(ir):
    return [action for step in ir['steps']
            for action in step.get('actions', [])
            if action['action'].startswith('chara_')]


def test_dialogue_only_speakers_do_not_emit_character_actions():
    ir = build_ir('//純一//\n「独白」\n//A//\n「男子」\n//C//\n「女子」')
    assert [step['text']['speaker'] for step in ir['steps']] == ['純一', 'A', 'C']
    assert character_actions(ir) == []


@pytest.mark.parametrize('filename', ['GD004.ks', 'GD005.ks', 'GD006.ks'])
def test_gd_character_actions_only_target_explicitly_shown_characters(filename):
    ir = build_ir((ROOT / 'events' / filename).read_text(encoding='utf-8'))
    shown = set()
    for action in character_actions(ir):
        if action['action'] == 'chara_show':
            shown.add(action['target'])
        assert action['target'] in shown, action


def test_clearing_an_existing_expression_still_emits_shift():
    # Legacy normalized dialogue can carry expression changes without an
    # explicit KS command. Preserve both setting and clearing those parts.
    def dialogue(eye):
        return [None, 'body', eye, '', '', '', 'line', None, 0.5, True, 'actor', False]

    ir = build_ir_from_normalized([dialogue('open'), dialogue(''), dialogue('')])
    actions = character_actions(ir)
    assert len(actions) == 2
    assert actions[0]['params'] == {'eye': 'open'}
    assert actions[1]['params'] == {'eye': ''}


def test_explicit_body_only_show_is_preserved():
    ir = build_ir('[chara_show name="actor" torso="body" x="0.3" size="2"]\n//actor//\n「line」')
    actions = character_actions(ir)
    assert len(actions) == 1
    assert actions[0]['action'] == 'chara_show'
    assert actions[0]['params']['torso'] == 'body'
    assert actions[0]['params']['x'] == 0.3
    assert actions[0]['params']['size'] == 2.0
