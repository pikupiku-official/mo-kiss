from __future__ import annotations

import pygame
import pytest

from core.config import FONT_EFFECTS, SEED_TEXT_COLOR
from dialogue import controller2
from dialogue.dialogue_loader import DialogueLoader
from dialogue.text_renderer import TextRenderer


class _SeedVisibility:
    def __init__(self, visible):
        self.visible = visible

    def can_show(self, seed_id):
        return self.visible


def _renderer(visible=True):
    renderer = TextRenderer.__new__(TextRenderer)
    renderer.pygame_fonts = {
        "text": pygame.font.Font(None, 40),
        "ruby": pygame.font.Font(None, 18),
    }
    renderer.ruby_h = 12
    renderer.char_spacing = 1
    renderer.max_chars_per_line = 26
    renderer.seed_manager = _SeedVisibility(visible)
    renderer.hovered_seed_id = None
    return renderer


def test_visible_seed_uses_configured_water_blue_and_underline(monkeypatch):
    pygame.init()
    pygame.display.set_mode((1, 1))
    monkeypatch.setitem(FONT_EFFECTS, "enable_shadow", False)
    monkeypatch.setitem(FONT_EFFECTS, "enable_pixelated", False)
    monkeypatch.setitem(FONT_EFFECTS, "enable_stretched", False)
    renderer = _renderer(visible=True)

    surface = renderer._render_text_with_grid_system(
        '[seed id="S1"]ABC[/seed]', (255, 255, 255)
    )
    pixels = pygame.surfarray.array3d(surface)
    water_blue_pixels = (
        (pixels[:, :, 0] == SEED_TEXT_COLOR[0])
        & (pixels[:, :, 1] == SEED_TEXT_COLOR[1])
        & (pixels[:, :, 2] == SEED_TEXT_COLOR[2])
    )

    assert int(water_blue_pixels.sum()) > 30
    assert any(int(water_blue_pixels[:, y].sum()) > 25 for y in range(surface.get_height()))


def test_parent_unmet_seed_is_plain_text_without_seed_color(monkeypatch):
    pygame.init()
    pygame.display.set_mode((1, 1))
    monkeypatch.setitem(FONT_EFFECTS, "enable_shadow", False)
    monkeypatch.setitem(FONT_EFFECTS, "enable_pixelated", False)
    monkeypatch.setitem(FONT_EFFECTS, "enable_stretched", False)
    renderer = _renderer(visible=False)

    surface = renderer._render_text_with_grid_system(
        '[seed id="S1"]ABC[/seed]', (255, 255, 255)
    )
    pixels = pygame.surfarray.array3d(surface)

    assert not (
        (pixels[:, :, 0] == SEED_TEXT_COLOR[0])
        & (pixels[:, :, 1] == SEED_TEXT_COLOR[1])
        & (pixels[:, :, 2] == SEED_TEXT_COLOR[2])
    ).any()


class _BranchRenderer:
    def __init__(self, seed_id, lines, scroll=True):
        self.seed_id = seed_id
        self.lines = lines
        self.calls = []
        self.displaying = False
        self.current_text = "クリックしたタネ本文"
        self.current_character_name = "純一"
        self.current_force_female = False
        self.scroll_manager = type(
            "Scroll", (), {"is_scroll_mode": lambda inner: scroll}
        )()

    def seed_at(self, mouse_pos):
        return self.seed_id

    def get_seed_dialogue_lines(self, seed_id):
        return list(self.lines) if seed_id == self.seed_id else []

    def set_dialogue(self, text, speaker, **kwargs):
        self.current_text = text
        self.current_character_name = speaker
        self.current_force_female = bool(kwargs.get("force_female", False))
        self.displaying = True
        self.calls.append((speaker, text, kwargs))

    def is_displaying(self):
        return self.displaying

    def skip_text(self):
        self.displaying = False


def _branch_game_state(renderer):
    return {
        "backlog_manager": type(
            "Backlog",
            (),
            {
                "is_showing_backlog": lambda self: False,
                "add_entry": lambda self, *args: None,
            },
        )(),
        "choice_renderer": type(
            "Choices", (), {"is_choice_showing": lambda self: False}
        )(),
        "show_text": True,
        "text_renderer": renderer,
        "active_characters": [],
    }


def test_seed_dialogue_is_an_ordinary_branch_then_advances_main_story(monkeypatch):
    lines = [
        {"speaker": "主人公", "text": "分岐一行目"},
        {"speaker": "増田", "text": "分岐二行目"},
    ]
    renderer = _BranchRenderer("S1", lines, scroll=True)
    game_state = _branch_game_state(renderer)
    resumed = []
    monkeypatch.setattr(
        controller2,
        "advance_to_next_dialogue",
        lambda state: resumed.append("next-main") or True,
    )

    controller2.handle_mouse_click(game_state, (10, 10), None)
    assert renderer.calls[-1][:2] == ("主人公", "分岐一行目")
    assert renderer.calls[-1][2]["should_scroll"] is True

    renderer.displaying = False
    controller2.handle_enter_key(game_state)
    assert renderer.calls[-1][:2] == ("増田", "分岐二行目")

    renderer.displaying = False
    controller2.handle_enter_key(game_state)
    assert game_state["seed_dialogue_session"] is None
    assert resumed == ["next-main"]
    assert renderer.current_text == "分岐二行目"


