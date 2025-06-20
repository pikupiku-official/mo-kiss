#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pygame
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from event_base import EventBase
from dialogue_loader import DialogueLoader

class E001(EventBase):
    """E001: 孤高のギャルとの初対面（分岐機能付き）"""
    
    def __init__(self):
        super().__init__()
        self.dialogue_loader = DialogueLoader(debug=True)
    
    def run_event(self, event_id, event_title, heroine_name):
        """E001イベントを実行"""
        print(f"🎭 E001イベント開始: {event_title}")
        
        # .ksファイルからダイアログデータを読み込み
        ks_file_path = os.path.join(os.path.dirname(__file__), "E001_test.ks")
        dialogue_data = self.dialogue_loader.load_dialogue_from_ks(ks_file_path)
        
        # ストーリーコマンドを処理
        processed_data = self.process_story_commands(dialogue_data)
        
        self.running = True
        current_text = 0
        user_choice = None
        
        while self.running and current_text < len(processed_data):
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    return "quit"
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                        return "back_to_map"
                    elif event.key == pygame.K_SPACE:
                        current_item = processed_data[current_text]
                        
                        # 選択肢の処理
                        if current_item.get('type') == 'choice':
                            user_choice = self.handle_choice(current_item.get('options', []))
                            if user_choice is not None:
                                # 選択肢の結果をフラグとして設定
                                self.dialogue_loader.execute_story_command({
                                    'type': 'flag_set',
                                    'name': 'choice',
                                    'value': user_choice + 1
                                })
                        
                        current_text += 1
                        if current_text >= len(processed_data):
                            self.running = False
                            return "back_to_map"
            
            # 画面描画
            if current_text < len(processed_data):
                self.draw_dialogue_screen(processed_data, current_text)
            
            pygame.display.flip()
            self.clock.tick(60)
        
        return "back_to_map"
    
    def process_story_commands(self, dialogue_data):
        """ストーリーコマンドを処理して実行可能なダイアログデータを生成"""
        processed_data = []
        skip_mode = False
        condition_stack = []
        
        for item in dialogue_data:
            if item.get('type') == 'if_start':
                # 条件分岐開始
                condition = item.get('condition', '')
                is_condition_met = self.dialogue_loader.check_condition(condition)
                condition_stack.append(is_condition_met)
                skip_mode = not is_condition_met
                continue
                
            elif item.get('type') == 'if_end':
                # 条件分岐終了
                if condition_stack:
                    condition_stack.pop()
                skip_mode = len(condition_stack) > 0 and not all(condition_stack)
                continue
                
            elif item.get('type') == 'event_control':
                # イベント制御コマンドを実行
                if not skip_mode:
                    self.dialogue_loader.execute_story_command(item)
                continue
                
            elif item.get('type') == 'flag_set':
                # フラグ設定コマンドを実行
                if not skip_mode:
                    self.dialogue_loader.execute_story_command(item)
                continue
            
            # 条件に応じてアイテムを追加
            if not skip_mode:
                processed_data.append(item)
        
        return processed_data
    
    def handle_choice(self, options):
        """選択肢を処理"""
        if len(options) < 2:
            return None
        
        print(f"🎯 選択肢表示: {options}")
        
        choice_running = True
        selected_option = 0
        
        while choice_running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return None
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return None
                    elif event.key == pygame.K_UP:
                        selected_option = (selected_option - 1) % len(options)
                    elif event.key == pygame.K_DOWN:
                        selected_option = (selected_option + 1) % len(options)
                    elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                        print(f"✅ 選択: {selected_option + 1} - {options[selected_option]}")
                        return selected_option
            
            # 選択肢画面を描画
            self.draw_choice_screen(options, selected_option)
            pygame.display.flip()
            self.clock.tick(60)
        
        return None
    
    def draw_choice_screen(self, options, selected_option):
        """選択肢画面を描画"""
        self.screen.fill(self.colors['background'])
        
        # タイトル
        title_text = self.fonts['large'].render("選択してください", True, self.colors['text_color'])
        title_rect = title_text.get_rect(center=(self.screen_width // 2, 200))
        self.screen.blit(title_text, title_rect)
        
        # 選択肢
        for i, option in enumerate(options):
            color = self.colors['name_color'] if i == selected_option else self.colors['text_color']
            prefix = "▶ " if i == selected_option else "  "
            
            option_text = self.fonts['medium'].render(f"{prefix}{i + 1}. {option}", True, color)
            option_rect = option_text.get_rect(center=(self.screen_width // 2, 300 + i * 50))
            self.screen.blit(option_text, option_rect)
        
        # 操作説明
        help_text = self.fonts['small'].render("↑↓: 選択  Enter/Space: 決定  ESC: キャンセル", True, self.colors['text_color'])
        help_rect = help_text.get_rect(center=(self.screen_width // 2, self.screen_height - 50))
        self.screen.blit(help_text, help_rect)
    
    def draw_dialogue_screen(self, dialogue_data, current_text):
        """ダイアログ画面を描画"""
        if current_text >= len(dialogue_data):
            return
        
        current_item = dialogue_data[current_text]
        
        self.screen.fill(self.colors['background'])
        
        if current_item.get('type') == 'dialogue':
            # テキストボックス描画
            text_box_rect = pygame.Rect(50, self.screen_height - 200, 
                                      self.screen_width - 100, 150)
            pygame.draw.rect(self.screen, self.colors['text_box'], text_box_rect)
            pygame.draw.rect(self.screen, self.colors['button_color'], text_box_rect, 3)
            
            # 話者名
            speaker = current_item.get('character', 'Unknown')
            speaker_text = self.fonts['medium'].render(speaker, True, self.colors['name_color'])
            self.screen.blit(speaker_text, (text_box_rect.left + 20, text_box_rect.top + 10))
            
            # セリフ
            dialogue_text = current_item.get('text', '')
            text_surface = self.fonts['small'].render(dialogue_text, True, self.colors['text_color'])
            self.screen.blit(text_surface, (text_box_rect.left + 20, text_box_rect.top + 45))
            
            # 進行表示
            progress_text = self.fonts['small'].render(f"{current_text + 1}/{len(dialogue_data)}", True, self.colors['text_color'])
            self.screen.blit(progress_text, (text_box_rect.right - 100, text_box_rect.bottom - 30))

# イベントインスタンスを作成
event_instance = E001()

def run_event(event_id, event_title, heroine_name):
    """E001イベント実行関数"""
    return event_instance.run_event(event_id, event_title, heroine_name)