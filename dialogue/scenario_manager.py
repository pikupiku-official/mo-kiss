import pygame
from config import *
from .character_manager import move_character, hide_character, set_blink_enabled, init_blink_system
from .background_manager import show_background, move_background
from .fade_manager import start_fadeout, start_fadein

def advance_dialogue(game_state):
    """次の対話に進む"""
    max_index = len(game_state['dialogue_data']) - 1

    if game_state['current_paragraph'] >= max_index:
        return False

    game_state['current_paragraph'] += 1

    # 境界チェック
    if game_state['current_paragraph'] >= len(game_state['dialogue_data']):
        print(f"[ERROR] 段落インデックス越界: {game_state['current_paragraph']} >= {len(game_state['dialogue_data'])}")
        return False

    current_dialogue = game_state['dialogue_data'][game_state['current_paragraph']]

    # 辞書タイプの場合はそのまま処理
    if isinstance(current_dialogue, dict):
        dialogue_text = ""
    else:
        # リストタイプの場合
        if len(current_dialogue) < 6:
            print(f"[ERROR] 対話データの形式が不正: 長さ={len(current_dialogue)}")
            return False
        dialogue_text = current_dialogue[6] if len(current_dialogue) > 6 else ""

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
    
    # フェードアウトコマンドかどうかチェック
    elif dialogue_text and dialogue_text.startswith("_FADEOUT_"):
        return _handle_fadeout(game_state, dialogue_text)
    
    # フェードインコマンドかどうかチェック
    elif dialogue_text and dialogue_text.startswith("_FADEIN_"):
        return _handle_fadein(game_state, dialogue_text)
    
    # SE再生コマンドかどうかチェック
    elif dialogue_text and dialogue_text.startswith("_SE_PLAY_"):
        return _handle_se_play(game_state, dialogue_text)
    
    # BGM一時停止コマンドかどうかチェック
    elif dialogue_text and dialogue_text.startswith("_BGM_PAUSE"):
        return _handle_bgm_pause(game_state, current_dialogue)
    
    # BGM再生開始コマンドかどうかチェック
    elif dialogue_text and dialogue_text.startswith("_BGM_UNPAUSE"):
        return _handle_bgm_unpause(game_state, current_dialogue)
    
    else:
        # 特殊タイプのコマンドチェック
        if isinstance(current_dialogue, dict):
            command_type = current_dialogue.get('type')

            # if条件分岐開始
            if command_type == 'if_start':
                return _handle_if_start(game_state, current_dialogue)

            # if条件分岐終了
            elif command_type == 'if_end':
                return _handle_if_end(game_state, current_dialogue)

            # フラグ設定
            elif command_type == 'flag_set':
                return _handle_flag_set(game_state, current_dialogue)

            # イベント解禁
            elif command_type == 'event_unlock':
                return _handle_event_unlock(game_state, current_dialogue)

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

    if len(parts) >= 6:  # _CHARA_NEW,キャラクター名,x,y,size,blink
        # T04_00_00のようなアンダースコア含みファイル名に対応
        if len(parts) >= 10:  # _CHARA_NEW_T04_00_00_x_y_size_blink の場合
            char_name = f"{parts[3]}_{parts[4]}_{parts[5]}"
            x_index = 6
            y_index = 7
            size_index = 8
            blink_index = 9
        else:  # 通常のキャラクター名の場合
            char_name = parts[3]
            x_index = 4
            y_index = 5
            size_index = 6
            blink_index = 7
        
        try:
            show_x = float(parts[x_index])
            show_y = float(parts[y_index])
            size = float(parts[size_index]) if len(parts) > size_index else 1.0
            blink_enabled = parts[blink_index].lower() == 'true' if len(parts) > blink_index else True
        except (ValueError, IndexError):
            show_x = 0.5
            show_y = 0.5
            size = 1.0
            blink_enabled = True

        # まず画像の存在を確認（遅延ロード対応）
        image_manager = game_state['image_manager']
        char_img = image_manager.get_image("characters", char_name)
        if not char_img:
            if DEBUG:
                print(f"警告: キャラクター画像 '{char_name}' が見つかりません")
            return

        # キャラクターが新規登場か既存キャラクターの表情変更かを判定
        is_new_character = char_name not in game_state['active_characters']

        if is_new_character:
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

            # まばたき機能を設定
            set_blink_enabled(game_state, char_name, blink_enabled)
            if blink_enabled:
                init_blink_system(game_state, char_name)
                if DEBUG:
                    print(f"キャラクター '{char_name}' のまばたき機能を有効にしました")
            else:
                if DEBUG:
                    print(f"キャラクター '{char_name}' のまばたき機能を無効にしました")

            print(f"[CHARACTER] '{char_name}' が登場しました (x={show_x}, y={show_y}, size={size}, blink={blink_enabled}) -> ({pos_x}, {pos_y})")
        else:
            if DEBUG:
                print(f"[CHARACTER] '{char_name}' は既に登場中 - 表情のみ更新します")

        # キャラクターの表情を更新（新規登場でも既存でも実行）
        if len(current_dialogue) >= 6:
            # 既存の表情を取得（存在しない場合は空の表情）
            existing_expressions = game_state['character_expressions'].get(char_name, {
                'eye': '', 'mouth': '', 'brow': '', 'cheek': ''
            })

            # 新しい表情データを構築（空でない場合のみ上書き）
            expressions = existing_expressions.copy()
            if current_dialogue[2]:  # 目
                expressions['eye'] = current_dialogue[2]
            if current_dialogue[3]:  # 口
                expressions['mouth'] = current_dialogue[3]
            if current_dialogue[4]:  # 眉
                expressions['brow'] = current_dialogue[4]
            if len(current_dialogue) > 5 and current_dialogue[5]:  # 頬
                expressions['cheek'] = current_dialogue[5]

            game_state['character_expressions'][char_name] = expressions

            print(f"[CHARACTER] '{char_name}' の表情{'設定' if is_new_character else '更新'}: {expressions}")
            print(f"[CHARACTER] まばたき有効: {blink_enabled}")

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

    # 話し手の表情を更新（空でない場合のみ）
    if current_dialogue[1] and current_dialogue[1] in game_state['active_characters']:
        char_name = current_dialogue[1]
        if len(current_dialogue) >= 5:
            # 既存の表情を取得
            existing_expressions = game_state['character_expressions'].get(char_name, {
                'eye': '', 'mouth': '', 'brow': '', 'cheek': ''
            })
            
            # 新しい表情データがある場合のみ更新
            expressions = existing_expressions.copy()
            if current_dialogue[2]:  # 新しい目のデータがある場合
                expressions['eye'] = current_dialogue[2]
            if current_dialogue[3]:  # 新しい口のデータがある場合
                expressions['mouth'] = current_dialogue[3]
            if current_dialogue[4]:  # 新しい眉のデータがある場合
                expressions['brow'] = current_dialogue[4]
            if len(current_dialogue) > 5 and current_dialogue[5]:  # 新しい頬のデータがある場合
                expressions['cheek'] = current_dialogue[5]
            
            game_state['character_expressions'][char_name] = expressions
    
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

