import pygame
from config import *
from character_manager import move_character, hide_character
from background_manager import show_background, move_background

def advance_dialogue(game_state):
    """次の対話に進む"""
    if game_state['current_paragraph'] >= len(game_state['dialogue_data']) - 1:
        if DEBUG:
            print("対話の終了に達しました")
        return False
    
    game_state['current_paragraph'] += 1
    current_dialogue = game_state['dialogue_data'][game_state['current_paragraph']]

    if DEBUG:
        print(f"段落 {game_state['current_paragraph'] + 1}/{len(game_state['dialogue_data'])} に進みました")
    
    if len(current_dialogue) < 6:
        if DEBUG:
            print("対話データの形式が不正です")
        return False
    
    dialogue_text = current_dialogue[5]
    if DEBUG:
        print(f"処理中のテキスト: '{dialogue_text[:50]}...'")

    # スクロール停止コマンドかどうかチェック
    if dialogue_text and dialogue_text.startswith("_SCROLL_STOP"):
        return _handle_scroll_stop(game_state)

    # キャラクター登場コマンドかどうかチェック
    if dialogue_text and dialogue_text.startswith("_CHARA_NEW_"):
        return _handle_character_show(game_state, dialogue_text, current_dialogue)
    
    # キャラクター退場コマンドかどうかチェック
    elif dialogue_text and dialogue_text.startswith("_CHARA_HIDE_"):
        return _handle_character_hide(game_state, dialogue_text)

    # 移動コマンドかどうかチェック
    elif dialogue_text and dialogue_text.startswith("_MOVE_"):
        return _handle_character_move(game_state, dialogue_text, current_dialogue)
    
    # 背景表示コマンドかどうかチェック
    elif dialogue_text and dialogue_text.startswith("_BG_SHOW_"):
        return _handle_background_show(game_state, dialogue_text)
    
    # 背景移動コマンドかどうかチェック
    elif dialogue_text and dialogue_text.startswith("_BG_MOVE_"):
        return _handle_background_move(game_state, dialogue_text)

    # 選択肢コマンドかどうかチェック
    elif dialogue_text and dialogue_text.startswith("_CHOICE_"):
        return _handle_choice(game_state, dialogue_text, current_dialogue)
    
    else:
        # 通常の対話テキスト
        return _handle_dialogue_text(game_state, current_dialogue)
    
def _handle_scroll_stop(game_state):
    """スクロール停止コマンドを処理"""
    if DEBUG:
        print("スクロール停止コマンド実行")
    
    game_state['text_renderer'].scroll_manager.process_scroll_stop_command()
    
    # スクロール停止コマンドの場合は次の対話に進む
    return advance_dialogue(game_state)

