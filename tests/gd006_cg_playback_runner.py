"""Measure GD006's authored CG sequence with real time and keyboard SKIP.

Run from the repository root: python tests/gd006_cg_playback_runner.py <output-dir>
Add --reference to measure the committed CG renderer without changing files.
Uses an isolated save profile; only the initial seek uses the preview helper.
"""

import hashlib
import json
import os
from pathlib import Path
import statistics
import sys
import tempfile
import time
from contextlib import redirect_stdout

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)
os.environ.update(SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy", QT_QPA_PLATFORM="offscreen")


def snapshot():
    paths = list((ROOT / "events").glob("*.ks"))
    paths += list((ROOT / "data/current_state").glob("*"))
    paths += [ROOT / "events/story_flags.json"]
    return {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths if p.is_file()}


def summary(values):
    ordered = sorted(values)
    return {"frames": len(ordered), "median_ms": statistics.median(ordered),
            "p95_ms": ordered[int((len(ordered) - 1) * .95)], "max_ms": max(ordered)}


def main():
    output = Path(sys.argv[1]).resolve()
    output.mkdir(parents=True, exist_ok=True)
    before = snapshot()
    with tempfile.TemporaryDirectory(prefix="gd006-cg-") as profile, \
            (output / "runtime.log").open("w", encoding="utf-8") as log, redirect_stdout(log):
        os.environ["MOKISS_PROFILE_ROOT"] = profile
        Path(profile, "current_state").mkdir()
        import onnxruntime  # noqa: F401 - use the application's DLL load order
        import PyQt5
        os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = str(
            Path(PyQt5.__file__).parent / "Qt5/plugins/platforms")
        from PyQt5.QtWidgets import QApplication
        qt_app = QApplication.instance() or QApplication([])
        import pygame
        reference = "--reference" in sys.argv[2:]
        if reference:
            import subprocess
            import types

            source = subprocess.check_output(["git", "show", "HEAD:dialogue/cg_manager.py"])
            module = types.ModuleType("dialogue.cg_manager")
            module.__package__ = "dialogue"
            sys.modules[module.__name__] = module
            exec(compile(source, "committed/dialogue/cg_manager.py", "exec"), module.__dict__)
            module.prepare_cg_images = lambda gs: None
        from core import config
        config.IR_DUMP_JSON = False
        from demo.application import DemoApplication
        from demo.flow import STAGES
        from dialogue import cg_manager
        from tools.preview_dialogue import start_preview_at_step

        app = DemoApplication()
        draw = cg_manager.draw_cg
        load = pygame.image.load
        image_loads = []
        buckets = {"show": [], "crossfade": [], "static": []}
        transitions = []
        seen = set()
        render_ms = []
        midpoint = []

        def tracked_load(path, *args, **kwargs):
            image_loads.append(str(path))
            return load(path, *args, **kwargs)

        def measured_draw(gs):
            tr = gs.get("cg_state", {}).get("transition")
            bucket = "crossfade" if tr and tr["from_storage"] else "show" if tr else "static"
            if tr and (not transitions or transitions[-1]["state"] is not tr):
                transitions.append({"state": tr, "frames": 0})
            if tr:
                transitions[-1]["frames"] += 1
            started = time.perf_counter()
            draw(gs)
            buckets[bucket].append((time.perf_counter() - started) * 1000)
            if tr and tr["from_storage"] and "midpoint" not in seen:
                progress = (pygame.time.get_ticks() - tr["start_time"]) / tr["duration"]
                if .4 <= progress <= .6:
                    # PNG encoding would stall the fade being measured.
                    midpoint.append(gs["screen"].copy())
                    seen.add("midpoint")

        try:
            assert app.initialize()
            index = next(i for i, stage in enumerate(STAGES) if stage.source == "GD006.ks")
            app.demo_flow.index = index
            app.enter_stage(STAGES[index])
            scene = app.current_subsystem
            gs = scene.game_state
            steps = gs["ir_data"]["steps"]
            cg_steps = [(i, a) for i, step in enumerate(steps) for a in step.get("actions", [])
                        if a["action"] in ("cg_show", "cg_shift")]
            # Render the preceding dialogue once, just as real playback does.
            # Seeking directly into cg_show leaves an evicted BG cold and
            # incorrectly charges seek-only loading time to its first fade.
            start_preview_at_step(gs, cg_steps[0][0])
            app.run_frame()
            cg_manager.draw_cg = measured_draw
            pygame.image.load = tracked_load
            render = scene.render

            def measured_render():
                started = time.perf_counter()
                render()
                render_ms.append((time.perf_counter() - started) * 1000)

            scene.render = measured_render
            pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE, mod=0))
            pygame.event.post(pygame.event.Event(pygame.KEYUP, key=pygame.K_SPACE, mod=0))
            deadline = time.monotonic() + 90
            while True:
                assert time.monotonic() < deadline, "GD006 CG SKIP stalled"
                app.run_frame()
                assert app.current_subsystem is scene
                state = gs.get("cg_state", {})
                if state.get("storage"):
                    seen.add(state["storage"])
                if state.get("storage") == cg_steps[-1][1]["params"]["storage"] and not state.get("transition"):
                    break
                assert gs["text_renderer"].skip_mode
            assert len(transitions) == len(cg_steps), (len(transitions), len(cg_steps))
            for observed, (_, action) in zip(transitions, cg_steps):
                tr = observed["state"]
                assert tr["to_storage"] == action["params"]["storage"]
                assert tr["duration"] == round(action["params"]["fade"] * 1000)
                if not reference:
                    assert observed["frames"] >= 2, observed
            assert {a["params"]["storage"] for _, a in cg_steps} <= seen
            report = {"cg_draw": {k: summary(v) for k, v in buckets.items() if v},
                      "scene_render": summary(render_ms),
                      "transitions": [{"storage": t["state"]["to_storage"],
                                       "duration_ms": t["state"]["duration"], "frames": t["frames"]}
                                      for t in transitions],
                      "playback_image_loads": image_loads,
                      "scene_image_cache_mib": gs["_character_images"].bytes / 2**20,
                      "real_clock": True, "keyboard_skip": True, "reference": reference}
            if not reference:
                assert not image_loads, image_loads
            pygame.image.save(app.virtual_screen, str(output / "final.png"))
            if midpoint:
                pygame.image.save(midpoint[0], str(output / "midpoint.png"))
        finally:
            cg_manager.draw_cg = draw
            pygame.image.load = load
            app.cleanup()
    assert snapshot() == before, "authored KS or main save data changed"
    report["authored_ks_and_main_state_unchanged"] = True
    (output / "metrics.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
