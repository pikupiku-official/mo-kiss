"""
option_overlay.py - OptionOverlay

ポーズ画面（OPTIONオーバーレイ）。
switch_to() を使わずに current_overlay として管理するため、
現在サブシステムの cleanup() を呼ばず BGM を継続する。

parent_mode によってセーブ/ロードボタンの有効/無効を切り替える:
    "map" / "home" → save_enabled = True
    "dialogue" / "menu" / "title" → save_enabled = False  (設計書準拠)

戻り値:
    "resume"      → オーバーレイを閉じてゲームに戻る
    "go_to_menu"  → メインメニューへ
    "quit"        → ゲーム終了

参照: docs/設計_システム.md  OPTION（Overlay）セクション
"""

import pygame
from .path_utils import get_project_root
from .config import OFFSET_X, OFFSET_Y, CONTENT_WIDTH, CONTENT_HEIGHT, SCALE


_SAVE_MODES = {"map", "home"}


class OptionOverlay:
    """OPTIONポーズオーバーレイ"""

    def __init__(self, screen: pygame.Surface, parent_mode: str = "map"):
        self.screen = screen
        self.parent_mode = parent_mode
        self.save_enabled = parent_mode in _SAVE_MODES

        # フォント
        self._font = None
        self._init_font()

        # オーバーレイ背景
        self._bg_alpha = 160  # 半透明

    def _init_font(self):
        import os
        try:
            from core.path_utils import get_project_root
            font_path = os.path.join(get_project_root(), "fonts", "MPLUSRounded1c-Regular.ttf")
            if os.path.exists(font_path):
                self._font = pygame.font.Font(font_path, 36)
                return
        except Exception:
            pass
        self._font = pygame.font.SysFont("msgothic", 36)

    # ─── イベント処理 ────────────────────────

    def handle_events(self, events=None) -> str | None:
        if events is None:
            events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "resume"
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                result = self._handle_click(event.pos)
                if result:
                    return result
        return None

    def _handle_click(self, pos) -> str | None:
        for label, rect, action in self._get_buttons():
            if rect.collidepoint(pos):
                return action
        return None

    # ─── アクション ──────────────────────────

    def resume(self) -> str:
        return "resume"

    def go_to_menu(self) -> str:
        return "go_to_menu"

    # ─── 描画 ────────────────────────────────

    def render_overlay(self):
        """オーバーレイを現在のスクリーン上に描画"""
        from . import config
        # DialogueSubsystem.on_enter() が OFFSET_X/Y を 0 にリセットするため、
        # 常に DISPLAY サイズから実オフセットを再計算する
        cw = config.CONTENT_WIDTH
        ch = config.CONTENT_HEIGHT
        ox = (config.DISPLAY_WIDTH - cw) // 2
        oy = (config.DISPLAY_HEIGHT - ch) // 2

        # 半透明背景
        overlay_surf = pygame.Surface((cw, ch), pygame.SRCALPHA)
        overlay_surf.fill((0, 0, 0, self._bg_alpha))
        self.screen.blit(overlay_surf, (ox, oy))

        # タイトル
        title_surf = self._font.render("OPTION", True, (255, 255, 255))
        self.screen.blit(title_surf, (ox + cw // 2 - title_surf.get_width() // 2,
                                      oy + int(ch * 0.2)))

        # ボタン描画
        for label, rect, _ in self._get_buttons():
            color = (80, 80, 120)
            pygame.draw.rect(self.screen, color, rect, border_radius=8)
            pygame.draw.rect(self.screen, (180, 180, 220), rect, 2, border_radius=8)
            text = self._font.render(label, True, (240, 240, 240))
            self.screen.blit(text, (rect.centerx - text.get_width() // 2,
                                    rect.centery - text.get_height() // 2))

    def render(self):
        """SubsystemBase 互換エイリアス"""
        self.render_overlay()

    def _get_buttons(self):
        """ボタン定義リスト [(ラベル, Rect, アクション文字列)]"""
        from . import config
        # 同上: 実オフセットを再計算
        cw = config.CONTENT_WIDTH
        ch = config.CONTENT_HEIGHT
        ox = (config.DISPLAY_WIDTH - cw) // 2
        oy = (config.DISPLAY_HEIGHT - ch) // 2

        btn_w, btn_h = int(cw * 0.3), int(ch * 0.07)
        cx = ox + cw // 2 - btn_w // 2
        buttons = []

        y = oy + int(ch * 0.35)
        gap = int(ch * 0.11)

        buttons.append(("ゲームに戻る", pygame.Rect(cx, y, btn_w, btn_h), "resume"))
        y += gap

        if self.save_enabled:
            buttons.append(("セーブ", pygame.Rect(cx, y, btn_w, btn_h), "save"))
            y += gap
            buttons.append(("ロード", pygame.Rect(cx, y, btn_w, btn_h), "load"))
            y += gap

        buttons.append(("メインメニューへ", pygame.Rect(cx, y, btn_w, btn_h), "go_to_menu"))
        y += gap
        buttons.append(("ゲーム終了", pygame.Rect(cx, y, btn_w, btn_h), "quit"))

        return buttons
