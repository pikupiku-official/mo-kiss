"""Run the real demo scenes offscreen without modifying human-authored KS."""

import hashlib
import os
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
os.environ["QT_QPA_PLATFORM"] = "offscreen"


def snapshot():
    paths = list((ROOT / "data/current_state").glob("*"))
    paths += [ROOT / "events/story_flags.json"]
    paths += list((ROOT / "events").glob("GD*.ks"))
    return {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths if p.is_file()}


def main():
    before = snapshot()
    output = ROOT / "outputs/demo-smoke"
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="demo-smoke-") as profile:
        os.environ["MOKISS_PROFILE_ROOT"] = profile
        Path(profile, "current_state").mkdir()
        # Load the semantic runtime before pygame's decoder DLLs, as in preview.
        import onnxruntime
        import PyQt5
        plugins = Path(PyQt5.__file__).parent / "Qt5/plugins"
        os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = str(plugins / "platforms")
        from PyQt5.QtWidgets import QApplication
        qt_app = QApplication.instance() or QApplication([])
        import pygame
        from core import config
        config.IR_DUMP_JSON = False
        from demo.application import DemoApplication
        from core.services.time_manager import get_time_manager
        from dialogue.name_manager import get_name_manager
        from demo.flow import STAGES

        app = DemoApplication()
        try:
            assert app.initialize()
            app.run_frame()
            pygame.image.save(app.virtual_screen, str(output / "title.png"))
            pygame.event.clear()
            # The exact boundary launches the attract PV, even if PV is absent.
            app.title_activity_at = pygame.time.get_ticks() - 20_000
            app.run_frame()
            assert app.current_mode == "demo_pv" and app.current_subsystem.attract
            pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
            app.run_frame()
            assert app.current_mode == "title" and app.demo_flow.stage is None
            app.run_frame()
            assert app.current_mode == "title"  # cancel input did not start OP
            pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
            app.run_frame()
            assert app.demo_flow.stage.name == "op"
            assert get_name_manager().get_fullname() == "久保田航輝"
            pygame.image.save(app.virtual_screen, str(output / "op.png"))
            # Exercise real constructors/renderers and the completion dispatcher;
            # this is a scene handoff test, not a full prose playback test.
            app._handle_transition("dialogue_ended")
            if not (ROOT / "events/GD001.ks").stat().st_size:
                assert app.demo_flow.stage.name == "before_map"
            else:
                assert app.demo_flow.stage.name == "morning"
                app._handle_transition("dialogue_ended")
            app.current_subsystem.render()
            pygame.image.save(app.virtual_screen, str(output / "choice.png"))
            app._handle_transition("demo_next")
            assert app.current_mode == "demo_map"

            def map_mouse(event_type, point):
                # Native map pixels -> virtual canvas -> real window pixels.
                rect = config.virtual_to_window_rect(pygame.Rect(
                    round(point[0] * 1440 / 640), round(point[1] * 1080 / 480), 1, 1,
                ))
                attrs = {"pos": rect.topleft}
                if event_type == pygame.MOUSEMOTION:
                    attrs.update(rel=(1, 1), buttons=(0, 0, 0))
                else:
                    attrs["button"] = 1
                pygame.event.post(pygame.event.Event(event_type, attrs))
                app.run_frame()

            map_mouse(pygame.MOUSEMOTION, (100, 100))
            assert not app.current_subsystem.hovered
            pygame.image.save(app.virtual_screen, str(output / "map-normal.png"))
            map_mouse(pygame.MOUSEMOTION, (460, 245))
            assert app.current_subsystem.hovered
            pygame.image.save(app.virtual_screen, str(output / "map-hover.png"))
            map_mouse(pygame.MOUSEBUTTONDOWN, (530, 274))
            assert app.current_mode == "demo_map"  # outside the slanted edge
            map_mouse(pygame.MOUSEMOTION, (460, 245))
            map_mouse(pygame.MOUSEBUTTONDOWN, (460, 245))
            assert app.demo_flow.stage.name == "noon"
            assert app.current_event_id == "GD002"
            app._handle_transition("dialogue_ended")
            assert app.demo_flow.stage.name == "evening"
            app._handle_transition("dialogue_ended")
            assert app.current_mode == "demo_home"
            home = app.current_subsystem
            home.render()
            pygame.image.save(app.virtual_screen, str(output / "home.png"))
            assert home._get_choice_renderer().enabled == [True, False, False, False]
            assert get_time_manager().current_period == "夜"
            home._show_submenu_choices(home.BED)
            home.render()
            pygame.image.save(app.virtual_screen, str(output / "bed.png"))
            app._handle_transition(home._activate_choice(0))
            assert app.demo_flow.stage.name == "before_monologue"
            app._handle_transition("demo_next")
            assert app.demo_flow.stage.name == "monologue"
            clock = get_time_manager()
            assert (clock.current_month, clock.current_day, clock.current_period) == (6, 15, "朝")
            app.current_subsystem.render()
            pygame.image.save(app.virtual_screen, str(output / "monologue.png"))
            app._handle_transition("dialogue_ended")
            assert app.demo_flow.stage.name == "free_text"
            assert get_time_manager().current_period == "放課後"
            assert app.current_event_id == "GD006"
            assert app.current_subsystem.game_state["seed_list_overlay"] is None
            app.current_subsystem.render()
            pygame.image.save(app.virtual_screen, str(output / "free-text-scene.png"))
            app._handle_transition("show_option")
            from core.ui.option_overlay import SettingsFaderOverlay
            assert isinstance(app.option_subsystem.overlay, SettingsFaderOverlay)
            app._handle_overlay_result("resume")
            app._handle_transition("dialogue_ended")
            assert app.current_mode == "demo_pv"
            assert app.current_subsystem.path.name == "PV1min.mp4"
            app._handle_transition("demo_title")
            assert app.current_mode == "title"
            for index in (2, 7):
                app.demo_flow.index = index
                app.enter_stage(STAGES[index])
                app._handle_transition("demo_pv")
                assert app.current_subsystem.path.name == "PV3min.mp4"
                app._handle_transition(app.current_subsystem.handle_events([
                    pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE),
                ]))
                assert app.current_mode == "title"
            print("DEMO_RUNTIME_SMOKE_OK")
        finally:
            app.cleanup()
    assert snapshot() == before, "main progress or authored KS changed"
    print("MAIN_STATE_AND_KS_UNCHANGED")


if __name__ == "__main__":
    main()
