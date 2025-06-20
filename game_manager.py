import pygame
from bgm_manager import BGMManager
from dialogue_loader import DialogueLoader
from image_manager import ImageManager
from text_renderer import TextRenderer
from backlog_manager import BacklogManager
from choice_renderer import ChoiceRenderer
from config import *
from data_normalizer import normalize_dialogue_data

def initialize_game():
    """ゲームの初期化を行う"""
    # Pygameを初期化
    init_qt_application()
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
    choice_renderer = ChoiceRenderer(screen, DEBUG)
    
    # バックログマネージャーの初期化
    backlog_fonts = {
        "default": text_renderer.fonts["default"],
        "text": text_renderer.fonts["text"],      # PyQt5フォント
        "name": text_renderer.fonts["name"]       # PyQt5フォント
    }
    backlog_manager = BacklogManager(screen, text_renderer.fonts, DEBUG)
    
    # TextRendererにBacklogManagerを設定
    text_renderer.set_backlog_manager(backlog_manager)

    # 画像の読み込み
    try:
        images = image_manager.load_all_images(SCREEN_WIDTH, SCREEN_HEIGHT)
    except Exception as e:
        print(f"画像の読み込みに失敗しました： {e}")
        return None

    # 会話データの読み込みと正規化
    try:
        raw_dialogue_data = dialogue_loader.load_dialogue_from_ks("events/E001_test.ks")
        print(f"game_manager.py: ロードされた生データ数: {len(raw_dialogue_data) if raw_dialogue_data else 0}")
        
        if raw_dialogue_data and len(raw_dialogue_data) > 0:
            print(f"game_manager.py: 生データの最初: {raw_dialogue_data[0]}")
            dialogue_data = normalize_dialogue_data(raw_dialogue_data)
            print(f"game_manager.py: 正規化後のデータ数: {len(dialogue_data) if dialogue_data else 0}")
            
            if dialogue_data and len(dialogue_data) > 0:
                print(f"game_manager.py: 正規化後の最初: {dialogue_data[0]}")
            else:
                print("game_manager.py: 警告 - 正規化後のデータが空です")
                dialogue_data = get_default_normalized_dialogue()
        else:
            print("game_manager.py: 警告 - 生データが空のためデフォルトデータを使用")
            dialogue_data = get_default_normalized_dialogue()
            
    except Exception as e:
        print(f"対話データの読み込みに失敗しました: {e}")
        import traceback
        traceback.print_exc()
        dialogue_data = get_default_normalized_dialogue()

    # キャラクター画像のサイズを取得
    # 利用可能な最初のキャラクター画像を使用
    char_width = 100
    char_height = 100
    if images["characters"]:
        first_char_key = list(images["characters"].keys())[0]
        char_width = images["characters"][first_char_key].get_width()
        char_height = images["characters"][first_char_key].get_height()
        print(f"キャラクター画像サイズ取得: {first_char_key} ({char_width}x{char_height})")
    else:
        print("警告: キャラクター画像が見つかりません。デフォルトサイズを使用します。")

    # キャラクター関連の初期化
    character_pos = {}
    character_anim = {}
    character_zoom = {}
    character_expressions = {}
    
    for char_name in CHARACTER_IMAGE_MAP.keys():
        character_zoom[char_name] = 1.0  # デフォルトは等倍
        character_expressions[char_name] = {
            'eye': CHARACTER_DEFAULTS[char_name]['eye'],
            'mouth': CHARACTER_DEFAULTS[char_name]['mouth'],
            'brow': CHARACTER_DEFAULTS[char_name]['brow']
        }

    # 顔のパーツの相対位置を設定
    face_pos = {
        "eye": (char_width * FACE_POS["eye"][0], char_height * FACE_POS["eye"][1]),
        "mouth": (char_width * FACE_POS["mouth"][0], char_height * FACE_POS["mouth"][1]),
        "brow": (char_width * FACE_POS["brow"][0], char_height * FACE_POS["brow"][1])
    }

    # 背景の位置とズーム管理を追加
    background_state = {
        'current_bg': DEFAULT_BACKGROUND,
        'pos': [0, 0],  # 背景の位置（オフセット）
        'zoom': 1.0,    # 背景のズーム倍率
        'anim': None    # アニメーション情報
    }

    # ゲーム状態の初期化
    game_state = {
        'screen': screen,
        'bgm_manager': bgm_manager,
        'dialogue_loader': dialogue_loader,
        'image_manager': image_manager,
        'text_renderer': text_renderer,
        'choice_renderer': choice_renderer,
        'backlog_manager': backlog_manager,
        'images': images,
        'dialogue_data': dialogue_data,
        'character_pos': character_pos,
        'character_anim': character_anim,
        'character_zoom': character_zoom,
        'character_expressions': character_expressions,
        'face_pos': face_pos,
        'background_state': background_state,
        'show_face_parts': True,
        'show_text': True,
        'current_paragraph': 0,
        'active_characters': [],
        'last_dialogue_logged': False
    }

    return game_state

