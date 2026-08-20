from core.services.seed_manager import SeedManager
from test_masuda_seed_free_text import (
    TURNING_POINT_ID,
    assume_all_turning_point_seeds,
)


def test_standalone_prompt_assumes_every_masuda_seed_without_saving(monkeypatch):
    manager = SeedManager()
    monkeypatch.setattr(manager, "save", lambda: (_ for _ in ()).throw(
        AssertionError("standalone setup must not save")
    ))

    acquired_ids = assume_all_turning_point_seeds(manager)
    required_ids = manager.turning_points[TURNING_POINT_ID]["required_seed_ids"]

    assert acquired_ids == required_ids
    assert [
        entry["id"] for entry in manager.journal_entries(TURNING_POINT_ID)
    ] == required_ids
    assert all(
        manager.state["acquired"][seed_id]["journaled_game_date"]
        for seed_id in required_ids
    )
