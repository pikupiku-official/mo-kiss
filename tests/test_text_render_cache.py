import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pygame
import pytest

from core.config import FONT_EFFECTS
from dialogue.text_renderer import TextRenderer


@pytest.fixture
def renderer():
    pygame.init()
    pygame.display.set_mode((100, 100))
    yield TextRenderer.__new__(TextRenderer)
    pygame.quit()


def test_unchanged_glyph_does_not_repeat_font_scaling(renderer, monkeypatch):
    font = pygame.font.Font(None, 32)
    calls = []
    scale = pygame.transform.smoothscale

    def tracked(*args, **kwargs):
        calls.append(True)
        return scale(*args, **kwargs)

    monkeypatch.setattr(pygame.transform, "smoothscale", tracked)
    first = renderer._render_text_with_effects(font, "a", (255, 255, 255))
    count = len(calls)
    assert count > 0
    for _ in range(10):
        result = renderer._render_text_with_effects(font, "a", (255, 255, 255))
        assert pygame.image.tostring(result, "RGBA") == pygame.image.tostring(first, "RGBA")
    assert len(calls) == count


def test_font_effect_and_color_changes_do_not_reuse_stale_pixels(renderer, monkeypatch):
    font = pygame.font.Font(None, 32)
    first = renderer._render_text_with_effects(font, "a", (255, 255, 255))
    colored = renderer._render_text_with_effects(font, "a", (255, 0, 0))
    assert colored is not first
    monkeypatch.setitem(FONT_EFFECTS, "enable_shadow", not FONT_EFFECTS["enable_shadow"])
    changed = renderer._render_text_with_effects(font, "a", (255, 255, 255))
    assert changed is not first
