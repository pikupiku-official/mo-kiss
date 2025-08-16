import datetime
import csv
import os
import sys
import subprocess
from typing import List, Dict, Tuple
from map_config import TimeSlot

# プロジェクトルートをパスに追加
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, "..", "..")
sys.path.insert(0, project_root)

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

class EventManager:
    def __init__(self):
        self.events = []
        self.completed_events = set()
        self.events_file = os.path.join(project_root, "events", "events.csv")
        self.completed_file = os.path.join(project_root, "events", "completed_events.csv")
        self.load_events()
        self.load_completed_events()
    
    def load_events(self):
        """CSVファイルからイベントを読み込み"""
        try:
            with open(self.events_file, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    event = GameEvent(
                        row['event_id'],
                        row['start_date'],
                        row['end_date'],
                        row['time_slots'],
                        row['heroine'],
                        row['location'],
                        row['title'],
                        row['active']
                    )
                    self.events.append(event)
        except FileNotFoundError:
            print(f"イベントファイルが見つかりません: {self.events_file}")
        except Exception as e:
            print(f"イベント読み込みエラー: {e}")
    
    def load_completed_events(self):
        """完了したイベントを読み込み"""
        try:
            with open(self.completed_file, 'r', encoding='utf-8') as file:
                reader = csv.reader(file)
                for row in reader:
                    if row:
                        self.completed_events.add(row[0])
        except FileNotFoundError:
            # ファイルが存在しない場合は新規作成
            self.initialize_completed_events_file()
        except Exception as e:
            print(f"完了イベント読み込みエラー: {e}")
    
    def initialize_completed_events_file(self):
        """完了イベントファイルを初期化"""
        try:
            with open(self.completed_file, 'w', encoding='utf-8', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(['event_id'])
        except Exception as e:
            print(f"完了イベントファイル初期化エラー: {e}")
    
    def mark_event_completed(self, event_id: str):
        """イベントを完了としてマーク"""
        if event_id not in self.completed_events:
            self.completed_events.add(event_id)
            try:
                with open(self.completed_file, 'a', encoding='utf-8', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow([event_id])
            except Exception as e:
                print(f"完了イベント保存エラー: {e}")
    
    def get_available_events(self, current_date: datetime.date, current_time: str, location: str = None, heroine: str = None) -> List[GameEvent]:
        """利用可能なイベントを取得"""
        available_events = []
        
        for event in self.events:
            # 完了済みイベントはスキップ
            if event.event_id in self.completed_events:
                continue
            
            # 現在の日時で有効なイベントかチェック
            if not event.is_active(current_date, current_time):
                continue
            
            # 場所フィルター
            if location and event.location != location:
                continue
            
            # ヒロインフィルター
            if heroine and event.heroine != heroine:
                continue
            
            available_events.append(event)
        
        return available_events
    
    def get_events_by_heroine(self, heroine: str, current_date: datetime.date, current_time: str) -> List[GameEvent]:
        """特定のヒロインのイベントを取得"""
        return self.get_available_events(current_date, current_time, heroine=heroine)
    
    def get_events_by_location(self, location: str, current_date: datetime.date, current_time: str) -> List[GameEvent]:
        """特定の場所のイベントを取得"""
        return self.get_available_events(current_date, current_time, location=location)
    
    def execute_event(self, event: GameEvent, screen):
        """イベントを実行"""
        print(f"イベント実行: {event.title} (ID: {event.event_id})")
        
        # 元の画面サイズを保存
        original_size = screen.get_size()
        
        try:
            ks_file = os.path.join(project_root, "events", f"{event.event_id}.ks")
            if os.path.exists(ks_file):
                # メインゲームエンジンを起動
                main_script = os.path.join(project_root, "main.py")
                result = subprocess.run([
                    sys.executable, main_script,
                    "--scenario", ks_file
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    # イベントを完了としてマーク
                    self.mark_event_completed(event.event_id)
                    print(f"イベント {event.event_id} が正常に完了しました")
                    return True
                else:
                    print(f"イベント実行エラー: {result.stderr}")
                    return False
            else:
                print(f"イベントファイルが見つかりません: {ks_file}")
                return False
                
        except Exception as e:
            print(f"イベント実行中にエラーが発生しました: {e}")
            return False
        
        finally:
            # 画面サイズを復元
            import pygame
            screen = pygame.display.set_mode(original_size)
    
    def get_event_counts_for_heroine(self, heroine: str, current_date: datetime.date, current_time: str) -> Dict[str, int]:
        """ヒロインの利用可能・完了イベント数を取得"""
        heroine_events = [e for e in self.events if e.heroine == heroine]
        
        available = 0
        completed = 0
        
        for event in heroine_events:
            if event.event_id in self.completed_events:
                completed += 1
            elif event.is_active(current_date, current_time):
                available += 1
        
        return {
            'available': available,
            'completed': completed
        }