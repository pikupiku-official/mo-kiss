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
            "brows": {}
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

        if self.debug:
            print("読み込んだ画像:")
            for category, image_dict in images.items():
                print(f"{category}: {list(image_dict.keys())}")

        return images 