"""Shared, IME-aware text editing state for pygame UI fields."""

from __future__ import annotations

import os
import re

import pygame


def _read_clipboard() -> str:
    """Read Unicode text without creating a helper window."""
    if os.name == "nt":
        try:
            import ctypes

            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32
            user32.OpenClipboard.argtypes = [ctypes.c_void_p]
            user32.GetClipboardData.argtypes = [ctypes.c_uint]
            user32.GetClipboardData.restype = ctypes.c_void_p
            kernel32.GlobalLock.argtypes = [ctypes.c_void_p]
            kernel32.GlobalLock.restype = ctypes.c_void_p
            kernel32.GlobalUnlock.argtypes = [ctypes.c_void_p]
            if not user32.OpenClipboard(None):
                return ""
            try:
                handle = user32.GetClipboardData(13)  # CF_UNICODETEXT
                if not handle:
                    return ""
                pointer = kernel32.GlobalLock(handle)
                if not pointer:
                    return ""
                try:
                    return ctypes.wstring_at(pointer)
                finally:
                    kernel32.GlobalUnlock(handle)
            finally:
                user32.CloseClipboard()
        except Exception:
            return ""

    try:
        if not pygame.scrap.get_init():
            pygame.scrap.init()
        value = pygame.scrap.get(pygame.SCRAP_TEXT)
        if not value:
            return ""
        if isinstance(value, str):
            return value
        for encoding in ("utf-8", "utf-16-le"):
            try:
                return value.decode(encoding).rstrip("\x00")
            except (UnicodeDecodeError, AttributeError):
                continue
    except pygame.error:
        pass
    return ""


def _write_clipboard(text: str) -> None:
    """Write Unicode text without creating a helper window."""
    if os.name == "nt":
        try:
            import ctypes

            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32
            kernel32.GlobalAlloc.argtypes = [ctypes.c_uint, ctypes.c_size_t]
            kernel32.GlobalAlloc.restype = ctypes.c_void_p
            kernel32.GlobalLock.argtypes = [ctypes.c_void_p]
            kernel32.GlobalLock.restype = ctypes.c_void_p
            kernel32.GlobalUnlock.argtypes = [ctypes.c_void_p]
            user32.SetClipboardData.argtypes = [ctypes.c_uint, ctypes.c_void_p]
            user32.SetClipboardData.restype = ctypes.c_void_p
            encoded = (str(text) + "\x00").encode("utf-16-le")
            handle = kernel32.GlobalAlloc(0x0002, len(encoded))  # GMEM_MOVEABLE
            if not handle:
                return
            pointer = kernel32.GlobalLock(handle)
            if not pointer:
                return
            try:
                ctypes.memmove(pointer, encoded, len(encoded))
            finally:
                kernel32.GlobalUnlock(handle)
            if not user32.OpenClipboard(None):
                return
            try:
                user32.EmptyClipboard()
                user32.SetClipboardData(13, handle)  # ownership transfers on success
            finally:
                user32.CloseClipboard()
            return
        except Exception:
            return

    try:
        if not pygame.scrap.get_init():
            pygame.scrap.init()
        pygame.scrap.put(pygame.SCRAP_TEXT, str(text).encode("utf-8"))
    except pygame.error:
        pass


