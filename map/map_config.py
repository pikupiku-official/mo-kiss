import pygame
from enum import Enum
from typing import List, Dict, Tuple

# 初期化
pygame.init()

# フルサイズウィンドウ設定
from PyQt5.QtWidgets import QApplication
import sys

# 画面サイズを取得してフルサイズに設定
if QApplication.instance() is None:
    _temp_app = QApplication(sys.argv if sys.argv else [''])
    screen = _temp_app.primaryScreen()
    screen_geometry = screen.geometry()
    SCREEN_WIDTH = screen_geometry.width()
    SCREEN_HEIGHT = screen_geometry.height()
else:
    app = QApplication.instance()
    screen = app.primaryScreen()
    screen_geometry = screen.geometry()
    SCREEN_WIDTH = screen_geometry.width()
    SCREEN_HEIGHT = screen_geometry.height()
FPS = 60

# マップタイプの定義
class MapType(Enum):
    WEEKDAY = "weekday"    # 平日（学校のみ）
    WEEKEND = "weekend"    # 休日（街のみ）

# 時間進行の定義
class TimeSlot(Enum):
    MORNING = 0   # 朝
    NOON = 1      # 昼
    NIGHT = 2     # 夜

# 高品質カラーパレット
ADVANCED_COLORS = {
    # 時間帯別空の色
    'sky_colors': {
        TimeSlot.MORNING: [(135, 206, 250), (255, 218, 185), (255, 228, 225)],
        TimeSlot.NOON: [(87, 205, 249), (255, 255, 255), (220, 240, 255)],
        TimeSlot.NIGHT: [(25, 25, 112), (72, 61, 139), (123, 104, 238)]
    },
    
    # 建物色
    'school_building': (248, 245, 240),
    'school_roof': (169, 50, 38),
    'cafe_color': (205, 133, 63),
    'station_color': (176, 196, 222),
    'shop_colors': [(255, 182, 193), (152, 251, 152), (173, 216, 230)],
    
    # 地形色
    'grass': (34, 139, 34),
    'water': (64, 164, 223),
    'road': (64, 64, 64),
    'sidewalk': (192, 192, 192),
    
    # UI色
    'ui_glass': (255, 255, 255, 180),
    'ui_border': (70, 130, 180),
    'text_color': (33, 37, 41),
    'girl_icon': (255, 20, 147),
    'event_glow': (255, 215, 0),
}

# ヒロイン情報
HEROINES = [
    {
        'name': '烏丸神無',
        'description': 'ギャル・水泳部',
        'image_file': 'Kanna.jpg'
    },
    {
        'name': '桔梗美鈴',
        'description': '先輩・元吹部',
        'image_file': 'Misuzu.jpg'
    },
    {
        'name': '愛沼桃子',
        'description': 'ムードメーカー・バド部',
        'image_file': 'Momoko.jpeg'
    },
    {
        'name': '舞田沙那子',
        'description': 'つっけんどん先輩',
        'image_file': 'Sanako.jpg'
    },
    {
        'name': '宮月深依里',
        'description': 'ミステリアス同級生',
        'image_file': 'Miyori.jpg'
    },
    {
        'name': '伊織紅',
        'description': '母性的後輩・弓道部',
        'image_file': 'Kou.png'
    }
]

# マップ上の場所情報
SCHOOL_LOCATIONS = {
    'classroom': {'pos': (800, 300), 'label': '教室'},
    'library': {'pos': (600, 350), 'label': '図書館'},
    'gym': {'pos': (1200, 450), 'label': '体育館'},
    'shop': {'pos': (400, 500), 'label': '購買部'},
    'rooftop': {'pos': (800, 200), 'label': '屋上'},
    'school_gate': {'pos': (800, 650), 'label': '学校正門'}
}

TOWN_LOCATIONS = {
    'park': {'pos': (300, 300), 'label': '公園'},
    'station': {'pos': (1300, 400), 'label': '駅前'},
    'shopping': {'pos': (800, 350), 'label': '商店街'},
    'cafe': {'pos': (600, 500), 'label': 'カフェ'}
}

# フォント設定
FONT_SIZES = {
    'title': 32,
    'large': 24,
    'medium': 18,
    'small': 14
}

# ゲーム期間設定
GAME_START_DATE = (1999, 5, 31)
GAME_END_DATE = (1999, 7, 1)

# BGM設定 - 時間帯・マップタイプ・特定日付別
# 構造: {map_type: {time_slot: bgm_filename}}
MAP_BGM_CONFIG = {
    'weekday': {
        '朝': 'subete_no_hajimari.mp3',
        '昼': 'subete_no_hajimari.mp3',
        '放課後': 'subete_no_hajimari.mp3',
    },
    'weekend': {
        '朝': 'subete_no_hajimari.mp3',
        '昼': 'subete_no_hajimari.mp3',
        '放課後': 'subete_no_hajimari.mp3',
    },
    'default': 'subete_no_hajimari.mp3'  # デフォルトBGM
}

# 特定日付のBGM設定（優先度高）
# 構造: {(month, day): bgm_filename}
SPECIAL_DATE_BGM = {
    # 例: (6, 1): 'special_event.mp3',
    # 例: (6, 15): 'midterm_exam.mp3',
}

# マップ背景画像設定 - 時間帯・マップタイプ別
# 構造: {map_type: {time_slot: background_filename}}
MAP_BACKGROUND_CONFIG = {
    'weekday': {
        '朝': None,  # None = プログラム生成背景
        '昼': None,
        '放課後': None,
    },
    'weekend': {
        '朝': None,
        '昼': None,
        '放課後': None,
    },
    'default': None  # デフォルト背景
}

# 特定日付の背景画像設定（優先度高）
# 構造: {(month, day): background_filename}
SPECIAL_DATE_BACKGROUND = {
    # 例: (6, 1): 'opening_ceremony.png',
}