"""
tests/test_inline_markup.py
inline_markup モジュールの単体テスト

実行方法:
    cd "c:\\Users\\kohet\\モーキス作業ディレクトリ"
    python -m pytest tests/test_inline_markup.py -v

pygame / PyQt5 不要（純粋な文字列処理のみ）
"""

import sys
import os
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from dialogue.inline_markup import (
    parse_inline_markup,
    count_chars_for_wrap,
    has_inline_markup,
    wrap_markup_text,
    PlainChar, RubySpan, BotenSpan,
)


# ─── parse_inline_markup ──────────────────────────────────────────────────

class TestParseInlineMarkup:

    def test_plain_text(self):
        """平文はすべて PlainChar になる"""
        tokens = parse_inline_markup("こんにちは")
        assert tokens == [
            PlainChar("こ"), PlainChar("ん"), PlainChar("に"),
            PlainChar("ち"), PlainChar("は"),
        ]

    def test_ruby_span(self):
        """ルビ構文は RubySpan になる"""
        tokens = parse_inline_markup("{愛沼|あいぬま}")
        assert len(tokens) == 1
        assert isinstance(tokens[0], RubySpan)
        assert tokens[0].base == "愛沼"
        assert tokens[0].ruby == "あいぬま"

    def test_boten_span(self):
        """傍点構文は BotenSpan になる"""
        tokens = parse_inline_markup("{boten:絶対に}")
        assert len(tokens) == 1
        assert isinstance(tokens[0], BotenSpan)
        assert tokens[0].base == "絶対に"

    def test_mixed_ruby_and_plain(self):
        """{ルビ}と平文が混在する場合"""
        tokens = parse_inline_markup("{愛沼|あいぬま}は来た")
        assert len(tokens) == 4
        assert isinstance(tokens[0], RubySpan)
        assert tokens[0].base == "愛沼"
        assert tokens[1] == PlainChar("は")
        assert tokens[2] == PlainChar("来")
        assert tokens[3] == PlainChar("た")

    def test_mixed_boten_and_plain(self):
        """{傍点}と平文が混在する場合"""
        tokens = parse_inline_markup("彼は{boten:絶対に}来ない")
        # 彼(1) + は(1) + BotenSpan(絶対に)(1) + 来(1) + な(1) + い(1) = 6
        assert len(tokens) == 6
        assert isinstance(tokens[2], BotenSpan)
        assert tokens[2].base == "絶対に"

    def test_multiple_ruby(self):
        """複数のルビが連続する場合"""
        tokens = parse_inline_markup("{A|a}{B|b}")
        assert len(tokens) == 2
        assert isinstance(tokens[0], RubySpan)
        assert isinstance(tokens[1], RubySpan)

    def test_ruby_single_char_base(self):
        """1文字ベースのルビ"""
        tokens = parse_inline_markup("{山|やま}")
        assert tokens == [RubySpan(base="山", ruby="やま")]

    def test_empty_string(self):
        """空文字列"""
        assert parse_inline_markup("") == []

    def test_no_markup(self):
        """マークアップなし = PlainChar のみ"""
        text = "普通の文章です。"
        tokens = parse_inline_markup(text)
        assert all(isinstance(t, PlainChar) for t in tokens)
        assert "".join(t.char for t in tokens) == text

    def test_plain_before_and_after_ruby(self):
        """ルビ前後に平文がある場合"""
        tokens = parse_inline_markup("私の{名前|なまえ}は")
        plain_before = [t for t in tokens[:2]]
        ruby = tokens[2]
        plain_after = tokens[3]
        assert all(isinstance(t, PlainChar) for t in plain_before)
        assert isinstance(ruby, RubySpan)
        assert isinstance(plain_after, PlainChar)

    def test_variable_like_syntax_not_matched(self):
        """{変数} 形式（| なし, boten: なし）は平文として通過"""
        tokens = parse_inline_markup("{苗字}さん")
        # マークアップにマッチしないので全部 PlainChar
        assert all(isinstance(t, PlainChar) for t in tokens)
        text = "".join(t.char for t in tokens)
        assert text == "{苗字}さん"


# ─── count_chars_for_wrap ────────────────────────────────────────────────

