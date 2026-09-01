import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pygame

from dialogue.backlog_manager import BacklogManager


class _ScrollManager:
    def __init__(self):
        self.scroll_mode = False
        self.scroll_lines = []

    def is_scroll_mode(self):
        return self.scroll_mode

    def get_scroll_lines(self):
        return self.scroll_lines.copy()


class _Renderer:
    def __init__(self, screen):
        self.screen = screen
        self.current_text = "現在の会話"
        self.current_character_name = "現在"
        self.current_force_female = False
        self.max_chars_per_line = 20
        self.max_display_lines = 3
        self.text_line_height = 50
        self.text_start_x = 298
        self.text_start_y = 798
        self.name_start_x = 95
        self.ruby_h = 0
        self.hovered_seed_id = "seed"
        self.scroll_manager = _ScrollManager()
        self.skip_calls = 0
        self.resumed_ms = None

    def skip_text(self):
        self.skip_calls += 1

    def resume_after_backlog(self, paused_ms):
        self.resumed_ms = paused_ms

    def get_current_dialogue_last_line_y(self):
        if not self.scroll_manager.is_scroll_mode():
            return self.text_start_y
        latest_index = max(0, len(self.scroll_manager.get_scroll_lines()) - 1)
        return self.text_start_y + latest_index * self.text_line_height

    @staticmethod
    def _render_name_with_grid_system(name, color):
        surface = pygame.Surface((120, 30), pygame.SRCALPHA)
        surface.fill((*color, 255))
        return surface

    @staticmethod
    def _render_stable_text_line(text, color):
        surface = pygame.Surface((300, 30), pygame.SRCALPHA)
        surface.fill((*color, 255))
        return surface


def _manager():
    pygame.init()
    screen = pygame.Surface((1440, 1080))
    manager = BacklogManager(screen, debug=False)
    renderer = _Renderer(screen)
    manager.set_text_renderer(renderer)
    return manager, renderer, screen


def test_open_completes_current_line_and_anchors_it_at_normal_position():
    manager, renderer, _ = _manager()
    manager.add_entry("過去", "過去の会話")
    manager.add_entry("現在", "現在の会話")

    manager.open_backlog()
    layout = manager._layout_entries()

    assert renderer.skip_calls == 1
    assert renderer.hovered_seed_id is None
    assert layout[-1]["entry"]["text"] == "現在の会話"
    assert layout[-1]["y"] == renderer.text_start_y
    assert manager.scroll_offset == 0


def test_open_keeps_latest_scroll_dialogue_on_its_second_row():
    manager, renderer, _ = _manager()
    renderer.current_character_name = "B"
    renderer.current_text = "current"
    renderer.scroll_manager.scroll_mode = True
    renderer.scroll_manager.scroll_lines = ["old", "current"]
    manager.add_entry("A", "old")
    manager.add_entry("B", "current")

    manager.open_backlog()
    layout = manager._layout_entries()

    assert layout[-2]["y"] == renderer.text_start_y
    assert layout[-1]["y"] == renderer.text_start_y + renderer.text_line_height


def test_layout_discards_blank_rows_and_uses_exact_line_height():
    manager, renderer, _ = _manager()
    renderer.current_text = "second"
    renderer.current_character_name = "B"
    manager.add_entry("A", "\nfirst\n")
    manager.add_entry("B", "second")

    manager.open_backlog()
    layout = manager._layout_entries()

    assert [item["line"] for item in layout] == ["first", "second"]
    assert layout[1]["y"] - layout[0]["y"] == renderer.text_line_height


def test_no_current_text_places_latest_history_on_the_third_row():
    manager, renderer, _ = _manager()
    renderer.current_text = ""
    manager.add_entry("A", "first")
    manager.add_entry("B", "second")
    manager.add_entry("C", "third")

    manager.open_backlog()
    layout = manager._layout_entries()

    assert [item["y"] for item in layout] == [
        renderer.text_start_y,
        renderer.text_start_y + renderer.text_line_height,
        renderer.text_start_y + 2 * renderer.text_line_height,
    ]


