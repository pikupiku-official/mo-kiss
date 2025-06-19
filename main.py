import pygame
import sys
from model import *
from controller2 import handle_events
from config import *

def main():
    """メイン関数"""
    # ゲーム初期化
    print("ゲームを初期化中...")
    game_state = initialize_game()
    
    if not game_state:
        print("エラー: ゲームの初期化に失敗しました")
        return False
    
    # 最初のシーンを初期化
    initialize_first_scene(game_state)
    
    # ゲームループの準備
    clock = pygame.time.Clock()
    running = True
    
    # メインゲームループ
    while running:
        try:
            # イベント処理
            running = handle_events(game_state, game_state['screen'])
            if not running:
                break
            
            # ゲーム状態の更新
            update_game_state(game_state)
            
            # 描画処理
            render_game(game_state)
            
            # フレームレート制限
            clock.tick(60)
            
        except Exception as e:
            print(f"ゲームループエラー: {e}")
            if DEBUG:
                import traceback
                traceback.print_exc()
            break
    
    # ゲーム終了処理
    cleanup_game()
    return True

def update_game_state(game_state):
    """ゲーム状態を更新する"""
    try:
        # テキスト表示の更新
        game_state['text_renderer'].update()
        
        # 背景アニメーションの更新
        update_background_animation(game_state)
        
        # キャラクターアニメーションの更新
        update_character_animations(game_state)
        
        # BGMの更新（controller.pyのupdate_game関数を呼び出し）
        from controller2 import update_game
        update_game(game_state)
        
    except Exception as e:
        if DEBUG:
            print(f"ゲーム状態更新エラー: {e}")

def render_game(game_state):
    """ゲーム画面を描画する"""
    try:
        screen = game_state['screen']
        
        # 画面をクリア（黒で塗りつぶし）
        screen.fill((0, 0, 0))
        
        # 背景を描画
        draw_background(game_state)
        
        # キャラクターを描画
        draw_characters(game_state)

        # UI要素（テキストボックス、ボタン類）を描画
        draw_ui_elements(game_state)
        
        # テキストを描画（選択肢表示中は非表示）
        if game_state['show_text'] and not game_state['choice_renderer'].is_choice_showing():
            game_state['text_renderer'].render()
        
        # 選択肢を描画
        game_state['choice_renderer'].render()
        
        # バックログを描画
        game_state['backlog_manager'].render()
        
        # 画面を更新
        pygame.display.flip()
        
    except Exception as e:
        if DEBUG:
            print(f"描画エラー: {e}")
        # エラー時は赤い画面で警告
        screen.fill((100, 0, 0))
        pygame.display.flip()

def draw_ui_elements(game_state):
    """UI要素を描画する"""
    try:
        if 'image_manager' in game_state and 'images' in game_state:
            image_manager = game_state['image_manager']
            images = game_state['images']
            screen = game_state['screen']
            show_text = game_state.get('show_text', True)
            
            # ImageManagerのdraw_ui_elementsメソッドを使用
            image_manager.draw_ui_elements(screen, images, show_text)
            
    except Exception as e:
        if DEBUG:
            print(f"UI描画エラー: {e}")

def cleanup_game():
    """ゲーム終了時のクリーンアップ"""
    try:
        pygame.mixer.quit()
        pygame.quit()
        print("ゲームを正常に終了しました")
    except Exception as e:
        print(f"終了処理エラー: {e}")

if __name__ == "__main__":
    success = main()
    if not success:
        print("ゲームが正常に終了しませんでした")
        sys.exit(1)