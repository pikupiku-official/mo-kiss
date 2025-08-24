import pygame
import time
from config import *

class NotificationManager:
    """右上エリアの通知システム"""
    
    def __init__(self, screen, debug=False):
        self.screen = screen
        self.debug = debug
        
        # 通知リスト（最大3つ表示）
        self.notifications = []
        self.max_notifications = 3
        self.notification_duration = 2000  # 2秒
        
        # 位置設定（右上エリア）
        self.notification_width = int(300 * SCALE)
        self.notification_height = int(60 * SCALE) 
        self.notification_spacing = int(10 * SCALE)
        self.margin_right = int(20 * SCALE)
        self.margin_top = int(20 * SCALE)
        
        # フォント設定
        self.font_size = int(SCREEN_HEIGHT * 0.025)
        self.font = pygame.font.SysFont("msgothic", self.font_size)
        
        # 色設定
        self.bg_color = (0, 0, 0, 180)  # 半透明黒
        self.text_color = (255, 255, 255)
        self.border_color = (100, 150, 255)
        
    def add_notification(self, message):
        """通知を追加"""
        current_time = time.time() * 1000  # ミリ秒
        
        notification = {
            'message': message,
            'start_time': current_time,
            'y_offset': 0,  # アニメーション用
            'alpha': 255
        }
        
        self.notifications.append(notification)
        
        # 最大数を超えた場合、古いものを削除
        if len(self.notifications) > self.max_notifications:
            self.notifications = self.notifications[-self.max_notifications:]
        
        if self.debug:
            print(f"通知追加: {message}")
    
    def update(self):
        """通知の状態を更新"""
        current_time = time.time() * 1000  # ミリ秒
        
        # 期限切れの通知を削除
        self.notifications = [
            notif for notif in self.notifications 
            if current_time - notif['start_time'] < self.notification_duration
        ]
        
        # アニメーション更新（フェードアウト）
        for i, notif in enumerate(self.notifications):
            elapsed = current_time - notif['start_time']
            
            # フェードアウト効果
            if elapsed > self.notification_duration - 500:  # 最後の500ms
                fade_progress = (elapsed - (self.notification_duration - 500)) / 500
                notif['alpha'] = int(255 * (1.0 - fade_progress))
            else:
                notif['alpha'] = 255
            
            # Y位置アニメーション（上に移動）
            target_y = i * (self.notification_height + self.notification_spacing)
            notif['y_offset'] = target_y
    
    def render(self):
        """通知を描画"""
        if not self.notifications:
            return
            
        for i, notif in enumerate(self.notifications):
            # 位置計算
            x = SCREEN_WIDTH - self.notification_width - self.margin_right
            y = self.margin_top + notif['y_offset']
            
            # 背景描画
            bg_surface = pygame.Surface((self.notification_width, self.notification_height), pygame.SRCALPHA)
            bg_surface.fill((*self.bg_color[:3], min(notif['alpha'], self.bg_color[3])))
            
            # 境界線描画
            pygame.draw.rect(bg_surface, (*self.border_color, notif['alpha']), 
                           (0, 0, self.notification_width, self.notification_height), 2)
            
            self.screen.blit(bg_surface, (x, y))
            
            # テキスト描画
            text_color_with_alpha = (*self.text_color, notif['alpha'])
            
            # テキストを複数行に分割
            lines = self._wrap_text(notif['message'], self.notification_width - 20)
            
            for j, line in enumerate(lines):
                text_surface = self.font.render(line, True, self.text_color)
                
                # アルファ値を適用
                if notif['alpha'] < 255:
                    alpha_surface = pygame.Surface(text_surface.get_size(), pygame.SRCALPHA)
                    alpha_surface.fill((255, 255, 255, notif['alpha']))
                    alpha_surface.blit(text_surface, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                    text_surface = alpha_surface
                
                text_x = x + 10
                text_y = y + 10 + (j * self.font.get_height())
                self.screen.blit(text_surface, (text_x, text_y))
    
    def _wrap_text(self, text, max_width):
        """テキストを指定幅で改行"""
        words = text.split(' ')
        lines = []
        current_line = ""
        
        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            if self.font.size(test_line)[0] <= max_width - 20:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        return lines if lines else [text]
    
    def clear_all(self):
        """すべての通知をクリア"""
        self.notifications.clear()
        if self.debug:
            print("すべての通知をクリア")