import pygame
from config import *

class BacklogManager:
    def __init__(self, screen, fonts):
        self.screen = screen
        self.fonts = fonts
        
        # バックログ機能
        self.backlog = [] # 過去の会話データを保存するリスト
        self.show_backlog = False # バックログ表示モード
        self.backlog_scroll = 0 # バックログのスクロール位置
        self.backlog_max_items = 100 # 最大保存メッセージ数

        # バックログウィンドウの設定
        self.backlog_bg_color = (0, 0, 0, 180)
        self.backlog_border_color = (100, 100, 100)
        self.backlog_padding = 20
        self.backlog_item_spacing = 10
        self.text_color = TEXT_COLOR
        self.name_color = TEXT_COLOR
        self.text_line_height = self.fonts["text_pygame"].get_height()
        
        # バックログウィンドウのサイズと位置
        self.backlog_width = self.screen.get_width() - 100
        self.backlog_height = self.screen.get_height() - 100
        self.backlog_x = 50
        self.backlog_y = 50

    def add_to_backlog(self, text, char_name=None):
        """バックログにテキストを追加する"""
        if not text:
            return
            
        # 同じキャラクターの連続したセリフは統合する
        if (self.backlog and 
            self.backlog[-1].get('char_name') == char_name and char_name is not None):
            # 前のエントリにテキストを追加
            self.backlog[-1]['text'] += text
        else:
            # 新しいエントリを作成
            self.backlog.append({
                'text': text,
                'char_name': char_name
            })

        # 最大保存数を超えた場合、古いメッセージを削除
        if len(self.backlog) > self.backlog_max_items:
            self.backlog.pop(0)

    def toggle_backlog(self):
        """バックログの表示・非表示を切り替え"""
        self.show_backlog = not self.show_backlog
        if self.show_backlog:
            self.backlog_scroll = max(0, len(self.backlog) - self.get_visible_backlog_items())
            self.backlog_scroll = int(self.backlog_scroll)

    def is_showing(self):
        """バックログが表示中かどうか"""
        return self.show_backlog

    def get_visible_backlog_items(self):
        """一度に表示可能なバックログアイテムの数を計算"""
        available_height = self.backlog_height - (self.backlog_padding * 2)
        average_item_height = (
            self.fonts["name"].get_height() + 
            self.text_line_height + 
            self.backlog_item_spacing
        )
        
        return max(1, int((available_height / average_item_height)))
    
    def scroll_backlog(self, direction):
        """バックログをスクロール (direction: 1=下, -1=上)"""
        if not self.show_backlog:
            return
            
        visible_items = self.get_visible_backlog_items()
        max_scroll = max(0, len(self.backlog) - visible_items)
        
        self.backlog_scroll += direction
        self.backlog_scroll = max(0, min(self.backlog_scroll, max_scroll))

    def handle_input(self, event):
        """バックログ関連の入力処理"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_b:  # Bキーでバックログ切り替え
                self.toggle_backlog()
            elif self.show_backlog:
                if event.key == pygame.K_UP:
                    self.scroll_backlog(-1)
                elif event.key == pygame.K_DOWN:
                    self.scroll_backlog(1)
                elif event.key == pygame.K_ESCAPE:
                    self.show_backlog = False
        
        elif event.type == pygame.MOUSEBUTTONDOWN and self.show_backlog:
            if event.button == 4:  # マウスホイール上
                self.scroll_backlog(-1)
            elif event.button == 5:  # マウスホイール下
                self.scroll_backlog(1)

    def render_backlog(self):
        """バックログを描画"""
        if not self.show_backlog:
            return
            
        # 半透明の背景
        backlog_surface = pygame.Surface((self.backlog_width, self.backlog_height), pygame.SRCALPHA)
        backlog_surface.fill(self.backlog_bg_color)
        self.screen.blit(backlog_surface, (self.backlog_x, self.backlog_y))
        
        # 枠線
        pygame.draw.rect(self.screen, self.backlog_border_color, 
                        (self.backlog_x, self.backlog_y, self.backlog_width, self.backlog_height), 2)
        
        # バックログアイテムを描画
        start_y = self.backlog_y + self.backlog_padding
        current_y = start_y
        
        start_index = int(self.backlog_scroll)

        # 描画領域の下端
        bottom_boundary = self.backlog_y + self.backlog_height - self.backlog_padding
        
        for i in range(start_index, len(self.backlog)):
            item = self.backlog[i]
            
            # キャラクター名を一度だけ表示
            character_name = item.get('char_name', None)
            if character_name:
                if current_y + self.fonts["name"].get_height() > bottom_boundary:
                    break
                name_surface = self.fonts["name"].render(character_name, True, self.name_color)
                self.screen.blit(name_surface, (self.backlog_x + self.backlog_padding, current_y))
                current_y += self.fonts["name"].get_height() + 5

            # テキストを句点（。）で分割して表示
            text = item.get('text', '')
            if text:
                # 句点で分割し、句点も含める
                lines = []
                sentences = text.split('。')
                for k, sentence in enumerate(sentences):
                    if sentence.strip():  # 空でない文の場合
                        if k < len(sentences) - 1:  # 最後の要素でない場合は句点を追加
                            full_sentence = sentence + '。'
                        else:  # 最後の要素の場合
                            full_sentence = sentence

                        # 29字を超える場合は29字ごとに分割
                        if len(full_sentence) > 29:
                            for j in range(0, len(full_sentence), 29):
                                lines.append(full_sentence[j:j+29])
                        else:
                            lines.append(full_sentence)
                
                for line in lines:
                    if line:
                        if current_y + self.text_line_height > bottom_boundary:
                            break
                        text_surface = self.fonts["text"].render(line, True, self.text_color)
                        self.screen.blit(text_surface, (self.backlog_x + self.backlog_padding, current_y))
                        current_y += self.text_line_height

            # アイテム間の余白を追加
            if current_y + self.backlog_item_spacing > bottom_boundary:
                break
            
            current_y += self.backlog_item_spacing
            
            # 描画範囲を超えた場合は中断
            if current_y > self.backlog_y + self.backlog_height - self.backlog_padding:
                break
        
        # スクロールバーを描画
        if len(self.backlog) > 1:
            self.render_scrollbar()

    def render_scrollbar(self):
        """スクロールバーを描画"""
        scrollbar_width = 10
        scrollbar_x = self.backlog_x + self.backlog_width - scrollbar_width - 5
        scrollbar_y = self.backlog_y + 50  # ヘッダー分の余白
        scrollbar_height = self.backlog_height - 100
        
        # スクロールバー背景
        pygame.draw.rect(self.screen, (50, 50, 50), 
                        (scrollbar_x, scrollbar_y, scrollbar_width, scrollbar_height))
        
        # スクロールハンドル
        total_items = len(self.backlog)

        if total_items > 1: # ゼロ除算を防ぐ
            handle_height = max(20, scrollbar_height // 4)
            
            if total_items <= 1:
                handle_position = 0
            else:
                handle_position = self.backlog_scroll / (total_items - 1)
                
            handle_y = scrollbar_y + int(handle_position * (scrollbar_height - handle_height))
            
            pygame.draw.rect(self.screen, (150, 150, 150), 
                            (scrollbar_x, handle_y, scrollbar_width, handle_height))
    
    def render(self):
        """バックログの描画メソッド"""
        if self.show_backlog:
            self.render_backlog()