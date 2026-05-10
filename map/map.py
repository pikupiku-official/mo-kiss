from logging import DEBUG
import pygame
import sys
import math
import datetime
import os
import random
import csv
from typing import List, Dict, Tuple
from enum import Enum

# プロジェクトルートをパスに追加
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, "..", "..")
sys.path.insert(0, project_root)

# TimeManagerとBGMManagerをインポート
from time_manager import get_time_manager
from loading_screen import show_loading, hide_loading
from bgm_manager import BGMManager
from subsystem_base import SubsystemBase

# 初期化
pygame.init()

# config.pyから画面サイズを取得
from config import SCREEN_WIDTH, SCREEN_HEIGHT
FPS = 60

# マップタイプの定義
class MapType(Enum):
    WEEKDAY = "weekday"    # 平日（学校のみ）
    WEEKEND = "weekend"    # 休日（街のみ）

# 時間進行の定義はtime_manager.pyに統合されました

# 高品質カラーパレット
ADVANCED_COLORS = {    
    # UI色
    'ui_glass': (255, 255, 255, 180),
    'ui_border': (70, 130, 180),
    'text_color': (33, 37, 41),
    'girl_icon': (255, 20, 147),
    'event_glow': (255, 215, 0),
}

class GameEvent:
    def __init__(self, event_id: str, start_date: str, end_date: str, time_slots: str, 
                 heroine: str, location: str, title: str):
        self.event_id = event_id
        self.start_date = self.parse_date(start_date)
        self.end_date = self.parse_date(end_date)
        if time_slots:
            slots = time_slots.split(';')
            self.time_slots = [slot.strip() for slot in slots]
        else:
            self.time_slots = []
        self.heroine = heroine
        self.location = location
        self.title = title
    
    def parse_date(self, date_str: str) -> tuple:
        """日付文字列を解析 (例: '6月1日の朝' -> (6, 1, '朝'))"""
        import re
        match = re.match(r'(\d+)月(\d+)日の(朝|昼|放課後)', date_str)
        if match:
            month, day, time_slot = match.groups()
            return (int(month), int(day), time_slot)
        return (6, 1, '朝')  # デフォルト値
    
    def is_in_time_period(self, current_date: datetime.date, current_time: str) -> bool:
        """現在の日時でイベントが期間・時間帯内かチェック"""
        # 日付の比較
        current_day_only = (current_date.month, current_date.day)
        start_day_only = (self.start_date[0], self.start_date[1])
        end_day_only = (self.end_date[0], self.end_date[1])
        
        # 期間内かつ指定時間帯かチェック
        is_in_period = start_day_only <= current_day_only <= end_day_only
        is_right_time = current_time in self.time_slots
        
        # デバッグ情報を出力
        if self.event_id in ["E002", "E003", "E004"]:  # 初期イベントのデバッグ
            print(f"[DEBUG] {self.event_id}: 現在({current_date.month}/{current_date.day} {current_time}) "
                  f"期間({start_day_only}-{end_day_only}) 時間帯{self.time_slots} "
                  f"期間内:{is_in_period} 時間帯OK:{is_right_time} -> {is_in_period and is_right_time}")
        
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

