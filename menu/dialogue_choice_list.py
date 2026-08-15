"""Dialogue-styled text lists shared by menu screens."""

from __future__ import annotations

import pygame

from dialogue.choice_renderer import ChoiceRenderer


class DialogueChoiceList:
    """A centered, keyboard and mouse operated list using dialogue glyphs."""

    def __init__(
        self,
        screen: pygame.Surface,
        choices,
        *,
        center_x: int | None = None,
        center_y: int | None = None,
        row_spacing: int = 78,
        enabled=None,
        renderer: ChoiceRenderer | None = None,
    ):
        self.screen = screen
        self.renderer = renderer or ChoiceRenderer(screen)
        self.choices = list(choices)
        self.enabled = list(enabled) if enabled is not None else [True] * len(self.choices)
        if len(self.enabled) != len(self.choices):
            raise ValueError("enabled must have the same length as choices")
        self.center_x = center_x if center_x is not None else screen.get_width() // 2
        self.center_y = center_y if center_y is not None else screen.get_height() // 2
        self.row_spacing = row_spacing
        self.selected_index = self._first_enabled_index()
        self.rects: list[pygame.Rect] = []
        self._surfaces = {}
        self._rebuild_layout()

    def _first_enabled_index(self):
        return next((index for index, value in enumerate(self.enabled) if value), -1)

    def _render_surface(self, index, color):
        key = (index, color)
        if key not in self._surfaces:
            self._surfaces[key] = self.renderer._render_choice_with_grid_system(
                self.choices[index], color
            )
        return self._surfaces[key]

    @staticmethod
    def _visible_bounds(surface: pygame.Surface) -> pygame.Rect:
        bounds = surface.get_bounding_rect(min_alpha=1)
        if bounds.width == 0 or bounds.height == 0:
            return pygame.Rect(0, 0, 1, max(1, surface.get_height()))
        return bounds

    def _rebuild_layout(self):
        self.rects = []
        if not self.choices:
            return
        first_surface = self._render_surface(0, self.renderer.normal_color)
        glyph_height = self._visible_bounds(first_surface).height
        total_height = glyph_height + self.row_spacing * (len(self.choices) - 1)
        first_center_y = self.center_y - total_height // 2 + glyph_height // 2

        for index in range(len(self.choices)):
            surface = self._render_surface(index, self.renderer.normal_color)
            bounds = self._visible_bounds(surface)
            center_y = first_center_y + index * self.row_spacing
            self.rects.append(
                pygame.Rect(
                    self.center_x - bounds.width // 2 - 24,
                    center_y - bounds.height // 2 - 10,
                    bounds.width + 48,
                    bounds.height + 20,
                )
            )

    def move(self, amount: int):
        if not self.choices or not any(self.enabled):
            self.selected_index = -1
            return
        index = self.selected_index
        if index < 0:
            index = self._first_enabled_index()
        for _ in range(len(self.choices)):
            index = (index + amount) % len(self.choices)
            if self.enabled[index]:
                self.selected_index = index
                return

    def update_hover(self, pos):
        for index, rect in enumerate(self.rects):
            if self.enabled[index] and rect.collidepoint(pos):
                self.selected_index = index
                return

    def choice_at(self, pos):
        for index, rect in enumerate(self.rects):
            if self.enabled[index] and rect.collidepoint(pos):
                self.selected_index = index
                return index
        return -1

    def activate(self):
        if 0 <= self.selected_index < len(self.choices) and self.enabled[self.selected_index]:
            return self.selected_index
        return -1

    def render(self):
        for index in range(len(self.choices)):
            if not self.enabled[index]:
                color = (105, 105, 105)
            elif index == self.selected_index:
                color = self.renderer.highlight_color
            else:
                color = self.renderer.normal_color
            surface = self._render_surface(index, color)
            bounds = self._visible_bounds(surface)
            target = self.rects[index]
            self.screen.blit(
                surface,
                (
                    target.centerx - bounds.width // 2 - bounds.x,
                    target.centery - bounds.height // 2 - bounds.y,
                ),
            )


def draw_dialogue_text_centered(
    screen: pygame.Surface,
    renderer: ChoiceRenderer,
    text: str,
    center_y: int,
    color=None,
):
    """Draw one dialogue-styled line centered on the screen."""
    color = renderer.normal_color if color is None else color
    surface = renderer._render_choice_with_grid_system(text, color)
    bounds = DialogueChoiceList._visible_bounds(surface)
    screen.blit(
        surface,
        (
            screen.get_width() // 2 - bounds.width // 2 - bounds.x,
            center_y - bounds.height // 2 - bounds.y,
        ),
    )