def _handle_character_show(game_state, dialogue_text, current_dialogue):
    """キャラクター登場コマンドを処理（スクロール状態に影響しない）"""
    parts = dialogue_text.split('_')
    if DEBUG:
        print(f"キャラクター登場コマンド解析: dialogue_text='{dialogue_text}'")
        print(f"分割結果: {parts}")

    if len(parts) >= 6:  # _CHARA_NEW,キャラクター名,x,y
        char_name = parts[3]
        
        try:
            show_x = float(parts[4])
            show_y = float(parts[5])
        except (ValueError, IndexError):
            show_x = 0.5
            show_y = 0.5

        if char_name not in game_state['active_characters']:
            game_state['active_characters'].append(char_name)

            # x,yパラメーターを使って位置を設定
            char_img_name = CHARACTER_IMAGE_MAP[char_name]
            char_img = game_state['images']["characters"][char_img_name]
            char_width = char_img.get_width()
            char_height = char_img.get_height()

            # 0.0-1.0の値をピクセル座標に変換
            # 仮想解像度基準で位置を計算してスケーリング
            from config import VIRTUAL_WIDTH, VIRTUAL_HEIGHT, scale_pos
            
            virtual_pos_x = int(VIRTUAL_WIDTH * show_x - char_width // 2)
            virtual_pos_y = int(VIRTUAL_HEIGHT * show_y - char_height // 2)
            
            # スケーリングした実際の位置を計算
            pos_x, pos_y = scale_pos(virtual_pos_x, virtual_pos_y)
            
            game_state['character_pos'][char_name] = [pos_x, pos_y]

            # キャラクターの表情を更新
            if len(current_dialogue) >= 5:
                game_state['character_expressions'][char_name] = {
                    'eye': current_dialogue[2] if current_dialogue[2] else CHARACTER_DEFAULTS[char_name]['eye'],
                    'mouth': current_dialogue[3] if current_dialogue[3] else CHARACTER_DEFAULTS[char_name]['mouth'],
                    'brow': current_dialogue[4] if current_dialogue[4] else CHARACTER_DEFAULTS[char_name]['brow']
                }
            if DEBUG:
                print(f"キャラクター '{char_name}' が登場しました (x={show_x}, y={show_y}) -> ({pos_x}, {pos_y})")
        
    # キャラクター登場コマンドの場合は次の対話に進む（スクロール状態維持）
    return advance_dialogue(game_state)

def _handle_character_hide(game_state, dialogue_text):
    """キャラクター退場コマンドを処理（スクロール状態に影響しない）"""
    parts = dialogue_text.split('_')
    if DEBUG:
        print(f"退場コマンド解析: dialogue_text='{dialogue_text}'")
        print(f"退場コマンド解析: parts={parts}")
    if len(parts) >= 4:  # _CHARA_HIDE_キャラクター名
        char_name = parts[3]
        if DEBUG:
            print(f"退場対象キャラクター名: '{char_name}'")
        hide_character(game_state, char_name)
    else:
        if DEBUG:
            print(f"エラー: 退場コマンドの形式が不正です: '{dialogue_text}'")
        
    # キャラクター退場コマンドの場合は次の対話に進む（スクロール状態維持）
    return advance_dialogue(game_state)

def _handle_character_move(game_state, dialogue_text, current_dialogue):
    """キャラクター移動コマンドを処理（スクロール状態に影響しない）"""
    parts = dialogue_text.split('_')
    if len(parts) >= 5:  # _MOVE_left_top_duration_zoom
        char_name = current_dialogue[1]
        left = float(parts[2])
        top = float(parts[3])
        duration = int(parts[4]) if parts[4].isdigit() else 600
        zoom = float(parts[5]) if len(parts) > 5 else 1.0
        move_character(game_state, char_name, left, top, duration, zoom)
        if DEBUG:
            print(f"移動コマンド実行: {char_name} -> ({left}, {top}, {zoom})")
    
    # 移動コマンドの場合は次の対話に進む（スクロール状態維持）
    return advance_dialogue(game_state)

def _handle_background_show(game_state, dialogue_text):
    """背景表示コマンドを処理（スクロール状態に影響しない）"""
    parts = dialogue_text.split('_')
    if DEBUG:
        print(f"背景表示コマンド解析: dialogue_text='{dialogue_text}'")
        print(f"分割結果: {parts}")

    if len(parts) >= 6:  # _BG_SHOW_,背景名,x,y,zoom
        bg_name = parts[3]
        
        try:
            bg_x = float(parts[4])
            bg_y = float(parts[5])
            bg_zoom = float(parts[6])
        except (ValueError, IndexError):
            bg_x = 0.5
            bg_y = 0.5
            bg_zoom = 1.0

        show_background(game_state, bg_name, bg_x, bg_y, bg_zoom)
        if DEBUG:
            print(f"背景 '{bg_name}' を表示しました (x={bg_x}, y={bg_y}, zoom={bg_zoom})")
        
    # 背景表示コマンドの場合は次の対話に進む（スクロール状態維持）
    return advance_dialogue(game_state)

def _handle_background_move(game_state, dialogue_text):
    """背景移動コマンドを処理（スクロール状態に影響しない）"""
    parts = dialogue_text.split('_')
    if DEBUG:
        print(f"背景移動コマンド解析: dialogue_text='{dialogue_text}'")
        print(f"分割結果: {parts}")
        
    if len(parts) >= 6:  # _BG_MOVE_left_top_duration_zoom
        bg_left = float(parts[3])
        bg_top = float(parts[4])
        bg_duration = int(parts[5]) if parts[5].isdigit() else 600
        bg_move_zoom = float(parts[6]) if len(parts) > 6 else 1.0
        move_background(game_state, bg_left, bg_top, bg_duration, bg_move_zoom)
        if DEBUG:
            print(f"背景移動コマンド実行: 相対移動({bg_left}, {bg_top}), zoom={bg_move_zoom}, 時間={bg_duration}ms")
    
    # 背景移動コマンドの場合は次の対話に進む（スクロール状態維持）
    return advance_dialogue(game_state)

def _handle_choice(game_state, dialogue_text, current_dialogue):
    """選択肢を処理"""
    try:
        options = []
        
        # 正規化された形式の場合（リスト形式）
        if isinstance(current_dialogue, list) and len(current_dialogue) > 11:
            if current_dialogue[5] == "_CHOICE_":
                options = current_dialogue[11]  # 12番目の要素が選択肢リスト
                if DEBUG:
                    print(f"正規化された選択肢データを取得: {options}")
        
        # 辞書形式の場合（dialogue_loaderからの直接データ）
        elif isinstance(current_dialogue, dict) and current_dialogue.get('type') == 'choice':
            options = current_dialogue.get('options', [])
            if DEBUG:
                print(f"辞書形式の選択肢データを取得: {options}")
        
        # その他の形式から解析
        else:
            options = _parse_choice_from_text(dialogue_text)
            if DEBUG:
                print(f"テキストから選択肢を解析: {options}")
        
        if options and len(options) >= 2:
            # 選択肢を表示
            game_state['choice_renderer'].show_choices(options)
            if DEBUG:
                print(f"選択肢を表示しました: {options}")
            return True
        else:
            if DEBUG:
                print(f"選択肢の形式が正しくありません: {options}")
            return advance_dialogue(game_state)
    
    except Exception as e:
        if DEBUG:
            print(f"選択肢処理エラー: {e}")
            import traceback
            traceback.print_exc()
        return advance_dialogue(game_state)

def _parse_choice_from_text(dialogue_text):
    """テキストから選択肢を解析"""
    import re
    options = []
    
    # _CHOICE_option1_option2_option3形式を解析
    parts = dialogue_text.split('_')
    for i, part in enumerate(parts):
        if i >= 2:  # _CHOICE_の後の部分
            if part.strip():
                options.append(part.strip())
    
    return options

def _handle_dialogue_text(game_state, current_dialogue):
    """通常の対話テキストを処理"""
    dialogue_text = current_dialogue[5]
    display_name = current_dialogue[9] if len(current_dialogue) > 9 and current_dialogue[9] else current_dialogue[1]
    
    # 表示名の有効性をチェック
    if display_name and display_name not in CHARACTER_IMAGE_MAP:
        display_name = None
    
    # スクロール継続フラグをチェック（リストの11番目の要素）
    should_scroll = False
    if len(current_dialogue) > 10:
        should_scroll = current_dialogue[10]
    
    # アクティブキャラクターリストを適切な形式で取得
    active_characters = game_state.get('active_characters', [])
    if isinstance(active_characters, dict):
        active_characters = list(active_characters.keys())
    
    # テキストレンダラーに対話を設定（スクロール情報も含む）
    game_state['text_renderer'].set_dialogue(
        dialogue_text, 
        display_name,
        should_scroll=should_scroll,
        background=current_dialogue[0],
        active_characters=active_characters
    )

    # 話し手の表情を更新
    if current_dialogue[1] and current_dialogue[1] in game_state['active_characters']:
        char_name = current_dialogue[1]
        if len(current_dialogue) >= 5:
            game_state['character_expressions'][char_name] = {
                'eye': current_dialogue[2] if current_dialogue[2] else CHARACTER_DEFAULTS[char_name]['eye'],
                'mouth': current_dialogue[3] if current_dialogue[3] else CHARACTER_DEFAULTS[char_name]['mouth'],
                'brow': current_dialogue[4] if current_dialogue[4] else CHARACTER_DEFAULTS[char_name]['brow']
            }
    
    if DEBUG:
        print(f"対話設定完了: text='{dialogue_text[:30]}...', speaker={display_name}, scroll={should_scroll}")
    
    return True

def reset_dialogue_state(game_state):
    """対話状態をリセット（スクロール状態は維持）"""
    if DEBUG:
        print("対話状態リセット実行（スクロール状態は維持）")
    # スクロール状態に影響しないようにコメントアウト
    # game_state['text_renderer'].scroll_manager.reset_state()

def force_end_scroll_mode(game_state):
    """スクロールモードを強制終了（機能無効化）"""
    if DEBUG:
        print("スクロールモード強制終了は無効化されています")
    # 強制終了機能を無効化
    # game_state['text_renderer'].scroll_manager.force_end_scroll_mode()