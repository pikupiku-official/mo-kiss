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

    def switch_to_menu(self):
        """メインメニューモードに切り替え"""
        print("📱 メインメニューモードに切り替え")
        self.current_mode = "menu"
        if not self.main_menu:
            self.main_menu = MainMenu(self.screen)

    def switch_to_map(self):
        """マップモードに切り替える"""
        print("🗺️ マップモードに切り替え")
        self.current_mode = "map"
        if not self.map_system:
            try:
                self.map_system = AdvancedKimikissMap()
            except Exception as e:
                print(f"❌ マップシステム初期化エラー: {e}")
                self.switch_to_menu()

    def switch_to_dialogue(self, event_file=None):
        """会話モードに切り替え"""
        print(f"💬 会話モードに切り替え (イベント: {event_file})")
        self.current_mode = "dialogue"
        
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
                self.switch_to_map()
            elif result == "dialogue_test":
                self.switch_to_dialogue("events/E001.ks")
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

    def handle_dialogue_events(self):
        """会話モードのイベント処理"""
        # controller2が独自にpygame.event.get()を使用するため、
        # main.pyからはeventsを渡さない
        if self.dialogue_game_state:
            from dialogue.controller2 import handle_events
            continue_dialogue = handle_events(self.dialogue_game_state, self.screen)
            if not continue_dialogue:  # 会話が終了した場合
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
                
                # 背景描画
                draw_background(self.dialogue_game_state)
                
                # UIエレメント描画（テキストボックス等）
                if ('image_manager' in self.dialogue_game_state and 'images' in self.dialogue_game_state):
                    image_manager = self.dialogue_game_state['image_manager']
                    images = self.dialogue_game_state['images']
                    show_text = self.dialogue_game_state.get('show_text', True)
                    image_manager.draw_ui_elements(self.screen, images, show_text)
                
                # キャラクター描画
                draw_characters(self.dialogue_game_state)
                
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

        pygame.display.flip()

    def run(self):
        """メインゲームループ"""
        if not self.initialize():
            return False
            
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