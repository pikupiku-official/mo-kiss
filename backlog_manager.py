import pygame
from config import *
from PyQt5.QtGui import QFont, QImage, QPainter, QColor, QFontMetrics
from PyQt5.QtCore import QSize

def render_text_with_qfont(text, qfont, color):
    """PyQt5のQFontでテキストを描画し、PygameのSurfaceとして返す"""
    metrics = QFontMetrics(qfont)  # PyQt5のQFontMetricsを使用
    width = metrics.horizontalAdvance(text)
    height = metrics.height()
    
    if width == 0 or height == 0:
        # 空のSurfaceを返す
        return pygame.Surface((1, 1), pygame.SRCALPHA)

    # QImageを作成 (ARGB32はアルファチャンネル付き32ビット)
    qimage = QImage(QSize(width, height), QImage.Format_ARGB32)
    qimage.fill(QColor(0, 0, 0, 0))  # 透明で塗りつぶし

    # QPainterでテキストを描画
    painter = QPainter(qimage)
    painter.setFont(qfont)
    painter.setPen(QColor(*color)) # Pygameの色(r,g,b)をQColorに設定
    painter.drawText(0, metrics.ascent(), text)
    painter.end()

    # QImageのデータをPygameのSurfaceに変換
    # tostring()は非推奨なのでbits()を使用
    image_data = qimage.bits().asstring(qimage.sizeInBytes())
    pygame_surface = pygame.image.fromstring(image_data, (width, height), 'RGBA')
    
    return pygame_surface

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
        self.default_text_color = TEXT_COLOR
        self.default_name_color = TEXT_COLOR
        self.female_text_color = TEXT_COLOR_FEMALE
        self.female_name_color = TEXT_COLOR_FEMALE
        
        self.name_font_metrics = QFontMetrics(self.fonts["name"])
        self.text_font_metrics = QFontMetrics(self.fonts["text"])
        self.text_line_height = self.text_font_metrics.height()
        
        # バックログウィンドウのサイズと位置
        self.backlog_width = self.screen.get_width() - 100
        self.backlog_height = self.screen.get_height() - 100
        self.backlog_x = 50
        self.backlog_y = 50

    def get_character_colors(self, char_name):
        """キャラクター名に基づいて色を決定する"""
        if char_name and char_name in CHARACTER_GENDERS:
            gender = CHARACTER_GENDERS.get(char_name)
            if gender == 'female':
                return self.female_name_color, self.female_text_color
        return self.default_name_color, self.default_text_color

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
            visible_items = self.get_visible_backlog_items()
            self.backlog_scroll = max(0.0, float(len(self.backlog) - visible_items))

    def is_showing(self):
        """バックログが表示中かどうか"""
        return self.show_backlog

    def get_visible_backlog_items(self):
        """一度に表示可能なバックログアイテムの数を計算（余裕を持った計算）"""
        available_height = self.backlog_height - (self.backlog_padding * 2)
        # 1アイテムあたり平均3-4行程度を想定して余裕を持って計算
        estimated_lines_per_item = 4
        average_item_height = (
            self.name_font_metrics.height() + 5 +  # キャラクター名 + 余白
            self.text_line_height * estimated_lines_per_item + 
            self.backlog_item_spacing
        )
        
        return max(1, int((available_height / average_item_height)))
    
    def scroll_backlog(self, direction):
        """バックログをスクロール (direction: 1=下, -1=上)"""
        if not self.show_backlog:
            return
            
        # 一行ずつスクロールするために小さい単位を使用
        # 1つのアイテムが平均4行程度なので、0.15で約1行分のスクロール
        scroll_step = 0.15
        
        visible_items = self.get_visible_backlog_items()
        max_scroll = max(0, len(self.backlog) - visible_items)
        
        self.backlog_scroll += direction * scroll_step
        self.backlog_scroll = max(0.0, min(float(max_scroll), self.backlog_scroll))

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
        
        # マウスホイールの連続イベント対応
        elif event.type == pygame.MOUSEWHEEL and self.show_backlog:
            if event.y > 0:  # 上スクロール
                self.scroll_backlog(-1)
            elif event.y < 0:  # 下スクロール
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
        
        # 浮動小数点スクロールに対応した描画位置調整
        start_index = int(self.backlog_scroll)
        scroll_fraction = self.backlog_scroll - start_index
        
        # 1アイテムの平均高さを計算
        estimated_lines_per_item = 4
        average_item_height = (
            self.name_font_metrics.height() + 5 +
            self.text_line_height * estimated_lines_per_item + 
            self.backlog_item_spacing
        )
        
        # スクロールの小数部分に応じて描画開始位置を上に移動
        current_y = start_y - int(scroll_fraction * average_item_height)

        # 描画領域の上下境界（少し余裕を持たせる）
        top_boundary = self.backlog_y + self.backlog_padding + 50  # ヘッダー分の余白
        bottom_boundary = self.backlog_y + self.backlog_height - self.backlog_padding - 50  # フッター分の余白
        
        for i in range(start_index, len(self.backlog)):
            item = self.backlog[i]
            
            # キャラクター名から色を決定
            character_name = item.get('char_name', None)
            name_color, text_color = self.get_character_colors(character_name)
            
            # キャラクター名を一度だけ表示
            if character_name:
                if current_y > bottom_boundary:
                    break
                if current_y + self.name_font_metrics.height() >= top_boundary:
                    # ヘルパー関数を使ってPyQt5フォントを描画
                    name_surface = render_text_with_qfont(character_name, self.fonts["name"], name_color)
                    self.screen.blit(name_surface, (self.backlog_x + self.backlog_padding, current_y))
                current_y += self.name_font_metrics.height() + 5

            # テキストを句点（。）で分割して表示（文字数による自動改行は行わない）
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
                        if len(full_sentence) > 26:
                            for j in range(0, len(full_sentence), 26):
                                lines.append(full_sentence[j:j+26])
                
                for line in lines:
                    if line:
                        if current_y > bottom_boundary:
                            break
                        if current_y + self.text_line_height >= top_boundary:
                            # ヘルパー関数を使ってPyQt5フォントを描画
                            text_surface = render_text_with_qfont(line, self.fonts["text"], text_color)
                            self.screen.blit(text_surface, (self.backlog_x + self.backlog_padding, current_y))
                        current_y += self.text_line_height

            # アイテム間の余白を追加
            if current_y > bottom_boundary:
                break
            
            current_y += self.backlog_item_spacing
            
            # 描画範囲を超えた場合は中断
            if current_y > bottom_boundary:
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
        visible_items = self.get_visible_backlog_items()

        if total_items > visible_items: # スクロール可能な場合のみハンドルを表示
            handle_height = max(20, scrollbar_height // 4)
            
            max_scroll = max(0.0, float(total_items - visible_items))
            if max_scroll > 0:
                handle_position = self.backlog_scroll / max_scroll
            else:
                handle_position = 0.0
                
            handle_y = scrollbar_y + int(handle_position * (scrollbar_height - handle_height))
            
            pygame.draw.rect(self.screen, (150, 150, 150), 
                            (scrollbar_x, handle_y, scrollbar_width, handle_height))
    
    def render(self):
        """バックログの描画メソッド"""
        if self.show_backlog:
            self.render_backlog()