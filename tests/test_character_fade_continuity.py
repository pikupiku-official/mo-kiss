import pygame
import pytest

from dialogue.character_manager import (
    _build_character_snapshot,
    draw_characters,
    render_face_parts,
    _blit_with_alpha,
    _begin_character_fade_on_first_render,
    update_character_fades,
)


class Images:
    def __init__(self, images):
        self.images = images

    def get_image(self, category, key):
        return self.images.get((category, key))


def surface(size, color):
    image = pygame.Surface(size, pygame.SRCALPHA)
    image.fill(color)
    return image


def test_expression_crossfade_keeps_opaque_overlap_opaque():
    screen = surface((8, 8), (0, 255, 0, 255))
    state = {
        'screen': screen,
        'image_manager': Images({
            ('torso', 'body'): surface((3, 3), (0, 0, 0, 0)),
            ('eye', 'old'): surface((3, 3), (255, 0, 0, 255)),
            ('eye', 'new'): surface((3, 3), (0, 0, 255, 255)),
        }),
        'character_pos': {'actor': [2, 2]},
        'character_torso': {'actor': 'body'},
    }
    render_face_parts(state, 'actor', '', 'new', '', '', 1.0,
                      fade_map={'eye': {'from': 'old', 'to': 'new',
                                        'start_time': 0, 'duration': 100}},
                      current_time=50)
    pixel = screen.get_at((3, 3))
    assert pixel.g == 0
    assert abs(pixel.r - pixel.b) <= 1


def test_snapshot_and_regular_pose_have_identical_pixel_positions():
    torso = surface((7, 1080), (255, 0, 0, 255))
    eye = surface((3, 1080), (0, 0, 255, 255))
    screen = surface((32, 1200), (0, 0, 0, 0))
    expressions = {'eye': 'eye'}
    state = {
        'screen': screen,
        'image_manager': Images({('torso', 'body'): torso, ('eye', 'eye'): eye}),
        'dialogue_data': [],
        'active_characters': ['actor'],
        'character_pos': {'actor': [2, 0]},
        'character_zoom': {'actor': 1.1},
        'character_torso': {'actor': 'body'},
        'character_expressions': {'actor': expressions},
        'show_face_parts': True,
    }
    draw_characters(state)
    snapshot, pos = _build_character_snapshot(
        state, 'actor', 'body', expressions, [2, 0], 1.1)
    composed = surface(screen.get_size(), (0, 0, 0, 0))
    composed.blit(snapshot, pos)
    assert pygame.image.tobytes(screen, 'RGBA') == pygame.image.tobytes(composed, 'RGBA')


@pytest.mark.parametrize('showing', [True, False])
def test_show_and_hide_fade_the_composed_pose_once(monkeypatch, showing):
    monkeypatch.setattr(pygame.time, 'get_ticks', lambda: 50)
    body = surface((8, 1080), (255, 0, 0, 255))
    eye = surface((8, 1080), (0, 0, 255, 255))
    state = {
        'screen': surface((8, 1080), (0, 255, 0, 255)),
        'image_manager': Images({('torso', 'body'): body, ('eye', 'eye'): eye}),
        'dialogue_data': [], 'active_characters': ['actor'],
        'character_pos': {'actor': [0, 0]}, 'character_zoom': {'actor': 1.0},
        'character_torso': {'actor': 'body'},
        'character_expressions': {'actor': {'eye': 'eye'}},
        'show_face_parts': True,
        'character_part_fades': {'actor': {
            part: {'from': None if showing else key,
                   'to': key if showing else None, 'start_time': 0, 'duration': 100}
            for part, key in [('torso', 'body'), ('eye', 'eye')]
        }},
    }
    draw_characters(state)
    pixel = state['screen'].get_at((4, 500))
    assert pixel.r == 0  # The body must never bleed through the opaque eye.
    assert abs(pixel.g - pixel.b) <= 1


def test_hide_waits_for_first_visible_frame_and_retimes_its_deadline(monkeypatch):
    fade = {'from': 'body', 'to': None, 'start_time': 0, 'duration': 100}
    state = {'character_part_fades': {'actor': {'torso': fade}},
             'character_fade_pending_render': {'actor': {'torso'}},
             'character_hide_pending': {'actor': 100}}
    monkeypatch.setattr(pygame.time, 'get_ticks', lambda: 500)
    update_character_fades(state)
    assert 'actor' in state['character_hide_pending']
    _begin_character_fade_on_first_render(state, 'actor', 500)
    assert state['character_hide_pending']['actor'] == 600


def test_cg_hidden_character_fades_start_without_waiting_for_visible_pixels(monkeypatch):
    monkeypatch.setattr(pygame.time, 'get_ticks', lambda: 500)
    state = {'cg_state': {'storage': 'cg'},
             'character_part_fades': {'actor': {
                 'torso': {'from': 'body', 'to': None, 'start_time': 0, 'duration': 100}}},
             'character_fade_pending_render': {'actor': {'torso'}},
             'character_hide_pending': {'actor': 100}}
    draw_characters(state)
    assert state['character_fade_pending_render'] == {}
    assert state['character_hide_pending']['actor'] == 600


@pytest.mark.parametrize('position', [(3, 4), (-2, -3), (3.75, 4.5)])
def test_alpha_crop_matches_full_canvas_blending_with_screen_clip(position):
    image = surface((20, 20), (0, 0, 0, 0))
    image.fill((200, 50, 30, 170), (2, 3, 6, 7))
    expected = surface((16, 16), (10, 20, 30, 255))
    actual = expected.copy()
    expected.set_clip((1, 2, 12, 10))
    actual.set_clip(expected.get_clip())
    faded = image.copy()
    faded.set_alpha(128)
    expected.blit(faded, position)
    _blit_with_alpha(actual, image, position, 128)
    assert pygame.image.tobytes(actual, 'RGBA') == pygame.image.tobytes(expected, 'RGBA')
