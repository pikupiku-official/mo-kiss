"""English dialogue contracts, including the actual Pygame drawing paths."""
import json
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from core.config import ENGLISH_FONT_FILENAME, ENGLISH_FONT_SIZE, FONT_EFFECTS, TEXT_COLOR
from core.path_utils import get_font_path
from dialogue.backlog_manager import BacklogManager
from dialogue.font_effects import render_text_with_effects
from dialogue.text_layout import base_characters, build_layout, english_only, sentence_pause_after
from dialogue.text_renderer import TextRenderer


def plain(line):
    return "".join(g.source.char for g in line.glyphs)


def test_english_detection_uses_the_whole_visible_dialogue_not_markup():
    assert english_only(base_characters('[seed id="日本語ID"]An English clue[/seed]'))
    assert english_only(base_characters('"Café, 1999!"'))
    assert not english_only(base_characters('日本語\nEnglish only on this row.'))
    assert not english_only(base_characters('[seed id="ENGLISH_ID"]手掛かり[/seed]'))
    assert not english_only(base_characters('1999...'))


def test_wrap_keeps_words_and_contractions_even_across_seed_boundaries():
    text = 'One don\'t un[seed id="S"]believ[/seed]able finish.'
    layout = build_layout(text, 14, len)
    assert [plain(line) for line in layout.lines] == ["One don't", "unbelievable", "finish."]
    seed = [g.source for line in layout.lines for g in line.glyphs if g.source.seed_id]
    assert "".join(c.char for c in seed) == "believ"
    assert all(c.seed_id == "S" for c in seed)


def test_justification_uses_full_lines_and_preserves_explicit_paragraphs():
    layout = build_layout('One two three four five six\nShort.', 14, len)
    assert [plain(line) for line in layout.lines] == ["One two three", "four five six", "Short."]
    assert layout.lines[0].justified
    assert layout.lines[0].width == 14
    assert not layout.lines[1].justified
    assert not layout.lines[2].justified
    assert layout.lines[1].paragraph_last and layout.lines[2].paragraph_last
    assert layout.lines[0].glyphs[-1].x + layout.lines[0].glyphs[-1].width == 14


def test_wide_spaces_do_not_trigger_left_alignment():
    layout = build_layout('A B impossible', 12, len)
    assert plain(layout.lines[0]) == "A B"
    assert layout.lines[0].justified
    assert layout.lines[0].glyphs[-1].x == 11


def test_quotes_and_decimal_numbers_do_not_split_away_from_their_words():
    layout = build_layout('One "hello" 3.14 end.', 10, len)
    assert [plain(line) for line in layout.lines] == ['One', '"hello"', '3.14 end.']


def test_mixed_text_keeps_grid_and_one_dialogue_classification():
    text = '日本語に Good morning を混ぜる。\nEnglish line stays on the grid.'
    layout = build_layout(text, 15, len)
    assert not layout.english
    assert all(not line.english and not line.justified for line in layout.lines)
    assert any('morning' in plain(line) for line in layout.lines)
    assert all(g.x == i for line in layout.lines for i, g in enumerate(line.glyphs))


def test_long_unbreakable_word_is_not_lost_or_given_inserted_hyphens():
    word = 'Pneumonoultramicroscopicsilicovolcanoconiosis'
    layout = build_layout(word, 10, len)
    assert ''.join(plain(line) for line in layout.lines) == word
    assert all(line.width <= 10 for line in layout.lines)
    assert [g.source.index for line in layout.lines for g in line.glyphs] == list(range(len(word)))


def test_blank_lines_and_original_character_indices_survive_wrapping():
    layout = build_layout('One two\n\nThree four', 8, len)
    assert [plain(line) for line in layout.lines] == ['One two', '', 'Three', 'four']
    assert layout.lines[-1].start == 15
    assert layout.total_chars == len('One two\n\nThree four')


@pytest.mark.parametrize(('text', 'paused'), [
    ('Hello. Next!', [5, 11]),
    ('Really?! Yes.', [7, 12]),
    ('"Go!" Next.', [4, 10]),
    ('Wait... Then.', [6, 12]),
    ('Dr. Smith paid 3.14 dollars. Then left.', [27, 38]),
    ('。）次', [1]),
])
def test_sentence_wait_rules(text, paused):
    assert [i for i in range(len(text)) if sentence_pause_after(text, i)] == paused


@pytest.fixture
def renderer():
    pygame.init()
    screen = pygame.display.set_mode((1440, 1080))
    result = TextRenderer(screen)
    result.seed_manager = type('Seeds', (), {'can_show': lambda self, seed: True})()
    manager = BacklogManager(screen)
    manager.set_text_renderer(result)
    result.set_backlog_manager(manager)
    return result


