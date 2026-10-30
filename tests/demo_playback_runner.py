"""Play the real GD001 through SKIP, retry and success using only UI events."""

import cProfile
import hashlib
import json
import os
from pathlib import Path
import pstats
import sys
import tempfile
import time
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
os.environ["QT_QPA_PLATFORM"] = "offscreen"


def snapshot():
    paths = list((ROOT / "data/current_state").glob("*"))
    paths += list((ROOT / "events").glob("*.ks"))
    paths += [ROOT / "events/story_flags.json"]
    return {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths if p.is_file()}


def main():
    before = snapshot()
    output = ROOT / os.environ.get("MOKISS_PLAYBACK_OUTPUT", "outputs/demo-playback")
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="demo-playback-") as profile:
        os.environ["MOKISS_PROFILE_ROOT"] = profile
        Path(profile, "current_state").mkdir()
        import onnxruntime
        import PyQt5
        plugins = Path(PyQt5.__file__).parent / "Qt5/plugins"
        os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = str(plugins / "platforms")
        from PyQt5.QtWidgets import QApplication
        qt_app = QApplication.instance() or QApplication([])
        import pygame
        from demo.application import DemoApplication
        from demo.flow import STAGES

        app = DemoApplication()
        profiler = cProfile.Profile()
        frames = []
        fade_frames = []
        image_loads = []
        original_load = pygame.image.load

        def tracked_load(path, *args, **kwargs):
            image_loads.append(str(path))
            return original_load(path, *args, **kwargs)

        pygame.image.load = tracked_load

        def frame():
            current_scene = app.current_subsystem
            state = getattr(current_scene, 'game_state', {})
            step = state.get('ir_step_index')
            fading = bool(state.get('character_transitions') or state.get('character_part_fades'))
            loads_before = len(image_loads)
            started = time.perf_counter()
            app.run_frame()
            elapsed = time.perf_counter() - started
            frames.append(elapsed)
            if fading and app.current_subsystem is current_scene and state.get('ir_step_index') == step:
                fade_frames.append({'ms': elapsed * 1000, 'loads': image_loads[loads_before:]})

        def press(key):
            pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=key, mod=0))
            pygame.event.post(pygame.event.Event(pygame.KEYUP, key=key, mod=0))
            frame()

        def play_until(predicate):
            deadline = time.monotonic() + 180
            while not predicate():
                assert time.monotonic() < deadline, "real playback stalled"
                assert app.current_subsystem is scene, "GD001 left before its answer completed"
                frame()
                renderer = scene.game_state["text_renderer"]
                if renderer.skip_mode and renderer.current_text:
                    assert renderer.is_text_complete, "SKIP presented a partial paragraph"

        try:
            assert app.initialize()
            app.demo_flow.index = 1
            from core.ui.loading_screen import LoadingScreen
            from core.ui.debug_hud import get_debug_hud

            percentages = []
            original_show = LoadingScreen.show

            def tracked_show(painter, message="読み込み中...", progress=None):
                original_show(painter, message, progress=progress)
                if progress is not None:
                    percentages.append(progress)
                    if progress == 50:
                        pygame.image.save(app.window_surface, str(output / "gd001-loading-50.png"))

            started = time.perf_counter()
            with patch.object(LoadingScreen, "show", tracked_show):
                app.enter_stage(STAGES[1])
            assert percentages[0] == 0 and percentages[-1] == 100
            assert percentages == sorted(set(percentages))
            assert len(percentages) > 10
            print("GD001_LOADING_PROGRESS_OK", percentages, "seconds",
                  round(time.perf_counter() - started, 3), flush=True)
            scene = app.current_subsystem
            gs = scene.game_state
            renderer = gs["text_renderer"]
            # Both activation and cancellation must work in the actual opening
            # animation; no forced text completion or simulated clock is used.
            press(pygame.K_SPACE)
            assert renderer.skip_mode
            press(pygame.K_SPACE)
            assert not renderer.skip_mode
            press(pygame.K_a)
            assert renderer.auto_mode
            press(pygame.K_a)
            assert not renderer.auto_mode
            press(pygame.K_SPACE)
            assert renderer.skip_mode
            profiler.enable()
            play_until(lambda: gs.get("seed_answer_overlay") is not None)
            profiler.disable()
            profiler.dump_stats(str(output / "gd001-playback.prof"))
            overlay = gs["seed_answer_overlay"]
            assert overlay.turning_point_id == "MOMOKO_GD_MONEY"
            assert not renderer.skip_mode and not renderer.auto_mode
            hud = get_debug_hud()
            assert not hud.enabled
            press(pygame.K_F8)
            assert hud.enabled
            assert any(line.startswith("MODEL") for line in hud.lines_for(app))
            pygame.image.save(app.virtual_screen, str(output / "gd001-debug-f8.png"))
            press(pygame.K_F8)
            assert not hud.enabled
            print("GD001_DEMO_F8_DEBUG_OK", flush=True)
            pygame.image.save(app.virtual_screen, str(output / "gd001-input.png"))
            index = gs["current_paragraph"]
            for _ in range(5):
                frame()
            assert gs["current_paragraph"] == index
            assert gs["seed_answer_overlay"] is overlay
            print("GD001_SKIP_STOPS_AT_FREE_INPUT_OK", flush=True)

            pygame.event.post(pygame.event.Event(pygame.TEXTINPUT, text="桃子は借金でお金がない"))
            press(pygame.K_RETURN)
            assert overlay.last_verdict["result"] == "incorrect"
            press(pygame.K_SPACE)
            play_until(lambda: gs.get("seed_answer_overlay") is not None)
            overlay = gs["seed_answer_overlay"]
            print("GD001_INCORRECT_RETURNS_TO_INPUT_OK", flush=True)
            gs["seed_manager"]._preload_thread.join(30)
            assert gs["seed_manager"].model_status() == "ready"
            answer = os.environ.get("MOKISS_PLAYBACK_ANSWER", "旅行のお土産で散財したから余裕がない")
            pygame.event.post(pygame.event.Event(pygame.TEXTINPUT, text=answer))
            press(pygame.K_RETURN)
            assert overlay.last_verdict["result"] == "correct"
            assert gs["seed_answer_overlay"] is None
            assert overlay.last_verdict["reason_codes"][0] in ("semantic_match", "exact_answer")
            press(pygame.K_SPACE)
            play_until(lambda: "ありがとっ" in renderer.current_text)
            pygame.image.save(app.virtual_screen, str(output / "gd001-success.png"))
            print("GD001_REAL_MODEL_AND_SUCCESS_BRANCH_OK", flush=True)
            play_until(lambda: app.current_subsystem is not scene)
            assert app.demo_flow.stage.name == "before_map"
            print("GD001_SKIP_REACHES_NEXT_SCENE_OK", flush=True)
            print("FRAME_SECONDS", "count", len(frames), "max", round(max(frames), 3),
                  "median", round(sorted(frames)[len(frames) // 2], 3), flush=True)
            ordered = sorted(item['ms'] for item in fade_frames)
            cache = gs.get('_character_images')
            report = {
                'fade_frames': len(ordered),
                'fade_frame_ms_median': ordered[len(ordered) // 2],
                'fade_frame_ms_p95': ordered[int((len(ordered) - 1) * 0.95)],
                'fade_frame_ms_max': max(ordered),
                'fade_frame_image_loads': [path for item in fade_frames for path in item['loads']],
                'prepared_character_mib': cache.bytes / (1024 * 1024) if cache else None,
                'native_image_mib': gs['image_manager']._cache_bytes / (1024 * 1024),
            }
            (output / 'fade-frames.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
            print('CHARACTER_FADE_FRAMES', json.dumps(report), flush=True)
            pstats.Stats(profiler).sort_stats("cumulative").print_stats(25)
        finally:
            pygame.image.load = original_load
            app.cleanup()
    after = snapshot()
    changed_paths = [str(path.relative_to(ROOT)) for path in before.keys() | after.keys()
                     if before.get(path) != after.get(path)]
    assert not changed_paths, f"KS or main profile changed during playback: {changed_paths}"
    print("AUTHORED_KS_AND_MAIN_STATE_UNCHANGED", flush=True)


if __name__ == "__main__":
    main()
