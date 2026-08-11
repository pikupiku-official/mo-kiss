"""Home-specific morning sequence, dialogue preload, and handoff."""

from __future__ import annotations

from core.flow.game_flow import MorningDeparture, Navigate, Scene, StartDialogue
from home.morning_sequence import MorningSequence


class MorningFlow:
    """Own every state needed between sleeping and the morning dialogue."""

    DIALOGUE_FILE = "events/HOME_MORNING_DEPARTURE.ks"

    def __init__(self, screen, dialogue_factory=None):
        self.screen = screen
        self.sequence = None
        self.frame_presented = False
        self.preload_attempted = False
        self.preloaded_dialogue = None
        self._dialogue_factory = dialogue_factory or self._build_dialogue

    @property
    def active(self) -> bool:
        return self.sequence is not None

    @property
    def background_key(self) -> str:
        return self.sequence.background_key if self.sequence else "home00"

    def start(self, date_text: str) -> None:
        self.sequence = MorningSequence(date_text)
        self.frame_presented = False
        self.preload_attempted = False
        self.preloaded_dialogue = None

    def handle_events(self, events):
        if not self.sequence:
            return None
        result = self.sequence.handle_events(events)
        if result:
            self.sequence = None
            return MorningDeparture()
        return None

    def update(self) -> None:
        if not self.sequence:
            return
        self.sequence.update()
        if self.frame_presented and not self.preload_attempted:
            self.preload_dialogue()

    def render_overlay(self, screen, content_rect, font, large_font) -> None:
        if not self.sequence:
            return
        self.sequence.render_overlay(screen, content_rect, font, large_font)
        self.frame_presented = True

    def preload_dialogue(self) -> None:
        """Prepare the first dialogue frame while the morning visual is visible."""
        self.preload_attempted = True
        try:
            self.preloaded_dialogue = self._dialogue_factory(
                self.screen,
                self.DIALOGUE_FILE,
            )
            print("[HOME] 朝の一言会話を事前読み込みしました")
        except Exception as exc:
            self.preloaded_dialogue = None
            print(f"[HOME] 朝の一言会話の事前読み込みに失敗しました: {exc}")

    def take_dialogue_request(self) -> StartDialogue:
        """Build the explicit, one-shot no-loading dialogue handoff."""
        dialogue = self.preloaded_dialogue
        self.preloaded_dialogue = None
        return StartDialogue(
            event_file=self.DIALOGUE_FILE,
            completion=Navigate(Scene.MAP),
            display_loading=False,
            preloaded_subsystem=dialogue,
        )

    @staticmethod
    def _build_dialogue(screen, event_file):
        from dialogue.dialogue_subsystem import DialogueSubsystem

        return DialogueSubsystem(screen, screen, event_file)
