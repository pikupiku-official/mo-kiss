"""
メインアプリケーション - ビジュアルノベルゲーム

このファイルはアプリケーション全体の制御を行います：
- メインメニュー
- マップシステム  
- 会話パート
の3つのモードを統括します。
"""

import warnings
import os
# 全ての警告を抑制してパフォーマンス向上
warnings.filterwarnings("ignore")
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

import sys
sys.path.append(os.path.dirname(__file__))

from config import *
from menu.main_menu import MainMenu
from map.map import FieldMap
from dialogue.model import initialize_game as init_dialogue_game
from title_screen import show_title_screen
from time_manager import get_time_manager
from home.home import HomeModule
from save_manager import get_save_manager
from loading_screen import show_loading, hide_loading
import pygame

class GameApplication:
    def __init__(self):
        """ゲームアプリケーションの初期化"""
        self.current_mode = "menu"  # "menu", "map", "dialogue"
        self.screen = None  # 実画面（フルスクリーン）
        self.virtual_screen = None  # 仮想画面（1440x1080）
        self.clock = None
        self.running = True

        # 各モードのインスタンス
        self.main_menu = None
        self.map_system = None
        self.dialogue_game_state = None
        self.home_module = None

        # 現在実行中のイベント情報を保持
        self.current_event_id = None

        print("🎮 ビジュアルノベルゲーム起動中...")

    def initialize(self):
        """アプリケーションの初期化"""
        try:
            # Pygameの初期化
            pygame.init()
            pygame.mixer.init()

            # 実画面設定（フルスクリーン）
            self.screen = init_game()  # config.pyのinit_game()を使用

            # 仮想画面サーフェスを作成（1440x1080）
            self.virtual_screen = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT))
            print(f"✓ 仮想画面作成: {VIRTUAL_WIDTH}x{VIRTUAL_HEIGHT}")

            self.clock = pygame.time.Clock()

            # ローディング画面表示
            show_loading("ゲームを初期化中...", self.screen)

            # メインメニューの初期化
            self.main_menu = MainMenu(self.screen)

            # ローディング画面を隠す
            hide_loading()

            print("✅ アプリケーション初期化完了")
            return True
            
        except Exception as e:
            print(f"❌ アプリケーション初期化エラー: {e}")
            return False

    def mark_current_event_as_completed(self):
        """現在のイベントをcompleted_events.csvに記録（実行回数管理）"""
        if not self.current_event_id:
            print("[EVENT] 現在のイベントIDが設定されていません")
            return
        
        try:
            import csv
            import os
            from datetime import datetime
            
            # events.csvから該当イベント情報を取得
            events_csv_path = os.path.join(os.path.dirname(__file__), "events", "events.csv")
            completed_events_csv_path = os.path.join(os.path.dirname(__file__), "data", "current_state", "completed_events.csv")
            
            event_info = None
            
            # events.csvから該当イベントを検索
            if os.path.exists(events_csv_path):
                with open(events_csv_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if row['イベントID'] == self.current_event_id:
                            event_info = row
                            break
            
            if not event_info:
                print(f"[EVENT] events.csvに{self.current_event_id}が見つかりません")
                return
            
            # completed_events.csvの全データを読み込み（全イベント保持）
            all_events = []
            file_exists = os.path.exists(completed_events_csv_path)
            event_found = False
            
            if file_exists:
                with open(completed_events_csv_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        # 不要なフィールドを削除（古いデータからの移行）
                        for field in ['ヒロイン名', '場所', 'イベントタイトル']:
                            row.pop(field, None)
                        # 有効フラグがない場合はTRUEで設定
                        if '有効フラグ' not in row:
                            row['有効フラグ'] = 'TRUE'
                            
                        if row['イベントID'] == self.current_event_id:
                            # 該当イベントの実行回数を+1
                            current_count = int(row.get('実行回数', '0'))
                            row['実行回数'] = str(current_count + 1)
                            # ゲーム内時間で更新
                            time_manager = get_time_manager()
                            row['実行日時'] = time_manager.get_full_time_string()
                            event_found = True
                            print(f"[EVENT] {self.current_event_id}の実行回数を{current_count + 1}に更新")
                        
                        all_events.append(row)
            
            # 新しいイベントの場合は追加
            if not event_found:
                # ゲーム内時間を取得
                time_manager = get_time_manager()
                game_time_str = time_manager.get_full_time_string()
                
                new_event = {
                    'イベントID': self.current_event_id,
                    '実行日時': game_time_str,
                    '実行回数': '1',
                    '有効フラグ': 'TRUE'  # 実行時点では有効
                }
                all_events.append(new_event)
                print(f"[EVENT] {self.current_event_id}を新規記録（実行回数: 1）")
            
            # ファイルに書き戻し（全イベントデータ保持）
            fieldnames = ['イベントID', '実行日時', '実行回数', '有効フラグ']
            with open(completed_events_csv_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(all_events)
            
            # イベントID をリセット
            self.current_event_id = None
            
        except Exception as e:
            print(f"[EVENT] イベント完了記録エラー: {e}")

    def switch_to_menu(self):
        """メインメニューモードに切り替え"""
        print("📱 メインメニューモードに切り替え")

        # dialogueモードから遷移する場合、全ての音を停止 + 座標系を元に戻す
        if self.current_mode == "dialogue" and self.dialogue_game_state:
            try:
                self.dialogue_game_state['bgm_manager'].stop_bgm()
                self.dialogue_game_state['se_manager'].stop_all_se()
                print("🔇 dialogue終了: BGMとSEを停止しました")
            except Exception as e:
                print(f"⚠️ 音声停止エラー: {e}")

            # 座標系を元に戻す
            if '_original_scale' in self.dialogue_game_state:
                import config
                config.OFFSET_X = self.dialogue_game_state['_original_offset_x']
                config.OFFSET_Y = self.dialogue_game_state['_original_offset_y']
                config.SCALE = self.dialogue_game_state['_original_scale']
                print(f"✓ 座標系を元に戻しました")

        # mapモードから遷移する場合、BGMを停止
        if self.current_mode == "map" and self.map_system:
            try:
                self.map_system.bgm_manager.stop_bgm()
                print("🔇 map終了: BGMを停止しました")
            except Exception as e:
                print(f"⚠️ 音声停止エラー: {e}")

        self.current_mode = "menu"
        if not self.main_menu:
            self.main_menu = MainMenu(self.screen)

    def _reload_game_systems(self):
        """ゲームシステムを再初期化（ロード後に使用）"""
        try:
            show_loading("ゲームシステムを再初期化中...", self.screen)
            
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
    
    def switch_to_map(self):
        """マップモードに切り替え"""
        print("🗺️ マップモードに切り替え")

        # dialogueモードから遷移する場合、全ての音を停止 + 座標系を元に戻す
        if self.current_mode == "dialogue" and self.dialogue_game_state:
            try:
                self.dialogue_game_state['bgm_manager'].stop_bgm()
                self.dialogue_game_state['se_manager'].stop_all_se()
                print("🔇 dialogue終了: BGMとSEを停止しました")
            except Exception as e:
                print(f"⚠️ 音声停止エラー: {e}")

            # 座標系を元に戻す
            if '_original_scale' in self.dialogue_game_state:
                import config
                config.OFFSET_X = self.dialogue_game_state['_original_offset_x']
                config.OFFSET_Y = self.dialogue_game_state['_original_offset_y']
                config.SCALE = self.dialogue_game_state['_original_scale']
                print(f"✓ 座標系を元に戻しました")

        self.current_mode = "map"
        if not self.map_system:
            try:
                show_loading("マップを読み込み中...", self.screen)
                self.map_system = FieldMap(self.screen)
                hide_loading()
            except Exception as e:
                print(f"❌ マップシステム初期化エラー: {e}")
                hide_loading()
                self.switch_to_menu()

    def switch_to_home(self):
        """家モジュールに切り替え"""
        print("🏠 家モジュールに切り替え")

        # dialogueモードから遷移する場合、全ての音を停止
        if self.current_mode == "dialogue" and self.dialogue_game_state:
            try:
                self.dialogue_game_state['bgm_manager'].stop_bgm()
                self.dialogue_game_state['se_manager'].stop_all_se()
                print("🔇 dialogue終了: BGMとSEを停止しました")
            except Exception as e:
                print(f"⚠️ 音声停止エラー: {e}")

        # mapモードから遷移する場合、BGMを停止
        if self.current_mode == "map" and self.map_system:
            try:
                self.map_system.bgm_manager.stop_bgm()
                print("🔇 map終了: BGMを停止しました")
            except Exception as e:
                print(f"⚠️ 音声停止エラー: {e}")

        self.current_mode = "home"
        if not self.home_module:
            try:
                show_loading("家を読み込み中...", self.screen)
                self.home_module = HomeModule(self.screen)
                hide_loading()
            except Exception as e:
                print(f"❌ 家モジュール初期化エラー: {e}")
                hide_loading()
                self.switch_to_menu()
    
    def switch_to_dialogue(self, event_file=None):
        """会話モードに切り替え"""
        print(f"💬 会話モードに切り替え (イベント: {event_file})")

        # mapモードから遷移する場合、BGMを停止
        if self.current_mode == "map" and self.map_system:
            try:
                self.map_system.bgm_manager.stop_bgm()
                print("🔇 map終了: BGMを停止しました")
            except Exception as e:
                print(f"⚠️ 音声停止エラー: {e}")

        self.current_mode = "dialogue"

        # イベントIDを抽出（events/E001.ks -> E001）
        if event_file:
            import os
            self.current_event_id = os.path.splitext(os.path.basename(event_file))[0]
            print(f"[EVENT] 開始イベントID: {self.current_event_id}")

        try:
            # ローディング画面表示
            show_loading("イベントを読み込み中...", self.screen)

            # ★dialogue用に座標系を仮想画面モードに切り替え★
            # scale_pos()が仮想座標をそのまま返すように設定
            import config
            original_offset_x = config.OFFSET_X
            original_offset_y = config.OFFSET_Y
            original_scale = config.SCALE
            config.OFFSET_X = 0
            config.OFFSET_Y = 0
            config.SCALE = 1.0
            print(f"✓ 仮想画面モード: OFFSET=0, SCALE=1.0")

            # 会話ゲームの初期化（仮想画面を使用）
            self.dialogue_game_state = init_dialogue_game()

            # game_state['screen']を仮想画面に差し替え
            if self.dialogue_game_state:
                self.dialogue_game_state['screen'] = self.virtual_screen
                # 各レンダラーのスクリーンも仮想画面に差し替え
                if 'text_renderer' in self.dialogue_game_state:
                    self.dialogue_game_state['text_renderer'].screen = self.virtual_screen
                if 'choice_renderer' in self.dialogue_game_state:
                    self.dialogue_game_state['choice_renderer'].screen = self.virtual_screen
                if 'backlog_manager' in self.dialogue_game_state:
                    self.dialogue_game_state['backlog_manager'].screen = self.virtual_screen
                if 'notification_manager' in self.dialogue_game_state:
                    self.dialogue_game_state['notification_manager'].screen = self.virtual_screen

                # 元の設定を保存（他のモードで使用）
                self.dialogue_game_state['_original_offset_x'] = original_offset_x
                self.dialogue_game_state['_original_offset_y'] = original_offset_y
                self.dialogue_game_state['_original_scale'] = original_scale

                print(f"✓ dialogue用に仮想画面を設定: {VIRTUAL_WIDTH}x{VIRTUAL_HEIGHT}")
            if not self.dialogue_game_state:
                hide_loading()
                print("❌ 会話ゲーム初期化失敗")
                self.switch_to_menu()
                return
                
            # 指定されたイベントファイルがあれば読み込み
            if event_file:
                from dialogue.dialogue_loader import DialogueLoader
                from dialogue.data_normalizer import normalize_dialogue_data
                
                dialogue_loader = DialogueLoader()
                raw_dialogue_data = dialogue_loader.load_dialogue_from_ks(event_file)
                if raw_dialogue_data:
                    dialogue_data = normalize_dialogue_data(raw_dialogue_data)
                    if dialogue_data:
                        self.dialogue_game_state['dialogue_data'] = dialogue_data
                        self.dialogue_game_state['current_paragraph'] = -1
                        # 最初の会話データを表示
                        from dialogue.model import advance_dialogue
                        advance_dialogue(self.dialogue_game_state)
                        print(f"✅ イベントファイル読み込み完了: {event_file}")
                    else:
                        print("❌ ダイアログデータの正規化に失敗")
                        hide_loading()
                        self.switch_to_menu()
                        return
                else:
                    print("❌ イベントファイルの読み込みに失敗")
                    hide_loading()
                    self.switch_to_menu()
                    return
            
            # ローディング画面を隠す
            hide_loading()
                
        except Exception as e:
            print(f"❌ 会話モード初期化エラー: {e}")
            hide_loading()
            self.switch_to_menu()

    def handle_menu_events(self, events):
        """メインメニューのイベント処理"""
        for event in events:
            if event.type == pygame.QUIT:
                self.running = False
                return
            
            result = self.main_menu.handle_event(event)
            
            if result == "new_game":
                # 新規ゲーム：E001イベント開始
                print("[NEW_GAME] E001イベントを開始")
                self.switch_to_dialogue("events/E001.ks")
            elif result == "continue_game":
                # ゲーム続行：ロード完了後にマップシステムを再初期化
                print("[CONTINUE] ロード完了 - システムを再初期化中...")
                self._reload_game_systems()
                
                # 時間帯に応じて遷移先を決定
                time_manager = get_time_manager()
                current_period = time_manager.get_current_period()
                print(f"[CONTINUE] ロード完了後の時間帯: {current_period}")
                
                if current_period == "夜":
                    # 夜の場合は家に遷移
                    print(f"[CONTINUE] 夜のため家モジュールに遷移")
                    self.switch_to_home()
                elif current_period in ["朝", "昼", "放課後"]:
                    # 朝・昼・放課後の場合はマップに遷移
                    print(f"[CONTINUE] {current_period}のためマップモジュールに遷移")
                    self.switch_to_map()
                else:
                    # 予期しない時間帯の場合はマップに遷移
                    print(f"[CONTINUE] 予期しない時間帯({current_period})のためマップモジュールに遷移")
                    self.switch_to_map()
            elif result == "dialogue_test":
                self.switch_to_dialogue("events/E004.ks")
            elif result == "go_to_home":
                self.switch_to_home()
            elif result == "quit":
                self.running = False

    def handle_map_events(self, events):
        """マップモードのイベント処理"""
        for event in events:
            if event.type == pygame.QUIT:
                self.running = False
                return
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.switch_to_menu()
                    return
            
            if self.map_system:
                result = self.map_system.handle_event(event)
                
                if result and result.startswith("launch_event:"):
                    event_file = result.split(":", 1)[1]
                    self.switch_to_dialogue(event_file)
                elif result == "back_to_menu":
                    self.switch_to_menu()
                elif result == "skip_to_home":
                    self.switch_to_home()
                elif result == "skip_time":
                    # 時間スキップ処理（マップは継続）
                    pass

    def handle_home_events(self, events):
        """家モードのイベント処理"""
        if self.home_module:
            result = self.home_module.handle_events(events)
            if result == "go_to_map":
                self.switch_to_map()
            elif result == "go_to_main_menu":
                self.switch_to_menu()

    def handle_dialogue_events(self):
        """会話モードのイベント処理"""
        # controller2が独自にpygame.event.get()を使用するため、
        # main.pyからはeventsを渡さない
        if self.dialogue_game_state:
            from dialogue.controller2 import handle_events
            continue_dialogue = handle_events(self.dialogue_game_state, self.screen)
            if not continue_dialogue:  # 会話が終了した場合
                print("💬 KSファイル終了 - 遷移判定開始")
                
                # 時間進行処理のためにイベントIDを保存
                current_event = self.current_event_id
                
                # イベント完了処理（この中でcurrent_event_idがNoneにリセットされる）
                self.mark_current_event_as_completed()
                
                # E001以外のイベントは時間を進める
                if current_event and current_event != "E001":
                    time_manager = get_time_manager()
                    current_period_before = time_manager.get_current_period()
                    print(f"[DEBUG] イベント{current_event}完了後 - 現在時間帯: {current_period_before}")
                    
                    # 現在が放課後かどうか事前にチェック
                    was_after_school = time_manager.is_after_school()
                    print(f"[DEBUG] 放課後判定: {was_after_school}")
                    
                    if was_after_school:
                        # 放課後イベント完了後は明示的に「夜」に設定
                        print(f"[DEBUG] 放課後イベント完了 - 時間を進めます")
                        time_manager.advance_period()  # 放課後 → 夜
                        current_period_after = time_manager.get_current_period()
                        print(f"[TIME] 放課後イベント{current_event}終了 - {current_period_before} → {current_period_after}: {time_manager.get_full_time_string()}")
                        print("[TIME] 夜になったため家モジュールに遷移")
                        self.switch_to_home()
                    else:
                        # 朝・昼のイベント完了後は通常の時間進行
                        time_manager.advance_period()
                        print(f"[TIME] {current_event}終了により時間進行: {time_manager.get_full_time_string()}")
                        print("[TIME] イベント終了 - mapモジュールに遷移")
                        self.switch_to_map()
                else:
                    # E001の場合は時間を進めずにmapに遷移
                    if current_event == "E001":
                        print("[TIME] E001終了 - 時間進行なしでmapモジュールに遷移")
                    self.switch_to_map()

    def update(self):
        """ゲーム状態の更新"""
        if self.current_mode == "menu":
            if self.main_menu:
                self.main_menu.update()
                
        elif self.current_mode == "map":
            if self.map_system:
                self.map_system.update()
                
        elif self.current_mode == "dialogue":
            # 会話システムの更新
            if self.dialogue_game_state:
                from dialogue.controller2 import update_game
                update_game(self.dialogue_game_state)
                
        elif self.current_mode == "home":
            if self.home_module:
                self.home_module.update()

    def render(self):
        """画面描画"""
        self.screen.fill((0, 0, 0))  # 画面クリア
        
        if self.current_mode == "menu":
            if self.main_menu:
                self.main_menu.render()
                
        elif self.current_mode == "map":
            if self.map_system:
                self.map_system.render()
                
        elif self.current_mode == "dialogue":
            # 会話システムの描画（仮想画面に描画）
            if self.dialogue_game_state:
                from dialogue.text_renderer import TextRenderer
                from dialogue.character_manager import draw_characters
                from dialogue.background_manager import draw_background
                from dialogue.choice_renderer import ChoiceRenderer
                from dialogue.fade_manager import draw_fade_overlay
                from dialogue.controller2 import draw_input_blocked_notice

                # 仮想画面をクリア
                self.virtual_screen.fill((0, 0, 0))

                # 背景描画
                draw_background(self.dialogue_game_state)

                # キャラクター描画
                draw_characters(self.dialogue_game_state)

                # フェードオーバーレイ描画（ゲームコンテンツの上、UIの下）
                draw_fade_overlay(self.dialogue_game_state)

                # UIエレメント描画（テキストボックス等）
                if ('image_manager' in self.dialogue_game_state and 'images' in self.dialogue_game_state):
                    image_manager = self.dialogue_game_state['image_manager']
                    images = self.dialogue_game_state['images']
                    show_text = self.dialogue_game_state.get('show_text', True)
                    image_manager.draw_ui_elements(self.virtual_screen, images, show_text)

                # 選択肢が表示中かどうかを確認
                choice_showing = False
                if 'choice_renderer' in self.dialogue_game_state:
                    choice_renderer = self.dialogue_game_state['choice_renderer']
                    choice_showing = choice_renderer.is_choice_showing()

                # テキスト描画（選択肢表示中はスキップ）
                if not choice_showing and 'text_renderer' in self.dialogue_game_state:
                    text_renderer = self.dialogue_game_state['text_renderer']
                    text_renderer.render_text_window(self.dialogue_game_state)

                # 選択肢描画
                if choice_showing:
                    choice_renderer.render()

                # バックログ描画（最後に描画して他の要素の上に表示）
                if 'backlog_manager' in self.dialogue_game_state:
                    backlog_manager = self.dialogue_game_state['backlog_manager']
                    backlog_manager.render()

                # 通知システム描画（最上位）
                if 'notification_manager' in self.dialogue_game_state:
                    notification_manager = self.dialogue_game_state['notification_manager']
                    notification_manager.render()

                draw_input_blocked_notice(self.dialogue_game_state, self.virtual_screen)

                # 仮想画面をフルスクリーンにスケーリングして転送
                # 4:3コンテンツを画面中央に配置
                scaled_surface = pygame.transform.smoothscale(
                    self.virtual_screen,
                    (CONTENT_WIDTH, CONTENT_HEIGHT)
                )
                self.screen.blit(scaled_surface, (OFFSET_X, OFFSET_Y))

        elif self.current_mode == "home":
            if self.home_module:
                self.home_module.render()

        pygame.display.flip()

    def run(self):
        """メインゲームループ"""
        if not self.initialize():
            return False
        
        # タイトル画面表示
        if not show_title_screen(self.screen, DEBUG):
            # タイトル画面でゲーム終了が選択された場合
            print("🚪 タイトル画面でゲーム終了")
            return True
            
        print("🎯 メインゲームループ開始")
        
        while self.running:
            try:
                # イベント処理
                if self.current_mode == "dialogue":
                    # dialogueモードではcontroller2.pyが独自にイベントを処理
                    self.handle_dialogue_events()
                else:
                    # menu/mapモードでは通常通りイベントを取得
                    events = pygame.event.get()
                    
                    if self.current_mode == "menu":
                        self.handle_menu_events(events)
                    elif self.current_mode == "map":
                        self.handle_map_events(events)
                    elif self.current_mode == "home":
                        self.handle_home_events(events)
                
                # 更新
                self.update()
                
                # 描画
                self.render()
                
                # フレームレート制限（パフォーマンス向上のため30FPSに）
                self.clock.tick(30)
                
            except Exception as e:
                print(f"❌ ゲームループエラー: {e}")
                if DEBUG:
                    import traceback
                    traceback.print_exc()
                break
        
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
