import pygame
import sys
import os
import json
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QFontDatabase

# PyQt5アプリケーションのグローバル変数
_qt_app = None

def init_qt_application():
    """PyQt5アプリケーションを初期化する"""
    global _qt_app
    if _qt_app is None:
        # 既存のQApplicationインスタンスがあるかチェック
        if QApplication.instance() is None:
            # コマンドライン引数を渡す（空のリストでも可）
            _qt_app = QApplication(sys.argv if sys.argv else [''])
            print("PyQt5 QApplication initialized")
        else:
            _qt_app = QApplication.instance()
            print("Using existing PyQt5 QApplication")
    return _qt_app

# PyQtを使用して画面サイズを取得
qt_app = init_qt_application()
screen = qt_app.primaryScreen()
screen_geometry = screen.geometry()
DISPLAY_WIDTH = screen_geometry.width()
DISPLAY_HEIGHT = screen_geometry.height()

# 仮想画面の基準解像度（全ての座標・サイズ計算の基準）
VIRTUAL_WIDTH = 1920
VIRTUAL_HEIGHT = 1080

# 実際のウィンドウサイズを16:9のアスペクト比に調整
# フルサイズ（ディスプレイの100%）でウィンドウを表示
WINDOW_WIDTH = DISPLAY_WIDTH  # 画面幅の100%（フルサイズ）
WINDOW_HEIGHT = DISPLAY_HEIGHT  # 画面高さの100%（フルサイズ）

# スケーリング係数を計算
SCALE_X = WINDOW_WIDTH / VIRTUAL_WIDTH
SCALE_Y = WINDOW_HEIGHT / VIRTUAL_HEIGHT
SCALE = max(SCALE_X, SCALE_Y)  # アスペクト比を維持するため小さい方を使用

# フルサイズの場合、ウィンドウ位置は左上角（0, 0）
X_POS = 0
Y_POS = 0

# 定数として設定（元のコードとの互換性のため）
SCREEN_WIDTH = WINDOW_WIDTH
SCREEN_HEIGHT = WINDOW_HEIGHT

# デバッグモード
DEBUG = True

# テキスト表示設定（仮想解像度1920x1080基準のピクセル値）
TEXT_COLOR = (255, 255, 255)
TEXT_COLOR_FEMALE = (255, 175, 227)
TEXT_BG_COLOR = (0, 0, 0, 100)
TEXT_START_X = 375  # 1文字分（約25px）左に移動
TEXT_START_Y = 765
NAME_START_X = 195  # 1文字分（約25px）右に移動
NAME_START_Y = TEXT_START_Y
TEXT_PADDING = 11

# テキスト表示設定（仮想座標をスケーリング）
def get_text_positions(screen):
    # 仮想座標を実際の画面座標にスケーリング
    name_1_pos = scale_pos(NAME_START_X, NAME_START_Y)
    speech_1_pos = scale_pos(TEXT_START_X, TEXT_START_Y)
    name_2_pos = scale_pos(NAME_START_X, NAME_START_Y + TEXT_LINE_SPACING)
    speech_2_pos = scale_pos(TEXT_START_X, TEXT_START_Y + TEXT_LINE_SPACING)
    line_height = int(TEXT_LINE_SPACING * SCALE)
    
    return {
        "name_1": name_1_pos,
        "speech_1": speech_1_pos,
        "name_2": name_2_pos,
        "speech_2": speech_2_pos,
        "line_height": line_height
    }

# UI要素の設定（仮想解像度1920x1080基準のピクセル値）
TEXTBOX_MARGIN_BOTTOM = 50   # テキストボックスの下マージン
TEXT_LINE_SPACING = 80       # 2つのテキスト行の間隔（1080 * 74 / 1000 = 79.92 → 80px）
AUTO_BUTTON_MARGIN_RIGHT = 401  # autoボタンの右マージン（1920 * 209 / 1000 = 401px）
SKIP_BUTTON_MARGIN_RIGHT = 258  # skipボタンの右マージン（1920 * 1345 / 10000 = 258px）
BUTTON_MARGIN_TOP = 704      # ボタンの上マージン（1080 * 647 / 1000 = 699px）

# 顔のパーツの相対位置を設定
FACE_POS = {
    "eye": (0.5, 0.5),
    "mouth": (0.5, 0.5),
    "brow": (0.5, 0.5)  # 眉毛の位置を追加
}

# キャラクター設定
CHARACTER_IMAGE_MAP = {
    "桃子": "girl1",
    "サナコ": "girl2",
    "烏丸神無": "girl1",
    "桔梗美鈴": "girl2", 
    "宮月深依里": "girl1",
    "伊織紅": "girl2"
}

# キャラクターの性別データを読み込む
CHARACTER_GENDERS = {}
try:
    # character_gender.jsonファイルを開き、内容を読み込む
    with open('character_gender.json', 'r', encoding='utf-8') as f:
        CHARACTER_GENDERS = json.load(f)
    if DEBUG:
        print(f"キャラクター性別データを読み込みました: {CHARACTER_GENDERS}")