class FieldMap(SubsystemBase):
    def __init__(self, screen=None):
        print("🚀 FieldMap 初期化開始...")

        # screen が渡されなければ既存の画面を使用（スタンドアローン起動対応）
        if screen is None:
            screen = pygame.display.get_surface()
        if screen is None:
            screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
            pygame.display.set_caption("mo-kiss フィールドマップ")

        super().__init__(screen)
        
        self.clock = pygame.time.Clock()
        self.running = True
        
        # デバッグモード検出
        self.debug_mode = self.is_debug_mode()

        # BGM管理
        self.bgm_manager = BGMManager(debug=self.debug_mode)
        self.current_bgm = None  # 現在再生中のBGM

        # フォント設定
        self.init_fonts()
        
        # 時間・曜日システムはtime_manager.pyに統合
        # セーブ/ロード対応のため毎回取得するように変更
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
        project_root = os.path.dirname(os.path.dirname(__file__))  # map -> mo-kiss
        self.completed_events_file = os.path.join(project_root, "data", "current_state", "completed_events.csv")
        
        # CSVの初期化は削除（データを保護）
        
        self.completed_events = self.load_completed_events()
        
        self.init_maps()
        self.update_events()

        # BGMを再生
        self.update_bgm()

        print("✅ FieldMap 初期化完了")

    def init_fonts(self):
        """フォント初期化（クロスプラットフォーム対応）"""
        import platform
        
        # プロジェクトフォントの正しいパス（path_utils使用）
        from path_utils import get_font_path
        project_font_path = get_font_path("MPLUS1p-Regular.ttf")
        
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
    
    
    def get_map_type(self) -> MapType:
        """現在の曜日からマップタイプを判定"""
        time_state = get_time_manager().get_time_state()
        weekday = time_state['weekday']  # 0=月曜, 6=日曜
        return MapType.WEEKDAY if weekday < 5 else MapType.WEEKEND

    def get_current_bgm(self) -> str:
        """現在の時間帯・日付・マップタイプに応じたBGMファイル名を取得"""
        from map.map_config import MAP_BGM_CONFIG, SPECIAL_DATE_BGM

        # 現在の時間帯と日付を取得
        time_manager = get_time_manager()
        time_state = time_manager.get_time_state()
        current_period = time_manager.get_current_period()
        current_date = (time_state['month'], time_state['day'])

        # 特定日付のBGMを優先
        if current_date in SPECIAL_DATE_BGM:
            return SPECIAL_DATE_BGM[current_date]

        # マップタイプを取得
        map_type = 'weekday' if self.current_map_type == MapType.WEEKDAY else 'weekend'

        # マップタイプ・時間帯に応じたBGMを取得
        if map_type in MAP_BGM_CONFIG:
            if current_period in MAP_BGM_CONFIG[map_type]:
                return MAP_BGM_CONFIG[map_type][current_period]

        # デフォルトBGM
        return MAP_BGM_CONFIG.get('default', 'subete_no_hajimari.mp3')

    def update_bgm(self):
        """BGMを現在の状態に応じて更新"""
        new_bgm = self.get_current_bgm()

        # 既に同じBGMが再生中の場合はスキップ
        if self.current_bgm == new_bgm:
            return

        # 新しいBGMを再生
        if new_bgm:
            self.bgm_manager.play_bgm(new_bgm)
            self.current_bgm = new_bgm
            print(f"🎵 マップBGM再生: {new_bgm}")

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
        # map から mo-kiss ルートディレクトリへ
        project_root = os.path.dirname(current_dir)
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
                    
                    # 小サイズ（マップ用）: 35px
                    small_image = pygame.transform.smoothscale(original_image, (35, 35))
                    char.circular_image = self.create_circular_image(small_image, 35)
                    
                    # 中サイズ（ホバー用）: 60px
                    medium_image = pygame.transform.smoothscale(original_image, (60, 60))
                    char.circular_image_hover = self.create_circular_image(medium_image, 60)
                    
                    # 大サイズ（パネル用）: 100px（超高品質）
                    large_image = pygame.transform.smoothscale(original_image, (100, 100))
                    char.circular_image_large = self.create_high_quality_circular_image(large_image, 100)
                    
                    print(f"✅ 画像読み込み成功: {char.name} - {char.image_file}")
                    
                except Exception as e:
                    print(f"❌ 画像読み込み失敗: {char.name} - {char.image_file}: {e}")
                    char.circular_image = None
    
    def create_circular_image(self, image, size):
        """画像を円形に切り抜く"""
        try:
            # アルファチャンネル付きのサーフェスを作成
            circular_surface = pygame.Surface((size, size), pygame.SRCALPHA)
            circular_surface.fill((0, 0, 0, 0))  # 完全透明で初期化
            
            # 円形マスクを作成
            center = size // 2
            radius = center - 1
            
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
            project_root = os.path.dirname(current_dir)  # map -> mo-kiss
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
                        title=row['イベントのタイトル']
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
                            'count': int(row['実行回数']),
                            'active': row.get('有効フラグ', 'TRUE').upper() == 'TRUE'
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
            # 座標は4:3基準（1440x1080）に変更（元の1920x1080の0.75倍）
            EventLocation("教室", 300, 495, "みんなが集まる教室", "classroom"),  # 本館中央
            EventLocation("図書館", 450, 263, "静かで落ち着いた図書館", "library"),  # 理科棟
            EventLocation("体育館", 975, 413, "体育の授業や部活で使う体育館", "gym"),  # 体育館建物中央
            EventLocation("購買部", 469, 394, "パンや飲み物を買える購買部", "shop"),  # 本館と東棟の間
            EventLocation("屋上", 450, 113, "景色の良い学校の屋上", "rooftop"),  # 本館屋上
            EventLocation("学校正門", 1050, 675, "学校の正門", "gate"),  # 正門位置
        ]
        
        # 休日マップ（街のみ）- 座標は4:3基準（1440x1080）に変更
        self.weekend_locations = [
            EventLocation("公園", 98, 488, "緑豊かな公園", "park"),  # 130*0.75=97.5, 650*0.75=487.5
            EventLocation("駅前", 525, 458, "賑やかな駅前広場", "station"),  # 700*0.75=525, 610*0.75=457.5
            EventLocation("商店街", 510, 300, "活気ある商店街", "shopping"),  # 680*0.75=510, 400*0.75=300
            EventLocation("カフェ", 270, 315, "おしゃれなカフェ", "cafe"),  # 360*0.75=270, 420*0.75=315
        ]
    
    def get_current_locations(self) -> List[EventLocation]:
        """現在のマップタイプに応じた場所リストを取得"""
        # 放課後と休日は街マップを使用
        current_period = get_time_manager().get_current_period()
        if self.current_map_type == MapType.WEEKDAY and current_period == "放課後":
            return self.weekend_locations  # 放課後は街
        elif self.current_map_type == MapType.WEEKEND:
            return self.weekend_locations  # 休日は街
        else:
            return self.weekday_locations   # 平日朝・昼・夕方は学校
    
    def advance_time_after_event(self):
        """イベント終了後の時間進行（time_manager使用）"""
        # time_managerを使って時間帯を進める
        get_time_manager().advance_period()
        
        # マップタイプを更新
        self.current_map_type = self.get_map_type()
        
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
        current_time_name = get_time_manager().get_current_period()
        
        # 現在の日付を取得
        time_state = get_time_manager().get_time_state()
        current_date = datetime.date(time_state['year'], time_state['month'], time_state['day'])
        
        # アクティブなイベントをチェック（実行済みは除外）
        active_events = []
        for event in self.events:
            # completed_eventsから有効フラグと実行回数をチェック
            event_data = self.completed_events.get(event.event_id, {})
            is_active_flag = event_data.get('active', True)  # 有効フラグをチェック
            is_not_completed = event_data.get('count', 0) == 0  # 未実行かチェック
            
            if (event.is_in_time_period(current_date, current_time_name) and
                is_active_flag and
                is_not_completed):
                active_events.append(event)
        
        # 全イベント数と利用可能イベント数を表示
        all_active_events = [event for event in self.events if event.is_in_time_period(current_date, current_time_name)]
        completed_active_events = [event for event in all_active_events if self.is_event_completed(event.event_id)]
        
        print(f"📅 {time_state['month']}月{time_state['day']}日 {current_time_name}: "
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
        current_period = get_time_manager().get_current_period()
        if self.current_map_type == MapType.WEEKDAY and current_period == "放課後":
            map_type_name = "街(放課後)"
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
        return get_time_manager().get_full_time_string()
    
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
    
    
    def draw_girl_icons(self):
        """女の子アイコンの描画（イベント表示付き、4:3コンテンツ基準）"""
        from config import scale_pos

        current_locations = self.get_current_locations()

        icon_count = 0
        for location in current_locations:
            if location.girl_characters:
                icon_count += len(location.girl_characters)
                # キャラクターアイコンの描画
                for i, char in enumerate(location.girl_characters):
                    # 仮想座標で計算してから実座標に変換
                    virtual_icon_x = location.x + (i * 50) - 10
                    virtual_icon_y = location.y - 35
                    icon_x, icon_y = scale_pos(virtual_icon_x, virtual_icon_y)
                    
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
                    
                    
                    
    
    def get_current_event_for_character(self, character_name: str, location_name: str):
        """指定キャラクター・場所の現在のイベントを取得（実行済みは除外）"""
        current_time_name = get_time_manager().get_current_period()
        time_state = get_time_manager().get_time_state()
        current_date = datetime.date(time_state['year'], time_state['month'], time_state['day'])
        
        for event in self.events:
            # completed_eventsから有効フラグをチェック
            event_data = self.completed_events.get(event.event_id, {})
            is_active_flag = event_data.get('active', True)  # 有効フラグをチェック
            is_not_completed = event_data.get('count', 0) == 0  # 未実行かチェック
            
            if (event.heroine == character_name and 
                event.location == location_name and
                event.is_in_time_period(current_date, current_time_name) and
                is_active_flag and
                is_not_completed):
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
        """場所マーカーの描画（4:3コンテンツ基準）"""
        from config import scale_pos

        current_locations = self.get_current_locations()

        for location in current_locations:
            # location座標を仮想座標から実座標に変換
            actual_x, actual_y = scale_pos(location.x, location.y)

            # マーカーのサイズと色（固定）
            radius = 12
            marker_color = (70, 130, 180)

            # マーカー描画
            pygame.draw.circle(self.screen, marker_color, (actual_x, actual_y), radius)
            pygame.draw.circle(self.screen, (255, 255, 255), (actual_x, actual_y), radius - 3)
            pygame.draw.circle(self.screen, marker_color, (actual_x, actual_y), radius - 6)

            # 場所名ラベル（常時表示、実座標を渡す）
            self.draw_location_label_always(location, actual_x, actual_y)
    
    def draw_location_label(self, location, actual_x, actual_y):
        """場所ラベルの描画（実座標を使用）"""
        text = self.fonts['medium'].render(location.name, True, ADVANCED_COLORS['text_color'])
        text_rect = text.get_rect(center=(actual_x, actual_y - 35))
        
        # ラベル背景
        bg_rect = text_rect.inflate(12, 6)
        bg_surf = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
        bg_surf.fill(ADVANCED_COLORS['ui_glass'])
        self.screen.blit(bg_surf, bg_rect)
        
        pygame.draw.rect(self.screen, ADVANCED_COLORS['ui_border'], bg_rect, 2, border_radius=5)
        self.screen.blit(text, text_rect)
    
    def draw_location_label_always(self, location, actual_x, actual_y):
        """場所ラベルの常時表示（アイコン右横、実座標を使用）"""
        text = self.fonts['small'].render(location.name, True, ADVANCED_COLORS['text_color'])

        # アイコンの右横に表示
        text_x = actual_x + 25  # アイコンから25ピクセル右
        text_y = actual_y - text.get_height() // 2  # 縦中央揃え
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
        """カレンダーの描画 - 左上の端（4:3コンテンツ基準）"""
        from config import VIRTUAL_WIDTH, VIRTUAL_HEIGHT, scale_pos, scale_size

        # カレンダー位置とサイズ（仮想座標1440x1080基準）
        virtual_cal_x = 10
        virtual_cal_y = 10
        virtual_cal_width = 200
        virtual_cal_height = 180

        # 実座標に変換
        cal_x, cal_y = scale_pos(virtual_cal_x, virtual_cal_y)
        cal_width, cal_height = scale_size(virtual_cal_width, virtual_cal_height)
        
        # カレンダー背景
        cal_rect = pygame.Rect(cal_x, cal_y, cal_width, cal_height)
        cal_surf = pygame.Surface((cal_width, cal_height), pygame.SRCALPHA)
        cal_surf.fill((255, 255, 255, 240))
        self.screen.blit(cal_surf, cal_rect)
        
        # カレンダー枠
        pygame.draw.rect(self.screen, ADVANCED_COLORS['ui_border'], cal_rect, 2, border_radius=8)
        
        # 年・月・日表示
        time_state = get_time_manager().get_time_state()
        month_year_day = f"{time_state['year']}年{time_state['month']}月{time_state['day']}日"
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
        time_state = get_time_manager().get_time_state()
        current_date_obj = datetime.date(time_state['year'], time_state['month'], time_state['day'])
        start_date = datetime.date(1999, 5, 31)  # 月曜日から開始
        end_date = datetime.date(1999, 7, 1)  # 終了日
        current_monday = start_date
        
        # 4週間 + 3日のカレンダー
        for week in range(5):  # 5行で表示
            for day in range(7):  # 7列（月～日）
                current_day = current_monday + datetime.timedelta(days=week * 7 + day)
                
                # 期間内の日付のみ表示
                if current_day <= end_date:
                    day_x = cal_rect.x + day * cell_width
                    day_y = header_y + 25 + week * 20
                    
                    # 現在の日付をハイライト
                    if current_day == current_date_obj:
                        highlight_rect = pygame.Rect(day_x + 2, day_y - 2, cell_width - 4, 18)
                        pygame.draw.rect(self.screen, (255, 215, 0), highlight_rect, border_radius=3)
                        pygame.draw.rect(self.screen, ADVANCED_COLORS['ui_border'], highlight_rect, 1, border_radius=3)
                    
                    # 日付テキスト
                    day_num = str(current_day.day)
                    color = ADVANCED_COLORS['text_color']
                    if current_day == current_date_obj:
                        color = (0, 0, 0)  # 現在日は黒文字
                    
                    day_text = self.fonts['small'].render(day_num, True, color)
                    day_text_rect = day_text.get_rect(centerx=day_x + cell_width // 2, y=day_y)
                    self.screen.blit(day_text, day_text_rect)
        
        # 時間帯表示マス（カレンダー直下）
        time_slots = ['朝', '昼', '放課後']
        time_y = cal_rect.bottom + 10
        time_square_size = 40
        time_spacing = 10
        
        current_period = get_time_manager().get_current_period()
        
        for i, time_name in enumerate(time_slots):
            time_x = cal_rect.x + i * (time_square_size + time_spacing)
            time_rect = pygame.Rect(time_x, time_y, time_square_size, time_square_size)
            
            # 現在の時間帯をハイライト
            if time_name == current_period:
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
    
    def draw_skip_button(self, panel_rect):
        """スキップボタンを描画"""
        # スキップボタンの位置とサイズ
        button_width = 120
        button_height = 40
        button_x = panel_rect.left + (panel_rect.width - button_width) // 2
        button_y = panel_rect.bottom - 80
        
        skip_button_rect = pygame.Rect(button_x, button_y, button_width, button_height)
        
        # ボタンの背景と枠線
        pygame.draw.rect(self.screen, (60, 80, 120), skip_button_rect, border_radius=5)
        pygame.draw.rect(self.screen, (150, 170, 200), skip_button_rect, 2, border_radius=5)
        
        # ボタンテキスト
        skip_text = self.fonts['medium'].render("時間スキップ", True, (255, 255, 255))
        skip_text_rect = skip_text.get_rect(center=skip_button_rect.center)
        self.screen.blit(skip_text, skip_text_rect)
        
        # クリック判定用にボタンの座標を保存
        self.skip_button_rect = skip_button_rect
    
    def draw_ui_panel(self):
        """UIパネルの描画（4:3コンテンツ基準）"""
        from config import VIRTUAL_WIDTH, VIRTUAL_HEIGHT, scale_pos, scale_size

        # UIパネル位置とサイズ（仮想座標1440x1080基準）
        virtual_panel_width = 262  # 350 * 0.75 = 262.5 ≈ 262
        virtual_panel_x = VIRTUAL_WIDTH - virtual_panel_width
        virtual_panel_y = 0
        virtual_panel_height = VIRTUAL_HEIGHT

        # 実座標に変換
        panel_x, panel_y = scale_pos(virtual_panel_x, virtual_panel_y)
        panel_width, panel_height = scale_size(virtual_panel_width, virtual_panel_height)

        panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
        
        # パネル背景
        panel_surf = pygame.Surface((panel_rect.width, panel_rect.height), pygame.SRCALPHA)
        panel_surf.fill((255, 255, 255, 200))
        self.screen.blit(panel_surf, panel_rect)
        
        pygame.draw.line(self.screen, ADVANCED_COLORS['ui_border'],
                        (panel_rect.left, panel_rect.top), (panel_rect.left, panel_rect.bottom), 3)
        
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
        
        # スキップボタンを描画
        self.draw_skip_button(panel_rect)
        
    
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
        """クリック処理（4:3コンテンツ基準）"""
        from config import scale_pos

        x, y = pos
        print(f"🖱️ クリック検出: ({x}, {y})")

        # キャラクターアイコンのクリック（優先処理）
        current_locations = self.get_current_locations()
        print(f"📍 現在の場所数: {len(current_locations)}")

        for location in current_locations:
            if location.girl_characters:
                print(f"🏢 {location.name} にキャラクター {len(location.girl_characters)} 人")
                for i, char in enumerate(location.girl_characters):
                    # 描画処理と同じ座標計算を使用（仮想座標から実座標に変換）
                    virtual_icon_x = location.x + (i * 50)
                    virtual_icon_y = location.y - 35
                    icon_x, icon_y = scale_pos(virtual_icon_x, virtual_icon_y)
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
                            
                            # 時間管理：放課後イベントかどうかを判定
                            time_manager = get_time_manager()
                            current_period = time_manager.get_current_period()
                            
                            # 放課後イベントでなければ時間帯を進める
                            if current_period != "放課後":
                                time_manager.advance_period()
                                print(f"[TIME] イベント選択により時間帯進行: {time_manager.get_current_period()}")
                            
                            # イベントファイルパスを返してmain.pyで会話パートを起動
                            ks_file_path = f"events/{event_info.event_id}.ks"
                            return f"launch_event:{ks_file_path}"
                        else:
                            print(f"⚠️ {char.name} @ {location.name} にイベントが見つかりません")
                        return None
        
        # 右パネルのヒロインアイコンクリック判定（4:3コンテンツ基準）
        # 描画処理と同じ座標を使用
        from config import VIRTUAL_WIDTH, VIRTUAL_HEIGHT, scale_pos, scale_size

        virtual_panel_width = 262  # 350 * 0.75
        virtual_panel_x = VIRTUAL_WIDTH - virtual_panel_width
        virtual_panel_y = 0
        virtual_panel_height = VIRTUAL_HEIGHT

        panel_x, panel_y = scale_pos(virtual_panel_x, virtual_panel_y)
        panel_width, panel_height = scale_size(virtual_panel_width, virtual_panel_height)
        panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
        
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
                            # イベントファイルパスを返してmain.pyで会話パートを起動
                            ks_file_path = f"events/{event_info.event_id}.ks"
                            return f"launch_event:{ks_file_path}"
                
                if not event_found:
                    print(f"⚠️ {character.name} の現在利用可能なイベントが見つかりません")
                return None
        
        # スキップボタンのクリック判定
        if hasattr(self, 'skip_button_rect') and self.skip_button_rect.collidepoint(pos):
            print("⏭️ 時間スキップボタンがクリックされました")
            
            # 時間管理：現在の時間帯に応じて処理
            time_manager = get_time_manager()
            current_period = time_manager.get_current_period()
            
            if current_period == "放課後":
                # 放課後の場合は夜に進めてから家に遷移
                time_manager.advance_period()  # 放課後 → 夜
                new_period = time_manager.get_current_period()
                print(f"[TIME] 放課後から夜に進行: {current_period} → {new_period}")
                print("[TIME] 夜になったため家モジュールに遷移")
                return "skip_to_home"
            else:
                time_manager.advance_period()
                new_period = time_manager.get_current_period()
                print(f"[TIME] 時間スキップ: {current_period} → {new_period}")
                
                # マップタイプを更新
                self.current_map_type = self.get_map_type()
                
                # イベント更新
                self.update_events()
                return "skip_time"
        
        # 自動進行システム削除により、クリック切り替えエリアを削除
    
    def execute_event(self, event_info):
        """イベントを実行"""
        print(f"🎬 イベント実行開始: {event_info.event_id}")
        
        try:
            # イベントファイルのパスを設定
            import sys
            import importlib.util
            
            # mo-kissルートディレクトリのeventsフォルダを参照
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(current_dir)
            events_dir = os.path.join(project_root, "events")
            
            # .ksファイルを優先的に使用
            ks_file_path = os.path.join(events_dir, f"{event_info.event_id}.ks")
            
            print(f"📁 .ksファイルパス: {ks_file_path}")
            
            if os.path.exists(ks_file_path):
                print(f"📜 .ksファイルを使用してメインゲームを起動: {ks_file_path}")
                # メインゲームシステムを起動
                result = self.launch_main_game(ks_file_path, event_info)
                
                if result == "quit":
                    self.running = False
                elif result == "back_to_map":
                    # イベント実行記録を保存
                    self.save_completed_event(event_info)
                    # イベント終了後に時間を進める
                    self.advance_time_after_event()
                    
            else:
                print(f"⚠️ .ksファイルが見つかりません: {ks_file_path}")
                print("イベント実行をスキップします。")
                
        except Exception as e:
            print(f"❌ イベント実行エラー: {e}")
            print(f"イベントファイルの実行に失敗しました: {event_info.event_id}")
            import traceback
            traceback.print_exc()
    
    def launch_main_game(self, ks_file_path, event_info):
        """同じウィンドウでメインゲームシステムを実行"""
        print(f"🎮 メインゲームシステムを起動: {ks_file_path}")
        
        try:
            # メインゲームの初期化処理を実行
            from ..dialogue.model import initialize_game, initialize_first_scene
            from ..dialogue.controller2 import handle_events
            
            print("🎯 ゲーム状態を初期化中...")
            
            # Pygameを再初期化（既存のウィンドウを使用）
            if not pygame.get_init():
                pygame.init()
            
            # 既存の画面を使用
            screen = self.screen
            
            # カレントディレクトリをプロジェクトルートに変更
            import os
            current_dir = os.getcwd()
            project_root_abs = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
            os.chdir(project_root_abs)
            print(f"カレントディレクトリを変更: {current_dir} -> {project_root_abs}")
            
            try:
                # config.pyの画面サイズをそのまま使用（4:3対応）
                from config import SCREEN_WIDTH, SCREEN_HEIGHT
                current_screen_size = (SCREEN_WIDTH, SCREEN_HEIGHT)

                game_state = initialize_game()
                # 画面サイズはconfig.pyの設定をそのまま使用（変更しない）
                screen = self.screen

                # UI要素を現在の画面サイズで再初期化
                self.reinitialize_ui_elements(game_state, screen, current_screen_size)
                
            finally:
                # カレントディレクトリを元に戻す
                os.chdir(current_dir)
            if not game_state:
                print("❌ ゲーム状態の初期化に失敗しました")
                return "back_to_map"
            
            # 画面を設定
            game_state['screen'] = screen
            
            # .ksファイルからダイアログを読み込み
            print(f"📜 .ksファイルを読み込み: {ks_file_path}")
            dialogue_loader = game_state.get('dialogue_loader')
            if dialogue_loader:
                # ファイルパスを正規化
                import os
                normalized_path = os.path.normpath(ks_file_path)
                if os.path.exists(normalized_path):
                    print(f"✅ .ksファイルが見つかりました: {normalized_path}")
                    raw_dialogue_data = dialogue_loader.load_dialogue_from_ks(normalized_path)
                    if raw_dialogue_data:
                        from ..dialogue.data_normalizer import normalize_dialogue_data
                        dialogue_data = normalize_dialogue_data(raw_dialogue_data)
                        if dialogue_data:
                            game_state['dialogue_data'] = dialogue_data
                            game_state['current_paragraph'] = 0
                            initialize_first_scene(game_state)
                            print(f"🎯 .ksファイルの読み込み完了: {len(dialogue_data)}個のダイアログ")
                        else:
                            print("❌ ダイアログデータの正規化に失敗")
                    else:
                        print("❌ .ksファイルの読み込みに失敗")
                else:
                    print(f"❌ .ksファイルが見つかりません: {normalized_path}")
            
            print("🎮 メインゲームループを開始...")
            
            # メインゲームループを実行
            clock = pygame.time.Clock()
            running = True
            
            while running:
                # イベント処理
                running = handle_events(game_state, screen)
                if not running:
                    break
                
                # ESCキーでマップに戻る
                keys = pygame.key.get_pressed()
                if keys[pygame.K_ESCAPE]:
                    print("🔙 ESCキーでマップに戻ります")
                    break
                
                # ゲーム状態の更新
                self.update_game_state(game_state)
                
                # 描画処理
                self.render_game(game_state)
                
                # フレームレート制限
                clock.tick(60)
            
            # イベント終了時（画面サイズは変更していないのでそのまま）
            print("🔙 イベント終了、マップ画面に戻ります")
            return "back_to_map"
            
        except Exception as e:
            print(f"❌ メインゲーム実行エラー: {e}")
            import traceback
            traceback.print_exc()
            # エラー時もマップ画面に戻る（画面サイズは変更していないのでそのまま）
            return "back_to_map"
    
    def update_game_state(self, game_state):
        """ゲーム状態を更新"""
        try:
            # テキスト表示の更新
            if 'text_renderer' in game_state:
                game_state['text_renderer'].update()
            
            # 背景アニメーションの更新
            from dialogue.model import update_background_animation
            update_background_animation(game_state)
            
            # キャラクターアニメーションの更新
            from dialogue.character_manager import update_character_animations
            update_character_animations(game_state)
            
            # controller2のupdate_game関数を使用（auto/skip機能に必要）
            from dialogue.controller2 import update_game
            update_game(game_state)
        except Exception as e:
            print(f"ゲーム状態更新エラー: {e}")
    
    def render_game(self, game_state):
        """ゲーム画面を描画"""
        try:
            screen = game_state['screen']
            
            # 画面をクリア
            screen.fill((0, 0, 0))
            
            # 背景を描画
            from dialogue.model import draw_background
            draw_background(game_state)
            
            # キャラクターを描画
            if 'active_characters' in game_state and game_state['active_characters']:
                from dialogue.character_manager import draw_characters
                draw_characters(game_state)
            
            # UI画像を描画 (auto, skip, text-box) - バックログ表示中は描画しない
            if ('image_manager' in game_state and 'images' in game_state and
                not game_state.get('backlog_manager', type('', (), {'is_showing_backlog': lambda: False})).is_showing_backlog()):
                image_manager = game_state['image_manager']
                images = game_state['images']
                show_text = game_state.get('show_text', True)
                image_manager.draw_ui_elements(screen, images, show_text)
            
            # テキストを描画（選択肢表示中またはバックログ表示中は非表示）
            if ('text_renderer' in game_state and 
                game_state.get('show_text', True) and 
                not game_state.get('choice_renderer', type('', (), {'is_choice_showing': lambda: False})).is_choice_showing() and
                not game_state.get('backlog_manager', type('', (), {'is_showing_backlog': lambda: False})).is_showing_backlog()):
                game_state['text_renderer'].render()
            
            # 選択肢を描画
            if 'choice_renderer' in game_state:
                game_state['choice_renderer'].render()
            
            # バックログを描画
            if 'backlog_manager' in game_state:
                game_state['backlog_manager'].render()
            
            # 画面を更新
            pygame.display.flip()
            
        except Exception as e:
            print(f"❌ 描画エラー: {e}")
            import traceback
            traceback.print_exc()
            # エラー時は黒い画面
            screen.fill((0, 0, 0))
            pygame.display.flip()
    
    def reinitialize_ui_elements(self, game_state, screen, screen_size):
        """画面サイズ変更後にUI要素を再初期化"""
        try:
            from dialogue.text_renderer import TextRenderer
            from dialogue.choice_renderer import ChoiceRenderer
            from dialogue.backlog_manager import BacklogManager
            from image_manager import ImageManager
            
            # 新しい画面サイズでUI要素を再作成
            text_renderer = TextRenderer(screen, DEBUG)
            choice_renderer = ChoiceRenderer(screen, DEBUG)
            
            # バックログマネージャーの再初期化
            backlog_manager = BacklogManager(screen, text_renderer.fonts, DEBUG)
            text_renderer.set_backlog_manager(backlog_manager)
            
            # 画像マネージャーで画像を新しいサイズで再読み込み
            image_manager = ImageManager(DEBUG)
            images = image_manager.load_all_images(screen_size[0], screen_size[1])
            
            # ゲーム状態を更新
            game_state['text_renderer'] = text_renderer
            game_state['choice_renderer'] = choice_renderer
            game_state['backlog_manager'] = backlog_manager
            game_state['image_manager'] = image_manager
            game_state['images'] = images
            
            print(f"UI要素を画面サイズ {screen_size} で再初期化しました")
            
        except Exception as e:
            print(f"UI要素再初期化エラー: {e}")
            import traceback
            traceback.print_exc()
    
    def draw_background(self, game_state):
        """背景を描画"""
        try:
            screen = game_state['screen']
            bg_state = game_state.get('background_state', {})
            bg_name = bg_state.get('current_bg', 'school')
            
            
            if 'images' in game_state and 'backgrounds' in game_state['images']:
                if bg_name in game_state['images']['backgrounds']:
                    bg_image = game_state['images']['backgrounds'][bg_name]
                    if bg_image:
                        screen.blit(bg_image, (0, 0))
        except Exception as e:
            print(f"❌ 背景描画エラー: {e}")
            import traceback
            traceback.print_exc()
    
    def run_ks_event_in_window(self, dialogue_data, event_info):
        """現在のウィンドウで.ksイベントを実行"""
        print(f"📜 .ksイベントを実行: {len(dialogue_data)}個のダイアログ")
        
        current_dialogue = 0
        event_running = True
        
        # 強制的に最初の画面を表示
        
        # フォント設定
        font_large = pygame.font.Font(None, 36)
        font_medium = pygame.font.Font(None, 24)
        font_small = pygame.font.Font(None, 18)
        
        while event_running and current_dialogue < len(dialogue_data):
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return "back_to_map"
                    elif event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
                        current_dialogue += 1
                        if current_dialogue >= len(dialogue_data):
                            event_running = False
            
            # 画面描画
            self.screen.fill((20, 25, 35))  # 暗い背景
            
            if current_dialogue < len(dialogue_data):
                dialogue_item = dialogue_data[current_dialogue]
                
                # タイトル表示
                title_text = font_large.render(event_info.title, True, (255, 215, 0))
                title_rect = title_text.get_rect(center=(self.screen_width // 2, 50))
                self.screen.blit(title_text, title_rect)
                
                # テキストボックス
                text_box_rect = pygame.Rect(50, self.screen_height - 200, 
                                          self.screen_width - 100, 150)
                pygame.draw.rect(self.screen, (40, 45, 60, 200), text_box_rect)
                pygame.draw.rect(self.screen, (70, 130, 180), text_box_rect, 3)
                
                # 話者名
                if len(dialogue_item) > 9 and dialogue_item[9]:
                    speaker = dialogue_item[9]
                elif len(dialogue_item) > 1 and dialogue_item[1]:
                    speaker = dialogue_item[1]
                else:
                    speaker = "ナレーション"
                    
                speaker_text = font_medium.render(speaker, True, (255, 215, 0))
                self.screen.blit(speaker_text, (text_box_rect.left + 20, text_box_rect.top + 10))
                
                # セリフ
                if len(dialogue_item) > 5 and dialogue_item[5]:
                    dialogue_text = dialogue_item[5]
                    # 長いテキストを改行
                    lines = self.wrap_text(dialogue_text, font_small, text_box_rect.width - 40)
                    for i, line in enumerate(lines[:4]):  # 最大4行まで
                        text_surface = font_small.render(line, True, (255, 255, 255))
                        self.screen.blit(text_surface, (text_box_rect.left + 20, text_box_rect.top + 45 + i * 25))
                
                # 進行状況
                progress_text = font_small.render(f"{current_dialogue + 1}/{len(dialogue_data)}", True, (255, 255, 255))
                self.screen.blit(progress_text, (text_box_rect.right - 100, text_box_rect.bottom - 30))
                
                # 操作説明
                help_text = font_small.render("Space/Enter: 次へ  ESC: マップに戻る", True, (192, 192, 192))
                help_rect = help_text.get_rect(center=(self.screen_width // 2, self.screen_height - 30))
                self.screen.blit(help_text, help_rect)
            
            pygame.display.flip()
            self.clock.tick(60)
        
        return "back_to_map"
    
    def wrap_text(self, text, font, max_width):
        """テキストを指定幅で改行"""
        words = text.split(' ')
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            if font.size(test_line)[0] <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                else:
                    lines.append(word)
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines
    
    def handle_key(self, key):
        """キー処理"""
        # 時間進行ボタン（Spaceキー）
        if key == pygame.K_SPACE:
            self.advance_time()
            
        # キャラクター選択（数字キー 1-5）
        elif key == pygame.K_1:
            self.select_character_by_number(0)
        elif key == pygame.K_2:
            self.select_character_by_number(1)
        elif key == pygame.K_3:
            self.select_character_by_number(2)
        elif key == pygame.K_4:
            self.select_character_by_number(3)
        elif key == pygame.K_5:
            self.select_character_by_number(4)
            
        # イベント実行（Enterキー）
        elif key == pygame.K_RETURN or key == pygame.K_KP_ENTER:
            if self.selected_character:
                event_info = self.get_current_event_for_character(
                    self.selected_character.name, 
                    self.selected_location.name if self.selected_location else None
                )
                if event_info:
                    return f"launch_event:{event_info.filename}"
        
        # デバッグ情報表示（Tabキー）
        elif key == pygame.K_TAB:
            self.print_debug_info()
            
        return None
    
    def select_character_by_number(self, index):
        """数字キーでキャラクターを選択"""
        current_locations = self.get_current_locations()
        all_characters = []
        
        for location in current_locations:
            all_characters.extend(location.girl_characters)
        
        if 0 <= index < len(all_characters):
            self.selected_character = all_characters[index]
            print(f"🎯 キャラクター選択: {self.selected_character.name}")
    
    def print_debug_info(self):
        """デバッグ情報を出力"""
        print(f"📊 現在の状態:")
        print(f"  時間: {self.get_time_display()}")
        print(f"  マップタイプ: {self.current_map_type.value}")
        print(f"  選択中のキャラクター: {self.selected_character.name if self.selected_character else 'なし'}")
        print(f"  現在の場所数: {len(self.get_current_locations())}")
    
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
        
        # 静的DBからヒロイン情報を取得して比較
        for event in self.events:
            if hasattr(event, 'heroine') and event.heroine == character_name:
                # completed_eventsで実行回数をチェック
                event_data = self.completed_events.get(event.event_id, {})
                if event_data.get('count', 0) > 0:
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
    
    def cleanup(self):
        """サブシステム終了時の処理（SubsystemBase実装）"""
        try:
            self.bgm_manager.stop_bgm()
            print("🔇 FieldMap cleanup: BGM停止")
        except Exception as e:
            print(f"⚠️ FieldMap cleanupエラー: {e}")

    def on_enter(self):
        """サブシステム開始時の処理（SubsystemBase実装）"""
        self.update_events()
        self.update_bgm()
        print("🎵 FieldMap on_enter: BGM再生")

    def update(self):
        """ゲーム状態の更新（main.pyからの呼び出し用）"""
        # アニメーション更新
        self.animation_time += 1
    
    def render(self):
        """画面描画（main.pyからの呼び出し用）"""
        # 全画面を黒で塗りつぶし（ピラーボックス用）
        self.screen.fill((0, 0, 0))

        # 背景画像を読み込んで描画
        try:
            if not hasattr(self, 'background_image'):
                # school.pngとmap_school.pngの両方を試行
                possible_paths = [
                    os.path.join(os.path.dirname(__file__), "..", "images", "maps", "school.png"),
                    os.path.join(os.path.dirname(__file__), "..", "images", "maps", "map_school.png")
                ]

                background_loaded = False
                for background_path in possible_paths:
                    if os.path.exists(background_path):
                        from config import CONTENT_WIDTH, CONTENT_HEIGHT
                        self.background_image = pygame.image.load(background_path)
                        # 4:3コンテンツサイズに合わせてスケール（正確な値を使用）
                        content_size = (CONTENT_WIDTH, CONTENT_HEIGHT)
                        self.background_image = pygame.transform.scale(self.background_image, content_size)
                        print(f"[MAP] 背景画像読み込み成功: {background_path} -> {content_size}")
                        background_loaded = True
                        break

                if not background_loaded:
                    print("[MAP] 背景画像が見つかりません。単色背景を使用します。")
                    self.background_image = None

            # 背景画像を4:3コンテンツ領域に描画
            if hasattr(self, 'background_image') and self.background_image:
                from config import OFFSET_X, OFFSET_Y
                self.screen.blit(self.background_image, (OFFSET_X, OFFSET_Y))
            else:
                # 背景なしの場合は4:3領域のみ単色で塗る
                from config import CONTENT_WIDTH, CONTENT_HEIGHT, OFFSET_X, OFFSET_Y
                content_rect = pygame.Rect(OFFSET_X, OFFSET_Y, CONTENT_WIDTH, CONTENT_HEIGHT)
                self.screen.fill((240, 240, 240), content_rect)
            
        except Exception as e:
            print(f"[MAP] 背景画像読み込みエラー: {e}")
            # フォールバック：単色背景
            self.screen.fill((240, 240, 240))

        # ★ピラーボックスを「奈落」にする：4:3コンテンツ領域にクリッピング設定★
        from config import CONTENT_WIDTH, CONTENT_HEIGHT, OFFSET_X, OFFSET_Y
        content_rect = pygame.Rect(OFFSET_X, OFFSET_Y, CONTENT_WIDTH, CONTENT_HEIGHT)
        self.screen.set_clip(content_rect)

        # 共通UI描画
        self.draw_locations()
        self.draw_girl_icons()
        self.draw_calendar()
        self.draw_ui_panel()

        # デバッグ情報
        if self.debug_mode:
            debug_text = f"デバッグモード - 時間: {self.animation_time}"
            debug_surface = self.fonts['small'].render(debug_text, True, (255, 255, 255))
            self.screen.blit(debug_surface, (10, 10))

        # ★クリッピング解除★
        self.screen.set_clip(None)
    
    def handle_events(self, events) -> str | None:
        """イベントリストを処理（SubsystemBase実装）"""
        result = None
        for event in events:
            r = self.handle_event(event)
            if r is not None:
                result = r
        return result

    def handle_event(self, event):
        """単一のイベントを処理して結果を返す（main.pyからの呼び出し用）"""
        if event.type == pygame.QUIT:
            return "back_to_menu"
        elif event.type == pygame.MOUSEBUTTONDOWN:
            print(f"🖱️ マウスボタンが押されました: ボタン={event.button}, 位置={event.pos}")
            if event.button == 1:  # 左クリック
                result = self.handle_click(event.pos)
                if result:
                    return result
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return "back_to_menu"
            else:
                result = self.handle_key(event.key)
                if result:
                    return result
        return None
    
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
                        result = self.handle_key(event.key)
                        if result and result.startswith("launch_event:"):
                            event_file = result.split(":", 1)[1]
                            print(f"🎬 イベント開始: {event_file}")
                            return self.launch_dialogue_event(event_file)
            
            # アニメーション更新
            self.animation_time += 1
            
            # 描画
            self.draw_advanced_sky()
            self.draw_clouds()  # 雲を追加
            self.draw_terrain()
            
            # マップタイプ別描画（朝昼は学校、放課後は街）
            current_period = get_time_manager().get_current_period()
            if current_period == "放課後" or self.current_map_type == MapType.WEEKEND:
                self.draw_weekend_map()  # 放課後と休日は街マップ
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
    print("=== mo-kiss FieldMap ===")
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
    
    game = FieldMap()
    game.run()