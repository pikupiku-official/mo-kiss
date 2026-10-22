"""Fixed-layout clue board; animation changes visibility, never saved progress."""

from __future__ import annotations

import re

import pygame

from core.config import CHARACTER_GENDERS, TEXT_COLOR, TEXT_COLOR_FEMALE
from core.path_utils import get_font_path


class CorkboardView:
    TABS = (("all", "すべて"), ("momoko", "桃子"),
            ("sanako", "沙那子"), ("other", "その他"))
    COLORS = {"before_tp1": (255, 242, 169), "after_tp1": (187, 222, 246)}
    NOTE_SIZE = (350, 240)
    NOTE_MAX_FONT_SIZE = 96
    MIN_ZOOM = 0.25
    MAX_ZOOM = 1.8
    NOTE_INTERVAL_MS = 700

    def __init__(self, screen, seed_manager, text_renderer, new_seed_ids=(), clock_ms=None):
        self.screen = screen
        self.text_renderer = text_renderer
        self.clock_ms = clock_ms or pygame.time.get_ticks
        self.entries = {item["id"]: item for item in seed_manager.board_entries()}
        self.new_ids = list(dict.fromkeys(seed_id for seed_id in new_seed_ids if seed_id in self.entries))
        self._new_set = set(self.new_ids)
        self.revealed = 0
        self._animation_finished = not self.new_ids
        self.started_at = self.clock_ms()
        self.tab = "all"
        self.zoom = 1.0
        self.offset = pygame.Vector2()
        self.quote_id = None
        self.quote_page = 0
        self.hovered_id = None
        self._pointer = None
        self._dragging = False
        self._note_cache = {}
        self._scaled_cache = {}
        self._heading_cache = {}
        self._fonts = {}
        width, height = screen.get_size()
        self.dialogue_top = min(int(text_renderer.text_start_y) - 46, height - 240)
        self.viewport = pygame.Rect(32, 110, width - 64, height - 174)
        self._full_viewport = self.viewport.copy()
        self.tab_rects = {key: pygame.Rect(32 + i * 163, 25, 155, 47)
                          for i, (key, _) in enumerate(self.TABS)}
        self.buttons = {
            "minus": pygame.Rect(width - 682, 25, 48, 47),
            "plus": pygame.Rect(width - 626, 25, 48, 47),
            "fit": pygame.Rect(width - 570, 25, 160, 47),
            "back": pygame.Rect(width - 180, 25, 148, 47),
            "skip": pygame.Rect(width - 372, 78, 340, 28),
        }
        self.quote_rect = pygame.Rect(0, self.dialogue_top, width, height - self.dialogue_top)
        self.close_quote_rect = pygame.Rect(width - 155, self.dialogue_top + 8, 123, 34)
        self.fit()
        if self.new_ids:
            self.focus(self.entries[self.new_ids[0]])

    @property
    def is_animating(self):
        return not self._animation_finished

    def visible_entries(self):
        hidden = set(self.new_ids[self.revealed:])
        return [entry for seed_id, entry in self.entries.items()
                if seed_id not in hidden and
                (self.tab == "all" or entry["category"]["group"] == self.tab)]

    @staticmethod
    def world_rect(entry):
        return pygame.Rect(*entry["position"], *CorkboardView.NOTE_SIZE)

    def screen_rect(self, entry):
        x, y = pygame.Vector2(entry["position"]) * self.zoom + self.offset
        return pygame.Rect(round(x), round(y), round(self.NOTE_SIZE[0] * self.zoom),
                           round(self.NOTE_SIZE[1] * self.zoom))

    def fit(self, entries=None):
        entries = self.visible_entries() if entries is None else entries
        if not entries:
            self.zoom = 1.0
            self.offset.update(self.viewport.x + 35, self.viewport.y + 30)
            return
        bounds = self.world_rect(entries[0])
        for entry in entries:
            bounds.union_ip(self.world_rect(entry))
            x, y = entry["category"]["position"]
            bounds.union_ip(pygame.Rect(x, y, 350, 50))
        self.zoom = max(self.MIN_ZOOM, min(1.0, (self.viewport.w - 70) / bounds.w,
                                         (self.viewport.h - 70) / bounds.h))
        self.offset = pygame.Vector2(self.viewport.center) - pygame.Vector2(bounds.center) * self.zoom
        self._clamp_offset()
        self._update_hover()

    def focus(self, entry):
        self.zoom = 1.0
        self.offset = pygame.Vector2(self.viewport.center) - pygame.Vector2(self.world_rect(entry).center) * self.zoom
        self._clamp_offset(include_pending=True)

    def zoom_at(self, factor, position):
        old_zoom = self.zoom
        self.zoom = max(self.MIN_ZOOM, min(self.MAX_ZOOM, old_zoom * factor))
        anchor = pygame.Vector2(position)
        self.offset = anchor - (anchor - self.offset) * (self.zoom / old_zoom)
        self._clamp_offset()
        self._update_hover()

    def _clamp_offset(self, include_pending=False):
        entries = list(self.entries.values()) if include_pending else self.visible_entries()
        if not entries:
            return
        bounds = self.world_rect(entries[0])
        for entry in entries:
            bounds.union_ip(self.world_rect(entry))
        # Permit space around the board, but keep at least one note reachable.
        for axis, low, high, start, end in (
            (0, bounds.left, bounds.right, self.viewport.left, self.viewport.right),
            (1, bounds.top - 58, bounds.bottom, self.viewport.top, self.viewport.bottom),
        ):
            minimum = start + 65 - high * self.zoom
            maximum = end - 65 - low * self.zoom
            self.offset[axis] = max(minimum, min(maximum, self.offset[axis]))

    def skip_animation(self):
        self.revealed = len(self.new_ids)
        self._animation_finished = True
        self.fit([self.entries[seed_id] for seed_id in self.new_ids])
        self._update_hover()

    def update(self):
        if not self.is_animating:
            return
        elapsed = max(0, self.clock_ms() - self.started_at)
        count = min(len(self.new_ids), elapsed // self.NOTE_INTERVAL_MS + 1)
        if count != self.revealed:
            self.revealed = count
            self.focus(self.entries[self.new_ids[count - 1]])
            self._update_hover()
        if elapsed >= len(self.new_ids) * self.NOTE_INTERVAL_MS:
            self._animation_finished = True
            self.fit([self.entries[seed_id] for seed_id in self.new_ids])

    def _update_hover(self):
        self.hovered_id = None
        if self._pointer is None or not self.viewport.collidepoint(self._pointer) or self._dragging:
            return
        for entry in reversed(self.visible_entries()):
            if self.screen_rect(entry).collidepoint(self._pointer):
                self.hovered_id = entry["id"]
                break

    def open_quote(self, seed_id):
        self.quote_id = seed_id
        self.quote_page = 0
        self.viewport.height = self.dialogue_top - 156
        # Keep the clicked note above the newly opened panel, at the current
        # zoom. Never rearrange its fixed world position to make room.
        rect = self.screen_rect(self.entries[seed_id])
        target = rect.clamp(self.viewport.inflate(-32, -32))
        self.offset += pygame.Vector2(target.topleft) - pygame.Vector2(rect.topleft)
        self._clamp_offset()
        self._update_hover()

    def close_quote(self):
        self.quote_id = None
        self.quote_page = 0
        self.viewport = self._full_viewport.copy()
        self._update_hover()

    def handle_events(self, events):
        for event in events:
            if hasattr(event, "pos"):
                self._pointer = event.pos
            if self.is_animating:
                if ((event.type == pygame.KEYDOWN and event.key in (
                        pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE, pygame.K_LCTRL, pygame.K_RCTRL))
                        or (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1)):
                    self.skip_animation()
                # Consume the skip input; it must not also close or move the board.
                continue
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if self.buttons["back"].collidepoint(event.pos):
                        return "back"
                    if self.buttons["fit"].collidepoint(event.pos):
                        self.fit()
                    elif self.buttons["minus"].collidepoint(event.pos):
                        self.zoom_at(1 / 1.15, self.viewport.center)
                    elif self.buttons["plus"].collidepoint(event.pos):
                        self.zoom_at(1.15, self.viewport.center)
                    elif self.quote_id is not None and self.quote_rect.collidepoint(event.pos):
                        if self.close_quote_rect.collidepoint(event.pos):
                            self.close_quote()
                        else:
                            self._turn_quote_page(-1 if event.pos[0] < self.screen.get_width() // 2 else 1)
                    elif self.viewport.collidepoint(event.pos):
                        self._update_hover()
                        if self.hovered_id is not None:
                            self.open_quote(self.hovered_id)
                        else:
                            self.close_quote()
                            self._dragging = True
                    else:
                        for key, rect in self.tab_rects.items():
                            if rect.collidepoint(event.pos):
                                self.tab = key
                                self.close_quote()
                                self.hovered_id = None
                                self.fit()
                                break
                elif event.button == 2 and self.viewport.collidepoint(event.pos):
                    self._dragging = True
            elif event.type == pygame.MOUSEBUTTONUP and event.button in (1, 2):
                self._dragging = False
                self._update_hover()
            elif event.type == pygame.MOUSEMOTION:
                if self._dragging:
                    self.offset += pygame.Vector2(event.rel)
                    self._clamp_offset()
                self._update_hover()
            elif event.type == pygame.MOUSEWHEEL:
                if self._pointer is not None and self.viewport.collidepoint(self._pointer):
                    self.zoom_at(1.15 ** max(-10, min(10, event.y)), self._pointer)
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_LEFT, pygame.K_PAGEUP):
                    self._turn_quote_page(-1)
                elif event.key in (pygame.K_RIGHT, pygame.K_PAGEDOWN, pygame.K_RETURN):
                    self._turn_quote_page(1)
                elif event.key in (pygame.K_HOME, pygame.K_0):
                    self.fit()
                elif event.key == pygame.K_BACKSPACE:
                    return "back"
        return None

    def _quote(self):
        if self.quote_id is None:
            return "", "", False
        source = self.entries[self.quote_id]["source"]
        text = source.get("text") or "このタネの元の発言は記録されていません。"
        # Reuse ruby/boten and original name substitution, without live seed links.
        text = re.sub(r'\[seed\s+id="[^"]+"\]|\[/seed\]', "", text)
        return source.get("speaker", ""), text, bool(source.get("force_female", False))

    def quote_pages(self):
        lines = self.text_renderer._wrap_text(self._quote()[1])
        page_size = self.text_renderer.max_display_lines
        return [lines[i:i + page_size] for i in range(0, len(lines), page_size)] or [[]]

    def _turn_quote_page(self, delta):
        if self.quote_id is None:
            return
        pages = self.quote_pages()
        self.quote_page = max(0, min(len(pages) - 1, self.quote_page + delta))

    def _font(self, size):
        if size not in self._fonts:
            self._fonts[size] = pygame.font.Font(get_font_path("MPLUS1p-Medium.ttf"), size)
        return self._fonts[size]

    def _label(self, text, position, size=24, color=(242, 237, 222)):
        self.screen.blit(self._font(size).render(text, True, color), position)

    @staticmethod
    def _wrap_note(text, font, width):
        lines, line = [], ""
        for char in str(text):
            if char == "\n":
                lines.append(line)
                line = ""
            elif line and font.size(line + char)[0] > width:
                lines.append(line)
                line = char
            else:
                line += char
        if line:
            lines.append(line)
        return lines

    def _note_text_layout(self, text):
        """Use the largest font whose wrapped lines fit the note's body."""
        width, height = self.NOTE_SIZE[0] - 42, self.NOTE_SIZE[1] - 67
        closing_punctuation = "、。，．！？!?」』）】〕〉》…"
        for size in range(self.NOTE_MAX_FONT_SIZE, 7, -1):
            font = self._font(size)
            lines = self._wrap_note(text, font, width)
            line_height = font.get_height() + 3
            total_height = max(font.get_height(), len(lines) * line_height - 3)
            orphan_punctuation = (len(lines) > 1 and lines[-1]
                                  and all(char in closing_punctuation for char in lines[-1]))
            if total_height <= height and not orphan_punctuation:
                break
        return font, lines, line_height

    def _note_surface(self, entry):
        seed_id = entry["id"]
        if seed_id in self._note_cache:
            return self._note_cache[seed_id]
        width, height = self.NOTE_SIZE
        surface = pygame.Surface((width, height), pygame.SRCALPHA)
        color = self.COLORS[entry["phase"]]
        pygame.draw.polygon(surface, color, [(0, 0), (width, 0), (width, height - 20),
                                           (width - 22, height), (0, height)])
        pygame.draw.polygon(surface, tuple(max(0, v - 30) for v in color),
                            [(width - 22, height - 20), (width, height - 20), (width - 22, height)])
        pygame.draw.circle(surface, (141, 64, 53), (width // 2, 17), 7)
        font, lines, line_height = self._note_text_layout(entry["text"])
        text_surface = pygame.Surface((width - 42, max(font.get_height(), len(lines) * line_height - 3)), pygame.SRCALPHA)
        for index, line in enumerate(lines):
            text_surface.blit(font.render(line, True, (53, 48, 41)), (0, index * line_height))
        # Even exceptionally long authored summaries stay inside the note.
        if text_surface.get_height() > height - 67:
            scale = (height - 67) / text_surface.get_height()
            text_surface = pygame.transform.smoothscale(text_surface, (
                max(1, round(text_surface.get_width() * scale)), height - 67))
        surface.blit(text_surface, (21, 39))
        self._note_cache[seed_id] = surface
        return surface

    def render(self):
        width, height = self.screen.get_size()
        self.screen.fill((43, 47, 46))
        pygame.draw.rect(self.screen, (91, 67, 47), self.viewport.inflate(14, 14), border_radius=6)
        pygame.draw.rect(self.screen, (169, 139, 102), self.viewport)
        old_clip = self.screen.get_clip()
        self.screen.set_clip(self.viewport)
        # A quiet cork pattern is independent of notes and never reveals empty slots.
        for y in range(self.viewport.top, self.viewport.bottom, 29):
            for x in range(self.viewport.left + (y % 17), self.viewport.right, 37):
                pygame.draw.circle(self.screen, (156, 125, 90), (x, y), 1)
        visible = self.visible_entries()
        categories = {item["category"]["id"]: item["category"] for item in visible}
        groups = dict(self.TABS)
        for category in categories.values():
            key = category["id"]
            if key not in self._heading_cache:
                title = f'{groups[category["group"]]} / {category.get("title", "")}'
                self._heading_cache[key] = self._font(36).render(title, True, (48, 39, 31))
            surface = self._heading_cache[key]
            size = (max(1, round(surface.get_width() * self.zoom)), max(1, round(surface.get_height() * self.zoom)))
            position = pygame.Vector2(category["position"]) * self.zoom + self.offset
            self.screen.blit(pygame.transform.smoothscale(surface, size), position)
        for entry in visible:
            rect = self.screen_rect(entry)
            if not rect.colliderect(self.viewport):
                continue
            cache_key = (entry["id"], rect.size)
            if cache_key not in self._scaled_cache:
                if len(self._scaled_cache) > 256:
                    self._scaled_cache.clear()
                self._scaled_cache[cache_key] = pygame.transform.smoothscale(self._note_surface(entry), rect.size)
            pygame.draw.rect(self.screen, (117, 91, 65), rect.move(5, 6))
            self.screen.blit(self._scaled_cache[cache_key], rect)
            if entry["id"] == self.hovered_id:
                pygame.draw.rect(self.screen, (255, 255, 242), rect, 3)
            if entry["id"] in self._new_set:
                self._label("NEW", (rect.x + 8, rect.y + 3), max(12, round(17 * self.zoom)), (140, 54, 38))
        if not visible and not self.is_animating:
            self._label("このタブには、まだ付箋がありません。", (self.viewport.x + 40, self.viewport.y + 40), 27, (54, 43, 32))
        self.screen.set_clip(old_clip)
        for key, label in self.TABS:
            rect = self.tab_rects[key]
            pygame.draw.rect(self.screen, (128, 108, 77) if key == self.tab else (64, 69, 65), rect, border_radius=5)
            self._label(label, (rect.x + 21, rect.y + 5), 27)
        for key, label in (("minus", "−"), ("plus", "＋"), ("fit", "全体表示"), ("back", "戻る")):
            rect = self.buttons[key]
            pygame.draw.rect(self.screen, (64, 69, 65), rect, border_radius=5)
            self._label(label, (rect.x + 12, rect.y + 8), 24)
        self._label("第一TP以前", (58, 80), 18)
        self._label("第一TP以後", (240, 80), 18)
        pygame.draw.rect(self.screen, self.COLORS["before_tp1"], (33, 86, 16, 16))
        pygame.draw.rect(self.screen, self.COLORS["after_tp1"], (215, 86, 16, 16))
        if self.is_animating:
            self._label("付箋を整理中…  クリック / Enter でスキップ", self.buttons["skip"].topleft, 18)
        else:
            self._label(f"{len(visible)}枚  /  {round(self.zoom * 100)}%", (width - 360, 80), 20)
        self._label("付箋クリック：会話    ホイール：拡大・縮小    背景ドラッグ：移動    Home：全体表示", (34, self.viewport.bottom + 13), 21)
        if self.quote_id is not None:
            pygame.draw.rect(self.screen, (24, 27, 28), self.quote_rect)
            self._render_quote()
            pygame.draw.rect(self.screen, (64, 69, 65), self.close_quote_rect, border_radius=4)
            self._label("閉じる", (self.close_quote_rect.x + 20, self.close_quote_rect.y + 2), 22)

    def _render_quote(self):
        renderer = self.text_renderer
        speaker, _, force_female = self._quote()
        color = TEXT_COLOR_FEMALE if force_female or CHARACTER_GENDERS.get(speaker) == "female" else TEXT_COLOR
        if speaker:
            name = renderer._render_name_with_grid_system(speaker, color)
            self.screen.blit(name, (round(renderer.name_start_x), round(renderer.name_start_y)))
        pages = self.quote_pages()
        self.quote_page = min(self.quote_page, len(pages) - 1)
        y = renderer.text_start_y
        for line in pages[self.quote_page]:
            surface = renderer._render_stable_text_line(line, color)
            margin = renderer._layout_line_render_padding(line)
            self.screen.blit(surface, (round(renderer.text_start_x) - margin,
                                       round(y) - renderer.ruby_h - margin))
            y += renderer.text_line_height
        if len(pages) > 1:
            self._label(f"← 前 / 次 →    {self.quote_page + 1} / {len(pages)}",
                        (self.screen.get_width() - 330, self.screen.get_height() - 35), 20)
