import pygame
from config import *

class TextRenderer:
    def __init__(self, screen, debug=False):
        self.screen = screen
        self.debug = debug
        self.fonts = init_fonts()
        self.text_color = TEXT_COLOR
        self.name_color = (255, 255, 0)  # 名前の色（黄色）
        self.text_bg_color = TEXT_BG_COLOR
        self.text_start_x = TEXT_START_X
        self.text_start_y = TEXT_START_Y
        self.name_start_y = NAME_START_Y
        self.text_line_height = self.fonts["text"].get_height()
        self.text_padding = TEXT_PADDING
        self.text_box_width = TEXT_BOX_WIDTH
        self.text_max_width = TEXT_MAX_WIDTH
        self.next_indicator_color = NEXT_INDICATOR_COLOR
        self.next_indicator_pos = NEXT_INDICATOR_POS
        self.next_indicator_text = NEXT_INDICATOR_TEXT
        
        # 現在の会話データ
        self.current_text = ""
        self.current_character_name = None

    def set_dialogue(self, text, character_name=None):
        """会話データを設定する"""
        self.current_text = text
        self.current_character_name = character_name

    def render_paragraph(self):
        """現在の会話データを描画する"""
        if not self.current_text:
            return 0

        # テキストを20文字ごとに分割
        lines = []
        for i in range(0, len(self.current_text), 20):
            lines.append(self.current_text[i:i+20])

        # テキストボックスの高さを計算
        box_height = len(lines) * self.text_line_height + self.text_padding * 2

        # テキストボックスの描画
        text_bg_surface = pygame.Surface((self.text_box_width, box_height), pygame.SRCALPHA)
        text_bg_surface.fill(self.text_bg_color)
        self.screen.blit(text_bg_surface, (self.text_start_x - self.text_padding, self.text_start_y - self.text_padding))

        # キャラクター名の描画
        if self.current_character_name:
            name_surface = self.fonts["name"].render(self.current_character_name, True, self.name_color)
            self.screen.blit(name_surface, (self.text_start_x, self.name_start_y))

        # 各行を描画
        y = self.text_start_y
        for line in lines:
            text_surface = self.fonts["text"].render(line, True, self.text_color)
            self.screen.blit(text_surface, (self.text_start_x, y))
            y += self.text_line_height

        return box_height  # テキストの高さを返す

    def render_next_indicator(self):
        """次のテキストがあることを示すインジケーターを描画する"""
        next_indicator_surface = self.fonts["text"].render(self.next_indicator_text, True, self.next_indicator_color)
        self.screen.blit(next_indicator_surface, self.next_indicator_pos)