except FileNotFoundError:
    if DEBUG:
        print("警告: character_gender.json が見つかりません。")
except json.JSONDecodeError:
    if DEBUG:
        print("警告: character_gender.json の解析に失敗しました。")

# キャラクターごとのデフォルトの表情設定
CHARACTER_DEFAULTS = {
    "桃子": {
        "eye": "eye1",
        "mouth": "mouth1",
        "brow": ""
    },
    "サナコ": {
        "eye": "eye1", 
        "mouth": "mouth1",
        "brow": ""
    },
    "烏丸神無": {
        "eye": "eye1",
        "mouth": "mouth1", 
        "brow": ""
    },
    "桔梗美鈴": {
        "eye": "eye1",
        "mouth": "mouth1",
        "brow": ""
    },
    "宮月深依里": {
        "eye": "eye1",
        "mouth": "mouth1",
        "brow": ""
    },
    "伊織紅": {
        "eye": "eye1",
        "mouth": "mouth1",
        "brow": ""
    }
}

# デフォルトの背景
DEFAULT_BACKGROUND = "school"

# デフォルトのBGM設定
DEFAULT_BGM_VOLUME = 0.1
DEFAULT_BGM_LOOP = True

def scale_pos(x, y):
    """仮想座標を実際の画面座標にスケーリング"""
    return int(x * SCALE), int(y * SCALE)

def scale_size(width, height):
    """仮想サイズを実際の画面サイズにスケーリング"""
    return int(width * SCALE), int(height * SCALE)

def get_textbox_position(screen, text_box):
    """テキストボックスの位置を計算する（仮想座標で計算してスケーリング）"""
    # テキストボックスのサイズは既にスケーリング済みなのでそのまま使用
    virtual_x = (VIRTUAL_WIDTH - 1632) // 2  # 仮想解像度でのテキストボックス幅
    virtual_y = VIRTUAL_HEIGHT - 352 - TEXTBOX_MARGIN_BOTTOM  # 仮想解像度でのテキストボックス高さ
    
    return scale_pos(virtual_x, virtual_y)

def get_ui_button_positions(screen):
    """UI要素のボタン位置を計算する（仮想座標で計算してスケーリング）"""
    auto_pos = scale_pos(VIRTUAL_WIDTH - AUTO_BUTTON_MARGIN_RIGHT, BUTTON_MARGIN_TOP)
    skip_pos = scale_pos(VIRTUAL_WIDTH - SKIP_BUTTON_MARGIN_RIGHT, BUTTON_MARGIN_TOP)
    
    return {
        "auto": auto_pos,
        "skip": skip_pos
    }

# Pygameの初期化時にウィンドウ位置を設定する関数
def set_window_position(x, y):
    import os
    os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (x, y)

# ゲーム初期化時に呼び出す
def init_game():
    init_qt_application()
    pygame.init()
    set_window_position(X_POS, Y_POS)
    
    # ウィンドウのタイトルを設定
    pygame.display.set_caption("ビジュアルノベル")
    
    # ウィンドウサイズを設定
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    
    print(f"Virtual resolution: {VIRTUAL_WIDTH}x{VIRTUAL_HEIGHT}")
    print(f"Window size: {SCREEN_WIDTH}x{SCREEN_HEIGHT} (16:9 ratio)")
    print(f"Scale factor: {SCALE:.3f}")
    print(f"Window position: {X_POS}, {Y_POS}")
    
    return screen

def update_screen_config(new_width, new_height):
    """画面サイズ設定を動的に更新する（イベント表示用）"""
    global SCREEN_WIDTH, SCREEN_HEIGHT, SCALE_X, SCALE_Y, SCALE
    
    # 新しい画面サイズを設定
    SCREEN_WIDTH = new_width
    SCREEN_HEIGHT = new_height
    
    # スケーリング係数を再計算
    SCALE_X = SCREEN_WIDTH / VIRTUAL_WIDTH
    SCALE_Y = SCREEN_HEIGHT / VIRTUAL_HEIGHT
    SCALE = min(SCALE_X, SCALE_Y)  # アスペクト比を維持
    
    print(f"画面設定を更新: {SCREEN_WIDTH}x{SCREEN_HEIGHT}, Scale: {SCALE:.3f}")

def restore_original_screen_config():
    """元の画面サイズ設定に戻す"""
    global SCREEN_WIDTH, SCREEN_HEIGHT, SCALE_X, SCALE_Y, SCALE
    
    # 元の設定に戻す
    SCREEN_WIDTH = WINDOW_WIDTH
    SCREEN_HEIGHT = WINDOW_HEIGHT
    SCALE_X = WINDOW_WIDTH / VIRTUAL_WIDTH
    SCALE_Y = WINDOW_HEIGHT / VIRTUAL_HEIGHT
    SCALE = min(SCALE_X, SCALE_Y)
    
    print(f"画面設定を元に戻しました: {SCREEN_WIDTH}x{SCREEN_HEIGHT}, Scale: {SCALE:.3f}")