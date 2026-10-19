import os
from pathlib import Path
import sys

root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root))
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'
os.environ['MOKISS_PROFILE_ROOT'] = str(Path(__file__).parent / 'profile')
import onnxruntime  # The same DLL loading order as the interactive preview.
from tools.preview_dialogue import create_step_preview_runtime, preview_step_image
from tools.preview_english_dialogue import ENGLISH, MIXED
from dialogue.dialogue_loader import DialogueLoader
from dialogue.data_normalizer import normalize_dialogue_data
from dialogue.ir_builder import build_ir_from_normalized

out = Path(__file__).parent
scenario = out / 'english-layout.ks'
scenario.write_text('*start\n//Alex//\n「' + ENGLISH + '」\n[scroll-stop]\n'
                    '//主人公//\n「' + MIXED + '」\n', encoding='utf-8')
data = DialogueLoader(False).load_dialogue_from_ks(str(scenario))
ir = build_ir_from_normalized(normalize_dialogue_data(data))
bodies = [s['text']['body'] for s in ir['steps'] if s.get('text')]
assert bodies == [ENGLISH, MIXED], bodies
runtime = create_step_preview_runtime()
assert preview_step_image(str(scenario), 1, str(out / 'ks-english.png'), runtime=runtime), runtime.get('last_error')
assert preview_step_image(str(scenario), 2, str(out / 'ks-mixed.png'), runtime=runtime), runtime.get('last_error')
print('KS_FLOW_PREVIEW_OK')