def test_no_current_text_bottom_aligns_short_history_to_the_third_row():
    manager, renderer, _ = _manager()
    renderer.current_text = ""
    manager.add_entry("A", "only")

    manager.open_backlog()
    layout = manager._layout_entries()

    assert layout[-1]["y"] == (
        renderer.text_start_y + 2 * renderer.text_line_height
    )


def test_fixed_margin_uses_full_three_line_dialogue_at_both_edges():
    manager, renderer, _ = _manager()

    expected = 1080 - (renderer.text_start_y + 3 * renderer.text_line_height)
    viewport = manager._viewport_rect()

    assert manager._fixed_edge_margin() == expected
    assert viewport.top == expected
    assert 1080 - viewport.bottom == expected


def test_top_clip_reserves_fixed_date_and_weather_hud_area():
    manager, renderer, _ = _manager()
    renderer.date_display_enabled = True
    renderer.date_position = (22, 30)
    renderer.weather_position = (22, 100)
    renderer.date_font = type("Font", (), {"get_height": lambda self: 60})()
    renderer.weather_font = type("Font", (), {"get_height": lambda self: 49})()

    viewport = manager._viewport_rect()

    # Font effects add a six-pixel outline surface around the 49-pixel font;
    # keep a small fixed gap below the resulting weather HUD rectangle.
    assert viewport.top == 163


def test_render_skips_a_dialogue_line_that_crosses_the_top_clip():
    manager, renderer, _ = _manager()
    renderer.current_text = ""
    renderer.date_display_enabled = True
    renderer.date_position = (22, 30)
    renderer.weather_position = (22, 100)
    renderer.date_font = type("Font", (), {"get_height": lambda self: 60})()
    renderer.weather_font = type("Font", (), {"get_height": lambda self: 49})()
    rendered = []
    renderer._render_stable_text_line = (
        lambda line, color: rendered.append(line)
        or pygame.Surface((300, 30), pygame.SRCALPHA)
    )
    for index in range(16):
        manager.add_entry("A", f"line {index}")

    manager.open_backlog()
    manager._render_entries(manager._layout_entries())

    assert "line 0" not in rendered
    assert "line 1" in rendered


def test_scrolling_to_past_moves_current_dialogue_down_and_thumb_up():
    manager, renderer, _ = _manager()
    for index in range(30):
        manager.add_entry(f"話者{index}", f"履歴{index}")
    manager.open_backlog()

    newest_y = manager._layout_entries()[-1]["y"]
    newest_thumb = manager._scrollbar_geometry()["thumb"].top
    manager.page_up()
    older_thumb = manager._scrollbar_geometry()["thumb"].top

    assert manager.scroll_offset > 0
    assert newest_y + manager.scroll_offset > renderer.text_start_y
    assert older_thumb < newest_thumb


def test_render_dims_scene_but_redraws_dialogue_brightly():
    manager, renderer, screen = _manager()
    manager.add_entry(
        renderer.current_character_name,
        renderer.current_text,
        renderer.current_force_female,
    )
    screen.fill((200, 200, 200))
    manager.open_backlog()
    manager.render()

    dimmed = screen.get_at((10, 10))[:3]
    dialogue = screen.get_at((300, 800))[:3]

    assert dimmed[0] < 200
    assert dialogue == (255, 255, 255)


def test_b_toggles_and_page_keys_are_consumed():
    manager, renderer, _ = _manager()
    for index in range(30):
        manager.add_entry("話者", f"履歴{index}")

    assert manager.handle_input(
        pygame.event.Event(pygame.KEYDOWN, key=pygame.K_b)
    )
    assert manager.is_showing_backlog()
    assert manager.handle_input(
        pygame.event.Event(pygame.KEYDOWN, key=pygame.K_PAGEUP)
    )
    assert manager.scroll_offset > 0
    assert manager.handle_input(
        pygame.event.Event(pygame.KEYDOWN, key=pygame.K_b)
    )
    assert not manager.is_showing_backlog()
    assert renderer.resumed_ms is not None


def test_snapshot_contains_only_entries_recorded_by_text_steps():
    manager, renderer, _ = _manager()
    manager.add_entry("A", "recorded")
    renderer.current_text = ""
    renderer.scroll_manager.scroll_mode = True
    manager.open_backlog()

    assert [entry["text"] for entry in manager._visible_entries] == ["recorded"]


