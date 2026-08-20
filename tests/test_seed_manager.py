import json

import pytest

from core.services.seed_manager import SeedCatalogError, SeedManager


def _write_project(tmp_path, seeds, turning_points):
    data = tmp_path / "data"
    current = data / "current_state"
    current.mkdir(parents=True)
    (data / "seed_catalog.json").write_text(
        json.dumps({"schema_version": 1, "seeds": seeds}, ensure_ascii=False),
        encoding="utf-8",
    )
    (data / "turning_points.json").write_text(
        json.dumps(
            {"schema_version": 1, "turning_points": turning_points},
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (current / "seed_state.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "acquired": {},
                "journal_days": [],
                "turning_point_results": {},
            }
        ),
        encoding="utf-8",
    )


def _seed(seed_id, parents=(), slot=1):
    return {
        "id": seed_id,
        "turning_point_id": "TP1",
        "journal_text": seed_id,
        "parents": list(parents),
        "journal_location": {"page": 1, "slot": slot},
    }


def test_seed_tree_is_acquired_only_after_each_event_finishes(tmp_path):
    _write_project(
        tmp_path,
        [_seed("S1"), _seed("S2", ["S1"], 2), _seed("S3", ["S2"], 3)],
        [{"id": "TP1", "accepted_answers": ["答え"]}],
    )
    manager = SeedManager(str(tmp_path))

    manager.begin_event("E1")
    assert manager.encounter("E1", "S1") is True
    assert "S1" not in manager.state["acquired"]
    assert manager.complete_event("E1", "1999-06-01") == ["S1"]

    manager.begin_event("E2")
    assert manager.encounter("E2", "S2") is True
    assert manager.complete_event("E2", "1999-06-01") == ["S2"]
    assert manager.can_show("S3") is True


def test_child_seed_is_not_encountered_before_parent(tmp_path):
    _write_project(
        tmp_path,
        [_seed("S1"), _seed("S2", ["S1"], 2)],
        [{"id": "TP1"}],
    )
    manager = SeedManager(str(tmp_path))
    manager.begin_event("E2")

    assert manager.encounter("E2", "S2") is False
    assert manager.complete_event("E2", "1999-06-01") == []


def test_finalize_day_is_idempotent_and_uses_fixed_order(tmp_path):
    _write_project(
        tmp_path,
        [_seed("S2", slot=2), _seed("S1", slot=1)],
        [{"id": "TP1"}],
    )
    manager = SeedManager(str(tmp_path))
    manager.begin_event("E")
    manager.encounter("E", "S2")
    manager.encounter("E", "S1")
    manager.complete_event("E", "1999-06-01")

    assert manager.finalize_day("1999-06-01") == ["S1", "S2"]
    assert manager.finalize_day("1999-06-01") == []
    assert manager.state["journal_days"] == [
        {"game_date": "1999-06-01", "seed_ids": ["S1", "S2"]}
    ]


def test_tutorial_answer_is_normalized_but_not_guessed(tmp_path):
    _write_project(
        tmp_path,
        [_seed("S1")],
        [{"id": "TP1", "accepted_answers": ["増田は真性包茎である"]}],
    )
    manager = SeedManager(str(tmp_path))

    assert manager.judge_answer("TP1", " 増田は、真性包茎である。 ")["result"] == "correct"
    assert manager.judge_answer("TP1", "増田は包茎ではない")["result"] == "incorrect"


def test_cycle_is_rejected(tmp_path):
    _write_project(
        tmp_path,
        [_seed("S1", ["S2"], 1), _seed("S2", ["S1"], 2)],
        [{"id": "TP1"}],
    )

    with pytest.raises(SeedCatalogError, match="循環"):
        SeedManager(str(tmp_path))
