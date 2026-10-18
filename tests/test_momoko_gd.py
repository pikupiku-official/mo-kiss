"""Real-model answers and actual preview playback for the GD tutorial."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
pytest.importorskip('onnxruntime')
import pygame

from core.services.seed_manager import SeedManager

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / 'data/evaluation/momoko_gd_money.json').read_text(encoding='utf-8'))
CASES = [(split, expected, answer)
         for split in ('calibration', 'validation', 'holdout')
         for expected, answers in DATA[split].items() for answer in answers]


@pytest.fixture(scope='module')
def manager():
    return SeedManager()


@pytest.mark.parametrize('split,expected,answer', CASES)
def test_real_model_tutorial_branch(manager, split, expected, answer):
    verdict = manager.judge_answer(DATA['turning_point_id'], answer)
    if expected == 'correct':
        assert verdict['result'] == 'correct', (split, answer, verdict)
    else:
        assert verdict['result'] in ('incorrect', 'borderline'), (split, answer, verdict)


def test_existing_preview_plays_retry_then_success(monkeypatch, tmp_path):
    """Run the real renderer/controller, type answers, and traverse the KS IR."""
    import PyQt5
    # The local venv is below a Japanese path; give Qt its platform directory.
    plugins = Path(PyQt5.__file__).parent / 'Qt5/plugins'
    monkeypatch.setenv('QT_QPA_PLATFORM_PLUGIN_PATH', str(plugins / 'platforms'))
    from PyQt5.QtWidgets import QApplication
    qt_app = QApplication.instance() or QApplication([])
    from tools import preview_dialogue as preview
    from dialogue import controller2, scenario_manager

    saved_paths = [ROOT / 'events/story_flags.json', ROOT / 'data/current_state/seed_state.json']
    before = {path: path.read_bytes() for path in saved_paths}
    captured = {}
    answers = ['桃子は借金でお金がない', '妹に服を贈るのが嫌だったからだ', '金欠']
    expected = ['incorrect', 'borderline', 'correct']
    config = preview.configure_seed_preview
    update = controller2.update_game
    flip = pygame.display.flip
    state = dict(frame=0, submitted=0, overlay=None, overlay_frames=0, results=[], texts=[], done=False)

    def configure(gs, path):
        config(gs, path)
        gs['seed_manager'].state['acquired'] = {}
        captured['gs'] = gs

    def update_and_drive(gs):
        update(gs)
        state['frame'] += 1
        assert state['frame'] < 700, 'preview did not finish the retry/success sequence'
        renderer = gs['text_renderer']
        renderer.skip_text()
        text = renderer.current_text
        if text and (not state['texts'] or text != state['texts'][-1]):
            state['texts'].append(text)
        overlay = gs.get('seed_answer_overlay')
        if overlay:
            if overlay is not state['overlay']:
                state['overlay'] = overlay
                state['overlay_frames'] = 0
                width = renderer._render_stable_text_line(overlay.prompt, (255, 255, 255)).get_width()
                assert renderer.text_start_x + width <= gs['screen'].get_width()
            state['overlay_frames'] += 1
            if state['overlay_frames'] == 3:
                index = state['submitted']
                assert index < len(answers), 'unexpected extra retry'
                overlay.text = ''
                pygame.event.post(pygame.event.Event(pygame.TEXTINPUT, text=answers[index]))
                pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN, mod=0))
                state['submitted'] += 1
            return
        if state['overlay'] is not None:
            state['results'].append(state['overlay'].last_verdict['result'])
            state['overlay'] = None
        if state['frame'] % 3 == 0 and controller2.is_ir_idle(gs):
            if not scenario_manager.advance_dialogue(gs):
                state['done'] = True
                pygame.event.post(pygame.event.Event(pygame.QUIT))

    def capture_frame():
        gs = captured.get('gs')
        if gs and gs.get('seed_answer_overlay') and state['overlay_frames'] == 2:
            pygame.image.save(gs['screen'], str(tmp_path / f'input-{state["submitted"]}.png'))
        if gs and 'ふたりとも、ありがとっ！' in gs['text_renderer'].current_text:
            pygame.image.save(gs['screen'], str(tmp_path / 'success.png'))
        flip()

    monkeypatch.setattr(preview, 'configure_seed_preview', configure)
    monkeypatch.setattr(controller2, 'update_game', update_and_drive)
    monkeypatch.setattr(pygame.display, 'flip', capture_frame)
    assert preview.preview_ks_file(str(ROOT / 'events/TestForGD.ks'))
    assert state['done']
    assert state['results'] == expected
    assert '（桃子は借金でお金がない・・・？）' in state['texts']
    assert '（妹に服を贈るのが嫌だったからだ・・・？）' in state['texts']
    assert state['texts'].count('（もう一度状況を整理しよう。）') == 2
    assert state['texts'].count('――そうだろ？') == 1
    assert (tmp_path / 'input-0.png').is_file()
    assert (tmp_path / 'success.png').is_file()
    assert all(path.read_bytes() == value for path, value in before.items())