LONG_TEXT = ('The rain had finally stopped, but the street was still empty. '
             'I could hear footsteps behind me, slow and steady, as though '
             'someone had been waiting there all night. ') * 3


def test_real_font_has_natural_width_and_mixed_text_retains_legacy_font(renderer):
    narrow = renderer._get_text_layout('iii').lines[0].width
    wide = renderer._get_text_layout('WWW').lines[0].width
    assert wide > narrow * 2
    mixed = renderer._get_text_layout('彼は Good morning と言った。')
    assert not mixed.english
    assert all(g.x == i * renderer.text_grid_width()
               for line in mixed.lines for i, g in enumerate(line.glyphs))
    assert renderer._get_text_layout('日本語だけの台詞。') is None


def test_english_glyph_uses_the_same_effects_as_japanese_body_text(renderer):
    line = renderer._get_text_layout('W').lines[0]
    actual = renderer._render_layout_line(line, TEXT_COLOR)
    expected = pygame.Surface(actual.get_size(), pygame.SRCALPHA)
    baseline = renderer.pygame_fonts['text'].get_ascent() - renderer.english_font.get_ascent()
    padding = renderer._layout_glyph_padding()
    margin = renderer._layout_line_render_padding(line)

    class PaddedFont:
        def render(self, text, antialias, color):
            raw = renderer.english_font.render(text, antialias, color)
            surface = pygame.Surface((raw.get_width() + padding * 2,
                                      raw.get_height() + padding * 2), pygame.SRCALPHA)
            surface.blit(raw, (padding, padding))
            return surface

    stretch = FONT_EFFECTS['stretch_factor'] if FONT_EFFECTS['enable_stretched'] else 1
    expected.blit(render_text_with_effects(PaddedFont(), 'W', TEXT_COLOR),
                  (margin - round(padding * stretch),
                   margin + renderer.ruby_h + baseline - padding))
    assert pygame.image.tobytes(actual, 'RGBA') == pygame.image.tobytes(expected, 'RGBA')


@pytest.mark.parametrize('text', ['j', 'g', 'W', 'Å'])
def test_glyph_overflow_survives_processing_and_line_edges(renderer, text):
    line = renderer._get_text_layout(text).lines[0]
    image = renderer._render_layout_line(line, TEXT_COLOR)
    bounds = image.get_bounding_rect()
    margin = renderer._layout_line_render_padding(line)
    # Resampling and the black outline can extend beyond the layout advance.
    # Retain those pixels on both sides, with transparent room outside them.
    assert 0 < bounds.left < margin
    assert margin + line.width < bounds.right < image.get_width()
    assert 0 < bounds.top < bounds.bottom < image.get_height()


@pytest.mark.parametrize('text', ['AV', 'LT', 'Ta', 'ff', 'Th'])
def test_next_letter_outline_does_not_erase_existing_strokes(renderer, text):
    line = renderer._get_text_layout(text).lines[0]
    early = renderer._render_layout_line(line, TEXT_COLOR, 1)
    complete = renderer._render_layout_line(line, TEXT_COLOR)
    checked = 0
    for x in range(early.get_width()):
        for y in range(early.get_height()):
            before = early.get_at((x, y))
            if before.r >= 120 and before.a >= 180:
                after = complete.get_at((x, y))
                assert after.r >= before.r - 3
                checked += 1
    assert checked > 0


def test_english_uses_the_bundled_rounded_gothic_font(renderer):
    assert ENGLISH_FONT_FILENAME == 'MPLUSRounded1c-Medium.ttf'
    rounded = pygame.font.Font(get_font_path('MPLUSRounded1c-Medium.ttf'), ENGLISH_FONT_SIZE)
    text = 'Round glyphs: Good morning!'
    assert pygame.image.tobytes(renderer.english_font.render(text, True, TEXT_COLOR), 'RGBA') == (
        pygame.image.tobytes(rounded.render(text, True, TEXT_COLOR), 'RGBA'))


def test_english_tracking_separates_glyphs_without_adding_a_trailing_gap(renderer):
    renderer.set_char_spacing(0)
    text = 'Minimum width AV fi.'
    tight = renderer._get_text_layout(text).lines[0]
    renderer.set_char_spacing(5)
    spaced = renderer._get_text_layout(text).lines[0]
    assert spaced.width == tight.width + (len(text) - 1) * 5
    for i, (before, after) in enumerate(zip(tight.glyphs, spaced.glyphs)):
        assert after.x == before.x + i * 5
        if not after.source.char.isspace():
            assert after.width == before.width
    assert spaced.glyphs[-1].x + spaced.glyphs[-1].width == spaced.width


