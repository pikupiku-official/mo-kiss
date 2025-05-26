# ゲーム管理関連
from game_manager import (
    initialize_game,
    initialize_first_scene,
    change_bgm,
    get_default_normalized_dialogue
)

# キャラクター管理関連
from character_manager import (
    move_character,
    hide_character,
    update_character_animations,
    render_face_parts,
    draw_characters
)

# 背景管理関連
from background_manager import (
    show_background,
    move_background,
    update_background_animation,
    draw_background
)

# シナリオ管理関連
from scenario_manager import (
    advance_dialogue
)

# データ正規化関連
from data_normalizer import (
    normalize_dialogue_data
)

# 互換性のための再エクスポート
__all__ = [
    # ゲーム管理
    'initialize_game',
    'initialize_first_scene',
    'change_bgm',
    'get_default_normalized_dialogue',
    
    # キャラクター管理
    'move_character',
    'hide_character',
    'update_character_animations',
    'render_face_parts',
    'draw_characters',
    
    # 背景管理
    'show_background',
    'move_background',
    'update_background_animation',
    'draw_background',
    
    # シナリオ管理
    'advance_dialogue',
    
    # データ正規化
    'normalize_dialogue_data'
]

# バージョン情報
__version__ = "2.0.0"
__description__ = "分割されたモジュール構成でのモデル層"

if __name__ == "__main__":
    print(f"Model module version {__version__}")
    print(f"Available functions: {len(__all__)}")
    for func_name in sorted(__all__):
        print(f"  - {func_name}")