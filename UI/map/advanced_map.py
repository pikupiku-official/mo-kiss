import pygame
import sys
import math
import datetime
import os
import random
import csv
from typing import List, Dict, Tuple
from enum import Enum

# 初期化
pygame.init()

# 16:9比率のウィンドウサイズ
SCREEN_WIDTH = 1600
SCREEN_HEIGHT = 900
FPS = 60

# マップタイプの定義
class MapType(Enum):
    WEEKDAY = "weekday"    # 平日（学校のみ）
    WEEKEND = "weekend"    # 休日（街のみ）

# 時間進行の定義
class TimeSlot(Enum):
    MORNING = 0   # 朝
    NOON = 1      # 昼
    NIGHT = 2     # 夜

# 高品質カラーパレット
ADVANCED_COLORS = {
    # 時間帯別空の色
    'sky_colors': {
        TimeSlot.MORNING: [(135, 206, 250), (255, 218, 185), (255, 228, 225)],
        TimeSlot.NOON: [(87, 205, 249), (255, 255, 255), (220, 240, 255)],
        TimeSlot.NIGHT: [(25, 25, 112), (72, 61, 139), (123, 104, 238)]
    },
    
    # 建物色
    'school_building': (248, 245, 240),
    'school_roof': (169, 50, 38),
    'cafe_color': (205, 133, 63),
    'station_color': (176, 196, 222),
    'shop_colors': [(255, 182, 193), (152, 251, 152), (173, 216, 230)],
    
    # 地形色
    'grass': (34, 139, 34),
    'water': (64, 164, 223),
    'road': (64, 64, 64),
    'sidewalk': (192, 192, 192),
    
    # UI色
    'ui_glass': (255, 255, 255, 180),
    'ui_border': (70, 130, 180),
    'text_color': (33, 37, 41),
    'girl_icon': (255, 20, 147),
    'event_glow': (255, 215, 0),
}

class GameEvent:
    def __init__(self, event_id: str, start_date: str, end_date: str, time_slots: str, 
                 heroine: str, location: str, title: str, active: str):
        self.event_id = event_id
        self.start_date = self.parse_date(start_date)
        self.end_date = self.parse_date(end_date)
        self.time_slots = time_slots.split(';') if time_slots else []
        self.heroine = heroine
        self.location = location
        self.title = title
        self.active = active.upper() == 'TRUE'
    
    def parse_date(self, date_str: str) -> tuple:
        """日付文字列を解析 (例: '6月1日の朝' -> (6, 1, '朝'))"""
        import re
        match = re.match(r'(\d+)月(\d+)日の(朝|昼|夜)', date_str)
        if match:
            month, day, time_slot = match.groups()
            return (int(month), int(day), time_slot)
        return (6, 1, '朝')  # デフォルト値
    
    def is_active(self, current_date: datetime.date, current_time: str) -> bool:
        """現在の日時でイベントが有効かチェック"""
        if not self.active:
            return False
        
        # 日付の比較
        current_day_only = (current_date.month, current_date.day)
        start_day_only = (self.start_date[0], self.start_date[1])
        end_day_only = (self.end_date[0], self.end_date[1])
        
        # 期間内かつ指定時間帯かチェック
        is_in_period = start_day_only <= current_day_only <= end_day_only
        is_right_time = current_time in self.time_slots
        
        
        return is_in_period and is_right_time

class EventLocation:
    def __init__(self, name: str, x: int, y: int, description: str, location_type: str = "normal"):
        self.name = name
        self.x = x
        self.y = y
        self.description = description
        self.type = location_type
        self.has_event = False
        self.girl_characters = []
        self.hover_scale = 1.0
        self.pulse_time = 0
        self.glow_intensity = 0

class Character:
    def __init__(self, name: str, color: tuple, personality: str = "", image_file: str = ""):
        self.name = name
        self.color = color
        self.personality = personality
        self.image_file = image_file
        self.image = None
        self.circular_image = None
        self.current_location = None
        self.friendship_level = 0
        self.mood = "normal"

