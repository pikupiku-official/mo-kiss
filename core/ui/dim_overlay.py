"""Shared scene-dimming layer used by in-game text overlays."""

import pygame


class SceneDimmer:
    def __init__(self, alpha=140):
        self.alpha = int(alpha)
        self._surface = None

    def render(self, target):
        if self._surface is None or self._surface.get_size() != target.get_size():
            self._surface = pygame.Surface(target.get_size(), pygame.SRCALPHA)
        self._surface.fill((0, 0, 0, self.alpha))
        target.blit(self._surface, (0, 0))
