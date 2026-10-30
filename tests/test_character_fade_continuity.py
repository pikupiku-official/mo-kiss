import pygame

from dialogue.character_manager import (
    _build_character_snapshot,
    draw_characters,
    render_face_parts,
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
