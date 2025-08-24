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
from map.map import AdvancedKimikissMap
from dialogue.model import initialize_game as init_dialogue_game
from title_screen import show_title_screen
from time_manager import get_time_manager
from home import HomeModule
import pygame

class GameApplication:
    def __init__(self):
        """ゲームアプリケーションの初期化"""
        self.current_mode = "menu"  # "menu", "map", "dialogue"
        self.screen = None
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
            
            # 画面設定
            self.screen = init_game()  # config.pyのinit_game()を使用
            self.clock = pygame.time.Clock()
            
            # メインメニューの初期化
            self.main_menu = MainMenu(self.screen)
            
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
            completed_events_csv_path = os.path.join(os.path.dirname(__file__), "events", "completed_events.csv")
            
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
            
            # completed_events.csvの既存データを読み込み
            completed_events = []
            file_exists = os.path.exists(completed_events_csv_path)
            event_found = False
            
            if file_exists:
                with open(completed_events_csv_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if row['イベントID'] == self.current_event_id:
                            # 既存イベントの実行回数を+1
                            current_count = int(row.get('実行回数', '0'))
                            row['実行回数'] = str(current_count + 1)
                            row['実行日時'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            event_found = True
                            print(f"[EVENT] {self.current_event_id}の実行回数を{current_count + 1}に更新")
                        completed_events.append(row)
            
            # 新しいイベントの場合は追加
            if not event_found:
                new_event = {
                    'イベントID': self.current_event_id,
                    '実行日時': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'ヒロイン名': event_info.get('対象のヒロイン', ''),
                    '場所': event_info.get('場所', ''),
                    'イベントタイトル': event_info.get('イベントのタイトル', ''),
                    '実行回数': '1'
                }
                completed_events.append(new_event)
                print(f"[EVENT] {self.current_event_id}を新規記録（実行回数: 1）")
            
            # ファイルに書き戻し
            fieldnames = ['イベントID', '実行日時', 'ヒロイン名', '場所', 'イベントタイトル', '実行回数']
            with open(completed_events_csv_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(completed_events)
            
            # イベントID をリセット
            self.current_event_id = None
            
        except Exception as e:
            print(f"[EVENT] イベント完了記録エラー: {e}")

    def switch_to_menu(self):
        """メインメニューモードに切り替え"""
        print("📱 メインメニューモードに切り替え")
        self.current_mode = "menu"
        if not self.main_menu:
            self.main_menu = MainMenu(self.screen)

    def switch_to_map(self):
        """マップモードに切り替え"""
        print("🗺️ マップモードに切り替え")
        self.current_mode = "map"
        if not self.map_system:
            try:
                self.map_system = AdvancedKimikissMap()
            except Exception as e:
                print(f"❌ マップシステム初期化エラー: {e}")
                self.switch_to_menu()

    def switch_to_home(self):
        """家モジュールに切り替え"""
        print("🏠 家モジュールに切り替え")
        self.current_mode = "home"
        if not self.home_module:
            self.home_module = HomeModule(self.screen)
    
    def switch_to_dialogue(self, event_file=None):
        """会話モードに切り替え"""
        print(f"💬 会話モードに切り替え (イベント: {event_file})")
        self.current_mode = "dialogue"
        
        # イベントIDを抽出（events/E001.ks -> E001）
        if event_file:
            import os
            self.current_event_id = os.path.splitext(os.path.basename(event_file))[0]
            print(f"[EVENT] 開始イベントID: {self.current_event_id}")
        
        try:
            # 会話ゲームの初期化
            self.dialogue_game_state = init_dialogue_game()
            if not self.dialogue_game_state:
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
                        self.switch_to_menu()
                        return
                else:
                    print("❌ イベントファイルの読み込みに失敗")
                    self.switch_to_menu()
                    return
                
        except Exception as e:
            print(f"❌ 会話モード初期化エラー: {e}")
            self.switch_to_menu()

    def handle_menu_events(self, events):
        """メインメニューのイベント処理"""
        for event in events:
            if event.type == pygame.QUIT:
                self.running = False
                return
            
            result = self.main_menu.handle_event(event)
            
            if result == "start_game":
                self.switch_to_dialogue("events/E001.ks")
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
                
                # イベント完了処理
                self.mark_current_event_as_completed()
                
                # 時間管理：放課後イベント終了時は家モジュールへ遷移
                time_manager = get_time_manager()
                if time_manager.is_after_school():
                    print("[TIME] 放課後イベント終了 - 家モジュールに遷移")
                    self.switch_to_home()
                else:
                    print("[TIME] 通常イベント終了 - mapモジュールに遷移")
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
            # 会話システムの描画
            if self.dialogue_game_state:
                from dialogue.text_renderer import TextRenderer
                from dialogue.character_manager import draw_characters
                from dialogue.background_manager import draw_background
                from dialogue.choice_renderer import ChoiceRenderer
                from dialogue.fade_manager import draw_fade_overlay
                
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
                    image_manager.draw_ui_elements(self.screen, images, show_text)
                
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
        pygame.quit()
        print("✅ アプリケーション終了")

def main():
    """メイン関数"""
    app = GameApplication()
    success = app.run()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())