import pygame
from bgm_manager import BGMManager
from dialogue_loader import DialogueLoader
from image_manager import ImageManager
from text_renderer import TextRenderer
from backlog_manager import BacklogManager
from config import *

def initialize_game():
    """ゲームの初期化を行う"""
    # Pygameを初期化
    pygame.init()
    pygame.mixer.init()

    # 画面の設定
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("テスト")

    # 各マネージャーの初期化
    bgm_manager = BGMManager(DEBUG)
    dialogue_loader = DialogueLoader(DEBUG)
    image_manager = ImageManager(DEBUG)
    text_renderer = TextRenderer(screen, DEBUG)
    
    # バックログマネージャーの初期化
    backlog_manager = BacklogManager(screen, text_renderer.fonts)
    
    # TextRendererにBacklogManagerを設定
    text_renderer.set_backlog_manager(backlog_manager)

    # 画像の読み込み
    try:
        images = image_manager.load_all_images(SCREEN_WIDTH, SCREEN_HEIGHT)
    except Exception as e:
        print(f"画像の読み込みに失敗しました： {e}")

    # 会話データの読み込みと正規化
    try:
        raw_dialogue_data = dialogue_loader.load_dialogue_from_ks("dialogue.ks")
        dialogue_data = normalize_dialogue_data(raw_dialogue_data)
    except Exception as e:
        print(f"対話データの読み込みに失敗しました: {e}")
        dialogue_data = get_default_normalized_dialogue()

    # キャラクター画像のサイズを取得
    char_width = images["characters"]["girl1"].get_width()
    char_height = images["characters"]["girl1"].get_height()

    # キャラクター画像を画面中央に配置
    character_pos = {}
    for char_name in CHARACTER_IMAGE_MAP.keys():
        character_pos[char_name] = [
            (SCREEN_WIDTH - char_width) // 2,
            (SCREEN_HEIGHT - char_height) // 2
        ]

    # キャラクター移動アニメーション
    character_anim = {}

    # 顔のパーツの相対位置を設定
    face_pos = {
        "eye": (char_width * FACE_POS["eye"][0], char_height * FACE_POS["eye"][1]),
        "mouth": (char_width * FACE_POS["mouth"][0], char_height * FACE_POS["mouth"][1]),
        "brow": (char_width * FACE_POS["brow"][0], char_height * FACE_POS["brow"][1])
    }

    # ゲーム状態の初期化
    game_state = {
        'screen': screen,
        'bgm_manager': bgm_manager,
        'dialogue_loader': dialogue_loader,
        'image_manager': image_manager,
        'text_renderer': text_renderer,
        'backlog_manager': backlog_manager,
        'images': images,
        'dialogue_data': dialogue_data,
        'character_pos': character_pos,
        'character_anim': character_anim,
        'face_pos': face_pos,
        'show_face_parts': True,
        'show_text': True,
        'current_paragraph': 0,
        'active_characters': []
    }

    return game_state

