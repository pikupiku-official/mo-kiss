"""
subsystem_base.py - サブシステム基底クラス

全サブシステム（MainMenu / HomeModule / FieldMap / DialogueSubsystem 等）が
継承する抽象基底クラス。

統一インターフェース:
    handle_events(events) -> str | None  : イベント処理・遷移先を返す
    update()                             : ゲームロジック更新
    render()                             : 画面描画
    cleanup()                            : サブシステム終了時の処理（省略可）
    on_enter()                           : サブシステム開始時の処理（省略可）

参照: docs/サブシステムのクラス化計画.md
"""

from abc import ABC, abstractmethod
import pygame


class SubsystemBase(ABC):
    """全サブシステムの基底クラス"""

    def __init__(self, screen: pygame.Surface):
        self.screen = screen

    @abstractmethod
    def handle_events(self, events) -> str | None:
        """
        イベント処理

        Args:
            events: pygame.event.get() で取得したイベントリスト。
                    サブシステムによっては内部で pygame.event.get() を呼ぶため
                    この引数を無視する実装もある（例: MainMenu, DialogueSubsystem）。

        Returns:
            str | None: 遷移先を表す文字列（例: "go_to_map", "go_to_menu"）
                        遷移しない場合は None
        """
        pass

    @abstractmethod
    def update(self):
        """ゲームロジックの更新"""
        pass

    @abstractmethod
    def render(self):
        """画面描画"""
        pass

    def cleanup(self):
        """
        サブシステム終了時の処理（オーバーライド可能）

        例: BGM停止、座標系復元など。
        デフォルトは何もしない。
        """
        pass

    def on_enter(self):
        """
        サブシステム開始時の処理（オーバーライド可能）

        例: BGM再生、初期化など。
        デフォルトは何もしない。
        """
        pass
