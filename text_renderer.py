import pygame
from config import *
from scroll_manager import ScrollManager
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
        self.text_line_height = self.fonts["text_pygame"].get_height()
        self.text_padding = TEXT_PADDING

        # 26文字での自動改行を設定
        self.max_chars_per_line = 26
        # 最大表示行数
        self.max_display_lines = 3

        self.pygame_fonts = {
            "text": self.fonts["text_pygame"],
            "name": self.fonts["name_pygame"]
        }
        
        self.current_text = ""
        self.current_character_name = None

        self.displayed_chars = 0
        self.last_char_time = 0
        self.char_delay = 110
        self.is_text_complete = False

        # 新しい遅延設定を追加
        self.punctuation_delay = 500  # 句読点「。」での追加遅延時間（ミリ秒）
        self.paragraph_transition_delay = 1000  # スクロール終了後の段落切り替え遅延時間（ミリ秒）
        self.punctuation_waiting = False  # 句読点遅延中フラグ
        self.punctuation_wait_start = 0  # 句読点遅延開始時刻
        self.paragraph_transition_waiting = False  # 段落切り替え遅延中フラグ
        self.paragraph_transition_start = 0  # 段落切り替え遅延開始時刻
        self.scroll_just_ended = False  # スクロールが直前に終了したかのフラグ

        self.auto_mode = False
        self.text_complete_time = 0
        self.is_ready_for_next = False
        self.auto_ready_logged = False
        
        self.backlog_manager = None
        self.scroll_manager = ScrollManager(debug)
        # ScrollManagerにTextRendererの参照を設定
        self.scroll_manager.set_text_renderer(self)

    def _wrap_text(self, text):
        """テキストを26文字で自動改行する"""
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
            
            # 26文字ごとに分割
            current_pos = 0
            while current_pos < len(paragraph):
                line_end = current_pos + self.max_chars_per_line
                if line_end >= len(paragraph):
                    # 最後の行
                    wrapped_lines.append(paragraph[current_pos:])
                    break
                else:
                    # 26文字で切り取り
                    wrapped_lines.append(paragraph[current_pos:line_end])
                    current_pos = line_end
        
        return wrapped_lines

    def _get_display_lines_with_scroll(self, display_text_segment):
        """表示用のテキストを26文字改行して、3行スクロール効果を適用"""
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
            name_font_size = int(SCREEN_HEIGHT * 47 / 1000)
            text_font_size = int(SCREEN_HEIGHT * 47 / 1000)
            default_font_size = int(SCREEN_HEIGHT * 0.027)  # 画面高さの2.7%
            
            # フォントファイルのパスを設定
            font_dir = os.path.join(os.path.dirname(__file__), "fonts")
            bold_font_path = os.path.join(font_dir, "MPLUSRounded1c-Bold.ttf")
            medium_font_path = os.path.join(font_dir, "MPLUSRounded1c-Regular.ttf")

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
            return self._get_fallback_fonts(
                int(SCREEN_HEIGHT * 0.044),
                int(SCREEN_HEIGHT * 0.044),
                int(SCREEN_HEIGHT * 0.027)
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

    def set_backlog_manager(self, backlog_manager):
        self.backlog_manager = backlog_manager

    def toggle_auto_mode(self):
        self.auto_mode = not self.auto_mode
        if self.debug:
            print(f"自動モード: {'ON' if self.auto_mode else 'OFF'}")
        return self.auto_mode
    
    def is_auto_mode(self):
        return self.auto_mode
    
    def is_ready_for_auto_advance(self):
        return self.auto_mode and self.is_ready_for_next
    
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
        
        self.current_text = str(text) if text is not None else ""
        self.current_character_name = str(character_name) if character_name is not None else ""
        
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
            
            # 話者が変わった場合は現在の話者を更新
            if self.scroll_manager.get_current_speaker() != character_name:
                if self.debug:
                    print(f"[SCROLL] 話者変更だがスクロール継続: {self.scroll_manager.get_current_speaker()} -> {character_name}")
                self.scroll_manager.current_speaker = character_name
            
            # テキストをスクロールに追加
            self.scroll_manager.add_text_to_scroll(text)
            self.displayed_chars = 0
            self.last_char_time = pygame.time.get_ticks()
            self.is_text_complete = False
            self.reset_auto_timer()
            self.last_speaker = character_name
            self.previous_text = text
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
                # 前のテキストでスクロール開始
                self.scroll_manager.start_scroll_mode(character_name, self.previous_text)
                # 現在のテキストを追加
                self.scroll_manager.add_text_to_scroll(text)
            else:
                # 新しくスクロール開始
                self.scroll_manager.start_scroll_mode(character_name, text)
            
            self.displayed_chars = 0
            self.last_char_time = pygame.time.get_ticks()
            self.is_text_complete = False
            self.reset_auto_timer()
            self.last_speaker = character_name
            self.previous_text = text
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
            
            if current_time - self.last_char_time >= char_delay_to_use:
                if self.displayed_chars < len(self.current_text):
                    # 次に表示する文字をチェック
                    next_char = self.current_text[self.displayed_chars]
                    self.displayed_chars += 1
                    
                    # 句読点「。」の場合は追加の遅延を適用
                    if next_char == '。':
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
                    if self.backlog_manager and self.current_text:
                        char_name = self.current_character_name if self.current_character_name else None
                        self.backlog_manager.add_to_backlog(self.current_text, char_name)

        elif self.auto_mode and self.is_text_complete and not self.is_ready_for_next:
            # スクロール終了直後で段落切り替え遅延が必要な場合
            if self.scroll_just_ended and not self.paragraph_transition_waiting:
                self.paragraph_transition_waiting = True
                self.paragraph_transition_start = current_time
                self.scroll_just_ended = False  # フラグをリセット
                if self.debug:
                    print(f"[DELAY] スクロール終了後の段落切り替え遅延開始 ({self.paragraph_transition_delay}ms)")
                return
            
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
            if self.backlog_manager:
                char_name = self.current_character_name if self.current_character_name else None
                self.backlog_manager.add_to_backlog(self.current_text, char_name)

    def is_displaying(self):
        return not self.is_text_complete and bool(self.current_text)

    def render_paragraph(self):
        """現在の会話データを描画する（26文字自動改行 + 3行スクロール）"""
        if not self.current_text:
            return 0
        
        if self.scroll_manager.is_scroll_mode():
            return self.render_scroll_text()
        
        display_text_segment = self.current_text[:self.displayed_chars]
        
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
                name_surface = self.pygame_fonts["name"].render(self.current_character_name, True, text_color_to_use)
                self.screen.blit(name_surface, (self.name_start_x, self.name_start_y))
            except Exception as e:
                if self.debug:
                    print(f"キャラクター名描画エラー: {e}, 名前: '{self.current_character_name}'")

        y = self.text_start_y
        for single_line in lines_to_draw:
            if single_line: # 空の行は描画しない
                try:
                    text_surface = self.pygame_fonts["text"].render(single_line, True, text_color_to_use)
                    self.screen.blit(text_surface, (self.text_start_x, y))
                except Exception as e:
                    if self.debug:
                        print(f"テキスト描画エラー: {e}, テキスト: '{single_line}'")
            y += self.text_line_height # 各行の後に高さを加算
        return y

    def render_scroll_text(self):
        """スクロールテキストを描画する（26文字自動改行対応 + 最大3行表示）"""
        scroll_text_blocks = self.scroll_manager.get_scroll_lines()
        
        if not scroll_text_blocks:
            return self.text_start_y
        
        # スクロールモードでは現在のスピーカーの名前を表示
        display_name = self.scroll_manager.current_speaker if self.scroll_manager.current_speaker else self.current_character_name

        # 話者名と本文に適用する色を決定
        color_to_use = self.text_color
        if display_name:
            gender = CHARACTER_GENDERS.get(display_name)
            if gender == 'female':
                color_to_use = self.text_color_female
        
        if display_name and display_name.strip():
            try:
                name_surface = self.pygame_fonts["name"].render(display_name, True, color_to_use)
                self.screen.blit(name_surface, (self.name_start_x, self.name_start_y))
            except Exception as e:
                if self.debug:
                    print(f"スクロールキャラクター名描画エラー: {e}, 名前: '{display_name}'")
        
        # 全ブロックを結合してから3行スクロール処理
        all_lines = []
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
            all_lines.extend(lines_in_block)
        
        # 最大3行表示でスクロール効果を適用
        lines_to_draw = []
        if len(all_lines) <= self.max_display_lines:
            lines_to_draw = all_lines
        else:
            # 3行を超える場合は最新3行のみ表示
            lines_to_draw = all_lines[-self.max_display_lines:]
            if self.debug:
                print(f"[SCROLL] スクロール表示: {len(all_lines)}行 -> 最新{self.max_display_lines}行表示")
        
        y = self.text_start_y
        for single_line in lines_to_draw:
            if single_line: # 空の行は描画しない
                try:
                    text_surface = self.pygame_fonts["text"].render(single_line, True, color_to_use)
                    self.screen.blit(text_surface, (self.text_start_x, y))
                except Exception as e:
                    if self.debug:
                        print(f"スクロールテキスト描画エラー: {e}, テキスト: '{single_line}'")
            y += self.text_line_height # 各行の後に高さを加算
        
        return y

    def render(self):
        if self.backlog_manager and self.backlog_manager.is_showing():
            return
        self.render_paragraph()
    
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