"""
option_overlay.py - OPTION visual frontends

描画、画像アニメーション、ヒット領域など表示状態だけを提供する。
実行時の入力判断とモーダル状態は OptionSubsystem が管理する。
handle_events() は既存呼び出しとの互換用として残している。

parent_mode によってセーブ/ロードボタンの有効/無効を切り替える:
    "map" / "home" → save_enabled = True
    "dialogue" / "menu" / "title" → save_enabled = False  (設計書準拠)

戻り値:
    "resume"      → オーバーレイを閉じてゲームに戻る
    "go_to_menu"  → メインメニューへ
    "quit"        → ゲーム終了

参照: docs/設計_システム.md  OPTION（Overlay）セクション
"""

import os

import pygame
from core.path_utils import get_project_root


_SAVE_MODES = {"map", "home"}
_MOCK_FRAME_DURATION_MS = 100
_MOCK_CLOSE_FRAME_DURATION_MS = 50
_OPTION_OPEN_FRAME_DURATION_MS = 150
_OPTION_CLOSE_FRAME_DURATION_MS = 50
_OPTION_HIDDEN_PIXELS = (400, 200, 0)
_OPTION_MOVE_FRAME_DURATION_MS = 50
_OPTION_MOVE_Y_OFFSETS = (30, 0)
_OPTION_MIN_NUMBER = 1
_OPTION_MAX_NUMBER = 6
_OPTION_ACTIONS = {
    2: "go_to_menu",
    3: "save",
    4: "load",
    5: "return_to_morning",
}


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

    def action_at(self, pos) -> str | None:
        """Return the action represented at a point for the modal controller."""
        return self._handle_click(pos)

    # ─── アクション ──────────────────────────

    def resume(self) -> str:
        return "resume"

    def go_to_menu(self) -> str:
        return "go_to_menu"

    # ─── 描画 ────────────────────────────────

    def render_overlay(self):
        """オーバーレイを現在のスクリーン上に描画"""
        cw, ch = self.screen.get_size()
        ox = 0
        oy = 0

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
        cw, ch = self.screen.get_size()
        ox = 0
        oy = 0

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