class AdvancedKimikissMap:
    def __init__(self):
        print("🚀 AdvancedKimikissMap 初期化開始...")
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Advanced Kimikiss Map - 曜日・時間システム")
        self.clock = pygame.time.Clock()
        self.running = True
        
        # デバッグモード検出
        self.debug_mode = self.is_debug_mode()
        
        # フォント設定
        self.init_fonts()
        
        # 時間・曜日システム
        self.current_date = datetime.date(1999, 5, 31)  # 開始日
        self.end_date = datetime.date(1999, 7, 1)       # 終了日
        self.current_time_slot = TimeSlot.MORNING
        # 自動時間進行システムを削除
        
        # マップ状態
        self.current_map_type = self.get_map_type()
        self.selected_location = None
        self.selected_character = None
        
        # エフェクト
        self.particles = []
        self.animation_time = 0
        self.clouds = self.init_clouds()  # 雲の初期化
        
        # データ初期化
        self.init_characters()
        self.load_events()  # イベントCSV読み込み
        
        # 実行済みイベント記録の管理 - /mo-kiss/events ディレクトリに配置
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))  # UI/map -> UI -> mo-kiss
        self.completed_events_file = os.path.join(project_root, "events", "completed_events.csv")
        
        # 実行時に常にCSVを初期化
        self.init_completed_events_csv()
        
        self.completed_events = self.load_completed_events()
        
        self.init_maps()
        self.update_events()
        
    def init_fonts(self):
        """フォント初期化（クロスプラットフォーム対応）"""
        import platform
        
        # 相対パスでのフォントファイル
        project_font_path = "../../fonts/MPLUSRounded1c-Regular.ttf"
        
        # プラットフォーム別システムフォントパス
        system_font_paths = []
        system_name = platform.system()
        
        if system_name == "Darwin":  # macOS
            system_font_paths = [
                "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc",
                "/Library/Fonts/ヒラギノ角ゴ ProN W3.otf",
                "/System/Library/Fonts/Arial Unicode MS.ttf"
            ]
        elif system_name == "Windows":  # Windows
            system_font_paths = [
                "C:/Windows/Fonts/msgothic.ttc",  # MS ゴシック
                "C:/Windows/Fonts/meiryo.ttc",    # メイリオ
                "C:/Windows/Fonts/arial.ttf"      # Arial
            ]
        else:  # Linux
            system_font_paths = [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
            ]
        
        # 試行するフォントパスリスト
        font_paths = [project_font_path] + system_font_paths
        
        self.fonts = {}
        font_loaded = False
        
        for path in font_paths:
            try:
                if os.path.exists(path):
                    self.fonts['title'] = pygame.font.Font(path, 32)
                    self.fonts['large'] = pygame.font.Font(path, 24)
                    self.fonts['medium'] = pygame.font.Font(path, 20)
                    self.fonts['small'] = pygame.font.Font(path, 16)
                    font_loaded = True
                    print(f"フォント読み込み成功: {path}")
                    break
            except Exception as e:
                print(f"フォント読み込み失敗: {path} - {e}")
                continue
        
        if not font_loaded:
            # システムフォントから日本語対応フォントを探す
            japanese_fonts = []
            if system_name == "Darwin":  # macOS
                japanese_fonts = [
                    'hiraginosans',         # ヒラギノサンス（内部名）
                    'hiraginokakugothicpro', # ヒラギノ角ゴ Pro
                    'arialunicodems',       # Arial Unicode MS
                    'applesdgothicneo',     # Apple SD ゴシック Neo
                    'geneva'                # Geneva
                ]
            elif system_name == "Windows":  # Windows
                japanese_fonts = [
                    'msgothic',     # MS Gothic
                    'meiryo',       # Meiryo  
                    'yugothic',     # Yu Gothic
                    'msmincho',     # MS Mincho
                    'arial'         # Arial
                ]
            else:  # Linux
                japanese_fonts = [
                    'dejavu sans',
                    'liberation sans', 
                    'noto sans cjk jp',
                    'arial'
                ]
            
            # 日本語対応システムフォントを試行
            for font_name in japanese_fonts:
                try:
                    test_font = pygame.font.SysFont(font_name, 16)
                    # 日本語文字のテスト描画
                    test_surface = test_font.render('あ', True, (0, 0, 0))
                    if test_surface.get_width() > 5:  # 最小サイズチェック
                        self.fonts['title'] = pygame.font.SysFont(font_name, 32, bold=True)
                        self.fonts['large'] = pygame.font.SysFont(font_name, 24, bold=True)
                        self.fonts['medium'] = pygame.font.SysFont(font_name, 20)
                        self.fonts['small'] = pygame.font.SysFont(font_name, 16)
                        font_loaded = True
                        print(f"システムフォント使用: {font_name}")
                        break
                except Exception as e:
                    print(f"フォント試行失敗: {font_name} - {e}")
                    continue
            
            # 最終的なフォールバック - 利用可能なフォントから日本語対応を探す
            if not font_loaded:
                print("⚠️ 利用可能なフォントから日本語対応フォントを検索中...")
                available_fonts = pygame.font.get_fonts()
                
                # 日本語系キーワードでフィルタリング
                japanese_keywords = ['hiragino', 'gothic', 'meiryo', 'yu', 'noto', 'sans', 'mincho']
                candidate_fonts = []
                
                for font in available_fonts:
                    if any(keyword in font.lower() for keyword in japanese_keywords):
                        candidate_fonts.append(font)
                
                # 候補フォントをテスト
                for font in candidate_fonts[:10]:  # 最初の10個をテスト
                    try:
                        test_font = pygame.font.SysFont(font, 16)
                        test_surface = test_font.render('テスト', True, (0, 0, 0))
                        if test_surface.get_width() > 10:
                            self.fonts['title'] = pygame.font.SysFont(font, 32, bold=True)
                            self.fonts['large'] = pygame.font.SysFont(font, 24, bold=True)
                            self.fonts['medium'] = pygame.font.SysFont(font, 20)
                            self.fonts['small'] = pygame.font.SysFont(font, 16)
                            font_loaded = True
                            print(f"✅ 動的検索で発見: {font}")
                            break
                    except:
                        continue
                
                # 最終的なデフォルトフォント
                if not font_loaded:
                    self.fonts['title'] = pygame.font.Font(None, 32)
                    self.fonts['large'] = pygame.font.Font(None, 24)
                    self.fonts['medium'] = pygame.font.Font(None, 20)
                    self.fonts['small'] = pygame.font.Font(None, 16)
                    print("⚠️ デフォルトフォント使用（日本語表示に問題がある可能性があります）")
    
    def is_debug_mode(self) -> bool:
        """デバッグモードかどうかを判定"""
        # 環境変数でデバッグモードを制御
        if os.environ.get('DEBUG', '').lower() in ('true', '1', 'yes'):
            return True
        
        # コマンドライン引数でデバッグモードを制御
        if '--debug' in sys.argv or '-d' in sys.argv:
            return True
        
        # PyCharm等のIDEから実行されている場合
        if 'PYCHARM_HOSTED' in os.environ:
            return True
            
        return False
    
    def init_completed_events_csv(self):
        """completed_events.csvを初期化"""
        print("🔄 completed_events.csvを初期化しています...")
        try:
            with open(self.completed_events_file, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['イベントID', '実行日時', 'ヒロイン名', '場所', 'イベントタイトル', '実行回数'])
            print("✅ completed_events.csv初期化完了")
        except Exception as e:
            print(f"❌ completed_events.csv初期化エラー: {e}")
    
    def get_map_type(self) -> MapType:
        """現在の曜日からマップタイプを判定"""
        weekday = self.current_date.weekday()  # 0=月曜, 6=日曜
        return MapType.WEEKDAY if weekday < 5 else MapType.WEEKEND
    
    def init_clouds(self):
        """雲の初期化（improved_map.pyと同じ）"""
        clouds = []
        for i in range(8):
            cloud = {
                'x': i * 200 + 50,
                'y': 30 + i * 15,
                'speed': 0.1 + i * 0.05,
                'size': 25 + i * 8,
                'opacity': 180 - i * 20
            }
            clouds.append(cloud)
        return clouds
    
    def init_characters(self):
        """キャラクター初期化"""
        print("🎯 init_characters メソッド実行中...")
        self.characters = [
            Character("烏丸神無", (255, 20, 147), "二年生　水泳部　孤高のギャル　本当はさみしがり屋さん　174cm", "Kanna.jpg"),
            Character("桔梗美鈴", (138, 43, 226), "三年生　元吹部　ずっと憧れの例の先輩、卒業近くなり急接近　170cm", "Misuzu.jpg"),
            Character("愛沼桃子", (255, 192, 203), "二年生　バド部　色白でふわふわ、クラスのムードメーカーなのだが…", "Momoko.jpeg"),
            Character("舞田沙那子", (75, 0, 130), "三年生　帰宅部　つっけんどんな先輩だが実は甘えんぼ！？髪が長い", "Sanako.jpg"),
            Character("宮月深依里", (176, 196, 222), "二年生　帰宅部　儚げなミステリアス　何故かよく隣の席になる同級生", "Miyori.jpg"),
            Character("伊織紅", (220, 20, 60), "一年生　弓道部　母性のある後輩　ちょっと僕のことを馬鹿にしている", "Kou.png"),
        ]
        
        # キャラクター画像を読み込み
        print("🔄 キャラクター画像読み込み開始...")
        self.load_character_images()
        print("✅ キャラクター画像読み込み完了")
        
    def load_character_images(self):
        """キャラクター画像を読み込み、円形に切り抜く"""
        print("📁 load_character_images メソッド実行中...")
        # 現在のファイルからの相対パスを確実に計算
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # UI/map から mo-kiss-main ルートディレクトリへ
        project_root = os.path.join(current_dir, "..", "..")
        project_root = os.path.abspath(project_root)  # 絶対パスに変換
        icon_dir = os.path.join(project_root, "images", "icons")
        icon_size = 35  # アイコンサイズ（通常時）
        
        print(f"プロジェクトルート: {project_root}")
        print(f"画像ディレクトリ: {icon_dir}")
        print(f"ディレクトリ存在確認: {os.path.exists(icon_dir)}")
        if os.path.exists(icon_dir):
            print(f"アイコンファイル一覧: {os.listdir(icon_dir)}")
        
        for char in self.characters:
            if char.image_file:
                try:
                    # 画像パスを構築
                    image_path = os.path.join(icon_dir, char.image_file)
                    print(f"読み込み試行: {image_path}")
                    print(f"ファイル存在確認: {os.path.exists(image_path)}")
                    
                    # 画像を読み込み
                    char.image = pygame.image.load(image_path)
                    
                    # 高解像度で画像を保存（複数サイズ用）
                    original_image = char.image
                    
                    # 円形に切り抜く（複数サイズ）
                    print(f"🔄 円形画像作成開始: {char.name}")
                    
                    # 小サイズ（マップ用）: 35px
                    small_image = pygame.transform.smoothscale(original_image, (35, 35))
                    char.circular_image = self.create_circular_image(small_image, 35)
                    
                    # 中サイズ（ホバー用）: 60px
                    medium_image = pygame.transform.smoothscale(original_image, (60, 60))
                    char.circular_image_hover = self.create_circular_image(medium_image, 60)
                    
                    # 大サイズ（パネル用）: 100px（超高品質）
                    large_image = pygame.transform.smoothscale(original_image, (100, 100))
                    char.circular_image_large = self.create_high_quality_circular_image(large_image, 100)
                    print(f"🔄 円形画像作成完了: {char.name}, 結果: {'成功' if char.circular_image else '失敗'}")
                    
                    print(f"✅ 画像読み込み成功: {char.name} - {char.image_file}")
                    print(f"   オブジェクトID: {id(char)}, circular_image: {'有' if char.circular_image else '無'}")
                    
                except Exception as e:
                    print(f"❌ 画像読み込み失敗: {char.name} - {char.image_file}: {e}")
                    char.circular_image = None
    
    def create_circular_image(self, image, size):
        """画像を円形に切り抜く"""
        print(f"      🎨 create_circular_image: サイズ={size}")
        try:
            # アルファチャンネル付きのサーフェスを作成
            circular_surface = pygame.Surface((size, size), pygame.SRCALPHA)
            circular_surface.fill((0, 0, 0, 0))  # 完全透明で初期化
            print(f"      ✅ サーフェス作成完了")
            
            # 円形マスクを作成
            center = size // 2
            radius = center - 1
            print(f"      🎯 円形処理開始: center={center}, radius={radius}")
            
            # 円の中だけ元画像を描画
            for x in range(size):
                for y in range(size):
                    distance = ((x - center) ** 2 + (y - center) ** 2) ** 0.5
                    if distance <= radius:
                        try:
                            # 元画像の色を取得
                            original_color = image.get_at((x, y))
                            circular_surface.set_at((x, y), original_color)
                        except IndexError:
                            pass
            
            print(f"      ✅ 円形処理完了")
            return circular_surface
            
        except Exception as e:
            print(f"      ❌ create_circular_image エラー: {e}")
            return None
    
    def create_high_quality_circular_image(self, image, size):
        """高品質な円形画像作成（アンチエイリアシング対応）"""
        try:
            # より大きいサイズで処理してからダウンスケール（スーパーサンプリング）
            oversample = 2
            large_size = size * oversample
            
            # 大きいサイズの画像を作成
            large_image = pygame.transform.smoothscale(image, (large_size, large_size))
            
            # アルファチャンネル付きのサーフェスを作成
            large_surface = pygame.Surface((large_size, large_size), pygame.SRCALPHA)
            large_surface.fill((0, 0, 0, 0))
            
            # 円形マスクを作成（大きいサイズで）
            center = large_size // 2
            radius = center - oversample
            
            # より滑らかな円形処理
            for x in range(large_size):
                for y in range(large_size):
                    distance = ((x - center) ** 2 + (y - center) ** 2) ** 0.5
                    if distance <= radius:
                        # エッジでのアルファブレンディング
                        alpha = 255
                        if distance > radius - oversample:
                            # エッジ部分で滑らかにフェード
                            fade = (radius - distance) / oversample
                            alpha = int(255 * max(0, min(1, fade)))
                        
                        try:
                            original_color = large_image.get_at((x, y))
                            if len(original_color) >= 3:
                                # アルファチャンネルを適用
                                color_with_alpha = (*original_color[:3], alpha)
                                large_surface.set_at((x, y), color_with_alpha)
                        except IndexError:
                            pass
            
            # 最終サイズにダウンスケール
            final_surface = pygame.transform.smoothscale(large_surface, (size, size))
            return final_surface
            
        except Exception as e:
            print(f"      ❌ create_high_quality_circular_image エラー: {e}")
            # フォールバック：通常の方法
            return self.create_circular_image(image, size)
    
    def load_events(self):
        """イベントCSVファイルを読み込み"""
        self.events = []
        try:
            # /mo-kiss/events ディレクトリのevents.csvを読み込み
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(current_dir))  # UI/map -> UI -> mo-kiss
            csv_path = os.path.join(project_root, 'events', 'events.csv')
            print(f"CSVファイルパス: {csv_path}")
            
            with open(csv_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    event = GameEvent(
                        event_id=row['イベントID'],
                        start_date=row['イベント開始日時'],
                        end_date=row['イベント終了日時'],
                        time_slots=row['イベントを選べる時間帯'],
                        heroine=row['対象のヒロイン'],
                        location=row['場所'],
                        title=row['イベントのタイトル'],
                        active=row['有効フラグ']
                    )
                    self.events.append(event)
            print(f"イベント読み込み完了: {len(self.events)}個のイベント")
        except FileNotFoundError:
            print("events.csvファイルが見つかりません")
            self.events = []
        except Exception as e:
            print(f"イベント読み込みエラー: {e}")
            self.events = []

    def load_completed_events(self):
        """実行済みイベントを読み込み"""
        completed_events = {}
        try:
            if os.path.exists(self.completed_events_file):
                with open(self.completed_events_file, 'r', encoding='utf-8') as file:
                    reader = csv.DictReader(file)
                    for row in reader:
                        event_id = row['イベントID']
                        completed_events[event_id] = {
                            'executed_at': row['実行日時'],
                            'heroine': row['ヒロイン名'],
                            'location': row['場所'],
                            'title': row['イベントタイトル'],
                            'count': int(row['実行回数'])
                        }
            print(f"実行済みイベント読み込み完了: {len(completed_events)}個")
        except Exception as e:
            print(f"実行済みイベント読み込みエラー: {e}")
            completed_events = {}
        
        return completed_events

    def save_completed_event(self, event_info):
        """イベント実行記録を保存"""
        try:
            # 現在の日時を取得
            now = datetime.datetime.now()
            executed_at = now.strftime("%Y-%m-%d %H:%M:%S")
            
            # 既存の記録があるかチェック
            event_id = event_info.event_id
            if event_id in self.completed_events:
                # 実行回数を増やす
                self.completed_events[event_id]['count'] += 1
                self.completed_events[event_id]['executed_at'] = executed_at
            else:
                # 新規記録
                self.completed_events[event_id] = {
                    'executed_at': executed_at,
                    'heroine': event_info.heroine,
                    'location': event_info.location,
                    'title': event_info.title,
                    'count': 1
                }
            
            # CSVファイルに保存
            self.write_completed_events_csv()
            print(f"✅ イベント実行記録を保存: {event_id}")
            
        except Exception as e:
            print(f"❌ イベント記録保存エラー: {e}")

    def write_completed_events_csv(self):
        """実行済みイベントをCSVファイルに書き込み"""
        try:
            with open(self.completed_events_file, 'w', encoding='utf-8', newline='') as file:
                fieldnames = ['イベントID', '実行日時', 'ヒロイン名', '場所', 'イベントタイトル', '実行回数']
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                
                # ヘッダーを書き込み
                writer.writeheader()
                
                # データを書き込み
                for event_id, data in self.completed_events.items():
                    writer.writerow({
                        'イベントID': event_id,
                        '実行日時': data['executed_at'],
                        'ヒロイン名': data['heroine'],
                        '場所': data['location'],
                        'イベントタイトル': data['title'],
                        '実行回数': data['count']
                    })
                    
        except Exception as e:
            print(f"❌ CSV書き込みエラー: {e}")

    def is_event_completed(self, event_id):
        """イベントが実行済みかチェック"""
        return event_id in self.completed_events
    
    def refresh_events(self):
        """イベントリストを再読み込み（外部から呼び出し用）"""
        self.load_events()
        self.update_events()
        print("🔄 イベントリスト再読み込み完了")
    
    def init_maps(self):
        """マップ初期化"""
        # 平日マップ（学校のみ）- 建物描画に合わせて位置調整
        self.weekday_locations = [
            EventLocation("教室", 390, 345, "みんなが集まる教室", "classroom"),  # 本館中央
            EventLocation("図書館", 675, 415, "静かで落ち着いた図書館", "library"),  # 理科棟
            EventLocation("体育館", 260, 535, "体育の授業や部活で使う体育館", "gym"),  # 体育館建物中央
            EventLocation("購買部", 510, 350, "パンや飲み物を買える購買部", "shop"),  # 本館と東棟の間
            EventLocation("屋上", 390, 310, "景色の良い学校の屋上", "rooftop"),  # 本館屋上
            EventLocation("学校正門", 390, 250, "学校の正門", "gate"),  # 正門位置
        ]
        
        # 休日マップ（街のみ）- 以前の座標に合わせて調整
        self.weekend_locations = [
            EventLocation("公園", 130, 650, "緑豊かな公園", "park"),
            EventLocation("駅前", 700, 610, "賑やかな駅前広場", "station"),
            EventLocation("商店街", 680, 400, "活気ある商店街", "shopping"),
            EventLocation("カフェ", 360, 420, "おしゃれなカフェ", "cafe"),
        ]
    
    def get_current_locations(self) -> List[EventLocation]:
        """現在のマップタイプに応じた場所リストを取得"""
        # 平日夜と休日は街マップを使用
        if self.current_map_type == MapType.WEEKDAY and self.current_time_slot == TimeSlot.NIGHT:
            return self.weekend_locations  # 夜は街
        elif self.current_map_type == MapType.WEEKEND:
            return self.weekend_locations  # 休日は街
        else:
            return self.weekday_locations   # 平日朝・昼・夕方は学校
    
    def advance_time_after_event(self):
        """イベント終了後の時間進行"""
        current_slots = list(TimeSlot)
        current_index = current_slots.index(self.current_time_slot)
        
        if current_index < len(current_slots) - 1:
            # 次の時間帯
            self.current_time_slot = current_slots[current_index + 1]
        else:
            # 次の日
            self.current_time_slot = TimeSlot.MORNING
            self.current_date += datetime.timedelta(days=1)
            self.current_map_type = self.get_map_type()
            
            # 7/1を過ぎたらゲーム終了
            if self.current_date > self.end_date:
                print("ゲーム期間が終了しました。ありがとうございました！")
                self.running = False
                return
        
        # イベント更新
        self.update_events()
        self.selected_location = None
        self.selected_character = None
        
        print(f"イベント終了後、時間が進みました: {self.get_time_display()}")
    
    
    def update_events(self):
        """イベント状態を更新（CSVベース）"""
        current_locations = self.get_current_locations()
        
        # 全てのキャラクターの場所をリセット
        for location in current_locations:
            location.girl_characters = []
            location.has_event = False
        
        # 現在の時間帯名を取得
        time_names = {
            TimeSlot.MORNING: "朝",
            TimeSlot.NOON: "昼", 
            TimeSlot.NIGHT: "夜"
        }
        current_time_name = time_names[self.current_time_slot]
        
        # アクティブなイベントをチェック（実行済みは除外）
        active_events = []
        for event in self.events:
            if (event.is_active(self.current_date, current_time_name) and
                not self.is_event_completed(event.event_id)):  # 実行済みイベントを除外
                active_events.append(event)
        
        # 全イベント数と利用可能イベント数を表示
        all_active_events = [event for event in self.events if event.is_active(self.current_date, current_time_name)]
        completed_active_events = [event for event in all_active_events if self.is_event_completed(event.event_id)]
        
        print(f"📅 {self.current_date.month}月{self.current_date.day}日 {current_time_name}: "
              f"利用可能{len(active_events)}個 / 全{len(all_active_events)}個のイベント "
              f"(実行済み: {len(completed_active_events)}個)")
        
        if len(active_events) > 0:
            for event in active_events:
                print(f"   → {event.event_id}: {event.heroine} @ {event.location} (時間帯: {event.time_slots})")
        
        if len(completed_active_events) > 0:
            print(f"   実行済み:")
            for event in completed_active_events:
                print(f"   ✅ {event.event_id}: {event.heroine} @ {event.location}")
        
        # 現在のマップタイプと利用可能場所をログ
        current_locations = self.get_current_locations()
        map_type_name = "学校" if self.current_map_type == MapType.WEEKDAY else "街"
        if self.current_map_type == MapType.WEEKDAY and self.current_time_slot == TimeSlot.NIGHT:
            map_type_name = "街(夜)"
        print(f"   現在のマップ: {map_type_name}, 利用可能場所: {[loc.name for loc in current_locations]}")
        
        # イベントがあるキャラクターのみを配置（キャラクター×場所の組み合わせで重複回避）
        placed_character_locations = set()
        for event in active_events:
            # 同じキャラクターが同じ場所に複数イベントがある場合、最初のものだけ使用
            character_location_key = f"{event.heroine}@{event.location}"
            if character_location_key in placed_character_locations:
                continue
                
            event_placed = False
            for location in current_locations:
                if location.name == event.location:
                    # キャラクターを見つけて配置
                    char_found = False
                    for character in self.characters:
                        if character.name == event.heroine:
                            # 元のキャラクターオブジェクト（画像データ付き）を使用
                            location.girl_characters.append(character)
                            location.has_event = True
                            print(f"   ✅ {event.heroine} → {event.location}")
                            print(f"      現在の{event.location}のキャラクター数: {len(location.girl_characters)}")
                            placed_character_locations.add(character_location_key)
                            event_placed = True
                            char_found = True
                            break
                    
                    if not char_found:
                        print(f"   ❌ キャラクター '{event.heroine}' が見つかりません")
                        print(f"      利用可能キャラ: {[c.name for c in self.characters]}")
                    if event_placed:
                        break
            
            if not event_placed:
                print(f"   ❌ 場所 '{event.location}' が見つかりません ({event.heroine}のイベント)")
    
    def get_time_display(self) -> str:
        """時間表示用文字列を取得"""
        time_names = {
            TimeSlot.MORNING: "朝",
            TimeSlot.NOON: "昼", 
            TimeSlot.NIGHT: "夜"
        }
        
        weekday_names = ["月", "火", "水", "木", "金", "土", "日"]
        weekday = weekday_names[self.current_date.weekday()]
        
        map_type_name = "学校" if self.current_map_type == MapType.WEEKDAY else "街"
        
        return f"{self.current_date.month}月{self.current_date.day}日({weekday}) {time_names[self.current_time_slot]} - {map_type_name}"
    
    def draw_advanced_sky(self):
        """高品質な空の描画 - 画面上部1/4のみ"""
        colors = ADVANCED_COLORS['sky_colors'][self.current_time_slot]
        sky_height = SCREEN_HEIGHT // 4  # 画面上部1/4に制限
        
        # 3色グラデーション
        for y in range(sky_height):
            ratio = y / sky_height
            
            if ratio < 0.5:
                t = ratio * 2
                r = int(colors[0][0] + (colors[1][0] - colors[0][0]) * t)
                g = int(colors[0][1] + (colors[1][1] - colors[0][1]) * t)
                b = int(colors[0][2] + (colors[1][2] - colors[0][2]) * t)
            else:
                t = (ratio - 0.5) * 2
                r = int(colors[1][0] + (colors[2][0] - colors[1][0]) * t)
                g = int(colors[1][1] + (colors[2][1] - colors[1][1]) * t)
                b = int(colors[1][2] + (colors[2][2] - colors[1][2]) * t)
            
            pygame.draw.line(self.screen, (r, g, b), (0, y), (SCREEN_WIDTH - 350, y))
    
    def draw_clouds(self):
        """雲の描画とアニメーション（improved_map.pyと同じ）"""
        for cloud in self.clouds:
            # 雲の移動
            cloud['x'] += cloud['speed']
            if cloud['x'] > SCREEN_WIDTH + cloud['size']:
                cloud['x'] = -cloud['size'] * 3
            
            # 時間帯による雲の色調整
            time_tints = [
                (255, 255, 255),  # 朝 - 白
                (255, 255, 255),  # 昼 - 白  
                (255, 200, 150),  # 夕方 - オレンジがかった白
                (200, 200, 255)   # 夜 - 青みがかった白
            ]
            
            tint = time_tints[self.current_time_slot.value]
            cloud_color = (*tint, cloud['opacity'])
            
            # 雲の描画（複数の円で雲らしく）
            cloud_surface = pygame.Surface((cloud['size'] * 4, cloud['size'] * 2), pygame.SRCALPHA)
            
            # より自然な雲の形状
            centers = [
                (cloud['size'] // 2, cloud['size']),
                (cloud['size'], cloud['size'] // 2), 
                (cloud['size'] * 2, cloud['size']),
                (cloud['size'] * 3, cloud['size'] // 3)
            ]
            
            for i, (cx, cy) in enumerate(centers):
                radius = cloud['size'] // 2 + i * 3
                pygame.draw.circle(cloud_surface, cloud_color, (cx, cy), radius)
            
            self.screen.blit(cloud_surface, (cloud['x'], cloud['y']))
    
    def draw_terrain(self):
        """地形描画 - 空の下の緑地エリア（画面全体）"""
        # 地面は空の下から画面下端まで
        ground_start = SCREEN_HEIGHT // 4
        ground_end = SCREEN_HEIGHT
        
        for y in range(ground_start, ground_end):
            ratio = (y - ground_start) / (ground_end - ground_start)
            base_color = ADVANCED_COLORS['grass']
            darker_color = (max(0, base_color[0] - 30), max(0, base_color[1] - 30), max(0, base_color[2] - 30))
            
            r = max(0, min(255, int(base_color[0] + (darker_color[0] - base_color[0]) * ratio)))
            g = max(0, min(255, int(base_color[1] + (darker_color[1] - base_color[1]) * ratio)))
            b = max(0, min(255, int(base_color[2] + (darker_color[2] - base_color[2]) * ratio)))
            
            pygame.draw.line(self.screen, (r, g, b), (0, y), (SCREEN_WIDTH - 350, y))
    
    def draw_weekday_map(self):
        """平日マップ（学校）の描画 - 鳥瞰図"""
        # 校舎レイアウト（上から見た図）
        self.draw_school_buildings()
        
        # 校庭
        self.draw_school_yard()
        
        # 校門
        self.draw_school_gate()
        
        # 学校敷地境界
        self.draw_school_boundary()
    
    def draw_school_buildings(self):
        """高品質校舎群の描画（プロ仕様鳥瞰図）"""
        # メイン校舎（現代的なデザイン）
        main_building = pygame.Rect(280, 300, 220, 90)
        east_wing = pygame.Rect(500, 300, 90, 170)
        
        # 高品質な影とグラデーション
        self.draw_premium_building_shadow(main_building, 6)
        self.draw_premium_building_shadow(east_wing, 6)
        
        # メイン校舎（グラデーション屋根）
        self.draw_premium_building(main_building, ADVANCED_COLORS['school_building'], "main")
        
        # 東棟（少し異なる色調）
        east_color = (max(0, ADVANCED_COLORS['school_building'][0] - 10), 
                     max(0, ADVANCED_COLORS['school_building'][1] - 5), 
                     max(0, ADVANCED_COLORS['school_building'][2] - 5))
        self.draw_premium_building(east_wing, east_color, "east")
        
        # 高品質屋上設備
        self.draw_premium_rooftop_equipment(main_building, east_wing)
        
        # 詳細な教室・窓システム
        self.draw_detailed_windows(main_building, 5, 3)
        self.draw_detailed_windows(east_wing, 3, 6)
        
        # プレミアム体育館
        gym_rect = pygame.Rect(190, 480, 140, 110)
        self.draw_premium_building_shadow(gym_rect, 8)
        self.draw_premium_gym(gym_rect)
        
        # 特別教室棟（理科棟風）
        special_building = pygame.Rect(620, 350, 110, 130)
        self.draw_premium_building_shadow(special_building, 6)
        special_color = (210, 200, 190)
        self.draw_premium_building(special_building, special_color, "special")
        self.draw_detailed_windows(special_building, 4, 5)
        
        # 渡り廊下
        self.draw_connecting_corridors()
        
        # 建物ラベル
        self.draw_building_labels()
    
    def draw_premium_building_shadow(self, building_rect, depth):
        """高品質な建物影の描画"""
        for i in range(depth):
            alpha = 120 - (i * 15)
            shadow_rect = building_rect.copy()
            shadow_rect.move_ip(i + 3, i + 3)
            
            shadow_surf = pygame.Surface((shadow_rect.width, shadow_rect.height), pygame.SRCALPHA)
            shadow_surf.fill((0, 0, 0, alpha))
            self.screen.blit(shadow_surf, shadow_rect)
    
    def draw_premium_building(self, rect, base_color, building_type):
        """高品質な建物描画（グラデーション・テクスチャ付き）"""
        # ベース建物
        pygame.draw.rect(self.screen, base_color, rect)
        
        # 上部のハイライト
        highlight_color = (min(255, base_color[0] + 20), 
                          min(255, base_color[1] + 20), 
                          min(255, base_color[2] + 20))
        highlight_rect = pygame.Rect(rect.left, rect.top, rect.width, rect.height // 3)
        pygame.draw.rect(self.screen, highlight_color, highlight_rect)
        
        # グラデーション効果
        for y in range(rect.height):
            ratio = y / rect.height
            r = max(0, min(255, int(highlight_color[0] + (base_color[0] - highlight_color[0]) * ratio)))
            g = max(0, min(255, int(highlight_color[1] + (base_color[1] - highlight_color[1]) * ratio)))
            b = max(0, min(255, int(highlight_color[2] + (base_color[2] - highlight_color[2]) * ratio)))
            pygame.draw.line(self.screen, (r, g, b), 
                           (rect.left, rect.top + y), (rect.right, rect.top + y))
        
        # 建物の輪郭（立体感）
        pygame.draw.rect(self.screen, (80, 80, 80), rect, 2)
        
        # コーナーの強調
        corner_size = 8
        corner_color = (60, 60, 60)
        corners = [
            (rect.left, rect.top),
            (rect.right - corner_size, rect.top),
            (rect.left, rect.bottom - corner_size),
            (rect.right - corner_size, rect.bottom - corner_size)
        ]
        for corner_x, corner_y in corners:
            corner_rect = pygame.Rect(corner_x, corner_y, corner_size, corner_size)
            pygame.draw.rect(self.screen, corner_color, corner_rect)
    
    def draw_premium_rooftop_equipment(self, main_building, east_wing):
        """高品質屋上設備"""
        # メイン校舎の設備
        equipment_data = [
            # (x, y, width, height, equipment_type)
            (main_building.centerx - 40, main_building.centery - 15, 25, 18, "hvac"),
            (main_building.centerx + 15, main_building.centery + 10, 20, 15, "hvac"),
            (main_building.right - 30, main_building.centery, 15, 12, "antenna"),
            (east_wing.centerx - 10, east_wing.centery - 20, 18, 14, "hvac"),
            (east_wing.centerx, east_wing.centery + 30, 12, 8, "solar")
        ]
        
        for x, y, w, h, eq_type in equipment_data:
            equipment_rect = pygame.Rect(x, y, w, h)
            
            if eq_type == "hvac":
                # 空調設備
                pygame.draw.rect(self.screen, (160, 160, 160), equipment_rect)
                pygame.draw.rect(self.screen, (120, 120, 120), equipment_rect, 2)
                # 通気口
                for i in range(3):
                    vent_x = x + 3 + i * 6
                    vent_y = y + h // 2
                    pygame.draw.line(self.screen, (100, 100, 100), 
                                   (vent_x, vent_y - 3), (vent_x, vent_y + 3), 1)
            elif eq_type == "antenna":
                # アンテナ
                pygame.draw.rect(self.screen, (140, 140, 140), equipment_rect)
                pygame.draw.line(self.screen, (100, 100, 100),
                               (x + w//2, y), (x + w//2, y - 15), 2)
            elif eq_type == "solar":
                # ソーラーパネル
                pygame.draw.rect(self.screen, (20, 30, 80), equipment_rect)
                pygame.draw.rect(self.screen, (100, 100, 100), equipment_rect, 1)
    
    def draw_detailed_windows(self, building_rect, cols, rows):
        """詳細な窓システム"""
        window_margin = 12
        window_spacing_x = (building_rect.width - window_margin * 2) // cols
        window_spacing_y = (building_rect.height - window_margin * 2) // rows
        window_width = window_spacing_x - 8
        window_height = window_spacing_y - 6
        
        for row in range(rows):
            for col in range(cols):
                window_x = building_rect.left + window_margin + col * window_spacing_x + 4
                window_y = building_rect.top + window_margin + row * window_spacing_y + 3
                window_rect = pygame.Rect(window_x, window_y, window_width, window_height)
                
                # 時間帯による窓の色
                if self.current_time_slot == TimeSlot.NIGHT:
                    window_color = (255, 240, 120)  # 暖かい光
                    glow_radius = 3
                    # 光のにじみ効果
                    for i in range(glow_radius):
                        glow_rect = window_rect.inflate(i * 2, i * 2)
                        glow_alpha = 40 - i * 10
                        glow_surf = pygame.Surface((glow_rect.width, glow_rect.height), pygame.SRCALPHA)
                        glow_surf.fill((*window_color, glow_alpha))
                        self.screen.blit(glow_surf, glow_rect)
                else:
                    window_color = (180, 220, 255)  # 昼間の反射
                
                # 窓本体
                pygame.draw.rect(self.screen, window_color, window_rect)
                
                # 窓枠
                pygame.draw.rect(self.screen, (90, 90, 90), window_rect, 2)
                
                # 窓の十字枠
                center_x = window_rect.centerx
                center_y = window_rect.centery
                pygame.draw.line(self.screen, (90, 90, 90),
                               (center_x, window_rect.top), (center_x, window_rect.bottom), 1)
                pygame.draw.line(self.screen, (90, 90, 90),
                               (window_rect.left, center_y), (window_rect.right, center_y), 1)
    
    def draw_premium_gym(self, gym_rect):
        """高品質体育館"""
        # グラデーション背景
        gym_color = (180, 180, 200)
        darker_gym = (150, 150, 170)
        
        for y in range(gym_rect.height):
            ratio = y / gym_rect.height
            r = max(0, min(255, int(gym_color[0] + (darker_gym[0] - gym_color[0]) * ratio)))
            g = max(0, min(255, int(gym_color[1] + (darker_gym[1] - gym_color[1]) * ratio)))
            b = max(0, min(255, int(gym_color[2] + (darker_gym[2] - gym_color[2]) * ratio)))
            pygame.draw.line(self.screen, (r, g, b),
                           (gym_rect.left, gym_rect.top + y), (gym_rect.right, gym_rect.top + y))
        
        # 体育館の特徴的な屋根構造
        roof_peaks = [
            (gym_rect.left + gym_rect.width // 4, gym_rect.top),
            (gym_rect.left + 3 * gym_rect.width // 4, gym_rect.top)
        ]
        
        for peak_x, peak_y in roof_peaks:
            roof_color = (120, 120, 140)
            pygame.draw.polygon(self.screen, roof_color, [
                (peak_x - 15, peak_y + 10),
                (peak_x + 15, peak_y + 10),
                (peak_x, peak_y - 8)
            ])
        
        # 大きな窓（体育館特有）
        large_windows = [
            pygame.Rect(gym_rect.left + 20, gym_rect.top + 25, 25, 40),
            pygame.Rect(gym_rect.right - 45, gym_rect.top + 25, 25, 40),
            pygame.Rect(gym_rect.left + 50, gym_rect.top + 25, 25, 40),
            pygame.Rect(gym_rect.right - 75, gym_rect.top + 25, 25, 40)
        ]
        
        for window in large_windows:
            pygame.draw.rect(self.screen, (200, 230, 255), window)
            pygame.draw.rect(self.screen, (80, 80, 80), window, 2)
        
        # 体育館入口
        entrance_rect = pygame.Rect(gym_rect.centerx - 15, gym_rect.bottom - 12, 30, 12)
        pygame.draw.rect(self.screen, (120, 80, 60), entrance_rect)
        pygame.draw.rect(self.screen, (80, 80, 80), entrance_rect, 2)
        
        pygame.draw.rect(self.screen, (80, 80, 80), gym_rect, 3)
    
    def draw_connecting_corridors(self):
        """渡り廊下の描画"""
        corridors = [
            # メイン校舎と東棟を繋ぐ
            pygame.Rect(490, 340, 20, 30),
            # 特別教室棟への渡り廊下
            pygame.Rect(590, 380, 40, 12)
        ]
        
        for corridor in corridors:
            pygame.draw.rect(self.screen, (200, 200, 210), corridor)
            pygame.draw.rect(self.screen, (120, 120, 120), corridor, 2)
            
            # 屋根
            roof_rect = corridor.inflate(6, 4)
            roof_rect.move_ip(-3, -8)
            pygame.draw.rect(self.screen, (180, 180, 190), roof_rect)
            pygame.draw.rect(self.screen, (100, 100, 100), roof_rect, 1)
    
    def draw_building_labels(self):
        """建物ラベル"""
        labels = [
            (380, 345, "本館", self.fonts['small']),
            (545, 385, "東棟", self.fonts['small']),
            (250, 535, "体育館", self.fonts['small']),
            (665, 415, "理科棟", self.fonts['small'])
        ]
        
        for x, y, text, font in labels:
            # ラベル背景
            text_surf = font.render(text, True, (50, 50, 50))
            bg_rect = text_surf.get_rect(center=(x, y))
            bg_rect.inflate_ip(8, 4)
            
            bg_surf = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
            bg_surf.fill((255, 255, 255, 200))
            self.screen.blit(bg_surf, bg_rect)
            
            pygame.draw.rect(self.screen, (150, 150, 150), bg_rect, 1)
            self.screen.blit(text_surf, text_surf.get_rect(center=(x, y)))
    
    def draw_school_yard(self):
        """高品質校庭の描画"""
        # メインの校庭エリア（グラデーション土）
        yard_rect = pygame.Rect(340, 500, 200, 130)
        self.draw_textured_ground(yard_rect, (139, 126, 102), (120, 110, 90))
        
        # プロ仕様トラック
        track_outer = pygame.Rect(350, 510, 180, 90)
        track_inner = pygame.Rect(370, 525, 140, 60)
        
        # トラックの影
        shadow_track = track_outer.copy()
        shadow_track.move_ip(2, 2)
        pygame.draw.ellipse(self.screen, (0, 0, 0, 60), shadow_track)
        
        # トラック表面
        pygame.draw.ellipse(self.screen, (180, 90, 70), track_outer)
        pygame.draw.ellipse(self.screen, (50, 140, 50), track_inner)  # 内側芝生
        
        # トラックのレーン線
        for i in range(1, 4):
            lane_rect = track_outer.inflate(-i*15, -i*10)
            pygame.draw.ellipse(self.screen, (255, 255, 255), lane_rect, 2)
        
        # 100mライン
        start_line_x = track_outer.left + 20
        pygame.draw.line(self.screen, (255, 255, 255),
                        (start_line_x, track_outer.top + 15),
                        (start_line_x, track_outer.bottom - 15), 3)
        
        # 高品質運動設備
        self.draw_premium_sports_equipment()
        
        # 観客席・ベンチ
        self.draw_school_seating()
        
        # 植栽・樹木
        self.draw_school_landscaping()
    
    def draw_textured_ground(self, rect, base_color, shadow_color):
        """テクスチャ付き地面"""
        # ベースグラデーション
        for y in range(rect.height):
            ratio = y / rect.height
            r = max(0, min(255, int(base_color[0] + (shadow_color[0] - base_color[0]) * ratio)))
            g = max(0, min(255, int(base_color[1] + (shadow_color[1] - base_color[1]) * ratio)))
            b = max(0, min(255, int(base_color[2] + (shadow_color[2] - base_color[2]) * ratio)))
            pygame.draw.line(self.screen, (r, g, b),
                           (rect.left, rect.top + y), (rect.right, rect.top + y))
        
        # テクスチャノイズ
        import random
        for _ in range(rect.width * rect.height // 50):
            noise_x = rect.left + random.randint(0, rect.width - 1)
            noise_y = rect.top + random.randint(0, rect.height - 1)
            noise_color = (max(0, min(255, base_color[0] + random.randint(-15, 15))),
                          max(0, min(255, base_color[1] + random.randint(-15, 15))),
                          max(0, min(255, base_color[2] + random.randint(-15, 15))))
            pygame.draw.circle(self.screen, noise_color, (noise_x, noise_y), 1)
    
    def draw_premium_sports_equipment(self):
        """高品質運動設備"""
        
        # バスケットボールコート
        court_rect = pygame.Rect(560, 520, 40, 80)
        pygame.draw.rect(self.screen, (200, 180, 160), court_rect, 2)
        
        # バスケットゴール（2つ）
        goal_positions = [(court_rect.centerx, court_rect.top + 10),
                         (court_rect.centerx, court_rect.bottom - 10)]
        
        for goal_x, goal_y in goal_positions:
            # ポール
            pygame.draw.line(self.screen, (150, 150, 150), (goal_x, goal_y), (goal_x, goal_y - 15), 3)
            # バックボード
            backboard = pygame.Rect(goal_x - 8, goal_y - 20, 16, 12)
            pygame.draw.rect(self.screen, (255, 255, 255), backboard)
            pygame.draw.rect(self.screen, (100, 100, 100), backboard, 1)
            # リング
            pygame.draw.circle(self.screen, (255, 100, 0), (goal_x, goal_y - 12), 4, 2)
        
        # 砂場
        sandbox_rect = pygame.Rect(270, 620, 60, 40)
        pygame.draw.rect(self.screen, (240, 220, 180), sandbox_rect)
        pygame.draw.rect(self.screen, (180, 160, 120), sandbox_rect, 2)
        # 砂のテクスチャ
        for _ in range(20):
            import random
            sand_x = sandbox_rect.left + random.randint(5, sandbox_rect.width - 5)
            sand_y = sandbox_rect.top + random.randint(5, sandbox_rect.height - 5)
            pygame.draw.circle(self.screen, (220, 200, 160), (sand_x, sand_y), 1)
    
    def draw_school_seating(self):
        """観客席・ベンチ"""
        # 観客席を校庭エリア内に移動し、より自然に
        bleacher_rect = pygame.Rect(560, 630, 60, 15)
        for i in range(3):
            step_rect = pygame.Rect(bleacher_rect.left, bleacher_rect.top + i * 5, 
                                   bleacher_rect.width, 5)
            # より自然な色調に変更
            step_color = (140, 120, 100)  # 木製ベンチ風
            pygame.draw.rect(self.screen, step_color, step_rect)
            pygame.draw.rect(self.screen, (100, 80, 60), step_rect, 1)
        
        # ベンチ
        bench_positions = [(420, 680), (480, 680), (540, 680)]
        for bench_x, bench_y in bench_positions:
            # 影
            shadow_rect = pygame.Rect(bench_x + 2, bench_y + 2, 35, 8)
            pygame.draw.rect(self.screen, (0, 0, 0, 60), shadow_rect)
            
            # ベンチ本体
            bench_rect = pygame.Rect(bench_x, bench_y, 35, 8)
            pygame.draw.rect(self.screen, (139, 119, 101), bench_rect)
            pygame.draw.rect(self.screen, (100, 80, 60), bench_rect, 1)
            
            # 脚
            for leg_offset in [5, 25]:
                leg_rect = pygame.Rect(bench_x + leg_offset, bench_y + 8, 4, 6)
                pygame.draw.rect(self.screen, (120, 100, 80), leg_rect)
    
    def draw_school_landscaping(self):
        """校内植栽"""
        # 大きな樹木
        tree_positions = [
            (260, 450, 25),  # 左上の木をさらに上に移動
            (600, 500, 20),
            (280, 680, 18),
            (580, 680, 22)
        ]
        
        for tree_x, tree_y, tree_size in tree_positions:
            # 木の影
            shadow_ellipse = pygame.Rect(tree_x - tree_size + 3, tree_y - tree_size + 3,
                                       tree_size * 2, tree_size * 2)
            pygame.draw.ellipse(self.screen, (0, 0, 0, 40), shadow_ellipse)
            
            # 幹
            trunk_rect = pygame.Rect(tree_x - 4, tree_y, 8, tree_size)
            pygame.draw.rect(self.screen, (101, 67, 33), trunk_rect)
            
            # 葉（多層）
            leaf_colors = [(34, 139, 34), (50, 205, 50), (0, 128, 0)]
            leaf_sizes = [tree_size, tree_size - 5, tree_size - 10]
            
            for i, (leaf_color, leaf_size) in enumerate(zip(leaf_colors, leaf_sizes)):
                if leaf_size > 0:
                    offset_x = (-2 + i) * 2
                    offset_y = (-1 + i) * 2
                    pygame.draw.circle(self.screen, leaf_color,
                                     (tree_x + offset_x, tree_y - tree_size // 2 + offset_y),
                                     leaf_size)
        
    
    def draw_school_gate(self):
        """高品質校門の描画"""
        # 立派な門柱（煉瓦風）
        gate_post1 = pygame.Rect(375, 245, 18, 40)
        gate_post2 = pygame.Rect(460, 245, 18, 40)
        
        # 門柱の影
        for post in [gate_post1, gate_post2]:
            shadow_post = post.copy()
            shadow_post.move_ip(3, 3)
            pygame.draw.rect(self.screen, (0, 0, 0, 100), shadow_post)
        
        # 門柱（煉瓦テクスチャ）
        brick_color = (180, 140, 120)
        for post in [gate_post1, gate_post2]:
            pygame.draw.rect(self.screen, brick_color, post)
            
            # 煉瓦のライン
            for y in range(0, post.height, 8):
                line_y = post.top + y
                pygame.draw.line(self.screen, (160, 120, 100),
                               (post.left, line_y), (post.right, line_y), 1)
            
            # 門柱のキャップ
            cap_rect = pygame.Rect(post.left - 3, post.top - 8, post.width + 6, 8)
            pygame.draw.rect(self.screen, (150, 110, 90), cap_rect)
            pygame.draw.rect(self.screen, (120, 80, 60), cap_rect, 1)
        
        # 豪華な門扉（開いた状態）
        gate_width = 25
        gate_height = 30
        
        # 左門扉
        left_gate_rect = pygame.Rect(gate_post1.right + 5, gate_post1.top + 5, gate_width, gate_height)
        pygame.draw.rect(self.screen, (40, 60, 40), left_gate_rect)
        pygame.draw.rect(self.screen, (80, 100, 80), left_gate_rect, 2)
        
        # 右門扉
        right_gate_rect = pygame.Rect(gate_post2.left - 5 - gate_width, gate_post2.top + 5, gate_width, gate_height)
        pygame.draw.rect(self.screen, (40, 60, 40), right_gate_rect)
        pygame.draw.rect(self.screen, (80, 100, 80), right_gate_rect, 2)
        
        # 門扉の装飾
        for gate_rect in [left_gate_rect, right_gate_rect]:
            # 縦の装飾線
            for x_offset in [8, 16]:
                line_x = gate_rect.left + x_offset
                pygame.draw.line(self.screen, (60, 80, 60),
                               (line_x, gate_rect.top + 5), (line_x, gate_rect.bottom - 5), 1)
            
            # 取っ手
            handle_center = (gate_rect.centerx, gate_rect.centery)
            pygame.draw.circle(self.screen, (200, 180, 120), handle_center, 3)
        
        # 豪華な校名プレート
        plate_rect = pygame.Rect(390, 255, 70, 20)
        
        # プレートの影
        plate_shadow = plate_rect.copy()
        plate_shadow.move_ip(2, 2)
        pygame.draw.rect(self.screen, (0, 0, 0, 80), plate_shadow)
        
        # プレート本体（金属調）
        pygame.draw.rect(self.screen, (220, 220, 240), plate_rect)
        
        # メタリックグラデーション
        for y in range(plate_rect.height):
            ratio = y / plate_rect.height
            if ratio < 0.5:
                color_factor = 1.0 + ratio * 0.3
            else:
                color_factor = 1.3 - (ratio - 0.5) * 0.6
            
            r = max(0, min(255, int(220 * color_factor)))
            g = max(0, min(255, int(220 * color_factor)))
            b = max(0, min(255, int(240 * color_factor)))
            color = (r, g, b)
            pygame.draw.line(self.screen, color,
                           (plate_rect.left, plate_rect.top + y),
                           (plate_rect.right, plate_rect.top + y))
        
        # プレートの縁取り
        pygame.draw.rect(self.screen, (150, 150, 170), plate_rect, 2)
        
        # 校名テキスト
        if hasattr(self.fonts, 'small'):
            school_text = self.fonts['small'].render("私立学園", True, (50, 50, 70))
            text_rect = school_text.get_rect(center=plate_rect.center)
            self.screen.blit(school_text, text_rect)
    
    def draw_school_boundary(self):
        """高品質学校敷地境界の描画"""
        # 敷地境界線（現代的なフェンス）- 体育館を避けて配置
        boundary_segments = [
            # 上辺
            ((160, 240), (375, 240)),  # 正門左まで
            ((493, 240), (750, 240)),  # 正門右から
            # 右辺  
            ((750, 240), (750, 740)),
            # 下辺
            ((750, 740), (160, 740)),
            # 左辺
            ((160, 740), (160, 240))
        ]
        
        # 高品質フェンス描画
        for start_pos, end_pos in boundary_segments:
            self.draw_premium_fence(start_pos, end_pos)
        
        # コーナーポスト（強化）
        corner_posts = [(160, 240), (750, 240), (750, 740), (160, 740)]
        for post_x, post_y in corner_posts:
            # ポスト基礎
            base_rect = pygame.Rect(post_x - 6, post_y - 6, 12, 12)
            pygame.draw.rect(self.screen, (100, 100, 100), base_rect)
            
            # ポスト本体
            post_rect = pygame.Rect(post_x - 3, post_y - 3, 6, 6)
            pygame.draw.rect(self.screen, (140, 140, 140), post_rect)
    
    def draw_premium_fence(self, start_pos, end_pos):
        """高品質フェンスの描画"""
        # メインフェンス線（太く）
        pygame.draw.line(self.screen, (120, 120, 130), start_pos, end_pos, 3)
        
        # フェンスの影
        shadow_start = (start_pos[0] + 1, start_pos[1] + 1)
        shadow_end = (end_pos[0] + 1, end_pos[1] + 1)
        pygame.draw.line(self.screen, (80, 80, 80), shadow_start, shadow_end, 3)
        
        # 上部の装飾線
        if start_pos[1] == end_pos[1]:  # 水平フェンス
            upper_start = (start_pos[0], start_pos[1] - 5)
            upper_end = (end_pos[0], end_pos[1] - 5)
            pygame.draw.line(self.screen, (140, 140, 150), upper_start, upper_end, 2)
        
        # フェンスポスト
        distance = ((end_pos[0] - start_pos[0])**2 + (end_pos[1] - start_pos[1])**2)**0.5
        if distance > 0:
            num_posts = max(2, int(distance // 25))
            for j in range(num_posts + 1):
                ratio = j / num_posts if num_posts > 0 else 0
                post_x = int(start_pos[0] + (end_pos[0] - start_pos[0]) * ratio)
                post_y = int(start_pos[1] + (end_pos[1] - start_pos[1]) * ratio)
                
                # ポスト本体
                if start_pos[1] == end_pos[1]:  # 水平線
                    post_rect = pygame.Rect(post_x - 2, post_y - 12, 4, 24)
                    pygame.draw.rect(self.screen, (130, 130, 140), post_rect)
                    
                    # ポストキャップ
                    cap_rect = pygame.Rect(post_x - 3, post_y - 14, 6, 4)
                    pygame.draw.rect(self.screen, (110, 110, 120), cap_rect)
                else:  # 垂直線
                    post_rect = pygame.Rect(post_x - 12, post_y - 2, 24, 4)
                    pygame.draw.rect(self.screen, (130, 130, 140), post_rect)
                    
                    # ポストキャップ
                    cap_rect = pygame.Rect(post_x - 14, post_y - 3, 4, 6)
                    pygame.draw.rect(self.screen, (110, 110, 120), cap_rect)
                
                # 金具・留め具
                clip_color = (180, 180, 190)
                if start_pos[1] == end_pos[1]:  # 水平線
                    pygame.draw.circle(self.screen, clip_color, (post_x, post_y - 3), 2)
                    pygame.draw.circle(self.screen, clip_color, (post_x, post_y + 3), 2)
                else:  # 垂直線
                    pygame.draw.circle(self.screen, clip_color, (post_x - 3, post_y), 2)
                    pygame.draw.circle(self.screen, clip_color, (post_x + 3, post_y), 2)
    
    def draw_weekend_map(self):
        """休日マップ（街）の描画 - 以前の街並みから学校を除外"""
        # 道路システム
        self.draw_roads()
        
        # 建物群（improved_map.pyと同じ配置）
        buildings = [
            # 商店街 - improved_map.pyと同じ位置
            {'rect': pygame.Rect(620, 385, 120, 80), 'type': 'shopping', 'name': '商店街'},
            # 駅 - improved_map.pyと同じ位置
            {'rect': pygame.Rect(650, 580, 100, 60), 'type': 'station', 'name': '駅'},
            # カフェ - improved_map.pyと同じ位置
            {'rect': pygame.Rect(320, 385, 80, 70), 'type': 'cafe', 'name': 'カフェ'},
        ]
        
        for building in buildings:
            rect = building['rect']
            building_type = building['type']
            
            # 建物の影
            shadow_rect = rect.copy()
            shadow_rect.move_ip(3, 3)
            pygame.draw.rect(self.screen, (0, 0, 0, 50), shadow_rect)
            
            # 建物タイプ別の描画
            if building_type == 'station':
                self.draw_station_building(rect)
            elif building_type == 'shopping':
                self.draw_shopping_district(rect)
            elif building_type == 'cafe':
                self.draw_cafe_building(rect)
        
        # 公園エリア（左下）
        self.draw_park_area()
        
        # 川
        self.draw_river()
    
    def draw_roads(self):
        """道路の描画"""
        road_width = 50
        
        # 道路の基本情報
        h_roads = [
            {'y': 330, 'width': road_width},
            {'y': 470, 'width': road_width}
        ]
        v_roads = [
            {'x': 220, 'width': road_width},
            {'x': 520, 'width': road_width}
        ]
        
        # 横道 - 緑地エリア内で完結
        road_start_x = 20      # 左端から20px
        road_end_x = SCREEN_WIDTH - 350  # 右端UI部分を避ける
        
        for h_road in h_roads:
            road_rect = pygame.Rect(road_start_x, h_road['y'], road_end_x - road_start_x, h_road['width'])
            pygame.draw.rect(self.screen, ADVANCED_COLORS['road'], road_rect)
            pygame.draw.rect(self.screen, ADVANCED_COLORS['sidewalk'], road_rect, 3)
            
            # 中央線
            for x in range(road_start_x, road_end_x, 20):
                line_rect = pygame.Rect(x, h_road['y'] + h_road['width']//2 - 1, 10, 2)
                pygame.draw.rect(self.screen, (255, 255, 255), line_rect)
        
        # 縦道 - 空の下から画面下端まで
        road_start_y = SCREEN_HEIGHT // 4  # 空の下から開始
        road_end_y = SCREEN_HEIGHT  # 画面下端まで
        
        for v_road in v_roads:
            road_rect = pygame.Rect(v_road['x'], road_start_y, v_road['width'], road_end_y - road_start_y)
            pygame.draw.rect(self.screen, ADVANCED_COLORS['road'], road_rect)
            pygame.draw.rect(self.screen, ADVANCED_COLORS['sidewalk'], road_rect, 3)
            
            # 中央線
            for y in range(road_start_y, road_end_y, 20):
                line_rect = pygame.Rect(v_road['x'] + v_road['width']//2 - 1, y, 2, 10)
                pygame.draw.rect(self.screen, (255, 255, 255), line_rect)
        
        # 交差点
        self.draw_intersections()
    
    def draw_intersections(self):
        """交差点の描画"""
        intersections = [(220, 330), (220, 470), (520, 330), (520, 470)]
        
        for x, y in intersections:
            intersection_rect = pygame.Rect(x, y, 50, 50)
            
            # 交差点の舗装
            intersection_color = (ADVANCED_COLORS['road'][0] + 15, 
                                ADVANCED_COLORS['road'][1] + 15, 
                                ADVANCED_COLORS['road'][2] + 15)
            pygame.draw.rect(self.screen, intersection_color, intersection_rect)
            pygame.draw.rect(self.screen, (255, 255, 255), intersection_rect, 2)
            
            # 横断歩道
            stripe_width = 4
            stripe_spacing = 6
            
            # 4方向の横断歩道
            for i in range(0, 50, stripe_spacing + stripe_width):
                if i + stripe_width <= 50:
                    # 上下
                    stripe_rect = pygame.Rect(x + i, y - 8, stripe_width, 8)
                    pygame.draw.rect(self.screen, (255, 255, 255), stripe_rect)
                    stripe_rect = pygame.Rect(x + i, y + 50, stripe_width, 8)
                    pygame.draw.rect(self.screen, (255, 255, 255), stripe_rect)
                    
                    # 左右
                    stripe_rect = pygame.Rect(x - 8, y + i, 8, stripe_width)
                    pygame.draw.rect(self.screen, (255, 255, 255), stripe_rect)
                    stripe_rect = pygame.Rect(x + 50, y + i, 8, stripe_width)
                    pygame.draw.rect(self.screen, (255, 255, 255), stripe_rect)
    
    def draw_station_building(self, rect):
        """駅建物の描画"""
        # 駅舎本体
        station_color = ADVANCED_COLORS['station_color']
        pygame.draw.rect(self.screen, station_color, rect)
        
        # アーチ屋根
        roof_rect = pygame.Rect(rect.left - 5, rect.top - 15, rect.width + 10, 15)
        pygame.draw.rect(self.screen, (150, 150, 170), roof_rect, border_radius=8)
        
        # 駅名看板
        sign_rect = pygame.Rect(rect.centerx - 25, rect.top - 12, 50, 8)
        pygame.draw.rect(self.screen, (0, 100, 200), sign_rect)
        
        # 改札口
        gate_rect = pygame.Rect(rect.centerx - 8, rect.bottom - 15, 16, 15)
        pygame.draw.rect(self.screen, (255, 255, 255), gate_rect)
        pygame.draw.rect(self.screen, (100, 100, 100), gate_rect, 1)
        
        pygame.draw.rect(self.screen, (100, 100, 100), rect, 2)
    
    def draw_shopping_district(self, rect):
        """商店街の描画"""
        shop_colors = ADVANCED_COLORS['shop_colors']
        shop_width = rect.width // 3
        
        for i in range(3):
            shop_rect = pygame.Rect(rect.left + i * shop_width, rect.top, 
                                  shop_width, rect.height)
            pygame.draw.rect(self.screen, shop_colors[i], shop_rect)
            pygame.draw.rect(self.screen, (100, 100, 100), shop_rect, 1)
            
            # 看板
            sign_rect = pygame.Rect(shop_rect.left + 5, shop_rect.top + 5, 
                                  shop_width - 10, 15)
            pygame.draw.rect(self.screen, (255, 255, 255), sign_rect)
            pygame.draw.rect(self.screen, (100, 100, 100), sign_rect, 1)
            
            # ショーウィンドウ
            window_rect = pygame.Rect(shop_rect.left + 8, shop_rect.top + 25, 
                                    shop_width - 16, 30)
            pygame.draw.rect(self.screen, (220, 220, 255), window_rect)
            pygame.draw.rect(self.screen, (100, 100, 100), window_rect, 2)
        
        pygame.draw.rect(self.screen, (100, 100, 100), rect, 2)
    
    def draw_cafe_building(self, rect):
        """カフェ建物の描画"""
        # カフェ本体
        cafe_color = ADVANCED_COLORS['cafe_color']
        pygame.draw.rect(self.screen, cafe_color, rect)
        
        # 大きなガラス窓
        window_rect = pygame.Rect(rect.left + 10, rect.top + 20, rect.width - 20, 25)
        pygame.draw.rect(self.screen, (240, 248, 255), window_rect)
        pygame.draw.rect(self.screen, (100, 100, 100), window_rect, 2)
        
        # 入り口ドア
        door_rect = pygame.Rect(rect.centerx - 8, rect.bottom - 20, 16, 20)
        pygame.draw.rect(self.screen, (101, 67, 33), door_rect)
        
        pygame.draw.rect(self.screen, (100, 100, 100), rect, 2)
    
    def draw_park_area(self):
        """公園エリアの描画（improved_map.pyと同じ）"""
        # 公園のエリア全体 - 川の下、左下に配置
        park_area = pygame.Rect(20, 580, 180, 150)
        
        # 苝生エリア
        grass_color = (50, 150, 50)
        pygame.draw.rect(self.screen, grass_color, park_area, border_radius=15)
        
        # 散歩道
        path_points = [
            (park_area.left + 20, park_area.bottom),
            (park_area.left + 40, park_area.centery + 20),
            (park_area.centerx, park_area.centery - 10),
            (park_area.right - 40, park_area.centery + 15),
            (park_area.right - 20, park_area.bottom)
        ]
        
        # 道の幅を作るために太い線で描画
        if len(path_points) > 1:
            for i in range(len(path_points) - 1):
                pygame.draw.line(self.screen, (139, 126, 102), path_points[i], path_points[i+1], 8)
        
        # 木々
        tree_positions = [
            (park_area.left + 30, park_area.top + 25),
            (park_area.right - 40, park_area.top + 30),
            (park_area.left + 25, park_area.bottom - 35),
            (park_area.right - 30, park_area.bottom - 40)
        ]
        
        for tree_x, tree_y in tree_positions:
            # 木の幹
            trunk_rect = pygame.Rect(tree_x - 3, tree_y, 6, 20)
            pygame.draw.rect(self.screen, (101, 67, 33), trunk_rect)
            
            # 木の葉（大小の違う円で自然な形）
            pygame.draw.circle(self.screen, (34, 139, 34), (tree_x, tree_y - 5), 18)
            pygame.draw.circle(self.screen, (0, 128, 0), (tree_x - 8, tree_y - 10), 12)
            pygame.draw.circle(self.screen, (50, 205, 50), (tree_x + 6, tree_y - 8), 10)
        
        # ベンチ
        bench_positions = [
            (park_area.centerx - 30, park_area.centery + 10),
            (park_area.centerx + 10, park_area.centery - 20)
        ]
        
        for bench_x, bench_y in bench_positions:
            # ベンチの背もたれ
            back_rect = pygame.Rect(bench_x, bench_y - 8, 35, 8)
            pygame.draw.rect(self.screen, (139, 69, 19), back_rect)
            
            # ベンチの座面
            seat_rect = pygame.Rect(bench_x, bench_y, 35, 6)
            pygame.draw.rect(self.screen, (160, 82, 45), seat_rect)
            
            # ベンチの脚
            for leg_x in [bench_x + 5, bench_x + 25]:
                pygame.draw.rect(self.screen, (101, 67, 33), (leg_x, bench_y + 6, 3, 8))
        
        # 池や噴水
        pond_center = (park_area.centerx + 40, park_area.centery + 25)
        pond_radius = 15
        
        # 池の本体
        pygame.draw.circle(self.screen, (100, 149, 237), pond_center, pond_radius)
        pygame.draw.circle(self.screen, (70, 130, 180), pond_center, pond_radius, 2)
        
        # 池の波紋
        for i in range(3):
            wave_radius = pond_radius - 3 - i * 3
            if wave_radius > 0:
                pygame.draw.circle(self.screen, (135, 206, 250, 100), pond_center, wave_radius, 1)
        
    
    def draw_river(self):
        """川の描画（橋付き）"""
        river_y = 520
        bridge_positions = [220, 520]  # 道路との交差点
        
        # 川の基本形状（まっすぐな川）
        points = []
        for x in range(0, SCREEN_WIDTH - 350, 20):
            points.append((x, river_y))
        
        # 川幅を追加
        top_points = points
        bottom_points = [(x, y + 40) for x, y in reversed(points)]
        river_polygon = top_points + bottom_points
        
        # 川の描画
        pygame.draw.polygon(self.screen, ADVANCED_COLORS['water'], river_polygon)
        
        # 水面の反射効果（橋の下を除く）- 静的
        for i, (x, y) in enumerate(points[::3]):
            # 橋の位置では反射を描画しない
            is_under_bridge = any(bridge_x <= x <= bridge_x + 50 for bridge_x in bridge_positions)
            
            if i % 2 == 0 and not is_under_bridge:
                # 静的な反射効果
                for j in range(2):
                    offset_y = y + 15 + j * 6
                    line_length = 10 - j * 2
                    pygame.draw.line(self.screen, (255, 255, 255), 
                                   (x, offset_y), (x + line_length, offset_y), 1)
        
        # 橋の描画
        self.draw_bridges(river_y, bridge_positions)
    
    def draw_bridges(self, river_y, bridge_positions):
        """橋の描画"""
        for bridge_x in bridge_positions:
            # 橋の基本構造
            bridge_rect = pygame.Rect(bridge_x, river_y - 5, 50, 50)  # 道路幅と同じ
            
            # 橋の影
            shadow_rect = bridge_rect.copy()
            shadow_rect.move_ip(2, 2)
            pygame.draw.rect(self.screen, (0, 0, 0, 100), shadow_rect)
            
            # 橋面（薄いグレー）
            bridge_color = (180, 180, 180)
            pygame.draw.rect(self.screen, bridge_color, bridge_rect)
            
            # 橋の縁取り
            pygame.draw.rect(self.screen, (120, 120, 120), bridge_rect, 2)
            
            # 橋脚（両端に柱）
            pillar_width = 8
            pillar_color = (100, 100, 100)
            
            # 左の橋脚
            left_pillar = pygame.Rect(bridge_x - 2, river_y + 20, pillar_width, 25)
            pygame.draw.rect(self.screen, pillar_color, left_pillar)
            
            # 右の橋脚
            right_pillar = pygame.Rect(bridge_x + 44, river_y + 20, pillar_width, 25)
            pygame.draw.rect(self.screen, pillar_color, right_pillar)
            
            # 手すり（上部の線）
            railing_y = river_y - 3
            pygame.draw.line(self.screen, (150, 150, 150),
                           (bridge_x + 5, railing_y), (bridge_x + 45, railing_y), 2)
            pygame.draw.line(self.screen, (150, 150, 150),
                           (bridge_x + 5, railing_y + 48), (bridge_x + 45, railing_y + 48), 2)
    
    def draw_girl_icons(self):
        """女の子アイコンの描画（イベント表示付き）- 確実表示版"""
        current_locations = self.get_current_locations()
        
        icon_count = 0
        for location in current_locations:
            if location.girl_characters:
                icon_count += len(location.girl_characters)
                print(f"🎨 描画中: {location.name}に{len(location.girl_characters)}人 (has_event: {location.has_event})")
                print(f"   キャラクター一覧: {[char.name for char in location.girl_characters]}")
                # キャラクターアイコンの描画
                for i, char in enumerate(location.girl_characters):
                    icon_x = location.x + (i * 50) - 10
                    icon_y = location.y - 35
                    
                    # イベント有無でアイコンの表示を変える（アルファ使わない）
                    if location.has_event:
                        # イベントありの場合、光る効果（単純な円で）
                        glow_radius = 20 + int(math.sin(self.animation_time * 0.1) * 5)
                        pygame.draw.circle(self.screen, (255, 215, 0), (icon_x, icon_y), glow_radius, 3)
                        pygame.draw.circle(self.screen, (255, 255, 0), (icon_x, icon_y), glow_radius - 3, 2)
                    
                    # ホバー判定
                    mouse_pos = pygame.mouse.get_pos()
                    is_hovered = math.sqrt((mouse_pos[0] - icon_x)**2 + (mouse_pos[1] - icon_y)**2) <= 30
                    
                    # キャラクター画像がある場合は画像を、ない場合は従来のアイコンを描画
                    if char.circular_image:
                        if is_hovered and hasattr(char, 'circular_image_hover') and char.circular_image_hover:
                            # ホバー時：大きい画像を使用
                            shadow_radius = 30
                            border_radius = 30
                            border_thickness = 4
                            # 影を描画
                            pygame.draw.circle(self.screen, (0, 0, 0), (icon_x + 3, icon_y + 3), shadow_radius)
                            # 円形の画像を描画
                            image_rect = char.circular_image_hover.get_rect(center=(icon_x, icon_y))
                            self.screen.blit(char.circular_image_hover, image_rect)
                            # 縁取りを追加（画像を際立たせる）
                            pygame.draw.circle(self.screen, char.color, (icon_x, icon_y), border_radius, border_thickness)
                        else:
                            # 通常時：小さい画像を使用
                            shadow_radius = 18
                            border_radius = 18
                            border_thickness = 3
                            # 影を描画
                            pygame.draw.circle(self.screen, (0, 0, 0), (icon_x + 2, icon_y + 2), shadow_radius)
                            # 円形の画像を描画
                            image_rect = char.circular_image.get_rect(center=(icon_x, icon_y))
                            self.screen.blit(char.circular_image, image_rect)
                            # 縁取りを追加（画像を際立たせる）
                            pygame.draw.circle(self.screen, char.color, (icon_x, icon_y), border_radius, border_thickness)
                        
                    else:
                        # 従来の色付きアイコン描画（画像が読み込めない場合）
                        # 黒い影
                        pygame.draw.circle(self.screen, (0, 0, 0), (icon_x + 3, icon_y + 3), 15)
                        
                        # アイコン本体（大きく）
                        pygame.draw.circle(self.screen, (0, 0, 0), (icon_x, icon_y), 16)  # 黒縁
                        pygame.draw.circle(self.screen, char.color, (icon_x, icon_y), 15)
                        pygame.draw.circle(self.screen, (255, 255, 255), (icon_x, icon_y), 12)
                        pygame.draw.circle(self.screen, char.color, (icon_x, icon_y), 10)
                        
                        # 白いハイライト（確実表示）
                        pygame.draw.circle(self.screen, (255, 255, 255), (icon_x - 4, icon_y - 4), 4)
                    
                    print(f"     - {char.name} @ ({icon_x}, {icon_y}) 色: {char.color}")
                    print(f"       画像状態: circular_image={'有' if char.circular_image else '無'}")
                    print(f"       オブジェクトID: {id(char)}")
                    print(f"       image属性: {'有' if hasattr(char, 'image') and char.image else '無'}")
                    print(f"       image_file: {getattr(char, 'image_file', 'なし')}")
                    
                    # デバッグ用：画面境界内かチェック
                    if 0 <= icon_x <= SCREEN_WIDTH and 0 <= icon_y <= SCREEN_HEIGHT:
                        print(f"       ✅ 画面内に描画")
                    else:
                        print(f"       ❌ 画面外: 画面サイズ({SCREEN_WIDTH}x{SCREEN_HEIGHT})")
                    
                    
    
    def get_current_event_for_character(self, character_name: str, location_name: str):
        """指定キャラクター・場所の現在のイベントを取得（実行済みは除外）"""
        time_names = {
            TimeSlot.MORNING: "朝",
            TimeSlot.NOON: "昼", 
            TimeSlot.NIGHT: "夜"
        }
        current_time_name = time_names[self.current_time_slot]
        
        for event in self.events:
            if (event.heroine == character_name and 
                event.location == location_name and
                event.is_active(self.current_date, current_time_name) and
                not self.is_event_completed(event.event_id)):  # 実行済みイベントを除外
                return event
        return None
    
    def get_heart_points(self, x, y, size):
        """ハート型の座標点を計算"""
        points = []
        for angle in range(0, 360, 10):
            t = math.radians(angle)
            # ハート型の数式
            heart_x = 16 * math.sin(t)**3
            heart_y = -(13 * math.cos(t) - 5 * math.cos(2*t) - 2 * math.cos(3*t) - math.cos(4*t))
            
            # サイズとポジション調整
            scale = size / 20.0
            px = x + heart_x * scale
            py = y + heart_y * scale
            points.append((px, py))
        
        return points
    
    def draw_locations(self):
        """場所マーカーの描画"""
        current_locations = self.get_current_locations()
        
        for location in current_locations:
            # マーカーのサイズと色（固定）
            radius = 12
            marker_color = (70, 130, 180)
            
            # マーカー描画
            pygame.draw.circle(self.screen, marker_color, (location.x, location.y), radius)
            pygame.draw.circle(self.screen, (255, 255, 255), (location.x, location.y), radius - 3)
            pygame.draw.circle(self.screen, marker_color, (location.x, location.y), radius - 6)
            
            # 場所名ラベル（常時表示）
            self.draw_location_label_always(location)
    
    def draw_location_label(self, location):
        """場所ラベルの描画"""
        text = self.fonts['medium'].render(location.name, True, ADVANCED_COLORS['text_color'])
        text_rect = text.get_rect(center=(location.x, location.y - 35))
        
        # ラベル背景
        bg_rect = text_rect.inflate(12, 6)
        bg_surf = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
        bg_surf.fill(ADVANCED_COLORS['ui_glass'])
        self.screen.blit(bg_surf, bg_rect)
        
        pygame.draw.rect(self.screen, ADVANCED_COLORS['ui_border'], bg_rect, 2, border_radius=5)
        self.screen.blit(text, text_rect)
    
    def draw_location_label_always(self, location):
        """場所ラベルの常時表示（アイコン右横）"""
        text = self.fonts['small'].render(location.name, True, ADVANCED_COLORS['text_color'])
        
        # アイコンの右横に表示
        text_x = location.x + 25  # アイコンから25ピクセル右
        text_y = location.y - text.get_height() // 2  # 縦中央揃え
        text_rect = pygame.Rect(text_x, text_y, text.get_width(), text.get_height())
        
        # 背景（半透明）
        bg_rect = text_rect.inflate(8, 4)
        bg_surf = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
        bg_surf.fill((255, 255, 255, 180))  # 半透明白背景
        self.screen.blit(bg_surf, bg_rect)
        
        # 境界線
        pygame.draw.rect(self.screen, (100, 100, 100), bg_rect, 1, border_radius=3)
        
        # テキスト描画
        self.screen.blit(text, text_rect)
    
    def draw_calendar(self):
        """カレンダーの描画 - 左上の端"""
        # カレンダー位置とサイズ
        cal_x = 10
        cal_y = 10
        cal_width = 200
        cal_height = 180
        
        # カレンダー背景
        cal_rect = pygame.Rect(cal_x, cal_y, cal_width, cal_height)
        cal_surf = pygame.Surface((cal_width, cal_height), pygame.SRCALPHA)
        cal_surf.fill((255, 255, 255, 240))
        self.screen.blit(cal_surf, cal_rect)
        
        # カレンダー枠
        pygame.draw.rect(self.screen, ADVANCED_COLORS['ui_border'], cal_rect, 2, border_radius=8)
        
        # 年・月・日表示
        month_year_day = f"{self.current_date.year}年{self.current_date.month}月{self.current_date.day}日"
        month_text = self.fonts['medium'].render(month_year_day, True, ADVANCED_COLORS['text_color'])
        month_rect = month_text.get_rect(centerx=cal_rect.centerx, y=cal_rect.y + 8)
        self.screen.blit(month_text, month_rect)
        
        # 曜日ヘッダー
        weekdays = ['月', '火', '水', '木', '金', '土', '日']
        header_y = cal_rect.y + 35
        cell_width = cal_width // 7
        
        for i, day in enumerate(weekdays):
            day_text = self.fonts['small'].render(day, True, ADVANCED_COLORS['text_color'])
            day_x = cal_rect.x + i * cell_width + cell_width // 2
            day_rect = day_text.get_rect(centerx=day_x, y=header_y)
            self.screen.blit(day_text, day_rect)
        
        # カレンダーグリッド描画
        start_date = datetime.date(1999, 5, 31)  # 月曜日から開始
        current_monday = start_date
        
        # 4週間 + 3日のカレンダー
        for week in range(5):  # 5行で表示
            for day in range(7):  # 7列（月～日）
                current_day = current_monday + datetime.timedelta(days=week * 7 + day)
                
                # 期間内の日付のみ表示
                if current_day <= self.end_date:
                    day_x = cal_rect.x + day * cell_width
                    day_y = header_y + 25 + week * 20
                    
                    # 現在の日付をハイライト
                    if current_day == self.current_date:
                        highlight_rect = pygame.Rect(day_x + 2, day_y - 2, cell_width - 4, 18)
                        pygame.draw.rect(self.screen, (255, 215, 0), highlight_rect, border_radius=3)
                        pygame.draw.rect(self.screen, ADVANCED_COLORS['ui_border'], highlight_rect, 1, border_radius=3)
                    
                    # 日付テキスト
                    day_num = str(current_day.day)
                    color = ADVANCED_COLORS['text_color']
                    if current_day == self.current_date:
                        color = (0, 0, 0)  # 現在日は黒文字
                    
                    day_text = self.fonts['small'].render(day_num, True, color)
                    day_text_rect = day_text.get_rect(centerx=day_x + cell_width // 2, y=day_y)
                    self.screen.blit(day_text, day_text_rect)
        
        # 時間帯表示マス（カレンダー直下）
        time_slots = ['朝', '昼', '夜']
        time_y = cal_rect.bottom + 10
        time_square_size = 40
        time_spacing = 10
        
        for i, time_name in enumerate(time_slots):
            time_x = cal_rect.x + i * (time_square_size + time_spacing)
            time_rect = pygame.Rect(time_x, time_y, time_square_size, time_square_size)
            
            # 現在の時間帯をハイライト
            if i == self.current_time_slot.value:
                pygame.draw.rect(self.screen, (255, 215, 0), time_rect)  # 金色
                pygame.draw.rect(self.screen, ADVANCED_COLORS['ui_border'], time_rect, 2)
                text_color = (0, 0, 0)
            else:
                pygame.draw.rect(self.screen, (255, 255, 255, 180), time_rect)
                pygame.draw.rect(self.screen, ADVANCED_COLORS['ui_border'], time_rect, 1)
                text_color = ADVANCED_COLORS['text_color']
            
            # 時間帯テキスト
            time_text = self.fonts['small'].render(time_name, True, text_color)
            time_text_rect = time_text.get_rect(center=time_rect.center)
            self.screen.blit(time_text, time_text_rect)
    
    def draw_ui_panel(self):
        """UIパネルの描画"""
        panel_rect = pygame.Rect(SCREEN_WIDTH - 350, 0, 350, SCREEN_HEIGHT)
        
        # パネル背景
        panel_surf = pygame.Surface((panel_rect.width, panel_rect.height), pygame.SRCALPHA)
        panel_surf.fill((255, 255, 255, 200))
        self.screen.blit(panel_surf, panel_rect)
        
        pygame.draw.line(self.screen, ADVANCED_COLORS['ui_border'], 
                        (panel_rect.left, 0), (panel_rect.left, SCREEN_HEIGHT), 3)
        
        # 時間・曜日表示
        time_text = self.fonts['large'].render("時間情報", True, ADVANCED_COLORS['text_color'])
        self.screen.blit(time_text, (panel_rect.left + 20, 20))
        
        time_display = self.get_time_display()
        time_lines = time_display.split(' - ')
        
        y_offset = 60
        for line in time_lines:
            line_text = self.fonts['medium'].render(line, True, ADVANCED_COLORS['text_color'])
            self.screen.blit(line_text, (panel_rect.left + 20, y_offset))
            y_offset += 30
        
        # 自動進行システムを削除したため、関連表示を削除
        
        # 選択されたキャラクター名表示
        if self.selected_character:
            char_name_text = self.fonts['large'].render(self.selected_character.name, True, self.selected_character.color)
            self.screen.blit(char_name_text, (panel_rect.left + 20, y_offset + 20))
        
        # ヒロイン画像を縦並びで描画（自動進行表示削除によりスペース節約）
        heroine_start_y = y_offset + 60
        self.draw_heroine_images_in_panel(panel_rect, heroine_start_y)
        
    
    # 自動進行システム削除により、progress_barメソッドを削除
    
    def draw_character_info(self, panel_rect, start_y):
        """キャラクター情報表示"""
        char_title = self.fonts['large'].render("キャラクター", True, ADVANCED_COLORS['text_color'])
        self.screen.blit(char_title, (panel_rect.left + 20, start_y))
        
        y_offset = start_y + 40
        for char in self.selected_location.girl_characters:
            # 選択されたキャラクターをハイライト
            if self.selected_character == char:
                highlight_rect = pygame.Rect(panel_rect.left + 10, y_offset - 5, panel_rect.width - 30, 65)
                pygame.draw.rect(self.screen, (255, 215, 0), highlight_rect, border_radius=5)
                pygame.draw.rect(self.screen, char.color, highlight_rect, 3, border_radius=5)
            
            # キャラクター名
            name_color = (0, 0, 0) if self.selected_character == char else ADVANCED_COLORS['text_color']
            name_text = self.fonts['medium'].render(char.name, True, name_color)
            self.screen.blit(name_text, (panel_rect.left + 20, y_offset))
            
            # 性格
            desc_color = (50, 50, 50) if self.selected_character == char else (100, 100, 100)
            personality_text = self.fonts['small'].render(char.personality, True, desc_color)
            self.screen.blit(personality_text, (panel_rect.left + 20, y_offset + 25))
            
            # イベント情報（選択時のみ）
            if self.selected_character == char:
                event_info = self.get_current_event_for_character(char.name, self.selected_location.name)
                if event_info:
                    event_text = self.fonts['small'].render(f"💫 {event_info.title}", True, (255, 0, 0))
                    self.screen.blit(event_text, (panel_rect.left + 20, y_offset + 45))
            
            y_offset += 70
    
    def handle_click(self, pos):
        """クリック処理"""
        x, y = pos
        print(f"🖱️ クリック検出: ({x}, {y})")
        
        # キャラクターアイコンのクリック（優先処理）
        current_locations = self.get_current_locations()
        print(f"📍 現在の場所数: {len(current_locations)}")
        
        for location in current_locations:
            if location.girl_characters:
                print(f"🏢 {location.name} にキャラクター {len(location.girl_characters)} 人")
                for i, char in enumerate(location.girl_characters):
                    # 描画処理と同じ座標計算を使用
                    icon_x = location.x + (i * 50)
                    icon_y = location.y - 35
                    distance = math.sqrt((x - icon_x)**2 + (y - icon_y)**2)
                    
                    print(f"   👤 {char.name}: 位置({icon_x}, {icon_y}), 距離={distance:.1f}")
                    
                    # アイコンクリック判定（半径30ピクセル内に拡大）
                    if distance <= 30:
                        self.selected_character = char
                        print(f"✨ キャラクター選択: {char.name} @ {location.name}")
                        
                        # イベント情報を表示
                        event_info = self.get_current_event_for_character(char.name, location.name)
                        if event_info:
                            print(f"📖 イベント: {event_info.title}")
                            # イベントを実行
                            self.execute_event(event_info)
                        else:
                            print(f"⚠️ {char.name} @ {location.name} にイベントが見つかりません")
                        return
        
        # 右パネルのヒロインアイコンクリック判定
        # 描画処理と同じ座標を使用
        panel_rect = pygame.Rect(SCREEN_WIDTH - 350, 0, 350, SCREEN_HEIGHT)
        
        # draw_ui_panelと同じロジックでstart_yを計算（自動進行表示削除によりスペース節約）
        time_display = self.get_time_display()
        time_lines = time_display.split(' - ')
        y_offset = 60 + (30 * len(time_lines))  # 初期位置 + 時間表示行数
        heroine_start_y = y_offset + 60
        
        icon_size = 100
        spacing = 110
        margin_x = 15
        
        print(f"🎨 右パネルクリック判定: パネル範囲=({panel_rect.x}, {panel_rect.y}, {panel_rect.width}, {panel_rect.height})")
        print(f"🎯 ヒロイン開始Y座標: {heroine_start_y}")
        
        for i, character in enumerate(self.characters):
            icon_y = heroine_start_y + (i * spacing)
            icon_x = panel_rect.left + margin_x
            
            # パネル内チェック
            if icon_y + icon_size > panel_rect.bottom - 20:
                break
            
            # 中心座標計算
            center_x = icon_x + icon_size // 2
            center_y = icon_y + icon_size // 2
            distance = math.sqrt((x - center_x)**2 + (y - center_y)**2)
            
            print(f"   👸 {character.name}: パネル位置({center_x}, {center_y}), 距離={distance:.1f}")
            
            # クリック判定（半径50ピクセル内）
            if distance <= 50:
                self.selected_character = character
                print(f"✨ パネルからキャラクター選択: {character.name}")
                
                # 現在の場所でのイベントを探す
                current_locations = self.get_current_locations()
                event_found = False
                
                for location in current_locations:
                    if character in location.girl_characters:
                        event_info = self.get_current_event_for_character(character.name, location.name)
                        if event_info:
                            print(f"📖 パネルイベント: {event_info.title} @ {location.name}")
                            self.execute_event(event_info)
                            event_found = True
                            break
                
                if not event_found:
                    print(f"⚠️ {character.name} の現在利用可能なイベントが見つかりません")
                return
        
        # 自動進行システム削除により、クリック切り替えエリアを削除
    
    def execute_event(self, event_info):
        """イベントを実行"""
        print(f"🎬 イベント実行開始: {event_info.event_id}")
        
        try:
            # イベントファイルのパスを設定
            import sys
            import importlib.util
            
            # MO-KISS-MAINルートディレクトリのeventsフォルダを参照
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.join(current_dir, "..", "..")
            events_dir = os.path.join(project_root, "events")
            event_file_path = os.path.join(events_dir, f"{event_info.event_id}.py")
            
            print(f"📁 イベントファイルパス: {event_file_path}")
            
            if os.path.exists(event_file_path):
                # 動的にイベントファイルをインポート
                # イベントディレクトリをパスに追加
                if events_dir not in sys.path:
                    sys.path.append(events_dir)
                spec = importlib.util.spec_from_file_location(event_info.event_id, event_file_path)
                event_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(event_module)
                
                # イベントを実行
                result = event_module.run_event(
                    event_info.event_id,
                    event_info.title,
                    event_info.heroine
                )
                
                print(f"🏁 イベント実行結果: {result}")
                
                # イベント終了後の処理
                if result == "quit":
                    self.running = False
                elif result == "back_to_map":
                    # イベント実行記録を保存
                    self.save_completed_event(event_info)
                    # マップに戻り、時間を進める
                    self.advance_time_after_event()
                    
            else:
                print(f"⚠️ イベントファイルが見つかりません: {event_file_path}")
                print("デフォルトイベントを実行します。")
                
                # デフォルトイベントを実行
                from events.event_base import EventBase
                default_event = EventBase()
                result = default_event.run_default_event(
                    event_info.event_id,
                    event_info.title,
                    event_info.heroine
                )
                
                if result == "quit":
                    self.running = False
                elif result == "back_to_map":
                    # イベント実行記録を保存
                    self.save_completed_event(event_info)
                    # デフォルトイベント終了後も時間を進める
                    self.advance_time_after_event()
                
        except Exception as e:
            print(f"❌ イベント実行エラー: {e}")
            print(f"イベントファイルの実行に失敗しました: {event_info.event_id}")
            import traceback
            traceback.print_exc()
    
    def handle_key(self, key):
        """キー処理"""
        # 自動時間進行システムを削除したため、キー処理は無効
        pass
    
    def get_available_events_for_character(self, character_name):
        """キャラクターの現在利用可能なイベント数を取得（実行済みは除外）"""
        event_count = 0
        current_locations = self.get_current_locations()
        
        for location in current_locations:
            if any(char.name == character_name for char in location.girl_characters):
                event_info = self.get_current_event_for_character(character_name, location.name)
                if event_info:
                    event_count += 1
        
        return event_count
    
    def get_completed_events_for_character(self, character_name):
        """キャラクターの実行済みイベント数を取得"""
        completed_count = 0
        for event_id, data in self.completed_events.items():
            if data['heroine'] == character_name:
                completed_count += 1
        
        return completed_count
    
    def draw_heroine_images_in_panel(self, panel_rect, start_y):
        """UIパネル内にヒロイン画像を縦並びで描画"""
        icon_size = 100  # より大きいサイズ
        spacing = 110
        margin_x = 15  # マージンを調整
        
        for i, character in enumerate(self.characters):
            icon_y = start_y + (i * spacing)
            icon_x = panel_rect.left + margin_x
            
            # パネル内チェック
            if icon_y + icon_size > panel_rect.bottom - 20:
                break
                
            if hasattr(character, 'circular_image_large') and character.circular_image_large:
                # 専用の大サイズ画像を使用（リサイズなし）
                
                # 影を描画
                shadow_radius = icon_size // 2
                pygame.draw.circle(self.screen, (0, 0, 0), 
                                 (icon_x + shadow_radius + 2, icon_y + shadow_radius + 2), 
                                 shadow_radius)
                
                # 画像を描画
                self.screen.blit(character.circular_image_large, (icon_x, icon_y))
                
                # 縁取りを追加
                pygame.draw.circle(self.screen, character.color, 
                                 (icon_x + shadow_radius, icon_y + shadow_radius), 
                                 shadow_radius, 2)
            else:
                # フォールバック：色付き円
                center = (icon_x + icon_size // 2, icon_y + icon_size // 2)
                radius = icon_size // 2
                pygame.draw.circle(self.screen, character.color, center, radius)
                pygame.draw.circle(self.screen, (255, 255, 255), center, radius - 5)
                pygame.draw.circle(self.screen, character.color, center, radius - 10)
            
            # キャラクター名を表示
            name_text = self.fonts['small'].render(character.name, True, ADVANCED_COLORS['text_color'])
            name_x = icon_x + icon_size + 10
            name_y = icon_y + 20
            self.screen.blit(name_text, (name_x, name_y))
            
            # 利用可能なイベント数と実行済みイベント数を表示
            available_count = self.get_available_events_for_character(character.name)
            completed_count = self.get_completed_events_for_character(character.name)
            
            info_x = icon_x + icon_size + 10
            info_y = icon_y + 40
            
            # 利用可能なイベント数（赤い円）
            if available_count > 0:
                pygame.draw.circle(self.screen, (220, 0, 0), (info_x + 15, info_y + 15), 15)
                pygame.draw.circle(self.screen, (255, 255, 255), (info_x + 15, info_y + 15), 15, 2)
                
                # イベント数のテキスト
                event_text = self.fonts['medium'].render(str(available_count), True, (255, 255, 255))
                event_text_rect = event_text.get_rect(center=(info_x + 15, info_y + 15))
                self.screen.blit(event_text, event_text_rect)
                
                # "new"ラベル
                new_label = self.fonts['small'].render("new", True, (220, 0, 0))
                self.screen.blit(new_label, (info_x + 35, info_y + 5))
            
            # 実行済みイベント数（青い円）
            if completed_count > 0:
                completed_y = info_y + 35 if available_count > 0 else info_y
                pygame.draw.circle(self.screen, (0, 100, 200), (info_x + 15, completed_y + 15), 15)
                pygame.draw.circle(self.screen, (255, 255, 255), (info_x + 15, completed_y + 15), 15, 2)
                
                # 実行済み数のテキスト
                completed_text = self.fonts['medium'].render(str(completed_count), True, (255, 255, 255))
                completed_text_rect = completed_text.get_rect(center=(info_x + 15, completed_y + 15))
                self.screen.blit(completed_text, completed_text_rect)
                
                # "done"ラベル
                done_label = self.fonts['small'].render("done", True, (0, 100, 200))
                self.screen.blit(done_label, (info_x + 35, completed_y + 5))
    
    def run(self):
        """メインループ"""
        # 初期イベント更新
        self.update_events()
        
        while self.running:
            # イベント処理
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    print(f"🖱️ マウスボタンが押されました: ボタン={event.button}, 位置={event.pos}")
                    if event.button == 1:  # 左クリック
                        self.handle_click(event.pos)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                    else:
                        self.handle_key(event.key)
            
            # アニメーション更新
            self.animation_time += 1
            
            # 描画
            self.draw_advanced_sky()
            self.draw_clouds()  # 雲を追加
            self.draw_terrain()
            
            # マップタイプ別描画（朝昼は学校、夜は街）
            if self.current_time_slot == TimeSlot.NIGHT or self.current_map_type == MapType.WEEKEND:
                self.draw_weekend_map()  # 夜と休日は街マップ
            else:
                self.draw_weekday_map()  # 朝・昼は学校マップ
            
            self.draw_locations()
            self.draw_calendar()  # カレンダーを描画
            self.draw_ui_panel()  # ヒロイン画像も含む
            
            # 最後にキャラクターアイコンを描画（確実に見えるように）
            self.draw_girl_icons()
            
            pygame.display.flip()
            self.clock.tick(FPS)
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    print("=== Advanced Kimikiss Map ===")
    print("機能:")
    print("- 曜日・時間帯システム")
    print("- 自動時間進行（5秒間隔）")
    print("- 平日マップ（学校のみ）")
    print("- 休日マップ（街のみ）")
    print("- 女の子アイコン表示")
    print("")
    print("操作:")
    print("- マウスクリック: 場所選択")
    print("- スペース: 手動時間進行")
    print("- TAB: 自動進行ON/OFF")
    print("- ESC: 終了")
    print("=========================")
    
    game = AdvancedKimikissMap()
    game.run()