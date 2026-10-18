"""The regular window/title/dialogue runtime with an independent event flow."""

from copy import deepcopy
from datetime import date
from pathlib import Path
import tempfile

import pygame

from main import GameApplication
from core.path_utils import get_current_state_dir, get_project_root
from core.services.seed_manager import EMPTY_SEED_STATE, get_seed_manager
from core.services.time_manager import get_time_manager
from core.ui.title_subsystem import TitleSubsystem
from dialogue.dialogue_subsystem import DialogueSubsystem
from dialogue.event_datetime import EventDateTime
from dialogue.name_manager import get_name_manager
from demo.flow import DemoFlow, TITLE_IDLE_MS
from demo.GDhome import GDHome
from demo.GDmap import GDMap
from demo.movie import PVScreen
from demo.screens import ChoiceScreen, is_activity


class DemoApplication(GameApplication):
    def __init__(self):
        super().__init__()
        self.demo_flow = DemoFlow()
        self.audio_cache = tempfile.TemporaryDirectory(prefix="mokiss-pv-")
        self.title_activity_at = 0

    def initialize(self):
        if not super().initialize():
            return False
        self.title_activity_at = pygame.time.get_ticks()
        return True

    def start_demo(self):
        # A visitor always starts fresh, even after an earlier visitor finished.
        state_dir = Path(get_current_state_dir())
        state_dir.mkdir(parents=True, exist_ok=True)
        get_name_manager().set_names("久保田", "航輝")
        seeds = get_seed_manager()
        seeds.state = deepcopy(EMPTY_SEED_STATE)
        seeds._pending_by_event.clear()
        seeds.save()
        (state_dir / "story_flags.json").write_text("{}", encoding="utf-8")
        self.enter_stage(self.demo_flow.start())

    def enter_stage(self, stage):
        if stage is None:
            self.return_to_title()
            return
        day = date.fromisoformat(stage.date)
        time = get_time_manager()
        time.current_year, time.current_month, time.current_day = day.year, day.month, day.day
        time.current_weekday, time.current_period = day.weekday(), stage.period
        time.save_time_state()
        if stage.kind == "dialogue":
            path = Path(get_project_root(), "events", stage.source)
            if not path.is_file():
                self.switch_to(ChoiceScreen(
                    self.screen, ("タイトルに戻る",), ("demo_title",),
                    f"原稿が見つかりません：{stage.source}",
                ), "demo_error")
                return
            # An authored but empty KS is an empty stage, not the engine's
            # default fallback dialogue. Do not add placeholder prose to KS.
            content = path.read_text(encoding="utf-8-sig")
            if not any(line.strip() and not line.lstrip().startswith((";", "*"))
                       for line in content.splitlines()):
                self.enter_stage(self.demo_flow.advance())
                return
            dialogue = DialogueSubsystem(self.screen, self.virtual_screen, str(path))
            dialogue.game_state["seed_list_overlay"] = None
            dialogue.game_state["text_renderer"].set_event_datetime(
                EventDateTime(day.year, day.month, day.day, stage.period)
            )
            self.current_event_id = path.stem
            self.switch_to(dialogue, "dialogue")
        elif stage.kind == "choice":
            destination = "MAPに進む" if stage.name == "before_map" else "モノローグに進む"
            self.switch_to(ChoiceScreen(
                self.screen, (destination, "3分の映像を見る"),
                ("demo_next", "demo_pv"), "このまま体験を続けますか？",
            ), "demo_choice")
        elif stage.kind == "map":
            self.switch_to(GDMap(self.screen), "demo_map")
        elif stage.kind == "home":
            self.switch_to(GDHome(self.screen), "demo_home")
        elif stage.kind == "movie":
            self.play_pv(stage.source)

    def play_pv(self, filename="PV3min.mp4", *, attract=False):
        self.switch_to(PVScreen(
            self.screen, filename, self.audio_cache.name, attract=attract,
        ), "demo_pv")

    def return_to_title(self):
        self.hide_option()
        self.current_event_id = None
        self.demo_flow.reset()
        self.switch_to(TitleSubsystem(self.screen), "title")
        self.title_activity_at = pygame.time.get_ticks()

    def _handle_transition(self, result):
        if result == "quit":
            self.running = False
        elif result in ("show_option", "show_settings"):
            self.show_settings()
        elif result == "go_to_menu" and self.current_mode == "title":
            self.start_demo()
        elif result in ("dialogue_ended", "demo_next"):
            self.enter_stage(self.demo_flow.advance())
        elif result == "demo_pv":
            self.play_pv()
        elif result == "demo_title":
            self.return_to_title()

    def show_option(self):
        self.show_settings()

    def _handle_overlay_result(self, result):
        value = getattr(result, "value", result)
        if value == "quit":
            self.running = False
        else:
            self.hide_option()
            self.title_activity_at = pygame.time.get_ticks()

    def run_frame(self):
        # WindowController consumes F11; retain activity before normalization
        # so even that input cancels the attract PV and resets the idle timer.
        raw_events = pygame.event.get()
        activity = any(is_activity(e) for e in raw_events)
        self._queue_events_for_dialogue(raw_events)
        events = self._gather_normalized_events()
        if any(e.type == pygame.QUIT for e in events):
            self.running = False
            return
        if self.option_subsystem is not None:
            result = self.option_subsystem.handle_events(events)
            if result:
                self._handle_overlay_result(result)
        else:
            scene = self.current_subsystem
            if self.current_mode == "title":
                if activity:
                    self.title_activity_at = pygame.time.get_ticks()
                # Escape exposes settings without entering a visitor session.
                if any(e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE for e in events):
                    self.show_settings()
                    result = None
                else:
                    result = scene.handle_events(events)
                if not result and not self.option_subsystem and (
                    pygame.time.get_ticks() - self.title_activity_at >= TITLE_IDLE_MS
                ):
                    self.play_pv(attract=True)
            elif isinstance(scene, PVScreen) and scene.attract and activity:
                result = "demo_title"
            elif isinstance(scene, DialogueSubsystem):
                self._queue_events_for_dialogue(events)
                result = scene.handle_events()
            else:
                result = scene.handle_events(events)
            if result:
                self._handle_transition(result)
            if self.running and self.option_subsystem is None:
                self.current_subsystem.update()
        self.current_subsystem.render()
        if self.option_subsystem is not None:
            self.option_subsystem.render_overlay()
        self._present_virtual_screen()
        pygame.display.flip()
        self.clock.tick(30)

    def run(self):
        try:
            if not self.initialize():
                return False
            while self.running:
                self.run_frame()
            return True
        finally:
            self.cleanup()

    def cleanup(self):
        # The regular cleanup resets the main save state; never call it here.
        if self.current_subsystem is not None:
            self.current_subsystem.cleanup()
        self.audio_cache.cleanup()
        pygame.quit()
