import pygame
import math
import random
from typing import List, Dict, Tuple
from map_config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, ADVANCED_COLORS, TimeSlot, MapType,
    SCHOOL_LOCATIONS, TOWN_LOCATIONS
)

class MapRenderer:
    def __init__(self):
        self.clouds = self.initialize_clouds()
    
    def initialize_clouds(self) -> List[Dict]:
        """雲を初期化"""
        clouds = []
        for i in range(8):
            cloud = {
                'x': random.randint(0, SCREEN_WIDTH),
                'y': random.randint(50, 200),
                'size': random.randint(40, 80),
                'speed': random.uniform(0.1, 0.3)
            }
            clouds.append(cloud)
        return clouds
    
    def update_clouds(self):
        """雲の位置を更新"""
        for cloud in self.clouds:
            cloud['x'] += cloud['speed']
            if cloud['x'] > SCREEN_WIDTH + cloud['size']:
                cloud['x'] = -cloud['size']
    
    def draw_sky(self, screen: pygame.Surface, time_slot: TimeSlot):
        """時間帯に応じた空を描画"""
        colors = ADVANCED_COLORS['sky_colors'][time_slot]
        
        # 3色のグラデーション
        for y in range(SCREEN_HEIGHT):
            if y < SCREEN_HEIGHT // 3:
                # 上部
                ratio = y / (SCREEN_HEIGHT // 3)
                color = self.interpolate_color(colors[0], colors[1], ratio)
            elif y < 2 * SCREEN_HEIGHT // 3:
                # 中部
                ratio = (y - SCREEN_HEIGHT // 3) / (SCREEN_HEIGHT // 3)
                color = self.interpolate_color(colors[1], colors[2], ratio)
            else:
                # 下部
                color = colors[2]
            
            pygame.draw.line(screen, color, (0, y), (SCREEN_WIDTH, y))
    
    def draw_clouds(self, screen: pygame.Surface, time_slot: TimeSlot):
        """雲を描画"""
        base_color = (255, 255, 255)
        if time_slot == TimeSlot.NIGHT:
            base_color = (200, 200, 220)
        elif time_slot == TimeSlot.MORNING:
            base_color = (255, 240, 240)
        
        for cloud in self.clouds:
            self.draw_cloud_shape(screen, cloud['x'], cloud['y'], cloud['size'], base_color)
    
    def draw_cloud_shape(self, screen: pygame.Surface, x: int, y: int, size: int, color: Tuple[int, int, int]):
        """雲の形を描画"""
        # 複数の円で雲の形を作成
        pygame.draw.circle(screen, color, (int(x), int(y)), size // 2)
        pygame.draw.circle(screen, color, (int(x + size * 0.4), int(y)), size // 3)
        pygame.draw.circle(screen, color, (int(x - size * 0.4), int(y)), size // 3)
        pygame.draw.circle(screen, color, (int(x + size * 0.2), int(y - size * 0.2)), size // 4)
        pygame.draw.circle(screen, color, (int(x - size * 0.2), int(y - size * 0.2)), size // 4)
    
    def draw_school_map(self, screen: pygame.Surface, time_slot: TimeSlot):
        """高品質な学校マップを描画"""
        # 地面のグラデーション
        self.draw_ground_gradient(screen)
        
        # メイン校舎
        self.draw_main_school_building(screen, time_slot)
        
        # 体育館
        self.draw_gym(screen, time_slot)
        
        # 校庭
        self.draw_school_yard(screen)
        
        # 校門
        self.draw_school_gate(screen)
        
        # フェンス
        self.draw_school_fence(screen)
        
        # 場所ラベル
        self.draw_location_labels(screen, SCHOOL_LOCATIONS)
    
    def draw_town_map(self, screen: pygame.Surface, time_slot: TimeSlot):
        """街マップを描画"""
        # 地面
        self.draw_ground_gradient(screen)
        
        # 道路システム
        self.draw_road_system(screen)
        
        # 建物群
        self.draw_town_buildings(screen, time_slot)
        
        # 公園
        self.draw_park(screen)
        
        # 川
        self.draw_river(screen)
        
        # 場所ラベル
        self.draw_location_labels(screen, TOWN_LOCATIONS)
    
    def draw_ground_gradient(self, screen: pygame.Surface):
        """地面のグラデーション"""
        grass_color = ADVANCED_COLORS['grass']
        for y in range(SCREEN_HEIGHT // 2, SCREEN_HEIGHT):
            ratio = (y - SCREEN_HEIGHT // 2) / (SCREEN_HEIGHT // 2)
            color = self.interpolate_color(grass_color, (20, 100, 20), ratio)
            pygame.draw.line(screen, color, (0, y), (SCREEN_WIDTH, y))
    
    def draw_main_school_building(self, screen: pygame.Surface, time_slot: TimeSlot):
        """メイン校舎を描画"""
        building_color = ADVANCED_COLORS['school_building']
        roof_color = ADVANCED_COLORS['school_roof']
        
        # メイン校舎
        main_building = pygame.Rect(600, 250, 400, 200)
        self.draw_building_with_shadow(screen, main_building, building_color, roof_color, time_slot)
        
        # 東棟
        east_building = pygame.Rect(1050, 280, 200, 150)
        self.draw_building_with_shadow(screen, east_building, building_color, roof_color, time_slot)
        
        # 渡り廊下
        corridor = pygame.Rect(1000, 320, 50, 50)
        pygame.draw.rect(screen, building_color, corridor)
    
    def draw_gym(self, screen: pygame.Surface, time_slot: TimeSlot):
        """体育館を描画"""
        gym_rect = pygame.Rect(1100, 400, 250, 150)
        gym_color = (220, 220, 200)
        roof_color = (150, 150, 130)
        
        self.draw_building_with_shadow(screen, gym_rect, gym_color, roof_color, time_slot)
        
        # 体育館特有の高い屋根
        roof_points = [
            (gym_rect.left, gym_rect.top),
            (gym_rect.right, gym_rect.top),
            (gym_rect.centerx, gym_rect.top - 30)
        ]
        pygame.draw.polygon(screen, roof_color, roof_points)
    
    def draw_school_yard(self, screen: pygame.Surface):
        """校庭を描画"""
        # トラック
        track_center = (800, 550)
        track_outer = 120
        track_inner = 80
        
        pygame.draw.ellipse(screen, (139, 69, 19), 
                          (track_center[0] - track_outer, track_center[1] - track_outer//2,
                           track_outer*2, track_outer))
        pygame.draw.ellipse(screen, ADVANCED_COLORS['grass'], 
                          (track_center[0] - track_inner, track_center[1] - track_inner//2,
                           track_inner*2, track_inner))
        
        # バスケットコート
        court = pygame.Rect(400, 520, 120, 80)
        pygame.draw.rect(screen, (200, 200, 200), court)
        pygame.draw.rect(screen, (100, 100, 100), court, 2)
        
        # 砂場
        sandbox = pygame.Rect(1200, 520, 80, 60)
        pygame.draw.rect(screen, (238, 203, 173), sandbox)
    
    def draw_school_gate(self, screen: pygame.Surface):
        """豪華な校門を描画"""
        # 門柱（左右）
        left_pillar = pygame.Rect(750, 600, 30, 80)
        right_pillar = pygame.Rect(820, 600, 30, 80)
        
        pillar_color = (139, 69, 19)  # 煉瓦色
        pygame.draw.rect(screen, pillar_color, left_pillar)
        pygame.draw.rect(screen, pillar_color, right_pillar)
        
        # 門柱の装飾
        pygame.draw.rect(screen, (160, 82, 45), left_pillar, 3)
        pygame.draw.rect(screen, (160, 82, 45), right_pillar, 3)
        
        # 学校名プレート
        plate = pygame.Rect(770, 620, 60, 20)
        pygame.draw.rect(screen, (255, 215, 0), plate)
        pygame.draw.rect(screen, (0, 0, 0), plate, 2)
    
    def draw_school_fence(self, screen: pygame.Surface):
        """フェンスを描画"""
        fence_color = (100, 100, 100)
        
        # 水平線
        pygame.draw.line(screen, fence_color, (0, 680), (SCREEN_WIDTH, 680), 3)
        pygame.draw.line(screen, fence_color, (0, 690), (SCREEN_WIDTH, 690), 3)
        
        # 垂直ポスト
        for x in range(0, SCREEN_WIDTH, 50):
            pygame.draw.line(screen, fence_color, (x, 675), (x, 695), 5)
    
    def draw_road_system(self, screen: pygame.Surface):
        """道路システムを描画"""
        road_color = ADVANCED_COLORS['road']
        line_color = (255, 255, 255)
        
        # メイン道路（水平）
        pygame.draw.rect(screen, road_color, (0, 400, SCREEN_WIDTH, 100))
        # 中央線
        for x in range(0, SCREEN_WIDTH, 40):
            pygame.draw.rect(screen, line_color, (x, 448, 20, 4))
        
        # 縦道路
        pygame.draw.rect(screen, road_color, (750, 300, 100, 400))
        for y in range(300, 700, 40):
            pygame.draw.rect(screen, line_color, (798, y, 4, 20))
        
        # 横断歩道
        self.draw_crosswalk(screen, (750, 400), (100, 100))
    
    def draw_crosswalk(self, screen: pygame.Surface, pos: Tuple[int, int], size: Tuple[int, int]):
        """横断歩道を描画"""
        stripe_color = (255, 255, 255)
        for i in range(0, size[0], 15):
            stripe_rect = pygame.Rect(pos[0] + i, pos[1], 10, size[1])
            pygame.draw.rect(screen, stripe_color, stripe_rect)
    
    def draw_town_buildings(self, screen: pygame.Surface, time_slot: TimeSlot):
        """街の建物群を描画"""
        # 商店街
        shop_colors = ADVANCED_COLORS['shop_colors']
        for i, color in enumerate(shop_colors):
            shop_rect = pygame.Rect(700 + i * 80, 250, 70, 120)
            self.draw_building_with_shadow(screen, shop_rect, color, (150, 150, 150), time_slot)
        
        # 駅
        station_rect = pygame.Rect(1200, 320, 200, 100)
        station_color = ADVANCED_COLORS['station_color']
        self.draw_building_with_shadow(screen, station_rect, station_color, (100, 100, 150), time_slot)
        
        # カフェ
        cafe_rect = pygame.Rect(500, 450, 120, 80)
        cafe_color = ADVANCED_COLORS['cafe_color']
        self.draw_building_with_shadow(screen, cafe_rect, cafe_color, (150, 100, 50), time_slot)
    
    def draw_park(self, screen: pygame.Surface):
        """公園を描画"""
        # 公園エリア
        park_area = pygame.Rect(100, 200, 300, 200)
        pygame.draw.rect(screen, ADVANCED_COLORS['grass'], park_area)
        
        # 木々
        tree_positions = [(150, 250), (200, 280), (250, 240), (320, 300)]
        for pos in tree_positions:
            self.draw_tree(screen, pos)
        
        # ベンチ
        bench_rect = pygame.Rect(180, 320, 40, 15)
        pygame.draw.rect(screen, (139, 69, 19), bench_rect)
        
        # 池
        pond_rect = pygame.Rect(300, 320, 80, 60)
        pygame.draw.ellipse(screen, ADVANCED_COLORS['water'], pond_rect)
        
        # 散歩道
        path_points = [(120, 380), (200, 350), (280, 370), (380, 340)]
        for i in range(len(path_points) - 1):
            pygame.draw.line(screen, (200, 180, 140), path_points[i], path_points[i+1], 8)
    
    def draw_tree(self, screen: pygame.Surface, pos: Tuple[int, int]):
        """木を描画"""
        trunk_color = (101, 67, 33)
        leaf_color = (34, 139, 34)
        
        # 幹
        trunk_rect = pygame.Rect(pos[0] - 5, pos[1], 10, 30)
        pygame.draw.rect(screen, trunk_color, trunk_rect)
        
        # 葉
        pygame.draw.circle(screen, leaf_color, pos, 20)
        pygame.draw.circle(screen, (0, 100, 0), pos, 20, 2)
    
    def draw_river(self, screen: pygame.Surface):
        """川を描画"""
        # 川の本体
        river_points = [(0, 600), (300, 580), (600, 590), (900, 570), (SCREEN_WIDTH, 580)]
        if len(river_points) > 2:
            pygame.draw.lines(screen, ADVANCED_COLORS['water'], False, river_points, 40)
        
        # 橋
        bridge_rect = pygame.Rect(580, 565, 40, 50)
        pygame.draw.rect(screen, (139, 69, 19), bridge_rect)
        pygame.draw.rect(screen, (160, 82, 45), bridge_rect, 3)
        
        # 水の反射効果
        for i in range(0, SCREEN_WIDTH, 20):
            y_offset = 5 * math.sin(i * 0.1)
            pygame.draw.circle(screen, (100, 180, 255), (i, int(590 + y_offset)), 3)
    
    def draw_building_with_shadow(self, screen: pygame.Surface, rect: pygame.Rect, 
                                building_color: Tuple[int, int, int], roof_color: Tuple[int, int, int], 
                                time_slot: TimeSlot):
        """影付きの建物を描画"""
        # 影を描画
        shadow_offset = 5 if time_slot != TimeSlot.NIGHT else 2
        shadow_rect = rect.copy()
        shadow_rect.x += shadow_offset
        shadow_rect.y += shadow_offset
        shadow_color = (50, 50, 50, 100)  # 半透明の影
        
        # 影用の一時的なサーフェス
        shadow_surface = pygame.Surface((shadow_rect.width, shadow_rect.height), pygame.SRCALPHA)
        shadow_surface.fill(shadow_color)
        screen.blit(shadow_surface, shadow_rect)
        
        # 建物本体
        pygame.draw.rect(screen, building_color, rect)
        
        # 屋根
        roof_rect = pygame.Rect(rect.x - 5, rect.y - 10, rect.width + 10, 15)
        pygame.draw.rect(screen, roof_color, roof_rect)
        
        # 窓
        self.draw_windows(screen, rect, time_slot)
        
        # 建物の境界線
        pygame.draw.rect(screen, (0, 0, 0), rect, 2)
    
    def draw_windows(self, screen: pygame.Surface, building_rect: pygame.Rect, time_slot: TimeSlot):
        """窓を描画"""
        window_color = (200, 230, 255) if time_slot == TimeSlot.NIGHT else (150, 200, 255)
        
        # 窓の配置を計算
        window_width = 15
        window_height = 20
        rows = max(1, building_rect.height // 40)
        cols = max(1, building_rect.width // 30)
        
        for row in range(rows):
            for col in range(cols):
                x = building_rect.x + 10 + col * 30
                y = building_rect.y + 20 + row * 40
                
                if x + window_width < building_rect.right - 10 and y + window_height < building_rect.bottom - 10:
                    window_rect = pygame.Rect(x, y, window_width, window_height)
                    pygame.draw.rect(screen, window_color, window_rect)
                    pygame.draw.rect(screen, (100, 100, 100), window_rect, 1)
                    
                    # 夜の場合は照明効果
                    if time_slot == TimeSlot.NIGHT and random.random() > 0.3:
                        pygame.draw.rect(screen, (255, 255, 150), window_rect)
    
    def draw_location_labels(self, screen: pygame.Surface, locations: Dict[str, Dict]):
        """場所ラベルを描画"""
        font = pygame.font.Font(None, 24)
        
        for location_key, location_data in locations.items():
            pos = location_data['pos']
            label = location_data['label']
            
            # ラベルの背景
            text_surface = font.render(label, True, (0, 0, 0))
            text_rect = text_surface.get_rect()
            text_rect.center = (pos[0], pos[1] - 30)
            
            # 半透明背景
            bg_surface = pygame.Surface((text_rect.width + 10, text_rect.height + 4), pygame.SRCALPHA)
            bg_surface.fill((255, 255, 255, 180))
            screen.blit(bg_surface, (text_rect.x - 5, text_rect.y - 2))
            
            # テキスト
            screen.blit(text_surface, text_rect)
    
    def draw_location_marker(self, screen: pygame.Surface, pos: Tuple[int, int]):
        """場所マーカーを描画"""
        # 外側の円
        pygame.draw.circle(screen, (255, 255, 255), pos, 20, 3)
        # 中間の円
        pygame.draw.circle(screen, ADVANCED_COLORS['ui_border'], pos, 15, 2)
        # 内側の円
        pygame.draw.circle(screen, (255, 255, 255), pos, 10)
    
    @staticmethod
    def interpolate_color(color1: Tuple[int, int, int], color2: Tuple[int, int, int], ratio: float) -> Tuple[int, int, int]:
        """2つの色の間を補間"""
        r = int(color1[0] + (color2[0] - color1[0]) * ratio)
        g = int(color1[1] + (color2[1] - color1[1]) * ratio)
        b = int(color1[2] + (color2[2] - color1[2]) * ratio)
        return (r, g, b)