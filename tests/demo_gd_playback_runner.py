"""Exercise authored demo questions and CGs through the real demo runtime."""

import hashlib
import os
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)
os.environ.update(SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy", QT_QPA_PLATFORM="offscreen")


def snapshot():
    paths = list((ROOT / "data/current_state").glob("*"))
    paths += [ROOT / "events/story_flags.json"]
    paths += list((ROOT / "events").glob("GD*.ks"))
    return {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in paths if path.is_file()}


def main():
    before = snapshot()
    # Select the isolated profile before importing shared singletons.
    with tempfile.TemporaryDirectory(prefix="demo-gd-playback-") as profile:
        os.environ["MOKISS_PROFILE_ROOT"] = profile
        Path(profile, "current_state").mkdir()
        import onnxruntime  # noqa: F401 - DLL load order matches demo.py
        import PyQt5
        plugins = Path(PyQt5.__file__).parent / "Qt5/plugins"
        os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = str(plugins / "platforms")
        from PyQt5.QtWidgets import QApplication
        qt_app = QApplication.instance() or QApplication([])
        import pygame
        from core import config
        from demo.application import DemoApplication
        from demo.flow import STAGES
        from dialogue import controller2, scenario_manager

        config.IR_DUMP_JSON = False
        output = ROOT / "outputs/demo-gd-playback-20261030"
        output.mkdir(parents=True, exist_ok=True)
        app = DemoApplication()
        original_ticks = pygame.time.get_ticks
        try:
            assert app.initialize()
            ticks = [original_ticks()]
            pygame.time.get_ticks = lambda: ticks[0]
            app.clock = type("Clock", (), {"tick": lambda self, fps: None})()
            for index, tp_id, correct, required_text, need_cg in (
                (1, "MOMOKO_GD_MONEY", "金欠", "ふたりとも、ありがとっ！", False),
                (9, "MOMOKO_TORO", "家族と不仲", "だから、僕に話してくれよ。", True),
            ):
                app.demo_flow.index = index
                app.enter_stage(STAGES[index])
                scene = app.current_subsystem
                gs = scene.game_state
                results, texts, cgs = [], set(), set()
                answers = iter(("バナナ", correct))
                for frame in range(3000):
                    ticks[0] += 1000
                    renderer = gs["text_renderer"]
                    renderer.skip_text()
                    texts.add(renderer.current_text)
                    overlay = gs.get("seed_answer_overlay")
                    if overlay is not None:
                        assert not overlay.suspended, overlay.last_verdict
                        answer = next(answers)
                        overlay.text = ""
                        # Traverse the same text-input/controller route as demo.py.
                        pygame.event.post(pygame.event.Event(pygame.TEXTINPUT, text=answer))
                        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN, mod=0))
                        app.run_frame()
                        results.append(overlay.last_verdict["result"])
                        continue
                    if controller2.is_ir_idle(gs):
                        if not scenario_manager.advance_dialogue(gs):
                            break
                    app.run_frame()
                    assert app.current_subsystem is scene, "unexpected stage transition"
                    state = gs.get("cg_state", {})
                    storage = state.get("storage")
                    if storage and not state.get("transition") and storage not in cgs:
                        cgs.add(storage)
                        pygame.image.save(app.virtual_screen, str(output / f"{storage}.png"))
                        # The upper viewport must show the actual CG, not only state.
                        from dialogue.cg_manager import _cg_surface_and_pos
                        cg, pos = _cg_surface_and_pos(gs, storage, 0, 0, 1)
                        expected = pygame.Surface(app.virtual_screen.get_size())
                        expected.blit(cg, pos)
                        assert app.virtual_screen.get_at((720, 200)) == expected.get_at((720, 200))
                else:
                    raise AssertionError(f"{tp_id}: playback did not finish")
                assert results == ["incorrect", "correct"], (tp_id, results)
                assert any(required_text in text for text in texts), (tp_id, texts)
                assert any("もう一度状況を整理しよう" in text for text in texts)
                if need_cg:
                    assert {"MMK_03_011", "MMK_03_006", "MMK_03_012"} <= cgs, cgs
                print(f"{tp_id}: retry -> correct; CG variants={sorted(cgs)}", flush=True)
            print("DEMO_GD_PLAYBACK_OK", flush=True)
        finally:
            pygame.time.get_ticks = original_ticks
            app.cleanup()
        assert snapshot() == before, "main progress or authored KS changed during playback"
        print("MAIN_STATE_AND_KS_UNCHANGED", flush=True)


if __name__ == "__main__":
    main()
