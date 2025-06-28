import pygame
from config import *
from .character_manager import move_character, hide_character
from .background_manager import show_background, move_background

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
        print(f"現在の対話データ: {current_dialogue}")
    
    if len(current_dialogue) < 6:
        if DEBUG:
            print("対話データの形式が不正です")
        return False
    
    dialogue_text = current_dialogue[6]
    if DEBUG:
        print(f"処理中のテキスト: '{dialogue_text[:50]}...'")
        print(f"対話データ全体: {current_dialogue}")

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
        if DEBUG:
            print(f"通常の対話テキストとして処理: '{dialogue_text}'")
            print(f"現在のデータ全体: {current_dialogue}")
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

    if len(parts) >= 6:  # _CHARA_NEW,キャラクター名,x,y,size
        # T04_00_00のようなアンダースコア含みファイル名に対応
        if len(parts) >= 9:  # _CHARA_NEW_T04_00_00_x_y_size の場合
            char_name = f"{parts[3]}_{parts[4]}_{parts[5]}"
            x_index = 6
            y_index = 7
            size_index = 8
        else:  # 通常のキャラクター名の場合
            char_name = parts[3]
            x_index = 4
            y_index = 5
            size_index = 6
        
        try:
            show_x = float(parts[x_index])
            show_y = float(parts[y_index])
            size = float(parts[size_index]) if len(parts) > size_index else 1.0
        except (ValueError, IndexError):
            show_x = 0.5
            show_y = 0.5
            size = 1.0

        # まず画像の存在を確認（遅延ロード対応）
        image_manager = game_state['image_manager']
        char_img = image_manager.get_image("characters", char_name)
        if not char_img:
            if DEBUG:
                print(f"警告: キャラクター画像 '{char_name}' が見つかりません")
            return
            
        if char_name not in game_state['active_characters']:
            game_state['active_characters'].append(char_name)
            if DEBUG:
                print(f"キャラクター '{char_name}' を active_characters に追加")

            # x,yパラメーターを使って位置を設定
            char_width = char_img.get_width()
            char_height = char_img.get_height()

            # 仮想解像度に対する基準スケールを計算
            char_base_scale = VIRTUAL_HEIGHT / char_height  # 高さ基準でスケール計算
            
            # 仮想座標系での描画サイズを計算
            virtual_width = char_width * char_base_scale * size
            virtual_height = char_height * char_base_scale * size

            # 0.0-1.0の値を仮想座標に変換
            # 指定位置に画像の中央が来るように座標を計算
            virtual_center_x = VIRTUAL_WIDTH * show_x
            virtual_center_y = VIRTUAL_HEIGHT * show_y
            virtual_pos_x = int(virtual_center_x - virtual_width // 2)
            virtual_pos_y = int(virtual_center_y - virtual_height // 2)
            
            # 仮想座標を実座標にスケーリング
            pos_x, pos_y = scale_pos(virtual_pos_x, virtual_pos_y)
            
            game_state['character_pos'][char_name] = [pos_x, pos_y]
            if DEBUG:
                print(f"キャラクター '{char_name}' の位置設定: ({pos_x}, {pos_y}), サイズ: {size}")
            
            # sizeパラメータをcharacter_zoomに設定
            game_state['character_zoom'][char_name] = size

            # キャラクターの表情を更新
            if len(current_dialogue) >= 6:
                expressions = {
                    'eye': current_dialogue[2] if current_dialogue[2] else '',
                    'mouth': current_dialogue[3] if current_dialogue[3] else '',
                    'brow': current_dialogue[4] if current_dialogue[4] else '',
                    'cheek': current_dialogue[5] if len(current_dialogue) > 5 and current_dialogue[5] else ''
                }
                game_state['character_expressions'][char_name] = expressions
                
                if DEBUG:
                    print(f"キャラクター '{char_name}' の表情設定: {expressions}")
                    
                # 表情パーツも事前ロード
                try:
                    image_manager.preload_character_set(char_name, {
                        'eyes': [expressions['eye']] if expressions['eye'] else [],
                        'mouths': [expressions['mouth']] if expressions['mouth'] else [],
                        'brows': [expressions['brow']] if expressions['brow'] else [],
                        'cheeks': [expressions['cheek']] if expressions['cheek'] else []
                    })
                except Exception as e:
                    if DEBUG:
                        print(f"表情パーツ事前ロードエラー（続行）: {char_name}: {e}")
            if DEBUG:
                print(f"キャラクター '{char_name}' が登場しました (x={show_x}, y={show_y}, size={size}) -> ({pos_x}, {pos_y})")
        
    # キャラクター登場コマンドの場合は次の対話に進む（スクロール状態維持）
    return advance_dialogue(game_state)

def _handle_character_hide(game_state, dialogue_text):
    """キャラクター退場コマンドを処理（スクロール状態に影響しない）"""
    parts = dialogue_text.split('_')
    if DEBUG:
        print(f"退場コマンド解析: dialogue_text='{dialogue_text}'")
        print(f"退場コマンド解析: parts={parts}")
    if len(parts) >= 4:  # _CHARA_HIDE_キャラクター名
        # T04_00_00のようなアンダースコア含みファイル名に対応
        if len(parts) >= 6:  # _CHARA_HIDE_T04_00_00 の場合
            char_name = f"{parts[3]}_{parts[4]}_{parts[5]}"
        else:  # 通常のキャラクター名の場合
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
        if isinstance(current_dialogue, list) and len(current_dialogue) > 12:
            if dialogue_text == "_CHOICE_":
                options = current_dialogue[12]  # 13番目の要素が選択肢リスト
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
    # cheek追加でインデックスがシフト: [bg, char, eye, mouth, brow, cheek, text, bgm, volume, loop, speaker, scroll]
    dialogue_text = current_dialogue[6]  # textは6番目
    display_name = current_dialogue[10] if len(current_dialogue) > 10 and current_dialogue[10] else current_dialogue[1]  # speakerは10番目
    
    if DEBUG:
        print(f"=== 対話テキスト処理 ===")
        print(f"テキスト: '{dialogue_text}'")
        print(f"話者名: '{display_name}'")
        print(f"現在の段落: {game_state['current_paragraph']}")
        print(f"アクティブキャラクター: {game_state.get('active_characters', [])}")
    
    # 表示名の有効性をチェック（CHARACTER_IMAGE_MAPは削除済み）
    # ファイル名直接使用するためチェック不要
    # if display_name and display_name not in CHARACTER_IMAGE_MAP:
    #     display_name = None
    
    # スクロール継続フラグをチェック（リストの12番目の要素）
    should_scroll = False
    if len(current_dialogue) > 11:
        should_scroll = current_dialogue[11]
    
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
            expressions = {
                'eye': current_dialogue[2] if current_dialogue[2] else '',
                'mouth': current_dialogue[3] if current_dialogue[3] else '',
                'brow': current_dialogue[4] if current_dialogue[4] else '',
                'cheek': current_dialogue[5] if len(current_dialogue) > 5 and current_dialogue[5] else ''
            }
            game_state['character_expressions'][char_name] = expressions
            
            if DEBUG:
                print(f"話し手 '{char_name}' の表情更新: {expressions}")
    
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