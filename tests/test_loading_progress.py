"""Loading percentages follow completed work and stay scoped to loading."""

import os
from types import SimpleNamespace

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from core.ui import loading_screen
from dialogue.character_images import prepare_character_images


@pytest.fixture
def reports(monkeypatch):
    rows = []
    monkeypatch.setattr(loading_screen, "_loading_screen", SimpleNamespace(
        show=lambda message, progress=None: rows.append((message, progress)),
    ))
    return rows


def test_progress_does_not_regress_or_outlive_its_loading_screen(reports):
    with loading_screen.loading_progress("Loading"):
        loading_screen.report_loading_progress(42.8)
        loading_screen.report_loading_progress(42.9)
        loading_screen.report_loading_progress(10)
        loading_screen.report_loading_progress(88)
    loading_screen.report_loading_progress(50)
    assert reports == [("Loading", percent) for percent in (0, 42, 88, 100)]


def test_failed_load_does_not_report_completion(reports):
    with pytest.raises(ValueError):
        with loading_screen.loading_progress("Loading"):
            loading_screen.report_loading_progress(30)
            raise ValueError("failed load")
    loading_screen.report_loading_progress(70)
    assert reports == [("Loading", 0), ("Loading", 30)]


def test_nested_transition_restores_the_parent_progress(reports):
    with loading_screen.loading_progress("Outer"):
        loading_screen.report_loading_progress(40)
        with loading_screen.loading_progress("Inner"):
            loading_screen.report_loading_progress(80)
        loading_screen.report_loading_progress(60)
    assert reports == [
        ("Outer", 0), ("Outer", 40), ("Inner", 0), ("Inner", 80),
        ("Inner", 100), ("Outer", 60), ("Outer", 100),
    ]


def test_preparing_character_images_reports_intermediate_work(reports):
    source = pygame.Surface((10, 10), pygame.SRCALPHA)
    source.fill((255, 255, 255, 255))
    state = {
        "image_manager": SimpleNamespace(get_image=lambda *args: source),
        "ir_data": {"steps": [{"actions": [{
            "action": "chara_show", "target": "actor",
            "params": {"torso": "body", "eye": "open", "mouth": "smile"},
        }]}]},
    }
    with loading_screen.loading_progress("Loading"):
        prepare_character_images(state)
        # The repeated cached preparation must not restart the percentage.
        prepare_character_images(state)
    percentages = [percent for _, percent in reports]
    assert percentages[0] == 0 and percentages[-1] == 100
    assert percentages == sorted(set(percentages))
    assert len([percent for percent in percentages if 25 < percent < 95]) >= 2
    assert len(state["_character_images"].images) == 3


def test_percentage_is_drawn_below_the_loading_message_and_preserves_quit(monkeypatch):
    pygame.init()
    screen = pygame.display.set_mode((960, 720))
    monkeypatch.setattr(loading_screen, "_loading_screen", None)
    try:
        painter = loading_screen.get_loading_screen(screen)
        painter.show("Loading")
        no_percent = pygame.image.tobytes(screen, "RGB")
        pygame.event.clear()
        pygame.event.post(pygame.event.Event(pygame.QUIT))
        painter.show("Loading", progress=42)
        assert pygame.image.tobytes(screen, "RGB") != no_percent
        expected = painter.font.render("42%", True, painter.text_color)
        message = painter.font.render("Loading", True, painter.text_color)
        message_rect = message.get_rect(center=screen.get_rect().center)
        area = expected.get_rect(midtop=(480, message_rect.bottom + 20))
        composited = pygame.Surface(expected.get_size())
        composited.fill(painter.background_color)
        composited.blit(expected, (0, 0))
        # Compare the actual displayed percent pixels, rather than a render call.
        assert pygame.image.tobytes(screen.subsurface(area), "RGB") == pygame.image.tobytes(composited, "RGB")
        assert pygame.event.peek(pygame.QUIT)
    finally:
        pygame.quit()
