import json

from dialogue.historical_weather import HistoricalWeather


def test_weather_becomes_unknown_from_june_28(tmp_path):
    path = tmp_path / "weather.json"
    path.write_text(
        json.dumps({"1999-06-28": {"weather": "曇", "fuchu_temperature": {"08": "21.4"}}}),
        encoding="utf-8",
    )

    weather = HistoricalWeather(str(path))

    assert weather.get_display_text(1999, 6, 28, "朝") == "？ ？？℃"


def test_weather_is_not_displayed_after_july_2(tmp_path):
    path = tmp_path / "weather.json"
    path.write_text(
        json.dumps(
            {
                "1999-07-02": {"weather": "薄曇", "fuchu_temperature": {"08": "24.5"}},
                "1999-07-03": {"weather": "曇", "fuchu_temperature": {"08": "23.0"}},
            }
        ),
        encoding="utf-8",
    )

    weather = HistoricalWeather(str(path))

    assert weather.get_display_text(1999, 7, 2, "朝") == "？ ？？℃"
    assert weather.get_display_text(1999, 7, 3, "朝") == ""