def normalize_dialogue_data(raw_data):
    """dialogue_loader.pyの出力を正規化して統一された構造にする"""
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
    
    for entry in raw_data:
        if not entry:
            continue
        
        # 新しい辞書形式のデータ処理
        if isinstance(entry, dict):
            entry_type = entry.get('type')
            
            if entry_type == 'background':
                current_bg = entry['value']
                if DEBUG:
                    print(f"背景設定: {current_bg}")
                    
            elif entry_type == 'character':
                current_char = entry['name']
                current_eye = entry['eye']
                current_mouth = entry['mouth']
                current_brow = entry['brow']
                if DEBUG:
                    print(f"キャラクター設定: {current_char}, {current_eye}, {current_mouth}, {current_brow}")
                # キャラクター登場コマンドを追加
                normalized_data.append([
                    current_bg, current_char, current_eye, current_mouth, current_brow,
                    f"_CHARA_NEW_{current_char}", current_bgm, current_bgm_volume, current_bgm_loop, current_char
                ])
                    
            elif entry_type == 'bgm':
                current_bgm = entry['file']
                current_bgm_volume = entry['volume']
                current_bgm_loop = entry['loop']
                if DEBUG:
                    print(f"BGM設定: {current_bgm}, 音量: {current_bgm_volume}, ループ: {current_bgm_loop}")
                    
            elif entry_type == 'dialogue':
                # セリフデータを正規化形式で追加
                normalized_data.append([
                    entry['background'], entry['character'], entry['eye'], entry['mouth'], entry['brow'],
                    entry['text'], entry['bgm'], entry['bgm_volume'], entry['bgm_loop'], entry['character']
                ])
                if DEBUG:
                    print(f"セリフ追加: {entry['character']}: {entry['text'][:20]}...")
                    
            elif entry_type == 'move':
                # 移動コマンドを正規化形式で追加
                move_command = f"_MOVE_{entry['left']}_{entry['top']}_{entry['time']}"
                normalized_data.append([
                    current_bg, entry['character'], current_eye, current_mouth, current_brow,
                    move_command, current_bgm, current_bgm_volume, current_bgm_loop, entry['character']
                ])
                if DEBUG:
                    print(f"移動コマンド追加: {entry['character']} -> ({entry['left']}, {entry['top']})")

            elif entry_type == 'hide':
                # キャラクター退場コマンドを正規化形式で追加
                hide_command = f"_CHARA_HIDE_{entry['character']}"
                normalized_data.append([
                    current_bg, entry['character'], current_eye, current_mouth, current_brow,
                    hide_command, current_bgm, current_bgm_volume, current_bgm_loop, entry['character']
                ])
                if DEBUG:
                    print(f"退場コマンド追加: {entry['character']}")
        
        # 古い形式のデータ処理（後方互換性のため）
        else:
            # 背景データの場合
            if len(entry) == 1 and entry[0] and not entry[0].startswith("_"):
                # 背景名かどうかを判定（簡単な判定）
                if entry[0] in ["school", "classroom"] or "bg" in entry[0]:
                    current_bg = entry[0]
                    if DEBUG:
                        print(f"背景設定: {current_bg}")
            
            # キャラクターデータの場合
            elif len(entry) == 4 and all(isinstance(x, str) for x in entry):
                # キャラクター名が最初の要素の場合
                if entry[0] in CHARACTER_IMAGE_MAP:
                    current_char = entry[0]
                    current_eye = entry[1] if entry[1] else "eye1"
                    current_mouth = entry[2] if entry[2] else "mouth1"
                    current_brow = entry[3] if entry[3] else "brow1"
                    if DEBUG:
                        print(f"キャラクター設定: {current_char}, {current_eye}, {current_mouth}, {current_brow}")
            
            # BGMデータの場合
            elif len(entry) == 3:
                current_bgm = entry[0] if entry[0] else current_bgm
                try:
                    current_bgm_volume = float(entry[1]) if entry[1] else 0.1
                    current_bgm_loop = entry[2].lower() == "true" if entry[2] else True
                except ValueError:
                    current_bgm_volume = 0.1
                    current_bgm_loop = True
                if DEBUG:
                    print(f"BGM設定: {current_bgm}, 音量: {current_bgm_volume}, ループ: {current_bgm_loop}")
            
            # セリフデータの場合
            elif len(entry) == 1 and entry[0] and not entry[0] in ["school", "classroom"]:
                text = entry[0]
                # 移動コマンドの場合
                if text.startswith("_MOVE_"):
                    normalized_data.append([
                        current_bg, current_char, current_eye, current_mouth, current_brow,
                        text, current_bgm, current_bgm_volume, current_bgm_loop, current_char
                    ])
                else:
                    # 通常のセリフ
                    normalized_data.append([
                        current_bg, current_char, current_eye, current_mouth, current_brow,
                        text, current_bgm, current_bgm_volume, current_bgm_loop, current_char
                    ])
                    if DEBUG:
                        print(f"セリフ追加: {current_char}: {text[:20]}...")
    
    if not normalized_data:
        return get_default_normalized_dialogue()
    
    return normalized_data

def get_default_normalized_dialogue():
    """デフォルトの正規化された対話データを返す"""
    return [
        [DEFAULT_BACKGROUND, "桃子", "eye1", "mouth1", "brow1", 
         "デフォルトのテキストです。", "maou_bgm_8bit29.mp3", 0.1, True, "桃子"],
        [DEFAULT_BACKGROUND, "桃子", "eye1", "mouth1", "brow1", 
         "デフォルトのテキストです。", "maou_bgm_8bit29.mp3", 0.1, True, "桃子"]
    ]

