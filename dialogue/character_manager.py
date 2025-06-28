import pygame
from config import *

# 画像スケーリングキャッシュ
_scaled_image_cache = {}

def get_scaled_image(image, zoom_scale):
    """画像をキャッシュ付きでスケーリング"""
    if zoom_scale == 1.0:
        return image
    
    # キャッシュキーを作成
    image_id = id(image)
    cache_key = (image_id, zoom_scale)
    
    # キャッシュから取得を試行
    if cache_key in _scaled_image_cache:
        return _scaled_image_cache[cache_key]
    
    # スケーリングして新しい画像を作成
    new_width = int(image.get_width() * zoom_scale)
    new_height = int(image.get_height() * zoom_scale)
    scaled_image = pygame.transform.scale(image, (new_width, new_height))
    
    # キャッシュに保存（最大100個まで）
    if len(_scaled_image_cache) > 100:
        # 古いエントリを削除
        oldest_key = next(iter(_scaled_image_cache))
        del _scaled_image_cache[oldest_key]
    
    _scaled_image_cache[cache_key] = scaled_image
    return scaled_image

def move_character(game_state, character_name, target_x, target_y, duration=600, zoom=1.0):
    """キャラクターを指定位置に移動するアニメーションを設定する"""
    if character_name not in game_state['character_pos']:
        if DEBUG:
            print(f"警告: キャラクター '{character_name}' は登録されていません")
        
        # 遅延ロードでキャラクター画像を取得
        image_manager = game_state['image_manager']
        char_img = image_manager.get_image("characters", character_name)
        
        if char_img:
            char_width = char_img.get_width()
            char_height = char_img.get_height()
        else:
            # キャラクター画像がない場合はデフォルトサイズを使用（元サイズ相当）
            char_width = 2894  # 元画像サイズ
            char_height = 4093
        
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

def render_face_parts(game_state, char_name, brow_type, eye_type, mouth_type, cheek_type, zoom_scale):
    """顔パーツの描画（遅延ロード対応）"""
    screen = game_state['screen']
    if char_name not in game_state['character_pos']:
        if DEBUG:
            print(f"[FACE] キャラクター '{char_name}' の位置情報がありません")
        return
    
    character_pos = game_state['character_pos'][char_name]
    image_manager = game_state['image_manager']
    
    if DEBUG:
        print(f"[FACE] 顔パーツ描画開始: {char_name}")
        print(f"[FACE] パーツ情報 - eye:{eye_type}, mouth:{mouth_type}, brow:{brow_type}, cheek:{cheek_type}")
    
    # キャラクター画像を遅延ロードで取得
    char_img = image_manager.get_image("characters", char_name)
    if not char_img:
        if DEBUG:
            print(f"[FACE] キャラクター画像 '{char_name}' が取得できません")
        return
    
    # キャラクター画像のサイズと中央座標を一度だけ計算
    actual_char_width = char_img.get_width() * zoom_scale
    actual_char_height = char_img.get_height() * zoom_scale
    char_center_x = character_pos[0] + actual_char_width // 2
    char_center_y = character_pos[1] + actual_char_height // 2
    
    if DEBUG:
        print(f"[FACE] キャラクター位置: {character_pos}, 中央: ({char_center_x}, {char_center_y}), ズーム: {zoom_scale}")
    
    # 眉毛を描画
    if brow_type:
        brow_img = image_manager.get_image("brows", brow_type)
        if brow_img:
            brow_img = get_scaled_image(brow_img, zoom_scale)
            brow_pos = (
                char_center_x - brow_img.get_width() // 2,
                char_center_y - brow_img.get_height() // 2
            )
            screen.blit(brow_img, brow_pos)
            if DEBUG:
                print(f"[FACE] 眉毛描画完了: {brow_type} at {brow_pos}")
        else:
            if DEBUG:
                print(f"[FACE] 眉毛画像が見つかりません: {brow_type}")
    elif DEBUG:
        print(f"[FACE] 眉毛データなし")

    # 目を描画
    if eye_type:
        eye_img = image_manager.get_image("eyes", eye_type)
        if eye_img:
            eye_img = get_scaled_image(eye_img, zoom_scale)
            eye_pos = (
                char_center_x - eye_img.get_width() // 2,
                char_center_y - eye_img.get_height() // 2
            )
            screen.blit(eye_img, eye_pos)
            if DEBUG:
                print(f"[FACE] 目描画完了: {eye_type} at {eye_pos}")
        else:
            if DEBUG:
                print(f"[FACE] 目画像が見つかりません: {eye_type}")
    elif DEBUG:
        print(f"[FACE] 目データなし")
    
    # 口を描画
    if mouth_type:
        mouth_img = image_manager.get_image("mouths", mouth_type)
        if mouth_img:
            mouth_img = get_scaled_image(mouth_img, zoom_scale)
            mouth_pos = (
                char_center_x - mouth_img.get_width() // 2,
                char_center_y - mouth_img.get_height() // 2
            )
            screen.blit(mouth_img, mouth_pos)
            if DEBUG:
                print(f"[FACE] 口描画完了: {mouth_type} at {mouth_pos}")
        else:
            if DEBUG:
                print(f"[FACE] 口画像が見つかりません: {mouth_type}")
    elif DEBUG:
        print(f"[FACE] 口データなし")
    
    # 頬を描画
    if cheek_type:
        cheek_img = image_manager.get_image("cheeks", cheek_type)
        if cheek_img:
            cheek_img = get_scaled_image(cheek_img, zoom_scale)
            cheek_pos = (
                char_center_x - cheek_img.get_width() // 2,
                char_center_y - cheek_img.get_height() // 2
            )
            screen.blit(cheek_img, cheek_pos)
            if DEBUG:
                print(f"[FACE] 頬描画完了: {cheek_type} at {cheek_pos}")
        else:
            if DEBUG:
                print(f"[FACE] 頬画像が見つかりません: {cheek_type}")
    elif DEBUG:
        print(f"[FACE] 頬データなし")

