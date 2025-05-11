import pygame
import sys
from bgm_manager import BGMManager
from dialogue_loader import DialogueLoader
from image_manager import ImageManager
from text_renderer import TextRenderer
from config import *

# Pygameを初期化
pygame.init()
pygame.mixer.init()

# 画面の設定
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("テスト")

# 各マネージャーの初期化
bgm_manager = BGMManager(DEBUG)
dialogue_loader = DialogueLoader(DEBUG)
image_manager = ImageManager(DEBUG)
text_renderer = TextRenderer(screen, DEBUG)

# 画像の読み込み
images = image_manager.load_all_images(SCREEN_WIDTH, SCREEN_HEIGHT)

# 会話データの読み込み
try:
    dialogue_data = dialogue_loader.load_dialogue_from_ks("dialogue.ks")
except Exception as e:
    print(f"対話データの読み込みに失敗しました: {e}")
    dialogue_data = dialogue_loader.get_default_dialogue()

# 現在の会話インデックス
current_paragraph = 0

# キャラクター画像のサイズを取得
char_width = images["characters"]["girl1"].get_width()
char_height = images["characters"]["girl1"].get_height()

# キャラクター画像を画面中央に配置
character_pos = [
    (SCREEN_WIDTH - char_width) // 2,
    (SCREEN_HEIGHT - char_height) // 2
]

# 顔のパーツの相対位置を設定
face_pos = {
    "eye": (char_width * FACE_POS["eye"][0], char_height * FACE_POS["eye"][1]),
    "mouth": (char_width * FACE_POS["mouth"][0], char_height * FACE_POS["mouth"][1]),
    "brow": (char_width * FACE_POS["brow"][0], char_height * FACE_POS["brow"][1])
}

# 表示フラグ
show_character = True
show_face_parts = True
show_text = True

# 最初のBGMを再生
if dialogue_data:
    bgm_manager.play_bgm(dialogue_data[0][5])

# メインループ
running = True
clock = pygame.time.Clock()

while running:
    # イベント処理
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            elif event.key == pygame.K_SPACE: # 消去予定
                show_character = not show_character
                if show_character:
                    print("キャラクターを表示しました")
                else:
                    print("キャラクターを非表示にしました")
                    show_face_parts = False
            elif event.key == pygame.K_f and show_character:
                show_face_parts = not show_face_parts
                if show_face_parts:
                    print("顔パーツを表示しました")
                else:
                    print("顔パーツを非表示にしました")
            elif event.key == pygame.K_t:
                show_text = not show_text
                if show_text:
                    print("テキストを表示しました")
                else:
                    print("テキストを非表示にしました")
            elif event.key == pygame.K_RETURN and show_text:
                if current_paragraph < len(dialogue_data) - 1:
                    current_paragraph += 1
                    # BGMの変更を確認
                    new_bgm = dialogue_data[current_paragraph][5]
                    if new_bgm != bgm_manager.current_bgm:
                        bgm_manager.play_bgm(new_bgm)
                    print(f"段落 {current_paragraph + 1}/{len(dialogue_data)} に進みました")
                else:
                    print("最後の段落です")

    screen.fill((0, 0, 0))
    
    # 現在の会話データを取得
    current_dialogue = dialogue_data[current_paragraph]
    bg_name, char_name, eye_type, mouth_type, dialogue_text, bgm_name, bgm_volume, bgm_loop = current_dialogue[:8]
    display_name = current_dialogue[8] if len(current_dialogue) > 8 else char_name
    brow_type = current_dialogue[9] if len(current_dialogue) > 9 else None
    
    # 背景画像を描画
    if bg_name in images["backgrounds"]:
        screen.blit(images["backgrounds"][bg_name], (0, 0))
    else:
        screen.fill((0, 0, 0))

    # BGMの変更を確認
    if bgm_name != bgm_manager.current_bgm:
        bgm_manager.play_bgm(bgm_name, bgm_volume)
        if not bgm_loop:
            bgm_manager.stop_bgm()  # ループしない場合は停止

    # キャラクターの描画
    if show_character and char_name in images["characters"]:
        screen.blit(images["characters"][char_name], character_pos)

        # 顔パーツの描画
        if show_face_parts:
            # 眉毛を描画
            if brow_type and brow_type in images["brows"]:
                brow_pos = (
                    character_pos[0] + face_pos["brow"][0],
                    character_pos[1] + face_pos["brow"][1]
                )
                screen.blit(images["brows"][brow_type], 
                           image_manager.center_part(images["brows"][brow_type], brow_pos))

            # 目を描画
            if eye_type and eye_type in images["eyes"]:
                eye_pos = (
                    character_pos[0] + face_pos["eye"][0],
                    character_pos[1] + face_pos["eye"][1]
                )
                screen.blit(images["eyes"][eye_type], 
                           image_manager.center_part(images["eyes"][eye_type], eye_pos))
            
            # 口を描画
            if mouth_type and mouth_type in images["mouths"]:
                mouth_pos = (
                    character_pos[0] + face_pos["mouth"][0],
                    character_pos[1] + face_pos["mouth"][1]
                )
                screen.blit(images["mouths"][mouth_type], 
                           image_manager.center_part(images["mouths"][mouth_type], mouth_pos))
    
    # テキストの描画
    if show_text:
        text_renderer.set_dialogue(dialogue_text, display_name)
        text_renderer.render_paragraph()
        
        # 次のテキストがある場合はインジケーターを表示
        if current_paragraph < len(dialogue_data) - 1:
            text_renderer.render_next_indicator()

    # FPSを設定
    clock.tick(30)
            
    # 画面を更新
    pygame.display.flip()

# BGMを停止して終了
bgm_manager.stop_bgm()
pygame.quit()
sys.exit() 