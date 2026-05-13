"""
tests/test_build_display_string.py
build_display_string / get_logical_char / total_base_chars の単体テスト

実行方法:
    cd "c:\\Users\\kohet\\モーキス作業ディレクトリ"
    python -m pytest tests/test_build_display_string.py -v
"""
import sys, os
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from dialogue.inline_markup import (
    parse_inline_markup,
    build_display_string,
    get_logical_char,
    total_base_chars,
)


# ─── total_base_chars ─────────────────────────────────────────────────────

def test_total_plain():
    assert total_base_chars(parse_inline_markup("abc")) == 3

def test_total_ruby():
    # {愛沼|あいぬま} → base=2文字
    assert total_base_chars(parse_inline_markup("{愛沼|あいぬま}")) == 2

def test_total_boten():
    # {boten:絶対} → base=2文字
    assert total_base_chars(parse_inline_markup("{boten:絶対}")) == 2

def test_total_mixed():
    # 私(1) + {愛沼|あいぬま}(2) + は(1) = 4
    assert total_base_chars(parse_inline_markup("私{愛沼|あいぬま}は")) == 4


# ─── get_logical_char ────────────────────────────────────────────────────

def test_get_logical_plain():
    tokens = parse_inline_markup("abc")
    assert get_logical_char(tokens, 0) == 'a'
    assert get_logical_char(tokens, 1) == 'b'
    assert get_logical_char(tokens, 2) == 'c'

def test_get_logical_ruby_base():
    tokens = parse_inline_markup("{愛沼|あいぬま}")
    assert get_logical_char(tokens, 0) == '愛'
    assert get_logical_char(tokens, 1) == '沼'

def test_get_logical_boten_base():
    tokens = parse_inline_markup("{boten:絶対}")
    assert get_logical_char(tokens, 0) == '絶'
    assert get_logical_char(tokens, 1) == '対'

def test_get_logical_mixed():
    tokens = parse_inline_markup("私{愛沼|あいぬま}は")
    assert get_logical_char(tokens, 0) == '私'
    assert get_logical_char(tokens, 1) == '愛'
    assert get_logical_char(tokens, 2) == '沼'
    assert get_logical_char(tokens, 3) == 'は'

def test_get_logical_out_of_range():
    tokens = parse_inline_markup("a")
    assert get_logical_char(tokens, 99) == '\x00'


# ─── build_display_string ────────────────────────────────────────────────

class TestBuildDisplayString:

    def test_plain_partial(self):
        """平文の途中まで表示"""
        tokens = parse_inline_markup("あいう")
        assert build_display_string(tokens, 0) == ""
        assert build_display_string(tokens, 1) == "あ"
        assert build_display_string(tokens, 2) == "あい"
        assert build_display_string(tokens, 3) == "あいう"

    def test_ruby_no_ruby_until_complete(self):
        """ルビはベース文字が全部出るまでルビなし"""
        tokens = parse_inline_markup("{愛沼|あいぬま}")
        # 1文字目だけ → ルビなし
        assert build_display_string(tokens, 1) == "愛"
        # 全部 → ルビ付き
        assert build_display_string(tokens, 2) == "{愛沼|あいぬま}"

    def test_ruby_appears_on_last_base_char(self):
        """最後のベース文字が出た瞬間にルビが付く"""
        tokens = parse_inline_markup("私{愛沼|あいぬま}は")
        # 私 + 愛（途中）
        assert build_display_string(tokens, 2) == "私愛"
        # 私 + 愛沼（完了） → ルビ付き
        assert build_display_string(tokens, 3) == "私{愛沼|あいぬま}"
        # 全部
        assert build_display_string(tokens, 4) == "私{愛沼|あいぬま}は"

    def test_boten_one_by_one(self):
        """傍点は1文字ずつ付与"""
        tokens = parse_inline_markup("{boten:絶対に}")
        assert build_display_string(tokens, 0) == ""
        assert build_display_string(tokens, 1) == "{boten:絶}"
        assert build_display_string(tokens, 2) == "{boten:絶}{boten:対}"
        assert build_display_string(tokens, 3) == "{boten:絶}{boten:対}{boten:に}"

    def test_boten_single_char(self):
        """傍点1文字"""
        tokens = parse_inline_markup("{boten:強}")
        assert build_display_string(tokens, 1) == "{boten:強}"

    def test_mixed_ruby_boten_plain(self):
        """ルビ・傍点・平文の混在"""
        tokens = parse_inline_markup("{AB|ab}{boten:CD}e")
        # {AB|ab}=2, {boten:CD}=2, e=1 → total=5
        assert build_display_string(tokens, 0) == ""
        assert build_display_string(tokens, 1) == "A"             # ruby途中
        assert build_display_string(tokens, 2) == "{AB|ab}"       # ruby完了
        assert build_display_string(tokens, 3) == "{AB|ab}{boten:C}"
        assert build_display_string(tokens, 4) == "{AB|ab}{boten:C}{boten:D}"
        assert build_display_string(tokens, 5) == "{AB|ab}{boten:C}{boten:D}e"

    def test_zero_count(self):
        assert build_display_string(parse_inline_markup("テスト"), 0) == ""

    def test_full_count_equals_total(self):
        """display_count == total_base_chars で完全な文字列"""
        text = "私の{名前|なまえ}は{boten:重要}です"
        tokens = parse_inline_markup(text)
        total = total_base_chars(tokens)
        result = build_display_string(tokens, total)
        # ルビ・傍点が全部付いている
        assert "{名前|なまえ}" in result
        assert "{boten:重}" in result
        assert "{boten:要}" in result

    def test_ruby_single_base_char(self):
        """ベース1文字のルビ → 1文字目（=全体）出た瞬間にルビ付く"""
        tokens = parse_inline_markup("{山|やま}")
        assert build_display_string(tokens, 1) == "{山|やま}"
