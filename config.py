import pygame

# 画面サイズの設定
SCREEN_WIDTH = 1600
SCREEN_HEIGHT = 900

# デバッグモード
DEBUG = True

# テキスト表示設定
TEXT_COLOR = (255, 255, 255)
TEXT_BG_COLOR = (0, 0, 0, 100)
TEXT_START_X = SCREEN_WIDTH / 20
TEXT_START_Y = SCREEN_HEIGHT * 11 / 15
NAME_START_Y = TEXT_START_Y - 65
TEXT_PADDING = 10
TEXT_BOX_WIDTH = SCREEN_WIDTH * 9 / 10
TEXT_MAX_WIDTH = TEXT_BOX_WIDTH - 2 * TEXT_PADDING

# インジケーター設定
NEXT_INDICATOR_COLOR = (255, 255, 255)
NEXT_INDICATOR_POS = (SCREEN_WIDTH * 9 / 10, SCREEN_HEIGHT * 9 / 10)
NEXT_INDICATOR_TEXT = "▼"

# フォント設定
def init_fonts():
    return {
        "default": pygame.font.SysFont(None, 24),
        "text": pygame.font.SysFont('meiryo', 50),
        "name": pygame.font.SysFont('meiryo', 50)
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
    }
}

# デフォルトの背景
DEFAULT_BACKGROUND = "school"

# デフォルトのBGM設定
DEFAULT_BGM_VOLUME = 0.1
DEFAULT_BGM_LOOP = True 