def _handle_fadeout(game_state, dialogue_text):
    """フェードアウトコマンドを処理"""
    parts = dialogue_text.split('_')
    if DEBUG:
        print(f"フェードアウトコマンド解析: dialogue_text='{dialogue_text}'")
        print(f"分割結果: {parts}")

    if len(parts) >= 4:  # _FADEOUT_color_time
        fade_color = parts[2]
        try:
            fade_time = float(parts[3])
        except (ValueError, IndexError):
            fade_time = 1.0
        
        start_fadeout(game_state, fade_color, fade_time)
        print(f"[FADE] フェードアウト実行: color={fade_color}, time={fade_time}s")
    else:
        if DEBUG:
            print(f"エラー: フェードアウトコマンドの形式が不正です: '{dialogue_text}'")
    
    # フェードアウトコマンドの場合は次の対話に進む
    return advance_dialogue(game_state)

def _handle_fadein(game_state, dialogue_text):
    """フェードインコマンドを処理"""
    parts = dialogue_text.split('_')
    if DEBUG:
        print(f"フェードインコマンド解析: dialogue_text='{dialogue_text}'")
        print(f"分割結果: {parts}")

    if len(parts) >= 3:  # _FADEIN_time
        try:
            fade_time = float(parts[2])
        except (ValueError, IndexError):
            fade_time = 1.0
        
        start_fadein(game_state, fade_time)
        print(f"[FADE] フェードイン実行: time={fade_time}s")
    else:
        if DEBUG:
            print(f"エラー: フェードインコマンドの形式が不正です: '{dialogue_text}'")
    
    # フェードインコマンドの場合は次の対話に進む
    return advance_dialogue(game_state)

