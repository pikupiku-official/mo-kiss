import pygame
from config import *

class ScrollManager:
    def __init__(self, debug=False):
        self.debug = debug
        
        # スクロール状態
        self.scroll_mode = False
        self.scroll_lines = []  # スクロール表示用のテキストブロック
        self.max_lines = 3  # 最大表示ブロック数
        self.all_scroll_text = []  # バックログ用：削除されたブロックも含むすべてのテキスト
        
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
        self.all_scroll_text = [text]  # バックログ用にも記録
        
    def add_text_to_scroll(self, text):
        """テキストをスクロール表示に追加"""
        if not text:
            return
            
        if self.debug:
            print(f"[SCROLL] テキストブロック追加: '{text[:30]}...'")
        
        self.scroll_lines.append(text)
        self.all_scroll_text.append(text)  # バックログ用にも記録
        
        # 最大ブロック数を超えた場合は古いブロックを削除（表示用のみ、all_scroll_textは保持）
        while len(self.scroll_lines) > self.max_lines:
            removed_line = self.scroll_lines.pop(0)
            if self.debug:
                print(f"[SCROLL] 古いブロック削除（表示用のみ）: '{removed_line[:30]}...'")
        
        if self.debug:
            print(f"[SCROLL] 現在のブロック数: {len(self.scroll_lines)}/{self.max_lines}")
            print(f"[SCROLL] バックログ用テキスト数: {len(self.all_scroll_text)}")
    
    def should_continue_scroll(self, speaker):
        """スクロール継続可能かを判定 - [scroll-stop]まで継続"""
        if not self.scroll_mode:
            return False
            
        # 話者が変わってもスクロールを継続（[scroll-stop]まで）
        if speaker != self.current_speaker:
            if self.debug:
                print(f"[SCROLL] 話者変更でもスクロール継続: {self.current_speaker} -> {speaker}")
            # 現在の話者を新しい話者に更新
            self.current_speaker = speaker
            
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
            return False
    
    def process_scroll_stop_command(self):
        """scroll-stopコマンドによるスクロール終了 - 次のテキストから新しい表示を開始"""
        if self.debug:
            print(f"[SCROLL] scroll-stopコマンドによりスクロール終了、次のテキストから新規表示開始")
        
        # スクロール中のすべてのテキスト（削除されたものも含む）をバックログに追加
        if self.scroll_mode and self.text_renderer and self.text_renderer.backlog_manager:
            combined_text = "".join(self.all_scroll_text)
            if combined_text and self.current_speaker:
                self.text_renderer.backlog_manager.add_entry(self.current_speaker, combined_text)
                # スクロール終了時にフラグを設定
                self.text_renderer.backlog_added_for_current = True
                if self.debug:
                    print(f"[BACKLOG] スクロール終了時にすべてのテキストをバックログに追加: {self.current_speaker} - {combined_text[:50]}... (全{len(self.all_scroll_text)}ブロック)")
        
        if self.scroll_mode and self.text_renderer:
            self.text_renderer.set_scroll_ended_flag()
        
        # スクロール状態をリセットして次のテキストから新しく開始できるようにする
        self.scroll_mode = False
        self.scroll_lines = []
        self.all_scroll_text = []  # バックログ用リストもリセット
        self.current_speaker = None
    
    def end_scroll_mode(self):
        """スクロールモードを終了 - scroll-stopコマンド以外では呼び出されない"""
        if self.debug:
            print(f"[SCROLL] スクロールモード終了（内部呼び出し）")
        
        # scroll-stopコマンド以外では自動的にスクロールを終了しない
        # この関数は process_scroll_stop_command からのみ呼び出されるべき
        pass
    
    def force_end_scroll_mode(self):
        """強制的にスクロールモードを終了 - 使用しない"""
        if self.debug:
            print(f"[SCROLL] 強制スクロール終了は無効化されています")
        
        # 強制終了機能を無効化
        # scroll-stopコマンド以外でスクロールを停止しない
        pass
    
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
        """状態を完全にリセット - 使用しない"""
        if self.debug:
            print(f"[SCROLL] 状態リセットは無効化されています")
        
        # 状態リセット機能を無効化
        # scroll-stopコマンド以外でスクロールを停止しない
        pass