# text_renderer.py用のパッチメソッド

def _get_current_positions(self):
    """現在の画面サイズに基づいてテキスト位置を取得"""
    from config import get_text_positions
    text_positions = get_text_positions(self.screen)
    return {
        'text_start_x': text_positions["speech_1"][0],
        'text_start_y': text_positions["speech_1"][1],
        'name_start_x': text_positions["name_1"][0],
        'name_start_y': text_positions["name_1"][1],
        'text_line_height': text_positions["line_height"]
    }