def _handle_se_play(game_state, dialogue_text):
    """SE再生コマンドを処理"""
    parts = dialogue_text.split('_')
    if DEBUG:
        print(f"SE再生コマンド解析: dialogue_text='{dialogue_text}'")
        print(f"分割結果: {parts}")

    if len(parts) >= 5:  # _SE_PLAY_filename_volume_frequency
        se_filename = parts[3]
        try:
            se_volume = float(parts[4])
        except (ValueError, IndexError):
            se_volume = 0.5
        try:
            se_frequency = int(parts[5])
        except (ValueError, IndexError):
            se_frequency = 1
        
        # SEManagerを使ってSEを再生
        se_manager = game_state.get('se_manager')
        if se_manager:
            success = se_manager.play_se(se_filename, se_volume, se_frequency)
            if DEBUG:
                if success:
                    print(f"SE再生成功: {se_filename} (volume={se_volume}, frequency={se_frequency})")
                else:
                    print(f"SE再生失敗: {se_filename}")
        else:
            if DEBUG:
                print("エラー: SEManagerが見つかりません")
    else:
        if DEBUG:
            print(f"エラー: SE再生コマンドの形式が不正です: '{dialogue_text}'")
    
    # SE再生コマンドの場合は次の対話に進む
    return advance_dialogue(game_state)

def _handle_bgm_pause(game_state, current_dialogue):
    """BGM一時停止コマンドを処理"""
    # フェードタイム情報を取得
    fade_time = 0.0
    
    # 正規化されたデータの場合（リスト形式）
    if isinstance(current_dialogue, list) and len(current_dialogue) > 12:
        bgm_data = current_dialogue[12]
        if isinstance(bgm_data, dict):
            fade_time = bgm_data.get('fade_time', 0.0)
    # 辞書形式の場合
    elif isinstance(current_dialogue, dict):
        fade_time = current_dialogue.get('fade_time', 0.0)
    
    if DEBUG:
        print(f"BGM一時停止コマンド実行: fade_time={fade_time}")
    
    # BGMManagerを使ってBGMを一時停止
    bgm_manager = game_state.get('bgm_manager')
    if bgm_manager:
        if fade_time > 0:
            bgm_manager.pause_bgm_with_fade(fade_time)
            if DEBUG:
                print(f"BGMを{fade_time}秒でフェードアウト一時停止しました")
        else:
            bgm_manager.pause_bgm()
            if DEBUG:
                print("BGMを即座に一時停止しました")
    else:
        if DEBUG:
            print("エラー: BGMManagerが見つかりません")
    
    # BGM一時停止コマンドの場合は次の対話に進む
    return advance_dialogue(game_state)

def _handle_bgm_unpause(game_state, current_dialogue):
    """BGM再生開始コマンドを処理"""
    # フェードタイム情報を取得
    fade_time = 0.0
    
    # 正規化されたデータの場合（リスト形式）
    if isinstance(current_dialogue, list) and len(current_dialogue) > 12:
        bgm_data = current_dialogue[12]
        if isinstance(bgm_data, dict):
            fade_time = bgm_data.get('fade_time', 0.0)
    # 辞書形式の場合
    elif isinstance(current_dialogue, dict):
        fade_time = current_dialogue.get('fade_time', 0.0)
    
    if DEBUG:
        print(f"BGM再生開始コマンド実行: fade_time={fade_time}")
    
    # BGMManagerを使ってBGMの再生を再開
    bgm_manager = game_state.get('bgm_manager')
    if bgm_manager:
        if fade_time > 0:
            bgm_manager.unpause_bgm_with_fade(fade_time)
            if DEBUG:
                print(f"BGMを{fade_time}秒でフェードイン再開しました")
        else:
            bgm_manager.unpause_bgm()
            if DEBUG:
                print("BGMの再生を即座に再開しました")
    else:
        if DEBUG:
            print("エラー: BGMManagerが見つかりません")
    
    # BGM再生開始コマンドの場合は次の対話に進む
    return advance_dialogue(game_state)

