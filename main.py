import pygame
import sys
from model import initialize_game, initialize_first_scene, update_character_animations, draw_characters, draw_background, update_background_animation
from controller import handle_events, update_game

def render_game(game_state):
    """ゲーム画面の描画"""
    screen = game_state['screen']
    
    # 背景を描画
    draw_background(game_state)

    # キャラクターの描画
    draw_characters(game_state)
    
    # テキストの描画
    if game_state['show_text']:
        game_state['text_renderer'].render()
    
    # バックログの描画
    game_state['backlog_manager'].render()

def main():
    """メイン関数"""
    # ゲームの初期化
    game_state = initialize_game()
    
    # 最初のシーンを初期化
    initialize_first_scene(game_state)
    
    # メインループ
    running = True
    clock = pygame.time.Clock()
    
    while running:
        # イベント処理
        running = handle_events(game_state)

        # 背景アニメーションの更新
        update_background_animation(game_state)

        # キャラクターアニメーションの更新
        update_character_animations(game_state)
        
        # ゲーム状態の更新
        update_game(game_state)
        
        # 画面の描画
        render_game(game_state)

        # 画面の更新
        pygame.display.flip()
        
        # FPSを設定
        clock.tick(30)
    
    # BGMを停止して終了
    game_state['bgm_manager'].stop_bgm()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()