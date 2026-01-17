from config import *

def normalize_dialogue_data(raw_data):
    """dialogue_loader.pyの辞書リストを正規化して統一された構造にする"""
    # デバッグ出力削除
    
    if not raw_data:
        return get_default_normalized_dialogue()
    
    normalized_data = []
    current_bg = None  # 初期背景はなし
    current_char = None
    current_eye = ""
    current_mouth = ""
    current_brow = ""
    current_cheek = ""
    current_blink = True  # デフォルトでまばたき有効
    current_bgm = "maou_bgm_8bit29.mp3"
    current_bgm_volume = 0.1
    current_bgm_loop = True
    
    for i, entry in enumerate(raw_data):
        if not entry or not isinstance(entry, dict):
            continue
        
        entry_type = entry.get('type')
        
        if entry_type == 'background':
            current_bg = entry['value']
            if DEBUG:
                print(f"背景設定: {current_bg}")

        elif entry_type == 'bg_show':
            # 背景表示コマンドを追加
            bg_show_command = f"_BG_SHOW_{entry['storage']}_{entry['x']}_{entry['y']}_{entry['zoom']}"
            normalized_data.append([
                entry['storage'], current_char, current_eye, current_mouth, current_brow, current_cheek,
                bg_show_command, current_bgm, current_bgm_volume, current_bgm_loop, current_char, False
            ])
            current_bg = entry['storage']
            # デバッグ出力削除
                
        elif entry_type == 'bg_move':
            # 背景移動コマンドを追加
            bg_move_command = f"_BG_MOVE_{entry['left']}_{entry['top']}_{entry['time']}_{entry['zoom']}"
            normalized_data.append([
                current_bg, current_char, current_eye, current_mouth, current_brow, current_cheek,
                bg_move_command, current_bgm, current_bgm_volume, current_bgm_loop, current_char, False
            ])
            # デバッグ出力削除
                
        elif entry_type == 'character':
            # キャラクター論理名を取得
            char_name = entry['name']

            # 胴体パーツIDを取得（新形式）
            # 後方互換性: torsoがない場合はnameをフォールバック
            torso_id = entry.get('torso', char_name)

            # 旧形式との互換性のため、桃子フォルダ用の名前変換を適用
            if torso_id == "桃子":
                torso_id = "T04_00_00"
            elif torso_id == "サナコ":
                torso_id = "T08_01_00"

            # current_charは画像ロード用にtorso_idを保持（character_manager.pyとの互換性維持）
            current_char = torso_id

            # 顔パーツはファイル名をそのまま使用
            current_eye = entry['eye']
            current_mouth = entry['mouth']
            current_brow = entry['brow']
            current_cheek = entry.get('cheek', '')
            current_blink = entry.get('blink', True)  # まばたき設定を取得
            show_x = entry.get('show_x', 0.5)
            show_y = entry.get('show_y', 0.5)
            size = entry.get('size', 1.0)
            fade = entry.get('fade', 0.3)  # フェード時間を取得（デフォルト: 0.3秒）
            # デバッグ出力削除
            # キャラクター登場コマンドを追加（torso_idを使用、論理名char_nameも渡す）
            command_text = f"_CHARA_NEW_{torso_id}_{show_x}_{show_y}_{size}_{current_blink}_{fade}_{char_name}"
            normalized_data.append([
                current_bg, torso_id, current_eye, current_mouth, current_brow, current_cheek,
                command_text, current_bgm, current_bgm_volume, current_bgm_loop, char_name, False
            ])
            # デバッグ出力削除
                
        elif entry_type == 'bgm':
            current_bgm = entry['file']
            current_bgm_volume = entry['volume']
            current_bgm_loop = entry['loop']
            # デバッグ出力削除
            
        elif entry_type == 'bgm_pause':
            # BGM一時停止コマンドを辞書形式で保持してフェードタイム情報を含める
            bgm_pause_data = {
                'type': 'bgm_pause',
                'fade_time': entry.get('fade_time', 0.0)
            }
            normalized_data.append([
                current_bg, current_char, current_eye, current_mouth, current_brow, current_cheek,
                "_BGM_PAUSE", current_bgm, current_bgm_volume, current_bgm_loop, current_char, False, bgm_pause_data
            ])
            if DEBUG:
                print(f"BGM一時停止コマンド追加: fade_time={entry.get('fade_time', 0.0)}")
                
        elif entry_type == 'bgm_unpause':
            # BGM再生開始コマンドを辞書形式で保持してフェードタイム情報を含める
            bgm_unpause_data = {
                'type': 'bgm_unpause',
                'fade_time': entry.get('fade_time', 0.0)
            }
            normalized_data.append([
                current_bg, current_char, current_eye, current_mouth, current_brow, current_cheek,
                "_BGM_UNPAUSE", current_bgm, current_bgm_volume, current_bgm_loop, current_char, False, bgm_unpause_data
            ])
            if DEBUG:
                print(f"BGM再生開始コマンド追加: fade_time={entry.get('fade_time', 0.0)}")
                
        elif entry_type == 'se':
            # SE再生コマンドを正規化形式で追加
            se_command = f"_SE_PLAY_{entry['file']}_{entry['volume']}_{entry['frequency']}"
            normalized_data.append([
                current_bg, current_char, current_eye, current_mouth, current_brow, current_cheek,
                se_command, current_bgm, current_bgm_volume, current_bgm_loop, current_char, False
            ])
            if DEBUG:
                print(f"SE再生コマンド追加: {entry['file']} (volume={entry['volume']}, frequency={entry['frequency']})")
                
        elif entry_type == 'dialogue':
            # セリフデータを正規化形式で追加（スクロール情報も含む）
            scroll_continue = entry.get('scroll_continue', False)
            dialogue_char = entry['character']
            # 桃子フォルダ用の名前変換（キャラクター管理用）
            converted_char = dialogue_char
            if dialogue_char == "桃子":
                converted_char = "T04_00_00"
            elif dialogue_char == "サナコ":
                converted_char = "T08_01_00"
            
            # 対話時の顔パーツもファイル名をそのまま使用
            dialogue_eye = entry['eye']
            dialogue_mouth = entry['mouth']
            dialogue_brow = entry['brow']
            dialogue_cheek = entry.get('cheek', '')
            
            
            normalized_data.append([
                entry['background'], converted_char, dialogue_eye, dialogue_mouth, dialogue_brow, dialogue_cheek,
                entry['text'], entry['bgm'], entry['bgm_volume'], entry['bgm_loop'], dialogue_char,  # 話者表示は元の名前を使用
                scroll_continue  # スクロール継続フラグ
            ])
                
        elif entry_type == 'move':
            # 移動コマンドを正規化形式で追加
            zoom_value = entry.get('zoom', '1.0')
            move_command = f"_MOVE_{entry['left']}_{entry['top']}_{entry['time']}_{zoom_value}"
            # 論理名をそのまま使用（active_charactersと一致させる）
            move_char = entry['character']
            normalized_data.append([
                current_bg, move_char, current_eye, current_mouth, current_brow, current_cheek,
                move_command, current_bgm, current_bgm_volume, current_bgm_loop, move_char, False
            ])
            if DEBUG:
                print(f"移動コマンド追加: {entry['character']} -> ({entry['left']}, {entry['top']}) zoom: {zoom_value}")

        elif entry_type == 'hide':
            # キャラクター退場コマンドを正規化形式で追加
            # 論理名をそのまま使用（active_charactersと一致させる）
            hide_char = entry['character']
            fade = entry.get('fade', 0.3)  # フェード時間を取得（デフォルト: 0.3秒）
            hide_command = f"_CHARA_HIDE_{hide_char}_{fade}"
            normalized_data.append([
                current_bg, hide_char, current_eye, current_mouth, current_brow, current_cheek,
                hide_command, current_bgm, current_bgm_volume, current_bgm_loop, hide_char, False
            ])
            if DEBUG:
                print(f"退場コマンド追加: {entry['character']} (fade={fade})")

        elif entry_type == 'scroll_stop':
            # スクロール停止コマンドを正規化形式で追加
            scroll_stop_command = "_SCROLL_STOP"
            normalized_data.append([
                current_bg, current_char, current_eye, current_mouth, current_brow, current_cheek,
                scroll_stop_command, current_bgm, current_bgm_volume, current_bgm_loop, current_char, False
            ])
            if DEBUG:
                print(f"スクロール停止コマンド追加: {scroll_stop_command}")

        elif entry_type == 'choice':
            # 選択肢コマンドを正規化形式で追加
            options = entry.get('options', [])
            normalized_data.append([
                current_bg, current_char, current_eye, current_mouth, current_brow, current_cheek,
                "_CHOICE_", current_bgm, current_bgm_volume, current_bgm_loop, current_char, False, options
            ])
            if DEBUG:
                print(f"選択肢コマンド追加: {options}")
                
        elif entry_type == 'fadeout':
            # フェードアウトコマンドを追加
            fadeout_command = f"_FADEOUT_{entry['color']}_{entry['time']}"
            normalized_data.append([
                current_bg, current_char, current_eye, current_mouth, current_brow, current_cheek,
                fadeout_command, current_bgm, current_bgm_volume, current_bgm_loop, current_char, False
            ])
        
        elif entry_type == 'if_start':
            # if条件分岐開始 - 辞書形式をそのまま保持
            normalized_data.append(entry)
            if DEBUG:
                print(f"if_start追加: {entry}")
        
        elif entry_type == 'if_end':
            # if条件分岐終了 - 辞書形式をそのまま保持
            normalized_data.append(entry)
            if DEBUG:
                print(f"if_end追加: {entry}")
        
        elif entry_type == 'flag_set':
            # フラグ設定 - 辞書形式をそのまま保持
            normalized_data.append(entry)
            if DEBUG:
                print(f"flag_set追加: {entry}")
        
        elif entry_type == 'event_unlock':
            # イベント解禁 - 辞書形式をそのまま保持
            normalized_data.append(entry)
            print(f"[NORMALIZE] event_unlock追加: {entry}")
                
        elif entry_type == 'fadein':
            # フェードインコマンドを追加
            fadein_command = f"_FADEIN_{entry['time']}"
            normalized_data.append([
                current_bg, current_char, current_eye, current_mouth, current_brow, current_cheek,
                fadein_command, current_bgm, current_bgm_volume, current_bgm_loop, current_char, False
            ])
            if DEBUG:
                print(f"フェードイン正規化: {fadein_command}")
    
    # 対話テキストエントリが含まれているかチェック
    dialogue_count = 0
    for i, entry in enumerate(normalized_data):
        if len(entry) > 6 and entry[6] and not entry[6].startswith('_'):
            dialogue_count += 1
    
    if not normalized_data:
        return get_default_normalized_dialogue()
    
    return normalized_data

def get_default_normalized_dialogue():
    """デフォルトの正規化された対話データを返す"""
    print("警告: get_default_normalized_dialogue()が呼ばれました")
    import traceback
    traceback.print_stack()  # 呼び出し元を特定
    
    return [
        [None, "桃子", "", "", "", "", 
         "デフォルトのテキストです。", None, 0.1, True, "桃子", False],
        [None, "桃子", "", "", "", "", 
         "デフォルトのテキストです。", None, 0.1, True, "桃子", False]
    ]
