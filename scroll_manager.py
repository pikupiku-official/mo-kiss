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
        self.last_active_characters = set()  # 最後のアクティブキャラクター
        self.last_dialogue_info = None  # 最後の対話情報（初回判定用）
        self.verbose_debug = False  # 詳細デバッグフラグ
        
    def should_start_scroll(self, speaker, background, active_characters):
        """スクロールを開始すべきかどうかを判定"""
        if self.verbose_debug:
            print(f"[DEBUG] should_start_scroll呼び出し: speaker={speaker}")
            print(f"[DEBUG] current_speaker={self.current_speaker}, last_background={self.last_background}")
            print(f"[DEBUG] last_dialogue_info={self.last_dialogue_info}")
            print(f"[DEBUG] 現在のactive_characters={set(active_characters) if active_characters else set()}")
        
        # 既にスクロールモードの場合は継続チェック（この関数では判定しない）
        if self.scroll_mode:
            if self.verbose_debug:
                print(f"[DEBUG] 既にスクロールモード中 - should_start_scrollでは判定しない")
            return False
        
        # 話者が存在しない場合はスクロールしない
        if not speaker:
            if self.verbose_debug:
                print(f"[DEBUG] 話者が存在しないためスクロール開始しない")
            self._update_state(speaker, background, active_characters)
            return False
        
        # 前回の対話情報がない場合（初回）は記録のみ
        if self.last_dialogue_info is None:
            if self.debug:
                print(f"[SCROLL] 初回対話記録: {speaker} @{background}")
            self._update_state(speaker, background, active_characters)
            return False
        
        # 前回の対話と比較してスクロール開始条件をチェック
        last_speaker, last_bg, _ = self.last_dialogue_info
        same_speaker = (last_speaker == speaker)
        same_background = (last_bg == background)
        
        if self.verbose_debug:
            print(f"[DEBUG] 前回対話: speaker={last_speaker}, background={last_bg}")
            print(f"[DEBUG] same_speaker={same_speaker}, same_background={same_background}")
        
        # 状態を更新
        self._update_state(speaker, background, active_characters)
        
        # スクロール開始の条件：話者が同じで、背景が同じならOK
        # または、話者が同じなら背景が変わってもスクロール可能
        if same_speaker and same_background:
            if self.debug:
                print(f"[SCROLL] スクロール開始: {speaker} (同一話者・背景)")
            return True
        elif same_speaker and not same_background:
            if self.debug:
                print(f"[SCROLL] スクロール開始: {speaker} (同一話者・背景変更)")
            return True
        
        if self.verbose_debug:
            print(f"[DEBUG] スクロール開始条件を満たしていません")
        return False
    
    def _update_state(self, speaker, background, active_characters):
        """内部状態を更新"""
        self.current_speaker = speaker
        self.last_background = background
        self.last_active_characters = set(active_characters) if active_characters else set()
        self.last_dialogue_info = (speaker, background, set(active_characters) if active_characters else set())
        
        if self.verbose_debug:
            print(f"[DEBUG] 状態更新: speaker={speaker}, bg={background}")
    
    def should_continue_scroll(self, speaker, background, active_characters):
        """スクロール継続の条件をチェック"""
        if self.verbose_debug:
            print(f"[DEBUG] should_continue_scroll: speaker={speaker}, current={self.current_speaker}")
        
        # 初回チェック
        if self.current_speaker is None:
            if self.verbose_debug:
                print(f"[DEBUG] current_speakerがNoneのため継続不可")
            return False
            
        # 話者が変わった場合
        if speaker != self.current_speaker:
            if self.debug:
                print(f"[SCROLL] 話者変更によりスクロール終了: {self.current_speaker} -> {speaker}")
            return False
            
        # 背景が変わった場合
        if background != self.last_background:
            if self.debug:
                print(f"[SCROLL] 背景変更によりスクロール終了: {self.last_background} -> {background}")
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
        self.last_active_characters = set(active_characters) if active_characters else set()
        self.scroll_lines = []
        
        # 初期テキストを行に分割して追加
        if initial_text:
            self.add_text_to_scroll(initial_text)
    
    def add_text_to_scroll(self, text):
        """テキストをスクロール表示に追加（2行でも3行目に追加可能）"""
        if not text:
            return
            
        if self.verbose_debug:
            print(f"[DEBUG] スクロールにテキスト追加: '{text[:20]}...'")
        
        # テキストを26文字ごとに分割
        lines = []
        for i in range(0, len(text), 26):
            lines.append(text[i:i+26])
        
        lines_added = 0
        # 各行をスクロールリストに追加
        for line in lines:
            self.scroll_lines.append(line)
            lines_added += 1
            if self.verbose_debug:
                print(f"[DEBUG] 行追加: '{line}'")
            
            # 3行を超えた場合のみ古い行を削除
            while len(self.scroll_lines) > self.max_lines:
                removed_line = self.scroll_lines.pop(0)
                if self.verbose_debug:
                    print(f"[DEBUG] 行削除: '{removed_line}'")
        
        if self.debug:
            print(f"[SCROLL] {lines_added}行追加, 合計{len(self.scroll_lines)}行")
    
    def continue_scroll(self, speaker, background, active_characters, new_text):
        """スクロールを継続"""
        if self.verbose_debug:
            print(f"[DEBUG] continue_scroll呼び出し: speaker={speaker}")
        
        if self.should_continue_scroll(speaker, background, active_characters):
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
        # 注意：状態はリセットしない（次回の判定で使用するため）
    
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
        self.last_active_characters = set()
        self.last_dialogue_info = None
    
    def soft_reset_for_background_change(self):
        """背景変更時のソフトリセット（継続性は一部保持）"""
        if self.debug:
            print(f"[DEBUG] 背景変更用ソフトリセット - スクロールモードのみ終了")
        # スクロールモードのみ終了、状態情報は保持（次の判定で使用）
        self.scroll_mode = False
        self.scroll_lines = []
        # current_speaker, last_background, last_dialogue_infoは保持
    
    def force_end_scroll_and_reset(self):
        """スクロール強制終了と状態リセット（完全リセット時）"""
        if self.debug:
            print(f"[DEBUG] スクロール強制終了と状態リセット")
        self.scroll_mode = False
        self.scroll_lines = []
        # 完全リセット
        self.current_speaker = None
        self.last_background = None
        self.last_active_characters = set()
        self.last_dialogue_info = None