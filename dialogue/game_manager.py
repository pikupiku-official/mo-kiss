import pygame
from bgm_manager import BGMManager
from se_manager import SEManager
from .dialogue_loader import DialogueLoader
from image_manager import ImageManager
from .text_renderer import TextRenderer
from .backlog_manager import BacklogManager
from .choice_renderer import ChoiceRenderer
from .notification_manager import NotificationManager
from config import *
from .data_normalizer import normalize_dialogue_data

def initialize_game(dialogue_file="events/E001.ks"):
    """ゲームの初期化を行う
    
    Args:
        dialogue_file (str): 読み込む対話ファイルのパス
    """
    # Pygameを初期化
    init_qt_application()
    pygame.init()
    pygame.mixer.init()

    # 画面の設定
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("テスト")

    # 各マネージャーの初期化
    bgm_manager = BGMManager(DEBUG)
    se_manager = SEManager(DEBUG)
    dialogue_loader = DialogueLoader(DEBUG)
    image_manager = ImageManager(DEBUG)
    text_renderer = TextRenderer(screen, DEBUG)
    choice_renderer = ChoiceRenderer(screen, DEBUG)
    notification_manager = NotificationManager(screen, DEBUG)
    
    # バックログマネージャーの初期化
    backlog_fonts = {
        "default": text_renderer.fonts["default"],
        "text": text_renderer.fonts["text"],      # PyQt5フォント
        "name": text_renderer.fonts["name"]       # PyQt5フォント
    }
    backlog_manager = BacklogManager(screen, text_renderer.fonts, DEBUG)
    
    # TextRendererにBacklogManagerを設定
    text_renderer.set_backlog_manager(backlog_manager)
    
    # DialogueLoaderに通知システムを設定
    dialogue_loader.notification_system = notification_manager

    # 画像パスのスキャンと必須画像のみロード
    try:
        print("画像パススキャン中...")
        image_manager.scan_image_paths(SCREEN_WIDTH, SCREEN_HEIGHT)
        print("必須画像ロード中...")
        images = image_manager.load_essential_images(SCREEN_WIDTH, SCREEN_HEIGHT)
    except Exception as e:
        print(f"画像の初期化に失敗しました： {e}")
        return None

    # 会話データの読み込みと正規化（最適化）
    try:
        print("会話データ読み込み中...")
        raw_dialogue_data = dialogue_loader.load_dialogue_from_ks(dialogue_file)
        
        if DEBUG:
            print(f"game_manager.py: ロードされた生データ数: {len(raw_dialogue_data) if raw_dialogue_data else 0}")
        
        if raw_dialogue_data and len(raw_dialogue_data) > 0:
            if DEBUG:
                print(f"game_manager.py: 生データの最初: {raw_dialogue_data[0]}")
            dialogue_data = normalize_dialogue_data(raw_dialogue_data)
            
            if DEBUG:
                print(f"game_manager.py: 正規化後のデータ数: {len(dialogue_data) if dialogue_data else 0}")
                if dialogue_data and len(dialogue_data) > 0:
                    print(f"game_manager.py: 正規化後の最初: {dialogue_data[0]}")
            
            if not dialogue_data:
                print("game_manager.py: 警告 - 正規化後のデータが空です")
                dialogue_data = get_default_normalized_dialogue()
            else:
                # キャラクターを事前ロード
                try:
                    print("キャラクター事前ロード中...")
                    image_manager.preload_characters_from_dialogue(dialogue_data)
                    print("キャラクター事前ロード完了")
                except Exception as e:
                    print(f"キャラクター事前ロードエラー（続行）: {e}")
                    if DEBUG:
                        import traceback
                        traceback.print_exc()
        else:
            print("game_manager.py: 警告 - 生データが空のためデフォルトデータを使用")
            dialogue_data = get_default_normalized_dialogue()
            
    except Exception as e:
        print(f"対話データの読み込みに失敗しました: {e}")
        if DEBUG:
            import traceback
            traceback.print_exc()
        dialogue_data = get_default_normalized_dialogue()

    # キャラクター画像は元サイズで表示（自動スケーリング無効）
    if "characters" in image_manager.image_paths and image_manager.image_paths["characters"]:
        first_char_key = list(image_manager.image_paths["characters"].keys())[0]
        print(f"キャラクター画像確認: {first_char_key} (元サイズで表示)")
    else:
        print("警告: キャラクター画像が見つかりません。")

    # キャラクター関連の初期化（デフォルトシステム不要）
    character_pos = {}
    character_anim = {}
    character_zoom = {}
    character_expressions = {}
    # CHARACTER_IMAGE_MAPとCHARACTER_DEFAULTSは削除済み

    # 顔パーツの位置は各キャラクターの実際のサイズに基づいて動的に計算される

    # 背景の位置とズーム管理を追加
    background_state = {
        'current_bg': None,  # 初期背景はなし
        'pos': [0, 0],  # 背景の位置（オフセット）
        'zoom': 1.0,    # 背景のズーム倍率
        'anim': None    # アニメーション情報
    }

    # まばたき関連の初期化
    character_blink_enabled = {}  # キャラクターごとのまばたき有効フラグ
    character_blink_state = {}    # キャラクターごとのまばたき状態
    character_blink_timers = {}   # キャラクターごとのまばたきタイマー
    
    # フェード関連の初期化
    fade_state = {
        'type': None,      # 'fadeout' or 'fadein'
        'start_time': 0,   # アニメーション開始時刻
        'duration': 0,     # アニメーション時間（ms）
        'color': (0, 0, 0), # フェード色
        'alpha': 0,        # 現在のアルファ値
        'active': False    # アクティブかどうか
    }
    
    # ゲーム状態の初期化
    game_state = {
        'screen': screen,
        'bgm_manager': bgm_manager,
        'se_manager': se_manager,
        'dialogue_loader': dialogue_loader,
        'image_manager': image_manager,
        'text_renderer': text_renderer,
        'choice_renderer': choice_renderer,
        'backlog_manager': backlog_manager,
        'notification_manager': notification_manager,
        'images': images,
        'dialogue_data': dialogue_data,
        'character_pos': character_pos,
        'character_anim': character_anim,
        'character_zoom': character_zoom,
        'character_expressions': character_expressions,
        'character_blink_enabled': character_blink_enabled,
        'character_blink_state': character_blink_state,
        'character_blink_timers': character_blink_timers,
        'fade_state': fade_state,
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
    
    # 最初のSEを再生
    se_success = _initialize_se(game_state)
    if DEBUG:
        print(f"SE初期化結果: {'成功' if se_success else '失敗'}") 
    
    # 最初のテキストを設定
    if game_state['dialogue_data']:
        # 最初のエントリから処理を開始
        game_state['current_paragraph'] = -1  # advance_dialogueで0になる
        from dialogue.scenario_manager import advance_dialogue
        if DEBUG:
            print("=== 最初の対話を開始 ===")
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
        if len(entry) > 7 and entry[7]:  # BGM情報がある場合（インデックス7）
            bgm_from_dialogue = entry[7]
            break
    
    # BGMの再生を試行
    if bgm_from_dialogue:
        if DEBUG:
            print(f"会話データからBGMを発見: {bgm_from_dialogue}")
        
        # ファイル名を正規化（拡張子自動補完）
        actual_bgm_filename = bgm_manager.get_bgm_for_scene(bgm_from_dialogue)
        
        if actual_bgm_filename:
            try:
                bgm_manager.play_bgm(actual_bgm_filename)
                if DEBUG:
                    print(f"BGM再生成功: {actual_bgm_filename}")
                return True
            except Exception as e:
                print(f"指定されたBGMの再生に失敗: {actual_bgm_filename}, エラー: {e}")
        else:
            if DEBUG:
                print(f"無効なBGMファイル名: {bgm_from_dialogue}")
    
    # BGMが指定されていない場合はサウンドなしで続行
    if DEBUG:
        print("BGMが指定されていません。サウンドなしで続行します。")
    
    return False

def _initialize_se(game_state):
    """SEの初期化を行う（内部関数）"""
    se_manager = game_state['se_manager']
    dialogue_data = game_state['dialogue_data']
    
    # 会話データからSEを探す
    se_from_dialogue = None
    for entry in dialogue_data:
        if len(entry) > 8 and entry[8]:  # SE情報がある場合（インデックス8）
            se_from_dialogue = entry[8]
            break
    
    # SEの再生を試行
    if se_from_dialogue:
        if DEBUG:
            print(f"会話データからSEを発見: {se_from_dialogue}")
        
        # ファイル名を正規化（拡張子自動補完）
        actual_se_filename = se_manager.get_se_for_scene(se_from_dialogue)
        
        if actual_se_filename:
            try:
                se_manager.play_se(actual_se_filename)
                if DEBUG:
                    print(f"SE再生成功: {actual_se_filename}")
                return True
            except Exception as e:
                print(f"指定されたSEの再生に失敗: {actual_se_filename}, エラー: {e}")
        else:
            if DEBUG:
                print(f"無効なSEファイル名: {se_from_dialogue}")
    
    # SEが指定されていない場合はサウンドなしで続行
    if DEBUG:
        print("SEが指定されていません。サウンドなしで続行します。")
    
    return False

def change_bgm(game_state, bgm_filename, volume=0.1):
    """BGMを変更する"""
    if not bgm_filename:
        if DEBUG:
            print("BGMファイル名が指定されていません")
        return False
    
    bgm_manager = game_state['bgm_manager']
    
    # ファイル名を正規化（拡張子自動補完）
    actual_bgm_filename = bgm_manager.get_bgm_for_scene(bgm_filename)
    
    if not actual_bgm_filename:
        if DEBUG:
            print(f"無効なBGMファイル名: {bgm_filename}")
        return False
    
    # 現在のBGMと同じ場合はスキップ
    if bgm_manager.current_bgm == actual_bgm_filename:
        if DEBUG:
            print(f"同じBGMが再生中のためスキップ: {actual_bgm_filename}")
        return True
    
    # BGMを変更
    try:
        bgm_manager.play_bgm(actual_bgm_filename, volume)
        if DEBUG:
            print(f"BGMを変更しました: {actual_bgm_filename}")
        return True
    except Exception as e:
        print(f"BGMの変更に失敗しました: {actual_bgm_filename}, エラー: {e}")
        return False

def change_se(game_state, se_filename, volume=0.7):
    """SEを再生する"""
    if not se_filename:
        if DEBUG:
            print("SEファイル名が指定されていません")
        return False
    
    se_manager = game_state['se_manager']
    
    # ファイル名を正規化（拡張子自動補完）
    actual_se_filename = se_manager.get_se_for_scene(se_filename)
    
    if not actual_se_filename:
        if DEBUG:
            print(f"無効なSEファイル名: {se_filename}")
        return False
    
    # SEを再生
    try:
        se_manager.play_se(actual_se_filename, volume)
        if DEBUG:
            print(f"SEを再生しました: {actual_se_filename}")
        return True
    except Exception as e:
        print(f"SEの再生に失敗しました: {actual_se_filename}, エラー: {e}")
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
    
    # BGM処理（インデックス7）
    if len(entry) > 7 and entry[7]:
        bgm_filename = entry[7]
        if bgm_filename != 'none' and bgm_filename.strip():
            change_bgm(game_state, bgm_filename)
            if DEBUG:
                print(f"BGM変更: {bgm_filename}")
    
    # SE処理（インデックス8）
    if len(entry) > 8 and entry[8]:
        se_filename = entry[8]
        if se_filename != 'none' and se_filename.strip():
            change_se(game_state, se_filename)
            if DEBUG:
                print(f"SE再生: {se_filename}")
    
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
    if DEBUG:
        print("警告: get_default_normalized_dialogue()が呼ばれました")
        import traceback
        traceback.print_stack()

    return [
        [None, "桃子", "eye1", "mouth1", "brow1", 
         "デフォルトのテキストです。", None, 0.1, True, "桃子", False],
        [None, "桃子", "eye1", "mouth1", "brow1", 
         "デフォルトのテキストです。", None, 0.1, True, "桃子", False]
    ]
