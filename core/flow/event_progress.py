"""Event completion persistence and post-event time progression."""

from __future__ import annotations

import csv
import os
from dataclasses import dataclass

from core.path_utils import get_project_root
from core.services.time_manager import get_time_manager


@dataclass(frozen=True)
class EventCompletionDecision:
    """Result of completing a regular event."""

    next_mode: str
    time_advanced: bool


class EventProgress:
    """Persist event history and decide the destination after dialogue."""

    def __init__(self, project_root=None, time_manager_getter=get_time_manager):
        self.project_root = project_root or get_project_root()
        self._time_manager_getter = time_manager_getter

    @property
    def events_csv_path(self):
        return os.path.join(self.project_root, "events", "events.csv")

    @property
    def completed_events_csv_path(self):
        return os.path.join(
            self.project_root,
            "data",
            "current_state",
            "completed_events.csv",
        )

    def record_completion(self, event_id: str | None) -> bool:
        """Record one execution of an event. Return whether it was recorded."""
        if not event_id:
            print("[EVENT] 現在のイベントIDが設定されていません")
            return False

        try:
            if not self._event_exists(event_id):
                print(f"[EVENT] events.csvに{event_id}が見つかりません")
                return False

            rows = self._read_completed_events()
            event_found = False
            game_time = self._time_manager_getter().get_full_time_string()

            for row in rows:
                if row.get("イベントID") != event_id:
                    continue
                current_count = int(row.get("実行回数", "0"))
                row["実行回数"] = str(current_count + 1)
                row["実行日時"] = game_time
                event_found = True
                print(f"[EVENT] {event_id}の実行回数を{current_count + 1}に更新")

            if not event_found:
                rows.append(
                    {
                        "イベントID": event_id,
                        "実行日時": game_time,
                        "実行回数": "1",
                        "有効フラグ": "TRUE",
                    }
                )
                print(f"[EVENT] {event_id}を新規記録（実行回数: 1）")

            self._write_completed_events(rows)
            return True
        except Exception as exc:
            print(f"[EVENT] イベント完了記録エラー: {exc}")
            return False

    def complete_dialogue(self, event_id: str | None) -> EventCompletionDecision:
        """Record a regular event, advance time when required, and choose a scene."""
        self.record_completion(event_id)
        if not event_id or event_id == "E001":
            print("[TIME] E001終了 - 時間進行なしでmapへ")
            return EventCompletionDecision(next_mode="map", time_advanced=False)

        time_manager = self._time_manager_getter()
        current_period = time_manager.get_current_period()
        was_after_school = time_manager.is_after_school()
        print(
            f"[DEBUG] イベント{event_id}完了後 - "
            f"時間帯: {current_period}, 放課後: {was_after_school}"
        )
        time_manager.advance_period()

        if was_after_school:
            print(
                f"[TIME] 放課後イベント終了 → "
                f"{time_manager.get_full_time_string()} → 家モジュールへ"
            )
            return EventCompletionDecision(next_mode="home", time_advanced=True)

        print(
            f"[TIME] イベント{event_id}終了 → "
            f"{time_manager.get_full_time_string()} → mapへ"
        )
        return EventCompletionDecision(next_mode="map", time_advanced=True)

    def _event_exists(self, event_id: str) -> bool:
        if not os.path.exists(self.events_csv_path):
            return False
        with open(self.events_csv_path, "r", encoding="utf-8") as handle:
            return any(
                row.get("イベントID") == event_id
                for row in csv.DictReader(handle)
            )

    def _read_completed_events(self) -> list[dict[str, str]]:
        if not os.path.exists(self.completed_events_csv_path):
            return []

        rows = []
        with open(self.completed_events_csv_path, "r", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                for field in ("ヒロイン名", "場所", "イベントタイトル"):
                    row.pop(field, None)
                row.setdefault("有効フラグ", "TRUE")
                rows.append(row)
        return rows

    def _write_completed_events(self, rows: list[dict[str, str]]) -> None:
        os.makedirs(os.path.dirname(self.completed_events_csv_path), exist_ok=True)
        fieldnames = ["イベントID", "実行日時", "実行回数", "有効フラグ"]
        with open(
            self.completed_events_csv_path,
            "w",
            encoding="utf-8",
            newline="",
        ) as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
