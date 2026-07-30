import pygame

from core.config import VIRTUAL_HEIGHT, VIRTUAL_WIDTH
from dialogue.background_manager import draw_background


class StubImageManager:
    def __init__(self, image):
        self.image = image

    def get_image(self, image_type, image_key):
        assert image_type == "bg"
        assert image_key == "test-background"
        return self.image


def test_background_source_is_scaled_to_virtual_screen():
    source = pygame.Surface((640, 360))
    source.fill((12, 34, 56))
    screen = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT))
    game_state = {
        "screen": screen,
        "image_manager": StubImageManager(source),
        "background_state": {
            "current_bg": "test-background",
            "zoom": 1.0,
            "pos": [0, 0],
            "anim": None,
        },
    }

    draw_background(game_state)

    assert screen.get_at((VIRTUAL_WIDTH - 1, VIRTUAL_HEIGHT - 1))[:3] == (
        12,
        34,
        56,
    )
