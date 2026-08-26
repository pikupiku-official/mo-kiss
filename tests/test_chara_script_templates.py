from dialogue.dialogue_loader import DialogueLoader
from tools.event_editor_part_templates import CharaPartTemplateStore


def _loader_with_template(tmp_path):
    path = tmp_path / "templates.json"
    CharaPartTemplateStore(path).create(
        "微笑",
        "桃子",
        {
            "torso": "T_SMILE",
            "eye": "E_SMILE",
            "mouth": "M_SMILE",
            "brow": "B_SMILE",
            "cheek": "C_SMILE",
            "effect": "",
            "accessory": "A_SMILE",
        },
        blink=False,
    )
    return DialogueLoader(chara_template_path=path)


def test_chara_show_expands_named_template(tmp_path):
    entry = _loader_with_template(tmp_path)._parse_ks_content(
        '[chara_show name="桃子" template="微笑" x="0.5"]'
    )[0]

    assert entry["torso"] == "T_SMILE"
    assert entry["eye"] == "E_SMILE"
    assert entry["mouth"] == "M_SMILE"
    assert entry["accessory"] == "A_SMILE"
    assert entry["blink"] is False


def test_chara_shift_template_allows_explicit_part_override(tmp_path):
    entry = _loader_with_template(tmp_path)._parse_ks_content(
        '[chara_shift name="桃子" template="微笑" eye="E_OVERRIDE"]'
    )[0]

    assert entry["torso"] == "T_SMILE"
    assert entry["eye"] == "E_OVERRIDE"
    assert entry["mouth"] == "M_SMILE"
    assert entry["effect"] == ""
