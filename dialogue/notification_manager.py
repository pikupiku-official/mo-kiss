import pygame
import time
import os
from config import *

class NotificationManager:
    """右上エリアの通知システム"""
    
    def __init__(self, screen, debug=False):
        self.screen = screen
        self.debug = debug
        
        # 通知リスト（最大3つ表示）
        self.notifications = []
        self.max_notifications = 3
        self.notification_duration = 4000  # nミリ秒
        
        # 位置設定（右上エリア、4:3コンテンツ基準）
        # 仮想座標（1440x1080基準）で定義
        self.virtual_notification_width = 300
        self.virtual_notification_height = 60
        self.virtual_notification_spacing = 10
        self.virtual_margin_right = 20
        self.virtual_margin_top = 20

        # 実座標に変換
        self.notification_width = int(self.virtual_notification_width * SCALE)
        self.notification_height = int(self.virtual_notification_height * SCALE)
        self.notification_spacing = int(self.virtual_notification_spacing * SCALE)
        self.margin_right = int(self.virtual_margin_right * SCALE)
        self.margin_top = int(self.virtual_margin_top * SCALE)
        
        # フォント設定
        self.font_size = int(SCREEN_HEIGHT * 0.025)
        # プロジェクト専用フォントを使用
        project_root = os.path.dirname(os.path.dirname(__file__))
        font_path = os.path.join(project_root, "fonts", "MPLUSRounded1c-Regular.ttf")
        try:
            self.font = pygame.font.Font(font_path, self.font_size)
        except:
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
        
        print(f"[NOTIFICATION] 通知追加: {message} (現在の通知数: {len(self.notifications)})")
        if self.debug:
            print(f"[DEBUG] 通知詳細: {notification}")
    
    def update(self):
        """通知の状態を更新"""
        current_time = time.time() * 1000  # ミリ秒
        
        if self.debug and self.notifications:
            print(f"[NOTIFICATION_UPDATE] 更新開始: 通知数={len(self.notifications)}")
        
        # 期限切れの通知を削除
        old_count = len(self.notifications)
        self.notifications = [
            notif for notif in self.notifications 
            if current_time - notif['start_time'] < self.notification_duration
        ]
        
        if old_count != len(self.notifications):
            print(f"[NOTIFICATION] {old_count - len(self.notifications)}個の通知が期限切れで削除されました")
        
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
            return  # 頻繁に呼ばれるのでログ出力しない

        # 通知描画（ログ出力しない）
            
        for i, notif in enumerate(self.notifications):
            # 位置計算（4:3コンテンツ基準）
            # 仮想座標で計算
            virtual_x = VIRTUAL_WIDTH - self.virtual_notification_width - self.virtual_margin_right
            virtual_y = self.virtual_margin_top + int(notif['y_offset'] / SCALE)

            # scale_pos()で実座標に変換
            x, y = scale_pos(virtual_x, virtual_y)
            
            if self.debug:
                print(f"[NOTIFICATION_RENDER] 通知{i}: pos=({x},{y}), alpha={notif['alpha']}, message='{notif['message']}'")
            
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
                if self.debug:
                    print(f"[NOTIFICATION_RENDER] テキスト行{j}: '{line}'")
                
                try:
                    # 日本語対応のため、アンチエイリアスを有効にしてテキストを描画
                    text_surface = self.font.render(line, True, self.text_color)
                    
                    if self.debug:
                        print(f"[NOTIFICATION_RENDER] テキストサーフェス作成: サイズ={text_surface.get_size()}")
                    
                    # アルファ値を適用（簡単な方法に変更）
                    if notif['alpha'] < 255:
                        text_surface.set_alpha(notif['alpha'])
                    
                    text_x = x + 10
                    text_y = y + 10 + (j * self.font.get_height())
                    
                    if self.debug:
                        print(f"[NOTIFICATION_RENDER] テキスト描画位置: ({text_x}, {text_y})")
                    
                    self.screen.blit(text_surface, (text_x, text_y))
                    
                except Exception as e:
                    print(f"[NOTIFICATION_RENDER] テキスト描画エラー: {e}")
                    # フォールバック: シンプルな英語フォントで描画
                    fallback_font = pygame.font.Font(None, 24)
                    text_surface = fallback_font.render(line, True, self.text_color)
                    text_x = x + 10
                    text_y = y + 10 + (j * 24)
                    self.screen.blit(text_surface, (text_x, text_y))
    
    def _wrap_text(self, text, max_width):
        """テキストを指定幅で改行（日本語対応）"""
        if not text:
            return [""]
        
        # 日本語テキストは文字単位で改行判定
        lines = []
        current_line = ""
        
        for char in text:
            test_line = current_line + char
            try:
                # フォントサイズでテキスト幅をチェック
                text_width = self.font.size(test_line)[0]
                if text_width <= max_width - 20:
                    current_line = test_line
                else:
                    # 現在の行を保存して新しい行を開始
                    if current_line:
                        lines.append(current_line)
                    current_line = char
            except:
                # フォント処理でエラーが発生した場合は文字を追加
                current_line = test_line
        
        # 最後の行を追加
        if current_line:
            lines.append(current_line)
        
        return lines if lines else [text]
    
    def clear_all(self):
        """すべての通知をクリア"""
        self.notifications.clear()
        if self.debug:
            print("すべての通知をクリア")
    
    def add_test_notification(self):
        """テスト用通知を追加"""
        self.add_notification("テスト通知です")
        print("[NOTIFICATION] テスト通知を追加しました")
    
    def get_notification_count(self):
        """現在の通知数を取得"""
        return len(self.notifications)