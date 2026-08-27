from pathlib import Path

import pytest

from tools.expression_status import inspect_status_text, set_status_text, write_status


def test_missing_marker_is_implicit_initial():
    assert inspect_status_text("*start\n[bg name=test]\n") == "initial"


def test_insert_marker_after_start_and_preserve_crlf():
    source = "*start\r\n\r\n[text]\r\n"
    updated = set_status_text(source, "ai_draft")
    assert updated == "*start\r\n;@expression-status: ai_draft\r\n\r\n[text]\r\n"


def test_replace_existing_marker():
    source = "*start\n;@expression-status: ai_draft\n"
    assert set_status_text(source, "human_confirmed") == (
        "*start\n;@expression-status: human_confirmed\n"
    )


def test_write_status_preserves_bom_crlf_and_missing_final_newline(tmp_path):
    path = tmp_path / "sample.ks"
    path.write_bytes(b"\xef\xbb\xbf*start\r\n\r\n[text]")

    write_status(path, "human_confirmed")

    assert path.read_bytes() == (
        b"\xef\xbb\xbf*start\r\n"
        b";@expression-status: human_confirmed\r\n\r\n[text]"
    )


@pytest.mark.parametrize(
    "source",
    [
        "*start\n;@expression-status: unknown\n",
        "*start\n;@expression-status: ai_draft\n;@expression-status: human_confirmed\n",
    ],
)
def test_invalid_markers_are_rejected(source):
    with pytest.raises(ValueError):
        inspect_status_text(source)


def test_confirmed_corpus_is_explicit_and_exact():
    events_dir = Path(__file__).resolve().parents[1] / "events"
    confirmed = {
        path.name
        for path in events_dir.glob("*.ks")
        if inspect_status_text(path.read_text(encoding="utf-8-sig")) == "human_confirmed"
    }
    assert confirmed == {"E002.ks", "E003.ks", "E005.ks", "E006.ks", "E008.ks"}
