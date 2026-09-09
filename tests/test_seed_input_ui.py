from concurrent.futures import Future
from types import SimpleNamespace

import pygame

from core.config import SEED_INPUT_CONFIG, TEXT_COLOR
from core.ui.debug_hud import DebugHud
from core.ui.text_edit import TextEditBuffer
from dialogue.seed_answer_overlay import SeedAnswerOverlay
from dialogue.seed_list_overlay import SeedListOverlay


def test_seed_input_keeps_prompt_fixed_and_scrolls_two_answer_rows():
    overlay = SeedAnswerOverlay.__new__(SeedAnswerOverlay)
    overlay.editor = TextEditBuffer("あ" * 45, max_length=120)
    overlay.editor.set_cursor(45)

    cells, first_index, caret_index = overlay._viewport()

    assert first_index == 20
    assert caret_index == 45
    assert len(cells) == 25
    assert SEED_INPUT_CONFIG["prompt_lines"] == 1
    assert SEED_INPUT_CONFIG["input_lines"] == 2


def test_seed_input_caps_committed_text_at_configured_length():
    overlay = SeedAnswerOverlay.__new__(SeedAnswerOverlay)
    overlay.editor = TextEditBuffer("あ" * 119, max_length=120)
    overlay.suspended = False
    overlay.cursor_visible = True
    overlay.last_blink = 0
    overlay._changed_at = 0
    overlay.last_verdict = None

    overlay.handle_event(pygame.event.Event(pygame.TEXTINPUT, text="いう"))

    assert len(overlay.text) == 120
    assert overlay.text.endswith("い")


def test_seed_input_home_end_follow_the_visual_wrapped_line():
    overlay = SeedAnswerOverlay.__new__(SeedAnswerOverlay)
    overlay.editor = TextEditBuffer("あ" * 45, max_length=120)
    overlay.suspended = False
    overlay.cursor_visible = True
    overlay.last_blink = 0
    overlay._changed_at = 0
    overlay.last_verdict = None
    overlay.editor.set_cursor(27)

    overlay.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_HOME, mod=0))
    assert overlay.editor.cursor == 20

    overlay.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_END, mod=0))
    assert overlay.editor.cursor == 40

    overlay.handle_event(
        pygame.event.Event(
            pygame.KEYDOWN,
            key=pygame.K_END,
            mod=pygame.KMOD_CTRL,
        )
    )
    assert overlay.editor.cursor == 45


def test_seed_list_uses_authored_masks_and_parent_depth():
    manager = SimpleNamespace(
        seeds={
            "S1": {
                "id": "S1",
                "turning_point_id": "TP",
                "parents": [],
                "journal_text": "取得済み本文",
                "masked_journal_text": "？？本文",
            },
            "S2": {
                "id": "S2",
                "turning_point_id": "TP",
                "parents": ["S1"],
                "journal_text": "秘密の本文",
                "masked_journal_text": "？？の本文",
            },
        },
        state={"acquired": {"S1": {}}},
        _seed_sort_key=lambda seed_id: (seed_id,),
    )
    renderer = SimpleNamespace(_wrap_text=lambda text: [text])
    overlay = SeedListOverlay(pygame.Surface((100, 100)), manager, renderer)

    rows = overlay._display_lines()

    assert rows[0] == ("●取得済み本文", TEXT_COLOR)
    assert rows[1][0] == "　○？？の本文"
    assert rows[1][1] == SEED_INPUT_CONFIG["masked_color"]


def test_debug_hud_contains_seed_diagnostics_and_input_blocking(monkeypatch):
    overlay = SimpleNamespace(debug_lines=lambda: ["MODEL          ready"])
    game_state = {"seed_answer_overlay": overlay}
    app = SimpleNamespace(current_subsystem=SimpleNamespace(game_state=game_state))
    monkeypatch.setattr("dialogue.controller2.is_input_blocked", lambda state: True)

    lines = DebugHud().lines_for(app)

    assert lines == ["INPUT BLOCKED  true", "MODEL          ready"]


def test_debug_preview_discards_a_result_for_stale_input():
    overlay = SeedAnswerOverlay.__new__(SeedAnswerOverlay)
    overlay.editor = TextEditBuffer("新しい入力", max_length=120)
    overlay.suspended = False
    overlay.last_verdict = None
    overlay._diagnostic_text = None
    overlay._diagnostic_future_text = "古い入力"
    overlay._diagnostic_future = Future()
    overlay._diagnostic_future.set_result({"result": "incorrect"})

    overlay.update(debug_enabled=False)

    assert overlay.last_verdict is None
    assert overlay._diagnostic_future is None


def test_dialogue_surface_swap_updates_seed_list_overlay():
    from dialogue.dialogue_subsystem import DialogueSubsystem

    old_surface = pygame.Surface((20, 20))
    virtual_surface = pygame.Surface((20, 20))
    seed_list = SimpleNamespace(screen=old_surface)
    subsystem = DialogueSubsystem.__new__(DialogueSubsystem)
    subsystem.virtual_screen = virtual_surface
    subsystem.game_state = {
        "screen": old_surface,
        "seed_list_overlay": seed_list,
    }

    subsystem._swap_to_virtual_screen()

    assert seed_list.screen is virtual_surface
