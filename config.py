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
SCALE = min(SCALE_X, SCALE_Y)  # アスペクト比を維持するため小さい方を使用

# フルサイズの場合、ウィンドウ位置は左上角（0, 0）
X_POS = 0
Y_POS = 0

# 定数として設定（元のコードとの互換性のため）
SCREEN_WIDTH = WINDOW_WIDTH
SCREEN_HEIGHT = WINDOW_HEIGHT

# デバッグモード（パフォーマンス向上のためFalseに）
DEBUG = False

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
TEXTBOX_MARGIN_BOTTOM = 50
TEXT_LINE_SPACING = 80
AUTO_BUTTON_MARGIN_RIGHT = 394
SKIP_BUTTON_MARGIN_RIGHT = 249
BUTTON_MARGIN_TOP = 703

# 顔のパーツの相対位置を設定
FACE_POS = {
    "eye": (0.5, 0.5),
    "mouth": (0.5, 0.5),
    "brow": (0.5, 0.5),  # 眉毛の位置を追加
    "cheek": (0.5, 0.5)  # 頬の位置を追加
}

# CHARACTER_IMAGE_MAPを削除（ファイル名直接使用）
# デフォルト用のマッピングは不要

# キャラクターの性別データを読み込む
CHARACTER_GENDERS = {}
try:
    # character_gender.jsonファイルを開き、内容を読み込む（絶対パス使用）
    gender_file_path = os.path.join(os.path.dirname(__file__), 'character_gender.json')
    with open(gender_file_path, 'r', encoding='utf-8') as f:
        CHARACTER_GENDERS = json.load(f)
    if DEBUG:
        print(f"キャラクター性別データを読み込みました: {CHARACTER_GENDERS}")
except FileNotFoundError:
    if DEBUG:
        print(f"警告: character_gender.json が見つかりません。パス: {gender_file_path}")
except json.JSONDecodeError:
    if DEBUG:
        print("警告: character_gender.json の解析に失敗しました。")

# CHARACTER_DEFAULTSも削除（デフォルトシステム不要）
# 全てファイル名直接指定で使用

# DEFAULT_BACKGROUNDは削除（背景は明示的に指定された場合のみ表示）

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
    # Pygameの最適化設定
    pygame.mixer.pre_init(frequency=22050, size=-16, channels=2, buffer=1024)
    pygame.init()
    set_window_position(X_POS, Y_POS)
    
    # ウィンドウのタイトルを設定
    pygame.display.set_caption("ビジュアルノベル")
    
    # 全画面表示でウィンドウサイズを設定
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
    
    # デバッグ出力削除（パフォーマンス向上）
    
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