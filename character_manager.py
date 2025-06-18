import pygame
from config import *

def move_character(game_state, character_name, target_x, target_y, duration=600, zoom=1.0):
    """キャラクターを指定位置に移動するアニメーションを設定する"""
    if character_name not in game_state['character_pos']:
        print(f"警告: キャラクター '{character_name}' は登録されていません")
        # キャラクターがまだ登録されていない場合は、デフォルト位置で登録
        char_width = game_state['images']["characters"]["girl1"].get_width()
        char_height = game_state['images']["characters"]["girl1"].get_height()
        game_state['character_pos'][character_name] = [
            (SCREEN_WIDTH - char_width) // 2,
            (SCREEN_HEIGHT - char_height) // 2
        ]
    
    # 現在の位置を取得
    current_x, current_y = game_state['character_pos'][character_name]
    current_zoom = game_state['character_zoom'].get(character_name, 1.0)

    # 目標位置を計算
    target_x_val = float(target_x)
    target_y_val = float(target_y)

    # 仮想解像度基準で位置を計算してスケーリング
    from config import VIRTUAL_WIDTH, VIRTUAL_HEIGHT, scale_pos
    
    # X方向とY方向の移動を仮想解像度基準で計算
    virtual_offset_x = target_x_val * VIRTUAL_WIDTH
    virtual_offset_y = target_y_val * VIRTUAL_HEIGHT
    
    # スケーリングした実際の位置を計算
    offset_x, offset_y = scale_pos(virtual_offset_x, virtual_offset_y)
    
    # 最終的な目標位置を計算
    final_target_x = current_x + int(offset_x)
    final_target_y = current_y + int(offset_y)
    
    # アニメーション情報を設定
    start_time = pygame.time.get_ticks()
    game_state['character_anim'][character_name] = {
        'start_x': current_x,
        'start_y': current_y,
        'target_x': final_target_x,
        'target_y': final_target_y,
        'start_zoom': current_zoom,
        'target_zoom': zoom,
        'start_time': start_time,
        'duration': duration
    }
    
    # キャラクターをアクティブリストに追加
    if character_name not in game_state['active_characters']:
        game_state['active_characters'].append(character_name)

    if DEBUG:
        print(f"移動アニメーション開始: {character_name} 比率({target_x}, {target_y}) -> 座標({final_target_x}, {final_target_y}), zoom: {current_zoom} -> {zoom}, 時間: {duration}ms")

def hide_character(game_state, character_name):
    """キャラクターを退場させる"""
    if character_name in game_state['active_characters']:
        game_state['active_characters'].remove(character_name)
        if DEBUG:
            print(f"キャラクター '{character_name}' が退場しました")
    else:
        if DEBUG:
            print(f"キャラクター '{character_name}' はアクティブではありません")

    # アニメーション中の場合は停止
    if character_name in game_state['character_anim']:
        del game_state['character_anim'][character_name]
        if DEBUG:
            print(f"警告: キャラクター '{character_name}' の移動アニメーションを停止しました")

def update_character_animations(game_state):
    """キャラクターアニメーションを更新する"""
    current_time = pygame.time.get_ticks()
    
    # 各キャラクターのアニメーション状態を更新
    for char_name, anim_data in list(game_state['character_anim'].items()):
        # 経過時間の計算
        elapsed = current_time - anim_data['start_time']
        
        if elapsed >= anim_data['duration']:
            # アニメーション完了
            game_state['character_pos'][char_name] = [
                anim_data['target_x'],
                anim_data['target_y']
            ]
            game_state['character_zoom'][char_name] = anim_data['target_zoom']
            # アニメーション情報を削除
            del game_state['character_anim'][char_name]
        else:
            # アニメーション進行中
            progress = elapsed / anim_data['duration']  # 0.0～1.0
            
            # 現在位置を線形補間で計算
            current_x = anim_data['start_x'] + (anim_data['target_x'] - anim_data['start_x']) * progress
            current_y = anim_data['start_y'] + (anim_data['target_y'] - anim_data['start_y']) * progress
            current_zoom = anim_data['start_zoom'] + (anim_data['target_zoom'] - anim_data['start_zoom']) * progress
            
            # 位置を更新
            game_state['character_pos'][char_name] = [int(current_x), int(current_y)]
            game_state['character_zoom'][char_name] = current_zoom

