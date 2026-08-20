from __future__ import annotations

from types import SimpleNamespace

from core.config import scale_pos
from map import map as map_module
from map.map import FieldMap


def test_map_reloads_event_activation_state_every_time_it_is_reentered():
    field_map = FieldMap.__new__(FieldMap)
    refreshed = {
        "TANE_MASUDA_01": {"count": 1, "active": False},
        "TANE_MASUDA_02": {"count": 0, "active": True},
    }
    calls = []
    field_map.completed_events = {
        "TANE_MASUDA_01": {"count": 0, "active": True}
    }
    field_map.load_completed_events = lambda: refreshed
    field_map.update_events = lambda: calls.append("events")
    field_map.update_bgm = lambda: calls.append("bgm")

    field_map.on_enter()

    assert field_map.completed_events is refreshed
    assert calls == ["events", "bgm"]


def test_clicking_map_event_does_not_advance_time_before_dialogue(monkeypatch):
    class TimeManager:
        def __init__(self):
            self.advances = 0

        def get_current_period(self):
            return "朝"

        def advance_period(self):
            self.advances += 1

    time_manager = TimeManager()
    monkeypatch.setattr(map_module, "get_time_manager", lambda: time_manager)

    character = SimpleNamespace(name="増田")
    location = SimpleNamespace(
        name="教室",
        x=300,
        y=495,
        girl_characters=[character],
    )
    event = SimpleNamespace(event_id="TANE_MASUDA_01", title="温泉への誘い")
    field_map = FieldMap.__new__(FieldMap)
    field_map.selected_character = None
    field_map.get_current_locations = lambda: [location]
    field_map.get_current_event_for_character = lambda name, place: event

    click_pos = scale_pos(location.x, location.y - 35)
    result = field_map.handle_click(click_pos)

    assert result == "launch_event:events/TANE_MASUDA_01.ks"
    assert time_manager.advances == 0