class MockOptionOverlay:
    """モック用の画像シーケンスを表示するだけのオーバーレイ"""

    def __init__(self, screen: pygame.Surface, frame_names: tuple[str, str, str]):
        self.screen = screen
        self.frame_names = frame_names
        self._opened_at_ms = pygame.time.get_ticks()
        self._closing_started_at_ms = None
        self._frames = self._load_frames()

    def _load_frames(self) -> list[pygame.Surface]:
        frames = []
        ui_dir = os.path.join(get_project_root(), "images", "UI")
        for frame_name in self.frame_names:
            frame_path = os.path.join(ui_dir, frame_name)
            try:
                frames.append(pygame.image.load(frame_path).convert_alpha())
            except Exception:
                fallback = pygame.Surface(self.screen.get_size())
                fallback.fill((24, 24, 24))
                frames.append(fallback)
        return frames

    def handle_events(self, events=None) -> str | None:
        if events is None:
            events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                return "quit"
        if self._closing_started_at_ms is not None and self._is_close_animation_finished():
            return "resume"
        return None

    def start_close(self):
        if self._closing_started_at_ms is None:
            self._closing_started_at_ms = pygame.time.get_ticks()

    def start_close_if_elapsed(self, delay_ms: int) -> bool:
        """表示開始から指定時間が過ぎていれば閉じるアニメーションを始める。"""
        if self._closing_started_at_ms is not None:
            return False
        if pygame.time.get_ticks() - self._opened_at_ms < delay_ms:
            return False
        self.start_close()
        return True

    def is_same_sequence(self, frame_names: tuple[str, str, str]) -> bool:
        return self.frame_names == frame_names

    def render_overlay(self):
        cw, ch = self.screen.get_size()
        ox = 0
        oy = 0

        frame = self._get_current_frame()
        if frame.get_size() != (cw, ch):
            frame = pygame.transform.smoothscale(frame, (cw, ch))
        self.screen.blit(frame, (ox, oy))

    def render(self):
        self.render_overlay()

    def _get_current_frame(self) -> pygame.Surface:
        if self._closing_started_at_ms is not None:
            return self._get_closing_frame()

        elapsed_ms = max(0, pygame.time.get_ticks() - self._opened_at_ms)
        frame_index = min(elapsed_ms // _MOCK_FRAME_DURATION_MS, len(self._frames) - 1)
        return self._frames[frame_index]

    def _get_closing_frame(self) -> pygame.Surface:
        elapsed_ms = max(0, pygame.time.get_ticks() - self._closing_started_at_ms)
        close_index = min(elapsed_ms // _MOCK_CLOSE_FRAME_DURATION_MS, len(self._frames) - 1)
        frame_index = max(0, (len(self._frames) - 1) - close_index)
        return self._frames[frame_index]

    def _is_close_animation_finished(self) -> bool:
        elapsed_ms = max(0, pygame.time.get_ticks() - self._closing_started_at_ms)
        return elapsed_ms >= len(self._frames) * _MOCK_CLOSE_FRAME_DURATION_MS

    def is_close_animation_finished(self) -> bool:
        if self._closing_started_at_ms is None:
            return False
        return self._is_close_animation_finished()


class OptionImageOverlay:
    """1.png〜6.png を切り替えられる OPTION オーバーレイ。"""

    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.selected_number = _OPTION_MIN_NUMBER
        self._opened_at_ms = pygame.time.get_ticks()
        self._closing_started_at_ms = None
        self._move_started_at_ms = None
        self._images = self._load_images()
        self._scaled_images = {}

    def _load_images(self) -> dict[int, pygame.Surface]:
        images = {}
        option_dir = os.path.join(get_project_root(), "images", "UI", "option")
        for number in range(_OPTION_MIN_NUMBER, _OPTION_MAX_NUMBER + 1):
            image_path = os.path.join(option_dir, f"{number}.png")
            try:
                images[number] = pygame.image.load(image_path).convert_alpha()
            except Exception:
                images[number] = pygame.Surface((640, 602), pygame.SRCALPHA)
        return images

    def handle_events(self, events=None) -> str | None:
        if events is None:
            events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                return "quit"

        if self.is_move_animating and not self.finish_move_animation_if_elapsed():
            return None

        for event in events:
            if event.type != pygame.KEYDOWN or self._closing_started_at_ms is not None:
                continue
            if event.key == pygame.K_RIGHT:
                self.move_selection(1)
            elif event.key == pygame.K_DOWN:
                self.move_selection(2)
            elif event.key == pygame.K_LEFT:
                self.move_selection(-1)
            elif event.key == pygame.K_UP:
                self.move_selection(-2)
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                result = self.activate_selection()
                if result is not None:
                    return result

        if self._closing_started_at_ms is not None and self._is_close_animation_finished():
            return "resume"
        return None

    def _move_selection(self, amount: int):
        option_count = _OPTION_MAX_NUMBER - _OPTION_MIN_NUMBER + 1
        self.selected_number = (
            (self.selected_number - _OPTION_MIN_NUMBER + amount) % option_count
        ) + _OPTION_MIN_NUMBER

    def move_selection(self, amount: int):
        """Update visual selection state at the modal controller's request."""
        if self.is_move_animating or self.is_closing:
            return False
        self._move_selection(amount)
        self._move_started_at_ms = pygame.time.get_ticks()
        return True

    def activate_selection(self) -> str | None:
        """Return the selected action immediately when no move animation is active."""
        if self.is_move_animating or self.is_closing:
            return None
        if self.selected_number == 1:
            self.start_close()
            return None
        return _OPTION_ACTIONS.get(self.selected_number)

    def finish_move_animation_if_elapsed(self) -> bool:
        if not self.is_move_animating:
            return True
        elapsed_ms = max(
            0,
            pygame.time.get_ticks() - self._move_started_at_ms,
        )
        duration_ms = (
            len(_OPTION_MOVE_Y_OFFSETS) * _OPTION_MOVE_FRAME_DURATION_MS
        )
        if elapsed_ms < duration_ms:
            return False
        self._move_started_at_ms = None
        return True

    @property
    def is_move_animating(self) -> bool:
        return self._move_started_at_ms is not None

    @property
    def is_closing(self) -> bool:
        return self._closing_started_at_ms is not None

    def start_close(self):
        if self._closing_started_at_ms is None:
            self._closing_started_at_ms = pygame.time.get_ticks()

    def render_overlay(self):
        screen_width, screen_height = self.screen.get_size()
        image = self._get_scaled_image(self.selected_number, screen_width)
        hidden_pixels = self._get_hidden_pixels()
        move_offset_y = self._get_move_offset_y()
        self.screen.blit(
            image,
            (
                0,
                screen_height
                - image.get_height()
                + hidden_pixels
                + move_offset_y,
            ),
        )

    def render(self):
        self.render_overlay()

    def _get_scaled_image(self, number: int, screen_width: int) -> pygame.Surface:
        cache_key = (number, screen_width)
        if cache_key not in self._scaled_images:
            image = self._images[number]
            scale = screen_width / image.get_width()
            scaled_height = max(1, round(image.get_height() * scale))
            self._scaled_images[cache_key] = pygame.transform.smoothscale(
                image,
                (screen_width, scaled_height),
            )
        return self._scaled_images[cache_key]

    def _get_move_offset_y(self) -> int:
        if not self.is_move_animating:
            return 0
        elapsed_ms = max(
            0,
            pygame.time.get_ticks() - self._move_started_at_ms,
        )
        frame_index = min(
            elapsed_ms // _OPTION_MOVE_FRAME_DURATION_MS,
            len(_OPTION_MOVE_Y_OFFSETS) - 1,
        )
        return _OPTION_MOVE_Y_OFFSETS[frame_index]

    def _get_hidden_pixels(self) -> int:
        if self._closing_started_at_ms is not None:
            elapsed_ms = max(0, pygame.time.get_ticks() - self._closing_started_at_ms)
            frame_index = min(
                elapsed_ms // _OPTION_CLOSE_FRAME_DURATION_MS,
                len(_OPTION_HIDDEN_PIXELS) - 1,
            )
            return tuple(reversed(_OPTION_HIDDEN_PIXELS))[frame_index]

        elapsed_ms = max(0, pygame.time.get_ticks() - self._opened_at_ms)
        frame_index = min(
            elapsed_ms // _OPTION_OPEN_FRAME_DURATION_MS,
            len(_OPTION_HIDDEN_PIXELS) - 1,
        )
        return _OPTION_HIDDEN_PIXELS[frame_index]

    def _is_close_animation_finished(self) -> bool:
        elapsed_ms = max(0, pygame.time.get_ticks() - self._closing_started_at_ms)
        return elapsed_ms >= len(_OPTION_HIDDEN_PIXELS) * _OPTION_CLOSE_FRAME_DURATION_MS

    def is_close_animation_finished(self) -> bool:
        if self._closing_started_at_ms is None:
            return False
        return self._is_close_animation_finished()
