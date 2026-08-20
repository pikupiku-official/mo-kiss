"""Diary-style free-text prompt used by seed turning points."""

from __future__ import annotations

import pygame


class SeedAnswerOverlay:
    """Collect one IME-capable answer while showing the acquired seed tree."""

    MAX_LENGTH = 120

    def __init__(self, screen, turning_point_id, seed_manager, text_renderer):
        self.screen = screen
        self.turning_point_id = turning_point_id
        self.seed_manager = seed_manager
        self.text_renderer = text_renderer
        self.text = ""
        self.composition = ""
        self.feedback_text = ""
        self.feedback_color = (235, 200, 105)
        width, height = screen.get_size()
        self.panel_rect = pygame.Rect(120, 90, width - 240, height - 180)
        self.input_rect = pygame.Rect(
            self.panel_rect.x + 70,
            self.panel_rect.bottom - 150,
            self.panel_rect.width - 140,
            70,
        )
        self.submit_rect = pygame.Rect(
            self.panel_rect.right - 260,
            self.panel_rect.bottom - 65,
            190,
            44,
        )
        try:
            pygame.key.start_text_input()
        except pygame.error:
            pass

    def close(self):
        try:
            pygame.key.stop_text_input()
        except pygame.error:
            pass

    def handle_event(self, event):
        if event.type == pygame.TEXTINPUT:
            self._clear_feedback()
            remaining = self.MAX_LENGTH - len(self.text)
            self.text += event.text[:remaining]
            self.composition = ""
        elif event.type == pygame.TEXTEDITING:
            self.composition = event.text
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE and not self.composition:
                self._clear_feedback()
                self.text = self.text[:-1]
            elif (
                event.key in (pygame.K_RETURN, pygame.K_KP_ENTER)
                and event.mod & pygame.KMOD_CTRL
            ):
                return self._answer_if_ready()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.submit_rect.collidepoint(event.pos):
                return self._answer_if_ready()
        return None

    def show_judge_feedback(self, result, message):
        self.feedback_text = str(message)
        self.feedback_color = {
            "correct": (125, 225, 150),
            "borderline": (235, 200, 105),
            "incorrect": (235, 125, 125),
            "error": (235, 125, 125),
        }.get(result, (235, 200, 105))

    def _clear_feedback(self):
        self.feedback_text = ""

    def _answer_if_ready(self):
        answer = self.text.strip()
        return answer if answer and not self.composition else None

    def render(self):
        shade = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 175))
        self.screen.blit(shade, (0, 0))
        pygame.draw.rect(self.screen, (32, 39, 51), self.panel_rect, border_radius=12)
        pygame.draw.rect(
            self.screen, (115, 198, 225), self.panel_rect, 3, border_radius=12
        )

        title_font = self.text_renderer.pygame_fonts["name"]
        body_font = self.text_renderer.pygame_fonts["text"]
        definition = self.seed_manager.turning_points.get(self.turning_point_id, {})
        self._blit(title_font, definition.get("title", "推理"), (190, 130), (235, 242, 245))
        self._blit(body_font, "取得したタネ", (190, 205), (115, 198, 225))

        y = 270
        entries = self.seed_manager.journal_entries(self.turning_point_id)
        acquired_ids = {entry["id"] for entry in entries}
        for entry in entries:
            depth = self._depth(entry, acquired_ids)
            prefix = "└ " if depth else "● "
            x = 210 + depth * 55
            self._blit(
                body_font,
                prefix + entry.get("journal_text", entry.get("title", "")),
                (x, y),
                (210, 228, 235),
            )
            y += body_font.get_height() + 20

        self._blit(body_font, "あなたの推理", (190, self.input_rect.y - 48), (235, 242, 245))
        if self.feedback_text:
            self._blit(
                body_font,
                self.feedback_text,
                (430, self.input_rect.y - 48),
                self.feedback_color,
            )
        pygame.draw.rect(self.screen, (16, 21, 29), self.input_rect, border_radius=6)
        pygame.draw.rect(self.screen, (115, 198, 225), self.input_rect, 2, border_radius=6)
        shown = self.text + self.composition
        color = (245, 245, 245) if self.text else (160, 170, 178)
        self._blit(body_font, shown or "ここに入力", (self.input_rect.x + 18, self.input_rect.y + 14), color)

        pygame.draw.rect(self.screen, (58, 132, 160), self.submit_rect, border_radius=6)
        self._blit(body_font, "推理する", (self.submit_rect.x + 26, self.submit_rect.y + 5), (255, 255, 255))
        self._blit(
            body_font,
            "Ctrl+Enterでも決定",
            (self.panel_rect.x + 70, self.submit_rect.y + 5),
            (150, 170, 180),
        )

    def _depth(self, entry, acquired_ids):
        depth = 0
        current = entry
        seen = set()
        while current.get("parents"):
            parent_id = current["parents"][0]
            if parent_id in seen or parent_id not in acquired_ids:
                break
            seen.add(parent_id)
            depth += 1
            current = self.seed_manager.seeds.get(parent_id, {})
        return depth

    def _blit(self, font, text, pos, color):
        surface = font.render(str(text), True, color)
        self.screen.blit(surface, pos)
