import pygame
from core.config import *
from .name_manager import get_name_manager
from .inline_markup import (
    parse_inline_markup, wrap_markup_text, has_inline_markup,
    PlainChar, RubySpan, BotenSpan,
)

# ルビ・傍点定数（config.py の TEXT_RENDERER_CONFIG から読み込む）
RUBY_FONT_RATIO = float(TEXT_RENDERER_CONFIG.get('ruby_font_ratio', 0.45))
RUBY_MARGIN_PX  = int(TEXT_RENDERER_CONFIG.get('ruby_margin_px', 2))

def _blit_ruby_justified(surface, ruby_text: str, render_fn, grid_x: int, span_width: int):
    """ルビ文字列を span_width 内に両端揃えで blit する。
    1文字のときは中央揃え。ルビ幅がスパン幅を超える場合は左詰め。"""
    chars = list(ruby_text)
    n = len(chars)
    surfs = [render_fn(ch) for ch in chars]
    total_w = sum(s.get_width() for s in surfs)

    if n == 1:
        rx = grid_x + (span_width - surfs[0].get_width()) // 2
        surface.blit(surfs[0], (rx, 0))
        return

    if total_w >= span_width:
        rx = float(grid_x)
        for s in surfs:
            surface.blit(s, (int(rx), 0))
            rx += s.get_width()
        return

    gap = (span_width - total_w) / (n - 1)
    rx = float(grid_x)
    for s in surfs:
        surface.blit(s, (int(rx), 0))
        rx += s.get_width() + gap

from PyQt5.QtGui import QFont, QImage, QPainter, QColor, QFontMetrics
from PyQt5.QtCore import QSize

# テキスト描画キャッシュ
_text_render_cache = {}

