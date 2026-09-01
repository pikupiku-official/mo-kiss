"""
メインアプリケーション - ビジュアルノベルゲーム

このファイルは起動、依存関係の配線、メインループだけを担当します。
画面ライフサイクル、ゲーム進行、OPTION、ウィンドウ処理は専用クラスへ委譲します。
"""

import warnings
import os
# 全ての警告を抑制してパフォーマンス向上
warnings.filterwarnings("ignore")
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

import sys
sys.path.append(os.path.dirname(__file__))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from core.config import *
from menu.main_menu import MainMenu
from menu.load_screen import LoadScreen, SaveSlotScreen
from map.map import FieldMap
from dialogue.dialogue_subsystem import DialogueSubsystem
from core.ui.title_subsystem import TitleSubsystem
from core.flow.event_progress import EventProgress
from core.flow.game_flow import (
    GameFlowController,
    Navigate,
    Scene,
    StartDialogue,
)
from core.flow.session_flow import SessionFlow
from core.ui.option_subsystem import (
    MOCK_AWAIT_FRAMES,
    OptionSubsystem,
)
from home.home import HomeModule
from core.services.save_manager import get_save_manager
from core.ui.loading_screen import show_loading, hide_loading
from core.flow.scene_manager import SceneManager
from core.runtime.window_controller import WindowController
from core.runtime.game_loop import GameLoop
import pygame