def _handle_if_start(game_state, command_data):
    """if条件分岐開始を処理"""
    condition = command_data.get('condition', '')
    dialogue_loader = game_state.get('dialogue_loader')
    
    if DEBUG:
        print(f"条件分岐開始: condition='{condition}'")
    
    # 条件を評価
    condition_met = False
    if dialogue_loader:
        condition_met = dialogue_loader.check_condition(condition)
        if DEBUG:
            print(f"条件評価結果: {condition} -> {condition_met}")
    
    # 条件が満たされない場合、対応するendifまでスキップ
    if not condition_met:
        current_pos = game_state['current_paragraph']
        if_nesting = 1  # ネストレベル
        max_pos = len(game_state['dialogue_data']) - 1
        
        print(f"[DEBUG] 条件不一致でスキップ開始: 現在位置={current_pos}, 最大位置={max_pos}")
        
        while current_pos < max_pos:
            current_pos += 1
            
            # 境界チェック
            if current_pos >= len(game_state['dialogue_data']):
                print(f"[DEBUG] スキップ中に段落境界に到達: {current_pos}")
                break
                
            entry = game_state['dialogue_data'][current_pos]
            print(f"[DEBUG] スキップ中の段落{current_pos}をチェック: {type(entry)}")
            
            if isinstance(entry, dict):
                entry_type = entry.get('type')
                print(f"[DEBUG] dict型エントリ: type={entry_type}, nesting={if_nesting}")
                
                if entry_type == 'if_start':
                    if_nesting += 1
                elif entry_type == 'if_end':
                    if_nesting -= 1
                    if if_nesting == 0:
                        # 対応するendifに到達
                        game_state['current_paragraph'] = current_pos
                        print(f"[DEBUG] 条件不一致により段落{current_pos}のendifまでスキップ完了")
                        # endifに到達したので、次の段落に進む
                        return advance_dialogue(game_state)
        
        # endifが見つからない場合
        if if_nesting > 0:
            print(f"[WARNING] 対応するendifが見つかりません。ネストレベル={if_nesting}")
            # 見つからない場合は最後まで進む
            game_state['current_paragraph'] = max_pos
            return False
    else:
        if DEBUG:
            print("条件一致により次の段落を実行")
    
    # 次の段落に進む
    return advance_dialogue(game_state)

def _handle_if_end(game_state, command_data):
    """if条件分岐終了を処理"""
    if DEBUG:
        print("条件分岐終了")
    
    # 単純に次の段落に進む
    return advance_dialogue(game_state)

def _handle_flag_set(game_state, command_data):
    """フラグ設定を処理"""
    flag_name = command_data.get('name')
    flag_value = command_data.get('value')
    dialogue_loader = game_state.get('dialogue_loader')
    
    if DEBUG:
        print(f"フラグ設定: {flag_name} = {flag_value}")
    
    if dialogue_loader and flag_name is not None:
        dialogue_loader.set_story_flag(flag_name, flag_value)
        if DEBUG:
            print(f"フラグ設定完了: {flag_name} = {flag_value}")
    
    # 次の段落に進む
    return advance_dialogue(game_state)

def _handle_event_unlock(game_state, command_data):
    """イベント解禁を処理"""
    events = command_data.get('events', [])
    dialogue_loader = game_state.get('dialogue_loader')
    
    print(f"[EVENT_UNLOCK] イベント解禁処理開始: {events}")
    
    if dialogue_loader and events:
        dialogue_loader.unlock_events(events)
        print(f"[EVENT_UNLOCK] イベント解禁完了: {events}")
    else:
        print(f"[EVENT_UNLOCK] 処理失敗: dialogue_loader={dialogue_loader}, events={events}")
    
    # 次の段落に進む
    return advance_dialogue(game_state)