def initialize_first_scene(game_state):
    """最初のシーンを初期化する"""
    if not game_state['dialogue_data']:
        print("会話データがありません")
        return
    
    # 最初のBGMを再生
    bgm_success = _initialize_bgm(game_state)
    if DEBUG:
        print(f"BGM初期化結果: {'成功' if bgm_success else '失敗'}") 
        
    """# 最初のキャラクターを見つけてアクティブリストに追加
    characters_found = set()
    for entry in game_state['dialogue_data']:
        if len(entry) > 1 and entry[1] and entry[1] in CHARACTER_IMAGE_MAP:  # 有効なキャラクター名のみ
            characters_found.add(entry[1])
    
    # 見つかったキャラクターをアクティブリストに追加
    for char_name in characters_found:
        if char_name not in game_state['active_characters']:
            game_state['active_characters'].append(char_name)
            if DEBUG:
                print(f"キャラクター '{char_name}' をアクティブリストに追加しました")"""
    
    # 最初のテキストを設定
    if game_state['dialogue_data']:
        current_dialogue = game_state['dialogue_data'][game_state['current_paragraph']]
        
        # データの長さをチェック
        if len(current_dialogue) >= 6:
            dialogue_text = current_dialogue[5]
            
            # テキストの有効性をチェック
            if dialogue_text and (dialogue_text.startswith("_CHARA_NEW_") or dialogue_text.startswith("_MOVE_")):
                advance_dialogue(game_state)
            else:
                display_name = current_dialogue[9] if len(current_dialogue) > 9 and current_dialogue[9] else current_dialogue[1]
                # 有効なキャラクター名かチェック
                if display_name and display_name not in CHARACTER_IMAGE_MAP:
                    display_name = None
                    
                game_state['text_renderer'].set_dialogue(dialogue_text, display_name)
                if DEBUG:
                    print(f"初期テキストを設定しました： {dialogue_text[:30]}...")
                    print(f"表示名: {display_name}")
                    print(f"アクティブキャラクター: {game_state['active_characters']}")

def _initialize_bgm(game_state):
    """BGMの初期化を行う（内部関数）"""
    bgm_manager = game_state['bgm_manager']
    dialogue_data = game_state['dialogue_data']
    
    # 会話データからBGMを探す
    bgm_from_dialogue = None
    for entry in dialogue_data:
        if len(entry) > 6 and entry[6]:  # BGM情報がある場合
            bgm_from_dialogue = entry[6]
            break
    
    # BGMの再生を試行
    if bgm_from_dialogue:
        if DEBUG:
            print(f"会話データからBGMを発見: {bgm_from_dialogue}")
        
        try:
            bgm_manager.play_bgm(bgm_from_dialogue)
            if DEBUG:
                print(f"BGM再生成功: {bgm_from_dialogue}")
            return True
        except Exception as e:
            print(f"指定されたBGMの再生に失敗: {bgm_from_dialogue}, エラー: {e}")
    
    # フォールバックBGMを試行
    if DEBUG:
        print("フォールバックBGMを試行中...")
    
    # デフォルトBGMリスト（優先度順）
    fallback_bgms = [
        bgm_manager.DEFAULT_BGM,
        bgm_manager.SECOND_BGM
    ]
    
    for bgm_file in fallback_bgms:
        if DEBUG:
            print(f"フォールバックBGMを試行: {bgm_file}")
        
        try:
            bgm_manager.play_bgm(bgm_file)
            if DEBUG:
                print(f"フォールバックBGM再生成功: {bgm_file}")
            return True
        except Exception as e:
            if DEBUG:
                print(f"フォールバックBGM再生失敗: {bgm_file}, エラー: {e}")
    
    # 全て失敗した場合
    print("警告: BGMの再生に失敗しました。サウンドなしで続行します。")
    if DEBUG:
        print("BGMファイルが存在するか、またはパスが正しいか確認してください。")
    
    return False

