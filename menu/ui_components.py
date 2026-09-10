import pygame
from .main_menu_config import COLORS, BUTTON_CONFIG, SLIDER_CONFIG
from core.ui.text_edit import TextEditBuffer
from dialogue.font_effects import render_text_with_effects

class Button:
    def __init__(self, x, y, width, height, text, font, color_scheme='normal'):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = font
        self.color_scheme = color_scheme
        self.is_hovered = False
        self.is_pressed = False
        self.is_selected = False  # 選択状態を追加
        
        # 色の設定
        if color_scheme == 'green':
            self.colors = {
                'normal': COLORS['btn_green_normal'],
                'hover': COLORS['btn_normal'],      # ホバー時は青色
                'pressed': COLORS['btn_pressed']     # プレス時は青色
            }
        else:
            self.colors = {
                'normal': COLORS['btn_normal'],
                'hover': COLORS['btn_hover'],
                'pressed': COLORS['btn_pressed']
            }
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.is_pressed = True
                return True
        elif event.type == pygame.MOUSEBUTTONUP:
            if self.is_pressed and self.rect.collidepoint(event.pos):
                self.is_pressed = False
                return 'click'
            self.is_pressed = False
        return False
    
    def draw(self, screen):
        # ボタンの色を決定
        if self.is_selected:
            # 選択状態の場合は青色を固定
            color = COLORS['btn_normal']
        elif self.is_pressed:
            color = self.colors['pressed']
        elif self.is_hovered:
            color = self.colors['hover']
        else:
            color = self.colors['normal']
        
        # ボタンを描画（角丸）
        pygame.draw.rect(screen, color, self.rect, border_radius=BUTTON_CONFIG['border_radius'])
        pygame.draw.rect(screen, COLORS['border_dark'], self.rect, 2, border_radius=BUTTON_CONFIG['border_radius'])
        
        # テキストを描画
        text_surface = self.font.render(self.text, True, COLORS['btn_text'])
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