def test_english_tracking_changes_word_wrap_and_retains_justified_edges(renderer, monkeypatch):
    text = 'Small words need room for readable letters. ' * 3
    renderer.set_max_chars_per_line(10)
    monkeypatch.setattr(renderer, 'text_grid_width', lambda: 47)
    renderer.set_char_spacing(0)
    tight = renderer._get_text_layout(text)
    renderer.set_char_spacing(8)
    spaced = renderer._get_text_layout(text)
    assert spaced is not tight
    assert [plain(line) for line in spaced.lines] != [plain(line) for line in tight.lines]
    for line in spaced.lines:
        assert line.width <= renderer.text_grid_width() * renderer.max_chars_per_line
        assert line.glyphs[-1].x + line.glyphs[-1].width == line.width
        if line.justified:
            assert line.width == renderer.text_grid_width() * renderer.max_chars_per_line


def test_english_layout_measures_processed_glyph_widths_and_aligned_edges(renderer):
    layout = renderer._get_text_layout(LONG_TEXT)
    for line in layout.lines:
        for glyph in line.glyphs:
            if not glyph.source.char.isspace():
                raw = renderer.english_font.render(glyph.source.char, True, TEXT_COLOR)
                assert glyph.width == renderer._apply_font_effects(raw).get_width()
        assert line.glyphs[-1].x + line.glyphs[-1].width == line.width
        assert line.width <= renderer.text_grid_width() * renderer.max_chars_per_line


def test_shared_pixelation_changes_english_pixels_without_changing_layout(renderer, monkeypatch):
    monkeypatch.setitem(FONT_EFFECTS, 'enable_pixelated', True)
    layout = renderer._get_text_layout('Thin lines and small letters.')
    pixelated = renderer._render_layout_line(layout.lines[0], TEXT_COLOR)
    monkeypatch.setitem(FONT_EFFECTS, 'enable_pixelated', False)
    assert renderer._get_text_layout('Thin lines and small letters.') is layout
    smooth = renderer._render_layout_line(layout.lines[0], TEXT_COLOR)
    assert pygame.image.tobytes(pixelated, 'RGBA') != pygame.image.tobytes(smooth, 'RGBA')


def test_shared_stretch_invalidates_layout_even_when_japanese_grid_width_is_unchanged(
        renderer, monkeypatch):
    monkeypatch.setitem(FONT_EFFECTS, 'enable_stretched', True)
    monkeypatch.setitem(FONT_EFFECTS, 'stretch_factor', 1.0)
    renderer.set_max_chars_per_line(100)
    text = 'The rain had finally stopped, but the street was still empty.'
    first = renderer._get_text_layout(text)
    grid_width = renderer.text_grid_width()
    monkeypatch.setitem(FONT_EFFECTS, 'stretch_factor', 1.001)
    assert renderer.text_grid_width() == grid_width
    second = renderer._get_text_layout(text)
    assert second is not first
    assert second.lines[0].width > first.lines[0].width
    assert second.lines[0].glyphs[-1].x + second.lines[0].glyphs[-1].width == second.lines[0].width


def test_live_typewriter_switches_to_fourth_row_without_early_page_change(renderer, monkeypatch):
    renderer.set_dialogue(LONG_TEXT)
    layout = renderer._get_text_layout(LONG_TEXT)
    assert len(layout.lines) > 3
    drawn = []
    original = renderer._render_layout_line
    def record(line, color, visible_chars=None):
        drawn.append(line)
        return original(line, color, visible_chars)
    monkeypatch.setattr(renderer, '_render_layout_line', record)
    renderer.displayed_chars = layout.lines[3].activation - 1
    renderer.render_paragraph()
    assert drawn == list(layout.lines[:3])
    drawn.clear()
    renderer.displayed_chars += 1
    renderer.render_paragraph()
    assert drawn == [layout.lines[3]]
    assert renderer.is_text_complete is False
    assert renderer._get_text_layout(LONG_TEXT) is layout


def test_earlier_letters_do_not_move_during_typing(renderer):
    renderer.set_dialogue(LONG_TEXT)
    line = renderer._get_text_layout(LONG_TEXT).lines[0]
    early = renderer._render_layout_line(line, TEXT_COLOR, 3)
    completed = renderer._render_layout_line(line, TEXT_COLOR)
    # Everything through the first word precedes the following word by a
    # justified gap. Later characters must not change these rendered pixels.
    right = line.glyphs[3].x
    crop = pygame.Rect(0, 0, right, early.get_height())
    assert pygame.image.tobytes(early.subsurface(crop), 'RGBA') == pygame.image.tobytes(
        completed.subsurface(crop), 'RGBA')


