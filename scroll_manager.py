import pygame
from config import *

class ScrollManager:
    def __init__(self, debug=False):
        self.debug = debug
        self.scroll_mode = False  # スクロールモードのON/OFF
        self.scroll_lines = []  # スクロール表示用の行データ
        self.max_lines = 3  # 最大表示行数
        self.current_speaker = None  # 現在の話者
        self.last_background = None  # 最後の背景
        self.verbose_debug = False  # 詳細デバッグフラグ
        
    def should_start_scroll(self, speaker, background, active_characters):
        """スクロールを開始すべきかどうかを判定（簡素化版）"""
        if self.verbose_debug:
            print(f"[DEBUG] should_start_scroll: speaker={speaker}, current={self.current_speaker}")
            print(f"[DEBUG] background={background}, last_bg={self.last_background}")
        
        # 既にスクロールモードの場合は開始判定しない
        if self.scroll_mode:
            return False
        
        # 話者が存在しない場合はスクロールしない
        if not speaker:
            self._update_state(speaker, background, active_characters)
            return False
        
        # 前回の対話情報がない場合（初回）は記録のみ
        if self.current_speaker is None:
            if self.debug:
                print(f"[SCROLL] 初回対話記録: {speaker} @{background}")
            self._update_state(speaker, background, active_characters)
            return False
        
        # スクロール開始の条件：話者が同じ場合（背景変更は無視）
        same_speaker = (self.current_speaker == speaker)
        
        if self.verbose_debug:
            print(f"[DEBUG] same_speaker={same_speaker}")
        
        # 状態を更新（判定前に更新）
        self._update_state(speaker, background, active_characters)
        
        # 同じ話者の場合はスクロール開始
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
        
        # スクロールモードでない場合は継続不可
        if not self.scroll_mode:
            return False
            
        # 話者が変わった場合は継続不可
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
        
        # 初期テキストを行に分割して追加
        if initial_text:
            self.add_text_to_scroll(initial_text)
    
    def add_text_to_scroll(self, text):
        """テキストをスクロール表示に追加（26文字で改行、正確なログ表示）"""
        if not text:
            return
            
        if self.verbose_debug:
            print(f"[DEBUG] スクロールにテキスト追加: '{text[:20]}...'")
        
        # テキストを26文字ごとに分割
        lines = []
        for i in range(0, len(text), 26):
            lines.append(text[i:i+26])
        
        # 古い行数を記録
        old_line_count = len(self.scroll_lines)
        
        # 全ての行を追加（26文字改行を維持）
        for line in lines:
            self.scroll_lines.append(line)
            if self.verbose_debug:
                print(f"[DEBUG] 行追加: '{line}'")
            
            # 3行を超えた場合のみ古い行を削除
            while len(self.scroll_lines) > self.max_lines:
                removed_line = self.scroll_lines.pop(0)
                if self.verbose_debug:
                    print(f"[DEBUG] 行削除: '{removed_line}'")
        
        # 実際に増加した行数を計算（削除された行も考慮）
        new_line_count = len(self.scroll_lines)
        actual_added_lines = min(len(lines), self.max_lines)
        
        if self.debug:
            if actual_added_lines == 1:
                print(f"[SCROLL] 1行追加, 合計{new_line_count}行")
            else:
                print(f"[SCROLL] {actual_added_lines}行追加, 合計{new_line_count}行")
    
    def continue_scroll(self, speaker, background, active_characters, new_text):
        """スクロールを継続"""
        if self.verbose_debug:
            print(f"[DEBUG] continue_scroll呼び出し: speaker={speaker}")
        
        if self.should_continue_scroll(speaker, background, active_characters):
            # 状態を更新してからテキスト追加
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
        self.scroll_mode = False
        self.scroll_lines = []
        # 状態はリセットしない（次回の判定で使用するため）
    
    def is_scroll_mode(self):
        """スクロールモードかどうかを返す"""
        return self.scroll_mode
    
    def get_scroll_lines(self):
        """現在のスクロール行を取得"""
        return self.scroll_lines.copy()
    
    def reset_state(self):
        """状態を完全にリセット（新しいシーンなどで使用）"""
        if self.debug:
            print(f"[DEBUG] ScrollManager状態リセット")
        self.scroll_mode = False
        self.scroll_lines = []
        self.current_speaker = None
        self.last_background = None
    
    def soft_reset_for_background_change(self):
        """背景変更時のソフトリセット（スクロールモードは維持）"""
        if self.debug:
            print(f"[DEBUG] 背景変更用ソフトリセット - スクロールモード維持")
        # 背景変更時はスクロールモードを維持
        # スクロール行も維持（話者が同じなら継続可能）
        self.last_background = None  # 背景情報のみリセット
    
    def force_end_scroll_and_reset(self):
        """スクロール強制終了と状態リセット（完全リセット時）"""
        if self.debug:
            print(f"[DEBUG] スクロール強制終了と状態リセット")
        self.scroll_mode = False
        self.scroll_lines = []
        # 完全リセット
        self.current_speaker = None
        self.last_background = None
    
    def get_current_line_count(self):
        """現在のスクロール行数を取得"""
        return len(self.scroll_lines)
    
    def get_last_added_lines_count(self, text):
        """最後に追加されたテキストの行数を計算"""
        if not text:
            return 0
        lines = 0
        for i in range(0, len(text), 26):
            lines += 1
        return lines
    
    def is_continuing_same_speaker(self, speaker):
        """同じ話者による継続かどうか"""
        return self.current_speaker == speaker and self.scroll_mode