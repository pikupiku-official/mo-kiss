import pygame
import os
from config import *
from .name_manager import get_name_manager
from PyQt5.QtGui import QFont, QFontDatabase
from PyQt5.QtWidgets import QApplication

class ChoiceRenderer:
    def __init__(self, screen, debug=False):
        self.screen = screen
        self.debug = debug
        
        # Qt初期化
        if QApplication.instance() is None:
            init_qt_application()
        
        # フォント設定 (text_rendererと同じフォント使用)
        self.fonts = self._init_fonts()
        self.text_color = TEXT_COLOR
        self.text_color_female = TEXT_COLOR_FEMALE
        
        # 選択肢の表示設定（configから取得）
        self.text_start_x, self.text_start_y = scale_pos(CHOICE_START_X, CHOICE_START_Y)
        self.line_spacing = TEXT_LINE_SPACING
        self.choice_spacing = CHOICE_SPACING
        
        # text_rendererと同じ行間設定
        base_line_height = self.fonts["text_pygame"].get_height()
        self.text_line_height = int(base_line_height * TEXT_LINE_HEIGHT_MULTIPLIER)
        
        # text_rendererと同じ文字間隔設定
        self.char_spacing = TEXT_CHAR_SPACING
        
        # Pygameフォント（描画用）
        self.pygame_fonts = {
            "text": self.fonts["text_pygame"]
        }
        
        # 選択肢の状態
        self.choices = []
        self.choice_rects = []
        self.hovered_choice = -1
        self.is_showing_choices = False
        self.selected_choice = -1
        self.last_selected_text = None  # 最後に選択されたテキスト
        
        # 多列表示設定
        self.column_width = int(CHOICE_COLUMN_WIDTH * SCALE)
        self.column_spacing = int(CHOICE_COLUMN_SPACING * SCALE)
        
        # 現在の表示設定
        self.current_columns = 1
        self.choices_per_column = []
        
        # 色設定（configから取得）
        self.normal_color = CHOICE_NORMAL_COLOR
        self.highlight_color = CHOICE_HIGHLIGHT_COLOR
        
        # 名前管理システム
        self.name_manager = get_name_manager()
    
    def _apply_font_effects(self, text_surface, is_shadow=False):
        """text_rendererと同じフォント効果を適用する"""
        if not FONT_EFFECTS:
            return text_surface

        # 元の描画結果
        original_surface = text_surface
        orig_w, orig_h = original_surface.get_size()

        # ここで最終幅を先に決めておく（横伸ばし考慮）
        stretch_factor = float(FONT_EFFECTS.get("stretch_factor", 1.25)) \
            if FONT_EFFECTS.get("enable_stretched", False) else 1.0
        final_w = int(round(orig_w * stretch_factor))
        final_h = orig_h

        processed_surface = original_surface

        if FONT_EFFECTS.get("enable_pixelated", False):
            # 1/n に縮小
            pixelate_factor = max(1, int(FONT_EFFECTS.get("pixelate_factor", 2)))
            small_w = max(1, orig_w // pixelate_factor)
            small_h = max(1, orig_h // pixelate_factor)

            # 縮小はAA付き（にじみを抑えるならsmoothscaleがよい）
            small_surface = pygame.transform.smoothscale(processed_surface, (small_w, small_h))

            # 拡大は「横伸ばし後の最終サイズ」へ一発で
            processed_surface = pygame.transform.smoothscale(small_surface, (final_w, final_h))
        else:
            # ピクセル化なしの場合だけ、必要なら一回だけ横方向拡大
            if stretch_factor != 1.0:
                processed_surface = pygame.transform.smoothscale(processed_surface, (final_w, final_h))

        # 透明最適化（描画の滲み対策というより速度向上）
        return processed_surface.convert_alpha()
    
    def _render_text_with_effects(self, font, text, color):
        """テキストと同じ効果で選択肢を描画"""
        text_surface = font.render(text, True, color)
        text_surface = self._apply_font_effects(text_surface, is_shadow=False)

        if FONT_EFFECTS.get("enable_shadow", False):
            shadow_color = (0, 0, 0)
            shadow_surface = font.render(text, True, shadow_color)
            shadow_surface = self._apply_font_effects(shadow_surface, is_shadow=True)

            offx, offy = FONT_EFFECTS.get("shadow_offset", (6, 6))
            offx, offy = int(round(offx)), int(round(offy))

            tw, th = text_surface.get_size()
            sw, sh = shadow_surface.get_size()
            final_w = max(tw, sw + offx)
            final_h = max(th, sh + offy)

            final_surface = pygame.Surface((final_w, final_h), pygame.SRCALPHA)
            final_surface.blit(shadow_surface, (offx, offy))
            final_surface.blit(text_surface, (0, 0))
            return final_surface.convert_alpha()

        return text_surface
    
    def _render_choice_with_grid_system(self, choice_text, color):
        """選択肢をグリッドシステムで描画"""
        if not choice_text:
            return pygame.Surface((1, 1), pygame.SRCALPHA)
        
        # 1文字あたりの標準幅を計算（日本語文字基準）
        sample_char = "あ"
        sample_surface = self.pygame_fonts["text"].render(sample_char, True, color)
        base_char_width = sample_surface.get_width()
        
        # フォント効果を考慮した文字幅
        stretch_factor = FONT_EFFECTS.get("stretch_factor", 1.0) if FONT_EFFECTS.get("enable_stretched", False) else 1.0
        grid_char_width = int(base_char_width * stretch_factor * 1.1) + self.char_spacing
        
        # 選択肢テキストを自動改行（text_rendererと同じ文字数）
        max_chars = TEXT_MAX_CHARS_PER_LINE
        wrapped_lines = self._wrap_text(choice_text)
        
        # 全体のサーフェスサイズを計算
        line_width = grid_char_width * max_chars
        total_height = len(wrapped_lines) * self.text_line_height
        
        # 選択肢サーフェスを作成
        choice_surface = pygame.Surface((line_width, total_height), pygame.SRCALPHA)
        choice_surface.fill((0, 0, 0, 0))
        
        # 各行を描画
        for line_index, line in enumerate(wrapped_lines):
            if not line:
                continue
                
            y_offset = line_index * self.text_line_height
            
            # 各文字を絶対座標グリッドに配置
            for char_index, char in enumerate(line):
                if char_index >= max_chars:
                    break
                    
                # グリッド位置計算
                grid_x = char_index * grid_char_width
                grid_y = y_offset
                
                # 個別文字をエフェクト付きで描画
                char_surface = self._render_text_with_effects(
                    self.pygame_fonts["text"], 
                    char, 
                    color
                )
                
                # 文字をグリッド位置に配置
                choice_surface.blit(char_surface, (grid_x, grid_y))
        
        return choice_surface
    
    def _wrap_text(self, text):
        """テキストをn文字で自動改行する（text_rendererと同じロジック）"""
        if not text:
            return []
        
        # 既存の改行コードで分割
        paragraphs = text.split('\n')
        wrapped_lines = []
        
        for paragraph in paragraphs:
            if not paragraph:
                wrapped_lines.append('')
                continue
            
            # 指定文字数ごとに分割
            current_pos = 0
            while current_pos < len(paragraph):
                line_end = current_pos + TEXT_MAX_CHARS_PER_LINE
                if line_end >= len(paragraph):
                    wrapped_lines.append(paragraph[current_pos:])
                    break
                else:
                    wrapped_lines.append(paragraph[current_pos:line_end])
                    current_pos = line_end
        
        return wrapped_lines
    
    def _calculate_column_layout(self, choice_count):
        """選択肢数に応じた列数とレイアウトを計算"""
        if choice_count <= CHOICE_MAX_SINGLE_COLUMN:
            # 1列表示（1-3個）
            return 1, [choice_count]
        elif choice_count <= CHOICE_MAX_DOUBLE_COLUMN:
            # 2列表示（4-6個）
            choices_per_column = choice_count // 2
            remainder = choice_count % 2
            if remainder == 0:
                return 2, [choices_per_column, choices_per_column]
            else:
                return 2, [choices_per_column + 1, choices_per_column]
        elif choice_count <= CHOICE_MAX_TRIPLE_COLUMN:
            # 3列表示（7-9個）
            choices_per_column = choice_count // 3
            remainder = choice_count % 3
            if remainder == 0:
                return 3, [choices_per_column, choices_per_column, choices_per_column]
            elif remainder == 1:
                return 3, [choices_per_column + 1, choices_per_column, choices_per_column]
            else:  # remainder == 2
                return 3, [choices_per_column + 1, choices_per_column + 1, choices_per_column]
        else:
            # 9個を超える場合は9個に制限
            if self.debug:
                print(f"警告: 選択肢が{choice_count}個ありますが、最大9個に制限されます")
            return 3, [3, 3, 3]
    
    def _get_choice_position(self, choice_index, column_layout):
        """選択肢のインデックスから列と行の位置を計算"""
        columns, choices_per_column = column_layout
        
        current_choice = 0
        for col in range(columns):
            if current_choice + choices_per_column[col] > choice_index:
                # この列にある
                row_in_column = choice_index - current_choice
                return col, row_in_column
            current_choice += choices_per_column[col]
        
        # エラーケース
        return 0, 0
    
    def _calculate_choice_coordinates(self, choice_index, choice_surface, column_layout):
        """選択肢の画面座標を計算"""
        col, row = self._get_choice_position(choice_index, column_layout)
        
        # 列のX座標を計算
        base_x = self.text_start_x + (col * (self.column_width + self.column_spacing))
        
        # 行のY座標を計算
        base_y = self.text_start_y + (row * (choice_surface.get_height() + self.choice_spacing))
        
        return base_x, base_y
        
    def _init_fonts(self):
        """text_rendererと同じフォント設定を使用"""
        try:
            # フォントサイズをスクリーンサイズに基づいて計算（text_rendererと同じ）
            text_font_size = int(SCREEN_HEIGHT * FONT_TEXT_SIZE_RATIO)
            default_font_size = int(SCREEN_HEIGHT * FONT_DEFAULT_SIZE_RATIO)
            
            # フォントファイルのパスを設定（プロジェクトルートから）
            project_root = os.path.dirname(os.path.dirname(__file__))
            font_dir = os.path.join(project_root, "fonts")
            medium_font_path = os.path.join(font_dir, "MPLUS1p-Medium.ttf")

            fonts = {}
            
            # PyQt5フォントの初期化
            if os.path.exists(medium_font_path):
                try:
                    # Mediumフォントの読み込み
                    medium_font_id = QFontDatabase.addApplicationFont(medium_font_path)

                    if medium_font_id != -1:
                        medium_font_family = QFontDatabase.applicationFontFamilies(medium_font_id)[0]
                        
                        # PyQt5フォント（BacklogManager用）
                        fonts["text"] = QFont(medium_font_family, text_font_size)
                        
                        # Pygameフォント（ChoiceRenderer用）
                        fonts["text_pygame"] = pygame.font.Font(medium_font_path, text_font_size)
                        
                        if self.debug:
                            print("ChoiceRenderer: カスタムフォント読み込み成功")
                    else:
                        raise Exception("PyQt5フォントID取得失敗")
                        
                except Exception as e:
                    if self.debug:
                        print(f"ChoiceRenderer: カスタムフォント読み込み失敗: {e}")
                    # フォールバック
                    fonts.update(self._get_fallback_fonts(text_font_size, default_font_size))
            else:
                if self.debug:
                    print(f"ChoiceRenderer: フォントファイルが見つかりません: {medium_font_path}")
                # フォールバック
                fonts.update(self._get_fallback_fonts(text_font_size, default_font_size))
            
            # デフォルトフォント
            fonts["default"] = pygame.font.SysFont(None, default_font_size)
            
            return fonts
            
        except Exception as e:
            if self.debug:
                print(f"ChoiceRenderer: フォント初期化エラー: {e}")
            # エラー時のフォールバック（仮想解像度基準）
            from config import SCALE
            virtual_fallback_font_size = 47  # 1080 * 0.044 = 47.52 → 47px
            virtual_default_font_size = 29   # 1080 * 0.027 = 29.16 → 29px
            
            return self._get_fallback_fonts(
                int(virtual_fallback_font_size * SCALE),
                int(virtual_default_font_size * SCALE)
            )
        
    def _get_fallback_fonts(self, text_size, default_size):
        """フォールバックフォントを取得"""
        return {
            "default": pygame.font.SysFont(None, default_size),
            "text": QFont("MS Gothic", text_size),  # PyQt5用
            "text_pygame": pygame.font.SysFont("msgothic", text_size),  # Pygame用
        }
    
    def show_choices(self, options):
        """選択肢を表示する（多列対応）"""
        print(f"[DEBUG] show_choices呼び出し: 受信選択肢数={len(options)}")
        print(f"[DEBUG] 受信選択肢: {options}")
        
        # 変数置換を適用
        self.choices = [self.name_manager.substitute_variables(option) if option else option for option in options]
        self.choice_rects = []
        self.is_showing_choices = True
        self.hovered_choice = -1
        self.selected_choice = -1
        
        print(f"[DEBUG] 変数置換後選択肢数={len(self.choices)}")
        print(f"[DEBUG] config値 - MAX_SINGLE={CHOICE_MAX_SINGLE_COLUMN}, MAX_DOUBLE={CHOICE_MAX_DOUBLE_COLUMN}, MAX_TRIPLE={CHOICE_MAX_TRIPLE_COLUMN}")
        
        # 9個を超える場合は制限
        if len(self.choices) > CHOICE_MAX_TRIPLE_COLUMN:
            self.choices = self.choices[:CHOICE_MAX_TRIPLE_COLUMN]
            print(f"[DEBUG] 警告: 選択肢を{CHOICE_MAX_TRIPLE_COLUMN}個に制限しました")
        
        # 列数とレイアウトを計算
        self.current_columns, self.choices_per_column = self._calculate_column_layout(len(self.choices))
        print(f"[DEBUG] レイアウト計算結果: {self.current_columns}列, 各列の選択肢数={self.choices_per_column}")
        
        # 各選択肢の矩形を計算（多列レイアウト対応）
        for i, choice in enumerate(self.choices):
            # グリッドシステムで選択肢をレンダリングしてサイズを取得
            choice_surface = self._render_choice_with_grid_system(choice, self.normal_color)
            
            # 多列レイアウトでの座標を計算
            x, y = self._calculate_choice_coordinates(i, choice_surface, (self.current_columns, self.choices_per_column))
            print(f"[DEBUG] 選択肢{i} '{choice}' 座標=({x}, {y})")
            
            # 当たり判定の幅を列幅に制限（複数列の場合は列幅、単列の場合は全幅）
            hit_width = self.column_width if self.current_columns > 1 else choice_surface.get_width()
            choice_rect = pygame.Rect(x, y, hit_width, choice_surface.get_height())
            self.choice_rects.append(choice_rect)
            print(f"[DEBUG] 選択肢{i} 当たり判定: width={hit_width} (列数={self.current_columns})")
        
        print(f"[DEBUG] 選択肢表示開始: {len(self.choices)}個の選択肢（{self.current_columns}列表示）")
    
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
        """選択肢を描画（多列表示、グリッドシステムとフォント効果付き）"""
        if not self.is_showing_choices or not self.choices:
            return

        # 頻繁に呼ばれるのでログ出力しない

        for i, choice in enumerate(self.choices):
            # ハイライト色を決定
            color = self.highlight_color if i == self.hovered_choice else self.normal_color

            # グリッドシステムで選択肢を描画（text_rendererと同じ効果）
            choice_surface = self._render_choice_with_grid_system(choice, color)

            # 多列レイアウトでの座標を計算
            pos_x, pos_y = self._calculate_choice_coordinates(i, choice_surface, (self.current_columns, self.choices_per_column))

            # 座標を整数にスナップして揺れを防止
            pos_x = int(round(pos_x))
            pos_y = int(round(pos_y))

            # 描画（ログ出力しない）
            self.screen.blit(choice_surface, (pos_x, pos_y))
    
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
    
    def set_choice_position(self, x, y):
        """選択肢表示位置を設定（仮想座標）"""
        self.text_start_x, self.text_start_y = scale_pos(x, y)
        if self.debug:
            print(f"選択肢表示位置を({x}, {y})に設定")
    
    def set_choice_spacing(self, spacing):
        """選択肢間のスペーシングを設定"""
        self.choice_spacing = spacing
        if self.debug:
            print(f"選択肢間スペーシングを{spacing}pxに設定")
    
    def set_choice_colors(self, normal_color, highlight_color):
        """選択肢の色を設定"""
        self.normal_color = normal_color
        self.highlight_color = highlight_color
        if self.debug:
            print(f"選択肢色を設定: 通常={normal_color}, ハイライト={highlight_color}")