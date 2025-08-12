import pygame
from .main_menu_config import COLORS, BUTTON_CONFIG, SLIDER_CONFIG

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
    """テキスト入力フィールド"""
    def __init__(self, x, y, width, height, font, max_length=3, placeholder=""):
        self.rect = pygame.Rect(x, y, width, height)
        self.font = font
        self.max_length = max_length
        self.placeholder = placeholder
        self.text = ""
        self.is_focused = False
        self.cursor_visible = True
        self.cursor_timer = 0
        self.is_hovered = False
        
        # IME入力用
        self.composition_text = ""  # IME変換中のテキスト
        self.is_composing = False   # IME変換中かどうか
        
        # カーソル点滅用
        self.cursor_blink_time = 500  # 500ms
        self.last_blink = pygame.time.get_ticks()
    
    def handle_event(self, event):
        """イベント処理（日本語IME対応改善版）"""
        result = None
        
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                if not self.is_focused:
                    self.is_focused = True
                    self.cursor_visible = True
                    # テキスト入力を有効にする
                    pygame.key.start_text_input()
                    result = 'focus'
            else:
                if self.is_focused:
                    self.is_focused = False
                    self.composition_text = ""
                    self.is_composing = False
                    # テキスト入力を無効にする
                    pygame.key.stop_text_input()
                    result = 'blur'
        
        elif self.is_focused:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_BACKSPACE:
                    if self.is_composing:
                        # IME変換中の場合は変換をクリア
                        self.composition_text = ""
                        self.is_composing = False
                    elif self.text:
                        # 通常のバックスペース処理
                        self.text = self.text[:-1]
                        result = 'text_changed'
                elif event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                    self.is_focused = False
                    self.composition_text = ""
                    self.is_composing = False
                    pygame.key.stop_text_input()
                    result = 'enter'
                elif event.key == pygame.K_ESCAPE:
                    # ESCキーで変換をキャンセル
                    if self.is_composing:
                        self.composition_text = ""
                        self.is_composing = False
            
            elif event.type == pygame.TEXTINPUT:
                # テキスト入力イベント（IME確定後の文字）
                if not self.is_composing and len(self.text) < self.max_length:
                    input_text = event.text
                    # 文字数制限を考慮して追加
                    remaining_length = self.max_length - len(self.text)
                    if len(input_text) <= remaining_length:
                        self.text += input_text
                        result = 'text_changed'
            
            elif event.type == pygame.TEXTEDITING:
                # テキスト編集イベント（IME変換中）
                self.composition_text = event.text
                self.is_composing = len(event.text) > 0
        
        # カーソル点滅処理
        current_time = pygame.time.get_ticks()
        if current_time - self.last_blink > self.cursor_blink_time:
            self.cursor_visible = not self.cursor_visible
            self.last_blink = current_time
        
        return result
    
    def set_text(self, text):
        """テキストを設定"""
        self.text = text[:self.max_length] if text else ""
    
    def get_text(self):
        """テキストを取得"""
        return self.text
    
    def clear_focus(self):
        """フォーカスをクリアしてIME入力を停止"""
        if self.is_focused:
            self.is_focused = False
            self.composition_text = ""
            self.is_composing = False
            pygame.key.stop_text_input()
    
    def draw(self, screen):
        """描画"""
        # 背景色を決定
        if self.is_focused:
            bg_color = COLORS['btn_hover']
            border_color = COLORS['slider_active']
            border_width = 3
        elif self.is_hovered:
            bg_color = (240, 240, 240)
            border_color = COLORS['border_dark']
            border_width = 2
        else:
            bg_color = (255, 255, 255)
            border_color = COLORS['border_dark']
            border_width = 1
        
        # フィールドを描画
        pygame.draw.rect(screen, bg_color, self.rect, border_radius=5)
        pygame.draw.rect(screen, border_color, self.rect, border_width, border_radius=5)
        
        # テキストまたはプレースホルダーを描画
        text_x = self.rect.x + 8
        text_y = self.rect.y + (self.rect.height - self.font.get_height()) // 2
        
        if self.text or self.composition_text:
            # 確定済みテキストを描画
            if self.text:
                text_surface = self.font.render(self.text, True, COLORS['text_dark'])
                screen.blit(text_surface, (text_x, text_y))
                text_width = text_surface.get_width()
            else:
                text_width = 0
            
            # IME変換中のテキストを描画（下線付き）
            if self.is_composing and self.composition_text:
                comp_surface = self.font.render(self.composition_text, True, (100, 100, 100))
                comp_x = text_x + text_width
                screen.blit(comp_surface, (comp_x, text_y))
                # 変換中テキストに下線を描画
                comp_width = comp_surface.get_width()
                pygame.draw.line(screen, (100, 100, 100), 
                               (comp_x, text_y + self.font.get_height() - 2), 
                               (comp_x + comp_width, text_y + self.font.get_height() - 2), 1)
            
            # カーソルを描画（フォーカス中かつ表示状態の場合）
            if self.is_focused and self.cursor_visible:
                cursor_x = text_x + text_width
                if self.is_composing and self.composition_text:
                    cursor_x += self.font.size(self.composition_text)[0]
                cursor_y1 = self.rect.y + 5
                cursor_y2 = self.rect.y + self.rect.height - 5
                pygame.draw.line(screen, COLORS['text_dark'], (cursor_x, cursor_y1), (cursor_x, cursor_y2), 2)
        
        elif self.placeholder:
            # プレースホルダーを描画
            placeholder_surface = self.font.render(self.placeholder, True, (150, 150, 150))
            screen.blit(placeholder_surface, (text_x, text_y))