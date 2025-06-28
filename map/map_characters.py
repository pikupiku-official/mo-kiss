import pygame
import os
import sys
from typing import List, Dict, Tuple, Optional
from map_config import HEROINES, ADVANCED_COLORS

# プロジェクトルートをパスに追加
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, "..", "..")
sys.path.insert(0, project_root)

class Character:
    def __init__(self, name: str, description: str, image_file: str):
        self.name = name
        self.description = description
        self.image_file = image_file
        self.image = None
        self.circular_images = {}  # サイズ別の円形画像キャッシュ
        self.load_image()
    
    def load_image(self):
        """キャラクター画像を読み込み"""
        image_path = os.path.join(project_root, "images", "icons", self.image_file)
        try:
            self.image = pygame.image.load(image_path)
        except pygame.error as e:
            print(f"画像読み込みエラー ({self.name}): {e}")
            self.image = None
    
    def get_circular_image(self, size: int) -> pygame.Surface:
        """指定サイズの円形画像を取得（キャッシュ付き）"""
        if size in self.circular_images:
            return self.circular_images[size]
        
        if self.image:
            circular_img = create_circular_image(self.image, size)
            self.circular_images[size] = circular_img
            return circular_img
        else:
            # フォールバック: 色付きの円
            fallback = create_fallback_icon(size)
            self.circular_images[size] = fallback
            return fallback

class CharacterManager:
    def __init__(self):
        self.characters = []
        self.load_characters()
    
    def load_characters(self):
        """ヒロイン情報から全キャラクターを読み込み"""
        for heroine_data in HEROINES:
            character = Character(
                heroine_data['name'],
                heroine_data['description'],
                heroine_data['image_file']
            )
            self.characters.append(character)
    
    def get_character_by_name(self, name: str) -> Optional[Character]:
        """名前でキャラクターを取得"""
        for character in self.characters:
            if character.name == name:
                return character
        return None
    
    def get_all_characters(self) -> List[Character]:
        """全キャラクターを取得"""
        return self.characters
    
    def draw_character_icon(self, screen: pygame.Surface, character: Character, 
                          pos: Tuple[int, int], size: int, has_event: bool = False):
        """キャラクターアイコンを描画"""
        circular_img = character.get_circular_image(size)
        
        # アイコンの中心位置を計算
        icon_rect = circular_img.get_rect()
        icon_rect.center = pos
        
        # イベントがある場合は光る効果を追加
        if has_event:
            # 光る効果の円を描画
            glow_radius = size // 2 + 5
            pygame.draw.circle(screen, ADVANCED_COLORS['event_glow'], pos, glow_radius, 3)
        
        # アイコンを描画
        screen.blit(circular_img, icon_rect)
        
        return icon_rect
    
    def check_character_click(self, mouse_pos: Tuple[int, int], character_positions: Dict[str, Tuple[int, int]], 
                            click_radius: int = 30) -> Optional[str]:
        """キャラクタークリック判定"""
        for character_name, pos in character_positions.items():
            distance = ((mouse_pos[0] - pos[0]) ** 2 + (mouse_pos[1] - pos[1]) ** 2) ** 0.5
            if distance <= click_radius:
                return character_name
        return None

def create_circular_image(original_image: pygame.Surface, size: int) -> pygame.Surface:
    """画像を円形に切り抜く関数（高品質アンチエイリアシング付き）"""
    # 元画像を正方形にリサイズ
    scaled_image = pygame.transform.smoothscale(original_image, (size, size))
    
    # 透明な円形サーフェスを作成
    circular_surface = pygame.Surface((size, size), pygame.SRCALPHA)
    circular_surface.fill((0, 0, 0, 0))
    
    # マスク用の円を作成
    mask_surface = pygame.Surface((size, size), pygame.SRCALPHA)
    mask_surface.fill((0, 0, 0, 0))
    pygame.draw.circle(mask_surface, (255, 255, 255, 255), (size//2, size//2), size//2)
    
    # アンチエイリアシング付きの境界線
    pygame.draw.circle(mask_surface, (255, 255, 255, 255), (size//2, size//2), size//2, 0)
    
    # マスクを適用
    for x in range(size):
        for y in range(size):
            if mask_surface.get_at((x, y))[3] > 0:  # アルファ値をチェック
                circular_surface.set_at((x, y), scaled_image.get_at((x, y)))
    
    return circular_surface

def create_fallback_icon(size: int) -> pygame.Surface:
    """フォールバック用の色付きアイコンを作成"""
    surface = pygame.Surface((size, size), pygame.SRCALPHA)
    surface.fill((0, 0, 0, 0))
    
    # 背景円
    pygame.draw.circle(surface, ADVANCED_COLORS['girl_icon'], (size//2, size//2), size//2)
    
    # 境界線
    pygame.draw.circle(surface, (255, 255, 255), (size//2, size//2), size//2, 2)
    
    return surface

def is_point_in_circle(point: Tuple[int, int], center: Tuple[int, int], radius: int) -> bool:
    """点が円の内部にあるかチェック"""
    distance = ((point[0] - center[0]) ** 2 + (point[1] - center[1]) ** 2) ** 0.5
    return distance <= radius

def get_character_positions_for_location(location: str, map_type: str) -> Dict[str, Tuple[int, int]]:
    """特定の場所でのキャラクター位置を取得"""
    # この関数は実際のイベントデータに基づいてキャラクターの位置を決定する
    # 現在は簡単な例として固定位置を返す
    
    positions = {}
    
    if map_type == "weekday":  # 学校
        base_positions = {
            'classroom': [(750, 280), (850, 280), (800, 320)],
            'library': [(580, 330), (620, 330), (600, 370)],
            'gym': [(1180, 430), (1220, 430), (1200, 470)],
            'shop': [(380, 480), (420, 480), (400, 520)],
            'rooftop': [(780, 180), (820, 180), (800, 220)],
            'school_gate': [(780, 630), (820, 630), (800, 670)]
        }
    else:  # 休日（街）
        base_positions = {
            'park': [(280, 280), (320, 280), (300, 320)],
            'station': [(1280, 380), (1320, 380), (1300, 420)],
            'shopping': [(780, 330), (820, 330), (800, 370)],
            'cafe': [(580, 480), (620, 480), (600, 520)]
        }
    
    if location in base_positions:
        # 最大3キャラクターまでの位置を設定
        character_names = [char['name'] for char in HEROINES]
        for i, pos in enumerate(base_positions[location]):
            if i < len(character_names):
                positions[character_names[i]] = pos
    
    return positions