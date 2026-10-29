"""Image-based school map with a single classroom destination."""

from pathlib import Path

import pygame

from core.config import window_to_virtual_pos
from core.path_utils import get_project_root
from core.runtime.subsystem_base import SubsystemBase


class GDMap(SubsystemBase):
    # Original 640x480 image coordinates, clockwise from the top-left corner.
    # Traced from the red classroom outline in images/maps/demo02.png.
    CLASSROOM_POLYGON = ((433, 214), (537, 230), (494, 276), (387, 258))

    def __init__(self, screen):
        super().__init__(screen)
        directory = Path(get_project_root(), "images", "maps")
        normal = pygame.image.load(str(directory / "demo01.png")).convert()
        hover = pygame.image.load(str(directory / "demo02.png")).convert()
        self.image_size = normal.get_size()
        self.normal_image = pygame.transform.smoothscale(normal, screen.get_size())
        self.hover_image = pygame.transform.smoothscale(hover, screen.get_size())
        self.hovered = False

    def classroom_at(self, pos):
        # Events already use virtual-screen coordinates. Undo only image scaling.
        x = pos[0] * self.image_size[0] / self.screen.get_width()
        y = pos[1] * self.image_size[1] / self.screen.get_height()
        vertices = self.CLASSROOM_POLYGON
        return all(
            (end[0] - start[0]) * (y - start[1])
            - (end[1] - start[1]) * (x - start[0]) >= 0
            for start, end in zip(vertices, vertices[1:] + vertices[:1])
        )

    def on_enter(self):
        self.hovered = self.classroom_at(window_to_virtual_pos(pygame.mouse.get_pos()))

    def handle_events(self, events=None):
        for event in events or []:
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return "show_settings"
            if event.type == pygame.WINDOWLEAVE:
                self.hovered = False
            elif event.type == pygame.MOUSEMOTION:
                self.hovered = self.classroom_at(event.pos)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.hovered = self.classroom_at(event.pos)
                if self.hovered:
                    return "demo_next"
        return None

    def render(self):
        self.screen.blit(self.hover_image if self.hovered else self.normal_image, (0, 0))

    def update(self):
        pass
