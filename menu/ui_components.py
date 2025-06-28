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