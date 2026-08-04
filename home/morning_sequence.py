"""「寝る」選択後の朝演出を管理する状態機械。"""

from __future__ import annotations

import pygame


NEWS_DURATION_MS = 4_000
PULLBACK_FRAME_MS = 300
PULLBACK_FRAMES = ("home03", "home02", "home01", "home00")
MORNING_DIALOGUE_RESULT = "launch_morning_departure"


class MorningSequence:
    """仮ニュースから部屋の引き演出、出発セリフまでを順番に進める。"""

    NEWS = "news"
    PULLBACK = "pullback"
    DIALOGUE_READY = "dialogue_ready"

    def __init__(self, date_text: str, clock_ms=None):
        self.date_text = date_text
        self.phase = self.NEWS
        self.frame_index = 0
        self._clock_ms = clock_ms or pygame.time.get_ticks
        self._news_started_at = self._clock_ms()
        self._pullback_started_at = None

    @property
    def background_key(self) -> str:
        if self.phase == self.PULLBACK:
            return PULLBACK_FRAMES[self.frame_index]
        if self.phase == self.NEWS:
            return "home03"
        return "home00"

    def handle_events(self, events) -> str | None:
        if self.phase == self.DIALOGUE_READY:
            return MORNING_DIALOGUE_RESULT
        return None

    def update(self) -> None:
        now = self._clock_ms()
        if self.phase == self.NEWS:
            if now - self._news_started_at < NEWS_DURATION_MS:
                return
            self.phase = self.PULLBACK
            self.frame_index = 0
            # 事前読み込みで更新間隔が延びても、引きの4枚を飛ばさず全て表示する。
            self._pullback_started_at = now

        if self.phase != self.PULLBACK or self._pullback_started_at is None:
            return

        elapsed = max(0, now - self._pullback_started_at)
        next_index = elapsed // PULLBACK_FRAME_MS
        if next_index >= len(PULLBACK_FRAMES):
            self.phase = self.DIALOGUE_READY
            self.frame_index = len(PULLBACK_FRAMES) - 1
            return

        self.frame_index = int(next_index)

    def render_overlay(self, screen, content_rect, font, large_font) -> None:
        if self.phase == self.NEWS:
            self._render_placeholder_news(screen, content_rect, font, large_font)

    def _render_placeholder_news(self, screen, content_rect, font, large_font) -> None:
        """Step 1用の平面CRT。曲面メッシュ化は次段階で行う。"""
        panel_rect = pygame.Rect(
            content_rect.x + int(content_rect.width * 0.16),
            content_rect.y + int(content_rect.height * 0.14),
            int(content_rect.width * 0.68),
            int(content_rect.height * 0.68),
        )
        panel = pygame.Surface(panel_rect.size, pygame.SRCALPHA)
        panel.fill((0, 12, 3, 205))
        pygame.draw.rect(panel, (70, 165, 88, 220), panel.get_rect(), 3)

        lines = [
            self.date_text,
            "朝刊ニュース",
            "1. 仮ニュース（未登録）",
            "2. 仮ニュース（未登録）",
            "3. 仮ニュース（未登録）",
        ]
        colors = [(125, 255, 145), (95, 230, 115)]
        y = 34
        for index, line in enumerate(lines):
            line_font = large_font if index == 0 else font
            color = colors[0] if index < 2 else colors[1]
            text = line_font.render(line, True, color)
            panel.blit(text, (36, y))
            y += text.get_height() + (24 if index == 1 else 16)

        help_text = font.render("4秒後に自動で切り替わります", True, (80, 185, 100))
        panel.blit(help_text, (36, panel.get_height() - help_text.get_height() - 28))
        screen.blit(panel, panel_rect.topleft)
