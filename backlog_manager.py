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
        
        # 仮想解像度基準のピクセル値設定（1920x1080基準）
        from config import VIRTUAL_WIDTH, VIRTUAL_HEIGHT, scale_pos, scale_size
        
        # レイアウト設定を先に計算する必要があるため、後でフォントサイズを計算する
        
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
        self.choice_color = TEXT_COLOR
        
        # レイアウト設定（仮想解像度1920x1080基準のピクセル値）
        # 仮想座標でのレイアウト計算
        virtual_margin = 50  # 1920 * 0.026 = 50px
        virtual_width = VIRTUAL_WIDTH - virtual_margin * 2
        virtual_height = VIRTUAL_HEIGHT - virtual_margin * 2 - 50
        
        virtual_speaker_width = 200  # 1920 * 0.104 = 200px
        virtual_text_width = virtual_width - virtual_speaker_width - 60  # 1920 * 0.031 = 60pxの余白
        virtual_padding = 19  # 1920 * 0.01 = 19px
        virtual_item_spacing = 15  # 1920 * 0.008 = 15px

        # 実際の画面座標にスケーリング
        self.margin = scale_size(virtual_margin, 0)[0]
        self.width, self.height = scale_size(virtual_width, virtual_height)
        self.x, self.y = scale_pos(virtual_margin, virtual_margin)
        
        self.speaker_width = scale_size(virtual_speaker_width, 0)[0]
        self.text_width = scale_size(virtual_text_width, 0)[0]
        self.padding = scale_size(virtual_padding, 0)[0]
        self.item_spacing = scale_size(virtual_item_spacing, 0)[0]

        # フォントサイズはtext_rendererと同じ方法で計算（実際の画面高さに基づく）
        # 画面サイズによる差を大きくし、全体的にサイズアップ
        base_size = int(SCREEN_HEIGHT * 49 / 1000)  # ベースサイズを30から45に増加
        scale_factor = SCREEN_HEIGHT / 1080.0  # 1080pを基準とした倍率
        size_multiplier = 0.1 + (scale_factor * 0.9)  # 0.8〜1.2の範囲で変動
        self.text_font_size = int(base_size * size_multiplier)
        self.name_font_size = self.text_font_size

        # フォント設定（バックログ用に新しいフォントオブジェクトを作成）
        from PyQt5.QtGui import QFont, QFontMetrics
        from config import SCALE
        
        # 元のフォントファミリー名を取得
        name_font_family = self.fonts["name"].family()
        text_font_family = self.fonts["text"].family()
        name_font_weight = self.fonts["name"].weight()
        text_font_weight = self.fonts["text"].weight()
        
        # バックログ用のフォントを作成（元のfontsは変更しない）
        self.backlog_name_font = QFont(name_font_family, self.name_font_size)
        self.backlog_name_font.setWeight(name_font_weight)
        self.backlog_text_font = QFont(text_font_family, self.text_font_size)  
        self.backlog_text_font.setWeight(text_font_weight)
        
        self.name_font_metrics = QFontMetrics(self.backlog_name_font)
        self.text_font_metrics = QFontMetrics(self.backlog_text_font)
        self.text_line_height = self.text_font_metrics.height()
        
        if self.debug:
            print(f"[BACKLOG] バックログ背景高さ: {self.height}px")
            print(f"[BACKLOG] フォントサイズ: {self.text_font_size}px (背景高さの1/30)")
            print(f"[BACKLOG] 行の高さ: {self.text_line_height}px")
        
    def get_character_colors(self, char_name):
        """キャラクター名に基づいて色を決定する（text_rendererと同じ）"""
        # 選択肢の場合は専用色を使用
        if char_name == "選択":
            return self.choice_color, self.choice_color
        
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
    
    def _wrap_text(self, text, max_chars=26):
        """テキストを26文字で改行し、句点でも改行"""
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
                # 句点がない場合は26文字で改行
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
            text_lines = self._wrap_text(entry["text"], 26)
            total_lines += len(text_lines)
        return total_lines
    
    def _get_visible_lines(self):
        """表示可能な最大行数（11行固定）"""
        return 11
    
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
            text_lines = self._wrap_text(text, 26)
            
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
        
        # スクロール位置に基づいて表示する行を決定（最大11行）
        max_lines = self._get_visible_lines()
        start_line = self.scroll_position
        end_line = min(start_line + max_lines, len(all_lines))
        
        # 描画開始位置
        current_y = self.y + self.padding + 10
        
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
                    name_surface = render_text_with_qfont(speaker, self.backlog_name_font, name_color)
                    self.screen.blit(name_surface, (self.x + self.padding, current_y))
                except Exception as e:
                    if self.debug:
                        print(f"話者名描画エラー: {e}, 名前: '{speaker}'")
            
            # テキストを描画（話者名と同じ高さ）
            text_x = self.x + self.padding + self.speaker_width + 60
            if text_line.strip():
                try:
                    text_surface = render_text_with_qfont(text_line, self.backlog_text_font, text_color)
                    self.screen.blit(text_surface, (text_x, current_y))
                except Exception as e:
                    if self.debug:
                        print(f"テキスト描画エラー: {e}, テキスト: '{text_line}'")
            
            current_y += self.text_line_height