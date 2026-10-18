"""Drive the real GDDEMO preview through its normal keyboard event path."""
from pathlib import Path
import contextlib
import json
import os
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
os.environ['MOKISS_PROFILE_ROOT'] = tempfile.mkdtemp(prefix='gddemo-seed-profile-')
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'
os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = str(ROOT / '.venv-gd/Lib/site-packages/PyQt5/Qt5/plugins/platforms')

import onnxruntime
import pygame
from PyQt5.QtWidgets import QApplication
app = QApplication([])
from tools import preview_dialogue as preview
from dialogue import controller2, scenario_manager
from dialogue.dialogue_loader import DialogueLoader
from dialogue.data_normalizer import normalize_dialogue_data
from dialogue.ir_builder import build_ir_from_normalized

state = dict(frame=0, submitted=0, overlay=None, overlay_frames=0, results=[], texts=[], finished=False)
answers = ['桃子は借金でお金がない', '妹に服を贈るのが嫌だったからだ', '金欠']
captured = {}
configure = preview.configure_seed_preview
update = controller2.update_game
handle_events = preview.dialogue_handle_events
flip = pygame.display.flip
open_answer = scenario_manager._handle_seed_answer

def open_with_playback_mode(gs, command, initial_text=''):
    if '--skip' in sys.argv and not state.get('skip_enabled'):
        gs['text_renderer'].skip_mode = True
        state['skip_enabled'] = True
    if '--auto' in sys.argv and not state.get('auto_enabled'):
        gs['text_renderer'].auto_mode = True
        state['auto_enabled'] = True
    return open_answer(gs, command, initial_text)

def configure_and_capture(gs, path):
    configure(gs, path)
    captured['gs'] = gs

def drive(gs):
    update(gs)
    state['frame'] += 1
    assert state['frame'] < 1200, 'preview did not finish'
    renderer = gs['text_renderer']
    renderer.skip_text()
    text = renderer.current_text
    if text and (not state['texts'] or state['texts'][-1] != text):
        state['texts'].append(text)
    overlay = gs.get('seed_answer_overlay')
    if overlay:
        if overlay is not state['overlay']:
            state['overlay'] = overlay
            state['overlay_frames'] = 0
        state['overlay_frames'] += 1
        if state['overlay_frames'] == 3:
            index = state['submitted']
            assert index < len(answers), 'unexpected retry'
            overlay.text = ''
            pygame.event.post(pygame.event.Event(pygame.TEXTINPUT, text=answers[index]))
            pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN, mod=0))
            pygame.event.post(pygame.event.Event(pygame.KEYUP, key=pygame.K_RETURN, mod=0))
            state['submitted'] += 1
        return
    if state['overlay'] is not None:
        state['results'].append(state['overlay'].last_verdict['result'])
        state['overlay'] = None
    if state['frame'] % 3 == 0 and controller2.is_ir_idle(gs):
        pygame.event.post(pygame.event.Event(pygame.KEYUP, key=pygame.K_RETURN, mod=0))
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN, mod=0))
        pygame.event.post(pygame.event.Event(pygame.KEYUP, key=pygame.K_RETURN, mod=0))

def observe_events(gs, screen):
    result = handle_events(gs, screen)
    if not result:
        state['finished'] = True
    return result

def capture_frame():
    gs = captured.get('gs')
    if gs and gs['text_renderer'].current_text == 'ふたりとも、ありがとっ！':
        pygame.image.save(gs['screen'], str(Path(__file__).with_name('seed-success.png')))
    flip()

preview.configure_seed_preview = configure_and_capture
scenario_manager._handle_seed_answer = open_with_playback_mode
controller2.update_game = drive
preview.dialogue_handle_events = observe_events
pygame.display.flip = capture_frame
preview.IR_DUMP_JSON = False
preview.DEBUG = False
ir = build_ir_from_normalized(normalize_dialogue_data(DialogueLoader().load_dialogue_from_ks(str(ROOT / 'events/GDDEMO.ks'))))
start_step = next(i for i, step in enumerate(ir['steps'], 1) if any(a['action'] == 'seed_answer' for a in step.get('actions', [])))
if '--from-start' in sys.argv:
    start_step = 1
try:
    stem = 'seed-flow-skip' if '--skip' in sys.argv else ('seed-flow-auto' if '--auto' in sys.argv else 'reproduce_seed_flow')
    with Path(__file__).with_name(stem + '.log').open('w', encoding='utf-8') as log, contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
        state['preview_result'] = preview.preview_ks_file(str(ROOT / 'events/GDDEMO.ks'), start_step=start_step)
finally:
    gs = captured.get('gs', {})
    state['position'] = {key: gs.get(key) for key in ['current_paragraph', 'ir_step_index', 'ks_finished']}
    state['anims'] = {key: repr(gs.get(key)) for key in ['ir_waiting_for_anim', 'ir_active_anims', 'character_transitions', 'character_part_fades', 'character_fade_pending_render']}
    state['overlay'] = repr(state['overlay'])
    Path(__file__).with_name(stem + '.json').write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({key: state[key] for key in ['frame', 'submitted', 'results', 'finished', 'position']}, ensure_ascii=False))
assert state['results'] == ['incorrect', 'borderline', 'correct'], state
assert state['texts'].count('（もう一度状況を整理しよう。）') == 2, state
assert 'ふたりとも、ありがとっ！' in state['texts'], state
