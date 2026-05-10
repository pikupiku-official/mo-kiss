"""
dialogue_subsystem.py - DialogueSubsystem ラッパークラス

SubsystemBase を継承し、既存の dialogue システム（game_state 辞書 + controller2）を
統一ライフサイクルインターフェースでラップする。

追加問題A対応:
    handle_events(events) は events 引数を無視する。
    内部で controller2.handle_events() が pygame.event.get() を直接呼ぶため。

追加問題B対応:
    on_enter()  : config.OFFSET_X/Y/SCALE を退避し 0/0/1.0 にリセット
    cleanup()   : BGM/SE 停止 + config 値を復元

参照: docs/サブシステムのクラス化計画.md フェーズ3
"""

import os
import pygame

from subsystem_base import SubsystemBase
from dialogue.model import initialize_game as _init_game
from dialogue.model import advance_dialogue


class DialogueSubsystem(SubsystemBase):
    """dialogue システムの SubsystemBase ラッパー"""

    def __init__(self, screen: pygame.Surface, virtual_screen: pygame.Surface,
                 event_file: str | None = None):
        """
        Args:
            screen:         実画面（フルスクリーン）
            virtual_screen: 仮想画面（1440x1080）。dialogue はここに描画する
            event_file:     読み込む .ks ファイルパス（省略可）
        """
        super().__init__(screen)
        self.virtual_screen = virtual_screen

        # 座標系の退避先（on_enter() で設定、None = 未設定）
        self._saved_offset_x: float | None = None
        self._saved_offset_y: float | None = None
        self._saved_scale:    float | None = None

        # イベントID（events/E001.ks → "E001"）
        self.current_event_id: str | None = None
        if event_file:
            self.current_event_id = os.path.splitext(os.path.basename(event_file))[0]

        # game_state を初期化
        self.game_state = _init_game()

        # 全レンダラーの screen を仮想画面に差し替え
        self._swap_to_virtual_screen()

        # イベントファイルを読み込む
        if event_file:
            self._load_event_file(event_file)

    # ─────────────────────────────────────────────
    # SubsystemBase 実装
    # ─────────────────────────────────────────────

    def on_enter(self):
        """サブシステム開始時: 座標系を仮想画面モードにリセットし元値を退避"""
        import config
        self._saved_offset_x = config.OFFSET_X
        self._saved_offset_y = config.OFFSET_Y
        self._saved_scale    = config.SCALE

        config.OFFSET_X = 0
        config.OFFSET_Y = 0
        config.SCALE    = 1.0
        print("✓ DialogueSubsystem on_enter: 座標系をリセット "
              f"(退避 OFFSET=({self._saved_offset_x},{self._saved_offset_y}) "
              f"SCALE={self._saved_scale})")

    def cleanup(self):
        """サブシステム終了時: BGM/SE 停止 + 座標系を復元"""
        # BGM / SE 停止
        try:
            if self.game_state.get('bgm_manager'):
                self.game_state['bgm_manager'].stop_bgm()
            if self.game_state.get('se_manager'):
                self.game_state['se_manager'].stop_all_se()
            print("🔇 DialogueSubsystem cleanup: BGM/SE 停止")
        except Exception as e:
            print(f"⚠️ DialogueSubsystem cleanup 音声停止エラー: {e}")

        # 座標系を復元（on_enter() が呼ばれていない場合は何もしない）
        if self._saved_offset_x is not None:
            import config
            config.OFFSET_X = self._saved_offset_x
            config.OFFSET_Y = self._saved_offset_y
            config.SCALE    = self._saved_scale
            print(f"✓ DialogueSubsystem cleanup: 座標系を復元 "
                  f"OFFSET=({config.OFFSET_X},{config.OFFSET_Y}) SCALE={config.SCALE}")
            # 復元後にリセット（二重復元防止）
            self._saved_offset_x = None
            self._saved_offset_y = None
            self._saved_scale    = None

    def handle_events(self, events=None) -> str | None:
        """
        イベント処理（追加問題A対応）

        events 引数は無視する。
        controller2.handle_events() が内部で pygame.event.get() を呼ぶため。

        Returns:
            "dialogue_ended" : KS ファイルが終了した
            None             : 会話継続中
        """
        from dialogue.controller2 import handle_events as _ctrl_events

        try:
            continue_dialogue = _ctrl_events(self.game_state, self.screen)
        except Exception as e:
            print(f"⚠️ DialogueSubsystem handle_events エラー: {e}")
            return "dialogue_ended"

        if not continue_dialogue:
            return "dialogue_ended"
        return None

    def update(self):
        """ゲームロジック更新"""
        from dialogue.controller2 import update_game
        from dialogue.model import update_background_animation
        from dialogue.character_manager import update_character_animations

        try:
            update_game(self.game_state)
            update_background_animation(self.game_state)
            update_character_animations(self.game_state)
        except Exception as e:
            print(f"⚠️ DialogueSubsystem update エラー: {e}")

    def render(self):
        """画面描画: 仮想画面に描画してフルスクリーンにスケーリング転送"""
        from dialogue.background_manager import draw_background
        from dialogue.character_manager import draw_characters
        from dialogue.fade_manager import draw_fade_overlay
        from dialogue.controller2 import draw_input_blocked_notice
        from config import CONTENT_WIDTH, CONTENT_HEIGHT, OFFSET_X, OFFSET_Y

        gs = self.game_state

        # 仮想画面クリア
        self.virtual_screen.fill((0, 0, 0))

        # 背景・キャラクター・フェード
        draw_background(gs)
        draw_characters(gs)
        draw_fade_overlay(gs)

        # UI エレメント（テキストボックス等）
        if 'image_manager' in gs and 'images' in gs:
            gs['image_manager'].draw_ui_elements(
                self.virtual_screen, gs['images'], gs.get('show_text', True)
            )

        # 選択肢 / テキスト
        choice_showing = False
        if 'choice_renderer' in gs:
            choice_showing = gs['choice_renderer'].is_choice_showing()

        if not choice_showing and 'text_renderer' in gs:
            gs['text_renderer'].render_text_window(gs)

        if choice_showing:
            gs['choice_renderer'].render()

        # バックログ・通知（最上位レイヤー）
        if 'backlog_manager' in gs:
            gs['backlog_manager'].render()
        if 'notification_manager' in gs:
            gs['notification_manager'].render()

        draw_input_blocked_notice(gs, self.virtual_screen)

        # 仮想画面をフルスクリーンにスケーリングして転送
        # on_enter()でOFFSET_X=0にリセットしているが、スクリーンへの
        # blit位置は元のOFFSET（中央寄せ用）を使う必要がある。
        # 旧main.pyは "from config import *" の初回バインド値（=元OFFSET）を
        # 使っていたため偶然正しく動いていた。
        blit_x = self._saved_offset_x if self._saved_offset_x is not None else OFFSET_X
        blit_y = self._saved_offset_y if self._saved_offset_y is not None else OFFSET_Y
        try:
            scaled = pygame.transform.smoothscale(
                self.virtual_screen, (CONTENT_WIDTH, CONTENT_HEIGHT)
            )
            self.screen.blit(scaled, (blit_x, blit_y))
        except Exception as e:
            print(f"⚠️ DialogueSubsystem render スケーリングエラー: {e}")

    # ─────────────────────────────────────────────
    # 内部ヘルパー
    # ─────────────────────────────────────────────

    def _swap_to_virtual_screen(self):
        """game_state 内の全レンダラーの screen を virtual_screen に差し替える"""
        gs = self.game_state
        if not gs:
            return

        gs['screen'] = self.virtual_screen

        for key in ('text_renderer', 'choice_renderer', 'backlog_manager', 'notification_manager'):
            if key in gs and hasattr(gs[key], 'screen'):
                gs[key].screen = self.virtual_screen

        print(f"✓ DialogueSubsystem: 仮想画面に差し替え完了")

    def _load_event_file(self, event_file: str):
        """イベントファイル（.ks）を読み込んで game_state に設定する"""
        from dialogue.dialogue_loader import DialogueLoader
        from dialogue.data_normalizer import normalize_dialogue_data

        try:
            loader = DialogueLoader()
            raw = loader.load_dialogue_from_ks(event_file)
            if not raw:
                print(f"⚠️ DialogueSubsystem: イベントファイル読み込み失敗: {event_file}")
                return

            data = normalize_dialogue_data(raw)
            if not data:
                print(f"⚠️ DialogueSubsystem: データ正規化失敗: {event_file}")
                return

            self.game_state['dialogue_data'] = data
            self.game_state['current_paragraph'] = -1
            advance_dialogue(self.game_state)
            print(f"✅ DialogueSubsystem: イベント読み込み完了: {event_file} "
                  f"({len(data)} 段落)")

        except Exception as e:
            print(f"⚠️ DialogueSubsystem: イベントファイル読み込みエラー: {e}")
