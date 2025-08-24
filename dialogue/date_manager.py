import datetime

class DateManager:
    """ゲーム内日付管理クラス"""
    
    def __init__(self, start_year=1999, start_month=5, start_day=31, start_weekday=0):
        """
        日付管理システムを初期化する
        
        Args:
            start_year (int): ゲーム開始年（西暦）
            start_month (int): ゲーム開始月
            start_day (int): ゲーム開始日
            start_weekday (int): ゲーム開始曜日（0=月曜日、6=日曜日）
        """
        self.current_year = start_year
        self.current_month = start_month
        self.current_day = start_day
        self.current_weekday = start_weekday
        
        # 曜日名の定義
        self.weekday_names = ["月", "火", "水", "木", "金", "土", "日"]
        
        # 月の日数
        self.days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    
    def is_leap_year(self, year):
        """うるう年判定"""
        return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
    
    def get_days_in_month(self, year, month):
        """指定した年月の日数を取得"""
        if month == 2 and self.is_leap_year(year):
            return 29
        return self.days_in_month[month - 1]
    
    def advance_day(self, days=1):
        """日付を進める"""
        for _ in range(days):
            self.current_day += 1
            self.current_weekday = (self.current_weekday + 1) % 7
            
            # 月末チェック
            if self.current_day > self.get_days_in_month(self.current_year, self.current_month):
                self.current_day = 1
                self.current_month += 1
                
                # 年末チェック
                if self.current_month > 12:
                    self.current_month = 1
                    self.current_year += 1
    
    def set_date(self, year, month, day):
        """日付を直接設定"""
        self.current_year = year
        self.current_month = month
        self.current_day = day
        
        # 曜日を計算
        date_obj = datetime.date(year, month, day)
        self.current_weekday = date_obj.weekday()
    
    def to_era_format(self):
        """元号形式に変換して返す（全角アラビア数字使用）"""
        # 元号の定義
        era_info = [
            ("平成", 1989, 1, 8),   # 平成開始日
            ("令和", 2019, 5, 1),   # 令和開始日
        ]
        
        # 適用される元号を特定
        era_name = "昭和"  # デフォルト
        era_year = self.current_year - 1925  # 昭和年
        
        for era, start_year, start_month, start_day in reversed(era_info):
            if (self.current_year > start_year or 
                (self.current_year == start_year and self.current_month > start_month) or
                (self.current_year == start_year and self.current_month == start_month and self.current_day >= start_day)):
                era_name = era
                if era == "平成":
                    era_year = self.current_year - 1988
                elif era == "令和":
                    era_year = self.current_year - 2018
                break
        
        # 数字を全角アラビア数字に変換
        era_year_zenkaku = self.to_zenkaku_number(era_year)
        month_zenkaku = self.to_zenkaku_number(self.current_month)
        day_zenkaku = self.to_zenkaku_number(self.current_day)
        weekday_name = self.weekday_names[self.current_weekday]
        
        return f"{era_name}{era_year_zenkaku}年{month_zenkaku}月{day_zenkaku}日（{weekday_name}）"
    
    def to_zenkaku_number(self, num):
        """数字を全角アラビア数字に変換"""
        # 半角数字から全角数字への変換テーブル
        zenkaku_digits = "０１２３４５６７８９"
        hankaku_digits = "0123456789"
        
        num_str = str(num)
        zenkaku_str = ""
        
        for digit in num_str:
            if digit in hankaku_digits:
                zenkaku_str += zenkaku_digits[int(digit)]
            else:
                zenkaku_str += digit
        
        return zenkaku_str
    
    def to_kanji_number(self, num):
        """数字を漢数字に変換"""
        if num == 0:
            return "〇"
        
        kanji_digits = ["〇", "一", "二", "三", "四", "五", "六", "七", "八", "九"]
        kanji_units = ["", "十", "百", "千"]
        
        if num < 10:
            return kanji_digits[num]
        elif num < 20:
            if num == 10:
                return "十"
            else:
                return "十" + kanji_digits[num - 10]
        elif num < 100:
            tens = num // 10
            ones = num % 10
            result = kanji_digits[tens] + "十"
            if ones > 0:
                result += kanji_digits[ones]
            return result
        else:
            # 100以上の場合は単純な変換
            result = ""
            str_num = str(num)
            for i, digit in enumerate(reversed(str_num)):
                digit_val = int(digit)
                if digit_val > 0:
                    if i > 0 and digit_val == 1 and i < 4:
                        result = kanji_units[i] + result
                    else:
                        result = kanji_digits[digit_val] + kanji_units[i] + result
            return result
    
    def get_current_date(self):
        """現在の日付情報を取得"""
        return {
            'year': self.current_year,
            'month': self.current_month,
            'day': self.current_day,
            'weekday': self.current_weekday,
            'weekday_name': self.weekday_names[self.current_weekday],
            'era_format': self.to_era_format()
        }

# グローバルインスタンス
_date_manager = None

def get_date_manager():
    """日付マネージャーのシングルトンインスタンスを取得"""
    global _date_manager
    if _date_manager is None:
        from config import GAME_START_YEAR, GAME_START_MONTH, GAME_START_DAY, GAME_START_WEEKDAY
        _date_manager = DateManager(GAME_START_YEAR, GAME_START_MONTH, GAME_START_DAY, GAME_START_WEEKDAY)
    return _date_manager

def advance_game_date(days=1):
    """ゲーム内日付を進める"""
    date_manager = get_date_manager()
    date_manager.advance_day(days)
    return date_manager.get_current_date()

def get_current_game_date():
    """現在のゲーム内日付を取得"""
    date_manager = get_date_manager()
    return date_manager.get_current_date()

def set_game_date(year, month, day):
    """ゲーム内日付を設定"""
    date_manager = get_date_manager()
    date_manager.set_date(year, month, day)
    return date_manager.get_current_date()