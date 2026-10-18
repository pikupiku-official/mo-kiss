import pygame
import pytest

from dialogue.inline_markup import parse_inline_markup, total_base_chars
from dialogue.text_renderer import TextRenderer


def _renderer(text="最後の文字"):
    pygame.font.init()
    renderer = TextRenderer.__new__(TextRenderer)
    renderer.screen = pygame.Surface((800, 300), pygame.SRCALPHA)
    renderer.current_text = text
    renderer._current_tokens = parse_inline_markup(text)
    renderer._total_base_chars = total_base_chars(renderer._current_tokens)
    renderer.displayed_chars = renderer._total_base_chars
    renderer.is_text_complete = True
    renderer.auto_mode = False
    renderer.skip_mode = False
    renderer._advance_indicator_started_at = None
    renderer.text_start_x = 50
    renderer.text_start_y = 80
    renderer.text_line_height = 50
    renderer.max_display_lines = 3
    renderer.max_chars_per_line = 20
    renderer.char_spacing = 0
    renderer.text_color = (255, 255, 255)
    renderer.pygame_fonts = {"text": pygame.font.Font(None, 40)}
    renderer.advance_indicator_font = pygame.font.Font(None, 28)
    renderer.scroll_manager = type(
        "Scroll", (), {"is_scroll_mode": lambda self: False}
    )()
    renderer._wrap_text = lambda value: [value[i:i + 20] for i in range(0, len(value), 20)]
    return renderer


def test_indicator_blinks_continuously_at_half_second_intervals():
    renderer = _renderer()

    assert renderer._advance_indicator_is_visible(1000) is True
    assert renderer._advance_indicator_is_visible(1499) is True
    assert renderer._advance_indicator_is_visible(1500) is False
    assert renderer._advance_indicator_is_visible(2000) is True
    assert renderer._advance_indicator_is_visible(2500) is False
    assert renderer._advance_indicator_is_visible(3000) is True
    assert renderer._advance_indicator_is_visible(10000) is True
    assert renderer._advance_indicator_is_visible(10500) is False


def test_indicator_is_hidden_during_typing_auto_and_skip():
    renderer = _renderer()

    renderer.is_text_complete = False
    assert renderer._can_show_advance_indicator() is False
    renderer.is_text_complete = True
    renderer.auto_mode = True
    assert renderer._can_show_advance_indicator() is False
    renderer.auto_mode = False
    renderer.skip_mode = True
    assert renderer._can_show_advance_indicator() is False


def test_indicator_position_follows_the_last_wrapped_line():
    renderer = _renderer("あ" * 23)
    grid_width = renderer.text_grid_width()

    x, y = renderer.get_advance_indicator_position()

    assert x == 50 + 3 * grid_width + 8
    assert y >= 80 + renderer.text_line_height


@pytest.mark.parametrize("text", ["日本語。", "English text.", "中文文本。"])
def test_indicator_position_supports_each_required_language(text):
    renderer = _renderer(text)

    x, y = renderer.get_advance_indicator_position()

    assert x > renderer.text_start_x
    assert y >= renderer.text_start_y


def test_indicator_is_hidden_for_choice_and_input_blocking_animation():
    renderer = _renderer()
    choices = type(
        "Choices", (), {"is_choice_showing": lambda self: True}
    )()
    game_state = {
        "show_text": True,
        "choice_renderer": choices,
        "use_ir": False,
    }
    assert renderer._can_show_advance_indicator(game_state) is False

    choices.is_choice_showing = lambda: False
    game_state.update(
        {
            "use_ir": True,
            "ir_anim_pending": True,
            "ir_active_anims": [{"on_advance": "block"}],
        }
    )
    assert renderer._can_show_advance_indicator(game_state) is False


def test_indicator_is_hidden_while_option_snapshot_is_requested():
    renderer = _renderer()
    game_state = {
        "show_text": True,
        "hide_advance_indicator": True,
        "use_ir": False,
    }

    assert renderer._can_show_advance_indicator(game_state) is False


def test_indicator_is_hidden_as_soon_as_the_event_finishes():
    renderer = _renderer()
    game_state = {
        "show_text": True,
        "ks_finished": True,
        "use_ir": False,
    }

    assert renderer._can_show_advance_indicator(game_state) is False


def test_render_indicator_uses_hard_visibility_and_resets_when_ineligible():
    renderer = _renderer()

    assert renderer.render_advance_indicator(current_time=1000) is True
    assert renderer._advance_indicator_started_at == 1000
    assert renderer.render_advance_indicator(current_time=1500) is False

    renderer.auto_mode = True
    assert renderer.render_advance_indicator(current_time=1600) is False
    assert renderer._advance_indicator_started_at is None

    renderer.auto_mode = False
    assert renderer.render_advance_indicator(current_time=5000) is True
    assert renderer._advance_indicator_started_at == 5000
