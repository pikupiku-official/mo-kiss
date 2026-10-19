"""Full-dialogue layout shared by typewriter text, history and hit testing.

Indices always refer to the original visible base characters (including spaces
and newlines), never to markup or inserted formatting. No hyphens are inserted.
"""

from dataclasses import dataclass
import re
import unicodedata
from typing import Callable

from .inline_markup import PlainChar, RubySpan, BotenSpan, SeedSpan, parse_inline_markup


def is_latin_letter(char: str) -> bool:
    return char.isalpha() and "LATIN" in unicodedata.name(char, "")


@dataclass(frozen=True)
class BaseChar:
    char: str
    index: int
    seed_id: str | None = None
    ruby: str | None = None
    group: int | None = None
    boten: bool = False


@dataclass(frozen=True)
class PlacedChar:
    source: BaseChar
    x: int
    width: int


@dataclass(frozen=True)
class LayoutLine:
    glyphs: tuple[PlacedChar, ...]
    markup: str
    start: int
    end: int
    activation: int
    width: int
    english: bool
    paragraph_last: bool
    justified: bool


@dataclass(frozen=True)
class TextLayout:
    lines: tuple[LayoutLine, ...]
    english: bool
    total_chars: int

    def visible_lines(self, count: int) -> tuple[LayoutLine, ...]:
        # Include an empty first row before typing starts, but never allocate
        # the next page merely because a future word has already been laid out.
        return tuple(line for i, line in enumerate(self.lines)
                     if i == 0 or line.activation <= count)


def base_characters(text: str) -> tuple[BaseChar, ...]:
    result = []
    for group, token in enumerate(parse_inline_markup(text)):
        if isinstance(token, PlainChar):
            result.append(BaseChar(token.char, len(result)))
            continue
        for char in token.base:
            result.append(BaseChar(
                char, len(result),
                seed_id=token.seed_id if isinstance(token, SeedSpan) else None,
                ruby=token.ruby if isinstance(token, RubySpan) else None,
                group=group if isinstance(token, (RubySpan, BotenSpan)) else None,
                boten=isinstance(token, BotenSpan),
            ))
    return tuple(result)


def contains_latin(text: str) -> bool:
    return any(is_latin_letter(c.char) for c in base_characters(text))


def english_only(chars: tuple[BaseChar, ...]) -> bool:
    # Inspect visible text, not seed IDs or ruby readings. Punctuation and
    # numerals do not turn an English dialogue into a mixed-script dialogue.
    return any(is_latin_letter(c.char) for c in chars) and all(
        not c.char.isalpha() or is_latin_letter(c.char) for c in chars
    )


_CLOSERS = frozenset(",.!?;:%-)]}»’”。，、！？：；）］｝」』】")
_OPENERS = frozenset("([{«‘“（［｛「『【")
_APOSTROPHES = frozenset("'’")


def _word_char(char: str) -> bool:
    return is_latin_letter(char) or char.isdecimal() or unicodedata.category(char).startswith("M")


def _units(chars: list[BaseChar]) -> list[list[BaseChar]]:
    units: list[list[BaseChar]] = []
    for i, char in enumerate(chars):
        join = False
        if i:
            prev = chars[i - 1]
            join = char.group is not None and char.group == prev.group
            join |= _word_char(prev.char) and _word_char(char.char)
            join |= (char.char in _APOSTROPHES and _word_char(prev.char)
                     and i + 1 < len(chars) and _word_char(chars[i + 1].char))
            join |= (prev.char in _APOSTROPHES and _word_char(char.char)
                     and i >= 2 and _word_char(chars[i - 2].char))
            join |= char.char in "\"'" and not prev.char.isspace()
            join |= prev.char in "\"'" and not char.char.isspace()
            join |= (char.char == "." and _word_char(prev.char)
                     and i + 1 < len(chars) and _word_char(chars[i + 1].char))
            join |= (prev.char == "." and _word_char(char.char)
                     and i >= 2 and _word_char(chars[i - 2].char))
            join |= char.char in _CLOSERS and not prev.char.isspace()
            join |= prev.char in _OPENERS
            join |= char.char.isspace() and prev.char.isspace()
        if join:
            units[-1].append(char)
        else:
            units.append([char])
    return units


def _markup(chars: list[BaseChar]) -> str:
    result = []
    i = 0
    while i < len(chars):
        first = chars[i]
        j = i + 1
        if first.group is not None:
            while j < len(chars) and chars[j].group == first.group:
                j += 1
        elif first.seed_id:
            while j < len(chars) and chars[j].seed_id == first.seed_id:
                j += 1
        content = "".join(c.char for c in chars[i:j])
        if first.ruby is not None:
            content = "{" + content + "|" + first.ruby + "}"
        elif first.boten:
            content = "{boten:" + content + "}"
        elif first.seed_id:
            content = f'[seed id="{first.seed_id}"]{content}[/seed]'
        result.append(content)
        i = j
    return "".join(result)


