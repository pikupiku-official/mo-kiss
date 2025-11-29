import pygame
from enum import Enum

# カラーパレット（レトロゲーム風）
COLORS = {
    # 背景色
    'bg_main': (245, 220, 220),  # 薄いピンク
    'bg_panel': (255, 240, 245),  # より薄いピンク
    
    # ボタン色
    'btn_normal': (100, 149, 237),  # コーンフラワーブルー
    'btn_hover': (72, 118, 255),   # より濃いブルー
    'btn_pressed': (65, 105, 225), # ロイヤルブルー
    'btn_text': (255, 255, 255),   # 白
    
    # 設定ボタン（緑系）
    'btn_green_normal': (60, 179, 113),  # ミディアムシーグリーン
    'btn_green_hover': (46, 139, 87),    # シーグリーン
    'btn_green_pressed': (34, 139, 34),  # フォレストグリーン
    
    # テキスト色
    'text_main': (70, 70, 70),     # ダークグレー
    'text_title': (139, 69, 19),   # サドルブラウン
    'text_white': (255, 255, 255), # 白
    'text_dark': (50, 50, 50),     # ダークグレー（テキスト入力用）
    
    # 枠線色
    'border_light': (200, 200, 200),  # ライトグレー
    'border_dark': (100, 100, 100),   # ダークグレー
    
    # スライダー色
    'slider_bg': (200, 200, 200),     # スライダー背景
    'slider_active': (60, 179, 113),  # アクティブ部分
    'slider_handle': (255, 255, 255), # ハンドル
}

# メニューの状態
class MenuState(Enum):
    MAIN = "main"
    SETTINGS = "settings"
    SAVE = "save"
    LOAD = "load"

# フォントサイズ（大きく調整）
FONT_SIZES = {
    'title': 54,
    'large': 42,
    'medium': 32,
    'small': 24
}

# ボタンの設定（大きく調整）
BUTTON_CONFIG = {
    'width': 300,
    'height': 70,
    'margin': 30,
    'border_radius': 15
}

# スライダーの設定（大きく調整）
SLIDER_CONFIG = {
    'width': 300,
    'height': 30,
    'handle_size': 24,
    'min_value': 0,
    'max_value': 100
}

# レイアウト設定（4:3コンテンツ基準 - 1440x1080）
LAYOUT = {
    'title_y': 90,  # 120 * 0.75
    'main_menu_start_y': 225,  # 300 * 0.75
    'settings_panel_x': 375,  # 500 * 0.75
    'settings_panel_y': 210,  # 280 * 0.75
    'settings_panel_width': 600,  # 800 * 0.75
    'settings_panel_height': 338,  # 450 * 0.75
    'right_buttons_x': 900,  # 1200 * 0.75（4:3コンテンツ内の位置）
    'right_buttons_y': 60  # 80 * 0.75
}

# 音声設定のデフォルト値
DEFAULT_AUDIO_SETTINGS = {
    'vibration': False,
    'bgm_volume': 80,
    'voice_volume': 80
}