"""Persistent seed knowledge, journal updates, and turning-point results."""

from __future__ import annotations

import json
import os
import re
import tempfile
import unicodedata
from copy import deepcopy
from typing import Any

from core.path_utils import get_project_root


EMPTY_SEED_STATE = {
    "schema_version": 1,
    "acquired": {},
    "journal_days": [],
    "turning_point_results": {},
}


class SeedCatalogError(ValueError):
    """Raised when authored seed data is inconsistent."""


class SeedManager:
    """Own seed definitions and the current player's acquired state."""

    def __init__(self, project_root: str | None = None):
        self.project_root = project_root or get_project_root()
        self.catalog_path = os.path.join(self.project_root, "data", "seed_catalog.json")
        self.turning_points_path = os.path.join(
            self.project_root, "data", "turning_points.json"
        )
        self.state_path = os.path.join(
            self.project_root, "data", "current_state", "seed_state.json"
        )
        self.catalog = self._load_json(
            self.catalog_path, {"schema_version": 1, "seeds": []}
        )
        turning_data = self._load_json(
            self.turning_points_path,
            {"schema_version": 1, "turning_points": []},
        )
        self.seeds = {
            item["id"]: item for item in self.catalog.get("seeds", []) if item.get("id")
        }
        self.turning_points = {
            item["id"]: item
            for item in turning_data.get("turning_points", [])
            if item.get("id")
        }
        self._validate_catalog()
        self.state = self._load_state()
        self._pending_by_event: dict[str, set[str]] = {}
        self._answer_judge = None

    @staticmethod
    def _load_json(path: str, fallback: dict[str, Any]) -> dict[str, Any]:
        if not os.path.exists(path):
            return deepcopy(fallback)
        with open(path, "r", encoding="utf-8") as handle:
            value = json.load(handle)
        return value if isinstance(value, dict) else deepcopy(fallback)

    def _load_state(self) -> dict[str, Any]:
        state = self._load_json(self.state_path, EMPTY_SEED_STATE)
        state.setdefault("schema_version", 1)
        state.setdefault("acquired", {})
        state.setdefault("journal_days", [])
        state.setdefault("turning_point_results", {})
        return state

    def _validate_catalog(self) -> None:
        authored = self.catalog.get("seeds", [])
        ids = [item.get("id") for item in authored]
        if len(ids) != len(set(ids)):
            raise SeedCatalogError("タネIDが重複しています")

        locations: set[tuple[str, int, int]] = set()
        for seed_id, seed in self.seeds.items():
            turning_point_id = seed.get("turning_point_id")
            if turning_point_id not in self.turning_points:
                raise SeedCatalogError(
                    f"{seed_id}: turning point {turning_point_id!r} が存在しません"
                )
            for parent_id in seed.get("parents", []):
                if parent_id not in self.seeds:
                    raise SeedCatalogError(f"{seed_id}: 親タネ {parent_id!r} が存在しません")
                if parent_id == seed_id:
                    raise SeedCatalogError(f"{seed_id}: 自分自身を親にはできません")
            location = seed.get("journal_location") or {}
            if "page" in location and "slot" in location:
                key = (
                    str(turning_point_id),
                    int(location["page"]),
                    int(location["slot"]),
                )
                if key in locations:
                    raise SeedCatalogError(f"日記位置が重複しています: {key}")
                locations.add(key)

        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(seed_id: str) -> None:
            if seed_id in visiting:
                raise SeedCatalogError(f"タネの親子関係が循環しています: {seed_id}")
            if seed_id in visited:
                return
            visiting.add(seed_id)
            for parent_id in self.seeds[seed_id].get("parents", []):
                visit(parent_id)
            visiting.remove(seed_id)
            visited.add(seed_id)

        for seed_id in self.seeds:
            visit(seed_id)

    def save(self) -> None:
        os.makedirs(os.path.dirname(self.state_path), exist_ok=True)
        fd, temporary_path = tempfile.mkstemp(
            prefix="seed_state_",
            suffix=".json",
            dir=os.path.dirname(self.state_path),
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(self.state, handle, ensure_ascii=False, indent=2)
                handle.write("\n")
            os.replace(temporary_path, self.state_path)
        finally:
            if os.path.exists(temporary_path):
                os.unlink(temporary_path)

    def begin_event(self, event_id: str | None) -> None:
        if event_id:
            self._pending_by_event[event_id] = set()

    def parents_met(self, seed_id: str) -> bool:
        seed = self.seeds.get(seed_id)
        if not seed:
            return False
        parents = seed.get("parents", [])
        if not parents:
            return True
        acquired = self.state["acquired"]
        checks = [parent_id in acquired for parent_id in parents]
        return any(checks) if seed.get("parent_mode") == "any" else all(checks)

    def can_show(self, seed_id: str) -> bool:
        return seed_id in self.state["acquired"] or self.parents_met(seed_id)

    def encounter(self, event_id: str | None, seed_id: str) -> bool:
        if not event_id or not self.can_show(seed_id):
            return False
        self._pending_by_event.setdefault(event_id, set()).add(seed_id)
        return True

    def complete_event(self, event_id: str | None, game_date: str) -> list[str]:
        if not event_id:
            return []
        pending = self._pending_by_event.pop(event_id, set())
        newly_acquired: list[str] = []
        acquired = self.state["acquired"]
        for seed_id in sorted(pending, key=self._seed_sort_key):
            if seed_id in acquired or not self.can_show(seed_id):
                continue
            acquired[seed_id] = {
                "source_event_id": event_id,
                "acquired_game_date": game_date,
                "journaled_game_date": None,
            }
            newly_acquired.append(seed_id)
        if newly_acquired:
            self.save()
        return newly_acquired

    def finalize_day(self, game_date: str) -> list[str]:
        acquired = self.state["acquired"]
        new_ids = [
            seed_id
            for seed_id, record in acquired.items()
            if not record.get("journaled_game_date")
        ]
        new_ids.sort(key=self._seed_sort_key)
        if not new_ids:
            return []

        journal_days = self.state["journal_days"]
        day = next(
            (item for item in journal_days if item.get("game_date") == game_date), None
        )
        if day is None:
            day = {"game_date": game_date, "seed_ids": []}
            journal_days.append(day)
        for seed_id in new_ids:
            if seed_id not in day["seed_ids"]:
                day["seed_ids"].append(seed_id)
            acquired[seed_id]["journaled_game_date"] = game_date
        self.save()
        return new_ids

    def journal_entries(
        self, turning_point_id: str | None = None
    ) -> list[dict[str, Any]]:
        result = []
        for seed_id, seed in self.seeds.items():
            if seed_id not in self.state["acquired"]:
                continue
            if turning_point_id and seed.get("turning_point_id") != turning_point_id:
                continue
            item = deepcopy(seed)
            item["state"] = deepcopy(self.state["acquired"][seed_id])
            result.append(item)
        result.sort(key=lambda item: self._seed_sort_key(item["id"]))
        return result

    def annotation_lines(self, seed_id: str) -> list[dict[str, str]]:
        seed = self.seeds.get(seed_id) or {}
        return [
            {"speaker": str(item.get("speaker", "")), "text": str(item.get("text", ""))}
            for item in seed.get("annotation", [])
            if item.get("text")
        ]

    def judge_answer(self, turning_point_id: str, answer_text: str) -> dict[str, Any]:
        definition = self.turning_points.get(turning_point_id)
        if not definition:
            return {"result": "error", "judge_version": "seed-rule-v1"}
        semantic_config = definition.get("semantic_judge") or {}
        if semantic_config.get("enabled", False):
            if self._answer_judge is None:
                from .semantic_answer_judge import SemanticAnswerJudge

                self._answer_judge = SemanticAnswerJudge(self.project_root)
            return self._answer_judge.judge(definition, answer_text)

        normalized = self._normalize_answer(answer_text)
        accepted = {
            self._normalize_answer(candidate)
            for candidate in definition.get("accepted_answers", [])
        }
        result = "correct" if normalized and normalized in accepted else "incorrect"
        return {
            "result": result,
            "confidence": 1.0 if result == "correct" else 0.0,
            "judge_version": "seed-rule-v1",
        }

    def record_turning_point_result(
        self,
        turning_point_id: str,
        answer_text: str,
        verdict: dict[str, Any],
        game_date: str,
    ) -> None:
        previous = self.state["turning_point_results"].get(turning_point_id, {})
        self.state["turning_point_results"][turning_point_id] = {
            "result": verdict.get("result", "error"),
            "attempt_count": int(previous.get("attempt_count", 0)) + 1,
            "resolved_game_date": game_date,
            "answer_text": answer_text,
            "judge_version": verdict.get("judge_version", "unknown"),
        }
        self.save()

    def _seed_sort_key(self, seed_id: str) -> tuple[str, int, int, str]:
        seed = self.seeds.get(seed_id) or {}
        location = seed.get("journal_location") or {}
        return (
            str(seed.get("turning_point_id", "")),
            int(location.get("page", 9999)),
            int(location.get("slot", 9999)),
            seed_id,
        )

    @staticmethod
    def _normalize_answer(text: str) -> str:
        normalized = unicodedata.normalize("NFKC", str(text)).lower()
        return re.sub(r"[\s、。,.!！?？・「」『』()（）]+", "", normalized)


_seed_manager: SeedManager | None = None


def get_seed_manager() -> SeedManager:
    global _seed_manager
    if _seed_manager is None:
        _seed_manager = SeedManager()
    return _seed_manager


def reload_seed_manager() -> SeedManager:
    global _seed_manager
    _seed_manager = SeedManager()
    return _seed_manager
