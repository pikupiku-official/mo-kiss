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

def _blit_with_alpha(screen, image, pos, alpha):
    if alpha >= 255:
        screen.blit(image, pos)
        return
    temp = image.copy()
    temp.set_alpha(alpha)
    screen.blit(temp, pos)

def start_character_part_fade(game_state, character_name, part_type, from_id, to_id, duration_ms):
    if duration_ms <= 0:
        return
    if from_id == to_id:
        if DEBUG:
            print(f"[FADE] skip (same) char={character_name} part={part_type} id={from_id}")
        return
    if DEBUG:
        print(f"[FADE] start char={character_name} part={part_type} from={from_id} to={to_id} duration_ms={duration_ms}")
    fades = game_state.setdefault('character_part_fades', {})
    char_fades = fades.setdefault(character_name, {})
    char_fades[part_type] = {
        'from': from_id,
        'to': to_id,
        'start_time': pygame.time.get_ticks(),
        'duration': duration_ms
    }

def start_character_hide_fade(game_state, character_name, duration_ms):
    if duration_ms <= 0:
        hide_character(game_state, character_name)
        return
    if DEBUG:
        print(f"[FADE] hide start char={character_name} duration_ms={duration_ms}")
    expressions = game_state.get('character_expressions', {}).get(character_name, {})
    torso_id = game_state.get('character_torso', {}).get(character_name, character_name)
    start_character_part_fade(game_state, character_name, 'torso', torso_id, None, duration_ms)
    start_character_part_fade(game_state, character_name, 'brow', expressions.get('brow'), None, duration_ms)
    start_character_part_fade(game_state, character_name, 'eye', expressions.get('eye'), None, duration_ms)
    start_character_part_fade(game_state, character_name, 'mouth', expressions.get('mouth'), None, duration_ms)
    start_character_part_fade(game_state, character_name, 'cheek', expressions.get('cheek'), None, duration_ms)
    hide_pending = game_state.setdefault('character_hide_pending', {})
    hide_pending[character_name] = pygame.time.get_ticks() + duration_ms

def move_character(game_state, character_name, target_x, target_y, duration=600, zoom=1.0):
    """キャラクターを指定位置に移動するアニメーションを設定する"""
    if character_name not in game_state['character_pos']:
        if DEBUG:
            print(f"警告: キャラクター '{character_name}' は登録されていません")

        # 遅延ロードでキャラクター画像を取得
        # 胴体IDを取得（新形式）後方互換性のためchar_nameをフォールバック
        torso_id = game_state.get('character_torso', {}).get(character_name, character_name)
        image_manager = game_state['image_manager']
        char_img = image_manager.get_image("characters", torso_id)
        
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

    # まばたきシステムの更新
    update_blink_system(game_state)
    update_character_fades(game_state)

def update_character_fades(game_state):
    current_time = pygame.time.get_ticks()
    fades = game_state.get('character_part_fades', {})
    for char_name, part_map in list(fades.items()):
        for part_type, fade in list(part_map.items()):
            duration = fade.get('duration', 0)
            if duration <= 0 or current_time - fade.get('start_time', 0) >= duration:
                if DEBUG:
                    print(f"[FADE] end char={char_name} part={part_type}")
                part_map.pop(part_type, None)
        if not part_map:
            fades.pop(char_name, None)

    hide_pending = game_state.get('character_hide_pending', {})
    for char_name, end_time in list(hide_pending.items()):
        if current_time >= end_time:
            hide_pending.pop(char_name, None)
            hide_character(game_state, char_name)
            fades.pop(char_name, None)

