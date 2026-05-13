import json
import os
from datetime import datetime, timedelta

class TimeManager:
    """時間帯・日付管理システム"""
    
    def __init__(self, debug=False):
        self.debug = debug
        self.data_file = os.path.join("data", "current_state", "time_state.json")
        
        # 時間帯の定義
        self.time_periods = ["朝", "昼", "放課後", "夜"]
        
        # デフォルト値
        self.current_year = 1999
        self.current_month = 5
        self.current_day = 31
        self.current_weekday = 0  # 0=月曜日
        self.current_period = "朝"  # 朝、昼、放課後
        
        # データ読み込み
        self.load_time_state()
    
    def load_time_state(self):
        """時間状態をファイルから読み込み"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.current_year = data.get('year', 1999)
                    self.current_month = data.get('month', 5)
                    self.current_day = data.get('day', 31)
                    self.current_weekday = data.get('weekday', 0)
                    self.current_period = data.get('period', '朝')
                print(f"[TIME] 時間状態読み込み: {self.get_date_string()} {self.current_period}")
            else:
                print(f"[TIME] デフォルト時間で初期化: {self.get_date_string()} {self.current_period}")
        except Exception as e:
            print(f"[TIME] 読み込みエラー: {e}")
    
    def save_time_state(self):
        """時間状態をファイルに保存"""
        try:
            data = {
                'year': self.current_year,
                'month': self.current_month,
                'day': self.current_day,
                'weekday': self.current_weekday,
                'period': self.current_period
            }
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"[TIME] 時間状態保存: {self.get_date_string()} {self.current_period}")
        except Exception as e:
            print(f"[TIME] 保存エラー: {e}")
    
    def advance_period(self):
        """時間帯を一つ進める（朝→昼→放課後→夜→翌日の朝）"""
        current_index = self.time_periods.index(self.current_period)
        
        if current_index < len(self.time_periods) - 1:
            # 同日内で次の時間帯に進む
            self.current_period = self.time_periods[current_index + 1]
            print(f"[TIME] 時間帯進行: {self.current_period}")
        else:
            # 夜の場合は翌日の朝に進む
            self.advance_day()
            self.current_period = "朝"
            print(f"[TIME] 翌日に進行: {self.get_date_string()} {self.current_period}")
        
        self.save_time_state()
        return self.current_period
    
    def advance_day(self):
        """日付を一日進める"""
        # 簡易的な日付計算（月末は30日固定）
        self.current_day += 1
        if self.current_day > 30:
            self.current_day = 1
            self.current_month += 1
            if self.current_month > 12:
                self.current_month = 1
                self.current_year += 1
        
        # 曜日を進める
        self.current_weekday = (self.current_weekday + 1) % 7
        
        print(f"[TIME] 日付進行: {self.get_date_string()}")
    
    def set_to_morning(self):
        """朝に設定（寝るときに使用）"""
        self.advance_day()
        self.current_period = "朝"
        self.save_time_state()
        print(f"[TIME] 朝に設定: {self.get_date_string()} {self.current_period}")
    
    def get_current_period(self):
        """現在の時間帯を取得"""
        return self.current_period
    
    def is_after_school(self):
        """放課後かどうか判定"""
        return self.current_period == "放課後"
    
    def is_night(self):
        """夜かどうか判定"""
        return self.current_period == "夜"
    
    def get_date_string(self):
        """日付文字列を取得"""
        weekday_names = ["月", "火", "水", "木", "金", "土", "日"]
        return f"{self.current_year}年{self.current_month}月{self.current_day}日({weekday_names[self.current_weekday]})"
    
    def get_full_time_string(self):
        """完全な時間文字列を取得"""
        return f"{self.get_date_string()} {self.current_period}"
    
    def get_time_state(self):
        """時間状態を辞書で取得"""
        return {
            'year': self.current_year,
            'month': self.current_month,
            'day': self.current_day,
            'weekday': self.current_weekday,
            'period': self.current_period,
            'date_string': self.get_date_string(),
            'full_string': self.get_full_time_string()
        }

# グローバルインスタンス
_time_manager = None

def get_time_manager():
    """TimeManagerのグローバルインスタンスを取得"""
    global _time_manager
    if _time_manager is None:
        _time_manager = TimeManager()
    return _time_manager

def reload_time_manager():
    """TimeManagerを再読み込み（セーブ/ロード後に使用）"""
    global _time_manager
    _time_manager = TimeManager()
    return _time_manager

def init_time_manager():
    """TimeManagerを初期化"""
    global _time_manager
    _time_manager = TimeManager()
    return _time_manager