def change_bgm(game_state, bgm_filename, volume=0.1):
    """BGMを変更する（新しい関数）"""
    if not bgm_filename:
        if DEBUG:
            print("BGMファイル名が指定されていません")
        return False
    
    bgm_manager = game_state['bgm_manager']
    
    # 現在のBGMと同じ場合はスキップ
    if bgm_manager.current_bgm == bgm_filename:
        if DEBUG:
            print(f"同じBGMが再生中のためスキップ: {bgm_filename}")
        return True
    
    # BGMを変更
    try:
        bgm_manager.play_bgm(bgm_filename, volume)
        if DEBUG:
            print(f"BGMを変更しました: {bgm_filename}")
        return True
    except Exception as e:
        print(f"BGMの変更に失敗しました: {bgm_filename}, エラー: {e}")
        return False

def advance_dialogue(game_state):
    """次の対話に進む"""
    if game_state['current_paragraph'] >= len(game_state['dialogue_data']) - 1:
        if DEBUG:
            print("対話の終了に達しました")
        return False
    
    game_state['current_paragraph'] += 1
    current_dialogue = game_state['dialogue_data'][game_state['current_paragraph']]
    
    if len(current_dialogue) < 6:
        if DEBUG:
            print("対話データの形式が不正です")
        return False
    
    dialogue_text = current_dialogue[5]

    # キャラクター登場コマンドかどうかチェック
    if dialogue_text and dialogue_text.startswith("_CHARA_NEW_"):
        # キャラクター登場コマンドを処理
        parts = dialogue_text.split('_')
        if len(parts) >= 3:  # _CHARA_NEW_キャラクター名
            char_name = parts[2]
            if char_name in CHARACTER_IMAGE_MAP and char_name not in game_state['active_characters']:
                game_state['active_characters'].append(char_name)
                if DEBUG:
                    print(f"キャラクター '{char_name}' が登場しました")
            
        # キャラクター登場コマンドの場合は次の対話に進む
        return advance_dialogue(game_state)
    
    # キャラクター退場コマンドかどうかチェック
    elif dialogue_text and dialogue_text.startswith("_CHARA_HIDE_"):
        # キャラクター退場コマンドを処理
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
            
        # キャラクター退場コマンドの場合は次の対話に進む
        return advance_dialogue(game_state)

    # 移動コマンドかどうかチェック
    if dialogue_text and dialogue_text.startswith("_MOVE_"):
        # 移動コマンドを処理
        parts = dialogue_text.split('_')
        if len(parts) >= 5:  # _MOVE_left_top_duration
            char_name = current_dialogue[1]
            left = int(parts[2])
            top = int(parts[3])
            duration = int(parts[4]) if parts[4].isdigit() else 600
            move_character(game_state, char_name, left, top, duration)
            if DEBUG:
                print(f"移動コマンド実行: {char_name} -> ({left}, {top})")
        
        # 移動コマンドの場合は次の対話に進む
        return advance_dialogue(game_state)
    else:
        # 通常の対話テキスト
        display_name = current_dialogue[9] if len(current_dialogue) > 9 and current_dialogue[9] else current_dialogue[1]
        
        # 表示名の有効性をチェック
        if display_name and display_name not in CHARACTER_IMAGE_MAP:
            display_name = None
            
        game_state['text_renderer'].set_dialogue(dialogue_text, display_name)
        
        # キャラクターが新しい場合はアクティブリストに追加
        if current_dialogue[1] and current_dialogue[1] in CHARACTER_IMAGE_MAP:
            if current_dialogue[1] not in game_state['active_characters']:
                game_state['active_characters'].append(current_dialogue[1])
                if DEBUG:
                    print(f"新しいキャラクター '{current_dialogue[1]}' をアクティブリストに追加")
        
    return True

