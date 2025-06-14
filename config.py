import pygame
import tkinter as tk  # 画面サイズを取得するために一時的に使用
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

# tkinterを使用して画面サイズを取得
root = tk.Tk()
DISPLAY_WIDTH = root.winfo_screenwidth()
DISPLAY_HEIGHT = root.winfo_screenheight()
root.destroy()  # 役目を終えたらtkinterウィンドウを閉じる

# ウィンドウサイズを16:9のアスペクト比に調整
# ディスプレイの横幅または高さに合わせて、小さい方を基準にする
if DISPLAY_WIDTH / DISPLAY_HEIGHT > 16 / 9:  # ディスプレイが16:9より横長の場合
    # 高さを基準にする
    WINDOW_HEIGHT = int(DISPLAY_HEIGHT * 0.8)  # 画面高さの80%
    WINDOW_WIDTH = int(WINDOW_HEIGHT * 16 / 9)  # 16:9のアスペクト比で幅を計算
else:  # ディスプレイが16:9より縦長の場合
    # 幅を基準にする
    WINDOW_WIDTH = int(DISPLAY_WIDTH * 0.8)  # 画面幅の80%
    WINDOW_HEIGHT = int(WINDOW_WIDTH * 9 / 16)  # 16:9のアスペクト比で高さを計算

# 中央の位置を計算
X_POS = (DISPLAY_WIDTH - WINDOW_WIDTH) // 2
Y_POS = (DISPLAY_HEIGHT - WINDOW_HEIGHT) // 2

# 定数として設定（元のコードとの互換性のため）
SCREEN_WIDTH = WINDOW_WIDTH
SCREEN_HEIGHT = WINDOW_HEIGHT

# デバッグモード
DEBUG = True

# テキスト表示設定（ウィンドウサイズに合わせて調整）
TEXT_COLOR = (255, 255, 255)
TEXT_COLOR_FEMALE = (255, 175, 227)
TEXT_BG_COLOR = (0, 0, 0, 100)
TEXT_START_X = SCREEN_WIDTH / 4.7
TEXT_START_Y = SCREEN_HEIGHT * 705 / 1000
NAME_START_X = SCREEN_WIDTH / 9
NAME_START_Y = TEXT_START_Y
TEXT_PADDING = SCREEN_HEIGHT / 100

# テキスト表示設定
def get_text_positions(screen):
    return {
        "name_1": (NAME_START_X, NAME_START_Y),
        "speech_1": (TEXT_START_X, TEXT_START_Y),
        "name_2": (NAME_START_X, NAME_START_Y + TEXT_LINE_SPACING),
        "speech_2": (TEXT_START_X, TEXT_START_Y + TEXT_LINE_SPACING),
        "line_height": TEXT_LINE_SPACING
    }

# UI要素の設定
TEXTBOX_MARGIN_BOTTOM = SCREEN_HEIGHT * 50 / 1080  # テキストボックスの下マージン
TEXT_LINE_SPACING = SCREEN_HEIGHT * 74 / 1000  # 2つのテキスト行の間隔
AUTO_BUTTON_MARGIN_RIGHT = SCREEN_WIDTH * 209 / 1000  # autoボタンの右マージン
SKIP_BUTTON_MARGIN_RIGHT = SCREEN_WIDTH * 1345 / 10000  # skipボタンの右マージン
BUTTON_MARGIN_TOP = SCREEN_HEIGHT * 647 / 1000  # ボタンの上マージン

# 顔のパーツの相対位置を設定
FACE_POS = {
    "eye": (0.5, 0.5),
    "mouth": (0.5, 0.5),
    "brow": (0.5, 0.5)  # 眉毛の位置を追加
}

# キャラクター設定
CHARACTER_IMAGE_MAP = {
    "桃子": "girl1",
    "サナコ": "girl2"
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
    }
}

# デフォルトの背景
DEFAULT_BACKGROUND = "school"

# デフォルトのBGM設定
DEFAULT_BGM_VOLUME = 0.1
DEFAULT_BGM_LOOP = True

def get_textbox_position(screen, text_box):
    """テキストボックスの位置を計算する"""
    text_box_width = text_box.get_width()
    text_box_height = text_box.get_height()
    
    x_pos = (SCREEN_WIDTH - text_box_width) // 2
    y_pos = SCREEN_HEIGHT - text_box_height- TEXTBOX_MARGIN_BOTTOM
    
    return x_pos, y_pos

def get_ui_button_positions(screen):
    """UI要素のボタン位置を計算する"""
    
    return {
        "auto": (SCREEN_WIDTH - AUTO_BUTTON_MARGIN_RIGHT, BUTTON_MARGIN_TOP),
        "skip": (SCREEN_WIDTH - SKIP_BUTTON_MARGIN_RIGHT, BUTTON_MARGIN_TOP)
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
    
    print(f"Window size: {SCREEN_WIDTH}x{SCREEN_HEIGHT} (16:9 ratio)")
    print(f"Window position: {X_POS}, {Y_POS}")
    
    return screen