class TestCountCharsForWrap:

    def test_plain_only(self):
        tokens = parse_inline_markup("あいうえお")
        assert count_chars_for_wrap(tokens) == 5

    def test_ruby_counts_base(self):
        tokens = parse_inline_markup("{愛沼|あいぬま}")
        assert count_chars_for_wrap(tokens) == 2  # ベース "愛沼" の文字数

    def test_boten_counts_base(self):
        tokens = parse_inline_markup("{boten:絶対に}")
        assert count_chars_for_wrap(tokens) == 3  # ベース "絶対に" の文字数

    def test_mixed(self):
        tokens = parse_inline_markup("あ{BC|bc}で{boten:EF}")
        # あ=1, BC=2, で=1, EF=2 → 合計 6
        assert count_chars_for_wrap(tokens) == 6


# ─── has_inline_markup ────────────────────────────────────────────────────

class TestHasInlineMarkup:

    def test_plain_false(self):
        assert has_inline_markup("普通のテキスト") is False

    def test_ruby_true(self):
        assert has_inline_markup("{山|やま}") is True

    def test_boten_true(self):
        assert has_inline_markup("{boten:強調}") is True

    def test_variable_like_false(self):
        """変数構文はマークアップではない"""
        assert has_inline_markup("{苗字}さん") is False

    def test_empty_false(self):
        assert has_inline_markup("") is False


# ─── wrap_markup_text ────────────────────────────────────────────────────

class TestWrapMarkupText:

    def test_no_wrap_needed(self):
        """max_chars 以内は 1 行"""
        lines = wrap_markup_text("短い文章", 26)
        assert lines == ["短い文章"]

    def test_plain_wrap(self):
        """平文の折り返し"""
        text = "あ" * 30
        lines = wrap_markup_text(text, 26)
        assert len(lines) == 2
        assert len(lines[0]) == 26
        assert len(lines[1]) == 4

    def test_ruby_not_broken(self):
        """ルビトークンが途中で切れない"""
        # 25文字の平文 + 2文字ベースのルビ → ルビはそのまま2行目に
        text = "あ" * 25 + "{AB|ab}"
        lines = wrap_markup_text(text, 26)
        assert len(lines) == 2
        assert lines[0] == "あ" * 25
        assert lines[1] == "{AB|ab}"

    def test_ruby_base_fits_exactly(self):
        """ルビのベースがちょうど収まる場合"""
        text = "あ" * 24 + "{AB|ab}"  # 24 + 2 = 26
        lines = wrap_markup_text(text, 26)
        assert len(lines) == 1
        assert "{AB|ab}" in lines[0]

    def test_boten_not_broken(self):
        """傍点トークンが途中で切れない"""
        text = "あ" * 25 + "{boten:XY}"
        lines = wrap_markup_text(text, 26)
        assert len(lines) == 2
        assert lines[1] == "{boten:XY}"

    def test_newline_paragraph(self):
        """改行コードで段落が分かれる"""
        text = "第1段落\n第2段落"
        lines = wrap_markup_text(text, 26)
        assert "第1段落" in lines
        assert "第2段落" in lines

    def test_empty_line_in_newline(self):
        """\\n\\n は空行を生成"""
        lines = wrap_markup_text("A\n\nB", 26)
        assert "" in lines

    def test_empty_string(self):
        assert wrap_markup_text("", 26) == []

    def test_ruby_base_too_long_for_single_line(self):
        """ルビのベースが max_chars より大きい場合は 1 トークンがそのまま 1 行"""
        # 30文字のルビベース → 1行に収まらないが、トークンなので分割しない
        long_base = "あ" * 30
        text = "{" + long_base + "|よみ}"
        lines = wrap_markup_text(text, 26)
        # 分割不可なので 1 行にまとまる
        assert len(lines) == 1

    def test_mixed_markup_wrap(self):
        """ルビ・傍点・平文が混在した折り返し"""
        # {A|a}=2, {B|b}=2, 平文22文字 → 1行目=26 で収まる
        text = "{AB|ab}{CD|cd}" + "あ" * 22
        lines = wrap_markup_text(text, 26)
        assert len(lines) == 1

        # 27文字目から2行目になるか
        text2 = "{AB|ab}{CD|cd}" + "あ" * 22 + "い"
        lines2 = wrap_markup_text(text2, 26)
        assert len(lines2) == 2
        assert lines2[1] == "い"
