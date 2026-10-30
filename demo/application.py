"""The regular window/title/dialogue runtime with an independent event flow."""

from copy import deepcopy
from contextlib import contextmanager
from datetime import date
from pathlib import Path
import tempfile

import pygame

from main import GameApplication
from core.path_utils import get_current_state_dir, get_project_root
from core.services.seed_manager import EMPTY_SEED_STATE, get_seed_manager
from core.services.time_manager import get_time_manager
from core.ui.title_subsystem import TitleSubsystem
from core.ui.loading_screen import show_loading
from core.ui.debug_hud import get_debug_hud
from core.runtime.game_loop import GameLoop
from dialogue.dialogue_subsystem import DialogueSubsystem
from dialogue.event_datetime import EventDateTime
from dialogue.name_manager import get_name_manager
from core.config import DIALOGUE_FPS
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
        self._shortcuts = GameLoop(self, dialogue_type=DialogueSubsystem)

    @contextmanager
    def _loading_transition(self, message):
        # Paint on the real window before constructors preload images/audio.
        show_loading(message, self.window_surface)
        try:
            yield
        finally:
            # Input typed while loading belongs to the outgoing screen. Keep
            # QUIT/window events, but never advance the newly entered scene.
            pygame.event.clear([
                pygame.KEYDOWN, pygame.KEYUP, pygame.TEXTINPUT,
                pygame.TEXTEDITING, pygame.MOUSEBUTTONDOWN,
                pygame.MOUSEBUTTONUP, pygame.MOUSEWHEEL,
            ])

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
        with self._loading_transition("次の画面を読み込み中..."):
            self._enter_stage(stage)

    def _enter_stage(self, stage):
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
            self._prepare_answer_prompt(dialogue, stage)
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

    @staticmethod
    def _prepare_answer_prompt(dialogue, stage):
        """Supply the missing demo prompt without editing reviewed KS prose."""
        turning_point = stage.answer_turning_point
        if not turning_point:
            return
        data = dialogue.game_state["dialogue_data"]
        condition = f"{turning_point}_RESULT==correct"
        branch = next((i for i, item in enumerate(data)
                       if isinstance(item, dict) and item.get("type") == "if_start"
                       and item.get("condition", "").replace(" ", "") == condition), None)
        if branch is None:
            raise ValueError(f"Demo answer branch is missing: {stage.source}: {condition}")
        if not any(isinstance(item, dict) and item.get("type") == "seed_answer"
                   and item.get("turning_point_id") == turning_point for item in data[:branch]):
            data.insert(branch, {"type": "seed_answer", "turning_point_id": turning_point,
                                 "prompt": stage.answer_prompt})
            from dialogue.ir_builder import build_ir_from_normalized
            dialogue.game_state["ir_data"] = build_ir_from_normalized(data)
        dialogue.seed_manager.preload_answer_model()

    def play_pv(self, filename="PV3min.mp4", *, attract=False):
        with self._loading_transition("映像を準備中..."):
            self.switch_to(PVScreen(
                self.screen, filename, self.audio_cache.name, attract=attract,
            ), "demo_pv")

    def return_to_title(self):
        self.hide_option()
        self.current_event_id = None
        self.demo_flow.reset()
        with self._loading_transition("タイトルを読み込み中..."):
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
        self._shortcuts._handle_debug_shortcut(events)
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
        get_debug_hud().render(self.virtual_screen, self)
        self._present_virtual_screen()
        pygame.display.flip()
        self.clock.tick(DIALOGUE_FPS if isinstance(self.current_subsystem, DialogueSubsystem) else 30)

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
