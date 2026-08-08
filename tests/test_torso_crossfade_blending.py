import pygame

from dialogue.character_manager import _blit_crossfade


def test_torso_crossfade_midpoint_does_not_dim_through_to_background():
    screen = pygame.Surface((1, 1), pygame.SRCALPHA)
    screen.fill((0, 255, 0, 255))
    old_torso = pygame.Surface((1, 1), pygame.SRCALPHA)
    old_torso.fill((255, 0, 0, 255))
    new_torso = pygame.Surface((1, 1), pygame.SRCALPHA)
    new_torso.fill((0, 0, 255, 255))

    _blit_crossfade(
        screen,
        old_torso,
        (0, 0),
        new_torso,
        (0, 0),
        0.5,
    )

    pixel = screen.get_at((0, 0))
    assert pixel.a == 255
    assert pixel.g == 0
    assert abs(pixel.r - pixel.b) <= 1


def test_torso_crossfade_fades_changed_silhouette_pixels():
    screen = pygame.Surface((1, 1), pygame.SRCALPHA)
    screen.fill((255, 255, 255, 255))
    old_torso = pygame.Surface((1, 1), pygame.SRCALPHA)
    old_torso.fill((255, 0, 0, 255))
    transparent_new_torso = pygame.Surface((1, 1), pygame.SRCALPHA)
    transparent_new_torso.fill((0, 0, 0, 0))

    _blit_crossfade(
        screen,
        old_torso,
        (0, 0),
        transparent_new_torso,
        (0, 0),
        0.5,
    )

    pixel = screen.get_at((0, 0))
    assert pixel.a == 255
    assert pixel.r == 255
    assert abs(pixel.g - 128) <= 1
    assert abs(pixel.b - 128) <= 1
