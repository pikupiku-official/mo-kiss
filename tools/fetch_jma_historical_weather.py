import argparse
import datetime as dt
import json
import os
import re
import urllib.request
from html import unescape


FUCHU_DAILY_URL = (
    "https://www.data.jma.go.jp/stats/etrn/view/daily_a1.php"
    "?prec_no=44&block_no=1133&year={year}&month={month}&day=1&view="
)
FUCHU_HOURLY_URL = (
    "https://www.data.jma.go.jp/stats/etrn/view/hourly_a1.php"
    "?prec_no=44&block_no=1133&year={year}&month={month}&day={day}&view="
)
TOKYO_HOURLY_URL = (
    "https://www.data.jma.go.jp/stats/etrn/view/hourly_s1.php"
    "?prec_no=44&block_no=47662&year={year}&month={month}&day={day}&view="
)
PERIOD_HOURS = ("09", "12", "15", "21")


def fetch_html(url):
    with urllib.request.urlopen(url, timeout=30) as response:
        return response.read().decode("utf-8", "ignore")


def strip_tags(text):
    text = re.sub(r'<img[^>]*alt="([^"]+)"[^>]*>', r"\1", text)
    text = re.sub(r"<br\s*/?>", " ", text)
    text = re.sub(r"<.*?>", "", text)
    return unescape(text).replace("\xa0", " ").strip()


def parse_table_rows(html_text):
    match = re.search(r"<table id=['\"]tablefix1['\"][^>]*>(.*?)</table>", html_text, flags=re.S)
    if not match:
        return []

    table_html = match.group(1)
    rows = []
    for row_html in re.findall(r"<tr[^>]*>(.*?)</tr>", table_html, flags=re.S):
        cells = re.findall(r"<t[hd][^>]*>(.*?)</t[hd]>", row_html, flags=re.S)
        rows.append([strip_tags(cell) for cell in cells])
    return rows


def parse_fuchu_daily_month(year, month):
    rows = parse_table_rows(fetch_html(FUCHU_DAILY_URL.format(year=year, month=month)))
    daily = {}
    for row in rows:
        if len(row) < 7 or not row[0].isdigit():
            continue
        day = int(row[0])
        daily[f"{year:04d}-{month:02d}-{day:02d}"] = {
            "fuchu_daily_mean": row[4],
            "fuchu_daily_max": row[5],
            "fuchu_daily_min": row[6],
        }
    return daily


def parse_fuchu_hourly_day(year, month, day):
    rows = parse_table_rows(fetch_html(FUCHU_HOURLY_URL.format(year=year, month=month, day=day)))
    hourly = {}
    for row in rows:
        if len(row) < 3 or not row[0].isdigit():
            continue
        hourly[f"{int(row[0]):02d}"] = row[2]
    return hourly


def parse_tokyo_weather_day(year, month, day):
    rows = parse_table_rows(fetch_html(TOKYO_HOURLY_URL.format(year=year, month=month, day=day)))
    weather = {}
    for row in rows:
        if len(row) < 15 or not row[0].isdigit():
            continue
        weather[f"{int(row[0]):02d}"] = row[14]
    return weather


def choose_weather(weather_by_hour):
    for hour in PERIOD_HOURS:
        weather = weather_by_hour.get(hour, "")
        if weather:
            return weather

    for hour in sorted(weather_by_hour):
        weather = weather_by_hour[hour]
        if weather:
            return weather

    return ""


def daterange(start_date, end_date):
    current = start_date
    while current <= end_date:
        yield current
        current += dt.timedelta(days=1)


def build_dataset(start_date, end_date):
    result = {}
    month_cache = {}

    for current in daterange(start_date, end_date):
        month_key = (current.year, current.month)
        if month_key not in month_cache:
            month_cache[month_key] = parse_fuchu_daily_month(current.year, current.month)
        result.update(month_cache[month_key])

        key = current.strftime("%Y-%m-%d")
        result.setdefault(key, {})
        result[key]["fuchu_temperature"] = parse_fuchu_hourly_day(
            current.year,
            current.month,
            current.day,
        )
        tokyo_weather = parse_tokyo_weather_day(current.year, current.month, current.day)
        result[key]["weather"] = choose_weather(tokyo_weather)
        result[key]["tokyo_weather_by_hour"] = {
            hour: tokyo_weather.get(hour, "")
            for hour in PERIOD_HOURS
        }
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", default="1999-05-31")
    parser.add_argument("--end", default="1999-12-31")
    parser.add_argument(
        "--output",
        default=os.path.join("data", "historical_weather", "jma_tokyo_fuchu_1999.json"),
    )
    args = parser.parse_args()

    start_date = dt.date.fromisoformat(args.start)
    end_date = dt.date.fromisoformat(args.end)
    dataset = build_dataset(start_date, end_date)

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)

    print(f"Wrote {len(dataset)} rows to {args.output}")


if __name__ == "__main__":
    main()
