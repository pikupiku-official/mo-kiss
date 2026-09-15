import pygame

from dialogue.character_manager import (
    _character_display_zoom,
    _character_haze_factor,
)
from dialogue.haze_manager import HazeManager


def test_character_haze_factor_uses_requested_linear_anchors():
    assert _character_haze_factor(0.5) == 1.0
    assert _character_haze_factor(0.75) == 0.75
    assert _character_haze_factor(1.0) == 0.5
    assert _character_haze_factor(1.5) == 0.25
    assert _character_haze_factor(2.0) == 0.0


def test_character_haze_factor_clamps_outside_authored_range():
    assert _character_haze_factor(0.1) == 1.0
    assert _character_haze_factor(2.5) == 0.0
    assert _character_haze_factor("not-a-number") == 0.5


def test_character_display_zoom_tracks_crossfade_size():
    game_state = {
        "character_zoom": {"桃子": 0.5},
        "character_transitions": {
            "桃子": {
                "mode": "crossfade",
                "from_zoom": 0.5,
                "to_zoom": 2.0,
                "start_time": 1000,
                "duration": 1000,
            }
        },
    }

    assert _character_display_zoom(game_state, "桃子", 1000) == 0.5
    assert _character_display_zoom(game_state, "桃子", 1500) == 1.25
    assert _character_display_zoom(game_state, "桃子", 2000) == 2.0


def test_haze_application_preserves_character_alpha():
    pygame.init()
    try:
        screen = pygame.Surface((20, 20), pygame.SRCALPHA, 32)
        screen.fill((200, 100, 50, 128))
        manager = HazeManager(screen)
        manager.state.update(
            opacity=1.0,
            color=(100, 150, 200),
            drift=0.0,
        )

        manager.apply_to_transparent_surface(screen, 1.0)

        red, green, blue, alpha = screen.get_at((10, 10))
        assert alpha == 128
        assert (red, green, blue) != (200, 100, 50)
    finally:
        pygame.quit()
