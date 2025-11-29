import pygame
import random
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
    print(f"[HIDE] hide_character呼び出し: char_name='{character_name}'")
    print(f"[HIDE] 現在のactive_characters: {game_state['active_characters']}")

    if character_name in game_state['active_characters']:
        game_state['active_characters'].remove(character_name)
        print(f"[HIDE] ✓ キャラクター '{character_name}' を退場させました")
        print(f"[HIDE] 更新後のactive_characters: {game_state['active_characters']}")
    else:
        print(f"[HIDE] ⚠ キャラクター '{character_name}' はアクティブではありません")
        print(f"[HIDE] 現在のactive_characters: {game_state['active_characters']}")

    # アニメーション中の場合は停止
    if character_name in game_state['character_anim']:
        del game_state['character_anim'][character_name]
        print(f"[HIDE] キャラクター '{character_name}' の移動アニメーションを停止しました")

def set_blink_enabled(game_state, character_name, enabled):
    """キャラクターのまばたき機能の有効/無効を設定"""
    game_state['character_blink_enabled'][character_name] = enabled
    if not enabled:
        # まばたきを無効にする場合、状態をリセット
        if character_name in game_state['character_blink_state']:
            del game_state['character_blink_state'][character_name]
        if character_name in game_state['character_blink_timers']:
            del game_state['character_blink_timers'][character_name]

def init_blink_system(game_state, character_name):
    """キャラクターのまばたきシステムを初期化"""
    if character_name not in game_state['character_blink_enabled']:
        game_state['character_blink_enabled'][character_name] = True
    
    if game_state['character_blink_enabled'].get(character_name, True):
        current_time = pygame.time.get_ticks()
        # 2-5秒のランダムな間隔
        next_blink_time = current_time + random.randint(2000, 5000)
        
        game_state['character_blink_timers'][character_name] = next_blink_time
        game_state['character_blink_state'][character_name] = {
            'current_state': 'normal',
            'animation_start': 0,
            'base_eye_type': '',
            'blink_sequence': [],
            'sequence_index': 0
        }
        
        print(f"[BLINK] {character_name}: まばたきシステム初期化完了 - 次回まばたき予定: {next_blink_time - current_time}ms後")

def update_blink_system(game_state):
    """まばたきシステムを更新"""
    if not game_state.get('active_characters'):
        return
    
    current_time = pygame.time.get_ticks()
    
    # デバッグ: まばたきシステムが動作していることを定期的に表示
    if not hasattr(game_state, 'last_blink_debug_time'):
        game_state['last_blink_debug_time'] = 0
    
    if current_time - game_state['last_blink_debug_time'] > 10000:  # 10秒おき
        # print(f"[BLINK] システム動作中 - アクティブキャラクター: {game_state['active_characters']}")
        for char_name in game_state['active_characters']:
            if char_name in game_state['character_blink_timers']:
                remaining = (game_state['character_blink_timers'][char_name] - current_time) / 1000
                state = game_state['character_blink_state'].get(char_name, {}).get('current_state', 'normal')
                # print(f"[BLINK] {char_name}: 状態={state}, 次回まで={remaining:.1f}秒")
        game_state['last_blink_debug_time'] = current_time
    
    for char_name in game_state['active_characters'].copy():
        # まばたきが無効な場合はスキップ
        if not game_state['character_blink_enabled'].get(char_name, True):
            continue
        
        # まばたきタイマーがない場合は初期化
        if char_name not in game_state['character_blink_timers']:
            init_blink_system(game_state, char_name)
            continue
        
        # まばたきタイマーチェック（アニメーション中でない場合のみ）
        blink_state = game_state['character_blink_state'].get(char_name, {})
        if (current_time >= game_state['character_blink_timers'][char_name] and 
            blink_state.get('current_state', 'normal') == 'normal'):
            start_blink_animation(game_state, char_name)
        
        # まばたきアニメーション更新
        update_blink_animation(game_state, char_name, current_time)

