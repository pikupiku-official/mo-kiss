"""Measure real KS parsing and scene image preparation with isolated saves."""
import cProfile
from collections import Counter
from contextlib import redirect_stdout
import gc
import hashlib
import io
import json
import os
from pathlib import Path
import pstats
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)
os.environ.update(SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy", QT_QPA_PLATFORM="offscreen")

import pygame
if os.environ.get("KS_LOADING_REFERENCE"):
    import dialogue.character_images as reference_module
    reference_source = Path(os.environ["KS_LOADING_REFERENCE"]).read_text(encoding="utf-8")
    exec(compile(reference_source, "reference/character_images.py", "exec"), reference_module.__dict__)

    def serial_prepare_many(self, requests):
        for (category, key), scales in requests.items():
            self.prepare(category, key, scales)
            yield

    reference_module.CharacterImages.prepare_many = serial_prepare_many
from core.services.image_manager import ImageManager
from dialogue.dialogue_loader import DialogueLoader
from dialogue.data_normalizer import normalize_dialogue_data
from dialogue.ir_builder import build_ir_from_normalized
from dialogue.character_images import prepare_character_images


def measure(filename):
    manager = ImageManager(cache_bytes=64 * 1024 * 1024)
    loader = DialogueLoader(False)
    loads = Counter()
    load_ms = 0.0
    original = pygame.image.load

    def tracked(path, *args, **kwargs):
        nonlocal load_ms
        start = time.perf_counter()
        result = original(path, *args, **kwargs)
        load_ms += (time.perf_counter() - start) * 1000
        loads[str(path)] += 1
        return result

    pygame.image.load = tracked
    profile = cProfile.Profile()
    try:
        start = time.perf_counter()
        manager.scan_image_paths(1440, 1080)
        scan_ms = (time.perf_counter() - start) * 1000
        start = time.perf_counter()
        raw = loader.load_dialogue_from_ks(filename)
        ir = build_ir_from_normalized(normalize_dialogue_data(raw))
        parse_ms = (time.perf_counter() - start) * 1000
        state = {"image_manager": manager, "ir_data": ir}
        start = time.perf_counter()
        profile.runcall(prepare_character_images, state)
        prepare_ms = (time.perf_counter() - start) * 1000
        summary = io.StringIO()
        pstats.Stats(profile, stream=summary).strip_dirs().sort_stats("cumulative").print_stats(18)
        result = {"ks": filename, "scan_ms": scan_ms, "parse_ms": parse_ms,
                  "prepare_ms": prepare_ms, "decode_ms": load_ms,
                  "decodes": sum(loads.values()), "unique_images": len(loads),
                  "duplicate_decodes": {Path(p).name: n for p, n in loads.items() if n > 1},
                  "renditions": len(state["_character_images"].images),
                  "cache_mib": state["_character_images"].bytes / 2**20,
                  "pixels": {str(key): {"sha256": hashlib.sha256(pygame.image.tobytes(image.pixels, "RGBA")).hexdigest(),
                                        "bounds": list(image.bounds), "size": image.size}
                             for key, image in state["_character_images"].images.items()},
                  "profile": summary.getvalue()}
    finally:
        pygame.image.load = original
        manager.cleanup()
        loader.executor.shutdown(wait=True)
    return result


if __name__ == "__main__":
    output = Path(sys.argv[1])
    pygame.init()
    pygame.display.set_mode((1, 1))
    rows = []
    with tempfile.TemporaryDirectory(prefix="ks-load-") as temporary:
        os.environ["MOKISS_PROFILE_ROOT"] = temporary
        Path(temporary, "current_state").mkdir()
        for filename in sys.argv[2:]:
            with redirect_stdout(io.StringIO()):
                row = measure(filename)
            rows.append(row)
            print(json.dumps({k: v for k, v in row.items() if k not in ("profile", "pixels")}, ensure_ascii=False), flush=True)
            gc.collect()
    pygame.quit()
    output.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