def test_scroll_stop_does_not_write_the_recorded_sequence_again():
    from dialogue.scroll_manager import ScrollManager

    manager, _, _ = _manager()
    renderer = type(
        "Renderer",
        (),
        {
            "backlog_manager": manager,
            "set_scroll_ended_flag": lambda self: None,
        },
    )()
    scroll = ScrollManager(debug=False)
    scroll.set_text_renderer(renderer)
    scroll.scroll_mode = True
    manager.add_entry("A", "one")
    manager.add_entry("B", "two")

    scroll.process_scroll_stop_command()

    assert [entry["text"] for entry in manager.entries] == ["one", "two"]
    assert not scroll.is_scroll_mode()


def test_e001_identical_lines_and_six_empty_steps_keep_exact_history():
    from pathlib import Path

    from dialogue.data_normalizer import normalize_dialogue_data
    from dialogue.dialogue_loader import DialogueLoader
    from dialogue.ir_builder import build_ir_from_normalized
    from dialogue.scroll_manager import ScrollManager
    from dialogue.text_renderer import TextRenderer

    source = Path("events/E001.ks").read_text(encoding="utf-8-sig")
    ir = build_ir_from_normalized(
        normalize_dialogue_data(DialogueLoader()._parse_ks_content(source))
    )
    steps = ir["steps"]
    assert all(steps[index].get("standalone") for index in range(9, 15))

    manager, _, _ = _manager()
    renderer = TextRenderer.__new__(TextRenderer)
    renderer.debug = False
    renderer.name_manager = manager.name_manager
    renderer.seed_manager = None
    renderer.seed_event_id = None
    renderer.backlog_manager = manager
    renderer.scroll_manager = ScrollManager(debug=False)
    renderer.scroll_manager.set_text_renderer(renderer)
    renderer.max_chars_per_line = 20
    renderer.max_display_lines = 3
    renderer.reset_auto_timer = lambda: None

    for step in steps[:9]:
        text = step["text"]
        renderer.set_dialogue(
            text["body"],
            text.get("speaker"),
            should_scroll=bool(text.get("scroll", False)),
            force_female=bool(text.get("force_female", False)),
        )

    assert len(manager.entries) == 9
    assert manager.entries[0]["text"] == manager.entries[1]["text"]

    for _ in steps[9:15]:
        renderer.set_dialogue("", "")

    assert len(manager.entries) == 9
    assert [entry["text"] for entry in manager._snapshot_entries()] == [
        entry["text"] for entry in manager.entries
    ]


def test_resume_after_backlog_shifts_active_text_timers():
    from dialogue.text_renderer import TextRenderer

    renderer = TextRenderer.__new__(TextRenderer)
    renderer.last_char_time = 100
    renderer.punctuation_wait_start = 200
    renderer.paragraph_transition_start = 0
    renderer.text_complete_time = 300

    renderer.resume_after_backlog(50)

    assert renderer.last_char_time == 150
    assert renderer.punctuation_wait_start == 250
    assert renderer.paragraph_transition_start == 0
    assert renderer.text_complete_time == 350


def test_controller_routes_b_and_blocks_gameplay_keys_while_open():
    from dialogue.controller2 import handle_events

    manager, renderer, screen = _manager()
    choices = type(
        "Choices",
        (),
        {
            "is_choice_showing": lambda self: False,
            "handle_mouse_motion": lambda self, pos: None,
        },
    )()
    game_state = {
        "backlog_manager": manager,
        "choice_renderer": choices,
        "text_renderer": renderer,
        "show_text": True,
        "ks_finished": False,
    }

    pygame.event.clear()
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_b))
    assert handle_events(game_state, screen)
    assert manager.is_showing_backlog()

    # A would call toggle_auto_mode on the deliberately minimal renderer if
    # it leaked through the backlog input gate.
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_a))
    assert handle_events(game_state, screen)
    assert manager.is_showing_backlog()

    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_b))
    assert handle_events(game_state, screen)
    assert not manager.is_showing_backlog()