def render_text_with_qfont_cached(text, qfont, color):
    """PyQt5のQFontでテキストを描画し、PygameのSurfaceとして返す（キャッシュ付き）"""
    # キャッシュキーを作成
    cache_key = (text, qfont.family(), qfont.pointSize(), qfont.weight(), tuple(color))
    
    # キャッシュから取得を試行
    if cache_key in _text_render_cache:
        return _text_render_cache[cache_key]
    
    # 新しく描画
    surface = render_text_with_qfont(text, qfont, color)
    
    # キャッシュに保存（最大200個まで）
    if len(_text_render_cache) > 200:
        # 古いエントリを削除
        oldest_key = next(iter(_text_render_cache))
        del _text_render_cache[oldest_key]
    
    _text_render_cache[cache_key] = surface
    return surface

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
        
        # 名前管理システム
        self.name_manager = get_name_manager()
        
        # 仮想解像度基準のピクセル値設定（1920x1080基準）
        from core.config import VIRTUAL_WIDTH, VIRTUAL_HEIGHT, scale_pos, scale_size
        
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

        # フォントはtext_rendererよりも小さくする（バックログ用に調整）
        from PyQt5.QtGui import QFont, QFontMetrics
        
        # text_rendererから元のフォントサイズを取得し、0.7倍に縮小
        original_text_size = self.fonts["text"].pointSize()
        original_name_size = self.fonts["name"].pointSize()
        self.text_font_size = int(original_text_size * 0.7)
        self.name_font_size = int(original_name_size * 0.7)
        
        # 元のフォントファミリー名と設定を取得
        name_font_family = self.fonts["name"].family()
        text_font_family = self.fonts["text"].family()
        name_font_weight = self.fonts["name"].weight()
        text_font_weight = self.fonts["text"].weight()
        
        # バックログ用のフォントを作成（text_rendererと同じサイズ）
        self.backlog_name_font = QFont(name_font_family, self.name_font_size)
        self.backlog_name_font.setWeight(name_font_weight)
        self.backlog_text_font = QFont(text_font_family, self.text_font_size)  
        self.backlog_text_font.setWeight(text_font_weight)
        
        self.name_font_metrics = QFontMetrics(self.backlog_name_font)
        self.text_font_metrics = QFontMetrics(self.backlog_text_font)
        self.text_line_height = self.text_font_metrics.height()

        # ルビ・傍点用小フォント（text の RUBY_FONT_RATIO 倍サイズ）
        ruby_point_size = max(6, int(self.text_font_size * RUBY_FONT_RATIO))
        self.backlog_ruby_font = QFont(text_font_family, ruby_point_size)
        self.backlog_ruby_font.setWeight(text_font_weight)
        self.ruby_h = int(self.text_line_height * RUBY_FONT_RATIO) + RUBY_MARGIN_PX

        if self.debug:
            print(f"[BACKLOG] バックログ背景高さ: {self.height}px")
            print(f"[BACKLOG] フォントサイズ: {self.text_font_size}px")
            print(f"[BACKLOG] 行の高さ: {self.text_line_height}px")
        
    def get_character_colors(self, char_name, force_female=False):
        """キャラクター名に基づいて色を決定する（text_rendererと同じ）"""
        # 選択肢の場合は専用色を使用
        if char_name == "選択":
            return self.choice_color, self.choice_color

        if force_female:
            return self.female_name_color, self.female_text_color
        
        if char_name and char_name in CHARACTER_GENDERS:
            gender = CHARACTER_GENDERS.get(char_name)
            if gender == 'female':
                return self.female_name_color, self.female_text_color
        return self.default_name_color, self.default_text_color
        
    def _apply_surface_fx(self, surf):
        """FONT_EFFECTS（ピクセル化・横引き）を surface に適用する"""
        if not FONT_EFFECTS:
            return surf
        orig_w, orig_h = surf.get_size()
        stretch = (float(FONT_EFFECTS.get("stretch_factor", 1.0))
                   if FONT_EFFECTS.get("enable_stretched", False) else 1.0)
        final_w = max(1, int(round(orig_w * stretch)))
        if FONT_EFFECTS.get("enable_pixelated", False):
            pf = max(1.0, float(FONT_EFFECTS.get("pixelate_factor", 2)))
            sw = max(1, int(orig_w / pf))
            sh = max(1, int(orig_h / pf))
            small = pygame.transform.smoothscale(surf, (sw, sh))
            surf = pygame.transform.smoothscale(small, (final_w, orig_h))
        elif stretch != 1.0:
            surf = pygame.transform.smoothscale(surf, (final_w, orig_h))
        return surf.convert_alpha()

    def _render_with_fx(self, text, qfont, color):
        """QFont 描画 + FONT_EFFECTS（影・ピクセル化・横引き）を適用して Surface を返す"""
        text_surf = render_text_with_qfont_cached(text, qfont, color)
        text_surf = self._apply_surface_fx(text_surf)
        if FONT_EFFECTS and FONT_EFFECTS.get("enable_shadow", False):
            shadow_surf = render_text_with_qfont_cached(text, qfont, (0, 0, 0))
            shadow_surf = self._apply_surface_fx(shadow_surf)
            offx = int(round(FONT_EFFECTS.get("shadow_offset", (6, 6))[0]))
            offy = int(round(FONT_EFFECTS.get("shadow_offset", (6, 6))[1]))
            tw, th = text_surf.get_size()
            sw, sh = shadow_surf.get_size()
            combined = pygame.Surface((max(tw, sw + offx), max(th, sh + offy)), pygame.SRCALPHA)
            combined.blit(shadow_surf, (offx, offy))
            combined.blit(text_surf,   (0, 0))
            return combined.convert_alpha()
        return text_surf

    def _render_markup_line(self, text_line: str, color) -> 'pygame.Surface':
        """ルビ・傍点マークアップ対応の1行描画（PyQt5フォント版）"""
        if not text_line:
            return pygame.Surface((1, 1), pygame.SRCALPHA)

        tokens = parse_inline_markup(text_line)

        # グリッド幅（QFontMetrics 基準）
        from PyQt5.QtGui import QFontMetrics
        metrics = QFontMetrics(self.backlog_text_font)
        grid_w = metrics.horizontalAdvance("あ") + 1

        base_h = self.text_line_height
        line_height = base_h + self.ruby_h + 4

        total_base = sum(
            len(t.base) if isinstance(t, (RubySpan, BotenSpan)) else 1
            for t in tokens
        )
        line_width = max(1, grid_w * total_base)
        surf = pygame.Surface((line_width, line_height), pygame.SRCALPHA)
        surf.fill((0, 0, 0, 0))

        char_count = 0
        for token in tokens:
            if isinstance(token, PlainChar):
                gx = char_count * grid_w
                cs = self._render_with_fx(token.char, self.backlog_text_font, color)
                surf.blit(cs, (gx, self.ruby_h))
                char_count += 1
            elif isinstance(token, RubySpan):
                span_w = grid_w * len(token.base)
                gx = char_count * grid_w
                for i, ch in enumerate(token.base):
                    cs = render_text_with_qfont_cached(ch, self.backlog_text_font, color)
                    surf.blit(cs, (gx + i * grid_w, self.ruby_h))
                _blit_ruby_justified(surf, token.ruby,
                    lambda ch: self._render_with_fx(ch, self.backlog_ruby_font, color),
                    gx, span_w)
                char_count += len(token.base)
            elif isinstance(token, BotenSpan):
                gx = char_count * grid_w
                for i, ch in enumerate(token.base):
                    cs = render_text_with_qfont_cached(ch, self.backlog_text_font, color)
                    surf.blit(cs, (gx + i * grid_w, self.ruby_h))
                    dot = self._render_with_fx("·", self.backlog_ruby_font, color)
                    dx = gx + i * grid_w + (grid_w - dot.get_width()) // 2
                    surf.blit(dot, (dx, 0))
                char_count += len(token.base)

        return surf

    def add_entry(self, speaker, text, force_female=False):
        """バックログにエントリを追加"""
        if not text or text.strip() == "":
            return
        
        # 変数置換を適用
        substituted_speaker = self.name_manager.substitute_variables(speaker) if speaker else speaker
        substituted_text = self.name_manager.substitute_variables(text) if text else text
            
        # 重複チェック（最後のエントリと同じ場合はスキップ）
        if (self.entries and
            self.entries[-1]["speaker"] == substituted_speaker and
            self.entries[-1]["text"] == substituted_text and
            bool(self.entries[-1].get("force_female")) == bool(force_female)):
            return
            
        self.entries.append({
            "speaker": substituted_speaker or "名無し",
            "text": substituted_text,
            "force_female": bool(force_female),
        })
        
        # デバッグ出力を削除（パフォーマンス向上）
    
    def _wrap_text(self, text, max_chars=26):
        """マークアップ対応折り返し"""
        return wrap_markup_text(text, max_chars)
    
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
                # ESC はバックログを閉じない（OPTION オーバーレイに委譲）
        
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
        previous_force_female = None
        
        for entry in self.entries:
            speaker = entry["speaker"]
            text = entry["text"]
            text_lines = self._wrap_text(text, 26)
            
            # 話者が変更された場合のみ話者名を表示
            force_female = bool(entry.get("force_female", False))
            show_speaker = (
                speaker != previous_speaker or force_female != previous_force_female
            )
            
            # 各エントリの行情報を作成
            for i, line in enumerate(text_lines):
                all_lines.append({
                    "type": "text",
                    "speaker": speaker if (i == 0 and show_speaker) else "",  # 話者変更時の最初の行のみ話者名
                    "text": line,
                    "entry": entry
                })
            
            previous_speaker = speaker
            previous_force_female = force_female
        
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
            name_color, text_color = self.get_character_colors(
                entry["speaker"], entry.get("force_female", False)
            )
            
            # 話者名を描画（最初の行のみ）
            if speaker and speaker.strip():
                try:
                    name_surface = render_text_with_qfont_cached(speaker, self.backlog_name_font, name_color)
                    self.screen.blit(name_surface, (self.x + self.padding, current_y))
                except Exception as e:
                    if self.debug:
                        print(f"話者名描画エラー: {e}, 名前: '{speaker}'")
            
            # テキストを描画（話者名と同じ高さ）
            text_x = self.x + self.padding + self.speaker_width + 60
            if text_line.strip():
                try:
                    if has_inline_markup(text_line):
                        # ルビ・傍点あり: 1文字ずつトークン描画
                        # base text はサーフェス内 ruby_h 下にあるので上シフトして Y を固定
                        text_surface = self._render_markup_line(text_line, text_color)
                        self.screen.blit(text_surface, (text_x, current_y - self.ruby_h))
                    else:
                        # 平文: QFont 一括描画 + FONT_EFFECTS 適用
                        text_surface = self._render_with_fx(
                            text_line, self.backlog_text_font, text_color
                        )
                        self.screen.blit(text_surface, (text_x, current_y))
                except Exception as e:
                    if self.debug:
                        print(f"テキスト描画エラー: {e}, テキスト: '{text_line}'")
            
            current_y += self.text_line_height
