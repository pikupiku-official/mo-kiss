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
        
    def should_start_scroll(self, speaker, background, active_characters):
        """スクロールを開始すべきかどうかを判定"""
        print(f"[DEBUG] should_start_scroll呼び出し: speaker={speaker}")
        print(f"[DEBUG] current_speaker={self.current_speaker}, last_background={self.last_background}")
        print(f"[DEBUG] last_active_characters={self.last_active_characters}")
        print(f"[DEBUG] 現在のactive_characters={set(active_characters)}")
        
        # 既にスクロールモードの場合は継続チェック（この関数では判定しない）
        if self.scroll_mode:
            print(f"[DEBUG] 既にスクロールモード中 - should_start_scrollでは判定しない")
            return False
        
        # 新規スクロール開始の条件
        if speaker:
            # 前回と同じ状態かチェック
            same_speaker = (self.current_speaker == speaker)
            same_background = (self.last_background == background)
            
            print(f"[DEBUG] same_speaker={same_speaker}, same_background={same_background}")
            
            # スクロール開始の条件：話者が同じで、背景が同じならOK
            if same_speaker and same_background:
                print(f"[DEBUG] スクロール開始条件満たしました: 話者={speaker}")
                return True
            
            # 状態を更新（次回の判定のため）
            print(f"[DEBUG] 状態更新: {self.current_speaker} -> {speaker}")
            self.current_speaker = speaker
            self.last_background = background
            self.last_active_characters = set(active_characters)
            
        print(f"[DEBUG] スクロール開始条件を満たしていません")
        return False
    
    def should_continue_scroll(self, speaker, background, active_characters):
        """スクロール継続の条件をチェック"""
        print(f"[DEBUG] should_continue_scroll: speaker={speaker}, current={self.current_speaker}")
        
        # 初回チェック
        if self.current_speaker is None:
            print(f"[DEBUG] current_speakerがNoneのため継続不可")
            return False
            
        # 話者が変わった場合
        if speaker != self.current_speaker:
            print(f"[DEBUG] 話者変更によりスクロール終了: {self.current_speaker} -> {speaker}")
            return False
            
        # 背景が変わった場合
        if background != self.last_background:
            print(f"[DEBUG] 背景変更によりスクロール終了: {self.last_background} -> {background}")
            return False
            
        print(f"[DEBUG] スクロール継続条件満たしました")
        return True
    
    def start_scroll_mode(self, speaker, background, active_characters, initial_text):
        """スクロールモードを開始"""
        print(f"[DEBUG] スクロールモード開始: 話者={speaker}, テキスト='{initial_text[:20]}...'")
        self.scroll_mode = True
        self.current_speaker = speaker
        self.last_background = background
        self.last_active_characters = set(active_characters)
        self.scroll_lines = []
        
        # 初期テキストを行に分割して追加
        self.add_text_to_scroll(initial_text)
    
    def add_text_to_scroll(self, text):
        """テキストをスクロール表示に追加"""
        if not text:
            return
            
        print(f"[DEBUG] スクロールにテキスト追加: '{text[:20]}...'")
        
        # テキストを26文字ごとに分割
        lines = []
        for i in range(0, len(text), 26):
            lines.append(text[i:i+26])
        
        # 各行をスクロールリストに追加
        for line in lines:
            self.scroll_lines.append(line)
            print(f"[DEBUG] 行追加: '{line}'")
            # 最大行数を超えた場合、古い行を削除
            if len(self.scroll_lines) > self.max_lines:
                removed_line = self.scroll_lines.pop(0)
                print(f"[DEBUG] 行削除: '{removed_line}'")
        
        print(f"[DEBUG] 現在のスクロール行数: {len(self.scroll_lines)}")
    
    def continue_scroll(self, speaker, background, active_characters, new_text):
        """スクロールを継続"""
        print(f"[DEBUG] continue_scroll呼び出し: speaker={speaker}")
        if self.should_continue_scroll(speaker, background, active_characters):
            self.add_text_to_scroll(new_text)
            print(f"[DEBUG] スクロール継続成功: '{new_text[:20]}...'")
            return True
        else:
            print(f"[DEBUG] スクロール継続失敗")
            self.end_scroll_mode()
            return False
    
    def end_scroll_mode(self):
        """スクロールモードを終了"""
        print(f"[DEBUG] スクロールモード終了")
        self.scroll_mode = False
        self.scroll_lines = []
        self.current_speaker = None
        self.last_background = None
        self.last_active_characters = set()
    
    def is_scroll_mode(self):
        """スクロールモードかどうかを返す"""
        return self.scroll_mode
    
    def get_scroll_lines(self):
        """現在のスクロール行を取得"""
        return self.scroll_lines.copy()