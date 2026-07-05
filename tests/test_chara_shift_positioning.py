from core.config import SCALE, VIRTUAL_HEIGHT, VIRTUAL_WIDTH, scale_pos
from dialogue.scenario_manager import _ir_handle_character_shift


class DummyImage:
    def __init__(self, width, height):
        self._width = width
        self._height = height

    def get_width(self):
        return self._width

    def get_height(self):
        return self._height


class DummyImageManager:
    def __init__(self, images):
        self._images = images

    def get_image(self, image_type, image_id):
        return self._images.get((image_type, image_id))


def _expected_position(width, height, show_x, show_y, size):
    base_scale = VIRTUAL_HEIGHT / height
    virtual_width = width * base_scale * size
    virtual_height = height * base_scale * size
    virtual_x = int(VIRTUAL_WIDTH * show_x - virtual_width // 2)
    virtual_y = int(VIRTUAL_HEIGHT * show_y - virtual_height // 2)
    return list(scale_pos(virtual_x, virtual_y))


def test_chara_shift_updates_position_and_size():
    torso = DummyImage(500, 1000)
    game_state = {
        "active_characters": ["momoko"],
        "character_pos": {"momoko": [10, 20]},
        "character_zoom": {"momoko": 1.0},
        "character_expressions": {"momoko": {}},
        "character_torso": {"momoko": "T00"},
        "image_manager": DummyImageManager({("torso", "T00"): torso}),
    }

    _ir_handle_character_shift(
        game_state,
        "momoko",
        {"x": 0.6, "y": 0.4, "size": 1.5, "fade": 0},
    )

    assert game_state["character_pos"]["momoko"] == _expected_position(500, 1000, 0.6, 0.4, 1.5)
    assert game_state["character_zoom"]["momoko"] == 1.5


def test_chara_shift_preserves_unspecified_axes():
    torso = DummyImage(500, 1000)
    base_scale = VIRTUAL_HEIGHT / torso.get_height()
    initial_x = 123
    initial_y = 456
    current_zoom = 1.25
    center_x = (initial_x + torso.get_width() * base_scale * current_zoom / 2) / SCALE / VIRTUAL_WIDTH
    center_y = (initial_y + torso.get_height() * base_scale * current_zoom / 2) / SCALE / VIRTUAL_HEIGHT
    game_state = {
        "active_characters": ["momoko"],
        "character_pos": {"momoko": [initial_x, initial_y]},
        "character_zoom": {"momoko": current_zoom},
        "character_expressions": {"momoko": {}},
        "character_torso": {"momoko": "T00"},
        "image_manager": DummyImageManager({("torso", "T00"): torso}),
    }

    _ir_handle_character_shift(
        game_state,
        "momoko",
        {"size": 1.5, "fade": 0},
    )

    assert game_state["character_pos"]["momoko"] == _expected_position(500, 1000, center_x, center_y, 1.5)
    assert game_state["character_zoom"]["momoko"] == 1.5
