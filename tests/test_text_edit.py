import pygame

from core.ui.text_edit import TextEditBuffer


def key(key, mod=0):
    return pygame.event.Event(pygame.KEYDOWN, key=key, mod=mod)


def test_editor_inserts_at_cursor_and_replaces_selection():
    editor = TextEditBuffer("abcdef", max_length=20)
    editor.set_cursor(2)
    editor.handle_event(pygame.event.Event(pygame.TEXTINPUT, text="X"))
    assert editor.text == "abXcdef"
    assert editor.cursor == 3

    editor.set_cursor(1)
    editor.set_cursor(4, selecting=True)
    editor.handle_event(pygame.event.Event(pygame.TEXTINPUT, text="日"))
    assert editor.text == "a日def"


def test_editor_supports_navigation_selection_and_delete():
    editor = TextEditBuffer("abcdef")
    editor.handle_event(key(pygame.K_LEFT))
    editor.handle_event(key(pygame.K_LEFT, pygame.KMOD_SHIFT))
    assert editor.selection == (4, 5)
    editor.handle_event(key(pygame.K_DELETE))
    assert editor.text == "abcdf"
    editor.handle_event(key(pygame.K_HOME))
    editor.handle_event(key(pygame.K_DELETE))
    assert editor.text == "bcdf"


def test_editor_enforces_seed_limit_on_commit_and_paste(monkeypatch):
    editor = TextEditBuffer("1234", max_length=5)
    editor.handle_event(pygame.event.Event(pygame.TEXTINPUT, text="567"))
    assert editor.text == "12345"

    editor.set_text("12")
    monkeypatch.setattr("core.ui.text_edit._read_clipboard", lambda: "34567")
    editor.handle_event(key(pygame.K_v, pygame.KMOD_CTRL))
    assert editor.text == "12345"


def test_editor_leaves_enter_and_backspace_to_active_ime():
    editor = TextEditBuffer("確定済み")
    editor.handle_event(
        pygame.event.Event(
            pygame.TEXTEDITING,
            text="へんかん",
            start=2,
            length=2,
        )
    )
    assert editor.handle_event(key(pygame.K_RETURN)) is None
    assert editor.handle_event(key(pygame.K_BACKSPACE)) is None
    assert editor.text == "確定済み"
    assert editor.composition == "へんかん"


def test_editor_moves_vertically_in_fixed_width_input():
    editor = TextEditBuffer("あ" * 50)
    editor.set_cursor(25)
    editor.move_vertical(20, -1)
    assert editor.cursor == 5
    editor.move_vertical(20, 1)
    assert editor.cursor == 25
