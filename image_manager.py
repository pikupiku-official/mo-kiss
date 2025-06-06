import pygame
import os

class ImageManager:
    def __init__(self, debug=False):
        self.debug = debug
        self.images = {}

    def load_image(self, filepath, size=None):
        try:
            if self.debug:
                print(f"画像ファイルを読み込み中: {filepath}")
            
            # 画像を読み込む
            image = pygame.image.load(filepath)
            image = image.convert_alpha()

            # 画面サイズに合わせて画像をリサイズ（必要に応じて）
            if size and isinstance(size, tuple) and len(size) == 2:
                image = pygame.transform.scale(image, size)

            return image
        
        except pygame.error as e:
            if self.debug:
                print(f"画像の読み込みに失敗しました: {e}")
                print(f"ファイルパス: {filepath}")
            return None

    def center_part(self, part, position):
        """パーツを指定された位置の中心に配置するための座標を計算"""
        return (
            position[0] - part.get_width() // 2,
            position[1] - part.get_height() // 2
        )

    def load_all_images(self, screen_width, screen_height):
        """すべての画像を読み込む"""
        images = {
            "backgrounds": {},
            "characters": {},
            "eyes": {},
            "mouths": {},
            "brows": {},
            "ui": {}
        }

        # imagesディレクトリ内のすべてのファイルを検索
        for root, dirs, files in os.walk("images"):
            for file in files:
                if file.endswith(('.png', '.jpg', '.jpeg')):
                    file_path = os.path.join(root, file)
                    
                    # ファイル名に基づいて分類
                    if "bg" in file:
                        # 背景画像は画面サイズに合わせてリサイズ
                        images["backgrounds"][file.split('.')[2]] = self.load_image(file_path, (screen_width, screen_height))
                    elif "char" in file:
                        images["characters"][file.split('.')[2]] = self.load_image(file_path)
                    elif "eye" in file:
                        images["eyes"][file.split('.')[2]] = self.load_image(file_path, (70, 20))
                    elif "mouth" in file:
                        images["mouths"][file.split('.')[2]] = self.load_image(file_path, (30, 30))
                    elif "brow" in file:
                        images["brows"][file.split('.')[2]] = self.load_image(file_path, (70, 20))
                    elif "ui" in file:
                        ui_name = file.split('.')[1] if len(file.split('.')) >= 3 else file.split('.')[0]
                        images["ui"][ui_name] = self.load_image(file_path)

        if self.debug:
            print("読み込んだ画像:")
            for category, image_dict in images.items():
                print(f"{category}: {list(image_dict.keys())}")

        return images 
    
    def draw_ui_elements(self, screen, images, show_text=True):
        """UI要素を描画する"""
        if not show_text or "ui" not in images:
            return
        
        ui_images = images["ui"]
        screen_width = screen.get_width()
        screen_height = screen.get_height()
        
        # テキストボックスを描画（画面下部）
        if "text-box" in ui_images and ui_images["text-box"]:
            text_box = ui_images["text-box"]
            text_box_width = text_box.get_width()
            text_box_height = text_box.get_height()
            x_pos = (screen_width - text_box_width) // 2
            y_pos = screen_height - text_box_height - screen_height * 2 / 45
            screen.blit(text_box, (x_pos, y_pos))
        
        # autoボタンを描画（右上付近）
        if "auto" in ui_images and ui_images["auto"]:
            auto_btn = ui_images["auto"]
            auto_x = screen_width - auto_btn.get_width() - 120
            auto_y = 20
            screen.blit(auto_btn, (auto_x, auto_y))
        
        # skipボタンを描画（右上付近、autoの隣）
        if "skip" in ui_images and ui_images["skip"]:
            skip_btn = ui_images["skip"]
            skip_x = screen_width - skip_btn.get_width() - 20
            skip_y = 20
            screen.blit(skip_btn, (skip_x, skip_y))