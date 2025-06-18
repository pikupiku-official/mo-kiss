import pygame
from config import *
from PyQt5.QtGui import QFont, QImage, QPainter, QColor, QFontMetrics
from PyQt5.QtCore import QSize

def render_text_with_qfont(text, qfont, color):
    """PyQt5のQFontでテキストを描画し、PygameのSurfaceとして返す"""
    metrics = QFontMetrics(qfont)
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
    painter.setPen(QColor(*color))  # Pygameの色(r,g,b)をQColorに設定
    painter.drawText(0, metrics.ascent(), text)
    painter.end()

    # QImageのデータをPygameのSurfaceに変換
    image_data = qimage.bits().asstring(qimage.sizeInBytes())
    pygame_surface = pygame.image.fromstring(image_data, (width, height), 'RGBA')
    
    return pygame_surface

class BacklogManager:
    def __init__(self, screen, fonts, debug=False):
        self.screen = screen
        self.fonts = fonts
        self.debug = debug
        
        # バックログデータ
        self.entries = []  # [{"speaker": "話者名", "text": "テキスト"}]
        self.is_showing = False
        self.scroll_position = 0
        
        # 表示設定（text_rendererと同じ）
        self.bg_color = (0, 0, 0, 180)
        self.border_color = (100, 100, 100)
        self.default_text_color = TEXT_COLOR
        self.default_name_color = TEXT_COLOR
        self.female_text_color = TEXT_COLOR_FEMALE
        self.female_name_color = TEXT_COLOR_FEMALE
        
        # レイアウト設定
        self.margin = 50
        self.width = screen.get_width() - self.margin * 2
        self.height = screen.get_height() - self.margin * 2
        self.x = self.margin
        self.y = self.margin
        
        self.speaker_width = 200  # 話者名の幅
        self.text_width = self.width - self.speaker_width - 60  # テキスト幅
        self.padding = 20
        self.item_spacing = 15
        
        # フォント設定（text_rendererと同じ）
        self.name_font_metrics = QFontMetrics(self.fonts["name"])
        self.text_font_metrics = QFontMetrics(self.fonts["text"])
        self.text_line_height = self.text_font_metrics.height()
        
    def get_character_colors(self, char_name):
        """キャラクター名に基づいて色を決定する（text_rendererと同じ）"""
        if char_name and char_name in CHARACTER_GENDERS:
            gender = CHARACTER_GENDERS.get(char_name)
            if gender == 'female':
                return self.female_name_color, self.female_text_color
        return self.default_name_color, self.default_text_color
        
    def add_entry(self, speaker, text):
        """バックログにエントリを追加"""
        if not text or text.strip() == "":
            return
            
        # 重複チェック（最後のエントリと同じ場合はスキップ）
        if (self.entries and 
            self.entries[-1]["speaker"] == speaker and 
            self.entries[-1]["text"] == text):
            return
            
        self.entries.append({
            "speaker": speaker or "名無し",
            "text": text
        })
        
        if self.debug:
            print(f"[BACKLOG] エントリ追加: {speaker} - {text[:30]}... (全{len(self.entries)}エントリ)")
    
    def _wrap_text(self, text, max_chars=22):
        """テキストを22文字で改行し、句点でも改行"""
        if not text:
            return []
        
        lines = []
        current_pos = 0
        
        while current_pos < len(text):
            # 句点で改行をチェック
            end_pos = current_pos + max_chars
            if end_pos >= len(text):
                # 残りのテキストが短い場合はそのまま追加
                lines.append(text[current_pos:])
                break
            
            # 現在の範囲で句点があるかチェック
            segment = text[current_pos:end_pos]
            period_pos = segment.find('。')
            
            if period_pos != -1:
                # 句点が見つかった場合、句点の後で改行
                actual_end = current_pos + period_pos + 1
                lines.append(text[current_pos:actual_end])
                current_pos = actual_end
            else:
                # 句点がない場合は22文字で改行
                lines.append(text[current_pos:end_pos])
                current_pos = end_pos
                
        return lines
    
    def toggle_backlog(self):
        """バックログの表示/非表示を切り替え"""
        self.is_showing = not self.is_showing
        if self.is_showing:
            # バックログを開いた時は最下部（最新テキスト）を表示
            total_lines = self._count_total_lines()
            max_lines = self._get_visible_lines()
            if total_lines > max_lines:
                self.scroll_position = total_lines - max_lines
            else:
                self.scroll_position = 0
            if self.debug:
                print(f"[BACKLOG] バックログ表示開始 (全{len(self.entries)}エントリ, スクロール位置: {self.scroll_position})")
    
    def is_showing_backlog(self):
        """バックログが表示中かどうか"""
        return self.is_showing
    
    def scroll_up(self):
        """上にスクロール（行単位）"""
        if self.scroll_position > 0:
            self.scroll_position -= 1
    
    def scroll_down(self):
        """下にスクロール（行単位）"""
        total_lines = self._count_total_lines()
        max_lines = self._get_visible_lines()
        max_scroll = max(0, total_lines - max_lines)
        if self.scroll_position < max_scroll:
            self.scroll_position += 1
    
    def _count_total_lines(self):
        """全エントリの総行数を計算"""
        total_lines = 0
        for entry in self.entries:
            text_lines = self._wrap_text(entry["text"], 22)
            total_lines += len(text_lines)
        return total_lines
    
    def _get_visible_lines(self):
        """表示可能な最大行数（9行固定）"""
        return 9
    
    def handle_input(self, event):
        """入力処理"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_b:
                self.toggle_backlog()
            elif self.is_showing:
                if event.key == pygame.K_UP:
                    self.scroll_up()
                elif event.key == pygame.K_DOWN:
                    self.scroll_down()
                elif event.key == pygame.K_ESCAPE:
                    self.is_showing = False
        
        elif event.type == pygame.MOUSEBUTTONDOWN and self.is_showing:
            if event.button == 4:  # マウスホイール上
                self.scroll_up()
            elif event.button == 5:  # マウスホイール下
                self.scroll_down()
        
        elif event.type == pygame.MOUSEWHEEL and self.is_showing:
            if event.y > 0:  # 上スクロール
                self.scroll_up()
            elif event.y < 0:  # 下スクロール
                self.scroll_down()
    
    def render(self):
        """バックログを描画"""
        if not self.is_showing:
            return
        
        # 背景
        bg_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        bg_surface.fill(self.bg_color)
        self.screen.blit(bg_surface, (self.x, self.y))
        
        # 枠線
        pygame.draw.rect(self.screen, self.border_color, 
                        (self.x, self.y, self.width, self.height), 2)
        
        # 全ての行を作成（話者名とテキスト行を統合）
        all_lines = []
        previous_speaker = None
        
        for entry in self.entries:
            speaker = entry["speaker"]
            text = entry["text"]
            text_lines = self._wrap_text(text, 22)
            
            # 話者が変更された場合のみ話者名を表示
            show_speaker = (speaker != previous_speaker)
            
            # 各エントリの行情報を作成
            for i, line in enumerate(text_lines):
                all_lines.append({
                    "type": "text",
                    "speaker": speaker if (i == 0 and show_speaker) else "",  # 話者変更時の最初の行のみ話者名
                    "text": line,
                    "entry": entry
                })
            
            previous_speaker = speaker
        
        # スクロール位置に基づいて表示する行を決定（最大9行）
        max_lines = self._get_visible_lines()
        start_line = self.scroll_position
        end_line = min(start_line + max_lines, len(all_lines))
        
        # 描画開始位置
        current_y = self.y + self.padding
        
        for i in range(start_line, end_line):
            if i >= len(all_lines):
                break
                
            line_info = all_lines[i]
            speaker = line_info["speaker"]
            text_line = line_info["text"]
            entry = line_info["entry"]
            
            # キャラクター名から色を決定
            name_color, text_color = self.get_character_colors(entry["speaker"])
            
            # 話者名を描画（最初の行のみ）
            if speaker and speaker.strip():
                try:
                    name_surface = render_text_with_qfont(speaker, self.fonts["name"], name_color)
                    self.screen.blit(name_surface, (self.x + self.padding, current_y))
                except Exception as e:
                    if self.debug:
                        print(f"話者名描画エラー: {e}, 名前: '{speaker}'")
            
            # テキストを描画（話者名と同じ高さ）
            text_x = self.x + self.padding + self.speaker_width
            if text_line.strip():
                try:
                    text_surface = render_text_with_qfont(text_line, self.fonts["text"], text_color)
                    self.screen.blit(text_surface, (text_x, current_y))
                except Exception as e:
                    if self.debug:
                        print(f"テキスト描画エラー: {e}, テキスト: '{text_line}'")
            
            current_y += self.text_line_height
        