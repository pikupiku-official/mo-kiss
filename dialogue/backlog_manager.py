import pygame

from core.config import (
    CHARACTER_GENDERS,
    FONT_EFFECTS,
    TEXT_COLOR,
    TEXT_COLOR_FEMALE,
    TEXT_MAX_CHARS_PER_LINE,
)
from .inline_markup import wrap_markup_text
from .name_manager import get_name_manager


class BacklogManager:
    """In-scene dialogue history overlay.

    The newest dialogue keeps the ordinary dialogue position. Older entries
    are stacked above it, and the whole dialogue plane moves when scrolling.
    """

    DIM_ALPHA = 140

    # Windows 95/2000 classic palette.
    CLASSIC_FACE = (212, 208, 200)
    CLASSIC_LIGHT = (255, 255, 255)
    CLASSIC_MIDLIGHT = (223, 220, 212)
    CLASSIC_DARK = (128, 128, 128)
    CLASSIC_SHADOW = (0, 0, 0)
    CLASSIC_TRACK = (192, 192, 192)

    SCROLLBAR_WIDTH = 28
    SCROLLBAR_RIGHT_MARGIN = 24
    MIN_THUMB_SIZE = 28
    HUD_GAP = 8

    def __init__(self, screen, fonts=None, debug=False):
        self.screen = screen
        self.fonts = fonts or {}
        self.debug = debug
        self.name_manager = get_name_manager()

        self.entries = []
        self.is_showing = False
        self.text_renderer = None
        self._visible_entries = []

        # Pixel scroll: 0 is newest, positive values move the dialogue plane
        # down to reveal older lines above it.
        self.scroll_offset = 0.0
        self.max_scroll_offset = 0.0
        self._opened_at_ms = None

        self._dragging_thumb = False
        self._drag_start_y = 0
        self._drag_start_offset = 0.0

        self.default_text_color = TEXT_COLOR
        self.default_name_color = TEXT_COLOR
        self.female_text_color = TEXT_COLOR_FEMALE
        self.female_name_color = TEXT_COLOR_FEMALE
        self.choice_color = TEXT_COLOR

        self._dim_surface = None

    def set_text_renderer(self, text_renderer):
        self.text_renderer = text_renderer

    def get_character_colors(self, char_name, force_female=False):
        if char_name == "選択":
            return self.choice_color, self.choice_color
        if force_female or CHARACTER_GENDERS.get(char_name) == "female":
            return self.female_name_color, self.female_text_color
        return self.default_name_color, self.default_text_color

    def add_entry(self, speaker, text, force_female=False, display_lines=None):
        if not text or not str(text).strip():
            return

        substituted_speaker = (
            self.name_manager.substitute_variables(speaker) if speaker else speaker
        )
        substituted_text = self.name_manager.substitute_variables(text)
        entry = {
            "speaker": substituted_speaker or "名無し",
            "text": substituted_text,
            "force_female": bool(force_female),
        }
        if display_lines is not None:
            entry["display_lines"] = [
                str(line) for line in display_lines if str(line).strip()
            ]
        self.entries.append(entry)

    @staticmethod
    def _entry_key(entry):
        return (
            entry.get("speaker") or "名無し",
            entry.get("text") or "",
            bool(entry.get("force_female", False)),
        )

    def _snapshot_entries(self):
        """Freeze the text-bearing scenario steps recorded so far."""
        return [dict(entry) for entry in self.entries]

    def _entry_rows(self, entry):
        lines = entry.get("display_lines")
        if lines is None:
            lines = self._wrap_text(entry.get("text", ""))
        return [str(line) for line in lines if str(line).strip()]

    def _history_rows(self):
        rows = []
        for entry in self._visible_entries:
            lines = self._entry_rows(entry)
            for index, line in enumerate(lines):
                rows.append(
                    {
                        "entry": entry,
                        "line": line,
                        "show_speaker": index == 0,
                    }
                )
        return rows

    def _newest_row_y(self):
        """Keep the newest actually displayed row fixed when B is pressed."""
        base_y = self._text_start_y()
        if not self._visible_entries or self.text_renderer is None:
            return base_y

        renderer = self.text_renderer
        current_text = getattr(renderer, "current_text", "")
        if not current_text:
            max_lines = max(1, int(getattr(renderer, "max_display_lines", 3)))
            return base_y + (max_lines - 1) * self._line_height()

        current = {
            "speaker": getattr(renderer, "current_character_name", None) or "名無し",
            "text": current_text,
            "force_female": bool(getattr(renderer, "current_force_female", False)),
        }
        if self._entry_key(self._visible_entries[-1]) != self._entry_key(current):
            return base_y

        get_y = getattr(renderer, "get_current_dialogue_last_line_y", None)
        if get_y is None:
            return base_y
        return int(round(get_y()))

    def open_backlog(self):
        renderer = self.text_renderer
        if renderer is not None:
            # Opening the log always resolves an in-progress typewriter line.
            if getattr(renderer, "current_text", ""):
                renderer.skip_text()
            renderer.hovered_seed_id = None

        self._visible_entries = self._snapshot_entries()
        self.scroll_offset = 0.0
        self._dragging_thumb = False
        self._opened_at_ms = pygame.time.get_ticks()
        self.is_showing = True
        self._refresh_scroll_bounds()
        if self.debug:
            print(f"[BACKLOG] opened ({len(self._visible_entries)} entries)")

    def close_backlog(self):
        if not self.is_showing:
            return
        now = pygame.time.get_ticks()
        if self.text_renderer is not None and self._opened_at_ms is not None:
            self.text_renderer.resume_after_backlog(now - self._opened_at_ms)
        self.is_showing = False
        self._visible_entries = []
        self._dragging_thumb = False
        self._opened_at_ms = None
        if self.debug:
            print("[BACKLOG] closed")

    def toggle_backlog(self):
        if self.is_showing:
            self.close_backlog()
        else:
            self.open_backlog()

    def is_showing_backlog(self):
        return self.is_showing

    def _max_chars_per_line(self):
        if self.text_renderer is not None:
            return int(self.text_renderer.max_chars_per_line)
        return TEXT_MAX_CHARS_PER_LINE

    def _wrap_text(self, text):
        return wrap_markup_text(text, self._max_chars_per_line())

    def _line_height(self):
        if self.text_renderer is not None:
            return max(1, int(self.text_renderer.text_line_height))
        return 48

    def _text_start_y(self):
        if self.text_renderer is not None:
            return int(round(self.text_renderer.text_start_y))
        return 798

    def _fixed_edge_margin(self):
        """Margin below a full three-line dialogue, reused at the top."""
        height = self.screen.get_height()
        max_lines = (
            int(self.text_renderer.max_display_lines)
            if self.text_renderer is not None
            else 3
        )
        full_dialogue_bottom = self._text_start_y() + max_lines * self._line_height()
        return max(0, height - full_dialogue_bottom)

    def _top_clip_y(self):
        """Keep backlog dialogue out of the fixed date/weather HUD area."""
        top = self._fixed_edge_margin()
        renderer = self.text_renderer
        if renderer is None or not getattr(renderer, "date_display_enabled", False):
            return top

        effect_padding = 0
        if FONT_EFFECTS.get("enable_shadow", False):
            shadow_offset = FONT_EFFECTS.get("shadow_offset", (6, 6))
            outline_width = max(
                2,
                min(
                    3,
                    int(
                        round(
                            max(abs(shadow_offset[0]), abs(shadow_offset[1]))
                        )
                    )
                    // 2,
                ),
            )
            effect_padding = outline_width * 2

        for position_attr, font_attr in (
            ("date_position", "date_font"),
            ("weather_position", "weather_font"),
        ):
            position = getattr(renderer, position_attr, None)
            font = getattr(renderer, font_attr, None)
            if position is None or font is None:
                continue
            hud_bottom = int(position[1]) + int(font.get_height()) + effect_padding
            top = max(top, hud_bottom + self.HUD_GAP)
        return top

    def _viewport_rect(self):
        margin = self._fixed_edge_margin()
        top = self._top_clip_y()
        return pygame.Rect(
            0,
            top,
            self.screen.get_width(),
            max(0, self.screen.get_height() - margin - top),
        )

    def _layout_entries(self):
        """Return one layout item per non-empty displayed dialogue row."""
        rows = self._history_rows()
        if not rows:
            return []

        line_height = self._line_height()
        layout = []
        next_y = self._newest_row_y()
        for row in reversed(rows):
            layout.append({**row, "y": next_y})
            next_y -= line_height
        layout.reverse()
        return layout

    def _refresh_scroll_bounds(self):
        layout = self._layout_entries()
        if not layout:
            self.max_scroll_offset = 0.0
            self.scroll_offset = 0.0
            return layout
        oldest_y = layout[0]["y"]
        self.max_scroll_offset = float(max(0, self._viewport_rect().top - oldest_y))
        self.scroll_offset = max(0.0, min(self.scroll_offset, self.max_scroll_offset))
        return layout

    def scroll_up(self, amount=None):
        self._refresh_scroll_bounds()
        step = self._line_height() if amount is None else amount
        self.scroll_offset = min(self.max_scroll_offset, self.scroll_offset + step)

    def scroll_down(self, amount=None):
        self._refresh_scroll_bounds()
        step = self._line_height() if amount is None else amount
        self.scroll_offset = max(0.0, self.scroll_offset - step)

    def page_up(self):
        self.scroll_up(
            max(
                self._line_height(),
                self._viewport_rect().height - self._line_height(),
            )
        )

    def page_down(self):
        self.scroll_down(
            max(
                self._line_height(),
                self._viewport_rect().height - self._line_height(),
            )
        )

    def _scrollbar_geometry(self):
        self._refresh_scroll_bounds()
        if self.max_scroll_offset <= 0:
            return None

        viewport = self._viewport_rect()
        width = self.SCROLLBAR_WIDTH
        bar = pygame.Rect(
            self.screen.get_width() - self.SCROLLBAR_RIGHT_MARGIN - width,
            viewport.top,
            width,
            viewport.height,
        )
        up_button = pygame.Rect(bar.x, bar.y, width, width)
        down_button = pygame.Rect(bar.x, bar.bottom - width, width, width)
        track = pygame.Rect(
            bar.x,
            up_button.bottom,
            width,
            max(0, bar.height - 2 * width),
        )

        scroll_world_height = viewport.height + self.max_scroll_offset
        thumb_height = max(
            self.MIN_THUMB_SIZE,
            int(round(track.height * viewport.height / scroll_world_height)),
        )
        thumb_height = min(track.height, thumb_height)
        travel = max(0, track.height - thumb_height)
        progress = self.scroll_offset / self.max_scroll_offset
        thumb_y = track.bottom - thumb_height - int(round(progress * travel))
        thumb = pygame.Rect(track.x, thumb_y, track.width, thumb_height)
        return {
            "bar": bar,
            "up": up_button,
            "down": down_button,
            "track": track,
            "thumb": thumb,
            "travel": travel,
        }

    def handle_input(self, event):
        """Handle backlog input and return whether the event was consumed."""
        if event.type == pygame.KEYDOWN and event.key == pygame.K_b:
            self.toggle_backlog()
            return True
        if not self.is_showing:
            return False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.scroll_up()
                return True
            if event.key == pygame.K_DOWN:
                self.scroll_down()
                return True
            if event.key == pygame.K_PAGEUP:
                self.page_up()
                return True
            if event.key == pygame.K_PAGEDOWN:
                self.page_down()
                return True

        if event.type == pygame.MOUSEWHEEL:
            if event.y > 0:
                self.scroll_up(self._line_height() * abs(event.y))
            elif event.y < 0:
                self.scroll_down(self._line_height() * abs(event.y))
            return True

        geometry = self._scrollbar_geometry()
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 4:
                self.scroll_up()
                return True
            if event.button == 5:
                self.scroll_down()
                return True
            if event.button != 1 or geometry is None:
                return True
            if geometry["up"].collidepoint(event.pos):
                self.scroll_up()
            elif geometry["down"].collidepoint(event.pos):
                self.scroll_down()
            elif geometry["thumb"].collidepoint(event.pos):
                self._dragging_thumb = True
                self._drag_start_y = event.pos[1]
                self._drag_start_offset = self.scroll_offset
            elif geometry["track"].collidepoint(event.pos):
                if event.pos[1] < geometry["thumb"].top:
                    self.page_up()
                elif event.pos[1] > geometry["thumb"].bottom:
                    self.page_down()
            return True

        if event.type == pygame.MOUSEMOTION and self._dragging_thumb:
            if geometry is not None and geometry["travel"] > 0:
                delta_y = event.pos[1] - self._drag_start_y
                offset_delta = (
                    -delta_y * self.max_scroll_offset / geometry["travel"]
                )
                self.scroll_offset = max(
                    0.0,
                    min(
                        self.max_scroll_offset,
                        self._drag_start_offset + offset_delta,
                    ),
                )
            return True

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self._dragging_thumb = False
            return True

        return True

    def _render_dim(self):
        if (
            self._dim_surface is None
            or self._dim_surface.get_size() != self.screen.get_size()
        ):
            self._dim_surface = pygame.Surface(
                self.screen.get_size(), pygame.SRCALPHA
            )
            self._dim_surface.fill((0, 0, 0, self.DIM_ALPHA))
        self.screen.blit(self._dim_surface, (0, 0))

    @staticmethod
    def _draw_bevel(surface, rect, raised=True):
        light = (
            BacklogManager.CLASSIC_LIGHT
            if raised
            else BacklogManager.CLASSIC_SHADOW
        )
        midlight = (
            BacklogManager.CLASSIC_MIDLIGHT
            if raised
            else BacklogManager.CLASSIC_DARK
        )
        dark = (
            BacklogManager.CLASSIC_DARK
            if raised
            else BacklogManager.CLASSIC_MIDLIGHT
        )
        shadow = (
            BacklogManager.CLASSIC_SHADOW
            if raised
            else BacklogManager.CLASSIC_LIGHT
        )
        pygame.draw.line(surface, light, rect.topleft, (rect.right - 1, rect.top))
        pygame.draw.line(surface, light, rect.topleft, (rect.left, rect.bottom - 1))
        pygame.draw.line(
            surface,
            midlight,
            (rect.left + 1, rect.top + 1),
            (rect.right - 2, rect.top + 1),
        )
        pygame.draw.line(
            surface,
            dark,
            (rect.right - 2, rect.top + 1),
            (rect.right - 2, rect.bottom - 2),
        )
        pygame.draw.line(
            surface,
            dark,
            (rect.left + 1, rect.bottom - 2),
            (rect.right - 2, rect.bottom - 2),
        )
        pygame.draw.line(
            surface,
            shadow,
            (rect.right - 1, rect.top),
            (rect.right - 1, rect.bottom - 1),
        )
        pygame.draw.line(
            surface,
            shadow,
            (rect.left, rect.bottom - 1),
            (rect.right - 1, rect.bottom - 1),
        )

    def _draw_classic_button(self, rect, direction):
        pygame.draw.rect(self.screen, self.CLASSIC_FACE, rect)
        self._draw_bevel(self.screen, rect, raised=True)
        cx, cy = rect.center
        if direction == "up":
            points = [(cx, cy - 4), (cx - 5, cy + 3), (cx + 5, cy + 3)]
        else:
            points = [(cx, cy + 4), (cx - 5, cy - 3), (cx + 5, cy - 3)]
        pygame.draw.polygon(self.screen, self.CLASSIC_SHADOW, points)

    def _render_scrollbar(self):
        geometry = self._scrollbar_geometry()
        if geometry is None:
            return

        track = geometry["track"]
        pygame.draw.rect(self.screen, self.CLASSIC_TRACK, track)
        # A tiny checker pattern evokes the classic Windows scrollbar trough.
        for y in range(track.top, track.bottom, 4):
            start_x = track.left + (2 if ((y - track.top) // 4) % 2 else 0)
            for x in range(start_x, track.right, 4):
                self.screen.set_at((x, y), self.CLASSIC_LIGHT)

        self._draw_classic_button(geometry["up"], "up")
        self._draw_classic_button(geometry["down"], "down")
        pygame.draw.rect(self.screen, self.CLASSIC_FACE, geometry["thumb"])
        self._draw_bevel(self.screen, geometry["thumb"], raised=True)

    def _render_entries(self, layout):
        renderer = self.text_renderer
        if renderer is None:
            return

        viewport = self._viewport_rect()
        old_clip = self.screen.get_clip()
        self.screen.set_clip(viewport)
        try:
            line_height = self._line_height()
            offset = int(round(self.scroll_offset))
            for item in layout:
                entry = item["entry"]
                y = item["y"] + offset
                if y < viewport.top or y >= viewport.bottom:
                    continue

                name_color, text_color = self.get_character_colors(
                    entry.get("speaker"), entry.get("force_female", False)
                )
                if item["show_speaker"] and entry.get("speaker"):
                    name_surface = renderer._render_name_with_grid_system(
                        entry["speaker"], name_color
                    )
                    self.screen.blit(
                        name_surface,
                        (int(round(renderer.name_start_x)), int(round(y))),
                    )
                text_surface = renderer._render_stable_text_line(
                    item["line"], text_color
                )
                self.screen.blit(
                    text_surface,
                    (
                        int(round(renderer.text_start_x)),
                        int(round(y)) - renderer.ruby_h,
                    ),
                )
        finally:
            self.screen.set_clip(old_clip)

    def render(self):
        if not self.is_showing:
            return
        layout = self._refresh_scroll_bounds()
        self._render_dim()
        self._render_entries(layout)
        self._render_scrollbar()
