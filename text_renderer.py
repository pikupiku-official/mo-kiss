import pygame
from config import *

class TextRenderer:
    def __init__(self, screen, debug=False):
        self.screen = screen
        self.debug = debug
        self.fonts = init_fonts()
        self.text_color = TEXT_COLOR
        self.name_color = TEXT_COLOR
        self.text_bg_color = TEXT_BG_COLOR
        self.text_start_x = TEXT_START_X
        self.text_start_y = TEXT_START_Y
        self.name_start_x = NAME_START_X
        self.name_start_y = NAME_START_Y
        self.text_line_height = self.fonts["text"].get_height()
        self.text_padding = TEXT_PADDING
        
        # 現在の会話データ
        self.current_text = ""
        self.current_character_name = None

        # 文字表示制限のための変数
        self.displayed_chars = 0 # 現在表示されている文字数
        self.last_char_time = 0 # 最後に文字を表示した時間
        self.char_delay = 70 # 文字間の遅延
        self.is_text_complete = False # テキスト表示が完了したかどうか
        
        # バックログに参照を持つ
        self.backlog_manager = None

    def set_backlog_manager(self, backlog_manager):
        """バックログマネージャーをセットする"""
        self.backlog_manager = backlog_manager

    def set_dialogue(self, text, character_name=None):
        """会話データを設定する"""
        self.current_text = text
        self.current_character_name = character_name
        self.displayed_chars = 0
        self.last_char_time = pygame.time.get_ticks()
        self.is_text_complete = False

    def update(self):
        """文字表示の更新"""
        if self.is_text_complete or not self.current_text:
            return 
        current_time = pygame.time.get_ticks()

        # 文字表示のタイミングチェック
        if current_time - self.last_char_time >= self.char_delay:
            if self.displayed_chars < len(self.current_text):
                self.displayed_chars += 1
                self.last_char_time = current_time
            else:
                self.is_text_complete = True
                # テキスト表示完了時にバックログへ追加
                if self.backlog_manager:
                    self.backlog_manager.add_to_backlog(self.current_text, self.current_character_name)

    def skip_text(self):
        """テキスト表示をスキップして全文表示"""
        self.displayed_chars = len(self.current_text)
        self.is_text_complete = True
        # スキップ時にもバックログへ追加
        if self.backlog_manager and self.current_text:
            self.backlog_manager.add_to_backlog(self.current_text, self.current_character_name)

    def is_displaying(self):
        """現在文字を表示中かどうか"""
        return not self.is_text_complete and self.current_text

    def render_paragraph(self):
        """現在の会話データを描画する"""
        if not self.current_text:
            return 0
        
        # 表示する文字列を取得
        display_text = self.current_text[:self.displayed_chars]

        # テキストを26文字ごとに分割
        lines = []
        for i in range(0, len(display_text), 26):
            lines.append(display_text[i:i+26])

        # キャラクター名の描画
        if self.current_character_name:
            name_surface = self.fonts["name"].render(self.current_character_name, True, self.name_color)
            self.screen.blit(name_surface, (self.name_start_x, self.name_start_y))

        # 各行を描画
        y = self.text_start_y
        for line in lines:
            if line:
                text_surface = self.fonts["text"].render(line, True, self.text_color)
                self.screen.blit(text_surface, (self.text_start_x, y))
            y += self.text_line_height

        return y  # テキストの高さを返す

    def render(self):
        """メインの描画メソッド"""
        # バックログが表示中の場合はテキストを描画しない
        if self.backlog_manager and self.backlog_manager.is_showing():
            return
        
        self.render_paragraph()
    
    def set_char_delay(self, delay_ms):
        """文字間の遅延を設定する"""
        self.char_delay = delay_ms

    def force_add_to_backlog(self):
        """現在の会話を強制的にバックログに追加（デバッグ用）"""
        if self.current_text and self.backlog_manager:
            self.backlog_manager.add_to_backlog(self.current_text, self.current_character_name)