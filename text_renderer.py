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
        self.name_color = TEXT_COLOR
        self.text_bg_color = TEXT_BG_COLOR
        self.text_positions = get_text_positions(screen)
        self.text_start_x = self.text_positions["speech_1"][0]
        self.text_start_y = self.text_positions["speech_1"][1]
        self.name_start_x = self.text_positions["name_1"][0]
        self.name_start_y = self.text_positions["name_1"][1]
        self.line_spacing = TEXT_LINE_SPACING
        self.text_line_height = self.fonts["text_pygame"].get_height()
        self.text_padding = TEXT_PADDING

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

        self.auto_mode = False
        self.auto_delay = 1500
        self.text_complete_time = 0
        self.is_ready_for_next = False
        self.auto_ready_logged = False
        
        self.backlog_manager = None
        self.scroll_manager = ScrollManager(debug)

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

    def set_dialogue(self, text, character_name=None, should_scroll=False, background=None, active_characters=None):
        if self.debug:
            scroll_status = "スクロール" if should_scroll else "通常"
            print(f"[TEXT] {scroll_status}表示: {character_name} - '{text[:30] if text else ''}...'")
        
        self.current_text = str(text) if text is not None else ""
        self.current_character_name = str(character_name) if character_name is not None else ""
        
        # 現在の話者を記録（前回の話者との比較用）
        if not hasattr(self, 'last_speaker'):
            self.last_speaker = None
        
        # スクロール表示の処理
        if should_scroll and character_name:
            # 既にスクロールモード中で同じ話者の場合は継続
            if self.scroll_manager.is_scroll_mode() and self.scroll_manager.current_speaker == character_name:
                if self.scroll_manager.continue_scroll(character_name, text):
                    self._start_text_display()
                    return
            
            # 話者が変わった場合は、スクロールを完全にリセットして新規開始
            if self.scroll_manager.is_scroll_mode() and self.scroll_manager.current_speaker != character_name:
                if self.debug:
                    print(f"[SCROLL] 話者変更によりスクロールリセット: {self.scroll_manager.current_speaker} -> {character_name}")
                self.scroll_manager.end_scroll_mode()
            
            # スクロールモードでない場合で、前回の話者と同じ場合は前のテキストを保持
            if (not self.scroll_manager.is_scroll_mode() and 
                self.last_speaker == character_name):
                if self.debug:
                    print(f"[SCROLL] 同一話者での通常→スクロール表示のため前テキスト保持: {character_name}")
                self.scroll_manager.start_scroll_mode(character_name, text, keep_previous=True)
                self._start_text_display()
                self.last_speaker = character_name
                return
            
            # 新しくスクロール開始（前のテキストはクリア）
            self.scroll_manager.start_scroll_mode(character_name, text, keep_previous=False)
            self._start_text_display()
            self.last_speaker = character_name
            return
        
        # 通常表示の処理
        if not should_scroll:
            # 通常表示の場合で、スクロールモード中かつ同一話者の場合のみ継続
            if (self.scroll_manager.is_scroll_mode() and 
                character_name and 
                self.scroll_manager.current_speaker == character_name):
                # 同一話者での通常表示をスクロールに追加
                if self.debug:
                    print(f"[SCROLL] 同一話者の通常表示をスクロールに追加: {character_name}")
                self.scroll_manager.add_text_to_scroll(text)
                self.scroll_manager.current_speaker = character_name
                self._start_text_display()
                self.last_speaker = character_name
                return
            else:
                # 話者が変わった場合や、スクロールモードでない場合は通常表示
                if self.scroll_manager.is_scroll_mode():
                    if self.debug:
                        print(f"[DEBUG] 話者変更または通常表示によりスクロールモード終了")
                    self.scroll_manager.end_scroll_mode()
                
                # 通常表示として処理し、前回テキストを保持（ScrollManagerに追加）
                if character_name:
                    if self.debug:
                        print(f"[SCROLL] 通常表示テキストを保持: {character_name}")
                    # 新しいスクロールモードを開始して、このテキストを最初に追加
                    self.scroll_manager.start_scroll_mode(character_name, text, keep_previous=False)
                    # ただし、スクロールモードは無効にして通常表示として扱う
                    self.scroll_manager.scroll_mode = False
                
                self._start_text_display()
                self.last_speaker = character_name
                return
        
        self._start_text_display()
        self.last_speaker = character_name

    def _start_text_display(self):
        self.displayed_chars = 0
        self.last_char_time = pygame.time.get_ticks()
        self.is_text_complete = False
        self.reset_auto_timer()

    def update(self):
        if not self.current_text:
            return 
        current_time = pygame.time.get_ticks()

        if not self.is_text_complete:
            char_delay_to_use = self.char_delay
            
            current_time = pygame.time.get_ticks()
            if current_time - self.last_char_time >= char_delay_to_use:
                if self.displayed_chars < len(self.current_text):
                    self.displayed_chars += 1
                    self.last_char_time = current_time
                else:
                    self.is_text_complete = True
                    self.text_complete_time = current_time
                    if self.backlog_manager and self.current_text:
                        char_name = self.current_character_name if self.current_character_name else None
                        self.backlog_manager.add_to_backlog(self.current_text, char_name)

        elif self.auto_mode and self.is_text_complete and not self.is_ready_for_next:
            auto_delay = self.auto_delay
            
            if current_time - self.text_complete_time >= auto_delay:
                self.is_ready_for_next = True
                if self.debug and not self.auto_ready_logged:
                    print("自動進行準備完了")
                    self.auto_ready_logged = True

    def skip_text(self):
        if self.current_text:
            self.displayed_chars = len(self.current_text)
            self.is_text_complete = True
            self.text_complete_time = pygame.time.get_ticks()
            if self.backlog_manager:
                char_name = self.current_character_name if self.current_character_name else None
                self.backlog_manager.add_to_backlog(self.current_text, char_name)

    def is_displaying(self):
        return not self.is_text_complete and bool(self.current_text)

    def render_paragraph(self):
        """現在の会話データを描画する（改行コード'\n'をサポート）"""
        if not self.current_text:
            return 0
        
        if self.scroll_manager.is_scroll_mode():
            return self.render_scroll_text()
        
        display_text_segment = self.current_text[:self.displayed_chars]
        
        # テキストを改行コードで分割
        lines_to_draw = display_text_segment.splitlines()
        # もし display_text_segment が空でなく、splitlines() が空リストを返す場合（例: "text" のみで改行なし）
        if not lines_to_draw and display_text_segment:
            lines_to_draw = [display_text_segment]

        if self.current_character_name and self.current_character_name.strip():
            try:
                name_surface = self.pygame_fonts["name"].render(self.current_character_name, True, self.name_color)
                self.screen.blit(name_surface, (self.name_start_x, self.name_start_y))
            except Exception as e:
                if self.debug:
                    print(f"キャラクター名描画エラー: {e}, 名前: '{self.current_character_name}'")

        y = self.text_start_y
        for single_line in lines_to_draw:
            if single_line: # 空の行は描画しない (明示的に空行を描画したい場合はこの条件を外す)
                try:
                    text_surface = self.pygame_fonts["text"].render(single_line, True, self.text_color)
                    self.screen.blit(text_surface, (self.text_start_x, y))
                except Exception as e:
                    if self.debug:
                        print(f"テキスト描画エラー: {e}, テキスト: '{single_line}'")
            y += self.text_line_height # 各行の後に高さを加算 (空行でも高さを消費させる)
        return y

    def render_scroll_text(self):
        """スクロールテキストを描画する（改行コード'\n'をサポート）"""
        scroll_text_blocks = self.scroll_manager.get_scroll_lines()
        
        if not scroll_text_blocks:
            return self.text_start_y
        
        # スクロールモードでは現在のスピーカーの名前を表示
        display_name = self.scroll_manager.current_speaker if self.scroll_manager.current_speaker else self.current_character_name
        
        if display_name and display_name.strip():
            try:
                name_surface = self.pygame_fonts["name"].render(display_name, True, self.name_color)
                self.screen.blit(name_surface, (self.name_start_x, self.name_start_y))
            except Exception as e:
                if self.debug:
                    print(f"スクロールキャラクター名描画エラー: {e}, 名前: '{display_name}'")
        
        y = self.text_start_y
        for block_index, text_block_content in enumerate(scroll_text_blocks):
            text_to_render_for_block = text_block_content
            
            is_latest_block = (block_index == len(scroll_text_blocks) - 1)
            if is_latest_block and not self.is_text_complete:
                # 最新のブロックで文字送り中の場合、表示する部分までを切り出す
                # self.current_text は scroll_text_blocks の最後の要素と同じはず
                text_to_render_for_block = self.current_text[:self.displayed_chars]

            lines_in_block_to_draw = text_to_render_for_block.splitlines()
            if not lines_in_block_to_draw and text_to_render_for_block:
                 lines_in_block_to_draw = [text_to_render_for_block]

            for single_line in lines_in_block_to_draw:
                if single_line: # 空の行は描画しない
                    try:
                        text_surface = self.pygame_fonts["text"].render(single_line, True, self.text_color)
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

    def set_auto_delay(self, delay_ms):
        self.auto_delay = delay_ms
        if self.debug:
            print(f"自動進行遅延を {delay_ms}ms に設定しました")

    def force_add_to_backlog(self):
        if self.current_text and self.backlog_manager:
            char_name = self.current_character_name if self.current_character_name else None
            self.backlog_manager.add_to_backlog(self.current_text, char_name)
    
    def reset_scroll_state(self):
        self.scroll_manager.reset_state()
    
    def on_background_change(self):
        if self.debug:
            print(f"[DEBUG] 背景変更によるスクロール完全停止")
        self.scroll_manager.end_scroll_mode()
    
    def on_scene_change(self):
        if self.debug:
            print(f"[DEBUG] シーン変更によるスクロール状態リセット")
        self.scroll_manager.reset_state()