@pytest.mark.parametrize(
    ("filename", "seed_id"),
    [
        ("events/TANE_MASUDA_01.ks", "MASUDA_TP1_001"),
        ("events/TANE_MASUDA_02.ks", "MASUDA_TP1_002"),
        ("events/TANE_MASUDA_03.ks", "MASUDA_TP1_003"),
    ],
)
def test_each_masuda_seed_click_draws_its_embedded_ks_dialogue(
    filename, seed_id
):
    """3本ともクリック後にKS内の会話分岐へ通常の本文経路で入る。"""
    loader = DialogueLoader(False)
    dialogue = loader.load_dialogue_from_ks(filename)
    next(
        item for item in dialogue
        if item.get("type") == "dialogue" and f'id="{seed_id}"' in item["text"]
    )
    lines = loader.seed_annotations[seed_id]
    renderer = _BranchRenderer(seed_id, lines, scroll=True)
    game_state = _branch_game_state(renderer)
    controller2.handle_mouse_click(game_state, (120, 100), None)

    assert game_state["seed_dialogue_session"]["seed_id"] == seed_id
    assert renderer.calls[0][:2] == (lines[0]["speaker"], lines[0]["text"])


def test_seed_in_scroll_dialogue_gets_click_hitbox():
    pygame.init()
    pygame.display.set_mode((1, 1))
    renderer = _renderer(visible=True)
    renderer.screen = pygame.Surface((800, 300), pygame.SRCALPHA)
    renderer.text_start_x = 100
    renderer.text_start_y = 80
    renderer.text_line_height = 50
    renderer.max_display_lines = 3
    renderer.text_color = (255, 255, 255)
    renderer.text_color_female = (255, 200, 220)
    renderer.current_text = '[seed id="MASUDA_TP1_001"]温泉を断った[/seed]'
    renderer.is_text_complete = True
    renderer.seed_hit_rects = []
    renderer.scroll_manager = type(
        "Scroll",
        (),
        {
            "get_scroll_lines": lambda self: [renderer.current_text],
            "get_line_speakers_info": lambda self: {
                "speakers": [None],
                "is_first": [False],
                "force_female": [False],
            },
        },
    )()

    renderer.render_scroll_text()

    assert len(renderer.seed_hit_rects) == 1
    hitbox = renderer.seed_hit_rects[0]
    assert hitbox["seed_id"] == "MASUDA_TP1_001"
    assert renderer.seed_at(hitbox["rect"].center) == "MASUDA_TP1_001"


def test_only_latest_scroll_dialogue_seed_gets_click_hitbox():
    pygame.init()
    pygame.display.set_mode((1, 1))
    renderer = _renderer(visible=True)
    renderer.screen = pygame.Surface((800, 300), pygame.SRCALPHA)
    renderer.text_start_x = 100
    renderer.text_start_y = 80
    renderer.text_line_height = 50
    renderer.max_display_lines = 3
    renderer.text_color = (255, 255, 255)
    renderer.text_color_female = (255, 200, 220)
    old_text = '[seed id="OLD"]過去のタネ[/seed]'
    renderer.current_text = '[seed id="LATEST"]最新のタネ[/seed]'
    renderer.is_text_complete = True
    renderer.seed_hit_rects = []
    renderer.scroll_manager = type(
        "Scroll",
        (),
        {
            "get_scroll_lines": lambda self: [old_text, renderer.current_text],
            "get_line_speakers_info": lambda self: {
                "speakers": [None, None],
                "is_first": [False, False],
                "force_female": [False, False],
            },
        },
    )()

    renderer.render_scroll_text()

    assert [item["seed_id"] for item in renderer.seed_hit_rects] == ["LATEST"]


def test_seed_click_starts_branch_even_while_normal_input_is_blocked(monkeypatch):
    renderer = _BranchRenderer(
        "MASUDA_TP1_001",
        [{"speaker": "主人公", "text": "分岐会話"}],
    )
    game_state = _branch_game_state(renderer)
    monkeypatch.setattr(controller2, "is_input_blocked", lambda state: True)

    controller2.handle_mouse_click(game_state, (10, 10), None)

    assert game_state["seed_dialogue_session"]["seed_id"] == "MASUDA_TP1_001"
    assert renderer.current_text == "分岐会話"
