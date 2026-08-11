"""Evening home flow: diary, free actions, sleep, and morning departure."""

from __future__ import annotations

from dataclasses import dataclass
import os

import numpy as np
import pygame

from core.path_utils import get_resource_path
from core.runtime.subsystem_base import SubsystemBase
from core.services.time_manager import get_time_manager
from home.morning_flow import MorningFlow


@dataclass
class _ImageTransition:
    frames: tuple[str, ...]
    frame_ms: int
    destination: str
    started_at_ms: int

    def frame_key(self, now_ms: int) -> str:
        index = min(
            max(0, now_ms - self.started_at_ms) // self.frame_ms,
            len(self.frames) - 1,
        )
        return self.frames[int(index)]

    def is_finished(self, now_ms: int) -> bool:
        return now_ms - self.started_at_ms >= len(self.frames) * self.frame_ms


class HomeModule(SubsystemBase):
    """Run the complete home flow within one reusable subsystem."""

    MORNING_DIALOGUE_FILE = MorningFlow.DIALOGUE_FILE
    DIARY_DIALOGUE_FILE = "events/HOME_DIARY.ks"
    # Background command parsing uses underscores as field separators.
    DIARY_BACKGROUND_KEY = "homedesk3"

    MAIN = "main"
    BED = "bed"
    DESK = "desk"
    CORKBOARD = "corkboard"
    PHONE = "phone"
    DIARY = "diary"

    MAIN_CHOICES = (
        ("ベッドに転がる", BED),
        ("机に向かう", DESK),
        ("コルクボードを見る", CORKBOARD),
        ("電話をかける", PHONE),
    )
    SUBMENU_CHOICES = {
        BED: (("寝る", "sleep"), ("戻る", "back")),
        DESK: (("戻る", "back"),),
        CORKBOARD: (("戻る", "back"),),
        PHONE: (("戻る", "back"),),
    }
    ENTRY_FRAMES = {
        BED: ("bed1", "bed2", "bed3"),
        DESK: ("desk1", "desk2", "desk3"),
        CORKBOARD: ("corkboard1", "corkboard2", "corkboard3"),
        PHONE: ("phone1", "phone2", "phone3"),
    }
    FINAL_FRAME = {
        MAIN: "home",
        BED: "bed3",
        DESK: "desk3",
        CORKBOARD: "corkboard3",
        PHONE: "phone3",
        DIARY: "desk3",
    }
    SCENE_FRAME_MS = 150
    PHONE_OPEN_FRAME_MS = 100
    PHONE_CLOSE_FRAME_MS = 50
    PHONE_Y_OFFSETS = {
        "phone1": 760,
        "phone2": 260,
        "phone3": 0,
    }

    def __init__(self, screen: pygame.Surface, clock_ms=None):
        super().__init__(screen)
        self._clock_ms = clock_ms or pygame.time.get_ticks
        self._phase = self.DIARY
        self._transition: _ImageTransition | None = None
        self._diary_dialogue = None
        self._diary_active = False
        self._choice_renderer = None
        self._choice_actions: tuple[str, ...] = ()
        self._images = self._load_home_images()
        self.morning_flow = MorningFlow(screen)

        # Kept as a lightweight compatibility view for older callers/tests.
        self.choices = [
            {"text": text, "action": action} for text, action in self.MAIN_CHOICES
        ]
        self.selected_choice = 0
        self.save_mode = None

    def _load_home_images(self) -> dict[str, pygame.Surface | None]:
        from core.config import VIRTUAL_HEIGHT, VIRTUAL_WIDTH

        paths = {
            "home": get_resource_path("images", os.path.join("UI", "home", "home.png")),
            "bed1": get_resource_path("images", os.path.join("UI", "home", "bed1.png")),
            "bed2": get_resource_path("images", os.path.join("UI", "home", "bed2.png")),
            "bed3": get_resource_path("images", os.path.join("UI", "home", "bed3.png")),
            "desk1": get_resource_path("images", os.path.join("UI", "home", "desk1.png")),
            "desk2": get_resource_path("images", os.path.join("UI", "home", "desk2.png")),
            "desk3": get_resource_path("images", os.path.join("UI", "home", "desk3.png")),
            "corkboard1": get_resource_path("images", os.path.join("UI", "home", "corkboard1.png")),
            "corkboard2": get_resource_path("images", os.path.join("UI", "home", "corkboard2.png")),
            "corkboard3": get_resource_path("images", os.path.join("UI", "home", "corkboard3.png")),
            "phone3": get_resource_path("images", os.path.join("UI", "home", "PHS.png")),
        }
        for index in range(4):
            key = f"home{index:02d}"
            path = get_resource_path("images", os.path.join("BG", f"{key}.jpg"))
            if not os.path.exists(path):
                path = get_resource_path("images", os.path.join("BG", f"{key}.JPG"))
            paths[key] = path
        images = {}
        for key, path in paths.items():
            try:
                image = pygame.image.load(path)
                if key == "phone3":
                    image = self._prepare_phone_overlay(image)
                scaled = self._scale_cover(image, (VIRTUAL_WIDTH, VIRTUAL_HEIGHT))
                images[key] = scaled
            except (OSError, pygame.error) as exc:
                print(f"[HOME] image load failed: {path}: {exc}")
                images[key] = None
        return images

    @staticmethod
    def _prepare_phone_overlay(image: pygame.Surface) -> pygame.Surface:
        """Recover the handset RGB while making its white field transparent."""
        overlay = pygame.Surface(image.get_size(), pygame.SRCALPHA)
        overlay.blit(image, (0, 0))
        rgb = pygame.surfarray.pixels3d(overlay)
        alpha = pygame.surfarray.pixels_alpha(overlay)
        # PHS.png contains black handset pixels below zero alpha. Derive an
        # additional alpha mask from distance to white, then retain whichever
        # alpha value is stronger so authored hand/edge transparency survives.
        distance_from_white = 255 - rgb.min(axis=2).astype(np.int16)
        derived_alpha = np.clip(distance_from_white * 22, 0, 255).astype(np.uint8)
        np.maximum(alpha, derived_alpha, out=alpha)
        del alpha
        del rgb
        return overlay

    @staticmethod
    def _scale_cover(image: pygame.Surface, size: tuple[int, int]) -> pygame.Surface:
        """Scale to 4:3 and center-crop; this also normalizes the taller PHS image."""
        target_w, target_h = size
        scale = max(target_w / image.get_width(), target_h / image.get_height())
        scaled_size = (
            max(1, round(image.get_width() * scale)),
            max(1, round(image.get_height() * scale)),
        )
        scaled = pygame.transform.smoothscale(image, scaled_size)
        x = max(0, (scaled.get_width() - target_w) // 2)
        y = max(0, (scaled.get_height() - target_h) // 2)
        return scaled.subsurface((x, y, target_w, target_h)).copy()

    def on_enter(self):
        """Every genuine return home starts with that evening's diary line."""
        self.morning_flow = MorningFlow(self.screen)
        self._transition = None
        self._phase = self.DIARY
        self._choice_actions = ()
        self._start_diary()

    def _start_diary(self):
        self._finish_diary_dialogue()
        try:
            from dialogue.dialogue_subsystem import DialogueSubsystem

            dialogue = DialogueSubsystem(
                self.screen,
                self.screen,
                self.DIARY_DIALOGUE_FILE,
            )
            desk_path = get_resource_path(
                "images", os.path.join("UI", "home", "desk3.png")
            )
            dialogue.game_state["image_manager"].image_paths.setdefault("bg", {})[
                self.DIARY_BACKGROUND_KEY
            ] = desk_path
            self._diary_dialogue = dialogue
            self._choice_renderer = dialogue.game_state["choice_renderer"]
            self._diary_active = True
            dialogue.on_enter()
        except Exception as exc:
            print(f"[HOME] diary dialogue initialization failed: {exc}")
            self._diary_dialogue = None
            self._diary_active = False
            self._show_main_choices()

    def _finish_diary_dialogue(self):
        if self._diary_dialogue is not None and self._diary_active:
            self._diary_dialogue.cleanup()
        self._diary_active = False

    def _get_choice_renderer(self):
        if self._choice_renderer is None:
            from dialogue.choice_renderer import ChoiceRenderer

            self._choice_renderer = ChoiceRenderer(self.screen)
        return self._choice_renderer

    def _show_choices(self, choices: tuple[tuple[str, str], ...]):
        renderer = self._get_choice_renderer()
        renderer.show_choices([text for text, _ in choices])
        renderer.hovered_choice = 0 if choices else -1
        self._choice_actions = tuple(action for _, action in choices)
        self.selected_choice = renderer.hovered_choice

    def _show_main_choices(self):
        self._phase = self.MAIN
        self._transition = None
        self._show_choices(self.MAIN_CHOICES)

    def _show_submenu_choices(self, phase: str):
        self._phase = phase
        self._transition = None
        self._show_choices(self.SUBMENU_CHOICES[phase])

    def handle_events(self, events=None):
        if events is None:
            events = pygame.event.get()

        # Preserve the small __new__-constructed compatibility fixture used by
        # older morning-flow tests while production instances use the new flow.
        if "_phase" not in self.__dict__:
            return self._handle_legacy_sleep_fixture(events)

        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return "show_option"

        if self.morning_flow.active:
            return self.morning_flow.handle_events(events)

        if self._phase == self.DIARY and self._diary_active:
            for event in events:
                try:
                    pygame.event.post(event)
                except pygame.error:
                    pass
            result = self._diary_dialogue.handle_events()
            if (
                result == "dialogue_ended"
                or self._diary_dialogue.game_state.get("ks_finished", False)
            ):
                self._finish_diary_dialogue()
                self._show_main_choices()
            return None

        # Construction-only callers have not entered the scene yet, so there
        # is no menu to operate and no reason to initialize Qt-backed fonts.
        if self._phase == self.DIARY:
            return None

        if self._transition is not None:
            return None

        renderer = self._get_choice_renderer()
        for event in events:
            if event.type == pygame.MOUSEMOTION:
                renderer.handle_mouse_motion(event.pos)
                self.selected_choice = renderer.hovered_choice
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                index = renderer.handle_mouse_click(event.pos)
                if index >= 0:
                    return self._activate_choice(index)
            elif event.type == pygame.KEYDOWN:
                if event.key in (
                    pygame.K_UP,
                    pygame.K_DOWN,
                    pygame.K_LEFT,
                    pygame.K_RIGHT,
                ):
                    self._move_choice(event.key)
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    if renderer.hovered_choice >= 0:
                        return self._activate_choice(renderer.hovered_choice)
        return None

    def _move_choice(self, key: int):
        renderer = self._get_choice_renderer()
        rects = renderer.choice_rects
        if not rects:
            return
        current = renderer.hovered_choice if renderer.hovered_choice >= 0 else 0
        direction = {
            pygame.K_LEFT: (-1, 0),
            pygame.K_RIGHT: (1, 0),
            pygame.K_UP: (0, -1),
            pygame.K_DOWN: (0, 1),
        }[key]
        cx, cy = rects[current].center
        candidates = []
        for index, rect in enumerate(rects):
            if index == current:
                continue
            dx, dy = rect.centerx - cx, rect.centery - cy
            projection = dx * direction[0] + dy * direction[1]
            if projection > 0:
                cross = abs(dx * direction[1] - dy * direction[0])
                candidates.append((cross, projection, index))
        if candidates:
            renderer.hovered_choice = min(candidates)[2]
        else:
            step = 1 if key in (pygame.K_RIGHT, pygame.K_DOWN) else -1
            renderer.hovered_choice = (current + step) % len(rects)
        self.selected_choice = renderer.hovered_choice

    def _activate_choice(self, index: int):
        if index < 0 or index >= len(self._choice_actions):
            return None
        action = self._choice_actions[index]
        if self._phase == self.MAIN:
            self._start_entry_transition(action)
        elif action == "back":
            self._start_return_transition(self._phase)
        elif action == "sleep":
            self._start_morning()
        return None

    def _hide_choices(self):
        if self._choice_renderer is not None:
            self._choice_renderer.hide_choices()
        self._choice_actions = ()

    def _start_entry_transition(self, destination: str):
        self._hide_choices()
        frame_ms = (
            self.PHONE_OPEN_FRAME_MS if destination == self.PHONE else self.SCENE_FRAME_MS
        )
        self._transition = _ImageTransition(
            self.ENTRY_FRAMES[destination],
            frame_ms,
            destination,
            self._clock_ms(),
        )

    def _start_return_transition(self, origin: str):
        self._hide_choices()
        frames = tuple(reversed(self.ENTRY_FRAMES[origin])) + ("home",)
        frame_ms = (
            self.PHONE_CLOSE_FRAME_MS if origin == self.PHONE else self.SCENE_FRAME_MS
        )
        self._transition = _ImageTransition(
            frames,
            frame_ms,
            self.MAIN,
            self._clock_ms(),
        )

    def _start_morning(self):
        self._hide_choices()
        time_manager = get_time_manager()
        time_manager.set_to_morning()
        self.morning_flow.start(time_manager.get_date_string())
        print("[HOME] sleep selected; morning sequence started")

    def _handle_legacy_sleep_fixture(self, events):
        if self._ensure_morning_flow().active:
            return None
        for event in events:
            if event.type != pygame.KEYDOWN or event.key not in (
                pygame.K_RETURN,
                pygame.K_KP_ENTER,
            ):
                continue
            action = self.choices[self.selected_choice]["action"]
            if action == "sleep":
                time_manager = get_time_manager()
                time_manager.set_to_morning()
                self._ensure_morning_flow().start(time_manager.get_date_string())
        return None

    def update(self):
        if self._phase == self.DIARY and self._diary_active:
            self._diary_dialogue.update()

        if self._transition is not None and self._transition.is_finished(self._clock_ms()):
            destination = self._transition.destination
            if destination == self.MAIN:
                self._show_main_choices()
            else:
                self._show_submenu_choices(destination)

        self.morning_flow.update()

    def render(self):
        if self._phase == self.DIARY and self._diary_active:
            self._diary_dialogue.render()
            return

        self.screen.fill((0, 0, 0))
        key = self._current_frame_key()
        if key in self.PHONE_Y_OFFSETS:
            home_image = self._images.get("home")
            if home_image is not None:
                self.screen.blit(home_image, (0, 0))
            phone_image = self._images.get("phone3")
            if phone_image is not None:
                self.screen.blit(phone_image, (0, self.PHONE_Y_OFFSETS[key]))
        else:
            image = self._images.get(key)
            if image is not None:
                self.screen.blit(image, (0, 0))

        if self.morning_flow.active:
            from core.config import VIRTUAL_HEIGHT, VIRTUAL_WIDTH

            self.morning_flow.render_overlay(
                self.screen,
                pygame.Rect(0, 0, VIRTUAL_WIDTH, VIRTUAL_HEIGHT),
                self._get_diary_font("text"),
                self._get_diary_font("name"),
            )
        elif self._transition is None and self._choice_renderer is not None:
            self._choice_renderer.render()

    def _current_frame_key(self) -> str:
        if self.morning_flow.active:
            return self.morning_flow.background_key
        if self._transition is not None:
            return self._transition.frame_key(self._clock_ms())
        return self.FINAL_FRAME.get(self._phase, "home")

    def _get_diary_font(self, font_key: str):
        if self._diary_dialogue is not None:
            renderer = self._diary_dialogue.game_state.get("text_renderer")
            if renderer is not None:
                font = renderer.fonts.get(font_key)
                if font is not None and hasattr(font, "render"):
                    return font
        return pygame.font.Font(None, 48 if font_key == "text" else 64)

    def cleanup(self):
        self._finish_diary_dialogue()

    def _ensure_morning_flow(self):
        flow = self.__dict__.get("morning_flow")
        if flow is None:
            flow = MorningFlow(getattr(self, "screen", None))
            self.__dict__["morning_flow"] = flow
        return flow

    # Compatibility accessors retained for the established morning handoff.
    @property
    def morning_sequence(self):
        return self._ensure_morning_flow().sequence

    @morning_sequence.setter
    def morning_sequence(self, value):
        self._ensure_morning_flow().sequence = value

    @property
    def _morning_frame_presented(self):
        return self._ensure_morning_flow().frame_presented

    @_morning_frame_presented.setter
    def _morning_frame_presented(self, value):
        self._ensure_morning_flow().frame_presented = value

    @property
    def _morning_dialogue_preload_attempted(self):
        return self._ensure_morning_flow().preload_attempted

    @_morning_dialogue_preload_attempted.setter
    def _morning_dialogue_preload_attempted(self, value):
        self._ensure_morning_flow().preload_attempted = value

    @property
    def _preloaded_morning_dialogue(self):
        return self._ensure_morning_flow().preloaded_dialogue

    @_preloaded_morning_dialogue.setter
    def _preloaded_morning_dialogue(self, value):
        self._ensure_morning_flow().preloaded_dialogue = value

    def _preload_morning_dialogue(self):
        self._ensure_morning_flow().preload_dialogue()

    def take_preloaded_morning_dialogue(self):
        return self._ensure_morning_flow().take_dialogue_request().preloaded_subsystem
