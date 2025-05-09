import pygame
import sys
import os
import json

# Pygameを初期化
pygame.init()

# 画面サイズの設定
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

# ウィンドウのタイトル設定
pygame.display.set_caption("テスト")

# デバッグモード
DEBUG = True

# JSONファイルから会話データを読み込む関数
def load_dialogue_from_json(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            data = json.load(file)

        dialogue_list = []
        if "scenes" in data:
            for scene in data["scenes"]:
                background = scene.get("background", "default")
                character = scene.get("character", "default")
                eye = scene.get("eye", "normal")
                mouth = scene.get("mouth", "normal")
                text = scene.get("text", "")

                # テキストに二つ連続したスペースがあれば分割する
                text_parts = text.split("  ")

                for i, text_part in enumerate(text_parts):
                    if i == 0:
                        dialogue_list.append([background, character, eye, mouth, text_part])
                    else:
                        if text_part.strip():
                            dialogue_list.append([background, character, eye, mouth, text_part])
                

        return dialogue_list
    
    except FileNotFoundError:
        print(f"ファイルが見つかりません: {filename}")
        return []
    except json.JSONDecodeError as e:
        print(f"JSONパースエラー: {e}")
        return []
    except Exception as e:
        print(f"エラー: {e}")
        return []

# 画像を読み込む関数
def load_image(filename, size=None):

    # ファイル名に基づいて適切なフォルダパスを決定
    if "bg" in filename:
        image_path = os.path.join("images", "backgrounds", filename)
    elif "char" in filename:
        image_path = os.path.join("images", "characters", filename)
    elif "eye" in filename:
        image_path = os.path.join("images", "eyes", filename)
    elif "mouth" in filename:
        image_path = os.path.join("images", "mouths", filename)
    else:
        image_path = os.path.join("images", filename)
    
    try:
        print(f"画像ファイルを読み込み中: {image_path}")
        # 画像を読み込む
        image = pygame.image.load(image_path)

        # 透明部分を適切に処理するために変換
        image = image.convert_alpha()

        # 画面サイズに合わせて画像をリサイズ（必要に応じて）
        if size and isinstance(size, tuple) and len(size) == 2:
            image = pygame.transform.scale(image, size)

        return image
    
    except pygame.error as e:
        print(f"画像の読み込みに失敗しました: {e}")
        print(f"ファイルパス: {image_path}")

        # 代わりに単色の背景を作成
        if size is None:
            size = (100, 100)
            surface = pygame.Surface(size, pygame.SRCALPHA)

        # 背景、キャラクター、目、口によって色を変える
        if "backgrounds" in image_path:  # "background" から "backgrounds" に修正
            surface.fill((100, 150, 200, 255))  # 青っぽい背景
        elif "characters" in image_path:
            surface.fill((220, 180, 180, 200))  # キャラクター
        elif "eyes" in image_path:
            surface.fill((0, 0, 0, 200))        # 黒い目
        elif "mouths" in image_path:
            surface.fill((200, 0, 0, 200))      # 赤い口
        else:
            surface.fill((150, 150, 150, 200))  # その他
        return surface
    
# テキストを描画する関数
def render_paragraph(paragraph, font, color, start_x, start_y, max_width, line_height):
    parts = paragraph.split(' ')
    lines = []
    current_line = []

    # 行に収まる単語を追加していく
    for part in parts:
        if not part:
            continue

        if current_line:
            lines.append(' '.join(current_line))
            current_line = []

        current_line.append(part)

    # 最後の行を追加
    if current_line:
        lines.append(' '.join(current_line))

    # 各行を描画
    y = start_y
    for line in lines:
        text_surface = font.render(line, True, color)
        screen.blit(text_surface, (start_x, y))
        y += line_height
    
    return y - start_y # テキストの高さを返す

# 顔パーツの中心合わせ用の関数
def center_part(part, position):
    """パーツを指定された位置の中心に配置するための座標を計算"""
    return (
        position[0] - part.get_width() // 2,
        position[1] - part.get_height() // 2
    )

# 利用可能な背景、キャラクター画像、パーツのリスト
available_backgrounds = {
    "classroom": load_image("test.bg.classroom.jpg", (SCREEN_WIDTH, SCREEN_HEIGHT)),
    "school": load_image("test.bg.school.jpg", (SCREEN_WIDTH, SCREEN_HEIGHT))
}

available_characters = {
    "girl1": load_image("test.char.girl1.png"),
    "girl2": load_image("test.char.girl2.png")
}

available_eyes = {
    "eye1": load_image("test.eye.eye1.png", (70, 20))
}

available_mouths = {
    "mouth1": load_image("test.mouth.mouth1.png", (30, 30))
}

# 会話データをJSONから読み込む
try:
    dialogue_data = load_dialogue_from_json("dialogue.json")
except Exception as e:
    print(f"対話データの読み込みに失敗しました: {e}")
    dialogue_data = []

# 会話データが無い場合のデフォルト値
if not dialogue_data:
    dialogue_data = [
        ["classroom", "girl1", "eye1", "mouth1", "JSONファイルが読み込めませんでした。"],
        ["classroom", "girl1", "eye1", "mouth1", "デフォルトの会話を表示しています。"]
    ]

# 現在の会話インデックス
current_dialogue_index = 0
current_paragraph = 0

# キャラクター画像のサイズを取得
char_width = available_characters["girl1"].get_width()
char_height = available_characters["girl1"].get_height()

# キャラクター画像を画面中央に配置
character_pos = [
    (SCREEN_WIDTH - char_width) // 2,
    (SCREEN_HEIGHT - char_height) // 2
]

# 顔のパーツの相対位置を設定
face_pos = {
    "eye": (available_characters["girl1"].get_width() * 0.49, available_characters["girl1"].get_height() * 0.24), # 目の位置
    "mouth": (available_characters["girl1"].get_width() * 0.49, available_characters["girl1"].get_height() * 0.31)  # 口の位置
}

# dialogue行列からデータを読み込む関数
def load_dialogue_data(index):
    if 0 <= index < len(dialogue_data):
        return dialogue_data[index]
    return None

# 表示フラグ
show_character = True
show_face_parts = True
show_text = True

# フォントの初期化
font = pygame.font.SysFont(None, 24)
text_font = pygame.font.SysFont('meiryo', 20)

# テキスト表示設定
text_color = (255, 255, 255)
text_bg_color = (0, 0, 0, 180)
text_start_x = 50
text_start_y = 450
text_line_height = 25
text_padding = 10
text_box_width = SCREEN_WIDTH - 100
text_max_width = text_box_width - 2 * text_padding

# 「次へ」のインジケーター(必要性ナシ)
next_indicator_color = (255, 255, 255)
next_indicator_pos = (SCREEN_WIDTH - 50, SCREEN_HEIGHT - 50)
next_indicator_text = "▼"


# メインループ
running = True
clock = pygame.time.Clock()

while running:
    # イベント処理
    for event in pygame.event.get():
        # ウィンドウの×ボタンが押されたら終了
        if event.type == pygame.QUIT:
            running = False
        # キーが押された時の処理
        elif event.type == pygame.KEYDOWN:
            # ESCキーが押されたら終了
            if event.key == pygame.K_ESCAPE:
                running = False
            # キャラクター表示フラグ切替
            elif event.key == pygame.K_SPACE:
                show_character = not show_character
                if show_character:
                    print("キャラクターを表示しました")
                else:
                    print("キャラクターを非表示にしました")
                    show_face_parts = False
            # 顔パーツ表示フラグ切替
            elif event.key == pygame.K_f and show_character:
                show_face_parts = not show_face_parts
                if show_face_parts:
                    print("顔パーツを表示しました")
                else:
                    print("顔パーツを非表示にしました")
            #テキスト表示フラグ
            elif event.key == pygame.K_t:
                show_text = not show_text
                if show_text:
                    print("テキストを表示しました")
                else:
                    print("テキストを非表示にしました")
            #テキスト遷移フラグ
            elif event.key == pygame.K_RETURN and show_text:
                if current_paragraph < len(dialogue_data) - 1:
                    current_paragraph += 1
                    print(f"段落 {current_paragraph + 1}/{len(dialogue_data)} に進みました")
                else:
                    print("最後の段落です")

    screen.fill((0, 0, 0))
    
    # 現在の会話データを取得
    current_dialogue = load_dialogue_data(current_paragraph)

    if current_dialogue:
        bg_name, char_name, eye_type, mouth_type, dialogue_text = current_dialogue
    
    # 背景画像を描画
    if bg_name in available_backgrounds:
        screen.blit(available_backgrounds[bg_name], (0, 0))
    else:
        screen.fill((0, 0, 0))

    # キャラクターフラグがTrueならキャラクターを描画
    if show_character and char_name in available_characters:
        screen.blit(available_characters[char_name], character_pos)

        # 顔パーツフラグがTrueなら顔のパーツを描画
        if show_face_parts:
            # 目を描画
            if eye_type in available_eyes:
                eye_pos = (
                    character_pos[0] + face_pos["eye"][0],
                    character_pos[1] + face_pos["eye"][1]
                )
                screen.blit(available_eyes[eye_type], center_part(available_eyes[eye_type], eye_pos))
            
            # 口を描画
            if mouth_type in available_mouths:
                mouth_pos = (
                    character_pos[0] + face_pos["mouth"][0],
                    character_pos[1] + face_pos["mouth"][1]
                )
                screen.blit(available_mouths[mouth_type], center_part(available_mouths[mouth_type], mouth_pos))
    
    # テキストフラグがTrueならテキストを描画
    if show_text and current_dialogue:
        # スペースで分割して行数を計算
        dialogue_parts = dialogue_text.split(' ')
        line_count = sum(1 for part in dialogue_parts if part.strip())

        # テキストボックスの高さを行数に応じて計算
        box_height = line_count * text_line_height + text_padding * 2

        #テキストボックスの描画
        text_bg_surface = pygame.Surface((text_box_width, box_height), pygame.SRCALPHA)
        text_bg_surface.fill(text_bg_color)
        screen.blit(text_bg_surface, (text_start_x - text_padding, text_start_y - text_padding))

        # テキストの描画
        text_height = render_paragraph(dialogue_text, text_font, text_color, text_start_x, text_start_y, text_max_width, text_line_height)
        
        # インジケーターの描画
        if current_paragraph < len(dialogue_data) - 1:
            next_indicator_surface = text_font.render(next_indicator_text, True, next_indicator_color)
            screen.blit(next_indicator_surface, next_indicator_pos)

    # FPSを設定
    clock.tick(30)
            
    # 画面を更新
    pygame.display.flip()

# Pygameを終了
pygame.quit()
sys.exit()