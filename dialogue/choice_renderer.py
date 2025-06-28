import pygame
from config import *

class ChoiceRenderer:
    def __init__(self, screen, debug=False):
        self.screen = screen
        self.debug = debug
        
        # フォント設定 (text_rendererと同じフォント使用)
        self.fonts = self._init_fonts()
        self.text_color = TEXT_COLOR
        self.text_color_female = TEXT_COLOR_FEMALE
        
        # 選択肢の表示設定
        self.text_positions = get_text_positions(screen)
        self.text_start_x = self.text_positions["speech_1"][0]
        self.text_start_y = self.text_positions["speech_1"][1]
        self.line_spacing = TEXT_LINE_SPACING
        self.text_line_height = self.fonts["text_pygame"].get_height()
        
        # 選択肢の状態
        self.choices = []
        self.choice_rects = []
        self.hovered_choice = -1
        self.is_showing_choices = False
        self.selected_choice = -1
        self.last_selected_text = None  # 最後に選択されたテキスト
        
        # 色設定
        self.normal_color = TEXT_COLOR
        self.highlight_color = (255, 255, 0)  # 黄色でハイライト
        
    def _init_fonts(self):
        """text_rendererと同じフォント設定を使用"""
        try:
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            font_dir = os.path.join(project_root, "mo-kiss", "fonts")
            medium_font_path = os.path.join(font_dir, "MPLUSRounded1c-Regular.ttf")
            text_font_size = int(SCREEN_HEIGHT * 43 / 1000)  # 16:9画面で46px
            
            fonts = {}
            
            if os.path.exists(medium_font_path):
                fonts["text_pygame"] = pygame.font.Font(medium_font_path, text_font_size)
                if self.debug:
                    print("ChoiceRenderer: カスタムフォント読み込み成功")
            else:
                fonts["text_pygame"] = pygame.font.SysFont("msgothic", text_font_size)
                if self.debug:
                    print("ChoiceRenderer: フォールバックフォント使用")
            
            return fonts
            
        except Exception as e:
            if self.debug:
                print(f"ChoiceRenderer フォント初期化エラー: {e}")
            text_font_size = int(SCREEN_HEIGHT * 43 / 1000)  # 16:9画面で46px
            return {
                "text_pygame": pygame.font.SysFont("msgothic", text_font_size)
            }
    
    def show_choices(self, options):
        """選択肢を表示する"""
        self.choices = options
        self.choice_rects = []
        self.is_showing_choices = True
        self.hovered_choice = -1
        self.selected_choice = -1
        
        # 各選択肢の矩形を計算
        y = self.text_start_y
        for i, choice in enumerate(self.choices):
            text_surface = self.fonts["text_pygame"].render(choice, True, self.normal_color)
            choice_rect = pygame.Rect(self.text_start_x, y, text_surface.get_width(), text_surface.get_height())
            self.choice_rects.append(choice_rect)
            y += self.text_line_height
        
        if self.debug:
            print(f"選択肢表示開始: {len(self.choices)}個の選択肢")
    
    def hide_choices(self):
        """選択肢を非表示にする"""
        self.is_showing_choices = False
        self.choices = []
        self.choice_rects = []
        self.hovered_choice = -1
        self.selected_choice = -1
        
        if self.debug:
            print("選択肢を非表示にしました")
    
    def handle_mouse_motion(self, mouse_pos):
        """マウス移動を処理してハイライトを更新"""
        if not self.is_showing_choices:
            return
        
        old_hovered = self.hovered_choice
        self.hovered_choice = -1
        
        for i, rect in enumerate(self.choice_rects):
            if rect.collidepoint(mouse_pos):
                self.hovered_choice = i
                break
        
        # ハイライト状態が変わった場合のデバッグログ
        if old_hovered != self.hovered_choice and self.debug:
            if self.hovered_choice >= 0:
                print(f"選択肢 {self.hovered_choice + 1} をハイライト")
            else:
                print("ハイライト解除")
    
    def handle_mouse_click(self, mouse_pos):
        """マウスクリックを処理して選択肢を決定"""
        if not self.is_showing_choices:
            return -1
        
        for i, rect in enumerate(self.choice_rects):
            if rect.collidepoint(mouse_pos):
                self.selected_choice = i
                self.last_selected_text = self.choices[i]  # 選択されたテキストを保存
                if self.debug:
                    print(f"選択肢 {i + 1} が選択されました: {self.choices[i]}")
                return i
        
        return -1
    
    def render(self):
        """選択肢を描画"""
        if not self.is_showing_choices or not self.choices:
            return
        
        for i, choice in enumerate(self.choices):
            # ハイライト色を決定
            color = self.highlight_color if i == self.hovered_choice else self.normal_color
            
            # テキストを描画
            text_surface = self.fonts["text_pygame"].render(choice, True, color)
            y_pos = self.text_start_y + (i * self.text_line_height)
            self.screen.blit(text_surface, (self.text_start_x, y_pos))
    
    def is_choice_showing(self):
        """選択肢が表示中かどうかを返す"""
        return self.is_showing_choices
    
    def get_selected_choice(self):
        """選択された選択肢番号を返す"""
        return self.selected_choice
    
    def get_last_selected_text(self):
        """最後に選択された選択肢のテキストを返す"""
        return self.last_selected_text
    
    def clear_last_selected(self):
        """最後に選択された選択肢をクリア"""
        self.last_selected_text = None