class TextEditBuffer:
    """Cursor, selection, clipboard, and IME composition state.

    Committed text and IME composition remain separate.  This prevents the
    Enter used to confirm a Japanese conversion from being mistaken for the
    application's submit action.
    """

    def __init__(self, text: str = "", *, max_length: int | None = None):
        self.max_length = max_length
        self.text = str(text)
        self.cursor = len(self.text)
        self.anchor = self.cursor
        self.composition = ""
        self.composition_start = 0
        self.composition_length = 0

    @property
    def is_composing(self) -> bool:
        return bool(self.composition)

    @property
    def selection(self) -> tuple[int, int]:
        return tuple(sorted((self.anchor, self.cursor)))

    @property
    def has_selection(self) -> bool:
        return self.anchor != self.cursor

    def set_text(self, text: str) -> None:
        self.text = str(text or "")
        self.cursor = len(self.text)
        self.anchor = self.cursor
        self.clear_composition()

    def set_cursor(self, index: int, *, selecting: bool = False) -> None:
        self.cursor = max(0, min(int(index), len(self.text)))
        if not selecting:
            self.anchor = self.cursor

    def select_all(self) -> None:
        self.anchor = 0
        self.cursor = len(self.text)

    def clear_composition(self) -> None:
        self.composition = ""
        self.composition_start = 0
        self.composition_length = 0

    def _delete_selection(self) -> bool:
        if not self.has_selection:
            return False
        start, end = self.selection
        self.text = self.text[:start] + self.text[end:]
        self.cursor = start
        self.anchor = start
        return True

    def insert(self, value: str, *, enforce_limit: bool = True) -> bool:
        value = str(value).replace("\r", "").replace("\n", "")
        start, end = self.selection
        if enforce_limit and self.max_length is not None:
            available = max(0, self.max_length - (len(self.text) - (end - start)))
            value = value[:available]
        if not value and start == end:
            return False
        self.text = self.text[:start] + value + self.text[end:]
        self.cursor = start + len(value)
        self.anchor = self.cursor
        return True

    def move_vertical(self, columns: int, direction: int, *, selecting: bool = False) -> None:
        columns = max(1, int(columns))
        line, column = divmod(self.cursor, columns)
        target_line = max(0, line + (-1 if direction < 0 else 1))
        target = min(len(self.text), target_line * columns + column)
        self.set_cursor(target, selecting=selecting)

    def _word_boundary(self, direction: int) -> int:
        if direction < 0:
            prefix = self.text[: self.cursor]
            match = re.search(r"(?:\w+|\W)\s*$", prefix)
            return match.start() if match else 0
        suffix = self.text[self.cursor :]
        match = re.match(r"\s*(?:\w+|\W)", suffix)
        return self.cursor + (match.end() if match else len(suffix))

    def handle_event(self, event, *, enforce_limit: bool = True) -> str | None:
        if event.type == pygame.TEXTEDITING:
            self.composition = str(getattr(event, "text", ""))
            self.composition_start = int(getattr(event, "start", 0) or 0)
            self.composition_length = int(getattr(event, "length", 0) or 0)
            return "composition"

        if event.type == pygame.TEXTINPUT:
            changed = self.insert(getattr(event, "text", ""), enforce_limit=enforce_limit)
            self.clear_composition()
            return "changed" if changed else None

        if event.type != pygame.KEYDOWN or self.is_composing:
            return None

        key = event.key
        mod = int(getattr(event, "mod", 0) or 0)
        control = bool(mod & (pygame.KMOD_CTRL | pygame.KMOD_GUI))
        shift = bool(mod & pygame.KMOD_SHIFT)

        if control and key == pygame.K_a:
            self.select_all()
            return "selection"
        if control and key == pygame.K_c:
            if self.has_selection:
                start, end = self.selection
                _write_clipboard(self.text[start:end])
            return "clipboard"
        if control and key == pygame.K_x:
            if self.has_selection:
                start, end = self.selection
                _write_clipboard(self.text[start:end])
                self._delete_selection()
                return "changed"
            return "clipboard"
        if control and key == pygame.K_v:
            return "changed" if self.insert(_read_clipboard(), enforce_limit=enforce_limit) else None

        if key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            return "submit"
        if key == pygame.K_BACKSPACE:
            if self._delete_selection():
                return "changed"
            if self.cursor > 0:
                self.text = self.text[: self.cursor - 1] + self.text[self.cursor :]
                self.cursor -= 1
                self.anchor = self.cursor
                return "changed"
            return None
        if key == pygame.K_DELETE:
            if self._delete_selection():
                return "changed"
            if self.cursor < len(self.text):
                self.text = self.text[: self.cursor] + self.text[self.cursor + 1 :]
                self.anchor = self.cursor
                return "changed"
            return None

        if key in (pygame.K_LEFT, pygame.K_RIGHT):
            direction = -1 if key == pygame.K_LEFT else 1
            if self.has_selection and not shift and not control:
                start, end = self.selection
                self.set_cursor(start if direction < 0 else end)
            else:
                target = self._word_boundary(direction) if control else self.cursor + direction
                self.set_cursor(target, selecting=shift)
            return "selection"
        if key in (pygame.K_HOME, pygame.K_END):
            self.set_cursor(0 if key == pygame.K_HOME else len(self.text), selecting=shift)
            return "selection"
        return None