def build_layout(text: str, max_width: int, measure: Callable[[str], int],
                 *, english: bool | None = None) -> TextLayout:
    """Greedy word wrap, then justify only non-final English paragraph rows.

    Explicit newlines end paragraphs. An unbreakable word wider than the
    entire box uses emergency character wrapping; it is never cropped, scaled
    down or silently dropped. Ruby/boten groups remain indivisible.
    """
    chars = base_characters(text)
    english = english_only(chars) if english is None else english
    max_width = max(1, int(max_width))
    paragraphs: list[tuple[list[BaseChar], int]] = []
    current: list[BaseChar] = []
    paragraph_start = 0
    for char in chars:
        if char.char == "\n":
            paragraphs.append((current, paragraph_start))
            current = []
            paragraph_start = char.index + 1
        else:
            current.append(char)
    paragraphs.append((current, paragraph_start))

    lines = []
    for paragraph, start in paragraphs:
        rows: list[list[BaseChar]] = []
        row: list[BaseChar] = []
        pending_space: list[BaseChar] = []
        for unit in _units(paragraph):
            if all(c.char.isspace() for c in unit):
                pending_space.extend(unit)
                continue
            candidate = row + pending_space + unit
            if row and measure("".join(c.char for c in candidate)) > max_width:
                rows.append(row)
                row = []
                pending_space = []
            row.extend(pending_space)
            pending_space = []
            if measure("".join(c.char for c in row + unit)) > max_width and all(
                c.group is None for c in unit
            ):
                # Only a token which cannot fit on an otherwise empty row
                # reaches this branch. Normal words always move as a unit.
                for char in unit:
                    if row and measure("".join(c.char for c in row + [char])) > max_width:
                        rows.append(row)
                        row = []
                    row.append(char)
            else:
                row.extend(unit)
        # Unpainted trailing/wrap spaces retain their original indices for
        # timing, but do not push the prompt or alignment past the box edge.
        if row or not rows:
            rows.append(row)

        for row_index, row in enumerate(rows):
            last = row_index == len(rows) - 1
            plain = "".join(c.char for c in row)
            natural_width = measure(plain)
            gaps = [i for i, c in enumerate(row)
                    if c.char.isspace() and any(not x.char.isspace() for x in row[:i])
                    and any(not x.char.isspace() for x in row[i + 1:])]
            justify = english and not last and bool(gaps) and natural_width < max_width
            extra = max_width - natural_width if justify else 0
            placed = []
            gaps_seen = 0
            for i, char in enumerate(row):
                prefix_width = measure(plain[:i])
                end_width = measure(plain[:i + 1])
                # Prefix measurements preserve the font's pair kerning. Using
                # the right edge minus the isolated width also keeps negative
                # kerning from moving an already visible letter later.
                x = end_width - measure(char.char) if english else prefix_width
                offset = round(extra * gaps_seen / len(gaps)) if justify else 0
                before = gaps_seen
                if i in gaps:
                    gaps_seen += 1
                after_offset = round(extra * gaps_seen / len(gaps)) if justify else 0
                width = max(0, end_width - prefix_width + after_offset - offset)
                if before == gaps_seen and english:
                    width = measure(char.char)
                placed.append(PlacedChar(char, x + offset, width))
            activation = row[0].index + 1 if row else start
            lines.append(LayoutLine(
                tuple(placed), _markup(row), row[0].index if row else start,
                row[-1].index + 1 if row else start, activation,
                max_width if justify else natural_width,
                bool(english), last, bool(justify),
            ))
    return TextLayout(tuple(lines), bool(english), len(chars))


_ABBREVIATIONS = frozenset({"mr", "mrs", "ms", "dr", "prof", "sr", "jr", "st", "vs", "etc", "e.g", "i.e"})
_WAIT_CLOSERS = frozenset(")）]］}｝〉》」』】〕〙〗〟'\"’”")


def sentence_pause_after(text: str, index: int) -> bool:
    """A small deterministic punctuation rule; no sentence parser required."""
    if not 0 <= index < len(text):
        return False
    end = index
    while end >= 0 and text[end] in _WAIT_CLOSERS:
        end -= 1
    if end < 0:
        return False
    # Wait once, after a complete punctuation/closing-quote run.
    if index + 1 < len(text) and text[index + 1] in _WAIT_CLOSERS | frozenset(".!?"):
        return False
    char = text[end]
    if char == "。":
        return True
    if char not in ".!?":
        return False
    if char == ".":
        if end and end + 1 < len(text) and text[end - 1].isdigit() and text[end + 1].isdigit():
            return False
        match = re.search(r"([A-Za-z]+(?:\.[A-Za-z]+)*)\.$", text[:end + 1])
        if match:
            word = match.group(1)
            if word.lower() in _ABBREVIATIONS or len(word) == 1 or "." in word:
                return False
        if end + 1 < len(text) and not (text[end + 1].isspace() or text[end + 1] in _WAIT_CLOSERS):
            return False
    return True
