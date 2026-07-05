import json
import os


PERIOD_TO_HOUR = {
    "朝": "09",
    "昼": "12",
    "放課後": "15",
    "夜": "21",
}


class HistoricalWeather:
    def __init__(self, data_path=None):
        base_dir = os.path.dirname(os.path.dirname(__file__))
        self.data_path = data_path or os.path.join(
            base_dir,
            "data",
            "historical_weather",
            "jma_tokyo_fuchu_1999.json",
        )
        self._data = None

    def _load(self):
        if self._data is not None:
            return self._data

        if not os.path.exists(self.data_path):
            self._data = {}
            return self._data

        with open(self.data_path, "r", encoding="utf-8") as f:
            self._data = json.load(f)
        return self._data

    def get_entry(self, year, month, day):
        key = f"{year:04d}-{month:02d}-{day:02d}"
        return self._load().get(key)

    def get_display_text(self, year, month, day, period):
        entry = self.get_entry(year, month, day)
        if not entry:
            return ""

        weather = entry.get("weather", "")
        hour_key = PERIOD_TO_HOUR.get(period)
        temp = None
        if hour_key:
            temp = (entry.get("fuchu_temperature") or {}).get(hour_key)

        if temp in (None, "", "///"):
            temp = entry.get("fuchu_daily_mean")
            if temp not in (None, ""):
                return f"史実 {weather} {temp}℃"
            return f"史実 {weather}".strip()

        return f"史実 {weather} {temp}℃".strip()


_historical_weather = None


def get_historical_weather():
    global _historical_weather
    if _historical_weather is None:
        _historical_weather = HistoricalWeather()
    return _historical_weather
