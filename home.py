"""
家モジュール - プレイヤーの部屋画面

家では以下の選択肢が提供される：
- 寝る：次の日の朝に時間を進めてmapモジュールへ
- メインメニューへ：main_menuモジュールへ
"""

import pygame
import sys
import os
from time_manager import get_time_manager

class HomeModule:
    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.Font(None, 48)
        self.large_font = pygame.font.Font(None, 64)
        
        # 選択肢データ
        self.choices = [
            {"text": "寝る", "action": "sleep"},
            {"text": "メインメニューへ", "action": "main_menu"}
        ]
        self.selected_choice = 0
        
        # 色設定
        self.bg_color = (20, 30, 50)
        self.text_color = (255, 255, 255)
        self.selected_color = (255, 220, 100)
        self.border_color = (100, 150, 200)
        
    def handle_events(self, events):
        """イベント処理"""
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    self.selected_choice = (self.selected_choice - 1) % len(self.choices)
                    print(f"[HOME] 選択: {self.choices[self.selected_choice]['text']}")
                    
                elif event.key == pygame.K_DOWN:
                    self.selected_choice = (self.selected_choice + 1) % len(self.choices)
                    print(f"[HOME] 選択: {self.choices[self.selected_choice]['text']}")
                    
                elif event.key == pygame.K_RETURN:
                    selected_action = self.choices[self.selected_choice]["action"]
                    print(f"[HOME] 実行: {selected_action}")
                    
                    if selected_action == "sleep":
                        # 時間管理：次の日の朝に設定
                        time_manager = get_time_manager()
                        time_manager.set_to_morning()
                        print("[HOME] 睡眠完了 - mapモジュールへ遷移")
                        return "go_to_map"
                        
                    elif selected_action == "main_menu":
                        print("[HOME] メインメニューへ遷移")
                        return "go_to_main_menu"
                        
        return None
    
    def update(self):
        """更新処理"""
        pass
    
    def render(self):
        """描画処理"""
        # 背景
        self.screen.fill(self.bg_color)
        
        # タイトル
        time_manager = get_time_manager()
        time_str = time_manager.get_full_time_string()
        title_text = self.large_font.render(f"家 - {time_str}", True, self.text_color)
        title_rect = title_text.get_rect(center=(self.screen.get_width() // 2, 100))
        self.screen.blit(title_text, title_rect)
        
        # 選択肢描画
        start_y = 250
        choice_height = 80
        
        for i, choice in enumerate(self.choices):
            y_pos = start_y + (i * choice_height)
            
            # 選択中の場合はハイライト
            if i == self.selected_choice:
                color = self.selected_color
                # 背景ボックス
                choice_rect = pygame.Rect(self.screen.get_width() // 2 - 200, y_pos - 20, 400, 60)
                pygame.draw.rect(self.screen, self.border_color, choice_rect, 3)
            else:
                color = self.text_color
            
            # テキスト描画
            choice_text = self.font.render(choice["text"], True, color)
            choice_rect = choice_text.get_rect(center=(self.screen.get_width() // 2, y_pos))
            self.screen.blit(choice_text, choice_rect)
        
        # 操作説明
        help_text = "↑↓キー: 選択  Enter: 決定"
        help_surface = self.font.render(help_text, True, (150, 150, 150))
        help_rect = help_surface.get_rect(center=(self.screen.get_width() // 2, self.screen.get_height() - 50))
        self.screen.blit(help_surface, help_rect)