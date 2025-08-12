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
            current_char = entry['name']
            # 桃子フォルダ用の名前変換
            if current_char == "桃子":
                current_char = "T04_00_00"
            elif current_char == "サナコ":
                current_char = "T08_01_00"
            
            # 顔パーツはファイル名をそのまま使用
            current_eye = entry['eye']
            current_mouth = entry['mouth']
            current_brow = entry['brow']
            current_cheek = entry.get('cheek', '')
            current_blink = entry.get('blink', True)  # まばたき設定を取得
            show_x = entry.get('show_x', 0.5)
            show_y = entry.get('show_y', 0.5)
            size = entry.get('size', 1.0)
            # デバッグ出力削除
            # キャラクター登場コマンドを追加
            command_text = f"_CHARA_NEW_{current_char}_{show_x}_{show_y}_{size}_{current_blink}"
            normalized_data.append([
                current_bg, current_char, current_eye, current_mouth, current_brow, current_cheek,
                command_text, current_bgm, current_bgm_volume, current_bgm_loop, current_char, False
            ])
            # デバッグ出力削除
                
        elif entry_type == 'bgm':
            current_bgm = entry['file']
            current_bgm_volume = entry['volume']
            current_bgm_loop = entry['loop']
            # デバッグ出力削除
                
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
            move_char = entry['character']
            # 桃子フォルダ用の名前変換
            if move_char == "桃子":
                move_char = "T04_00_00"
            elif move_char == "サナコ":
                move_char = "T08_01_00"
            normalized_data.append([
                current_bg, move_char, current_eye, current_mouth, current_brow, current_cheek,
                move_command, current_bgm, current_bgm_volume, current_bgm_loop, move_char, False
            ])
            if DEBUG:
                print(f"移動コマンド追加: {entry['character']} -> ({entry['left']}, {entry['top']}) zoom: {zoom_value}")

        elif entry_type == 'hide':
            # キャラクター退場コマンドを正規化形式で追加
            hide_char = entry['character']
            # 桃子フォルダ用の名前変換
            if hide_char == "桃子":
                hide_char = "T04_00_00"
            elif hide_char == "サナコ":
                hide_char = "T08_01_00"
            hide_command = f"_CHARA_HIDE_{hide_char}"
            normalized_data.append([
                current_bg, hide_char, current_eye, current_mouth, current_brow, current_cheek,
                hide_command, current_bgm, current_bgm_volume, current_bgm_loop, hide_char, False
            ])
            if DEBUG:
                print(f"退場コマンド追加: {entry['character']}")

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