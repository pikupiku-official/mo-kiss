from config import *

def normalize_dialogue_data(raw_data):
    """dialogue_loader.pyの出力を正規化して統一された構造にする"""
    print(f"data_normalizer.py: 正規化前のデータ数: {len(raw_data) if raw_data else 0}")
    
    if not raw_data:
        return get_default_normalized_dialogue()
    
    normalized_data = []
    current_bg = DEFAULT_BACKGROUND
    current_char = None
    current_eye = "eye1"
    current_mouth = "mouth1"
    current_brow = "brow1"
    current_bgm = "maou_bgm_8bit29.mp3"
    current_bgm_volume = 0.1
    current_bgm_loop = True
    
    for i, entry in enumerate(raw_data):
        if not entry:
            continue
        
        # 新しいリスト形式のデータ処理（dialogue_loaderからの出力）
        if isinstance(entry, list) and len(entry) >= 6:
            # 既に正規化された形式の場合はそのまま追加
            text = entry[5]
            
            # コマンドでない場合（通常の対話）
            if not text.startswith('_'):
                # スクロール継続フラグを追加（11番目の要素）
                scroll_continue = entry[10] if len(entry) > 10 else False
                
                normalized_entry = [
                    entry[0],  # 背景
                    entry[1],  # キャラクター
                    entry[2],  # 目
                    entry[3],  # 口
                    entry[4],  # 眉
                    entry[5],  # テキスト
                    entry[6],  # BGM
                    entry[7],  # BGM音量
                    entry[8],  # BGMループ
                    entry[9],  # 表示名
                    scroll_continue  # スクロール継続フラグ
                ]
                normalized_data.append(normalized_entry)
                
                if DEBUG:
                    print(f"対話追加: {entry[1]}: {text[:20]}..., スクロール: {scroll_continue}")
            else:
                # コマンドの場合はそのまま追加（スクロールフラグはFalse）
                normalized_entry = list(entry)
                if len(normalized_entry) < 11:
                    normalized_entry.append(False)  # スクロールフラグ追加
                normalized_data.append(normalized_entry)
                
                if DEBUG:
                    print(f"コマンド追加: {text}")
        
        # 辞書形式のデータ処理（下位互換性のため残す）
        elif isinstance(entry, dict):
            entry_type = entry.get('type')
            
            if entry_type == 'background':
                current_bg = entry['value']
                if DEBUG:
                    print(f"背景設定: {current_bg}")

            elif entry_type == 'bg_show':
                # 背景表示コマンドを追加
                bg_show_command = f"_BG_SHOW_{entry['storage']}_{entry['x']}_{entry['y']}_{entry['zoom']}"
                normalized_data.append([
                    entry['storage'], current_char, current_eye, current_mouth, current_brow,
                    bg_show_command, current_bgm, current_bgm_volume, current_bgm_loop, current_char, False
                ])
                current_bg = entry['storage']
                if DEBUG:
                    print(f"背景表示コマンド追加: {bg_show_command}")
                    
            elif entry_type == 'bg_move':
                # 背景移動コマンドを追加
                bg_move_command = f"_BG_MOVE_{entry['left']}_{entry['top']}_{entry['time']}_{entry['zoom']}"
                normalized_data.append([
                    current_bg, current_char, current_eye, current_mouth, current_brow,
                    bg_move_command, current_bgm, current_bgm_volume, current_bgm_loop, current_char, False
                ])
                if DEBUG:
                    print(f"背景移動コマンド追加: {bg_move_command}")
                    
            elif entry_type == 'character':
                current_char = entry['name']
                current_eye = entry['eye']
                current_mouth = entry['mouth']
                current_brow = entry['brow']
                show_x = entry.get('show_x', 0.5)
                show_y = entry.get('show_y', 0.5)
                if DEBUG:
                    print(f"キャラクター設定: {current_char}, {current_eye}, {current_mouth}, {current_brow}, x={show_x}, y={show_y}")
                # キャラクター登場コマンドを追加
                command_text = "_CHARA_NEW_" + current_char + "_" + str(show_x) + "_" + str(show_y)
                normalized_data.append([
                    current_bg, current_char, current_eye, current_mouth, current_brow,
                    command_text, current_bgm, current_bgm_volume, current_bgm_loop, current_char, False
                ])
                if DEBUG:
                    print(f"キャラクター登場コマンド追加: _CHARA_NEW_{current_char}_{show_x}_{show_y}")
                    
            elif entry_type == 'bgm':
                current_bgm = entry['file']
                current_bgm_volume = entry['volume']
                current_bgm_loop = entry['loop']
                if DEBUG:
                    print(f"BGM設定: {current_bgm}, 音量: {current_bgm_volume}, ループ: {current_bgm_loop}")
                    
            elif entry_type == 'dialogue':
                # セリフデータを正規化形式で追加（スクロール情報も含む）
                scroll_continue = entry.get('scroll_continue', False)
                normalized_data.append([
                    entry['background'], entry['character'], entry['eye'], entry['mouth'], entry['brow'],
                    entry['text'], entry['bgm'], entry['bgm_volume'], entry['bgm_loop'], entry['character'],
                    scroll_continue  # スクロール継続フラグ
                ])
                if DEBUG:
                    print(f"セリフ追加: {entry['character']}: {entry['text'][:20]}..., スクロール: {scroll_continue}")
                    
            elif entry_type == 'move':
                # 移動コマンドを正規化形式で追加
                zoom_value = entry.get('zoom', '1.0')
                move_command = f"_MOVE_{entry['left']}_{entry['top']}_{entry['time']}_{zoom_value}"
                normalized_data.append([
                    current_bg, entry['character'], current_eye, current_mouth, current_brow,
                    move_command, current_bgm, current_bgm_volume, current_bgm_loop, entry['character'], False
                ])
                if DEBUG:
                    print(f"移動コマンド追加: {entry['character']} -> ({entry['left']}, {entry['top']}) zoom: {zoom_value}")

            elif entry_type == 'hide':
                # キャラクター退場コマンドを正規化形式で追加
                hide_command = f"_CHARA_HIDE_{entry['character']}"
                normalized_data.append([
                    current_bg, entry['character'], current_eye, current_mouth, current_brow,
                    hide_command, current_bgm, current_bgm_volume, current_bgm_loop, entry['character'], False
                ])
                if DEBUG:
                    print(f"退場コマンド追加: {entry['character']}")
    
    print(f"data_normalizer.py: 正規化後のデータ数: {len(normalized_data)}")
    
    if normalized_data and len(normalized_data) > 0:
        print(f"data_normalizer.py: 出力データの最初: {normalized_data[0]}")
        print(f"data_normalizer.py: 出力データの2番目: {normalized_data[1] if len(normalized_data) > 1 else 'なし'}")
    
    if not normalized_data:
        return get_default_normalized_dialogue()
    
    return normalized_data

def get_default_normalized_dialogue():
    """デフォルトの正規化された対話データを返す"""
    print("警告: get_default_normalized_dialogue()が呼ばれました")
    import traceback
    traceback.print_stack()  # 呼び出し元を特定
    
    return [
        [DEFAULT_BACKGROUND, "桃子", "eye1", "mouth1", "brow1", 
         "デフォルトのテキストです。", "maou_bgm_8bit29.mp3", 0.1, True, "桃子", False],
        [DEFAULT_BACKGROUND, "桃子", "eye1", "mouth1", "brow1", 
         "デフォルトのテキストです。", "maou_bgm_8bit29.mp3", 0.1, True, "桃子", False]
    ]