def draw_characters(game_state):
    """画面上にキャラクターを描画する（遅延ロード対応）"""
    current_dialogue = game_state['dialogue_data'][game_state['current_paragraph']] if game_state['dialogue_data'] else None
    current_speaker = current_dialogue[1] if current_dialogue and len(current_dialogue) > 1 else None
    image_manager = game_state['image_manager']

    for char_name in game_state['active_characters']:
        if char_name in game_state['character_pos']:
            # キャラクター画像を遅延ロードで取得
            char_img = image_manager.get_image("characters", char_name)
            
            if not char_img:
                if DEBUG:
                    print(f"警告: キャラクター画像 '{char_name}' が取得できません")
                continue

            # キャラクターの位置とズーム倍率を取得
            x, y = game_state['character_pos'][char_name]
            zoom_scale = game_state['character_zoom'].get(char_name, 1.0)
            # 自動スケールは無効化（元サイズで表示）

            # ズーム倍率を適用してキャラクター画像をスケール（キャッシュ使用）
            # キャラクター画像は非常に大きい（2894x4093）ので、仮想解像度に合わせて基準スケールを適用
            # 仮想解像度1920x1080に対して適切なサイズに調整する基準スケール
            char_base_scale = VIRTUAL_HEIGHT / char_img.get_height()  # 高さ基準でスケール計算
            final_zoom = zoom_scale * char_base_scale * SCALE
            scaled_char_img = get_scaled_image(char_img, final_zoom)
            
            # 画面に描画
            game_state['screen'].blit(scaled_char_img, (x, y))

            # 表情パーツを表示
            if game_state['show_face_parts']:
                
                # 強制的に顔パーツを表示するため、複数のソースから表情データを取得
                eye_type = ""
                mouth_type = ""
                brow_type = ""
                cheek_type = ""
                
                # 1. 現在の話し手の場合は対話データから表情を取得
                if char_name == current_speaker and current_dialogue and len(current_dialogue) >= 6:
                    eye_type = current_dialogue[2] if current_dialogue[2] else ""
                    mouth_type = current_dialogue[3] if current_dialogue[3] else ""
                    brow_type = current_dialogue[4] if current_dialogue[4] else ""
                    cheek_type = current_dialogue[5] if len(current_dialogue) > 5 and current_dialogue[5] else ""
                
                # 2. 記録された表情を使用
                expressions = game_state['character_expressions'].get(char_name, {})
                if not eye_type and expressions.get('eye'):
                    eye_type = expressions.get('eye', '')
                if not mouth_type and expressions.get('mouth'):
                    mouth_type = expressions.get('mouth', '')
                if not brow_type and expressions.get('brow'):
                    brow_type = expressions.get('brow', '')
                if not cheek_type and expressions.get('cheek'):
                    cheek_type = expressions.get('cheek', '')
                
                # デバッグ出力
                if DEBUG:
                    print(f"[FACE] {char_name}の表情データ: eye={eye_type}, mouth={mouth_type}, brow={brow_type}, cheek={cheek_type}")
                    print(f"[FACE] 現在の話し手: {current_speaker}, アクティブキャラクター: {game_state['active_characters']}")
                    expressions = game_state['character_expressions'].get(char_name, {})
                    print(f"[FACE] 保存された表情: {expressions}")
                
                # 顔パーツを描画（必ず呼び出し）
                # 顔パーツも同じスケールを適用
                face_final_zoom = zoom_scale * char_base_scale * SCALE
                render_face_parts(game_state, char_name, brow_type, eye_type, mouth_type, cheek_type, face_final_zoom)