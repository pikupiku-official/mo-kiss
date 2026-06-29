from dialogue.backlog_manager import BacklogManager
from dialogue.data_normalizer import normalize_dialogue_data
from dialogue.dialogue_loader import DialogueLoader
from dialogue.ir_builder import build_ir_from_normalized
from event_editor import EventEditorGUI


def _loader():
    loader = DialogueLoader.__new__(DialogueLoader)
    loader.debug = False
    loader.disable_scroll_continue = False
    loader.max_chars_per_line = 26
    return loader


def test_female_tag_is_scoped_to_one_dialogue_line():
    raw = _loader()._parse_ks_content(
        "//？？//\n"
        "「女の子の声」[female]\n"
        "「男の子の声」[scroll-stop]\n"
    )
    dialogues = [entry for entry in raw if entry.get("type") == "dialogue"]

    assert dialogues[0]["character"] == "？？"
    assert dialogues[0]["force_female"] is True
    assert dialogues[1]["character"] == "？？"
    assert dialogues[1]["force_female"] is False


def test_female_tag_survives_normalization_and_ir_conversion():
    raw = _loader()._parse_ks_content("//？？//\n「女の子の声」[female]\n")
    normalized = normalize_dialogue_data(raw)
    dialogue = next(entry for entry in normalized if isinstance(entry, list))

    assert dialogue[12] is True

    ir = build_ir_from_normalized(normalized)
    text = next(step["text"] for step in ir["steps"] if "text" in step)
    assert text == {
        "speaker": "？？",
        "body": "女の子の声",
        "scroll": False,
        "force_female": True,
    }


def test_female_override_selects_female_backlog_colors_for_unknown_speaker():
    manager = BacklogManager.__new__(BacklogManager)
    manager.default_name_color = (255, 255, 255)
    manager.default_text_color = (255, 255, 255)
    manager.female_name_color = (255, 200, 255)
    manager.female_text_color = (255, 200, 255)
    manager.choice_color = (255, 255, 255)

    assert manager.get_character_colors("？？", False) == (
        manager.default_name_color,
        manager.default_text_color,
    )
    assert manager.get_character_colors("？？", True) == (
        manager.female_name_color,
        manager.female_text_color,
    )


def test_step_editor_round_trip_preserves_female_tag():
    source = "//？？//\n「元のセリフ」[female]\n"
    step = EventEditorGUI._parse_steps_from_ks_text(None, source)[0]
    assert step["force_female"] is True

    updated = EventEditorGUI._build_step_update_text(
        None,
        source,
        step,
        "？？",
        "更新したセリフ",
        False,
        True,
        [],
    )
    assert "「更新したセリフ」[female]" in updated