class Slider:
    def __init__(self, x, y, width, height, min_val, max_val, initial_val):
        self.rect = pygame.Rect(x, y, width, height)
        self.min_val = min_val
        self.max_val = max_val
        self.val = initial_val
        self.dragging = False
        self.handle_size = SLIDER_CONFIG['handle_size']
        
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.dragging = True
                self._update_value(event.pos[0])
                return True
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            self._update_value(event.pos[0])
            return True
        return False
    
    def _update_value(self, mouse_x):
        # マウス位置から値を計算
        relative_x = mouse_x - self.rect.x
        relative_x = max(0, min(relative_x, self.rect.width))
        self.val = self.min_val + (relative_x / self.rect.width) * (self.max_val - self.min_val)
    
    def draw(self, screen):
        # スライダーの背景
        pygame.draw.rect(screen, COLORS['slider_bg'], self.rect, border_radius=self.rect.height//2)
        pygame.draw.rect(screen, COLORS['border_dark'], self.rect, 2, border_radius=self.rect.height//2)
        
        # アクティブ部分
        active_width = (self.val - self.min_val) / (self.max_val - self.min_val) * self.rect.width
        active_rect = pygame.Rect(self.rect.x, self.rect.y, active_width, self.rect.height)
        pygame.draw.rect(screen, COLORS['slider_active'], active_rect, border_radius=self.rect.height//2)
        
        # ハンドル
        handle_x = self.rect.x + active_width - self.handle_size // 2
        handle_y = self.rect.y + self.rect.height // 2 - self.handle_size // 2
        handle_rect = pygame.Rect(handle_x, handle_y, self.handle_size, self.handle_size)
        pygame.draw.ellipse(screen, COLORS['slider_handle'], handle_rect)
        pygame.draw.ellipse(screen, COLORS['border_dark'], handle_rect, 2)

class Panel:
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
    
    def draw(self, screen):
        # パネルの背景
        pygame.draw.rect(screen, COLORS['bg_panel'], self.rect, border_radius=15)
        pygame.draw.rect(screen, COLORS['border_light'], self.rect, 3, border_radius=15)
        
        # 内側の枠線
        inner_rect = pygame.Rect(self.rect.x + 10, self.rect.y + 10, 
                                self.rect.width - 20, self.rect.height - 20)
        pygame.draw.rect(screen, COLORS['border_dark'], inner_rect, 2, border_radius=10)

class VolumeIndicator:
    def __init__(self, x, y, volume_level):
        self.x = x
        self.y = y
        self.volume_level = volume_level
        self.icon_size = 20
        
    def draw(self, screen):
        # 音符アイコンを5つ描画（大きく調整）
        for i in range(5):
            icon_x = self.x + i * 35
            icon_y = self.y
            
            # 音量レベルに応じて色を変更
            if i < (self.volume_level / 20):  # 0-100を0-5に変換
                color = COLORS['slider_active']
            else:
                color = COLORS['slider_bg']
            
            # 簡単な音符の形を描画（大きく）
            pygame.draw.ellipse(screen, color, (icon_x, icon_y, 18, 12))
            pygame.draw.rect(screen, color, (icon_x + 15, icon_y - 8, 3, 16))

class ToggleButton:
    def __init__(self, x, y, width, height, font, is_enabled=False):
        self.rect = pygame.Rect(x, y, width, height)
        self.font = font
        self.is_enabled = is_enabled
        self.is_hovered = False
        self.is_pressed = False
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.is_pressed = True
                return True
        elif event.type == pygame.MOUSEBUTTONUP:
            if self.is_pressed and self.rect.collidepoint(event.pos):
                self.is_pressed = False
                self.is_enabled = not self.is_enabled  # 状態を切り替え
                return 'toggle'
            self.is_pressed = False
        return False
    
    def draw(self, screen):
        # ボタンの色を決定
        if self.is_enabled:
            color = COLORS['slider_active']  # 有効時は緑
            text = "あり"
        else:
            color = COLORS['slider_bg']      # 無効時はグレー
            text = "なし"
        
        if self.is_pressed:
            color = COLORS['btn_pressed']
        elif self.is_hovered:
            # ホバー時は少し暗くする
            r, g, b = color
            color = (max(0, r-30), max(0, g-30), max(0, b-30))
        
        # ボタンを描画
        pygame.draw.rect(screen, color, self.rect, border_radius=5)
        pygame.draw.rect(screen, COLORS['border_dark'], self.rect, 2, border_radius=5)
        
        # テキストを描画
        text_surface = self.font.render(text, True, COLORS['text_white'])
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)


class TextInput:
    """Single-line name field backed by the shared IME editor."""

    def __init__(
        self,
        x,
        y,
        width,
        height,
        font,
        max_length=3,
        placeholder="",
        input_rect_transform=None,
        grid_width=None,
    ):
        self.rect = pygame.Rect(x, y, width, height)
        self.font = font
        self.max_length = max_length
        self.placeholder = placeholder
        self.input_rect_transform = input_rect_transform or (lambda rect: rect)
        self.grid_width = grid_width or max(8, self.font.get_height())
        # Name entry intentionally accepts overlong text and reports the
        # existing validation error at confirmation time.
        self.editor = TextEditBuffer(max_length=max_length)
        self.is_focused = False
        self.cursor_visible = True
        self.is_hovered = False
        self.cursor_blink_time = 500
        self.last_blink = pygame.time.get_ticks()

    @property
    def text(self):
        return self.editor.text

    @text.setter
    def text(self, value):
        self.editor.set_text(value)

    @property
    def composition_text(self):
        return self.editor.composition

    @composition_text.setter
    def composition_text(self, value):
        self.editor.composition = str(value or "")

    @property
    def is_composing(self):
        return self.editor.is_composing

    @is_composing.setter
    def is_composing(self, value):
        if not value:
            self.editor.clear_composition()

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
            return None
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                if not self.is_focused:
                    self.focus()
                self._place_cursor_from_mouse(event.pos[0])
                return "focus"
            if self.is_focused:
                self.clear_focus()
                return "blur"
            return None
        if not self.is_focused:
            return None

        result = self.editor.handle_event(event, enforce_limit=False)
        if result == "submit":
            self.clear_focus()
            return "enter"
        if result == "changed":
            self._reset_cursor_blink()
            return "text_changed"
        if result in ("selection", "composition"):
            self._reset_cursor_blink()
        return None

    def _place_cursor_from_mouse(self, mouse_x):
        relative = max(0, mouse_x - (self.rect.x + 8))
        best_index = 0
        best_distance = float("inf")
        for index in range(len(self.text) + 1):
            distance = abs(index * self.grid_width - relative)
            if distance < best_distance:
                best_index = index
                best_distance = distance
        self.editor.set_cursor(best_index)
        self._reset_cursor_blink()

    def _reset_cursor_blink(self):
        self.cursor_visible = True
        self.last_blink = pygame.time.get_ticks()

    def set_text(self, text):
        self.editor.set_text(text)

    def get_text(self):
        return self.editor.text

    def focus(self):
        self.is_focused = True
        self._reset_cursor_blink()
        self.update_ime_rect()
        pygame.key.start_text_input()

    def _caret_virtual_rect(self):
        text_x = self.rect.x + 8
        text_y = self.rect.y + (self.rect.height - self.font.get_height()) // 2
        selection_start, selection_end = self.editor.selection
        insert_at = (
            selection_start
            if self.composition_text and selection_start != selection_end
            else self.editor.cursor
        )
        prefix = self.text[:insert_at] + self.composition_text
        caret_x = text_x + len(prefix) * self.grid_width
        return pygame.Rect(caret_x, text_y + self.font.get_height(), 2, self.font.get_height())

    def update_ime_rect(self):
        input_rect = pygame.Rect(self.input_rect_transform(self._caret_virtual_rect()))
        pygame.key.set_text_input_rect(input_rect)

    def clear_focus(self):
        if self.is_focused:
            self.is_focused = False
            self.editor.clear_composition()
            pygame.key.stop_text_input()

    def _draw_editor_text(self, screen, text_x, text_y, text_color=None,
                          selected_color=(255, 255, 255), selection_color=None):
        text_color = COLORS["text_dark"] if text_color is None else text_color
        selection_color = COLORS["slider_active"] if selection_color is None else selection_color
        selection_start, selection_end = self.editor.selection
        replacing_selection = bool(
            self.composition_text and selection_start != selection_end
        )
        insert_at = selection_start if replacing_selection else self.editor.cursor
        resume_at = selection_end if replacing_selection else self.editor.cursor
        visual = []
        for index, char in enumerate(self.text[:insert_at]):
            kind = "text" if replacing_selection else (
                "selected" if selection_start <= index < selection_end else "text"
            )
            visual.append((char, kind))
        for index, char in enumerate(self.composition_text):
            active = (
                self.editor.composition_start
                <= index
                < self.editor.composition_start + self.editor.composition_length
            )
            visual.append((char, "composition_active" if active else "composition"))
        for index in range(resume_at, len(self.text)):
            visual.append(
                (
                    self.text[index],
                    "text" if replacing_selection else (
                        "selected" if selection_start <= index < selection_end else "text"
                    ),
                )
            )

        x = text_x
        for char, kind in visual:
            selected = kind in ("selected", "composition_active")
            color = selected_color if selected else text_color
            # Use the exact outline/stretch pipeline used by Dialogue text;
            # plain Font.render here was the source of the visibly softer
            # name-input glyphs.
            glyph = render_text_with_effects(self.font, char, color)
            if selected:
                pygame.draw.rect(
                    screen,
                    selection_color if kind == "selected" else (70, 70, 70),
                    pygame.Rect(x, text_y, glyph.get_width(), self.font.get_height()),
                )
            screen.blit(glyph, (x, text_y))
            if kind.startswith("composition"):
                pygame.draw.line(
                    screen,
                    COLORS["text_dark"],
                    (x, text_y + self.font.get_height() - 2),
                    (x + glyph.get_width(), text_y + self.font.get_height() - 2),
                    2,
                )
            # Advance by the underlying font width, as TextRenderer's grid
            # does; outline padding must not change character spacing.
            x += self.grid_width

    def draw(self, screen, *, frame=True, text_color=None,
             selected_color=(255, 255, 255), selection_color=None):
        if self.is_focused:
            now = pygame.time.get_ticks()
            if now - self.last_blink >= self.cursor_blink_time:
                self.cursor_visible = not self.cursor_visible
                self.last_blink = now
            self.update_ime_rect()

        if frame and self.is_focused:
            bg_color, border_color, border_width = COLORS["btn_hover"], COLORS["slider_active"], 3
        elif frame and self.is_hovered:
            bg_color, border_color, border_width = (240, 240, 240), COLORS["border_dark"], 2
        elif frame:
            bg_color, border_color, border_width = (255, 255, 255), COLORS["border_dark"], 1
        else:
            bg_color = (0, 0, 0)
        if frame:
            pygame.draw.rect(screen, bg_color, self.rect, border_radius=5)
            pygame.draw.rect(screen, border_color, self.rect, border_width, border_radius=5)

        text_x = self.rect.x + 8
        text_y = self.rect.y + (self.rect.height - self.font.get_height()) // 2
        if self.text or self.composition_text:
            self._draw_editor_text(
                screen, text_x, text_y, text_color=text_color,
                selected_color=selected_color, selection_color=selection_color,
            )
            if self.is_focused and self.cursor_visible:
                selection_start, selection_end = self.editor.selection
                insert_at = (
                    selection_start
                    if self.composition_text and selection_start != selection_end
                    else self.editor.cursor
                )
                cursor_x = text_x + len(
                    self.text[:insert_at] + self.composition_text
                ) * self.grid_width
                # Japanese dialogue uses a full-width grid cell.  A half-width
                # underscore made the caret hard to see beside CJK glyphs.
                block_width = max(8, self.font.size("あ")[0])
                block_width = self.grid_width
                caret = pygame.Rect(cursor_x, text_y, block_width, self.font.get_height())
                pygame.draw.rect(screen, text_color or COLORS["text_dark"], caret)
                if self.editor.cursor < len(self.text) and not self.composition_text:
                    glyph = render_text_with_effects(
                        self.font, self.text[self.editor.cursor], bg_color
                    )
                    screen.blit(glyph, (cursor_x, text_y))
        elif self.placeholder:
            if frame:
                surface = self.font.render(self.placeholder, True, (150, 150, 150))
                screen.blit(surface, (text_x, text_y))
            if self.is_focused and self.cursor_visible:
                pygame.draw.rect(
                    screen,
                    COLORS["text_dark"],
                    pygame.Rect(
                        text_x,
                        text_y,
                        max(8, self.font.size("あ")[0]),
                        self.font.get_height(),
                    ),
                )