def start_blink_animation(game_state, character_name):
    """まばたきアニメーションを開始"""
    current_time = pygame.time.get_ticks()
    expressions = game_state['character_expressions'].get(character_name, {})
    base_eye_type = expressions.get('eye', '')
    
    print(f"[BLINK] {character_name}: まばたき開始試行 - 目の種類: '{base_eye_type}', 表情データ: {expressions}")
    
    if not base_eye_type:
        # 次のまばたき時間を設定して終了
        game_state['character_blink_timers'][character_name] = current_time + random.randint(3000, 6000)
        print(f"[BLINK] {character_name}: 目の種類が設定されていません - スキップ")
        return
    
    # 目の種類を解析（例: F04_Ea00_00 -> 00）
    if '_' in base_eye_type:
        parts = base_eye_type.split('_')
        print(f"[BLINK] {character_name}: 目の種類解析 - 分割結果: {parts}")
        if len(parts) >= 3:
            eye_base = '_'.join(parts[:2])  # F04_Ea00
            eye_number = parts[2]  # 00
            
            print(f"[BLINK] {character_name}: eye_base='{eye_base}', eye_number='{eye_number}'")

            # まばたきシーケンスを決定
            if eye_number == '00':
                # 00 -> 01 -> 02 -> 01 -> 00
                sequence = ['00', '01', '02', '02', '02', '01', '00']
            elif eye_number == '01':
                # 01 -> 02 -> 01
                sequence = ['01', '02', '02', '02', '01']
            else:
                # その他の場合はまばたき無し
                print(f"[BLINK] {character_name}: サポートされていない目の種類 '{eye_number}' - スキップ")
                game_state['character_blink_timers'][character_name] = current_time + random.randint(3000, 6000)
                return

            # まばたきシーケンスの全画像が存在するか確認
            image_manager = game_state.get('image_manager')
            if image_manager:
                all_images_exist = True
                for suffix in sequence:
                    test_eye_type = f"{eye_base}_{suffix}"
                    # image_pathsに存在するか確認
                    if 'eyes' not in image_manager.image_paths or test_eye_type not in image_manager.image_paths['eyes']:
                        print(f"[BLINK] {character_name}: まばたき画像が存在しません: {test_eye_type} - まばたき無効化")
                        all_images_exist = False
                        break

                if not all_images_exist:
                    # まばたきを無効化
                    game_state['character_blink_enabled'][character_name] = False
                    print(f"[BLINK] {character_name}: まばたき機能を無効化しました")
                    return

            # まばたき状態を設定
            blink_state = game_state['character_blink_state'].get(character_name, {})
            blink_state.update({
                'current_state': 'blinking',
                'animation_start': current_time,
                'base_eye_type': base_eye_type,
                'eye_base': eye_base,
                'blink_sequence': sequence,
                'sequence_index': 0
            })
            game_state['character_blink_state'][character_name] = blink_state

            print(f"[BLINK] {character_name}: まばたき開始 {base_eye_type} -> {sequence}")
        else:
            print(f"[BLINK] {character_name}: 目の種類の形式が不正 - スキップ")
            game_state['character_blink_timers'][character_name] = current_time + random.randint(3000, 6000)
    else:
        print(f"[BLINK] {character_name}: アンダースコアが含まれていない目の種類 - スキップ") 
        game_state['character_blink_timers'][character_name] = current_time + random.randint(3000, 6000)

def update_blink_animation(game_state, character_name, current_time):
    """まばたきアニメーションを更新"""
    if character_name not in game_state['character_blink_state']:
        return
    
    blink_state = game_state['character_blink_state'][character_name]
    
    if blink_state['current_state'] != 'blinking':
        return
    
    elapsed = current_time - blink_state['animation_start']
    frame_duration = 40  # 各フレーム40ms

    # シーケンスの現在のフレームを計算
    frame_index = elapsed // frame_duration
    
    if frame_index >= len(blink_state['blink_sequence']):
        # アニメーション完了
        blink_state['current_state'] = 'normal'
        # まばたき用の一時的な目の情報を削除
        if 'eye_blink' in game_state['character_expressions'][character_name]:
            del game_state['character_expressions'][character_name]['eye_blink']
        # 次のまばたき時間を設定（3-6秒後）
        game_state['character_blink_timers'][character_name] = current_time + random.randint(3000, 6000)
        print(f"[BLINK] {character_name}: まばたき完了 - 次回予定: {(game_state['character_blink_timers'][character_name] - current_time) / 1000:.1f}秒後")
        return
    
    # 現在の目の状態を設定
    current_eye_suffix = blink_state['blink_sequence'][int(frame_index)]
    current_eye_type = f"{blink_state['eye_base']}_{current_eye_suffix}"
    
    # キャラクターの表情を一時的に更新（まばたき用）
    if character_name not in game_state['character_expressions']:
        game_state['character_expressions'][character_name] = {}
    
    # まばたき中の目の表情を設定
    game_state['character_expressions'][character_name]['eye_blink'] = current_eye_type

def update_character_fade_animations(game_state):
    """キャラクターのフェードアニメーションを更新する"""
    if 'character_fade_anim' not in game_state:
        return

    current_time = pygame.time.get_ticks()

    for char_name, anim_data in list(game_state['character_fade_anim'].items()):
        # 経過時間の計算
        elapsed = current_time - anim_data['start_time']

        if elapsed >= anim_data['duration']:
            # アニメーション完了
            game_state['character_alpha'][char_name] = anim_data['target_alpha']

            # 完了時のコールバックがあれば実行
            if 'on_complete' in anim_data and anim_data['on_complete']:
                anim_data['on_complete']()

            # アニメーション情報を削除
            del game_state['character_fade_anim'][char_name]
        else:
            # アニメーション進行中
            progress = elapsed / anim_data['duration']  # 0.0～1.0

            # 現在のアルファ値を線形補間で計算
            current_alpha = anim_data['start_alpha'] + (anim_data['target_alpha'] - anim_data['start_alpha']) * progress
            game_state['character_alpha'][char_name] = int(current_alpha)

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

    # フェードアニメーションの更新
    update_character_fade_animations(game_state)

    # まばたきシステムの更新
    update_blink_system(game_state)

