import pygame

from core.config import VIRTUAL_HEIGHT, VIRTUAL_WIDTH
from dialogue.background_manager import draw_background, show_background


class StubImageManager:
    def __init__(self, image):
        self.image = image

    def get_image(self, image_type, image_key):
        assert image_type == "bg"
        assert image_key == "test-background"
        return self.image


def test_wide_background_keeps_aspect_ratio_and_uses_black_letterbox():
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

    assert screen.get_at((VIRTUAL_WIDTH // 2, VIRTUAL_HEIGHT // 2))[:3] == (
        12,
        34,
        56,
    )
    assert screen.get_at((VIRTUAL_WIDTH // 2, 0))[:3] == (0, 0, 0)
    assert screen.get_at((VIRTUAL_WIDTH - 1, VIRTUAL_HEIGHT - 1))[:3] == (0, 0, 0)


def test_portrait_background_keeps_aspect_ratio_when_zoomed_below_one():
    source = pygame.Surface((400, 800))
    source.fill((90, 120, 150))
    screen = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT))
    game_state = {
        "screen": screen,
        "image_manager": StubImageManager(source),
        "background_state": {
            "current_bg": "test-background",
            "zoom": 0.5,
            "pos": [0, 0],
            "anim": None,
        },
    }

    draw_background(game_state)

    # A 1:2 source fits to 540x1080 at zoom 1, then becomes 270x540.
    assert screen.get_at((VIRTUAL_WIDTH // 2, VIRTUAL_HEIGHT // 2))[:3] == (
        90,
        120,
        150,
    )
    assert screen.get_at((VIRTUAL_WIDTH // 2 - 136, VIRTUAL_HEIGHT // 2))[:3] == (
        0,
        0,
        0,
    )
    assert screen.get_at((VIRTUAL_WIDTH // 2, VIRTUAL_HEIGHT // 2 - 271))[:3] == (
        0,
        0,
        0,
    )


def test_background_zoom_below_half_is_not_silently_raised():
    source = pygame.Surface((400, 800))
    state = {
        "image_manager": StubImageManager(source),
        "background_state": {
            "current_bg": None,
            "zoom": 1.0,
            "pos": [0, 0],
            "anim": None,
        },
    }

    show_background(state, "test-background", 0.5, 0.5, 0.3)

    assert state["background_state"]["zoom"] == 0.3


def test_background_x_positions_image_center_independently_of_zoom():
    source = pygame.Surface((400, 800))

    def offset_for(bg_x, zoom):
        state = {
            "image_manager": StubImageManager(source),
            "background_state": {
                "current_bg": None,
                "zoom": 1.0,
                "pos": [0, 0],
                "anim": None,
            },
        }
        show_background(state, "test-background", bg_x, 0.5, zoom)
        return state["background_state"]["pos"][0]

    assert offset_for(0.0, 0.3) == -VIRTUAL_WIDTH / 2
    assert offset_for(0.4, 0.5) == VIRTUAL_WIDTH * -0.1
    assert offset_for(0.5, 1.0) == 0
    assert offset_for(1.0, 2.0) == VIRTUAL_WIDTH / 2


def test_empty_background_storage_clears_to_black():
    source = pygame.Surface((400, 800))
    screen = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT))
    screen.fill((255, 0, 0))
    state = {
        "screen": screen,
        "image_manager": StubImageManager(source),
        "background_state": {
            "current_bg": "test-background",
            "zoom": 1.0,
            "pos": [0, 0],
            "anim": None,
        },
    }

    show_background(state, "", 0.5, 0.5, 1.0)
    draw_background(state)

    assert state["background_state"]["current_bg"] == ""
    assert screen.get_at((VIRTUAL_WIDTH // 2, VIRTUAL_HEIGHT // 2))[:3] == (0, 0, 0)
