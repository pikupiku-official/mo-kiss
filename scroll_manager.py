import pygame
from config import *

class ScrollManager:
    def __init__(self, debug=False):
        self.debug = debug
        
        # スクロール状態
        self.scroll_mode = False
        self.scroll_lines = []  # スクロール表示用のテキストブロック
        self.max_lines = 3  # 最大表示ブロック数
        
        # 話者管理
        self.current_speaker = None
        
        # TextRendererへの参照（終了通知用）
        self.text_renderer = None
        
    def set_text_renderer(self, text_renderer):
        """TextRendererの参照を設定"""
        self.text_renderer = text_renderer
        
    def start_scroll_mode(self, speaker, text):
        """スクロールモードを開始"""
        if self.debug:
            print(f"[SCROLL] スクロール開始: {speaker} - '{text[:30] if text else ''}...'")
        
        self.scroll_mode = True
        self.current_speaker = speaker
        self.scroll_lines = [text]  # 最初のテキストで初期化
        
    def add_text_to_scroll(self, text):
        """テキストをスクロール表示に追加"""
        if not text:
            return
            
        if self.debug:
            print(f"[SCROLL] テキストブロック追加: '{text[:30]}...'")
        
        self.scroll_lines.append(text)
        
        # 最大ブロック数を超えた場合は古いブロックを削除
        while len(self.scroll_lines) > self.max_lines:
            removed_line = self.scroll_lines.pop(0)
            if self.debug:
                print(f"[SCROLL] 古いブロック削除: '{removed_line[:30]}...'")
        
        if self.debug:
            print(f"[SCROLL] 現在のブロック数: {len(self.scroll_lines)}/{self.max_lines}")
    
    def should_continue_scroll(self, speaker):
        """スクロール継続可能かを判定"""
        if not self.scroll_mode:
            return False
            
        if speaker != self.current_speaker:
            if self.debug:
                print(f"[SCROLL] 話者変更により継続不可: {self.current_speaker} -> {speaker}")
            return False
            
        return True
    
    def continue_scroll(self, speaker, text):
        """スクロールを継続"""
        if self.should_continue_scroll(speaker):
            self.add_text_to_scroll(text)
            if self.debug:
                print(f"[SCROLL] 継続成功: {speaker}")
            return True
        else:
            if self.debug:
                print(f"[SCROLL] 継続失敗、スクロール終了")
            self.end_scroll_mode()
            return False
    
    def process_scroll_stop_command(self):
        """scroll-stopコマンドによるスクロール終了"""
        if self.debug:
            print(f"[SCROLL] scroll-stopコマンドによりスクロール終了")
        
        if self.scroll_mode and self.text_renderer:
            self.text_renderer.set_scroll_ended_flag()
        
        self.end_scroll_mode()
    
    def end_scroll_mode(self):
        """スクロールモードを終了"""
        if self.debug:
            print(f"[SCROLL] スクロールモード終了")
        
        # スクロール終了をTextRendererに通知
        if self.scroll_mode and self.text_renderer:
            self.text_renderer.set_scroll_ended_flag()
        
        self.scroll_mode = False
        self.scroll_lines = []
        # current_speakerはリセットしない（次回の判定で使用するため）
    
    def force_end_scroll_mode(self):
        """強制的にスクロールモードを終了（背景変更時など）"""
        if self.debug:
            print(f"[SCROLL] 強制スクロール終了")
        
        if self.scroll_mode and self.text_renderer:
            self.text_renderer.set_scroll_ended_flag()
        
        self.scroll_mode = False
        self.scroll_lines = []
        self.current_speaker = None  # 強制終了時は話者もリセット
    
    def is_scroll_mode(self):
        """スクロールモードかどうかを返す"""
        return self.scroll_mode
    
    def get_scroll_lines(self):
        """現在のスクロールテキストブロックを取得"""
        return self.scroll_lines.copy()
    
    def get_current_speaker(self):
        """現在の話者を取得"""
        return self.current_speaker
    
    def reset_state(self):
        """状態を完全にリセット"""
        if self.debug:
            print(f"[SCROLL] 状態完全リセット")
        
        if self.scroll_mode and self.text_renderer:
            self.text_renderer.set_scroll_ended_flag()
        
        self.scroll_mode = False
        self.scroll_lines = []
        self.current_speaker = None