def render_face_parts(game_state, char_name, brow_type, eye_type, mouth_type, cheek_type, zoom_scale, alpha=255):
    """顔パーツの描画（遅延ロード対応）"""
    screen = game_state['screen']
    if char_name not in game_state['character_pos']:
        return

    character_pos = game_state['character_pos'][char_name]
    image_manager = game_state['image_manager']

    # キャラクター画像を遅延ロードで取得
    char_img = image_manager.get_image("characters", char_name)
    if not char_img:
        return

    # キャラクター画像のサイズと中央座標を一度だけ計算
    actual_char_width = char_img.get_width() * zoom_scale
    actual_char_height = char_img.get_height() * zoom_scale
    char_center_x = character_pos[0] + actual_char_width // 2
    char_center_y = character_pos[1] + actual_char_height // 2

    # 眉毛を描画
    if brow_type:
        brow_img = image_manager.get_image("brows", brow_type)
        if brow_img:
            brow_img = get_scaled_image(brow_img, zoom_scale)
            if alpha < 255:
                brow_img = brow_img.copy()
                brow_img.set_alpha(alpha)
            brow_pos = (
                char_center_x - brow_img.get_width() // 2,
                char_center_y - brow_img.get_height() // 2
            )
            screen.blit(brow_img, brow_pos)

    # 目を描画（まばたき考慮）
    final_eye_type = eye_type

    # まばたき中の場合は、まばたき用の目を使用
    if char_name in game_state.get('character_blink_state', {}) and \
       game_state['character_blink_state'][char_name].get('current_state') == 'blinking':
        blink_eye = game_state['character_expressions'].get(char_name, {}).get('eye_blink', '')
        if blink_eye:
            final_eye_type = blink_eye

    if final_eye_type:
        eye_img = image_manager.get_image("eyes", final_eye_type)
        if eye_img:
            eye_img = get_scaled_image(eye_img, zoom_scale)
            if alpha < 255:
                eye_img = eye_img.copy()
                eye_img.set_alpha(alpha)
            eye_pos = (
                char_center_x - eye_img.get_width() // 2,
                char_center_y - eye_img.get_height() // 2
            )
            screen.blit(eye_img, eye_pos)

    # 口を描画
    if mouth_type:
        mouth_img = image_manager.get_image("mouths", mouth_type)
        if mouth_img:
            mouth_img = get_scaled_image(mouth_img, zoom_scale)
            if alpha < 255:
                mouth_img = mouth_img.copy()
                mouth_img.set_alpha(alpha)
            mouth_pos = (
                char_center_x - mouth_img.get_width() // 2,
                char_center_y - mouth_img.get_height() // 2
            )
            screen.blit(mouth_img, mouth_pos)

    # 頬を描画
    if cheek_type:
        cheek_img = image_manager.get_image("cheeks", cheek_type)
        if cheek_img:
            cheek_img = get_scaled_image(cheek_img, zoom_scale)
            if alpha < 255:
                cheek_img = cheek_img.copy()
                cheek_img.set_alpha(alpha)
            cheek_pos = (
                char_center_x - cheek_img.get_width() // 2,
                char_center_y - cheek_img.get_height() // 2
            )
            screen.blit(cheek_img, cheek_pos)

def draw_characters(game_state):
    """画面上にキャラクターを描画する（遅延ロード対応）"""
    current_dialogue = game_state['dialogue_data'][game_state['current_paragraph']] if game_state['dialogue_data'] else None
    current_speaker = current_dialogue[1] if current_dialogue and len(current_dialogue) > 1 else None
    image_manager = game_state['image_manager']
    screen = game_state['screen']

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

            # アルファブレンディングを適用
            alpha = game_state.get('character_alpha', {}).get(char_name, 255)
            if alpha < 255:
                # アルファ値が255未満の場合のみコピーして透明度を設定
                scaled_char_img = scaled_char_img.copy()
                scaled_char_img.set_alpha(alpha)

            # 画面に描画
            game_state['screen'].blit(scaled_char_img, (x, y))

            # 表情パーツを表示
            if game_state['show_face_parts']:

                # 保存された表情を使用（scenario_manager.pyで既に更新済み）
                expressions = game_state['character_expressions'].get(char_name, {})
                eye_type = expressions.get('eye', '')
                mouth_type = expressions.get('mouth', '')
                brow_type = expressions.get('brow', '')
                cheek_type = expressions.get('cheek', '')

                # 顔パーツを描画（必ず呼び出し）
                # 顔パーツも同じスケールを適用
                face_final_zoom = zoom_scale * char_base_scale * SCALE
                render_face_parts(game_state, char_name, brow_type, eye_type, mouth_type, cheek_type, face_final_zoom, alpha)