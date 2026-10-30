"""CG blend appearance and fallback behavior at intermediate fade frames."""

import os
import weakref
import gc

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pygame
import pytest

from dialogue.cg_manager import _blit_cg_crossfade, _opaque_cg_cache
from dialogue.character_manager import _blit_crossfade


def image(color, size=(8, 6)):
    surface = pygame.Surface(size, pygame.SRCALPHA)
    surface.fill(color)
    return surface


@pytest.mark.parametrize("progress", [0, .1, .25, .5, .75, .9, 1])
def test_opaque_cg_blend_matches_linear_fade_without_background_leak(progress):
    old = image((229, 21, 141, 255))
    new = image((16, 179, 50, 255))
    # Include spatial detail and clipped placement, not just uniform fills.
    old.set_at((3, 2), (0, 255, 90, 255))
    new.set_at((3, 2), (255, 0, 170, 255))
    expected = image((0, 255, 0, 255))
    actual = expected.copy()
    expected.set_clip((1, 1, 5, 4))
    actual.set_clip(expected.get_clip())
    before = [pygame.image.tostring(s, "RGBA") for s in (old, new)]
    _blit_crossfade(expected, old, (-1, 0), new, (-1, 0), progress)
    _blit_cg_crossfade(actual, old, (-1, 0), new, (-1, 0), progress)
    # The two integer compositors can round a channel one step differently.
    assert max(abs(a - b) for a, b in zip(pygame.image.tostring(actual, "RGBA"),
                                        pygame.image.tostring(expected, "RGBA"))) <= 2
    assert [pygame.image.tostring(s, "RGBA") for s in (old, new)] == before
    assert old.get_alpha() == new.get_alpha() == 255


@pytest.mark.parametrize("case", ["transparent", "hole", "global_alpha", "colorkey",
                                  "move", "zoom", "show", "hide"])
def test_other_cg_blends_preserve_existing_pixels_exactly(case):
    old, new = image((230, 20, 140, 255)), image((15, 180, 50, 255))
    old_pos = new_pos = (0, 0)
    if case == "transparent":
        new.fill((15, 180, 50, 128))
    elif case == "hole":
        new.set_at((2, 2), (15, 180, 50, 0))
    elif case == "global_alpha":
        new.set_alpha(100)
    elif case == "colorkey":
        new.set_colorkey((15, 180, 50))
    elif case == "move":
        new_pos = (2, 1)
    elif case == "zoom":
        new = image((15, 180, 50, 255), (9, 7))
    elif case == "show":
        old = None
    elif case == "hide":
        new = None
    expected = image((245, 245, 245, 255))
    actual = expected.copy()
    _blit_crossfade(expected, old, old_pos, new, new_pos, .5)
    _blit_cg_crossfade(actual, old, old_pos, new, new_pos, .5)
    assert pygame.image.tostring(actual, "RGBA") == pygame.image.tostring(expected, "RGBA")


def test_opaque_renditions_do_not_keep_the_source_cg_alive():
    from dialogue.cg_manager import _opaque_cg_surface

    source = image((255, 255, 255, 255))
    ref = weakref.ref(source)
    _opaque_cg_surface(source)
    assert source in _opaque_cg_cache
    del source
    gc.collect()
    assert ref() is None


def test_cg_frames_do_not_reload_images_when_background_exceeds_native_cache(tmp_path, monkeypatch):
    from core.services.image_manager import ImageManager
    from dialogue.background_manager import show_background, draw_background
    from dialogue.cg_manager import show_cg, shift_cg, draw_cg, update_cg_animation
    from dialogue.character_images import prepare_character_images

    pygame.display.init()
    pygame.display.set_mode((1, 1))
    paths = {}
    for name, size, color in (("room", (80, 60), (10, 20, 30, 255)),
                              ("old", (8, 6), (230, 20, 140, 255)),
                              ("new", (8, 6), (15, 180, 50, 255))):
        path = tmp_path / f"{name}.png"
        pygame.image.save(image(color, size), str(path))
        paths[name] = str(path)
    manager = ImageManager(cache_bytes=2000)
    manager.image_paths = {"bg": {"room": paths["room"]},
                           "cg": {key: paths[key] for key in ("old", "new")}}
    state = {"screen": pygame.Surface((1440, 1080)), "image_manager": manager,
             "background_state": {}, "ir_data": {"steps": [
                 {"actions": [{"action": "cg_show", "params": {"storage": "old"}}]},
                 {"actions": [{"action": "cg_shift", "params": {"storage": "new"}}]},
             ]}}
    now = [0]
    monkeypatch.setattr(pygame.time, "get_ticks", lambda: now[0])
    try:
        prepare_character_images(state)
        show_background(state, "room", .5, .5, 1)
        load = pygame.image.load
        requests = []

        def tracked_load(path):
            requests.append(path)
            return load(path)

        monkeypatch.setattr(pygame.image, "load", tracked_load)
        assert show_cg(state, "old", {"fade": .5}) == 500
        for tick in range(0, 501, 50):
            now[0] = tick
            update_cg_animation(state)
            draw_background(state)
            draw_cg(state)
        assert shift_cg(state, {"storage": "new", "fade": .3}) == 300
        for tick in (0, 50, 100, 150, 200, 250, 300, 350):
            now[0] = tick + 500
            update_cg_animation(state)
            draw_background(state)
            draw_cg(state)
        assert requests == []
        assert state["cg_state"]["storage"] == "new"
        assert state["cg_state"]["transition"] is None
    finally:
        manager.cleanup()


def test_cg_resize_finishes_before_fade_clock_starts(monkeypatch):
    from dialogue.cg_manager import show_cg, shift_cg

    class Manager:
        def get_image(self, category, key):
            return image((10, 20, 30, 255))

    now = [1000]
    resize = pygame.transform.smoothscale
    monkeypatch.setattr(pygame.time, "get_ticks", lambda: now[0])

    def slow_resize(*args):
        result = resize(*args)
        now[0] += 100
        return result

    monkeypatch.setattr(pygame.transform, "smoothscale", slow_resize)
    state = {"image_manager": Manager()}
    assert show_cg(state, "old", {"fade": .5}) == 500
    assert state["cg_state"]["transition"]["start_time"] == now[0] == 1100
    now[0] = 1600
    assert shift_cg(state, {"storage": "new", "fade": .3}) == 300
    assert state["cg_state"]["transition"]["start_time"] == now[0] == 1700
