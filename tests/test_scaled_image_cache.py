import pygame

from dialogue.character_manager import (
    _SCALED_IMAGE_CACHE_LIMIT,
    _scaled_image_cache,
    get_scaled_image,
)


def setup_function():
    _scaled_image_cache.clear()


def teardown_function():
    _scaled_image_cache.clear()


def test_scaled_cache_keys_by_surface_not_integer_id():
    source = pygame.Surface((2, 2), pygame.SRCALPHA)
    source.fill((255, 0, 0, 255))

    scaled = get_scaled_image(source, 2.0)

    cache_key = next(iter(_scaled_image_cache))
    assert cache_key[0] is source
    assert not isinstance(cache_key[0], int)
    assert _scaled_image_cache[cache_key] is scaled


def test_different_surfaces_never_share_a_scaled_entry():
    red = pygame.Surface((2, 2), pygame.SRCALPHA)
    red.fill((255, 0, 0, 255))
    transparent = pygame.Surface((2, 2), pygame.SRCALPHA)
    transparent.fill((0, 0, 0, 0))

    red_scaled = get_scaled_image(red, 2.0)
    transparent_scaled = get_scaled_image(transparent, 2.0)

    assert red_scaled is not transparent_scaled
    assert red_scaled.get_at((0, 0)).a == 255
    assert transparent_scaled.get_at((0, 0)).a == 0


def test_scaled_cache_is_lru_bounded():
    sources = []
    for index in range(_SCALED_IMAGE_CACHE_LIMIT + 1):
        source = pygame.Surface((1, 1), pygame.SRCALPHA)
        source.fill((index % 256, 0, 0, 255))
        sources.append(source)
        get_scaled_image(source, 2.0)

    assert len(_scaled_image_cache) == _SCALED_IMAGE_CACHE_LIMIT
    cached_sources = [key[0] for key in _scaled_image_cache]
    assert sources[0] not in cached_sources
    assert sources[-1] in cached_sources