class GameApplication:
    def __init__(self):
        """ゲームアプリケーションの初期化"""
        self.scene_manager = SceneManager(initial_mode="menu")
        self.screen = None  # 仮想画面
        self.window_surface = None  # 実ウィンドウ
        self.virtual_screen = None  # 仮想画面（1440x1080）
        self.clock = None
        self.running = True
        self.window_controller = None

        # 各モードのインスタンス
        self.main_menu = None
        self.load_screen = None
        self.map_system = None
        self.home_module = None
        self.option_subsystem = None
        self.slot_screen = None
        self._option_snapshot = None
        self._option_notice = ""
        self._option_notice_until_ms = 0

        self.event_progress = EventProgress()
        self.game_flow = GameFlowController(
            self,
            event_progress=self.event_progress,
        )
        self.session_flow = self._create_session_flow()

        # 現在実行中のイベント情報を保持
        self.current_event_id = None
        # 通常イベントとは異なる、明示的な会話終了ルート（朝演出など）
        self.dialogue_completion_result = None

        print("🎮 ビジュアルノベルゲーム起動中...")

    @property
    def current_mode(self):
        return self.scene_manager.current_mode

    @current_mode.setter
    def current_mode(self, mode_name):
        if not hasattr(self, "scene_manager"):
            self.scene_manager = SceneManager(initial_mode=mode_name)
        else:
            self.scene_manager.current_mode = mode_name

    @property
    def current_subsystem(self):
        return self.scene_manager.current_subsystem

    @current_subsystem.setter
    def current_subsystem(self, subsystem):
        if not hasattr(self, "scene_manager"):
            self.scene_manager = SceneManager()
        self.scene_manager.current_subsystem = subsystem

    @property
    def current_overlay(self):
        """Compatibility view of the frontend owned by OptionSubsystem."""
        option_subsystem = getattr(self, "option_subsystem", None)
        return option_subsystem.overlay if option_subsystem else None

    @current_overlay.setter
    def current_overlay(self, overlay):
        if overlay is None:
            self.option_subsystem = None
        else:
            self.option_subsystem = OptionSubsystem(
                getattr(self, "screen", None),
                overlay,
            )

    def _get_game_flow(self):
        flow = getattr(self, "game_flow", None)
        if flow is None:
            event_progress = getattr(self, "event_progress", None) or EventProgress()
            self.event_progress = event_progress
            flow = GameFlowController(self, event_progress=event_progress)
            self.game_flow = flow
        return flow

    def _create_session_flow(self):
        return SessionFlow(
            self,
            save_manager_getter=lambda: get_save_manager(),
            dialogue_factory=lambda event_file: DialogueSubsystem(
                self.screen,
                self.virtual_screen,
                event_file,
            ),
            dialogue_type=DialogueSubsystem,
        )

    def _get_session_flow(self):
        flow = getattr(self, "session_flow", None)
        if flow is None:
            flow = self._create_session_flow()
            self.session_flow = flow
        return flow

    def _gather_normalized_events(self):
        """WindowControllerへの互換委譲（派生アプリが拡張している）。"""
        if getattr(self, "window_controller", None) is None:
            self.window_controller = WindowController(
                self.window_surface,
                self.virtual_screen,
            )
        events = self.window_controller.gather_normalized_events()
        self.window_surface = self.window_controller.window_surface
        return events

    def _queue_events_for_dialogue(self, events):
        for event in events:
            try:
                pygame.event.post(event)
            except Exception:
                pass

    def _present_virtual_screen(self):
        """WindowControllerへの互換委譲。"""
        if getattr(self, "window_controller", None) is None:
            self.window_controller = WindowController(
                self.window_surface,
                self.virtual_screen,
            )
        self.window_controller.present_virtual_screen()
        self.window_surface = self.window_controller.window_surface

    def initialize(self):
        """アプリケーションの初期化"""
        try:
            # Pygameの初期化
            pygame.init()
            pygame.mixer.init()

            # 実ウィンドウを作成
            self.window_surface = init_game()  # config.pyのinit_game()を使用
            # 仮想画面サーフェスを作成（1440x1080）
            self.virtual_screen = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT))
            self.screen = self.virtual_screen
            self.window_controller = WindowController(
                self.window_surface,
                self.virtual_screen,
            )
            from core.services.settings_manager import get_settings_manager
            self._set_fullscreen(get_settings_manager().get("fullscreen"))
            print(f"✓ 仮想画面作成: {VIRTUAL_WIDTH}x{VIRTUAL_HEIGHT}")

            self.clock = pygame.time.Clock()

            # ローディング画面表示
            show_loading("ゲームを初期化中...", self.window_surface)

            # メインメニューの初期化
            self.main_menu = MainMenu(
                self.screen,
                text_input_rect_transform=virtual_to_window_rect,
            )

            # ローディング画面を隠す
            hide_loading()

            # 初期サブシステムをタイトル画面に設定（フェーズ8）
            self.current_subsystem = TitleSubsystem(self.screen)
            self.current_mode = "title"
            self.current_subsystem.on_enter()  # BGM再生等の初期化処理（①修正）

            print("✅ アプリケーション初期化完了")
            return True
            
        except Exception as e:
            print(f"❌ アプリケーション初期化エラー: {e}")
            return False

    def mark_current_event_as_completed(self):
        """Compatibility delegate to the core event-progress service."""
        event_progress = getattr(self, "event_progress", None) or EventProgress()
        self.event_progress = event_progress
        if event_progress.record_completion(self.current_event_id):
            self.current_event_id = None

    def show_option(self):
        """OPTIONモーダルSubsystemを表示（BGM継続）。"""
        if self.option_subsystem is None:
            if self.current_subsystem:
                self.current_subsystem.render()
            self._option_snapshot = self.screen.copy()
            self.option_subsystem = OptionSubsystem.image_option(
                self.screen,
                fullscreen_callback=self._set_fullscreen,
            )
            print("[OPTION] オーバーレイ表示")

    def show_settings(self):
        """メインメニューからフェーダー設定を直接表示する。"""
        if self.option_subsystem is None:
            self.option_subsystem = OptionSubsystem.settings(
                self.screen,
                fullscreen_callback=self._set_fullscreen,
            )
            print("[SETTINGS] フェーダー設定表示")

    def show_mock_option(self):
        """モック用 OPTION アニメーションを表示"""
        if self.option_subsystem is None:
            self.option_subsystem = OptionSubsystem.image_option(
                self.screen,
                fullscreen_callback=self._set_fullscreen,
            )
            print("[OPTION] モックオーバーレイ表示")

    def _set_fullscreen(self, enabled: bool):
        if self.window_controller is not None:
            self.window_controller.set_fullscreen(enabled)
            self.window_surface = self.window_controller.window_surface

    def show_mock_await(self):
        """モック用 AWAIT アニメーションを表示"""
        if self.option_subsystem is None:
            self.option_subsystem = OptionSubsystem.await_sequence(self.screen)
            print("[AWAIT] モックオーバーレイ表示")

    def hide_option(self):
        """OPTIONオーバーレイを閉じる"""
        self.option_subsystem = None
        self.slot_screen = None
        self._option_snapshot = None
        print("[OPTION] オーバーレイ非表示")

    def show_slot_screen(self, mode: str):
        """Open the reusable manual-slot selector above OPTION."""
        self.slot_screen = SaveSlotScreen(
            self.screen,
            mode=mode,
            cancel_action="cancel_slot",
            save_callback=self._save_manual_slot if mode == "save" else None,
            load_callback=self._load_manual_slot if mode == "load" else None,
        )

    def _serialize_completion(self):
        return SessionFlow.serialize_completion(self.dialogue_completion_result)

    @staticmethod
    def _deserialize_completion(data):
        return SessionFlow.deserialize_completion(data)

    def _build_resume_state(self, mode=None):
        return self._get_session_flow().build_resume_state(mode)

    def _save_manual_slot(self, slot_name: str) -> bool:
        return self._get_session_flow().save_manual_slot(
            slot_name,
            thumbnail_surface=self._option_snapshot,
        )

    @staticmethod
    def _load_manual_slot(slot_name: str) -> bool:
        return get_save_manager().load_game(slot_name)

    def _handle_slot_result(self, result: str):
        if result == "cancel_slot":
            self.slot_screen = None
            return
        if result == "quit":
            self.running = False
            return
        if result.startswith("save_complete:"):
            slot_name = result.split(":", 1)[1]
            slot_number = slot_name.rsplit("_", 1)[-1]
            self.slot_screen = None
            self._option_notice = f"スロット{slot_number}に保存しました"
            self._option_notice_until_ms = pygame.time.get_ticks() + 1800
            return
        if result.startswith("load_complete:"):
            self.slot_screen = None
            self.option_subsystem = None
            self._option_snapshot = None
            self._get_game_flow().resume_loaded_game()

    def _render_option_notice(self):
        if not self._option_notice:
            return
        if pygame.time.get_ticks() >= self._option_notice_until_ms:
            self._option_notice = ""
            return
        font_path = os.path.join(
            os.path.dirname(__file__), "fonts", "MPLUS1p-Medium.ttf"
        )
        font = pygame.font.Font(font_path if os.path.exists(font_path) else None, 36)
        text = font.render(self._option_notice, True, (255, 255, 255))
        padding = 24
        rect = text.get_rect(center=(self.screen.get_width() // 2, 80))
        panel = rect.inflate(padding * 2, padding)
        pygame.draw.rect(self.screen, (20, 20, 28), panel, border_radius=8)
        pygame.draw.rect(self.screen, (210, 210, 235), panel, 2, border_radius=8)
        self.screen.blit(text, rect)

    def _handle_overlay_result(self, result: str):
        """Compatibility delegate for modal actions."""
        self._get_game_flow().handle_option_action(result)

    def _resume_loaded_game(self):
        """Compatibility delegate to GameFlowController."""
        self._get_game_flow().resume_loaded_game()

    def _poll_mock_overlay_shortcuts(self, events) -> bool:
        """Compatibility delegate for the explicit F6/F7 modal shortcuts."""
        if self.option_subsystem is not None:
            return self.option_subsystem.poll_mock_shortcuts(events)

        shortcut_key = None
        remaining_events = []
        for event in events:
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_F6, pygame.K_F7):
                shortcut_key = event.key
                continue
            remaining_events.append(event)
        events[:] = remaining_events
        if shortcut_key == pygame.K_F6:
            self.show_mock_option()
            return True
        if shortcut_key == pygame.K_F7:
            self.show_mock_await()
            return True
        return False

    def switch_to(self, subsystem, mode_name: str):
        """Compatibility delegate to the scene lifecycle manager."""
        self.scene_manager.switch_to(subsystem, mode_name)

    def _handle_transition(self, result: str):
        """Normalize legacy results and delegate routing to GameFlowController."""
        self._get_game_flow().handle(result)

    def switch_to_menu(self):
        """メインメニューモードに切り替え"""
        if not self.main_menu:
            self.main_menu = MainMenu(self.screen)
        self.switch_to(self.main_menu, "menu")

    def switch_to_load(self):
        """どの呼び出し元からも利用できるロード専用画面へ切り替える。"""
        if not self.load_screen:
            self.load_screen = LoadScreen(self.screen)
        self.switch_to(self.load_screen, "load")

    def reload_game_systems(self):
        """ゲームシステムを再初期化（ロード後に使用）"""
        try:
            show_loading("ゲームシステムを再初期化中...", self.window_surface)
            
            # マップシステムを再初期化
            print("[RELOAD] マップシステムを再初期化中...")
            self.map_system = None  # 既存のインスタンスを削除
            
            # 家モジュールも再初期化
            print("[RELOAD] 家モジュールを再初期化中...")
            self.home_module = None  # 既存のインスタンスを削除
            
            hide_loading()
            print("[RELOAD] ゲームシステム再初期化完了")
        except Exception as e:
            hide_loading()
            print(f"[RELOAD] ゲームシステム再初期化エラー: {e}")

    def _reload_game_systems(self):
        """Compatibility delegate for older callers."""
        return self.reload_game_systems()
    
    def switch_to_map(self):
        """マップモードに切り替え"""
        if not self.map_system:
            try:
                show_loading("マップを読み込み中...", self.window_surface)
                self.map_system = FieldMap(self.screen)
                hide_loading()
            except Exception as e:
                print(f"❌ マップシステム初期化エラー: {e}")
                hide_loading()
                self.switch_to_menu()
                return
        self._get_session_flow().autosave("map", "saveslot_auto")
        self.switch_to(self.map_system, "map")

    def switch_to_home(self):
        """家モジュールに切り替え"""
        if not self.home_module:
            try:
                show_loading("家を読み込み中...", self.window_surface)
                self.home_module = HomeModule(self.screen)
                hide_loading()
            except Exception as e:
                print(f"❌ 家モジュール初期化エラー: {e}")
                hide_loading()
                self.switch_to_menu()
                return
        self._get_session_flow().autosave("home", "saveslot_auto")
        self.switch_to(self.home_module, "home")

    def resume_loaded_state(self):
        """Compatibility delegate for restoring a loaded semantic snapshot."""
        self._get_session_flow().resume_loaded_state()
    
    def start_morning_dialogue(self):
        """Consume Home's explicit one-shot morning dialogue request."""
        home_module = (
            self.current_subsystem
            if isinstance(self.current_subsystem, HomeModule)
            else self.home_module
        )
        if home_module is not None:
            request = home_module._ensure_morning_flow().take_dialogue_request()
        else:
            request = StartDialogue(
                event_file=HomeModule.MORNING_DIALOGUE_FILE,
                completion=Navigate(Scene.MAP),
                display_loading=False,
            )
        self.start_dialogue(request)

    def switch_to_morning_dialogue(self):
        """Compatibility delegate for the isolated MorningFlow handoff."""
        self.start_morning_dialogue()

    def start_dialogue(self, request: StartDialogue):
        """Start a typed dialogue request, including explicit preloaded handoffs."""
        event_file = request.event_file
        print(f'💬 会話モードに切り替え: {event_file}')
        self.dialogue_completion_result = request.completion
        if event_file:
            self.current_event_id = os.path.splitext(os.path.basename(event_file))[0]

        if request.preloaded_subsystem is not None:
            self.switch_to(request.preloaded_subsystem, "dialogue")
            return

        try:
            if request.display_loading:
                show_loading('イベントを読み込み中...', self.window_surface)
            dialogue = DialogueSubsystem(self.screen, self.virtual_screen, event_file)
            if request.display_loading:
                hide_loading()
            self.switch_to(dialogue, 'dialogue')
        except Exception as e:
            print(f'❌ 会話モード初期化エラー: {e}')
            self.dialogue_completion_result = None
            if request.display_loading:
                hide_loading()
            self.switch_to_menu()

    def switch_to_dialogue(
        self,
        event_file=None,
        completion_result=None,
        display_loading=True,
    ):
        """Compatibility adapter from legacy arguments to StartDialogue."""
        self.start_dialogue(
            StartDialogue(
                event_file=event_file,
                completion=completion_result,
                display_loading=display_loading,
            )
        )

    def run(self):
        """初期化と終了処理の間のフレーム制御をGameLoopへ委譲する。"""
        if not self.initialize():
            return False

        print('🎯 メインゲームループ開始（タイトル → メインメニュー → ゲーム）')
        GameLoop(self, dialogue_type=DialogueSubsystem).run()

        self.cleanup()
        return True

    def cleanup(self):
        """終了処理"""
        print("🔄 アプリケーション終了処理中...")
        
        # ゲーム状態を初期化（セーブシステム用）
        save_manager = get_save_manager()
        if save_manager.reset_current_state():
            print("🎮 ゲーム状態を初期化しました")
        
        pygame.quit()
        print("✅ アプリケーション終了")

def main():
    """メイン関数"""
    app = GameApplication()
    success = app.run()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
