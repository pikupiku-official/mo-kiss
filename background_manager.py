import pygame
from config import *

def show_background(game_state, bg_name, bg_x, bg_y, bg_zoom):
    """背景を指定位置とズームで表示する"""
    bg_state = game_state['background_state']
    
    # パラメータの範囲制限
    bg_x = max(0.0, min(1.0, bg_x))
    bg_y = max(0.0, min(1.0, bg_y))
    bg_zoom = max(0.5, min(3.0, bg_zoom))

    # 背景名を更新
    bg_state['current_bg'] = bg_name

    # ズーム倍率に応じて移動可能範囲を調整
    if bg_zoom >= 1.0:
        # 拡大時：ズーム倍率に応じて移動可能範囲を制限
        # 仮想解像度基準でオフセットを計算してスケーリング
        from config import VIRTUAL_WIDTH, VIRTUAL_HEIGHT, scale_pos
        
        virtual_max_offset_x = VIRTUAL_WIDTH * (bg_zoom - 1.0) / 2
        virtual_max_offset_y = VIRTUAL_HEIGHT * (bg_zoom - 1.0) / 2
        
        # スケーリングした実際のオフセットを計算
        max_offset_x, max_offset_y = scale_pos(virtual_max_offset_x, virtual_max_offset_y)
    else:
        # 縮小時：画面中央に余白ができるが、少しの位置調整は可能
        # 仮想解像度基準でオフセットを計算してスケーリング（縮小時）
        virtual_max_offset_x = VIRTUAL_WIDTH * (1.0 - bg_zoom) / 4  # 縮小時は移動範囲を制限
        virtual_max_offset_y = VIRTUAL_HEIGHT * (1.0 - bg_zoom) / 4
        
        # スケーリングした実際のオフセットを計算
        max_offset_x, max_offset_y = scale_pos(virtual_max_offset_x, virtual_max_offset_y)

    offset_x = (bg_x - 0.5) * max_offset_x * 2
    offset_y = (bg_y - 0.5) * max_offset_y * 2
    
    bg_state['pos'] = [offset_x, offset_y]
    bg_state['zoom'] = bg_zoom
    bg_state['anim'] = None
    
    if DEBUG:
        print(f"背景表示: {bg_name}, オフセット: ({offset_x:.1f}, {offset_y:.1f}), ズーム: {bg_zoom}")

def move_background(game_state, target_x, target_y, duration=600, zoom=1.0):
    """背景を指定位置に移動するアニメーションを設定する"""
    bg_state = game_state['background_state']

    # パラメータの範囲制限
    target_x = max(-0.3, min(0.3, target_x))
    target_y = max(-0.3, min(0.3, target_y))
    zoom = max(0.5, min(3.0, zoom))
    
    # 現在の状態を取得
    current_x, current_y = bg_state['pos']
    current_zoom = bg_state['zoom']
    
    # 目標位置を計算
    if zoom >= 1.0:
        # 拡大時の移動範囲
        # 仮想解像度基準で移動範囲を計算してスケーリング（拡大時）
        from config import VIRTUAL_WIDTH, VIRTUAL_HEIGHT, scale_pos
        
        virtual_max_move_x = VIRTUAL_WIDTH * (zoom - 1.0) / 2
        virtual_max_move_y = VIRTUAL_HEIGHT * (zoom - 1.0) / 2
        
        # スケーリングした実際の移動範囲を計算
        max_move_x, max_move_y = scale_pos(virtual_max_move_x, virtual_max_move_y)
    else:
        # 縮小時の移動範囲（制限的）
        # 仮想解像度基準で移動範囲を計算してスケーリング（縮小時）
        virtual_max_move_x = VIRTUAL_WIDTH * (1.0 - zoom) / 4
        virtual_max_move_y = VIRTUAL_HEIGHT * (1.0 - zoom) / 4
        
        # スケーリングした実際の移動範囲を計算
        max_move_x, max_move_y = scale_pos(virtual_max_move_x, virtual_max_move_y)
    
    offset_x = target_x * max_move_x * 2
    offset_y = target_y * max_move_y * 2
    
    final_target_x = current_x + offset_x
    final_target_y = current_y + offset_y
    
    # 最終位置の範囲制限
    if zoom >= 1.0:
        max_final_x = SCREEN_WIDTH * (zoom - 1.0) / 2
        max_final_y = SCREEN_HEIGHT * (zoom - 1.0) / 2
    else:
        max_final_x = SCREEN_WIDTH * (1.0 - zoom) / 4
        max_final_y = SCREEN_HEIGHT * (1.0 - zoom) / 4

    final_target_x = max(-max_final_x, min(max_final_x, final_target_x))
    final_target_y = max(-max_final_y, min(max_final_y, final_target_y))
    
    # アニメーション情報を設定
    start_time = pygame.time.get_ticks()
    bg_state['anim'] = {
        'start_x': current_x,
        'start_y': current_y,
        'target_x': final_target_x,
        'target_y': final_target_y,
        'start_zoom': current_zoom,
        'target_zoom': zoom,
        'start_time': start_time,
        'duration': duration
    }
    
    if DEBUG:
        print(f"背景移動アニメーション開始: 相対移動({target_x}, {target_y}) -> 最終位置({final_target_x}, {final_target_y}), zoom: {current_zoom} -> {zoom}, 時間: {duration}ms")

