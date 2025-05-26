import pygame
from model import *
from controller import handle_events, update_game
from config import *

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

def diagnose_background_issue(game_state):
    """背景問題の診断"""
    bg_state = game_state['background_state']
    
    print(f"\n=== 背景診断 ===")
    print(f"現在の背景: {bg_state['current_bg']}")
    print(f"背景位置: {bg_state['pos']}")
    print(f"背景ズーム: {bg_state['zoom']}")
    print(f"アニメーション中: {bg_state['anim'] is not None}")
    
    # 背景画像の存在確認
    bg_name = bg_state['current_bg']
    if bg_name in game_state['images']["backgrounds"]:
        print(f"背景画像 '{bg_name}' は存在します")
    else:
        print(f"エラー: 背景画像 '{bg_name}' が見つかりません")
        print(f"利用可能な背景: {list(game_state['images']['backgrounds'].keys())}")
    
    print("===============\n")

def main():
    """メイン関数"""
    # ゲームの初期化
    game_state = initialize_game()
    
    # 最初のシーンを初期化
    initialize_first_scene(game_state)
    
    # メインループ
    running = True
    clock = pygame.time.Clock()

    frame_count = 0
    
    while running:
        # イベント処理
        running = handle_events(game_state)

        # フレームカウント
        frame_count += 1
        
        # 5秒に1回診断情報を表示
        if frame_count % 300 == 0:  # 60FPS × 5秒
            diagnose_background_issue(game_state)

        print(f"Frame {frame_count}: アニメーション更新中...")

        # 背景アニメーションの更新
        update_background_animation(game_state)

        # キャラクターアニメーションの更新
        update_character_animations(game_state)

        screen = game_state['screen']
        
        # 1. 画面クリア
        screen.fill((30, 30, 30))  # 濃いグレーでクリア
        
        # 2. 背景描画テスト
        print(f"Frame {frame_count}: 背景描画中...")
        try:
            draw_background(game_state)
            print(f"背景描画成功")
        except Exception as e:
            print(f"背景描画エラー: {e}")
            # エラー時は赤い画面で警告
            screen.fill((255, 0, 0))
        
        # 3. キャラクター描画
        print(f"Frame {frame_count}: キャラクター描画中...")
        draw_characters(game_state)
        
        # 4. テキスト描画
        if game_state['show_text']:
            game_state['text_renderer'].draw()
        
        # 画面更新
        pygame.display.flip()
        clock.tick(60)

# 最小限のテスト用描画関数
def test_draw_background(game_state):
    """テスト用の簡単な背景描画"""
    screen = game_state['screen']
    bg_state = game_state['background_state']
    
    # 背景の存在確認
    bg_name = bg_state['current_bg']
    if not bg_name or bg_name not in game_state['images']["backgrounds"]:
        # 背景がない場合は青い画面
        screen.fill((0, 0, 255))
        print("テスト: 背景画像なし - 青で表示")
        return
    
    # 背景画像を取得
    bg_image = game_state['images']["backgrounds"][bg_name]
    
    # 単純にそのまま表示（テスト用）
    scaled_bg = pygame.transform.scale(bg_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
    screen.blit(scaled_bg, (0, 0))
    
    print(f"テスト: 背景 '{bg_name}' を表示")
    
    # ズーム情報をテキストで表示
    font = pygame.font.Font(None, 36)
    zoom_text = font.render(f"Zoom: {bg_state['zoom']:.2f}", True, (255, 255, 255))
    screen.blit(zoom_text, (10, 10))