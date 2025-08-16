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
            event_file (str): 読み込むイベントファイル（指定しない場合は実行時に選択）
        """
        self.event_file = event_file
        self.screen = None
        self.clock = None
        self.running = True
        self.dialogue_game_state = None
        self.file_loaded = False
        
        print(f"💬 Dialogueシステム起動中...")

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

    def reload_current_file(self):
        """現在のファイルを再読み込み"""
        print(f"🔄 ファイル再読み込み中: {self.event_file}")
        if self.load_event_file():
            print(f"✅ ファイル再読み込み完了: {self.event_file}")
        else:
            print(f"❌ ファイル再読み込み失敗: {self.event_file}")

    def prompt_file_selection(self):
        """コンソールでファイル選択を促す"""
        print("\n" + "="*50)
        print("🔄 ファイル変更 - 新しい.ksファイルを指定してください:")
        print("  例: E001, E002.ks, events/E003.ks, test_bgm.ks")
        print("  空白でEnterを押すとキャンセル")
        
        # 利用可能なファイルを表示
        self.show_available_files()
        
        print("="*50)
        
        try:
            # コンソール入力を取得
            user_input = input("ファイル名: ").strip()
            
            if not user_input:
                print("❌ キャンセルしました")
                return
            
            # ファイルパスを正規化
            new_file = self.normalize_file_path(user_input)
            
            # ファイルの存在確認
            if not os.path.exists(new_file):
                print(f"❌ ファイルが見つかりません: {new_file}")
                return
            
            # ファイルを変更
            old_file = self.event_file
            self.event_file = new_file
            
            if self.load_event_file():
                self.file_loaded = True
                print(f"✅ ファイル変更完了: {old_file} → {new_file}")
            else:
                # 失敗した場合は元に戻す
                self.event_file = old_file
                print(f"❌ ファイル変更失敗: {new_file}")
                
        except Exception as e:
            print(f"❌ ファイル選択エラー: {e}")

    def normalize_file_path(self, file_input):
        """ファイルパスを正規化"""
        # 拡張子がない場合は.ksを追加
        if not file_input.endswith('.ks'):
            file_input += '.ks'
        
        # eventsディレクトリのパスがない場合は追加
        if not file_input.startswith('events/') and not os.path.exists(file_input):
            return f"events/{file_input}"
        else:
            return file_input

    def initial_file_selection(self):
        """初回のファイル選択"""
        print("\n" + "="*60)
        print("🎬 Dialogue System - KSファイル選択")
        print("="*60)
        print("読み込むKSファイルを指定してください:")
        print("  例: E001, E002.ks, events/E003.ks, test_bgm")
        print("  何も入力せずEnterを押すとevents/E001.ksを読み込みます")
        
        # 利用可能なファイルを表示
        self.show_available_files()
        
        print("="*60)
        
        try:
            user_input = input("ファイル名: ").strip()
            
            if not user_input:
                # デフォルトファイル
                self.event_file = "events/E001.ks"
                print(f"📁 デフォルトファイルを使用: {self.event_file}")
            else:
                # ユーザー指定ファイル
                self.event_file = self.normalize_file_path(user_input)
            
            # ファイル存在確認
            if not os.path.exists(self.event_file):
                print(f"❌ ファイルが見つかりません: {self.event_file}")
                return False
            
            # ファイル読み込み
            if self.load_event_file():
                self.file_loaded = True
                print(f"✅ ファイル読み込み完了: {self.event_file}")
                return True
            else:
                print(f"❌ ファイル読み込み失敗: {self.event_file}")
                return False
                
        except Exception as e:
            print(f"❌ ファイル選択エラー: {e}")
            return False

    def show_available_files(self):
        """利用可能なKSファイルを表示"""
        print("\n📂 利用可能なファイル:")
        
        # eventsディレクトリのファイル
        events_dir = "events"
        if os.path.exists(events_dir):
            ks_files = [f for f in os.listdir(events_dir) if f.endswith('.ks')]
            if ks_files:
                ks_files.sort()
                print("  [eventsディレクトリ]")
                for f in ks_files[:10]:  # 最初の10個だけ表示
                    print(f"    {f.replace('.ks', '')}")
                if len(ks_files) > 10:
                    print(f"    ... 他{len(ks_files) - 10}個")
        
        # カレントディレクトリのKSファイル
        current_ks_files = [f for f in os.listdir('.') if f.endswith('.ks')]
        if current_ks_files:
            current_ks_files.sort()
            print("  [カレントディレクトリ]")
            for f in current_ks_files:
                print(f"    {f.replace('.ks', '')}")
        
        print("")

    def handle_events(self):
        """イベント処理"""
        events = pygame.event.get()
        
        # 独自のキーボードイベント処理
        for event in events:
            if event.type == pygame.QUIT:
                self.running = False
                return
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F5:  # F5キーでファイル再読み込み
                    self.reload_current_file()
                    return
                elif event.key == pygame.K_F6:  # F6キーでファイル選択
                    self.prompt_file_selection()
                    return
                elif event.key == pygame.K_ESCAPE:  # ESCキーで終了
                    self.running = False
                    return
        
        # ファイルが読み込まれていない場合、dialogueイベントは処理しない
        if not self.file_loaded:
            return
        
        # controller2にイベントを渡す（pygameのイベントキューを再構築）
        for event in events:
            pygame.event.post(event)
        
        continue_dialogue = handle_events(self.dialogue_game_state, events)
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
        
        # ファイルが読み込まれていない場合は待機画面を表示
        if not self.file_loaded:
            self.render_waiting_screen()
            pygame.display.flip()
            return
        
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

    def render_waiting_screen(self):
        """待機画面を描画"""
        try:
            # 基本フォント
            font = pygame.font.Font(None, 36)
            small_font = pygame.font.Font(None, 24)
            
            # 画面中央に待機メッセージを表示
            center_x = self.screen.get_width() // 2
            center_y = self.screen.get_height() // 2
            
            # メインメッセージ
            main_text = font.render("KSファイルを選択してください", True, (255, 255, 255))
            main_rect = main_text.get_rect(center=(center_x, center_y - 60))
            self.screen.blit(main_text, main_rect)
            
            # 指示メッセージ
            instruction_text = small_font.render("コンソールでファイル名を入力してください", True, (200, 200, 200))
            instruction_rect = instruction_text.get_rect(center=(center_x, center_y - 20))
            self.screen.blit(instruction_text, instruction_rect)
            
            # キーボードショートカット
            shortcut_text = small_font.render("F6: ファイル選択 | ESC: 終了", True, (150, 150, 150))
            shortcut_rect = shortcut_text.get_rect(center=(center_x, center_y + 20))
            self.screen.blit(shortcut_text, shortcut_rect)
            
        except Exception as e:
            # フォント読み込みに失敗した場合
            pass

    def run(self):
        """メインループ"""
        if not self.initialize():
            return False
        
        # コマンドライン引数でファイルが指定されている場合
        if self.event_file:
            # ファイル存在確認
            if not os.path.exists(self.event_file):
                print(f"❌ 指定されたファイルが見つかりません: {self.event_file}")
                self.event_file = None
            else:
                # ファイル読み込み
                if self.load_event_file():
                    self.file_loaded = True
                    print(f"✅ ファイル読み込み完了: {self.event_file}")
                else:
                    print(f"❌ ファイル読み込み失敗: {self.event_file}")
                    self.event_file = None
        
        # ファイルが指定されていない、または読み込みに失敗した場合
        if not self.file_loaded:
            if not self.initial_file_selection():
                print("❌ ファイル選択に失敗しました")
                return False
            
        print("🎯 Dialogueシステム開始")
        print("🎮 キーボードショートカット: F5=再読み込み, F6=ファイル変更, ESC=終了")
        
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
        print("  python run_dialogue_only.py test_bgm")
        print("  引数なし: 実行時にファイル選択プロンプトを表示")
        print("\n🎮 実行中のキーボードショートカット:")
        print("  F5     : 現在のファイルを再読み込み")
        print("  F6     : 新しい.ksファイルを指定")
        print("  ESC    : 終了")
    
    runner = DialogueOnlyRunner(event_file)
    success = runner.run()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())

if __name__ == "__main__":

    sys.exit(main())