def move_character(game_state, character_name, target_x, target_y, duration=600):
    """キャラクターを指定位置に移動するアニメーションを設定する
    
    Parameters:
    -----------
    game_state : dict
        ゲーム状態の辞書
    character_name : str
        移動させるキャラクターの名前
    target_x : int
        目標X座標
    target_y : int
        目標Y座標
    duration : int
        アニメーション時間（ミリ秒）
    """
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

    """# 目標位置を計算（相対値の処理）
    final_target_x = target_x
    final_target_y = target_y"""
    
    # 目標位置を計算（相対値の処理）
    if isinstance(target_x, str):
        offset_x = int(target_x)
        final_target_x = current_x + offset_x
    elif isinstance(target_x, int):
        final_target_x = current_x + target_x
    else:
        final_target_x = current_x
    
    if isinstance(target_y, str):
        offset_y = int(target_y)
        final_target_y = current_y - offset_y
    elif isinstance(target_y, int):
        final_target_y = current_y + target_y
    else:
        final_target_y = current_y
    
    # アニメーション情報を設定
    start_time = pygame.time.get_ticks()
    game_state['character_anim'][character_name] = {
        'start_x': current_x,
        'start_y': current_y,
        'target_x': final_target_x,
        'target_y': final_target_y,
        'start_time': start_time,
        'duration': duration
    }
    
    # キャラクターをアクティブリストに追加（まだない場合）
    if character_name not in game_state['active_characters']:
        game_state['active_characters'].append(character_name)

    if DEBUG:
        print(f"移動アニメーション開始: {character_name} ({current_x}, {current_y}) -> ({final_target_x}, {final_target_y}) 時間: {duration}ms")

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
            # アニメーション情報を削除
            del game_state['character_anim'][char_name]
        else:
            # アニメーション進行中
            progress = elapsed / anim_data['duration']  # 0.0～1.0
            
            # 現在位置を線形補間で計算
            current_x = anim_data['start_x'] + (anim_data['target_x'] - anim_data['start_x']) * progress
            current_y = anim_data['start_y'] + (anim_data['target_y'] - anim_data['start_y']) * progress
            
            # 位置を更新
            game_state['character_pos'][char_name] = [int(current_x), int(current_y)]

def render_face_parts(game_state, char_name, brow_type, eye_type, mouth_type):
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
        brow_pos = (
            character_pos[0] + face_pos["brow"][0],
            character_pos[1] + face_pos["brow"][1]
        )
        screen.blit(images["brows"][brow_type], 
                  image_manager.center_part(images["brows"][brow_type], brow_pos))

    # 目を描画
    if eye_type and eye_type in images["eyes"]:
        eye_pos = (
            character_pos[0] + face_pos["eye"][0],
            character_pos[1] + face_pos["eye"][1]
        )
        screen.blit(images["eyes"][eye_type], 
                  image_manager.center_part(images["eyes"][eye_type], eye_pos))
    
    # 口を描画
    if mouth_type and mouth_type in images["mouths"]:
        mouth_pos = (
            character_pos[0] + face_pos["mouth"][0],
            character_pos[1] + face_pos["mouth"][1]
        )
        screen.blit(images["mouths"][mouth_type], 
                  image_manager.center_part(images["mouths"][mouth_type], mouth_pos))

def draw_characters(game_state):
    """画面上にキャラクターを描画する"""
    for char_name in game_state['active_characters']:
        if char_name in game_state['character_pos']:
            # キャラクター画像の取得
            char_img_name = CHARACTER_IMAGE_MAP.get(char_name, "girl1")
            if char_img_name not in game_state['images']["characters"]:
                if DEBUG:
                    print(f"警告: キャラクター画像 '{char_img_name}' が見つかりません")
                continue
            char_img = game_state['images']["characters"][char_img_name]

            # キャラクターの位置を取得
            x, y = game_state['character_pos'][char_name]
            
            # 画面に描画
            game_state['screen'].blit(char_img, (x, y))

            # 現在の会話データを取得して表情パーツを決定
            current_dialogue = game_state['dialogue_data'][game_state['current_paragraph']]
            
            # 現在のキャラクターが話し手である場合のみ、顔パーツを表示
            if len(current_dialogue) > 1 and current_dialogue[1] == char_name and game_state['show_face_parts']:
                # パーツ情報を取得
                eye_type = current_dialogue[2] if len(current_dialogue) > 2 else CHARACTER_DEFAULTS[char_name]["eye"]
                mouth_type = current_dialogue[3] if len(current_dialogue) > 3 else CHARACTER_DEFAULTS[char_name]["mouth"]
                brow_type = current_dialogue[4] if len(current_dialogue) > 4 else CHARACTER_DEFAULTS[char_name]["brow"]
                
                # 顔パーツを描画
                render_face_parts(game_state, char_name, brow_type, eye_type, mouth_type)