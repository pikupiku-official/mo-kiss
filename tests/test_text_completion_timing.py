from dialogue.inline_markup import parse_inline_markup, total_base_chars
from dialogue.text_renderer import TextRenderer
from dialogue import controller2


def _renderer(text, displayed_chars=0):
    renderer = TextRenderer.__new__(TextRenderer)
    renderer.current_text = text
    renderer._current_tokens = parse_inline_markup(text)
    renderer._total_base_chars = total_base_chars(renderer._current_tokens)
    renderer.displayed_chars = displayed_chars
    renderer.last_char_time = 0
    renderer.char_delay = 100
    renderer.is_text_complete = False
    renderer.text_complete_time = 0
    renderer.punctuation_delay = 500
    renderer.punctuation_waiting = False
    renderer.punctuation_wait_start = 0
    renderer.paragraph_transition_delay = 1000
    renderer.paragraph_transition_waiting = False
    renderer.paragraph_transition_start = 0
    renderer.scroll_just_ended = False
    renderer.auto_mode = False
    renderer.skip_mode = False
    renderer.is_ready_for_next = False
    renderer.auto_ready_logged = False
    renderer.debug = False
    return renderer


def test_last_character_and_input_wait_become_ready_in_the_same_update(monkeypatch):
    renderer = _renderer("終）", displayed_chars=1)
    monkeypatch.setattr("pygame.time.get_ticks", lambda: 100)

    renderer.update()

    assert renderer.displayed_chars == 2
    assert renderer.is_text_complete is True
    assert renderer.is_displaying() is False
    assert renderer.punctuation_waiting is False
    assert renderer.text_complete_time == 100


def test_click_after_last_character_advances_instead_of_being_consumed(monkeypatch):
    renderer = _renderer("終）", displayed_chars=1)
    renderer.scroll_manager = type(
        "Scroll", (), {"is_scroll_mode": lambda self: False}
    )()
    monkeypatch.setattr("pygame.time.get_ticks", lambda: 100)
    renderer.update()

    advanced = []
    monkeypatch.setattr(
        controller2,
        "advance_to_next_dialogue",
        lambda game_state: advanced.append(True) or True,
    )
    game_state = {
        "text_renderer": renderer,
        "backlog_manager": type(
            "Backlog", (), {"is_showing_backlog": lambda self: False}
        )(),
        "choice_renderer": type(
            "Choices", (), {"is_choice_showing": lambda self: False}
        )(),
        "show_text": True,
        "use_ir": False,
    }

    controller2.handle_enter_key(game_state)

    assert advanced == [True]


def test_period_does_not_pause_before_a_closing_parenthesis(monkeypatch):
    renderer = _renderer("。）")
    ticks = iter((100, 200))
    monkeypatch.setattr("pygame.time.get_ticks", lambda: next(ticks))

    renderer.update()
    assert renderer.displayed_chars == 1
    assert renderer.punctuation_waiting is False

    renderer.update()
    assert renderer.displayed_chars == 2
    assert renderer.is_text_complete is True
    assert renderer.punctuation_waiting is False


def test_internal_parenthetical_sentence_pauses_after_the_closer(monkeypatch):
    renderer = _renderer("。）次")
    ticks = iter((100, 200))
    monkeypatch.setattr("pygame.time.get_ticks", lambda: next(ticks))

    renderer.update()
    assert renderer.punctuation_waiting is False

    renderer.update()
    assert renderer.displayed_chars == 2
    assert renderer.punctuation_waiting is True


def test_final_period_does_not_delay_input_wait(monkeypatch):
    renderer = _renderer("終。", displayed_chars=1)
    monkeypatch.setattr("pygame.time.get_ticks", lambda: 100)

    renderer.update()

    assert renderer.is_text_complete is True
    assert renderer.punctuation_waiting is False
