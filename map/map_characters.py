import pygame
import os
import sys
from typing import List, Dict, Tuple, Optional
from map_config import HEROINES, ADVANCED_COLORS

# 繝励Ο繧ｸ繧ｧ繧ｯ繝医Ν繝ｼ繝医ｒ繝代せ縺ｫ霑ｽ蜉
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, "..", "..")
sys.path.insert(0, project_root)

class Character:
    def __init__(self, name: str, description: str, image_file: str):
        self.name = name
        self.description = description
        self.image_file = image_file
        self.image = None
        self.circular_images = {}  # 繧ｵ繧､繧ｺ蛻･縺ｮ蜀・ｽ｢逕ｻ蜒上く繝｣繝・す繝･
        self.load_image()
    
    def load_image(self):
        """繧ｭ繝｣繝ｩ繧ｯ繧ｿ繝ｼ逕ｻ蜒上ｒ隱ｭ縺ｿ霎ｼ縺ｿ"""
        image_path = os.path.join(project_root, "images", "ICON", self.image_file)
        try:
            self.image = pygame.image.load(image_path)
        except pygame.error as e:
            print(f"逕ｻ蜒剰ｪｭ縺ｿ霎ｼ縺ｿ繧ｨ繝ｩ繝ｼ ({self.name}): {e}")
            self.image = None
    
    def get_circular_image(self, size: int) -> pygame.Surface:
        """謖・ｮ壹し繧､繧ｺ縺ｮ蜀・ｽ｢逕ｻ蜒上ｒ蜿門ｾ暦ｼ医く繝｣繝・す繝･莉倥″・・""
        if size in self.circular_images:
            return self.circular_images[size]
        
        if self.image:
            circular_img = create_circular_image(self.image, size)
            self.circular_images[size] = circular_img
            return circular_img
        else:
            # 繝輔か繝ｼ繝ｫ繝舌ャ繧ｯ: 濶ｲ莉倥″縺ｮ蜀・
            fallback = create_fallback_icon(size)
            self.circular_images[size] = fallback
            return fallback

class CharacterManager:
    def __init__(self):
        self.characters = []
        self.load_characters()
    
    def load_characters(self):
        """繝偵Ο繧､繝ｳ諠・ｱ縺九ｉ蜈ｨ繧ｭ繝｣繝ｩ繧ｯ繧ｿ繝ｼ繧定ｪｭ縺ｿ霎ｼ縺ｿ"""
        for heroine_data in HEROINES:
            character = Character(
                heroine_data['name'],
                heroine_data['description'],
                heroine_data['image_file']
            )
            self.characters.append(character)
    
    def get_character_by_name(self, name: str) -> Optional[Character]:
        """蜷榊燕縺ｧ繧ｭ繝｣繝ｩ繧ｯ繧ｿ繝ｼ繧貞叙蠕・""
        for character in self.characters:
            if character.name == name:
                return character
        return None
    
    def get_all_characters(self) -> List[Character]:
        """蜈ｨ繧ｭ繝｣繝ｩ繧ｯ繧ｿ繝ｼ繧貞叙蠕・""
        return self.characters
    
    def draw_character_icon(self, screen: pygame.Surface, character: Character, 
                          pos: Tuple[int, int], size: int, has_event: bool = False):
        """繧ｭ繝｣繝ｩ繧ｯ繧ｿ繝ｼ繧｢繧､繧ｳ繝ｳ繧呈緒逕ｻ"""
        circular_img = character.get_circular_image(size)
        
        # 繧｢繧､繧ｳ繝ｳ縺ｮ荳ｭ蠢・ｽ咲ｽｮ繧定ｨ育ｮ・
        icon_rect = circular_img.get_rect()
        icon_rect.center = pos
        
        # 繧､繝吶Φ繝医′縺ゅｋ蝣ｴ蜷医・蜈峨ｋ蜉ｹ譫懊ｒ霑ｽ蜉
        if has_event:
            # 蜈峨ｋ蜉ｹ譫懊・蜀・ｒ謠冗判
            glow_radius = size // 2 + 5
            pygame.draw.circle(screen, ADVANCED_COLORS['event_glow'], pos, glow_radius, 3)
        
        # 繧｢繧､繧ｳ繝ｳ繧呈緒逕ｻ
        screen.blit(circular_img, icon_rect)
        
        return icon_rect
    
    def check_character_click(self, mouse_pos: Tuple[int, int], character_positions: Dict[str, Tuple[int, int]], 
                            click_radius: int = 30) -> Optional[str]:
        """繧ｭ繝｣繝ｩ繧ｯ繧ｿ繝ｼ繧ｯ繝ｪ繝・け蛻､螳・""
        for character_name, pos in character_positions.items():
            distance = ((mouse_pos[0] - pos[0]) ** 2 + (mouse_pos[1] - pos[1]) ** 2) ** 0.5
            if distance <= click_radius:
                return character_name
        return None