def test_backlog_reuses_whole_dialogue_layout_after_json_roundtrip(renderer):
    text = '日本語と English が混ざる台詞。\nEnglish only on this line.'
    renderer.set_dialogue(text)
    renderer.skip_text()
    manager = renderer.backlog_manager
    manager.entries = json.loads(json.dumps(manager.entries))
    manager.open_backlog()
    rows = manager._history_rows()
    layout = renderer._get_text_layout(text)
    assert [row['layout_line'] for row in rows] == list(layout.lines)
    assert all(not row['layout_line'].english for row in rows)
    manager._render_entries(manager._layout_entries())


def test_backlog_preserves_justification_and_final_paragraph_line(renderer):
    renderer.set_dialogue(LONG_TEXT)
    renderer.skip_text()
    manager = renderer.backlog_manager
    manager.open_backlog()
    rows = manager._history_rows()
    layout = renderer._get_text_layout(LONG_TEXT)
    assert rows[0]['layout_line'].justified
    assert not rows[-1]['layout_line'].justified
    for row, line in zip(rows, layout.lines):
        assert row['layout_line'] is line


def test_seed_hitbox_and_indicator_follow_real_english_glyph_coordinates(renderer):
    text = 'Look for the [seed id="S"]blue envelope[/seed] on the table.'
    renderer.set_dialogue(text)
    renderer.skip_text()
    renderer.render_paragraph()
    layout = renderer._get_text_layout(text)
    line = layout.lines[0]
    seed_glyphs = [g for g in line.glyphs if g.source.seed_id == 'S']
    assert len(renderer.seed_hit_rects) == 1
    rect = renderer.seed_hit_rects[0]['rect']
    assert rect.left == renderer.text_start_x + seed_glyphs[0].x
    assert rect.right == renderer.text_start_x + seed_glyphs[-1].x + seed_glyphs[-1].width
    assert renderer.seed_at(rect.center) == 'S'
    assert renderer.get_advance_indicator_position()[0] == (
        renderer.text_start_x + layout.lines[-1].width + 8)


def test_only_revealed_seed_text_is_clickable(renderer):
    text = 'Find the [seed id="S"]hidden envelope[/seed].'
    renderer.set_dialogue(text)
    glyphs = [g for g in renderer._get_text_layout(text).lines[0].glyphs if g.source.seed_id]
    renderer.displayed_chars = glyphs[0].source.index
    renderer.render_paragraph()
    assert renderer.seed_hit_rects == []
    renderer.displayed_chars += 1
    renderer.render_paragraph()
    assert len(renderer.seed_hit_rects) == 1
    assert renderer.seed_hit_rects[0]['rect'].width == glyphs[0].width


def test_layout_invalidates_after_grid_width_setting_changes(renderer):
    first = renderer._get_text_layout(LONG_TEXT)
    renderer.set_max_chars_per_line(12)
    second = renderer._get_text_layout(LONG_TEXT)
    assert second is not first
    assert len(second.lines) > len(first.lines)


def test_scroll_uses_english_layout_and_only_latest_seeds_are_active(renderer):
    renderer.set_dialogue('Old [seed id="OLD"]envelope[/seed].', 'A')
    renderer.skip_text()
    renderer.set_dialogue('New [seed id="NEW"]letter[/seed].', 'B', should_scroll=True)
    renderer.skip_text()
    renderer.render_scroll_text()
    assert renderer.scroll_manager.is_scroll_mode()
    assert [item['seed_id'] for item in renderer.seed_hit_rects] == ['NEW']
    assert len(renderer.scroll_manager.get_scroll_lines()) == 2


def test_mixed_ruby_and_seed_markup_still_draw_on_legacy_grid(renderer):
    text = '{彼|かれ}は [seed id="S"]blue envelope[/seed] を見た。'
    renderer.set_dialogue(text)
    renderer.skip_text()
    renderer.render_paragraph()
    layout = renderer._get_text_layout(text)
    assert not layout.english
    assert any('blue envelope' in line.markup for line in layout.lines)
    assert renderer.seed_hit_rects
    assert all(renderer.seed_at(item['rect'].center) == 'S'
               for item in renderer.seed_hit_rects)


def test_english_punctuation_uses_existing_delay_and_final_input_timing(renderer, monkeypatch):
    renderer.set_dialogue('First. Second.')
    renderer.last_char_time = 0
    renderer.displayed_chars = 5
    monkeypatch.setattr('pygame.time.get_ticks', lambda: renderer.char_delay)
    renderer.update()
    assert renderer.punctuation_waiting
    assert renderer.punctuation_delay == 500
    renderer.skip_text()
    assert renderer.is_text_complete
    assert not renderer.punctuation_waiting
    renderer.set_dialogue('Final.')
    renderer.last_char_time = 0
    renderer.displayed_chars = 5
    renderer.update()
    assert renderer.is_text_complete
    assert not renderer.punctuation_waiting
