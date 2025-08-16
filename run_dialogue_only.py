#!/usr/bin/env python3
"""
dialogueフォルダのみ実行するファイル

このファイルはdialogueシステムのみを起動し、
メインメニューやマップシステムを経由せずに
直接会話パートを実行できます。
"""

import warnings
import os
import sys

# パフォーマンス向上のため警告を抑制
warnings.filterwarnings("ignore")
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

# パスの設定 - 現在のディレクトリ（mo-kiss）をパスに追加
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

import pygame
from config import *
from dialogue.model import initialize_game as init_dialogue_game
from dialogue.controller2 import handle_events, update_game
from dialogue.text_renderer import TextRenderer
from dialogue.character_manager import draw_characters
from dialogue.background_manager import draw_background
from dialogue.choice_renderer import ChoiceRenderer
from dialogue.dialogue_loader import DialogueLoader
from dialogue.data_normalizer import normalize_dialogue_data

class DialogueOnlyRunner:
    def __init__(self, event_file=None):
        """
        dialogueシステム専用の実行クラス
        
        Args:
            event_file (str): 読み込むイベントファイル（デフォルト: events/E001.ks）
        """
        self.event_file = event_file or "events/E001.ks"
        self.screen = None
        self.clock = None
        self.running = True
        self.dialogue_game_state = None
        
        print(f"💬 Dialogueシステム起動中... (イベント: {self.event_file})")

    def initialize(self):
        """dialogueシステムの初期化"""
        try:
            # Pygameの初期化
            pygame.init()
            pygame.mixer.init()
            
            # 画面設定
            self.screen = init_game()  # config.pyのinit_game()を使用
            self.clock = pygame.time.Clock()
            
            # dialogueゲームの初期化
            self.dialogue_game_state = init_dialogue_game()
            if not self.dialogue_game_state:
                print("❌ dialogue初期化失敗")
                return False
            
            # イベントファイルを読み込み
            if not self.load_event_file():
                return False
                
            print("✅ Dialogueシステム初期化完了")
            return True
            
        except Exception as e:
            print(f"❌ 初期化エラー: {e}")
            if DEBUG:
                import traceback
                traceback.print_exc()
            return False

    def load_event_file(self):
        """指定されたイベントファイルを読み込み"""
        try:
            dialogue_loader = DialogueLoader()
            raw_dialogue_data = dialogue_loader.load_dialogue_from_ks(self.event_file)
            
            if raw_dialogue_data:
                dialogue_data = normalize_dialogue_data(raw_dialogue_data)
                if dialogue_data:
                    self.dialogue_game_state['dialogue_data'] = dialogue_data
                    self.dialogue_game_state['current_paragraph'] = -1
                    
                    # 最初の会話データを表示
                    from dialogue.scenario_manager import advance_dialogue
                    advance_dialogue(self.dialogue_game_state)
                    
                    print(f"✅ イベントファイル読み込み完了: {self.event_file}")
                    return True
                else:
                    print("❌ ダイアログデータの正規化に失敗")
                    return False
            else:
                print("❌ イベントファイルの読み込みに失敗")
                return False
                
        except Exception as e:
            print(f"❌ イベントファイル読み込みエラー: {e}")
            if DEBUG:
                import traceback
                traceback.print_exc()
            return False

    def handle_events(self):
        """イベント処理"""
        # controller2が独自にpygame.event.get()を使用
        continue_dialogue = handle_events(self.dialogue_game_state, self.screen)
        if not continue_dialogue:
            print("💬 会話終了")
            self.running = False

    def update(self):
        """ゲーム状態の更新"""
        if self.dialogue_game_state:
            update_game(self.dialogue_game_state)

    def render(self):
        """画面描画"""
        self.screen.fill((0, 0, 0))  # 画面クリア
        
        if self.dialogue_game_state:
            # 背景描画
            draw_background(self.dialogue_game_state)
            
            # キャラクター描画
            draw_characters(self.dialogue_game_state)
            
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

        pygame.display.flip()

    def run(self):
        """メインループ"""
        if not self.initialize():
            return False
            
        print("🎯 Dialogueシステム開始")
        
        while self.running:
            try:
                # イベント処理
                self.handle_events()
                
                # 更新
                self.update()
                
                # 描画
                self.render()
                
                # フレームレート制限
                self.clock.tick(60)
                
            except Exception as e:
                print(f"❌ ループエラー: {e}")
                if DEBUG:
                    import traceback
                    traceback.print_exc()
                break
        
        self.cleanup()
        return True

    def cleanup(self):
        """終了処理"""
        print("🔄 Dialogueシステム終了処理中...")
        pygame.quit()
        print("✅ Dialogueシステム終了")

def main():
    """メイン関数"""
    # コマンドライン引数でイベントファイルを指定可能
    event_file = None
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        
        # 拡張子がない場合は.ksを追加
        if not arg.endswith('.ks'):
            arg += '.ks'
        
        # eventsディレクトリのパスがない場合は追加
        if not arg.startswith('events/'):
            event_file = f"events/{arg}"
        else:
            event_file = arg
            
        print(f"📁 指定されたイベントファイル: {event_file}")
    else:
        print("📁 使用法:")
        print("  python run_dialogue_only.py E001")
        print("  python run_dialogue_only.py E002.ks")
        print("  python run_dialogue_only.py events/E003.ks")
        print("  デフォルト: events/E001.ks")
    
    runner = DialogueOnlyRunner(event_file)
    success = runner.run()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())