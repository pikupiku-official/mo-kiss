import pygame
import tkinter as tk  # 画面サイズを取得するために一時的に使用
import sys
import os
import json
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QTextEdit
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QFontDatabase

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
TEXT_BG_COLOR = (0, 0, 0, 100)
TEXT_START_X = SCREEN_WIDTH / 6
TEXT_START_Y = SCREEN_HEIGHT * 11 / 15
NAME_START_X = SCREEN_WIDTH / 20
NAME_START_Y = TEXT_START_Y
TEXT_PADDING = 10

def init_fonts(self):
    # フォントの設定
    bold_font_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "fonts", "MPLUSRounded1c-Bold.ttf")
    medium_font_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "fonts", "MPLUSRounded1c-Regular.ttf")

    # Boldフォントの読み込み
    bold_font_id = QFontDatabase.addApplicationFont(bold_font_path)
    # Mediumフォントの読み込み
    medium_font_id = QFontDatabase.addApplicationFont(medium_font_path)

    if bold_font_id != -1 and medium_font_id != -1:
        bold_font_family = QFontDatabase.applicationFontFamilies(bold_font_id)[0]
        medium_font_family = QFontDatabase.applicationFontFamilies(medium_font_id)[0]
        
        # 人物名用のフォント（Bold）
        self.name_font = QFont(bold_font_family, 48)
        
        # セリフ用のフォント（Medium）
        self.speech_font = QFont(medium_font_family, 48)
    else:
        print("Warning: Rounded Mplus font not found, using system font")

    return {
        "default": pygame.font.SysFont(None, int(SCREEN_HEIGHT * 0.027)),
        "text": self.speech_font,
        "name": self.name_font
    }

# 顔のパーツの相対位置を設定
FACE_POS = {
    "eye": (0.49, 0.24),
    "mouth": (0.49, 0.31),
    "brow": (0.49, 0.18)  # 眉毛の位置を追加
}

# キャラクター設定
CHARACTER_IMAGE_MAP = {
    "桃子": "girl1",
    "サナコ": "girl2"
}

# キャラクターごとのデフォルトの表情設定
CHARACTER_DEFAULTS = {
    "桃子": {
        "eye": "eye1",
        "mouth": "mouth1",
        "brow": "brow1"  # 眉毛のデフォルト設定を追加
    },
    "サナコ": {
        "eye": "eye1",
        "mouth": "mouth1",
        "brow": "brow1"  # サナコのデフォルト設定も追加
    }
}

# デフォルトの背景
DEFAULT_BACKGROUND = "school"

# デフォルトのBGM設定
DEFAULT_BGM_VOLUME = 0.1
DEFAULT_BGM_LOOP = True

# Pygameの初期化時にウィンドウ位置を設定する関数
def set_window_position(x, y):
    import os
    os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (x, y)

# ゲーム初期化時に呼び出す
def init_game():
    pygame.init()
    set_window_position(X_POS, Y_POS)
    
    # ウィンドウのタイトルを設定
    pygame.display.set_caption("ビジュアルノベル")
    
    # ウィンドウサイズを設定
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    
    print(f"Window size: {SCREEN_WIDTH}x{SCREEN_HEIGHT} (16:9 ratio)")
    print(f"Window position: {X_POS}, {Y_POS}")
    
    return screen