import csv
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core.services.time_manager import format_game_datetime
from dialogue.event_datetime import (
    EventDateTime,
    apply_event_datetime,
    load_event_datetime,
    parse_event_datetime,
)


class EventDateTimeTest(unittest.TestCase):
    def test_parse_event_datetime(self):
        parsed = parse_event_datetime("1999-06-01 夜")

        self.assertEqual(parsed, EventDateTime(1999, 6, 1, "夜"))
        self.assertEqual(parsed.weekday, 1)

    def test_parse_event_datetime_rejects_invalid_values(self):
        for value in (
            "1999/06/01 夜",
            "1999-06-31 夜",
            "1999-06-01 深夜",
        ):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    parse_event_datetime(value)

    def test_empty_event_datetime_is_unset(self):
        self.assertIsNone(parse_event_datetime(""))
        self.assertIsNone(parse_event_datetime("   "))

    def test_load_event_datetime_from_events_csv(self):
        with tempfile.TemporaryDirectory() as directory:
            csv_path = Path(directory) / "events.csv"
            with csv_path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(
                    handle, fieldnames=["イベントID", "イベント日時"]
                )
                writer.writeheader()
                writer.writerow(
                    {"イベントID": "E006", "イベント日時": "1999-06-01 夜"}
                )

            self.assertEqual(
                load_event_datetime("E006", str(csv_path)),
                EventDateTime(1999, 6, 1, "夜"),
            )
            self.assertIsNone(load_event_datetime("E007", str(csv_path)))

    def test_apply_event_datetime_sets_renderer(self):
        expected = EventDateTime(1999, 6, 2, "朝")

        class Renderer:
            event_datetime = None

            def set_event_datetime(self, value):
                self.event_datetime = value

        renderer = Renderer()
        with patch(
            "dialogue.event_datetime.load_event_datetime",
            return_value=expected,
        ) as loader:
            result = apply_event_datetime(
                renderer, ks_file_path="events/E007.ks"
            )

        loader.assert_called_once_with("E007")
        self.assertEqual(result, expected)
        self.assertEqual(renderer.event_datetime, expected)

    def test_event_datetime_uses_existing_display_format(self):
        display = format_game_datetime(1999, 6, 1, 1, "夜")

        self.assertEqual(display, "平成１１年（１９９９年）６月１日（火）夜")

    def test_renderer_uses_event_datetime_for_date_and_weather(self):
        from dialogue.text_renderer import TextRenderer

        class Screen:
            def __init__(self):
                self.blits = []

            def blit(self, surface, position):
                self.blits.append((surface, position))

        class Weather:
            def __init__(self):
                self.args = None

            def get_display_text(self, *args):
                self.args = args
                return "晴 20.0℃"

        renderer = TextRenderer.__new__(TextRenderer)
        renderer.date_display_enabled = True
        renderer.event_datetime = EventDateTime(1999, 6, 1, "夜")
        renderer.date_font = object()
        renderer.date_color = (255, 255, 255)
        renderer.date_position = (22, 30)
        renderer.weather_font = object()
        renderer.weather_color = (255, 255, 255)
        renderer.weather_position = (22, 100)
        renderer.historical_weather = Weather()
        renderer.screen = Screen()
        renderer.debug = False

        with patch(
            "dialogue.text_renderer.render_text_with_effects",
            side_effect=lambda font, text, color: text,
        ):
            renderer.render_date()

        self.assertEqual(
            renderer.historical_weather.args,
            (1999, 6, 1, "夜"),
        )
        self.assertEqual(
            renderer.screen.blits[0][0],
            "平成１１年（１９９９年）６月１日（火）夜",
        )
        self.assertEqual(renderer.screen.blits[1][0], "晴 20.0℃")


if __name__ == "__main__":
    unittest.main()
