import pygame
from config import *
from .scroll_manager import ScrollManager
from .name_manager import get_name_manager
import os
from PyQt5.QtGui import QFont, QFontDatabase
from PyQt5.QtWidgets import QApplication

class TextRenderer:
    def __init__(self, screen, debug=False):
        self.screen = screen
        self.debug = debug

        if QApplication.instance() is None:
            init_qt_application()

        self.fonts = self._init_fonts()
        self.text_color = TEXT_COLOR
        self.text_color_female = TEXT_COLOR_FEMALE
        self.text_bg_color = TEXT_BG_COLOR
        self.text_positions = get_text_positions(screen)
        self.text_start_x = self.text_positions["speech_1"][0]
        self.text_start_y = self.text_positions["speech_1"][1]
        self.name_start_x = self.text_positions["name_1"][0]
        self.name_start_y = self.text_positions["name_1"][1]
        self.line_spacing = TEXT_LINE_SPACING
        # 行間調整機能を追加
        base_line_height = self.fonts["text_pygame"].get_height()
        self.text_line_height = int(base_line_height * TEXT_LINE_HEIGHT_MULTIPLIER)
        self.text_padding = TEXT_PADDING
        self.char_spacing = TEXT_CHAR_SPACING
        # 名前表示モードの初期化
        self.name_display_mode = "auto"  # デフォルトは自動均等配置

        # n文字での自動改行を設定
        self.max_chars_per_line = TEXT_MAX_CHARS_PER_LINE
        # 最大表示行数
        self.max_display_lines = TEXT_MAX_DISPLAY_LINES

        self.pygame_fonts = {
            "text": self.fonts["text_pygame"],
            "name": self.fonts["name_pygame"]
        }
        
        self.current_text = ""
        self.current_character_name = None

        self.displayed_chars = 0
        self.last_char_time = 0
        self.char_delay = TEXT_CHAR_DELAY
        self.is_text_complete = False

        # 新しい遅延設定を追加
        self.punctuation_delay = TEXT_PUNCTUATION_DELAY  # 句読点「。」での追加遅延時間（ミリ秒）
        self.paragraph_transition_delay = TEXT_PARAGRAPH_TRANSITION_DELAY  # スクロール終了後の段落切り替え遅延時間（ミリ秒）
        self.punctuation_waiting = False  # 句読点遅延中フラグ
        self.punctuation_wait_start = 0  # 句読点遅延開始時刻
        self.paragraph_transition_waiting = False  # 段落切り替え遅延中フラグ
        self.paragraph_transition_start = 0  # 段落切り替え遅延開始時刻
        self.scroll_just_ended = False  # スクロールが直前に終了したかのフラグ

        self.auto_mode = False
        self.skip_mode = False
        self.text_complete_time = 0
        self.is_ready_for_next = False
        self.auto_ready_logged = False
        
        self.backlog_manager = None
        self.scroll_manager = ScrollManager(debug)
        # ScrollManagerにTextRendererの参照を設定
        self.scroll_manager.set_text_renderer(self)
        
        # バックログ追加フラグの初期化
        self.backlog_added_for_current = True
        
        # 名前管理システム
        self.name_manager = get_name_manager()

    def _wrap_text(self, text):
        """テキストをn文字で自動改行する（グリッドシステム対応）"""
        if not text:
            return []
        
        # 既存の改行コードで分割
        paragraphs = text.split('\n')
        wrapped_lines = []
        
        for paragraph in paragraphs:
            if not paragraph:
                # 空行の場合はそのまま追加
                wrapped_lines.append('')
                continue
            
            # 指定文字数ごとに分割（グリッドシステム用に正確にn文字）
            current_pos = 0
            while current_pos < len(paragraph):
                line_end = current_pos + self.max_chars_per_line
                if line_end >= len(paragraph):
                    # 最後の行
                    wrapped_lines.append(paragraph[current_pos:])
                    break
                else:
                    # 指定文字数で切り取り（グリッドシステムで処理）
                    wrapped_lines.append(paragraph[current_pos:line_end])
                    current_pos = line_end
        
        return wrapped_lines

    def _get_display_lines_with_scroll(self, display_text_segment):
        """表示用のテキストをn文字改行して、3行スクロール効果を適用"""
        wrapped_lines = self._wrap_text(display_text_segment)
        
        # 3行以下の場合はそのまま返す
        if len(wrapped_lines) <= self.max_display_lines:
            return wrapped_lines
        
        # 3行を超える場合は最新の3行のみを返す（スクロール効果）
        display_lines = wrapped_lines[-self.max_display_lines:]
        
        return display_lines

    def _init_fonts(self):
        """フォントを初期化する（PyQt5 + Pygame混在版）"""
        try:
            # フォントサイズをスクリーンサイズに基づいて計算
            name_font_size = int(SCREEN_HEIGHT * FONT_NAME_SIZE_RATIO)
            text_font_size = int(SCREEN_HEIGHT * FONT_TEXT_SIZE_RATIO)
            default_font_size = int(SCREEN_HEIGHT * FONT_DEFAULT_SIZE_RATIO)
            
            # フォントファイルのパスを設定（プロジェクトルートから）
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            font_dir = os.path.join(project_root, "mo-kiss", "fonts")
            bold_font_path = os.path.join(font_dir, "MPLUS1p-Bold.ttf")
            medium_font_path = os.path.join(font_dir, "MPLUS1p-Medium.ttf")

            fonts = {}
            
            # PyQt5フォントの初期化
            if os.path.exists(bold_font_path) and os.path.exists(medium_font_path):
                try:
                    # Boldフォントの読み込み
                    bold_font_id = QFontDatabase.addApplicationFont(bold_font_path)
                    # Mediumフォントの読み込み
                    medium_font_id = QFontDatabase.addApplicationFont(medium_font_path)

                    if bold_font_id != -1 and medium_font_id != -1:
                        bold_font_family = QFontDatabase.applicationFontFamilies(bold_font_id)[0]
                        medium_font_family = QFontDatabase.applicationFontFamilies(medium_font_id)[0]
                        
                        # PyQt5フォント（BacklogManager用）
                        fonts["name"] = QFont(bold_font_family, name_font_size)
                        fonts["text"] = QFont(medium_font_family, text_font_size)
                        
                        # Pygameフォント（TextRenderer用）
                        fonts["name_pygame"] = pygame.font.Font(bold_font_path, name_font_size)
                        fonts["text_pygame"] = pygame.font.Font(medium_font_path, text_font_size)
                        
                        if self.debug:
                            print("PyQt5とPygameのカスタムフォント読み込み成功")
                    else:
                        raise Exception("PyQt5フォントID取得失敗")
                        
                except Exception as e:
                    if self.debug:
                        print(f"カスタムフォント読み込み失敗: {e}")
                    # フォールバック
                    fonts.update(self._get_fallback_fonts(name_font_size, text_font_size, default_font_size))
            else:
                if self.debug:
                    print(f"フォントファイルが見つかりません: {bold_font_path}, {medium_font_path}")
                # フォールバック
                fonts.update(self._get_fallback_fonts(name_font_size, text_font_size, default_font_size))
            
            # デフォルトフォント
            fonts["default"] = pygame.font.SysFont(None, default_font_size)
            
            return fonts
            
        except Exception as e:
            print(f"フォント初期化エラー: {e}")
            # エラーが発生した場合はフォールバック
            # エラー時のフォールバック（仮想解像度基準）
            from config import SCALE
            virtual_fallback_font_size = 47  # 1080 * 0.044 = 47.52 → 47px
            virtual_default_font_size = 29   # 1080 * 0.027 = 29.16 → 29px
            
            return self._get_fallback_fonts(
                int(virtual_fallback_font_size * SCALE),
                int(virtual_fallback_font_size * SCALE), 
                int(virtual_default_font_size * SCALE)
            )
        
    def _get_fallback_fonts(self, name_size, text_size, default_size):
        """フォールバックフォントを取得"""
        return {
            "default": pygame.font.SysFont(None, default_size),
            "text": QFont("MS Gothic", text_size),  # PyQt5用
            "name": QFont("MS Gothic", name_size),  # PyQt5用
            "text_pygame": pygame.font.SysFont("msgothic", text_size),  # Pygame用
            "name_pygame": pygame.font.SysFont("msgothic", name_size)   # Pygame用
        }
    
    def _apply_font_effects(self, text_surface, is_shadow=False):
        """フォント効果を適用する（ピクセル化、横引き延ばし）"""
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

            # ！！ここが肝：拡大は「横伸ばし後の最終サイズ」へ一発で
            processed_surface = pygame.transform.smoothscale(small_surface, (final_w, final_h))
        else:
            # ピクセル化なしの場合だけ、必要なら一回だけ横方向拡大
            if stretch_factor != 1.0:
                processed_surface = pygame.transform.smoothscale(processed_surface, (final_w, final_h))

        # 透明最適化（描画の滲み対策というより速度向上）
        return processed_surface.convert_alpha()

    
    def _render_text_with_effects(self, font, text, color, is_name=False):
        text_surface = font.render(text, True, color)
        text_surface = self._apply_font_effects(text_surface, is_shadow=False)

        if FONT_EFFECTS.get("enable_shadow", False):
            shadow_color = (0, 0, 0)
            shadow_surface = font.render(text, True, shadow_color)
            shadow_surface = self._apply_font_effects(shadow_surface, is_shadow=True)

            offx, offy = FONT_EFFECTS.get("shadow_offset", (6, 6))
            offx, offy = int(round(offx)), int(round(offy))  # ← 揺れ防止

            tw, th = text_surface.get_size()
            sw, sh = shadow_surface.get_size()
            final_w = max(tw, sw + offx)
            final_h = max(th, sh + offy)

            final_surface = pygame.Surface((final_w, final_h), pygame.SRCALPHA)
            # blit位置も整数スナップ
            final_surface.blit(shadow_surface, (offx, offy))
            final_surface.blit(text_surface, (0, 0))
            return final_surface.convert_alpha()

        return text_surface

    def _render_stable_text_line(self, displayed_line, color):
        """文字送り時の揺れを防ぐ安定した行描画（絶対座標グリッドシステム）"""
        if not displayed_line:
            return pygame.Surface((1, 1), pygame.SRCALPHA)
        
        # 【根本解決】絶対座標グリッドシステム
        # 各文字を固定されたグリッド位置に配置することで揺れを完全に解消
        
        return self._render_text_with_grid_system(displayed_line, color)
    
    def _render_text_with_grid_system(self, text_line, color):
        """絶対座標グリッドシステムで文字を描画"""
        if not text_line:
            return pygame.Surface((1, 1), pygame.SRCALPHA)
        
        # 1文字あたりの標準幅を計算（日本語文字基準）
        sample_char = "あ"  # 日本語の代表的な文字
        sample_surface = self.pygame_fonts["text"].render(sample_char, True, color)
        base_char_width = sample_surface.get_width()
        
        # フォント効果を考慮した文字幅（横引き延ばし効果込み）
        stretch_factor = FONT_EFFECTS.get("stretch_factor", 1.0) if FONT_EFFECTS.get("enable_stretched", False) else 1.0
        grid_char_width = int(base_char_width * stretch_factor * 1.1) + self.char_spacing  # 文字間隔を追加
        
        # 行全体のサーフェスサイズを計算
        max_chars = min(len(text_line), self.max_chars_per_line)
        line_width = grid_char_width * max_chars
        line_height = self.pygame_fonts["text"].get_height() * 2  # 高さも余裕を持たせる
        
        # 行サーフェスを作成
        line_surface = pygame.Surface((line_width, line_height), pygame.SRCALPHA)
        line_surface.fill((0, 0, 0, 0))  # 透明で初期化
        
        # 各文字を絶対座標グリッドに配置
        for char_index, char in enumerate(text_line):
            if char_index >= self.max_chars_per_line:
                break
                
            # グリッド位置計算（絶対座標）
            grid_x = char_index * grid_char_width
            grid_y = 0
            
            # 個別文字をエフェクト付きで描画
            char_surface = self._render_text_with_effects(
                self.pygame_fonts["text"], 
                char, 
                color, 
                is_name=False
            )
            
            # 文字をグリッド位置に配置
            line_surface.blit(char_surface, (grid_x, grid_y))
        
        return line_surface
    
    def _render_name_with_grid_system(self, name, color):
        """名前を均等配置のグリッドシステムで描画"""
        if not name:
            return pygame.Surface((1, 1), pygame.SRCALPHA)
        
        # 通常表示モードの場合は従来通り
        if getattr(self, 'name_display_mode', 'auto') == 'normal':
            return self._render_text_with_effects(self.pygame_fonts["name"], name, color, is_name=True)
        
        # 1文字あたりの標準幅を計算（名前フォント基準）
        sample_char = "あ"
        sample_surface = self.pygame_fonts["name"].render(sample_char, True, color)
        base_char_width = sample_surface.get_width()
        
        # フォント効果を考慮した文字幅
        stretch_factor = FONT_EFFECTS.get("stretch_factor", 1.0) if FONT_EFFECTS.get("enable_stretched", False) else 1.0
        grid_char_width = int(base_char_width * stretch_factor * 1.1) + self.char_spacing
        
        # 名前の文字数に応じた均等配置ロジック
        name_length = len(name)
        if name_length == 1:
            # 1文字の場合: 「　橘　」（前後に全角スペース）
            display_name = "　" + name + "　"
            total_chars = 3
        elif name_length == 2:
            # 2文字の場合: 「純　一」（間に全角スペース）
            display_name = name[0] + "　" + name[1]
            total_chars = 3
        else:
            # 3文字以上の場合: そのまま表示
            display_name = name
            total_chars = name_length
        
        # 名前全体のサーフェスサイズを計算
        name_width = grid_char_width * total_chars
        name_height = self.pygame_fonts["name"].get_height() * 2
        
        # 名前サーフェスを作成
        name_surface = pygame.Surface((name_width, name_height), pygame.SRCALPHA)
        name_surface.fill((0, 0, 0, 0))
        
        # 各文字を絶対座標グリッドに配置
        for char_index, char in enumerate(display_name):
            # グリッド位置計算
            grid_x = char_index * grid_char_width
            grid_y = 0
            
            # 個別文字をエフェクト付きで描画
            char_surface = self._render_text_with_effects(
                self.pygame_fonts["name"], 
                char, 
                color, 
                is_name=True
            )
            
            # 文字をグリッド位置に配置
            name_surface.blit(char_surface, (grid_x, grid_y))
        
        return name_surface

    def set_backlog_manager(self, backlog_manager):
        self.backlog_manager = backlog_manager

    def toggle_auto_mode(self):
        self.auto_mode = not self.auto_mode
        if self.auto_mode:
            self.skip_mode = False  # autoモードONの時はskipモードOFF
        if self.debug:
            print(f"自動モード: {'ON' if self.auto_mode else 'OFF'}")
        return self.auto_mode
    
    def toggle_skip_mode(self):
        self.skip_mode = not self.skip_mode
        if self.skip_mode:
            self.auto_mode = False  # skipモードONの時はautoモードOFF
        if self.debug:
            print(f"スキップモード: {'ON' if self.skip_mode else 'OFF'}")
        return self.skip_mode
    
    def is_auto_mode(self):
        return self.auto_mode
    
    def is_ready_for_auto_advance(self):
        return (self.auto_mode or self.skip_mode) and self.is_ready_for_next
    
    def reset_auto_timer(self):
        self.is_ready_for_next = False
        self.text_complete_time = 0
        self.auto_ready_logged = False
        # 新しい遅延状態もリセット
        self.paragraph_transition_waiting = False
        self.paragraph_transition_start = 0

    def set_scroll_ended_flag(self):
        """スクロール終了フラグを設定"""
        self.scroll_just_ended = True
        if self.debug:
            print("[DELAY] スクロール終了フラグを設定")

    def set_dialogue(self, text, character_name=None, should_scroll=False, background=None, active_characters=None):
        if self.debug:
            print(f"[TEXT] set_dialogue呼び出し: テキスト='{text[:50] if text else None}...', 話者='{character_name}'")
        
        # スクロール停止コマンドの処理（唯一のスクロール停止方法）
        if text and text.startswith('_SCROLL_STOP'):
            if self.debug:
                print(f"[SCROLL] scroll-stopコマンドを実行")
            self.scroll_manager.process_scroll_stop_command()
            # previous_textをクリアしてスクロール履歴をリセット
            if hasattr(self, 'previous_text'):
                self.previous_text = None
            if self.debug:
                print(f"[SCROLL] previous_textをクリア")
            return
        
        if self.debug:
            scroll_status = "スクロール" if should_scroll else "通常"
            print(f"[TEXT] {scroll_status}表示: {character_name} - '{text[:30] if text else ''}...'")
        
        # 変数置換を適用
        substituted_text = self.name_manager.substitute_variables(text) if text is not None else ""
        substituted_character_name = self.name_manager.substitute_variables(character_name) if character_name is not None else ""
        
        self.current_text = str(substituted_text)
        self.current_character_name = str(substituted_character_name)
        
        # 新しいテキストが設定されたのでバックログ追加フラグをリセット
        self.backlog_added_for_current = False
        
        # 現在の話者を記録
        if not hasattr(self, 'last_speaker'):
            self.last_speaker = None
        
        # 前のテキストを保持するフラグ
        if not hasattr(self, 'previous_text'):
            self.previous_text = None
        
        # スクロールモード中の場合、話者に関係なく常に継続
        if self.scroll_manager.is_scroll_mode():
            if self.debug:
                print(f"[SCROLL] スクロールモード中 - 無条件で継続: {character_name}")
            
            # テキストをスクロールに追加（修正点：話者情報も渡す）
            self.scroll_manager.add_text_to_scroll(text, character_name)
            self.displayed_chars = 0
            self.last_char_time = pygame.time.get_ticks()
            self.is_text_complete = False
            self.reset_auto_timer()
            self.last_speaker = character_name
            self.previous_text = text
            # スクロールモード中はバックログ追加しないため、フラグは True に設定
            self.backlog_added_for_current = True
            return
        
        # スクロール表示の処理（新規開始）
        if should_scroll and character_name:
            if self.debug:
                print(f"[SCROLL] 新規スクロール開始: {character_name}")
            
            # 前のテキストがある場合は、それも含めてスクロール開始
            if (hasattr(self, 'previous_text') and self.previous_text and 
                hasattr(self, 'last_speaker') and self.last_speaker == character_name):
                if self.debug:
                    print(f"[SCROLL] 前のテキストを含めてスクロール開始: {character_name}")
                
                # 重複防止：前のテキストが既にバックログに単独で存在する場合は削除
                if (self.backlog_manager and self.backlog_manager.entries and 
                    self.backlog_manager.entries[-1]["speaker"] == character_name and
                    self.backlog_manager.entries[-1]["text"] == self.previous_text):
                    removed_entry = self.backlog_manager.entries.pop()
                    if self.debug:
                        print(f"[BACKLOG] スクロール開始時に重複エントリを削除: {removed_entry['speaker']} - {removed_entry['text'][:30]}...")
                
                # 前のテキストでスクロール開始
                self.scroll_manager.start_scroll_mode(character_name, self.previous_text)
                # 現在のテキストを追加（修正点：話者情報も渡す）
                self.scroll_manager.add_text_to_scroll(text, character_name)
            else:
                # 新しくスクロール開始
                self.scroll_manager.start_scroll_mode(character_name, text)
            
            self.displayed_chars = 0
            self.last_char_time = pygame.time.get_ticks()
            self.is_text_complete = False
            self.reset_auto_timer()
            self.last_speaker = character_name
            self.previous_text = text
            # スクロールモード開始時はバックログ追加しないため、フラグは True に設定
            self.backlog_added_for_current = True
            return
        
        # 通常表示
        if self.debug:
            print(f"[TEXT] 通常表示: {character_name}")
        self.displayed_chars = 0
        self.last_char_time = pygame.time.get_ticks()
        self.is_text_complete = False
        self.reset_auto_timer()
        self.last_speaker = character_name
        self.previous_text = text
        # 通常表示ではskip_text()でバックログ追加するため、フラグは False のまま
    
    def update(self):
        if not self.current_text:
            return 
        current_time = pygame.time.get_ticks()

        # 段落切り替え遅延中の処理
        if self.paragraph_transition_waiting:
            if current_time - self.paragraph_transition_start >= self.paragraph_transition_delay:
                self.paragraph_transition_waiting = False
                self.is_ready_for_next = True
                if self.debug:
                    print("[DELAY] 段落切り替え遅延完了、次の段落へ進行可能")
            return

        # 句読点遅延中の処理
        if self.punctuation_waiting:
            if current_time - self.punctuation_wait_start >= self.punctuation_delay:
                self.punctuation_waiting = False
                self.last_char_time = current_time
                if self.debug:
                    print("[DELAY] 句読点遅延完了、テキスト表示再開")
            return

        if not self.is_text_complete:
            char_delay_to_use = self.char_delay
            
            # skipモードの場合は表示速度を40倍にする（char_delayを1/6にする）
            if self.skip_mode:
                char_delay_to_use = self.char_delay // 40
                if char_delay_to_use < 1:  # 最小値は1ms
                    char_delay_to_use = 1
            
            if current_time - self.last_char_time >= char_delay_to_use:
                if self.displayed_chars < len(self.current_text):
                    # 次に表示する文字をチェック
                    next_char = self.current_text[self.displayed_chars]
                    self.displayed_chars += 1
                    
                    # 句読点「。」の場合は追加の遅延を適用（skipモード時は遅延なし）
                    if next_char == '。' and not self.skip_mode:
                        self.punctuation_waiting = True
                        self.punctuation_wait_start = current_time
                        if self.debug:
                            print("[DELAY] 句読点「。」を検出、追加遅延開始")
                        return  # 句読点遅延開始時は処理を中断
                    else:
                        self.last_char_time = current_time
                else:
                    self.is_text_complete = True
                    self.text_complete_time = current_time
                    
                    # バックログへの追加処理は skip_text() でのみ実行するよう変更（重複防止）
                    # update()での自動追加は無効化

        elif (self.auto_mode or self.skip_mode) and self.is_text_complete and not self.is_ready_for_next:
            # スクロール終了直後で段落切り替え遅延が必要な場合（skipモード時は遅延なし）
            if self.scroll_just_ended and not self.paragraph_transition_waiting and not self.skip_mode:
                self.paragraph_transition_waiting = True
                self.paragraph_transition_start = current_time
                self.scroll_just_ended = False  # フラグをリセット
                if self.debug:
                    print(f"[DELAY] スクロール終了後の段落切り替え遅延開始 ({self.paragraph_transition_delay}ms)")
                return
            
            # skipモード時は即座に進行、scrollが終了した場合もskipモードなら即座に進行
            if self.skip_mode and self.scroll_just_ended:
                self.scroll_just_ended = False  # フラグをリセット
                if self.debug:
                    print("[DELAY] skipモードのため段落切り替え遅延をスキップ")
            
            # 通常の自動進行（即座に進行可能に設定）
            self.is_ready_for_next = True
            if self.debug and not self.auto_ready_logged:
                print("自動進行準備完了")
                self.auto_ready_logged = True

    def skip_text(self):
        if self.current_text:
            self.displayed_chars = len(self.current_text)
            self.is_text_complete = True
            self.text_complete_time = pygame.time.get_ticks()
            # 遅延状態をリセット
            self.punctuation_waiting = False
            self.paragraph_transition_waiting = False
            
            # バックログへの追加処理（重複チェック強化、スクロール中は追加しない）
            if (self.backlog_manager and not getattr(self, 'backlog_added_for_current', False) and
                not self.scroll_manager.is_scroll_mode()):
                # 通常モードの場合のみ（スクロール中は scroll_manager が終了時に処理）
                char_name = self.current_character_name if self.current_character_name else None
                self.backlog_manager.add_entry(char_name, self.current_text)
                self.backlog_added_for_current = True  # バックログに追加済みフラグを設定
                if self.debug:
                    print(f"[BACKLOG] スキップ時にテキストをバックログに追加: {char_name} - {self.current_text[:30]}...")

    def is_displaying(self):
        return not self.is_text_complete and bool(self.current_text)

    def render_paragraph(self):
        """現在の会話データを描画する（26文字自動改行 + 3行スクロール）"""
        if not self.current_text:
            # 空テキストのログを1回だけ出力するためのフラグ管理
            if not hasattr(self, '_empty_text_logged') or not self._empty_text_logged:
                if self.debug:
                    print(f"[RENDER] テキストが空のため描画をスキップ")
                self._empty_text_logged = True
            return 0
        
        # テキストがある場合はフラグをリセット
        if hasattr(self, '_empty_text_logged'):
            self._empty_text_logged = False
        
        if self.scroll_manager.is_scroll_mode():
            return self.render_scroll_text()
        
        # 【重要】文字送り時の揺れ対策：完全な文字列でエフェクトを計算してからマスクで切り取る
        full_text = self.current_text  # 完全なテキスト
        display_text_segment = full_text[:self.displayed_chars]  # 表示する部分
        
        # テキストを26文字で自動改行
        all_lines = self._wrap_text(display_text_segment)
        
        # 3行スクロール効果を適用：表示中の文字数に基づいて動的にスクロール
        lines_to_draw = []
        if len(all_lines) <= self.max_display_lines:
            # 3行以下の場合はそのまま表示
            lines_to_draw = all_lines
        else:
            # 3行を超える場合：文字送り進行に応じて最新3行を表示（スクロール効果）
            lines_to_draw = all_lines[-self.max_display_lines:]
            if self.debug and len(all_lines) > self.max_display_lines:
                print(f"[SCROLL] 単一テキストの3行スクロール適用: {len(all_lines)}行 -> 最新{self.max_display_lines}行表示")

        # 話者名と本文に適用する色を決定
        text_color_to_use = self.text_color
        if self.current_character_name:
            gender = CHARACTER_GENDERS.get(self.current_character_name)
            if gender == 'female':
                text_color_to_use = self.text_color_female

        if self.current_character_name and self.current_character_name.strip():
            try:
                # グリッドシステムで名前を描画
                name_surface = self._render_name_with_grid_system(self.current_character_name, text_color_to_use)
                # 名前の座標も整数にスナップ
                name_pos_x = int(round(self.name_start_x))
                name_pos_y = int(round(self.name_start_y))
                self.screen.blit(name_surface, (name_pos_x, name_pos_y))
            except Exception as e:
                if self.debug:
                    print(f"キャラクター名描画エラー: {e}, 名前: '{self.current_character_name}'")

        y = self.text_start_y
        for single_line in lines_to_draw:
            if single_line: # 空の行は描画しない
                try:
                    # 【揺れ対策】完全な行でエフェクトを適用してから部分表示でマスク
                    text_surface = self._render_stable_text_line(single_line, text_color_to_use)
                    # 座標を整数にスナップして揺れを防止
                    pos_x = int(round(self.text_start_x))
                    pos_y = int(round(y))
                    self.screen.blit(text_surface, (pos_x, pos_y))
                except Exception as e:
                    if self.debug:
                        print(f"テキスト描画エラー: {e}, テキスト: '{single_line}'")
            y += self.text_line_height # 各行の後に高さを加算
        return y

    def render_scroll_text(self):
        """スクロールテキストを描画する（各行に適切な話者名を表示）"""
        scroll_text_blocks = self.scroll_manager.get_scroll_lines()
        
        if not scroll_text_blocks:
            return self.text_start_y
        
        # 各行の話者情報を取得（修正点）
        speakers_info = self.scroll_manager.get_line_speakers_info()
        line_speakers = speakers_info['speakers']
        line_is_first = speakers_info['is_first']
        
        # 全ブロックを結合してから3行スクロール処理
        all_lines = []
        line_speaker_mapping = []  # 各行がどの話者の何行目かを記録
        
        for block_index, text_block_content in enumerate(scroll_text_blocks):
            text_to_render_for_block = text_block_content
            
            is_latest_block = (block_index == len(scroll_text_blocks) - 1)
            if is_latest_block and not self.is_text_complete:
                # 最新のブロックで文字送り中の場合、表示する部分までを切り出す
                if self.current_text in text_block_content or text_block_content in self.current_text:
                    # 現在の表示状況に合わせて切り取り
                    displayed_portion = self.current_text[:self.displayed_chars]
                    text_to_render_for_block = displayed_portion

            # テキストを26文字で自動改行
            lines_in_block = self._wrap_text(text_to_render_for_block)
            
            # 各行に話者情報をマッピング
            block_speaker = line_speakers[block_index] if block_index < len(line_speakers) else None
            block_is_first = line_is_first[block_index] if block_index < len(line_is_first) else False
            
            for line_index, line in enumerate(lines_in_block):
                all_lines.append(line)
                # 最初の行のみ話者名を表示する
                should_show_speaker = (block_is_first and line_index == 0)
                line_speaker_mapping.append({
                    'speaker': block_speaker,
                    'show_speaker': should_show_speaker
                })
        
        # 最大3行表示でスクロール効果を適用
        if len(all_lines) <= self.max_display_lines:
            lines_to_draw = all_lines
            speaker_mapping_to_draw = line_speaker_mapping
        else:
            # 3行を超える場合は最新3行のみ表示
            lines_to_draw = all_lines[-self.max_display_lines:]
            speaker_mapping_to_draw = line_speaker_mapping[-self.max_display_lines:]
        
        # 表示エリア内での話者の初回出現を判定（修正点）
        seen_speakers_in_display = set()
        for mapping in speaker_mapping_to_draw:
            speaker = mapping['speaker']
            if speaker and speaker not in seen_speakers_in_display:
                mapping['show_speaker'] = True  # 表示エリア内で初回出現
                seen_speakers_in_display.add(speaker)
            else:
                mapping['show_speaker'] = False  # 既に出現済みまたは話者なし
        
        # 描画処理（修正：各行ごとに正しい話者の色を適用）
        y = self.text_start_y
        for line_index, single_line in enumerate(lines_to_draw):
            speaker_name_to_show = ""
            # デフォルトの色を設定
            speaker_text_color = self.text_color
            
            if line_index < len(speaker_mapping_to_draw):
                mapping = speaker_mapping_to_draw[line_index]
                
                # 話者名を表示すべき行の場合、話者名を設定
                if mapping['show_speaker'] and mapping['speaker']:
                    speaker_name_to_show = mapping['speaker']
                
                # この行の話者に基づいて色を決定（重要な修正点）
                if mapping['speaker']:
                    gender = CHARACTER_GENDERS.get(mapping['speaker'])
                    if gender == 'female':
                        speaker_text_color = self.text_color_female
                    else:
                        speaker_text_color = self.text_color
            
            # 話者名を各行の左側に描画（表示すべき場合のみ）
            if speaker_name_to_show:
                try:
                    # グリッドシステムで話者名を描画
                    name_surface = self._render_name_with_grid_system(speaker_name_to_show, speaker_text_color)
                    # スクロール時の名前座標も整数にスナップ
                    scroll_name_x = int(round(self.name_start_x))
                    scroll_name_y = int(round(y))
                    self.screen.blit(name_surface, (scroll_name_x, scroll_name_y))
                except Exception as e:
                    if self.debug:
                        print(f"スクロール話者名描画エラー: {e}, 名前: '{speaker_name_to_show}'")
            
            # テキストを描画（この行の話者の色を使用）
            if single_line:  # 空の行は描画しない
                try:
                    # 【重要】スクロール時もグリッドシステムを使用
                    text_surface = self._render_stable_text_line(single_line, speaker_text_color)
                    # スクロール時のテキスト座標も整数にスナップ
                    scroll_text_x = int(round(self.text_start_x))
                    scroll_text_y = int(round(y))
                    self.screen.blit(text_surface, (scroll_text_x, scroll_text_y))
                except Exception as e:
                    if self.debug:
                        print(f"スクロールテキスト描画エラー: {e}, テキスト: '{single_line}'")
                        
            y += self.text_line_height # 各行の後に高さを加算
        
        return y

    def render(self):
        if self.backlog_manager and self.backlog_manager.is_showing_backlog():
            return
        self.render_paragraph()
    
    def render_text_window(self, game_state):
        """テキストウィンドウを描画する（メインループから呼び出し用）"""
        self.render()
    
    def set_char_delay(self, delay_ms):
        self.char_delay = delay_ms

    def set_punctuation_delay(self, delay_ms):
        """句読点での遅延時間を設定"""
        self.punctuation_delay = delay_ms

    def set_paragraph_transition_delay(self, delay_ms):
        """段落切り替え遅延時間を設定"""
        self.paragraph_transition_delay = delay_ms

    def force_add_to_backlog(self):
        if self.current_text and self.backlog_manager:
            char_name = self.current_character_name if self.current_character_name else None
            self.backlog_manager.add_to_backlog(self.current_text, char_name)
    
    def reset_scroll_state(self):
        """スクロール状態リセット機能を無効化"""
        if self.debug:
            print("[SCROLL] スクロール状態リセットは無効化されています")
        pass
    
    def on_scene_change(self):
        """シーン変更時のスクロール状態リセットを無効化"""
        if self.debug:
            print(f"[SCROLL] シーン変更時のスクロール状態リセットは無効化されています")
        pass

    def set_max_chars_per_line(self, max_chars):
        """1行あたりの最大文字数を設定"""
        self.max_chars_per_line = max_chars
        if self.debug:
            print(f"1行あたりの最大文字数を{max_chars}文字に設定")
    
    def set_max_display_lines(self, max_lines):
        """最大表示行数を設定"""
        self.max_display_lines = max_lines
        if self.debug:
            print(f"最大表示行数を{max_lines}行に設定")
    
    def set_line_height_multiplier(self, multiplier):
        """行間の倍率を設定"""
        base_line_height = self.fonts["text_pygame"].get_height()
        self.text_line_height = int(base_line_height * multiplier)
        if self.debug:
            print(f"行間倍率を{multiplier}に設定（行高: {self.text_line_height}px）")
    
    def set_char_spacing(self, spacing):
        """文字間隔を設定"""
        self.char_spacing = spacing
        if self.debug:
            print(f"文字間隔を{spacing}pxに設定")
    
    def set_name_display_mode(self, mode="auto"):
        """名前表示モードを設定
        
        Args:
            mode (str): "auto" = 自動均等配置, "normal" = 通常表示
        """
        self.name_display_mode = mode
        if self.debug:
            print(f"名前表示モードを{mode}に設定")