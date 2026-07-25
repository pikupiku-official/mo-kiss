"""イベントメタデータに設定された表示日時を読み込む。"""

from __future__ import annotations

import csv
import datetime
import os
import re
from dataclasses import dataclass

from core.path_utils import get_project_root


EVENT_DATETIME_HEADER = "イベント日時"
EVENT_DATETIME_FORMAT = "YYYY-MM-DD 朝/昼/放課後/夜"
VALID_PERIODS = ("朝", "昼", "放課後", "夜")
_EVENT_DATETIME_RE = re.compile(
    r"^\s*(\d{4})-(\d{1,2})-(\d{1,2})\s+(朝|昼|放課後|夜)\s*$"
)


@dataclass(frozen=True)
class EventDateTime:
    year: int
    month: int
    day: int
    period: str

    @property
    def weekday(self) -> int:
        return datetime.date(self.year, self.month, self.day).weekday()


def parse_event_datetime(value: str) -> EventDateTime | None:
    """`1999-06-01 夜`形式を解析する。空欄は未設定としてNoneを返す。"""
    if not value or not value.strip():
        return None

    match = _EVENT_DATETIME_RE.fullmatch(value)
    if not match:
        raise ValueError(f"{EVENT_DATETIME_FORMAT} の形式で入力してください")

    year, month, day, period = match.groups()
    try:
        parsed_date = datetime.date(int(year), int(month), int(day))
    except ValueError as exc:
        raise ValueError(f"存在しない日付です: {year}-{month}-{day}") from exc

    return EventDateTime(
        year=parsed_date.year,
        month=parsed_date.month,
        day=parsed_date.day,
        period=period,
    )


def load_event_datetime(
    event_id: str | None,
    events_csv_path: str | None = None,
) -> EventDateTime | None:
    """events.csvからイベントIDに対応する表示日時を取得する。"""
    if not event_id:
        return None

    csv_path = events_csv_path or os.path.join(
        get_project_root(), "events", "events.csv"
    )
    if not os.path.exists(csv_path):
        return None

    with open(csv_path, "r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            if row.get("イベントID") == event_id:
                return parse_event_datetime(row.get(EVENT_DATETIME_HEADER) or "")
    return None


def get_event_id_from_ks_path(ks_file_path: str | None) -> str | None:
    if not ks_file_path:
        return None
    return os.path.splitext(os.path.basename(ks_file_path))[0]


def apply_event_datetime(
    text_renderer,
    *,
    event_id: str | None = None,
    ks_file_path: str | None = None,
) -> EventDateTime | None:
    """イベント日時があればTextRendererへ設定し、なければ解除する。"""
    resolved_event_id = event_id or get_event_id_from_ks_path(ks_file_path)
    try:
        event_datetime = load_event_datetime(resolved_event_id)
    except (OSError, csv.Error, ValueError) as exc:
        print(
            f"[EVENT_DATETIME] {resolved_event_id or '-'}のイベント日時を"
            f"読み込めません: {exc}"
        )
        event_datetime = None
    text_renderer.set_event_datetime(event_datetime)
    return event_datetime
