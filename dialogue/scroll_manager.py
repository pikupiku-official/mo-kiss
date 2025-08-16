import pygame
from config import *
from .name_manager import get_name_manager

class ScrollManager:
    def __init__(self, debug=False):
        self.debug = debug
        
        # スクロール状態
        self.scroll_mode = False
        self.scroll_lines = []  # スクロール表示用のテキストブロック
        self.max_lines = 3  # 最大表示ブロック数
        self.all_scroll_text = []  # バックログ用：削除されたブロックも含むすべてのテキスト
        
        # 各行の話者情報を管理（修正点）
        self.line_speakers = []  # 各行の話者名
        self.line_is_first = []  # 各行がその話者の最初の行かどうか
        
        # 話者管理
        self.current_speaker = None
        self.last_added_speaker = None  # 最後に追加された話者を記録
        
        # TextRendererへの参照（終了通知用）
        self.text_renderer = None
        
        # 名前管理システム
        self.name_manager = get_name_manager()
        
    def set_text_renderer(self, text_renderer):
        """TextRendererの参照を設定"""
        self.text_renderer = text_renderer
        
    def start_scroll_mode(self, speaker, text):
        """スクロールモードを開始"""
        # 変数置換を適用
        substituted_speaker = self.name_manager.substitute_variables(speaker) if speaker else speaker
        substituted_text = self.name_manager.substitute_variables(text) if text else text
        
        if self.debug:
            print(f"[SCROLL] スクロール開始: {substituted_speaker} - '{substituted_text[:30] if substituted_text else ''}...'")
        
        self.scroll_mode = True
        self.current_speaker = substituted_speaker
        self.last_added_speaker = substituted_speaker
        self.scroll_lines = [substituted_text]  # 最初のテキストで初期化
        self.all_scroll_text = [substituted_text]  # バックログ用にも記録
        
        # 話者情報を初期化（修正点）
        self.line_speakers = [substituted_speaker]
        self.line_is_first = [True]  # 最初の行なので True
        
    def add_text_to_scroll(self, text, speaker=None):
        """テキストをスクロール表示に追加"""
        if not text:
            return
            
        # 話者が指定されていない場合は現在の話者を使用
        if speaker is None:
            speaker = self.current_speaker
        
        # 変数置換を適用
        substituted_speaker = self.name_manager.substitute_variables(speaker) if speaker else speaker
        substituted_text = self.name_manager.substitute_variables(text) if text else text
            
        if self.debug:
            print(f"[SCROLL] テキストブロック追加: '{substituted_text[:30]}...' by {substituted_speaker}")
        
        self.scroll_lines.append(substituted_text)
        self.all_scroll_text.append(substituted_text)  # バックログ用にも記録
        
        # 話者情報を追加（修正点）
        is_speaker_first_line = (substituted_speaker != self.last_added_speaker)
        self.line_speakers.append(substituted_speaker)
        self.line_is_first.append(is_speaker_first_line)
        self.last_added_speaker = substituted_speaker
        
        # 現在の話者を更新
        self.current_speaker = substituted_speaker
        
        # 最大ブロック数を超えた場合は古いブロックを削除
        while len(self.scroll_lines) > self.max_lines:
            removed_line = self.scroll_lines.pop(0)
            removed_speaker = self.line_speakers.pop(0)
            removed_is_first = self.line_is_first.pop(0)
            if self.debug:
                print(f"[SCROLL] 古いブロック削除: '{removed_line[:30]}...' by {removed_speaker} (first: {removed_is_first})")
        
        if self.debug:
            print(f"[SCROLL] 現在のブロック数: {len(self.scroll_lines)}/{self.max_lines}")
            print(f"[SCROLL] バックログ用テキスト数: {len(self.all_scroll_text)}")
            print(f"[SCROLL] 話者情報: {list(zip(self.line_speakers, self.line_is_first))}")
    
    def should_continue_scroll(self, speaker):
        """スクロール継続可能かを判定 - [scroll-stop]まで継続"""
        if not self.scroll_mode:
            return False
            
        # 話者が変わってもスクロールを継続（[scroll-stop]まで）
        if speaker != self.current_speaker:
            if self.debug:
                print(f"[SCROLL] 話者変更でもスクロール継続: {self.current_speaker} -> {speaker}")
            
        return True
    
    def continue_scroll(self, speaker, text):
        """スクロールを継続"""
        if self.should_continue_scroll(speaker):
            self.add_text_to_scroll(text, speaker)
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
        self.line_speakers = []  # 話者情報もリセット（修正点）
        self.line_is_first = []  # 最初行情報もリセット（修正点）
        self.current_speaker = None
        self.last_added_speaker = None
    
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
    
    def get_line_speakers_info(self):
        """各行の話者情報を取得（修正点）"""
        return {
            'speakers': self.line_speakers.copy(),
            'is_first': self.line_is_first.copy()
        }
    
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