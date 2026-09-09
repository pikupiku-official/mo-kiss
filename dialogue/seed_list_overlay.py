"""Minimal, backlog-like list of acquired and masked seed clues."""

from __future__ import annotations

import pygame

from core.config import SEED_INPUT_CONFIG, TEXT_COLOR
from core.ui.dim_overlay import SceneDimmer


class SeedListOverlay:
    """Render the authored seed hierarchy without cards or window chrome."""

    def __init__(self, screen, seed_manager, text_renderer):
        self.screen = screen
        self.seed_manager = seed_manager
        self.text_renderer = text_renderer
        self.is_showing = False
        self.scroll_line = 0
        self._opened_at_ms = None
        self._dimmer = SceneDimmer(SEED_INPUT_CONFIG["seed_list_dim_alpha"])

    def toggle(self):
        self.is_showing = not self.is_showing
        if self.is_showing:
            self.scroll_line = 0
            self._opened_at_ms = pygame.time.get_ticks()
            if getattr(self.text_renderer, "current_text", ""):
                self.text_renderer.skip_text()
        elif self._opened_at_ms is not None:
            self.text_renderer.resume_after_backlog(
                pygame.time.get_ticks() - self._opened_at_ms
            )
            self._opened_at_ms = None
        return self.is_showing

    def close(self):
        self.is_showing = False
        self._opened_at_ms = None

    def handle_event(self, event):
        if not self.is_showing:
            return False
        if event.type == pygame.MOUSEWHEEL:
            self.scroll_line = max(0, self.scroll_line - event.y)
            return True
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.scroll_line = max(0, self.scroll_line - 1)
            elif event.key == pygame.K_DOWN:
                self.scroll_line += 1
            elif event.key == pygame.K_PAGEUP:
                self.scroll_line = max(0, self.scroll_line - 6)
            elif event.key == pygame.K_PAGEDOWN:
                self.scroll_line += 6
            return True
        return True

    def _depth(self, seed):
        depth = 0
        current = seed
        seen = set()
        while current.get("parents"):
            parent_id = current["parents"][0]
            if parent_id in seen:
                break
            seen.add(parent_id)
            parent = self.seed_manager.seeds.get(parent_id)
            if not parent:
                break
            depth += 1
            current = parent
        return depth

    def _display_lines(self):
        acquired = self.seed_manager.state.get("acquired", {})
        rows = []
        seeds = sorted(
            self.seed_manager.seeds.values(),
            key=lambda item: self.seed_manager._seed_sort_key(item["id"]),
        )
        for seed in seeds:
            is_acquired = seed["id"] in acquired
            if is_acquired:
                text = seed.get("journal_text", seed.get("title", seed["id"]))
                color = TEXT_COLOR
                marker = "●"
            else:
                text = seed.get("masked_journal_text") or "？？？"
                color = SEED_INPUT_CONFIG["masked_color"]
                marker = "○"
            depth = self._depth(seed)
            prefix = "　" * depth + marker
            wrapped = self.text_renderer._wrap_text(prefix + str(text))
            continuation = "　" * (depth + 1)
            wrapped = [
                line if index == 0 else continuation + line
                for index, line in enumerate(wrapped)
            ]
            rows.extend((line, color) for line in wrapped)
        return rows

    def render(self):
        if not self.is_showing:
            return
        self._dimmer.render(self.screen)
        rows = self._display_lines()
        line_height = self.text_renderer.text_line_height
        top = 150
        bottom = self.screen.get_height() - 90
        visible_count = max(1, (bottom - top) // line_height)
        max_scroll = max(0, len(rows) - visible_count)
        self.scroll_line = min(self.scroll_line, max_scroll)
        x = self.text_renderer.name_start_x
        y = top
        for text, color in rows[self.scroll_line : self.scroll_line + visible_count]:
            surface = self.text_renderer._render_stable_text_line(text, color)
            self.screen.blit(surface, (x, y - self.text_renderer.ruby_h))
            y += line_height
