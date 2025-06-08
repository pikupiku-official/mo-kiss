import pygame
from config import *

class ScrollManager:
    def __init__(self, debug=False):
        self.debug = debug
        self.scroll_mode = False  # スクロールモードのON/OFF
        self.scroll_lines = []  # スクロール表示用の行データ (完全なテキストブロックを格納)
        self.max_lines = 3  # 最大表示ブロック数 (以前は行数だったが、ここではブロック単位)
        self.current_speaker = None  # 現在の話者
        self.last_background = None  # 最後の背景
        self.verbose_debug = False  # 詳細デバッグフラグ
        self.text_renderer = None  # TextRendererへの参照（終了通知用）
        
    def set_text_renderer(self, text_renderer):
        """TextRendererの参照を設定（スクロール終了通知用）"""
        self.text_renderer = text_renderer
        
    def should_start_scroll(self, speaker, background, active_characters):
        """スクロールを開始すべきかどうかを判定（簡素化版）"""
        if self.verbose_debug:
            print(f"[DEBUG] should_start_scroll: speaker={speaker}, current={self.current_speaker}")
            print(f"[DEBUG] background={background}, last_bg={self.last_background}")
        
        if self.scroll_mode:
            return False
        
        if not speaker:
            self._update_state(speaker, background, active_characters)
            return False
        
        if self.current_speaker is None:
            if self.debug:
                print(f"[SCROLL] 初回対話記録: {speaker} @{background}")
            self._update_state(speaker, background, active_characters)
            return False
        
        same_speaker = (self.current_speaker == speaker)
        
        if self.verbose_debug:
            print(f"[DEBUG] same_speaker={same_speaker}")
        
        self._update_state(speaker, background, active_characters)
        
        if same_speaker:
            if self.debug:
                print(f"[SCROLL] スクロール開始: {speaker} (同一話者)")
            return True
        
        return False
    
    def _update_state(self, speaker, background, active_characters):
        """内部状態を更新"""
        self.current_speaker = speaker
        self.last_background = background
        
        if self.verbose_debug:
            print(f"[DEBUG] 状態更新: speaker={speaker}, bg={background}")
    
    def should_continue_scroll(self, speaker, background, active_characters):
        """スクロール継続の条件をチェック（簡素化版）"""
        if self.verbose_debug:
            print(f"[DEBUG] should_continue_scroll: speaker={speaker}, current={self.current_speaker}")
        
        if not self.scroll_mode:
            return False
            
        if speaker != self.current_speaker:
            if self.debug:
                print(f"[SCROLL] 話者変更によりスクロール終了: {self.current_speaker} -> {speaker}")
            return False
            
        if self.verbose_debug:
            print(f"[DEBUG] スクロール継続条件満たしました")
        return True
    
    def start_scroll_mode(self, speaker, background, active_characters, initial_text):
        """スクロールモードを開始"""
        if self.debug:
            print(f"[SCROLL] スクロール開始: {speaker} - '{initial_text[:30] if initial_text else ''}...'")
        
        self.scroll_mode = True
        self.current_speaker = speaker
        self.last_background = background
        self.scroll_lines = []
        
        if initial_text:
            self.add_text_to_scroll(initial_text)
    
    def add_text_to_scroll(self, text):
        """テキストをスクロール表示に追加（テキストブロック単位）"""
        if not text:
            return
            
        if self.verbose_debug:
            print(f"[DEBUG] スクロールにテキスト追加: '{text[:30]}...'")
        
        # テキストをそのまま1つのブロックとして追加
        self.scroll_lines.append(text)
        if self.verbose_debug:
            print(f"[DEBUG] テキストブロック追加: '{text}'")
            
        # 最大ブロック数を超えた場合のみ古いブロックを削除
        while len(self.scroll_lines) > self.max_lines:
            removed_line = self.scroll_lines.pop(0)
            if self.verbose_debug:
                print(f"[DEBUG] テキストブロック削除: '{removed_line}'")
        
        new_block_count = len(self.scroll_lines)
        
        if self.debug:
            # 1つのテキストブロックが追加されたことを示す
            print(f"[SCROLL] 1テキストブロック追加, 合計{new_block_count}ブロック")
    
    def continue_scroll(self, speaker, background, active_characters, new_text):
        """スクロールを継続"""
        if self.verbose_debug:
            print(f"[DEBUG] continue_scroll呼び出し: speaker={speaker}")
        
        if self.should_continue_scroll(speaker, background, active_characters):
            self._update_state(speaker, background, active_characters)
            self.add_text_to_scroll(new_text)
            if self.debug:
                print(f"[SCROLL] 継続成功: {speaker}")
            return True
        else:
            if self.debug:
                print(f"[SCROLL] 継続失敗、終了")
            self.end_scroll_mode()
            return False
    
    def end_scroll_mode(self):
        """スクロールモードを終了"""
        if self.debug:
            print(f"[DEBUG] スクロールモード終了")
        
        # スクロール終了をTextRendererに通知
        if self.scroll_mode and self.text_renderer:
            self.text_renderer.set_scroll_ended_flag()
        
        self.scroll_mode = False
        self.scroll_lines = []
        # 状態はリセットしない（次回の判定で使用するため）
    
    def is_scroll_mode(self):
        """スクロールモードかどうかを返す"""
        return self.scroll_mode
    
    def get_scroll_lines(self):
        """現在のスクロールテキストブロックを取得"""
        return self.scroll_lines.copy()
    
    def reset_state(self):
        """状態を完全にリセット（新しいシーンなどで使用）"""
        if self.debug:
            print(f"[DEBUG] ScrollManager状態リセット")
        
        # スクロール終了をTextRendererに通知
        if self.scroll_mode and self.text_renderer:
            self.text_renderer.set_scroll_ended_flag()
        
        self.scroll_mode = False
        self.scroll_lines = []
        self.current_speaker = None
        self.last_background = None
    
    def soft_reset_for_background_change(self):
        """背景変更時のソフトリセット（スクロールモードは維持）"""
        if self.debug:
            print(f"[DEBUG] 背景変更用ソフトリセット - スクロールモード維持")
        self.last_background = None
    
    def force_end_scroll_and_reset(self):
        """スクロール強制終了と状態リセット（完全リセット時）"""
        if self.debug:
            print(f"[DEBUG] スクロール強制終了と状態リセット")
        
        # スクロール終了をTextRendererに通知
        if self.scroll_mode and self.text_renderer:
            self.text_renderer.set_scroll_ended_flag()
        
        self.scroll_mode = False
        self.scroll_lines = []
        self.current_speaker = None
        self.last_background = None
    
    def get_current_line_count(self):
        """現在のスクロールブロック数を取得"""
        return len(self.scroll_lines)
    
    def get_last_added_lines_count(self, text):
        """最後に追加されたテキストが何ブロック分に相当するかを計算（常に1ブロック）"""
        if not text:
            return 0
        return 1 # テキストは1ブロックとして扱われる
    
    def is_continuing_same_speaker(self, speaker):
        """同じ話者による継続かどうか"""
        return self.current_speaker == speaker and self.scroll_mode