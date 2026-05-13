"""
dialogue/inline_markup.py
ルビ・傍点インラインマークアップ パーサー

対応構文:
  {ベーステキスト|よみ}   ← ルビ
  {boten:対象テキスト}    ← 傍点

呼び出し順: name_manager.substitute_variables() の後に parse_inline_markup() を呼ぶこと。
"""

from __future__ import annotations
import re
from dataclasses import dataclass


# ─── Token 型 ─────────────────────────────────────────────────────────────

@dataclass
class PlainChar:
    """通常の1文字"""
    char: str


@dataclass
class RubySpan:
    """ルビ（振り仮名）スパン"""
    base: str   # ベーステキスト（1文字以上）
    ruby: str   # よみ（1文字以上）


@dataclass
class BotenSpan:
    """傍点スパン"""
    base: str   # 傍点を振るテキスト（1文字以上）


Token = PlainChar | RubySpan | BotenSpan

# ─── 内部定数 ──────────────────────────────────────────────────────────────

# マークアップ認識パターン（ルビ優先、傍点次）
_MARKUP_RE = re.compile(r'\{([^}|]+)\|([^}]+)\}|\{boten:([^}]+)\}')

# 折り返し計算用（マークアップ単位 or 1文字にマッチ）
_WRAP_TOKEN_RE = re.compile(r'\{[^}|]+\|[^}]+\}|\{boten:[^}]+\}|.')


# ─── 公開 API ─────────────────────────────────────────────────────────────

def parse_inline_markup(text: str) -> list[Token]:
    """
    変数置換済みテキストをトークンリストに変換する。

    >>> parse_inline_markup("普通のテキスト")
    [PlainChar(char='普'), PlainChar(char='通'), ...]

    >>> parse_inline_markup("{愛沼|あいぬま}は来た")
    [RubySpan(base='愛沼', ruby='あいぬま'), PlainChar(char='は'), ...]

    >>> parse_inline_markup("{boten:絶対に}")
    [BotenSpan(base='絶対に')]
    """
    tokens: list[Token] = []
    last = 0
    for m in _MARKUP_RE.finditer(text):
        # マッチ前の平文を1文字ずつ追加
        for ch in text[last:m.start()]:
            tokens.append(PlainChar(ch))
        if m.group(1) is not None:
            # ルビ: {base|ruby}
            tokens.append(RubySpan(base=m.group(1), ruby=m.group(2)))
        else:
            # 傍点: {boten:base}
            tokens.append(BotenSpan(base=m.group(3)))
        last = m.end()
    # 末尾の平文
    for ch in text[last:]:
        tokens.append(PlainChar(ch))
    return tokens


def count_chars_for_wrap(tokens: list[Token]) -> int:
    """折り返し計算用のベース文字数を返す"""
    n = 0
    for t in tokens:
        if isinstance(t, PlainChar):
            n += 1
        else:
            n += len(t.base)  # RubySpan / BotenSpan
    return n


def has_inline_markup(text: str) -> bool:
    """テキストにルビまたは傍点マークアップが含まれているか"""
    return bool(_MARKUP_RE.search(text))


def wrap_markup_text(text: str, max_chars: int) -> list[str]:
    """
    マークアップを壊さずに max_chars 文字（ベース文字数）で折り返す。
    改行コード \\n で段落を区切る。
    戻り値は元のマークアップ文字列（ただし max_chars ごとに分割済み）のリスト。
    """
    if not text:
        return []

    result: list[str] = []

    for paragraph in text.split('\n'):
        if not paragraph:
            result.append('')
            continue

        # マークアップ単位または1文字のトークンリストに分割
        raw_tokens = _WRAP_TOKEN_RE.findall(paragraph)
        current_parts: list[str] = []
        current_count = 0

        for tok in raw_tokens:
            base_len = _base_len_of_raw(tok)

            # このトークンを追加すると max_chars を超える場合は改行
            if current_count + base_len > max_chars and current_parts:
                result.append(''.join(current_parts))
                current_parts = []
                current_count = 0

            current_parts.append(tok)
            current_count += base_len

        if current_parts:
            result.append(''.join(current_parts))

    return result


# ─── 内部ユーティリティ ────────────────────────────────────────────────────

def _base_len_of_raw(tok: str) -> int:
    """生トークン文字列のベース文字数を返す"""
    m = _MARKUP_RE.fullmatch(tok)
    if m:
        if m.group(1) is not None:
            return len(m.group(1))   # ルビのベース
        else:
            return len(m.group(3))   # 傍点のベース
    return 1  # 平文1文字

# ─── 文字送り用ユーティリティ ──────────────────────────────────────────────

def total_base_chars(tokens: list) -> int:
    """トークンリストの論理ベース文字数合計（displayed_chars の上限）"""
    return count_chars_for_wrap(tokens)


def get_logical_char(tokens: list, logical_idx: int) -> str:
    """論理インデックス idx の1文字を返す（句読点チェック用）"""
    pos = 0
    for t in tokens:
        if isinstance(t, PlainChar):
            if pos == logical_idx:
                return t.char
            pos += 1
        else:  # RubySpan / BotenSpan
            for ch in t.base:
                if pos == logical_idx:
                    return ch
                pos += 1
    return '\x00'


def build_display_string(tokens: list, display_count: int) -> str:
    """
    display_count 個のベース文字分のトークンを表示用文字列に変換する。

    - PlainChar        : そのまま出力
    - RubySpan         : ベース文字をすべて出力した瞬間にルビ付与、
                         途中まではベース文字のみ（ルビなし）
    - BotenSpan        : 表示済みの各文字に個別で {boten:X} を付与
    """
    result = []
    remaining = display_count

    for token in tokens:
        if remaining <= 0:
            break

        if isinstance(token, PlainChar):
            result.append(token.char)
            remaining -= 1

        elif isinstance(token, RubySpan):
            base_len = len(token.base)
            shown = min(remaining, base_len)
            if shown >= base_len:
                # スパン全体が表示済み → ルビ付き
                result.append(f"{{{token.base}|{token.ruby}}}")
            else:
                # 途中まで → ベース文字のみ
                result.append(token.base[:shown])
            remaining -= shown

        elif isinstance(token, BotenSpan):
            base_len = len(token.base)
            shown = min(remaining, base_len)
            for ch in token.base[:shown]:
                result.append(f"{{boten:{ch}}}")
            remaining -= shown

    return "".join(result)

