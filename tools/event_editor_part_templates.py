"""Persistent character-part templates used only by the event editor."""

from __future__ import annotations

import json
import os
import uuid


PART_FIELDS = (
    "torso",
    "brow",
    "cheek",
    "eye",
    "mouth",
    "accessory",
    "effect",
)


class CharaPartTemplateStore:
    def __init__(self, path):
        self.path = os.fspath(path)

    def load(self):
        try:
            with open(self.path, "r", encoding="utf-8") as handle:
                raw = json.load(handle)
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return []
        templates = raw.get("templates", []) if isinstance(raw, dict) else []
        return [item for item in templates if isinstance(item, dict)]

    def _write(self, templates):
        directory = os.path.dirname(self.path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        temp_path = self.path + ".tmp"
        with open(temp_path, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(
                {"version": 1, "templates": templates},
                handle,
                ensure_ascii=False,
                indent=2,
            )
            handle.write("\n")
        os.replace(temp_path, self.path)

    def for_character(self, character):
        character = (character or "").strip()
        return [
            item
            for item in self.load()
            if str(item.get("character", "")).strip() == character
        ]

    def find(self, character, name):
        """Return a character template by its display name."""
        name = (name or "").strip()
        if not name:
            return None
        return next(
            (item for item in self.for_character(character)
             if str(item.get("name", "")).strip() == name),
            None,
        )

    def create(self, name, character, parts, blink=True):
        item = {
            "id": uuid.uuid4().hex,
            "name": (name or "").strip(),
            "character": (character or "").strip(),
            "parts": {
                part: str((parts or {}).get(part, "")).strip()
                for part in PART_FIELDS
            },
            "blink": bool(blink),
        }
        if not item["name"] or not item["character"]:
            raise ValueError("テンプレート名とキャラクター名が必要です")
        templates = self.load()
        templates.append(item)
        self._write(templates)
        return item

    def rename(self, template_id, new_name):
        new_name = (new_name or "").strip()
        if not new_name:
            raise ValueError("テンプレート名が必要です")
        templates = self.load()
        for item in templates:
            if item.get("id") == template_id:
                item["name"] = new_name
                self._write(templates)
                return item
        return None

    def duplicate(self, template_id, new_name):
        source = next(
            (item for item in self.load() if item.get("id") == template_id),
            None,
        )
        if source is None:
            return None
        return self.create(
            new_name,
            source.get("character", ""),
            source.get("parts", {}),
            source.get("blink", True),
        )

    def delete(self, template_id):
        templates = self.load()
        remaining = [item for item in templates if item.get("id") != template_id]
        if len(remaining) == len(templates):
            return False
        self._write(remaining)
        return True