def render_face_parts(game_state, char_name, brow_type, eye_type, mouth_type, cheek_type, zoom_scale, fade_map=None, current_time=None):
    """Face parts rendering with optional crossfade."""
    screen = game_state['screen']
    if char_name not in game_state['character_pos']:
        return

    if current_time is None:
        current_time = pygame.time.get_ticks()
    if fade_map is None:
        fade_map = {}

    character_pos = game_state['character_pos'][char_name]
    image_manager = game_state['image_manager']

    torso_id = game_state.get('character_torso', {}).get(char_name, char_name)
    char_img = image_manager.get_image("characters", torso_id)
    if not char_img:
        return

    actual_char_width = char_img.get_width() * zoom_scale
    actual_char_height = char_img.get_height() * zoom_scale
    char_center_x = character_pos[0] + actual_char_width // 2
    char_center_y = character_pos[1] + actual_char_height // 2

    def draw_part_image(part_img, alpha=255):
        part_pos = (
            char_center_x - part_img.get_width() // 2,
            char_center_y - part_img.get_height() // 2
        )
        _blit_with_alpha(screen, part_img, part_pos, alpha)

    def draw_part(part_type, part_id):
        fade = fade_map.get(part_type)
        if fade:
            duration = fade.get('duration', 0)
            start_time = fade.get('start_time', 0)
            progress = 1.0 if duration <= 0 else min(1.0, (current_time - start_time) / duration)
            if progress >= 1.0:
                fade_map.pop(part_type, None)
                part_id = fade.get('to')
                if not part_id:
                    return
                fade = None
            else:
                from_id = fade.get('from')
                to_id = fade.get('to')
                if from_id:
                    from_img = image_manager.get_image(part_type + "s", from_id)
                    if from_img:
                        from_img = get_scaled_image(from_img, zoom_scale)
                        draw_part_image(from_img, int(255 * (1.0 - progress)))
                if to_id:
                    to_img = image_manager.get_image(part_type + "s", to_id)
                    if to_img:
                        to_img = get_scaled_image(to_img, zoom_scale)
                        draw_part_image(to_img, int(255 * progress))
                return

        if part_id:
            part_img = image_manager.get_image(part_type + "s", part_id)
            if part_img:
                part_img = get_scaled_image(part_img, zoom_scale)
                draw_part_image(part_img)

    final_eye_type = eye_type
    if char_name in game_state.get('character_blink_state', {}) and \
       game_state['character_blink_state'][char_name].get('current_state') == 'blinking':
        blink_eye = game_state['character_expressions'].get(char_name, {}).get('eye_blink', '')
        if blink_eye and 'eye' not in fade_map:
            final_eye_type = blink_eye

    draw_part('brow', brow_type)
    draw_part('eye', final_eye_type)
    draw_part('mouth', mouth_type)
    draw_part('cheek', cheek_type)

def draw_characters(game_state):
    """Draw characters with optional part fades."""
    current_dialogue = game_state['dialogue_data'][game_state['current_paragraph']] if game_state['dialogue_data'] else None
    current_speaker = current_dialogue[1] if current_dialogue and len(current_dialogue) > 1 else None
    image_manager = game_state['image_manager']
    screen = game_state['screen']

    for char_name in game_state['active_characters']:
        if char_name not in game_state['character_pos']:
            continue

        fade_map = game_state.get('character_part_fades', {}).get(char_name, {})
        current_time = pygame.time.get_ticks()
        torso_id = game_state.get('character_torso', {}).get(char_name, char_name)

        char_img = image_manager.get_image("characters", torso_id)
        if not char_img:
            if DEBUG:
                print(f"??: ????????'{char_name}' ????????")
            continue

        x, y = game_state['character_pos'][char_name]
        zoom_scale = game_state['character_zoom'].get(char_name, 1.0)

        def draw_torso_image(torso_key, alpha=255):
            torso_img = image_manager.get_image("characters", torso_key)
            if not torso_img:
                return None
            base_scale = VIRTUAL_HEIGHT / torso_img.get_height()
            final_zoom = zoom_scale * base_scale * SCALE
            scaled_img = get_scaled_image(torso_img, final_zoom)
            _blit_with_alpha(screen, scaled_img, (x, y), alpha)
            return torso_img

        torso_fade = fade_map.get('torso')
        if torso_fade:
            duration = torso_fade.get('duration', 0)
            start_time = torso_fade.get('start_time', 0)
            progress = 1.0 if duration <= 0 else min(1.0, (current_time - start_time) / duration)
            if progress >= 1.0:
                fade_map.pop('torso', None)
                torso_to = torso_fade.get('to')
                if torso_to:
                    char_img = draw_torso_image(torso_to) or char_img
                else:
                    continue
            else:
                if torso_fade.get('from'):
                    draw_torso_image(torso_fade.get('from'), int(255 * (1.0 - progress)))
                if torso_fade.get('to'):
                    draw_torso_image(torso_fade.get('to'), int(255 * progress))
        else:
            draw_torso_image(torso_id, 255)

        char_base_scale = VIRTUAL_HEIGHT / char_img.get_height()

        if game_state['show_face_parts']:
            expressions = game_state['character_expressions'].get(char_name, {})
            eye_type = expressions.get('eye', '')
            mouth_type = expressions.get('mouth', '')
            brow_type = expressions.get('brow', '')
            cheek_type = expressions.get('cheek', '')

            face_final_zoom = zoom_scale * char_base_scale * SCALE
            render_face_parts(
                game_state,
                char_name,
                brow_type,
                eye_type,
                mouth_type,
                cheek_type,
                face_final_zoom,
                fade_map=fade_map,
                current_time=current_time,
            )

