import pygame
import os
from config import get_textbox_position, get_ui_button_positions

class ImageManager:
    def __init__(self, debug=False):
        self.debug = debug
        self.images = {}
        self.image_cache = {}  # パフォーマンス改善のためのキャッシュ

    def load_image(self, filepath, size=None):
        # キャッシュキーを生成
        cache_key = f"{filepath}_{size if size else 'original'}"
        
        # キャッシュから返す
        if cache_key in self.image_cache:
            return self.image_cache[cache_key]
        
        try:
            if not os.path.exists(filepath):
                if self.debug:
                    print(f"警告: 画像ファイルが見つかりません: {filepath}")
                return None
                
            # 画像を読み込む
            image = pygame.image.load(filepath)
            image = image.convert_alpha()

            # 画面サイズに合わせて画像をリサイズ（必要に応じて）
            if size and isinstance(size, tuple) and len(size) == 2:
                image = pygame.transform.scale(image, size)
                
            # キャッシュに保存
            self.image_cache[cache_key] = image

            return image
        
        except pygame.error as e:
            if self.debug:
                print(f"エラー: pygameエラー - {filepath}: {e}")
            return None
        except Exception as e:
            if self.debug:
                print(f"エラー: 一般エラー - {filepath}: {e}")
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
            "cheeks": {},
            "ui": {}
        }

        # imagesディレクトリ内のすべてのファイルを検索
        for root, dirs, files in os.walk("images"):
            for file in files:
                if file.endswith(('.png', '.jpg', '.jpeg')):
                    file_path = os.path.join(root, file)
                    
                    # ファイル名に基づいて分類（ファイル名をキーとして使用）
                    file_name_without_ext = os.path.splitext(file)[0]  # 拡張子を除いたファイル名
                    
                    if "bg" in file:
                        # 背景画像は画面サイズに合わせてリサイズ
                        bg_key = file.split('.')[2] if '.' in file and len(file.split('.')) > 2 else file_name_without_ext
                        images["backgrounds"][bg_key] = self.load_image(file_path, (screen_width, screen_height))
                    elif "char" in file or root.endswith("characters") or root.endswith("桃子"):
                        # 桃子フォルダからも読み込み
                        images["characters"][file_name_without_ext] = self.load_image(file_path)
                    elif "eye" in file or root.endswith("eyes"):
                        images["eyes"][file_name_without_ext] = self.load_image(file_path)
                    elif "mouth" in file or root.endswith("mouths"):
                        images["mouths"][file_name_without_ext] = self.load_image(file_path)
                    elif "brow" in file or root.endswith("brows"):
                        images["brows"][file_name_without_ext] = self.load_image(file_path)
                    elif "cheek" in file or root.endswith("cheeks"):
                        images["cheeks"][file_name_without_ext] = self.load_image(file_path)
                    elif "ui" in file:
                        ui_name = file.split('.')[1] if len(file.split('.')) >= 3 else file.split('.')[0]
                        if ui_name == "text-box":
                            # テキストボックスを画面幅に合わせてリサイズ
                            original_image = self.load_image(file_path)
                            if original_image:
                                original_width = original_image.get_width()
                                original_height = original_image.get_height()
                                
                                # テキストボックスのサイズ調整（仮想解像度基準）
                                from config import scale_size
                                
                                # 仮想解像度でのサイズ計算（1920 * 259 / 302 = 1646px）
                                virtual_width = 1646
                                virtual_height = int(virtual_width * original_height / original_width)
                                
                                # スケーリングしたサイズを計算
                                new_width, new_height = scale_size(virtual_width, virtual_height)
                                
                                images["ui"][ui_name] = pygame.transform.scale(original_image, (new_width, new_height))

                        elif ui_name == "auto":
                            original_image2 = self.load_image(file_path)
                            if original_image2:
                                original_width2 = original_image2.get_width()
                                original_height2 = original_image2.get_height()
                                
                                # autoボタンのサイズ調整（仮想解像度基準）
                                from config import scale_size
                                
                                # 仮想解像度でのサイズ計算（1920 * 530 / 10000 = 102px）
                                virtual_width2 = 102
                                virtual_height2 = int(virtual_width2 * original_height2 / original_width2)
                                
                                # スケーリングしたサイズを計算
                                new_width2, new_height2 = scale_size(virtual_width2, virtual_height2)
                                
                                images["ui"][ui_name] = pygame.transform.scale(original_image2, (new_width2, new_height2))

                        elif ui_name == "skip":
                            original_image3 = self.load_image(file_path)
                            if original_image3:
                                original_width3 = original_image3.get_width()
                                original_height3 = original_image3.get_height()
                                
                                # skipボタンのサイズ調整（仮想解像度基準）
                                from config import scale_size
                                
                                # 仮想解像度でのサイズ計算（1920 * 440 / 10000 = 84px）
                                virtual_width3 = 84
                                virtual_height3 = int(virtual_width3 * original_height3 / original_width3)
                                
                                # スケーリングしたサイズを計算
                                new_width3, new_height3 = scale_size(virtual_width3, virtual_height3)
                                
                                images["ui"][ui_name] = pygame.transform.scale(original_image3, (new_width3, new_height3))

                        else:
                            images["ui"][ui_name] = self.load_image(file_path)

        if self.debug:
            total_images = sum(len(v) for v in images.values())
            print(f"画像読み込み完了: {total_images}件")

        return images 
    
    def draw_ui_elements(self, screen, images, show_text=True):
        """UI要素を描画する"""
        if not show_text or "ui" not in images:
            return
        
        ui_images = images["ui"]
        
        # テキストボックスを描画（画面下部）
        if "text-box" in ui_images and ui_images["text-box"]:
            text_box = ui_images["text-box"]
            x_pos, y_pos = get_textbox_position(screen, text_box)
            screen.blit(text_box, (x_pos, y_pos))

        # ボタン類を描画
        button_positions = get_ui_button_positions(screen)
        
        # autoボタンを描画（右上付近）
        if "auto" in ui_images and ui_images["auto"]:
            auto_btn = ui_images["auto"]
            auto_x, auto_y = button_positions["auto"]
            screen.blit(auto_btn, (auto_x, auto_y))
        
        # skipボタンを描画（右上付近、autoの隣）
        if "skip" in ui_images and ui_images["skip"]:
            skip_btn = ui_images["skip"]
            skip_x, skip_y = button_positions["skip"]
            screen.blit(skip_btn, (skip_x, skip_y))