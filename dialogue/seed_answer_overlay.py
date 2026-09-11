"""Dialogue-native free-text input used by seed turning points."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

import pygame

from core.config import SEED_INPUT_CONFIG, TEXT_COLOR, virtual_to_window_rect
from core.ui.text_edit import TextEditBuffer


class SeedAnswerOverlay:
    """Edit an answer directly in the ordinary three-line dialogue grid."""

    MAX_LENGTH = SEED_INPUT_CONFIG["max_length"]

    def __init__(
        self,
        screen,
        turning_point_id,
        seed_manager,
        text_renderer,
        prompt="",
        initial_text="",
    ):
        self.screen = screen
        self.turning_point_id = turning_point_id
        self.seed_manager = seed_manager
        self.text_renderer = text_renderer
        definition = seed_manager.turning_points.get(turning_point_id, {})
        self.prompt = str(prompt or definition.get("title", "推理を入力する"))
        self.editor = TextEditBuffer(
            initial_text,
            max_length=SEED_INPUT_CONFIG["max_length"],
        )
        self.cursor_visible = True
        self.last_blink = pygame.time.get_ticks()
        self.suspended = False
        self.fallback_armed = False
        self.last_verdict = None
        self._changed_at = pygame.time.get_ticks()
        self._diagnostic_text = None
        self._diagnostic_future = None
        self._diagnostic_future_text = None
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="seed-score")
        self._start_text_input()

    @property
    def text(self):
        return self.editor.text

    @text.setter
    def text(self, value):
        self.editor.set_text(value)

    @property
    def composition(self):
        return self.editor.composition

    @composition.setter
    def composition(self, value):
        self.editor.composition = str(value or "")

    @property
    def is_composing(self):
        return self.editor.is_composing

    def _start_text_input(self):
        try:
            pygame.key.start_text_input()
            self.update_ime_rect()
        except pygame.error:
            pass

    def suspend(self):
        self.suspended = True
        self.editor.clear_composition()
        try:
            pygame.key.stop_text_input()
        except pygame.error:
            pass

    def resume(self):
        self.suspended = False
        self.editor.set_cursor(len(self.editor.text))
        self._start_text_input()

    def close(self):
        self.suspend()
        self._executor.shutdown(wait=False, cancel_futures=True)

    def arm_model_fallback(self):
        self.fallback_armed = True

    @staticmethod
    def fallback_verdict():
        return {
            "result": "correct",
            "confidence": 0.0,
            "judge_version": "model-unavailable-fallback-v1",
            "reason_codes": ("model_unavailable_fallback",),
        }

    def show_judge_feedback(self, result, message):
        """Compatibility hook for the standalone developer launcher."""
        self.last_verdict = {
            "result": str(result),
            "reason_codes": (str(message),),
        }

    def handle_event(self, event):
        if self.suspended:
            return None
        if event.type == pygame.KEYDOWN and not self.is_composing:
            mod = int(getattr(event, "mod", 0) or 0)
            selecting = bool(mod & pygame.KMOD_SHIFT)
            columns = SEED_INPUT_CONFIG["chars_per_line"]
            if event.key == pygame.K_UP:
                self.editor.move_vertical(columns, -1, selecting=selecting)
                self._reset_blink()
                return None
            if event.key == pygame.K_DOWN:
                self.editor.move_vertical(columns, 1, selecting=selecting)
                self._reset_blink()
                return None
            if event.key in (pygame.K_HOME, pygame.K_END) and not (
                mod & (pygame.KMOD_CTRL | pygame.KMOD_GUI)
            ):
                line_start = (self.editor.cursor // columns) * columns
                target = (
                    line_start
                    if event.key == pygame.K_HOME
                    else min(len(self.text), line_start + columns)
                )
                self.editor.set_cursor(target, selecting=selecting)
                self._reset_blink()
                return None

        result = self.editor.handle_event(event, enforce_limit=True)
        if result == "submit":
            return self._answer_if_ready()
        if result in ("changed", "composition", "selection"):
            self._reset_blink()
        if result == "changed":
            self._changed_at = pygame.time.get_ticks()
            self._diagnostic_text = None
            self.last_verdict = None
        return None

    def _reset_blink(self):
        self.cursor_visible = True
        self.last_blink = pygame.time.get_ticks()

    def _answer_if_ready(self):
        answer = self.text.strip()
        return answer if answer and not self.is_composing else None

    def update(self, debug_enabled=False):
        if self._diagnostic_future is not None and self._diagnostic_future.done():
            try:
                verdict = self._diagnostic_future.result()
            except Exception as exc:
                verdict = {
                    "result": "error",
                    "reason_codes": ("debug_judge_error",),
                    "error_detail": str(exc),
                }
            if self._diagnostic_future_text == self.text:
                self.last_verdict = verdict
                self._diagnostic_text = self.text
            self._diagnostic_future = None
            self._diagnostic_future_text = None

        if not debug_enabled or self.suspended or self.is_composing or not self.text.strip():
            return
        if self._diagnostic_future is not None or self._diagnostic_text == self.text:
            return
        if pygame.time.get_ticks() - self._changed_at < SEED_INPUT_CONFIG["debug_debounce_ms"]:
            return
        self._diagnostic_future_text = self.text
        self._diagnostic_future = self._executor.submit(
            self.seed_manager.judge_answer,
            self.turning_point_id,
            self.text,
        )

    def debug_lines(self):
        verdict = self.last_verdict or {}
        reason = ",".join(verdict.get("reason_codes", ())) or "-"

        def score(name):
            value = verdict.get(name)
            return f"{value:.4f}" if isinstance(value, (int, float)) else "-"

        return [
            "MODEL          "
            f"{self.seed_manager.model_status_for_turning_point(self.turning_point_id)}",
            f"RESULT         {verdict.get('result', '-')}",
            f"POS            {score('semantic_score')}",
            f"NEG            {score('hard_negative_score')}",
            f"MARGIN         {score('semantic_margin')}",
            f"REASON         {reason}",
        ]

    def _visual_cells(self):
        cells = []
        start, end = self.editor.selection
        replacing_selection = bool(self.composition and start != end)
        insert_at = start if replacing_selection else self.editor.cursor
        resume_at = end if replacing_selection else self.editor.cursor
        for index, char in enumerate(self.text[:insert_at]):
            kind = "text" if replacing_selection else (
                "selected" if start <= index < end else "text"
            )
            cells.append((char, kind, index))
        for index, char in enumerate(self.composition):
            active = (
                self.editor.composition_start
                <= index
                < self.editor.composition_start + self.editor.composition_length
            )
            cells.append((char, "composition_active" if active else "composition", None))
        for index in range(resume_at, len(self.text)):
            cells.append(
                (
                    self.text[index],
                    "text" if replacing_selection else (
                        "selected" if start <= index < end else "text"
                    ),
                    index,
                )
            )
        return cells

    def _visual_caret_index(self):
        start, end = self.editor.selection
        insert_at = start if self.composition and start != end else self.editor.cursor
        return insert_at + len(self.composition)

    def _viewport(self):
        columns = SEED_INPUT_CONFIG["chars_per_line"]
        rows = SEED_INPUT_CONFIG["input_lines"]
        cells = self._visual_cells()
        caret_index = self._visual_caret_index()
        caret_line = caret_index // columns
        first_line = max(0, caret_line - rows + 1)
        first_index = first_line * columns
        return cells[first_index : first_index + columns * rows], first_index, caret_index

    def _caret_virtual_rect(self):
        columns = SEED_INPUT_CONFIG["chars_per_line"]
        _, first_index, caret_index = self._viewport()
        relative = max(0, caret_index - first_index)
        line, column = divmod(relative, columns)
        x = self.text_renderer.text_start_x + column * self.text_renderer.text_grid_width()
        y = (
            self.text_renderer.text_start_y
            + (SEED_INPUT_CONFIG["prompt_lines"] + line) * self.text_renderer.text_line_height
        )
        return pygame.Rect(x, y + self.text_renderer.pygame_fonts["text"].get_height(), 2, 2)

    def update_ime_rect(self):
        try:
            pygame.key.set_text_input_rect(virtual_to_window_rect(self._caret_virtual_rect()))
        except pygame.error:
            pass

    def render(self):
        if self.suspended:
            return
        now = pygame.time.get_ticks()
        if now - self.last_blink >= SEED_INPUT_CONFIG["cursor_blink_ms"]:
            self.cursor_visible = not self.cursor_visible
            self.last_blink = now
        self.update_ime_rect()

        renderer = self.text_renderer
        name = renderer.name_manager.substitute_variables("{苗字}")
        name_surface = renderer._render_name_with_grid_system(name, TEXT_COLOR)
        self.screen.blit(
            name_surface,
            (int(renderer.name_start_x), int(renderer.name_start_y)),
        )
        prompt_surface = renderer._render_stable_text_line(self.prompt, TEXT_COLOR)
        self.screen.blit(
            prompt_surface,
            (int(renderer.text_start_x), int(renderer.text_start_y) - renderer.ruby_h),
        )
        self._render_input_cells()

    def _render_input_cells(self):
        renderer = self.text_renderer
        cells, first_index, caret_index = self._viewport()
        columns = SEED_INPUT_CONFIG["chars_per_line"]
        grid_width = renderer.text_grid_width()
        font_height = renderer.pygame_fonts["text"].get_height()
        base_y = renderer.text_start_y + renderer.text_line_height
        underline_width = SEED_INPUT_CONFIG["composition_underline_width"]

        for relative, (char, kind, _) in enumerate(cells):
            line, column = divmod(relative, columns)
            x = renderer.text_start_x + column * grid_width
            y = base_y + line * renderer.text_line_height
            selected = kind in ("selected", "composition_active")
            if selected:
                pygame.draw.rect(
                    self.screen,
                    TEXT_COLOR,
                    pygame.Rect(x, y, grid_width - 2, font_height),
                )
            char_color = (10, 14, 20) if selected else TEXT_COLOR
            glyph = renderer._render_text_with_effects(
                renderer.pygame_fonts["text"], char, char_color
            )
            self.screen.blit(glyph, (x, y))
            if kind.startswith("composition"):
                pygame.draw.line(
                    self.screen,
                    TEXT_COLOR,
                    (x, y + font_height - 1),
                    (x + grid_width - 3, y + font_height - 1),
                    underline_width,
                )

        if self.cursor_visible:
            relative = max(0, caret_index - first_index)
            line, column = divmod(relative, columns)
            x = renderer.text_start_x + column * grid_width
            y = base_y + line * renderer.text_line_height
            caret = pygame.Rect(x, y, grid_width - 2, font_height)
            pygame.draw.rect(self.screen, TEXT_COLOR, caret)
            if relative < len(cells):
                char = cells[relative][0]
                glyph = renderer._render_text_with_effects(
                    renderer.pygame_fonts["text"], char, (10, 14, 20)
                )
                self.screen.blit(glyph, (x, y))
