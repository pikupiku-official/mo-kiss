from dialogue.text_renderer import select_current_line_set
from dialogue.text_renderer import TextRenderer
from dialogue.inline_markup import parse_inline_markup, total_base_chars
from dialogue.scroll_manager import ScrollManager


def test_line_sets_clear_together_when_fourth_line_arrives():
    assert select_current_line_set(["1", "2", "3"], 3) == ["1", "2", "3"]
    assert select_current_line_set(["1", "2", "3", "4"], 3) == ["4"]
    assert select_current_line_set(["1", "2", "3", "4", "5", "6"], 3) == [
        "4",
        "5",
        "6",
    ]
    assert select_current_line_set(
        ["1", "2", "3", "4", "5", "6", "7"], 3
    ) == ["7"]


def test_scroll_manager_starts_new_set_before_a_dialogue_that_will_not_fit():
    manager = ScrollManager()
    manager.start_scroll_mode("A", "one-line", display_line_count=1)
    manager.add_text_to_scroll("three-line", "B", display_line_count=3)

    assert manager.get_scroll_lines() == ["three-line"]
    assert manager.get_line_speakers_info()["speakers"] == ["B"]
    assert manager.all_scroll_text == ["one-line", "three-line"]


def test_scroll_manager_keeps_dialogues_together_when_they_fit():
    manager = ScrollManager()
    manager.start_scroll_mode("A", "one-line", display_line_count=1)
    manager.add_text_to_scroll("two-line", "B", display_line_count=2)

    assert manager.get_scroll_lines() == ["one-line", "two-line"]
    assert manager.current_set_line_count == 3


def test_scroll_manager_bounds_visible_work_to_the_current_set():
    manager = ScrollManager()
    manager.start_scroll_mode("A", "0")

    for index in range(1, 100):
        manager.add_text_to_scroll(str(index), "A")

    assert manager.get_scroll_lines() == ["99"]
    assert len(manager.all_scroll_text) == 100


def test_text_renderer_reserves_the_completed_dialogue_line_count_up_front():
    captured = {}

    class ScrollSpy:
        def is_scroll_mode(self):
            return True

        def add_text_to_scroll(self, *args):
            captured["args"] = args

    renderer = TextRenderer.__new__(TextRenderer)
    renderer.debug = False
    renderer.name_manager = type(
        "Names", (), {"substitute_variables": lambda self, value: value or ""}
    )()
    renderer.seed_manager = None
    renderer.seed_event_id = None
    renderer.backlog_added_for_current = True
    renderer.scroll_manager = ScrollSpy()
    renderer.max_display_lines = 3
    renderer._wrap_text = lambda text: ["a", "b", "c"]
    renderer.reset_auto_timer = lambda: None

    renderer.set_dialogue("a full three-line dialogue", "A")

    assert captured["args"][3:] == (3, 3)


def test_normal_dialogue_renderer_draws_only_the_new_set():
    drawn = []
    renderer = TextRenderer.__new__(TextRenderer)
    renderer.current_text = "1234"
    renderer.current_character_name = ""
    renderer.current_force_female = False
    renderer._current_tokens = parse_inline_markup(renderer.current_text)
    renderer.displayed_chars = total_base_chars(renderer._current_tokens)
    renderer.max_display_lines = 3
    renderer.text_color = (255, 255, 255)
    renderer.text_color_female = (255, 200, 255)
    renderer.text_start_x = 0
    renderer.text_start_y = 0
    renderer.text_line_height = 1
    renderer.ruby_h = 0
    renderer.seed_hit_rects = []
    renderer.debug = False
    renderer.scroll_manager = type(
        "Scroll", (), {"is_scroll_mode": lambda self: False}
    )()
    renderer.screen = type("Screen", (), {"blit": lambda self, surface, pos: None})()
    renderer._wrap_text = lambda text: ["1", "2", "3", "4"]
    renderer._render_stable_text_line = lambda line, color: drawn.append(line) or object()
    renderer._record_seed_hit_rects = lambda *args: None

    renderer.render_paragraph()

    assert drawn == ["4"]


def test_scroll_dialogue_renderer_draws_only_the_new_set():
    drawn = []
    renderer = TextRenderer.__new__(TextRenderer)
    renderer.current_text = "4"
    renderer.is_text_complete = True
    renderer._current_tokens = parse_inline_markup(renderer.current_text)
    renderer.displayed_chars = 1
    renderer.max_display_lines = 3
    renderer.text_color = (255, 255, 255)
    renderer.text_color_female = (255, 200, 255)
    renderer.text_start_x = 0
    renderer.text_start_y = 0
    renderer.text_line_height = 1
    renderer.ruby_h = 0
    renderer.seed_hit_rects = []
    renderer.debug = False
    renderer.scroll_manager = type(
        "Scroll",
        (),
        {
            "get_scroll_lines": lambda self: ["1", "2", "3", "4"],
            "get_line_speakers_info": lambda self: {
                "speakers": [None, None, None, None],
                "is_first": [False, False, False, False],
                "force_female": [False, False, False, False],
            },
        },
    )()
    renderer.screen = type("Screen", (), {"blit": lambda self, surface, pos: None})()
    renderer._wrap_text = lambda text: [text]
    renderer._render_stable_text_line = lambda line, color: drawn.append(line) or object()
    renderer._record_seed_hit_rects = lambda *args: None

    renderer.render_scroll_text()

    assert drawn == ["4"]