def initialize_first_scene(game_state):
    """最初のシーンを初期化する"""
    print(f"game_manager.py initialize_first_scene: 対話データ数: {len(game_state['dialogue_data'])}")
    
    if not game_state['dialogue_data']:
        print("会話データがありません")
        return
    
    if len(game_state['dialogue_data']) > 0:
        print(f"game_manager.py initialize_first_scene: 最初のデータ: {game_state['dialogue_data'][0]}")

    if not game_state['dialogue_data']:
        print("会話データがありません")
        return
    
    # 最初のBGMを再生
    bgm_success = _initialize_bgm(game_state)
    if DEBUG:
        print(f"BGM初期化結果: {'成功' if bgm_success else '失敗'}") 
    
    # 最初のテキストを設定
    if game_state['dialogue_data']:
        # 最初のエントリから処理を開始
        game_state['current_paragraph'] = -1  # advance_dialogueで0になる
        from scenario_manager import advance_dialogue
        advance_dialogue(game_state)
        
        # 最初のテキストのバックログ追加フラグをリセット（重複を避けるため、自動追加に任せる）
        if game_state['text_renderer'].current_text:
            game_state['text_renderer'].backlog_added_for_current = False
            if DEBUG:
                print(f"[BACKLOG] 最初のテキストのバックログ追加フラグをリセット")

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
    """BGMを変更する"""
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

def handle_background_command(game_state, dialogue_text):
    """背景コマンドを処理し、スクロール状態をリセット"""
    if "_BG_SHOW_" in dialogue_text or "_BG_MOVE_" in dialogue_text:
        # 背景変更時にスクロール状態をリセット
        if DEBUG:
            print(f"背景コマンド検出、スクロール状態をリセット: {dialogue_text}")
        game_state['text_renderer'].on_background_change()
        return True
    return False

def handle_character_command(game_state, dialogue_text):
    """キャラクターコマンドを処理"""
    if "_CHARA_HIDE_" in dialogue_text:
        # キャラクター退場時の処理
        if DEBUG:
            print(f"キャラクター退場コマンド検出: {dialogue_text}")
        return True
    elif "_CHARA_NEW_" in dialogue_text:
        # キャラクター登場時の処理
        if DEBUG:
            print(f"キャラクター登場コマンド検出: {dialogue_text}")
        return True
    return False

def process_dialogue_entry(game_state, entry):
    """対話エントリーを処理する統合関数"""
    if not entry or len(entry) < 6:
        if DEBUG:
            print("無効な対話エントリー")
        return False
    
    dialogue_text = entry[5]  # テキスト部分
    
    # コマンド系の処理
    if dialogue_text and dialogue_text.startswith("_"):
        # 背景コマンドの場合
        if handle_background_command(game_state, dialogue_text):
            return True
        
        # キャラクターコマンドの場合
        if handle_character_command(game_state, dialogue_text):
            return True
        
        # その他のコマンド（移動など）
        return True
    
    # 通常の対話の場合
    if dialogue_text and not dialogue_text.startswith("_"):
        character_name = entry[1] if len(entry) > 1 else None
        should_scroll = entry[10] if len(entry) > 10 else False
        background = entry[0] if len(entry) > 0 else None
        
        # アクティブキャラクターのリストを取得
        active_characters = list(game_state.get('active_characters', {}).keys()) if isinstance(game_state.get('active_characters'), dict) else game_state.get('active_characters', [])
        
        # テキストレンダラーに対話を設定
        game_state['text_renderer'].set_dialogue(
            dialogue_text, 
            character_name, 
            should_scroll, 
            background, 
            active_characters
        )
        
        if DEBUG:
            print(f"対話設定: speaker={character_name}, scroll={should_scroll}, bg={background}")
        
        return True
    
    return False

def reset_scroll_state_for_scene_change(game_state):
    """シーン変更時のスクロール状態リセット"""
    if DEBUG:
        print("シーン変更によるスクロール状態リセット")
    game_state['text_renderer'].on_scene_change()

def get_active_characters_list(game_state):
    """アクティブキャラクターのリストを取得"""
    active_chars = game_state.get('active_characters', [])
    if isinstance(active_chars, dict):
        return list(active_chars.keys())
    return active_chars if active_chars else []

def get_default_normalized_dialogue():
    """デフォルトの正規化された対話データを返す"""
    print("警告: get_default_normalized_dialogue()が呼ばれました")
    import traceback
    traceback.print_stack()

    return [
        [DEFAULT_BACKGROUND, "桃子", "eye1", "mouth1", "brow1", 
         "デフォルトのテキストです。", "maou_bgm_8bit29.mp3", 0.1, True, "桃子", False],
        [DEFAULT_BACKGROUND, "桃子", "eye1", "mouth1", "brow1", 
         "デフォルトのテキストです。", "maou_bgm_8bit29.mp3", 0.1, True, "桃子", False]
    ]