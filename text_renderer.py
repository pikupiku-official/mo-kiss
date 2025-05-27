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
        
        # 現在の会話データ
        self.current_text = ""
        self.current_character_name = None

        # 文字表示制限のための変数
        self.displayed_chars = 0 # 現在表示されている文字数
        self.last_char_time = 0 # 最後に文字を表示した時間
        self.char_delay = 70 # 文字間の遅延
        self.is_text_complete = False # テキスト表示が完了したかどうか

        # 自動テキスト遷移機能
        self.auto_mode = False # 自動モードのON/OFF
        self.auto_delay = 1000 # テキスト表示完了後の待機時間（ミリ秒）
        self.text_complete_time = 0 # テキスト表示が完了した時刻
        self.is_ready_for_next = False # 次のテキストに進む準備ができているか
        self.auto_ready_logged = False # 自動進行準備完了ログ出力済みフラグ
        
        # バックログに参照を持つ
        self.backlog_manager = None

        # スクロールマネージャーの追加
        self.scroll_manager = ScrollManager(debug)

    def set_backlog_manager(self, backlog_manager):
        """バックログマネージャーをセットする"""
        self.backlog_manager = backlog_manager

    def toggle_auto_mode(self):
        """自動モードを切り替える"""
        self.auto_mode = not self.auto_mode
        if self.debug:
            print(f"自動モード: {'ON' if self.auto_mode else 'OFF'}")
        return self.auto_mode
    
    def is_auto_mode(self):
        """自動モードかどうかを返す"""
        return self.auto_mode
    
    def is_ready_for_auto_advance(self):
        """自動進行の準備ができているかどうか"""
        return self.auto_mode and self.is_ready_for_next
    
    def reset_auto_timer(self):
        """自動進行タイマーをリセット"""
        self.is_ready_for_next = False
        self.text_complete_time = 0
        self.auto_ready_logged = False

    def set_dialogue(self, text, character_name=None, should_scroll=False, background=None, active_characters=None):
        """会話データを設定する"""
        print(f"[DEBUG] set_dialogue開始: should_scroll={should_scroll}, speaker={character_name}")
        
        # Noneや空文字列の処理
        self.current_text = str(text) if text is not None else ""
        self.current_character_name = str(character_name) if character_name is not None else ""
        
        # スクロール処理（should_scrollがTrueの場合のみ）
        if should_scroll and character_name:
            print(f"[DEBUG] スクロール処理開始: speaker={character_name}, background={background}")
            
            if self.scroll_manager.is_scroll_mode():
                # スクロール継続
                print(f"[DEBUG] 既にスクロールモード中、継続判定")
                if self.scroll_manager.continue_scroll(character_name, background, active_characters or [], text):
                    print(f"[DEBUG] スクロール継続成功")
                    self.displayed_chars = len(self.current_text)
                    self.is_text_complete = True
                    self.text_complete_time = pygame.time.get_ticks()
                    self.reset_auto_timer()
                    return
                else:
                    print(f"[DEBUG] スクロール継続失敗、通常表示へ")
            
            # 新規スクロール開始の判定（必ず実行）
            print(f"[DEBUG] should_start_scroll呼び出し開始")
            should_start = self.scroll_manager.should_start_scroll(character_name, background, active_characters or [])
            print(f"[DEBUG] should_start_scroll結果: {should_start}")
            
            if should_start:
                print(f"[DEBUG] 新規スクロール開始")
                self.scroll_manager.start_scroll_mode(character_name, background, active_characters or [], text)
                self.displayed_chars = len(self.current_text)
                self.is_text_complete = True
                self.text_complete_time = pygame.time.get_ticks()
                self.reset_auto_timer()
                return
            else:
                print(f"[DEBUG] スクロール開始条件未満")
        else:
            print(f"[DEBUG] スクロール処理スキップ: should_scroll={should_scroll}, character_name={character_name}")
            # スクロール対象外の場合のみend_scroll_mode()を呼ぶ
            if not should_scroll:
                self.scroll_manager.end_scroll_mode()
        
        # 通常のテキスト表示
        print(f"[DEBUG] 通常表示モード")
        # should_scroll=Trueでもスクロール開始条件に合わない場合は、状態をリセットしない
        if not should_scroll:
            self.scroll_manager.end_scroll_mode()
            
        self.displayed_chars = 0
        self.last_char_time = pygame.time.get_ticks()
        self.is_text_complete = False
        
        # 自動進行タイマーをリセット
        self.reset_auto_timer()

    def update(self):
        """文字表示の更新"""
        if not self.current_text:
            return 
        current_time = pygame.time.get_ticks()

        # 文字表示の更新
        if not self.is_text_complete:
            # 文字表示のタイミングチェック
            if current_time - self.last_char_time >= self.char_delay:
                if self.displayed_chars < len(self.current_text):
                    self.displayed_chars += 1
                    self.last_char_time = current_time
                else:
                    self.is_text_complete = True
                    self.text_complete_time = current_time
                    # テキスト表示完了時にバックログへ追加
                    if self.backlog_manager and self.current_text:
                        # 空文字列でないキャラクター名のみ渡す
                        char_name = self.current_character_name if self.current_character_name else None
                        self.backlog_manager.add_to_backlog(self.current_text, char_name)

        # 自動進行の更新
        elif self.auto_mode and self.is_text_complete and not self.is_ready_for_next:
            # テキスト表示完了後の待機時間をチェック
            if current_time - self.text_complete_time >= self.auto_delay:
                self.is_ready_for_next = True
                if self.debug and not self.auto_ready_logged:
                    print("自動進行準備完了")
                    self.auto_ready_logged = True

    def skip_text(self):
        """テキスト表示をスキップして全文表示"""
        if self.current_text:
            self.displayed_chars = len(self.current_text)
            self.is_text_complete = True
            self.text_complete_time = pygame.time.get_ticks()
            # スキップ時にもバックログへ追加
            if self.backlog_manager:
                char_name = self.current_character_name if self.current_character_name else None
                self.backlog_manager.add_to_backlog(self.current_text, char_name)

    def is_displaying(self):
        """現在文字を表示中かどうか"""
        return not self.is_text_complete and bool(self.current_text)

    def render_paragraph(self):
        """現在の会話データを描画する"""
        if not self.current_text:
            return 0
        
        # スクロールモードの場合
        if self.scroll_manager.is_scroll_mode():
            return self.render_scroll_text()
        
        # 表示する文字列を取得
        display_text = self.current_text[:self.displayed_chars]
        lines = []
        for i in range(0, len(display_text), 26):
            lines.append(display_text[i:i+26])

        # キャラクター名の描画
        if self.current_character_name and self.current_character_name.strip():
            try:
                name_surface = self.fonts["name"].render(self.current_character_name, True, self.name_color)
                self.screen.blit(name_surface, (self.name_start_x, self.name_start_y))
            except Exception as e:
                if self.debug:
                    print(f"キャラクター名描画エラー: {e}, 名前: '{self.current_character_name}'")

        # 各行を描画
        y = self.text_start_y
        for line in lines:
            if line:
                try:
                    text_surface = self.fonts["text"].render(line, True, self.text_color)
                    self.screen.blit(text_surface, (self.text_start_x, y))
                except Exception as e:
                    if self.debug:
                        print(f"テキスト描画エラー: {e}, テキスト: '{line}'")
            y += self.text_line_height

        return y

    def render_scroll_text(self):
        """スクロールテキストを描画する"""
        scroll_lines = self.scroll_manager.get_scroll_lines()
        
        # キャラクター名の描画
        if self.current_character_name and self.current_character_name.strip():
            try:
                name_surface = self.fonts["name"].render(self.current_character_name, True, self.name_color)
                self.screen.blit(name_surface, (self.name_start_x, self.name_start_y))
            except Exception as e:
                if self.debug:
                    print(f"スクロールキャラクター名描画エラー: {e}, 名前: '{self.current_character_name}'")
        
        # スクロール行を描画（最大3行）
        y = self.text_start_y
        for line in scroll_lines[-3:]:  # 最新の3行のみ表示
            if line:
                try:
                    text_surface = self.fonts["text"].render(line, True, self.text_color)
                    self.screen.blit(text_surface, (self.text_start_x, y))
                except Exception as e:
                    if self.debug:
                        print(f"スクロールテキスト描画エラー: {e}, テキスト: '{line}'")
            y += self.text_line_height
        
        return y

    def render(self):
        """メインの描画メソッド"""
        # バックログが表示中の場合はテキストを描画しない
        if self.backlog_manager and self.backlog_manager.is_showing():
            return
        
        self.render_paragraph()
    
    def set_char_delay(self, delay_ms):
        """文字間の遅延を設定する"""
        self.char_delay = delay_ms

    def set_auto_delay(self, delay_ms):
        """自動進行の遅延を設定する"""
        self.auto_delay = delay_ms
        if self.debug:
            print(f"自動進行遅延を {delay_ms}ms に設定しました")

    def force_add_to_backlog(self):
        """現在の会話を強制的にバックログに追加（デバッグ用）"""
        if self.current_text and self.backlog_manager:
            char_name = self.current_character_name if self.current_character_name else None
            self.backlog_manager.add_to_backlog(self.current_text, char_name)