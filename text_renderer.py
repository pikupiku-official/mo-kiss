import pygame
from config import *
from scroll_manager import ScrollManager

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
        
        if should_scroll and character_name:
            if self.scroll_manager.is_scroll_mode() and self.scroll_manager.current_speaker == character_name:
                if self.scroll_manager.continue_scroll(character_name, background, active_characters or [], text):
                    self._start_text_display()
                    return
            
            if self.scroll_manager.should_start_scroll(character_name, background, active_characters or []):
                self.scroll_manager.start_scroll_mode(character_name, background, active_characters or [], text)
                self._start_text_display()
                return
        
        if not should_scroll:
            if self.scroll_manager.is_scroll_mode():
                if self.debug:
                    print(f"[DEBUG] スクロールモード終了")
                self.scroll_manager.end_scroll_mode()
        
        if character_name and background and not self.scroll_manager.is_scroll_mode():
            self.scroll_manager._update_state(character_name, background, active_characters or [])
            
        self._start_text_display()

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
                name_surface = self.fonts["name"].render(self.current_character_name, True, self.name_color)
                self.screen.blit(name_surface, (self.name_start_x, self.name_start_y))
            except Exception as e:
                if self.debug:
                    print(f"キャラクター名描画エラー: {e}, 名前: '{self.current_character_name}'")

        y = self.text_start_y
        for single_line in lines_to_draw:
            if single_line: # 空の行は描画しない (明示的に空行を描画したい場合はこの条件を外す)
                try:
                    text_surface = self.fonts["text"].render(single_line, True, self.text_color)
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
        
        if self.current_character_name and self.current_character_name.strip():
            try:
                name_surface = self.fonts["name"].render(self.current_character_name, True, self.name_color)
                self.screen.blit(name_surface, (self.name_start_x, self.name_start_y))
            except Exception as e:
                if self.debug:
                    print(f"スクロールキャラクター名描画エラー: {e}, 名前: '{self.current_character_name}'")
        
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
                        text_surface = self.fonts["text"].render(single_line, True, self.text_color)
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