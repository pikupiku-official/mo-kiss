"""Typed application flow requests and their central dispatcher."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from core.flow.event_progress import EventProgress
from core.services.save_manager import get_save_manager
from core.services.time_manager import get_time_manager


class Scene(str, Enum):
    MAP = "map"
    MENU = "menu"
    HOME = "home"
    LOAD = "load"


@dataclass(frozen=True)
class Navigate:
    scene: Scene


@dataclass(frozen=True)
class StartDialogue:
    event_file: str
    completion: Any = None
    display_loading: bool = True
    preloaded_subsystem: Any = None


@dataclass(frozen=True)
class ShowOption:
    pass


@dataclass(frozen=True)
class ShowSettings:
    pass


@dataclass(frozen=True)
class DialogueEnded:
    pass


@dataclass(frozen=True)
class ContinueGame:
    pass


@dataclass(frozen=True)
class MorningDeparture:
    pass


@dataclass(frozen=True)
class QuitApplication:
    pass


FlowRequest = (
    Navigate
    | StartDialogue
    | ShowOption
    | ShowSettings
    | DialogueEnded
    | ContinueGame
    | MorningDeparture
    | QuitApplication
)


def normalize_flow_request(result) -> FlowRequest | None:
    """Convert legacy subsystem strings into typed flow requests."""
    if result is None or isinstance(
        result,
        (
            Navigate,
            StartDialogue,
            ShowOption,
            ShowSettings,
            DialogueEnded,
            ContinueGame,
            MorningDeparture,
            QuitApplication,
        ),
    ):
        return result

    if not isinstance(result, str):
        raise TypeError(f"Unsupported flow result: {result!r}")

    aliases = {
        "go_to_map": Navigate(Scene.MAP),
        "go_to_menu": Navigate(Scene.MENU),
        "back_to_menu": Navigate(Scene.MENU),
        "go_to_main_menu": Navigate(Scene.MENU),
        "go_to_home": Navigate(Scene.HOME),
        "go_to_load": Navigate(Scene.LOAD),
        "skip_to_home": Navigate(Scene.HOME),
        "show_option": ShowOption(),
        "show_settings": ShowSettings(),
        "dialogue_ended": DialogueEnded(),
        "launch_morning_departure": MorningDeparture(),
        "new_game": StartDialogue("events/E001.ks"),
        "dialogue_test": StartDialogue("events/E004.ks"),
        "continue_game": ContinueGame(),
        "quit": QuitApplication(),
        # FieldMap already applies the time change; the shell only stays in place.
        "skip_time": None,
    }
    if result in aliases:
        return aliases[result]
    if result.startswith("launch_event:"):
        return StartDialogue(result.split(":", 1)[1])
    if result.startswith("start_event:"):
        event_id = result.split(":", 1)[1]
        return StartDialogue(f"events/{event_id}.ks")
    raise ValueError(f"Unknown flow result: {result}")


class GameFlowController:
    """Execute typed flow requests against the application shell."""

    def __init__(
        self,
        application,
        event_progress=None,
        time_manager_getter=get_time_manager,
        save_manager_getter=get_save_manager,
    ):
        self.application = application
        self.event_progress = event_progress or EventProgress(
            time_manager_getter=time_manager_getter
        )
        self._time_manager_getter = time_manager_getter
        self._save_manager_getter = save_manager_getter

    def handle(self, result) -> None:
        request = normalize_flow_request(result)
        if request is None:
            return

        if isinstance(request, Navigate):
            self._navigate(request.scene)
        elif isinstance(request, ShowOption):
            self.application.show_option()
        elif isinstance(request, ShowSettings):
            self.application.show_settings()
        elif isinstance(request, StartDialogue):
            if (
                request.completion is None
                and request.display_loading
                and request.preloaded_subsystem is None
            ):
                # Keep specialized application players free to override dialogue startup.
                self.application.switch_to_dialogue(request.event_file)
            else:
                self.application.start_dialogue(request)
        elif isinstance(request, DialogueEnded):
            self._complete_dialogue()
        elif isinstance(request, MorningDeparture):
            self.application.start_morning_dialogue()
        elif isinstance(request, ContinueGame):
            self.resume_loaded_game()
        elif isinstance(request, QuitApplication):
            self.application.running = False

    def handle_option_action(self, action) -> None:
        action_value = getattr(action, "value", action)
        if action_value == "resume":
            self.application.hide_option()
        elif action_value == "save":
            self.application.show_slot_screen("save")
        elif action_value == "load":
            self.application.show_slot_screen("load")
        elif action_value == "return_to_morning":
            time_manager = self._time_manager_getter()
            time_manager.current_period = time_manager.time_periods[0]
            time_manager.save_time_state()
            self.application.hide_option()
            self.application.reload_game_systems()
            self._navigate(Scene.MAP)
        elif action_value == "go_to_menu":
            self.application.hide_option()
            self._navigate(Scene.MENU)
        elif action_value == "quit":
            self.application.hide_option()
            self.handle(QuitApplication())

    def resume_loaded_game(self) -> None:
        if hasattr(self.application, "resume_loaded_state"):
            self.application.resume_loaded_state()
            return
        self.application.reload_game_systems()
        if self._time_manager_getter().is_night():
            self._navigate(Scene.HOME)
        else:
            self._navigate(Scene.MAP)

    def _complete_dialogue(self) -> None:
        print("💬 KSファイル終了 - 遷移判定開始")
        completion = self.application.dialogue_completion_result
        self.application.dialogue_completion_result = None
        if completion is not None:
            print(f"💬 指定された会話終了ルートへ遷移: {completion}")
            self.application.current_event_id = None
            self.handle(completion)
            return

        event_id = self.application.current_event_id
        decision = self.event_progress.complete_dialogue(event_id)
        self.application.current_event_id = None
        self._navigate(Scene(decision.next_mode))

    def _navigate(self, scene: Scene) -> None:
        if scene is Scene.MAP:
            self.application.switch_to_map()
        elif scene is Scene.MENU:
            self.application.switch_to_menu()
        elif scene is Scene.HOME:
            self.application.switch_to_home()
        elif scene is Scene.LOAD:
            self.application.switch_to_load()