def render_face_parts(game_state, char_name, brow_type, eye_type, mouth_type, zoom_scale):
    """顔パーツの描画"""
    screen = game_state['screen']
    if char_name not in game_state['character_pos']:
        return
    
    character_pos = game_state['character_pos'][char_name]
    face_pos = game_state['face_pos']
    image_manager = game_state['image_manager']
    images = game_state['images']
    
    # 眉毛を描画
    if brow_type and brow_type in images["brows"]:
        brow_img = images["brows"][brow_type]
        if zoom_scale != 1.0:
            new_width = int(brow_img.get_width() * zoom_scale)
            new_height = int(brow_img.get_height() * zoom_scale)
            brow_img = pygame.transform.scale(brow_img, (new_width, new_height))
        
        brow_pos = (
            character_pos[0] + face_pos["brow"][0] * zoom_scale,
            character_pos[1] + face_pos["brow"][1] * zoom_scale
        )
        screen.blit(brow_img, 
                  image_manager.center_part(brow_img, brow_pos))

    # 目を描画
    if eye_type and eye_type in images["eyes"]:
        eye_img = images["eyes"][eye_type]
        if zoom_scale != 1.0:
            new_width = int(eye_img.get_width() * zoom_scale)
            new_height = int(eye_img.get_height() * zoom_scale)
            eye_img = pygame.transform.scale(eye_img, (new_width, new_height))
        
        eye_pos = (
            character_pos[0] + face_pos["eye"][0] * zoom_scale,
            character_pos[1] + face_pos["eye"][1] * zoom_scale
        )
        screen.blit(eye_img, 
                  image_manager.center_part(eye_img, eye_pos))
    
    # 口を描画
    if mouth_type and mouth_type in images["mouths"]:
        mouth_img = images["mouths"][mouth_type]
        if zoom_scale != 1.0:
            new_width = int(mouth_img.get_width() * zoom_scale)
            new_height = int(mouth_img.get_height() * zoom_scale)
            mouth_img = pygame.transform.scale(mouth_img, (new_width, new_height))
        
        mouth_pos = (
            character_pos[0] + face_pos["mouth"][0] * zoom_scale,
            character_pos[1] + face_pos["mouth"][1] * zoom_scale
        )
        screen.blit(mouth_img, 
                  image_manager.center_part(mouth_img, mouth_pos))

def draw_characters(game_state):
    """画面上にキャラクターを描画する"""
    current_dialogue = game_state['dialogue_data'][game_state['current_paragraph']] if game_state['dialogue_data'] else None
    current_speaker = current_dialogue[1] if current_dialogue and len(current_dialogue) > 1 else None

    for char_name in game_state['active_characters']:
        if char_name in game_state['character_pos']:
            # キャラクター画像の取得
            char_img_name = CHARACTER_IMAGE_MAP.get(char_name, "girl1")
            if char_img_name not in game_state['images']["characters"]:
                if DEBUG:
                    print(f"警告: キャラクター画像 '{char_img_name}' が見つかりません")
                continue
            char_img = game_state['images']["characters"][char_img_name]

            # キャラクターの位置とズーム倍率を取得
            x, y = game_state['character_pos'][char_name]
            zoom_scale = game_state['character_zoom'].get(char_name, 1.0)

            # ズーム倍率を適用してキャラクター画像をスケール
            if zoom_scale != 1.0:
                new_width = int(char_img.get_width() * zoom_scale)
                new_height = int(char_img.get_height() * zoom_scale)
                scaled_char_img = pygame.transform.scale(char_img, (new_width, new_height))
            else:
                scaled_char_img = char_img
            
            # 画面に描画
            game_state['screen'].blit(scaled_char_img, (x, y))

            # 表情パーツを表示
            if game_state['show_face_parts']:
                # 現在の話し手の場合は対話データから表情を取得
                if char_name == current_speaker and current_dialogue and len(current_dialogue) >= 5:
                    eye_type = current_dialogue[2] if current_dialogue[2] else CHARACTER_DEFAULTS[char_name]["eye"]
                    mouth_type = current_dialogue[3] if current_dialogue[3] else CHARACTER_DEFAULTS[char_name]["mouth"]
                    brow_type = current_dialogue[4] if current_dialogue[4] else CHARACTER_DEFAULTS[char_name]["brow"]
                else:
                    # 話し手でない場合は記録された表情を使用
                    expressions = game_state['character_expressions'].get(char_name, CHARACTER_DEFAULTS[char_name])
                    eye_type = expressions['eye']
                    mouth_type = expressions['mouth']
                    brow_type = expressions['brow']
                
                # 顔パーツを描画
                render_face_parts(game_state, char_name, brow_type, eye_type, mouth_type, zoom_scale)