def update_background_animation(game_state):
    """背景アニメーションを更新する"""
    bg_state = game_state['background_state']
    
    if not bg_state['anim']:
        return
    
    current_time = pygame.time.get_ticks()
    anim_data = bg_state['anim']
    
    # 経過時間の計算
    elapsed = current_time - anim_data['start_time']
    
    if elapsed >= anim_data['duration']:
        # アニメーション完了
        bg_state['pos'] = [anim_data['target_x'], anim_data['target_y']]
        bg_state['zoom'] = anim_data['target_zoom']
        bg_state['anim'] = None
    else:
        # アニメーション進行中
        progress = elapsed / anim_data['duration']  # 0.0～1.0
        
        # 現在位置を線形補間で計算
        current_x = anim_data['start_x'] + (anim_data['target_x'] - anim_data['start_x']) * progress
        current_y = anim_data['start_y'] + (anim_data['target_y'] - anim_data['start_y']) * progress
        current_zoom = anim_data['start_zoom'] + (anim_data['target_zoom'] - anim_data['start_zoom']) * progress
        
        # 位置を更新
        bg_state['pos'] = [current_x, current_y]
        bg_state['zoom'] = current_zoom

def draw_background(game_state):
    """背景を描画する"""
    screen = game_state['screen']
    bg_state = game_state['background_state']
    
    # 現在の背景を取得
    bg_name = bg_state['current_bg']
    if not bg_name or bg_name not in game_state['images']["backgrounds"]:
        # デフォルト背景にフォールバック
        bg_name = DEFAULT_BACKGROUND
        if bg_name not in game_state['images']['backgrounds']:
            # 背景がない場合は黒で塗りつぶし
            screen.fill((0, 0, 0))
            if DEBUG:
                print(f"警告: 背景画像が見つかりません: {bg_name}")
            return
    
    try:
        # 背景画像を取得
        bg_image = game_state['images']["backgrounds"][bg_name]
        zoom = bg_state['zoom']

        # ズームを適用してサイズを計算
        if zoom >= 1.0:
            # 拡大時：画面サイズ以上になるように
            # 仮想解像度基準でサイズを計算してスケーリング
            from config import VIRTUAL_WIDTH, VIRTUAL_HEIGHT, scale_size
            
            virtual_new_width = int(VIRTUAL_WIDTH * zoom)
            virtual_new_height = int(VIRTUAL_HEIGHT * zoom)
            
            # スケーリングした実際のサイズを計算
            new_width, new_height = scale_size(virtual_new_width, virtual_new_height)
        else:
            # 縮小時：画面サイズより小さくなる（余白が生まれる）
            # 仮想解像度基準でサイズを計算してスケーリング（縮小時）
            virtual_new_width = int(VIRTUAL_WIDTH * zoom)
            virtual_new_height = int(VIRTUAL_HEIGHT * zoom)
            
            # スケーリングした実際のサイズを計算
            new_width, new_height = scale_size(virtual_new_width, virtual_new_height)
        
        # 背景画像をスケール
        if new_width != SCREEN_WIDTH or new_height != SCREEN_HEIGHT:
            scaled_bg = pygame.transform.scale(bg_image, (new_width, new_height))
        else:
            scaled_bg = bg_image
        
        # 描画位置を計算
        # 背景の中心が画面の中心に来るように、オフセットを適用
        # 仮想解像度基準で中央位置を計算してスケーリング
        from config import VIRTUAL_WIDTH, VIRTUAL_HEIGHT, scale_pos
        
        virtual_center_x = VIRTUAL_WIDTH // 2
        virtual_center_y = VIRTUAL_HEIGHT // 2
        
        # スケーリングした実際の中央位置を計算
        center_x, center_y = scale_pos(virtual_center_x, virtual_center_y)
        
        pos_x = int(center_x - new_width // 2 + bg_state['pos'][0])
        pos_y = int(center_y - new_height // 2 + bg_state['pos'][1])
        
        # 縮小時は背景色で塗りつぶし（余白部分）
        if zoom < 1.0:
            screen.fill((20, 20, 40))  # 暗い青で余白を塗りつぶし
        
        # 背景を描画
        screen.blit(scaled_bg, (pos_x, pos_y))
            
    except Exception as e:
        if DEBUG:
            print(f"背景描画エラー: {e}")
        # エラー時は紫で塗りつぶし
        screen.fill((100, 0, 100))