def create_circular_image(original_image: pygame.Surface, size: int) -> pygame.Surface:
    """逕ｻ蜒上ｒ蜀・ｽ｢縺ｫ蛻・ｊ謚懊￥髢｢謨ｰ・磯ｫ伜刀雉ｪ繧｢繝ｳ繝√お繧､繝ｪ繧｢繧ｷ繝ｳ繧ｰ莉倥″・・""
    # 蜈・判蜒上ｒ豁｣譁ｹ蠖｢縺ｫ繝ｪ繧ｵ繧､繧ｺ
    scaled_image = pygame.transform.smoothscale(original_image, (size, size))
    
    # 騾乗・縺ｪ蜀・ｽ｢繧ｵ繝ｼ繝輔ぉ繧ｹ繧剃ｽ懈・
    circular_surface = pygame.Surface((size, size), pygame.SRCALPHA)
    circular_surface.fill((0, 0, 0, 0))
    
    # 繝槭せ繧ｯ逕ｨ縺ｮ蜀・ｒ菴懈・
    mask_surface = pygame.Surface((size, size), pygame.SRCALPHA)
    mask_surface.fill((0, 0, 0, 0))
    pygame.draw.circle(mask_surface, (255, 255, 255, 255), (size//2, size//2), size//2)
    
    # 繧｢繝ｳ繝√お繧､繝ｪ繧｢繧ｷ繝ｳ繧ｰ莉倥″縺ｮ蠅・阜邱・
    pygame.draw.circle(mask_surface, (255, 255, 255, 255), (size//2, size//2), size//2, 0)
    
    # 繝槭せ繧ｯ繧帝←逕ｨ
    for x in range(size):
        for y in range(size):
            if mask_surface.get_at((x, y))[3] > 0:  # 繧｢繝ｫ繝輔ぃ蛟､繧偵メ繧ｧ繝・け
                circular_surface.set_at((x, y), scaled_image.get_at((x, y)))
    
    return circular_surface

def create_fallback_icon(size: int) -> pygame.Surface:
    """繝輔か繝ｼ繝ｫ繝舌ャ繧ｯ逕ｨ縺ｮ濶ｲ莉倥″繧｢繧､繧ｳ繝ｳ繧剃ｽ懈・"""
    surface = pygame.Surface((size, size), pygame.SRCALPHA)
    surface.fill((0, 0, 0, 0))
    
    # 閭梧勹蜀・
    pygame.draw.circle(surface, ADVANCED_COLORS['girl_icon'], (size//2, size//2), size//2)
    
    # 蠅・阜邱・
    pygame.draw.circle(surface, (255, 255, 255), (size//2, size//2), size//2, 2)
    
    return surface

def is_point_in_circle(point: Tuple[int, int], center: Tuple[int, int], radius: int) -> bool:
    """轤ｹ縺悟・縺ｮ蜀・Κ縺ｫ縺ゅｋ縺九メ繧ｧ繝・け"""
    distance = ((point[0] - center[0]) ** 2 + (point[1] - center[1]) ** 2) ** 0.5
    return distance <= radius

def get_character_positions_for_location(location: str, map_type: str) -> Dict[str, Tuple[int, int]]:
    """迚ｹ螳壹・蝣ｴ謇縺ｧ縺ｮ繧ｭ繝｣繝ｩ繧ｯ繧ｿ繝ｼ菴咲ｽｮ繧貞叙蠕・""
    # 縺薙・髢｢謨ｰ縺ｯ螳滄圀縺ｮ繧､繝吶Φ繝医ョ繝ｼ繧ｿ縺ｫ蝓ｺ縺･縺・※繧ｭ繝｣繝ｩ繧ｯ繧ｿ繝ｼ縺ｮ菴咲ｽｮ繧呈ｱｺ螳壹☆繧・
    # 迴ｾ蝨ｨ縺ｯ邁｡蜊倥↑萓九→縺励※蝗ｺ螳壻ｽ咲ｽｮ繧定ｿ斐☆
    
    positions = {}
    
    if map_type == "weekday":  # 蟄ｦ譬｡
        base_positions = {
            'classroom': [(750, 280), (850, 280), (800, 320)],
            'library': [(580, 330), (620, 330), (600, 370)],
            'gym': [(1180, 430), (1220, 430), (1200, 470)],
            'shop': [(380, 480), (420, 480), (400, 520)],
            'rooftop': [(780, 180), (820, 180), (800, 220)],
            'school_gate': [(780, 630), (820, 630), (800, 670)]
        }
    else:  # 莨第律・郁｡暦ｼ・
        base_positions = {
            'park': [(280, 280), (320, 280), (300, 320)],
            'station': [(1280, 380), (1320, 380), (1300, 420)],
            'shopping': [(780, 330), (820, 330), (800, 370)],
            'cafe': [(580, 480), (620, 480), (600, 520)]
        }
    
    if location in base_positions:
        # 譛螟ｧ3繧ｭ繝｣繝ｩ繧ｯ繧ｿ繝ｼ縺ｾ縺ｧ縺ｮ菴咲ｽｮ繧定ｨｭ螳・
        character_names = [char['name'] for char in HEROINES]
        for i, pos in enumerate(base_positions[location]):
            if i < len(character_names):
                positions[character_names[i]] = pos
    
    return positions
