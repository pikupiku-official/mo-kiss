"""
title_subsystem.py - TitleSubsystem

既存の TitleScreen クラスを SubsystemBase でラップする。

- handle_events(): 任意キー/クリック → "go_to_menu" / QUIT → "quit"
- on_enter(): BGM 再生
- cleanup(): BGM 停止
- update() / render(): TitleScreen に委譲

参照: docs/設計_システム.md  TITLE セクション
"""

import pygame
from subsystem_base import SubsystemBase
from title_screen import TitleScreen


class TitleSubsystem(SubsystemBase):
    """タイトル画面サブシステム（SubsystemBase ラッパー）"""

    def __init__(self, screen: pygame.Surface):
        super().__init__(screen)
        from config import DEBUG
        self._title = TitleScreen(screen, debug=DEBUG)

    # ─── SubsystemBase 実装 ───────────────────

    def handle_events(self, events=None) -> str | None:
        """任意キー/クリック → 'go_to_menu'、QUIT → 'quit'"""
        if events is None:
            events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                return "quit"
            if self._title.handle_input(event):
                return "go_to_menu"
        return None

    def update(self):
        self._title.update()

    def render(self):
        self._title.render()

    def on_enter(self):
        """BGM 再生"""
        self._play_bgm()

    def cleanup(self):
        """BGM 停止"""
        self._stop_bgm()

    # ─── BGM ヘルパー（テスト用にメソッド分離） ──

    def _play_bgm(self):
        try:
            self._title.play_title_bgm()
        except Exception as e:
            print(f"[TITLE] BGM 再生エラー: {e}")

    def _stop_bgm(self):
        try:
            self._title.stop_title_bgm()
        except Exception as e:
            print(f"[TITLE] BGM 停止エラー: {e}")
