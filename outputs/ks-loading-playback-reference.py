"""Run the real CG playback with the pre-change scene preparation."""
import os
from pathlib import Path
import runpy
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)
os.environ.update(SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy", QT_QPA_PLATFORM="offscreen")
import onnxruntime
import dialogue.character_images as module

source = (ROOT / "outputs/ks-character-images-before.py.txt").read_text(encoding="utf-8")
exec(compile(source, "reference/character_images.py", "exec"), module.__dict__)


def serial_prepare_many(self, requests):
    for (category, key), scales in requests.items():
        self.prepare(category, key, scales)
        yield


# The current CG preparation calls the common batch helper; make this serial
# for the reference, just as it was before the loading changes.
module.CharacterImages.prepare_many = serial_prepare_many
sys.argv = ["tests/gd006_cg_playback_runner.py", "outputs/ks-loading-cg-reference"]
runpy.run_path(str(ROOT / sys.argv[0]), run_name="__main__")
