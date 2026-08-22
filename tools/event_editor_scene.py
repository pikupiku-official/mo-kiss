"""Object-based scene preview helpers for ``event_editor``.

The normal step preview is a faithful Pygame screenshot.  This module keeps a
separate, lightweight scene model for editor interaction so backgrounds and
characters remain selectable objects instead of being flattened into one PNG.
"""

from __future__ import annotations

import copy
import os
import re
from collections import OrderedDict

from PyQt5.QtCore import QTimer, Qt, pyqtSignal
from PyQt5.QtGui import QColor, QImage, QPainter, QPen, QPixmap
from PyQt5.QtWidgets import (
    QGraphicsItem,
    QGraphicsPixmapItem,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsSimpleTextItem,
    QGraphicsView,
    QLabel,
    QSizePolicy,
)

from core.config import VIRTUAL_HEIGHT, VIRTUAL_WIDTH


CHARACTER_PARTS = (
    "torso",
    "brow",
    "cheek",
    "eye",
    "mouth",
    "accessory",
    "effect",
)


class FitPixmapLabel(QLabel):
    """A preview label that always refits its source image to the current tab."""

    def __init__(self, text="", parent=None):
        self._source_pixmap = QPixmap()
        super().__init__(text, parent)
        self.setAlignment(Qt.AlignCenter)
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.setMinimumSize(1, 1)

    def setText(self, text):
        self._source_pixmap = QPixmap()
        super().setText(text)

    def set_source_pixmap(self, pixmap):
        if isinstance(pixmap, QImage):
            self._source_pixmap = QPixmap.fromImage(pixmap)
        else:
            self._source_pixmap = QPixmap(pixmap) if pixmap is not None else QPixmap()
        if self._source_pixmap.isNull():
            super().setText("")
            return
        super().setText("")
        self._refit_pixmap()

    def set_image_path(self, image_path):
        self.set_source_pixmap(QPixmap(image_path))

    def _refit_pixmap(self):
        if self._source_pixmap.isNull():
            return
        target_size = self.contentsRect().size()
        if target_size.width() <= 0 or target_size.height() <= 0:
            return
        super().setPixmap(
            self._source_pixmap.scaled(
                target_size,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
        )

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._refit_pixmap()

    def showEvent(self, event):
        super().showEvent(event)
        self._refit_pixmap()


def parse_step_action(text):
    """Parse the editor's one-line action representation.

    The return value intentionally matches ``StepEditorDialog._parse_action``:
    ``(tag, [(key, value), ...])``.  Keeping this helper outside the dialog
    lets the scene model and tests consume the same explicit action target.
    """

    text = (text or "").strip()
    if text.startswith("[") and text.endswith("]"):
        text = text[1:-1].strip()
    if not text:
        return "", []
    parts = text.split(None, 1)
    tag = parts[0].lower()
    params_text = parts[1] if len(parts) > 1 else ""
    params = [
        (match.group(1), match.group(2))
        for match in re.finditer(r'(\w+)\s*=\s*"([^"]*)"', params_text)
    ]
    return tag, params


_QIMAGE_CACHE = OrderedDict()
_QIMAGE_CACHE_LIMIT = 160


def _resolve_asset_path(image_manager, image_type, image_key):
    """Resolve an editor asset with the same legacy matching as the runtime."""

    if not image_manager or not image_key:
        return ""
    paths = image_manager.image_paths.get(image_type, {})
    if image_key in paths:
        return paths[image_key]

    wanted = str(image_key).lower().replace(".webp", "").replace(".png", "")
    for candidate, path in paths.items():
        candidate_lower = candidate.lower()
        if wanted in candidate_lower or candidate_lower in wanted:
            return path

    if image_type == "torso":
        match = re.search(r"_T(\d+)", str(image_key), re.IGNORECASE)
        match = match or re.search(r"T(\d+)", str(image_key), re.IGNORECASE)
        if match:
            token = f"_t{match.group(1)}_"
            for candidate, path in paths.items():
                if token in candidate.lower():
                    return path
    return ""


def _image_cache_key(path):
    """Include cheap file metadata so replaced editor assets invalidate safely."""

    try:
        stat = os.stat(path)
    except OSError:
        return (path, None, None)
    return (path, stat.st_mtime_ns, stat.st_size)


def load_qimage(path):
    """Load an editor asset, with a Pygame fallback for Qt5 WebP gaps."""

    if not path or not os.path.exists(path):
        return QImage()
    cache_key = _image_cache_key(path)
    cached = _QIMAGE_CACHE.get(cache_key)
    if cached is not None:
        _QIMAGE_CACHE.move_to_end(cache_key)
        return cached

    image = QImage(path)
    if not image.isNull():
        image = image.convertToFormat(QImage.Format_ARGB32)
        _QIMAGE_CACHE[cache_key] = image
        _QIMAGE_CACHE.move_to_end(cache_key)
        while len(_QIMAGE_CACHE) > _QIMAGE_CACHE_LIMIT:
            _QIMAGE_CACHE.popitem(last=False)
        return image

    try:
        import pygame

        surface = pygame.image.load(path)
        try:
            rgba_data = pygame.image.tobytes(surface, "RGBA")
        except AttributeError:
            rgba_data = pygame.image.tostring(surface, "RGBA")
        width, height = surface.get_size()
        image = QImage(
            rgba_data, width, height, QImage.Format_RGBA8888
        ).copy()
        _QIMAGE_CACHE[cache_key] = image
        _QIMAGE_CACHE.move_to_end(cache_key)
        while len(_QIMAGE_CACHE) > _QIMAGE_CACHE_LIMIT:
            _QIMAGE_CACHE.popitem(last=False)
        return image
    except Exception:
        return QImage()


def _to_float(value, default):
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


class StepSceneStateBuilder:
    """Replay spatial KS actions into serializable before/after scene states."""

    def __init__(self, image_manager=None, image_size_lookup=None):
        self.image_manager = image_manager
        self._image_size_lookup = image_size_lookup
        self._size_cache = {}
        self._build_cache = OrderedDict()
        self._build_cache_limit = 96
        self._timeline_signature = ()
        self._timeline_states = []

    def _asset_path(self, image_type, image_key):
        return _resolve_asset_path(self.image_manager, image_type, image_key)

    def _image_size(self, image_type, image_key):
        cache_key = (image_type, image_key)
        if cache_key in self._size_cache:
            return self._size_cache[cache_key]

        size = None
        if self._image_size_lookup:
            size = self._image_size_lookup(image_type, image_key)
        else:
            image = load_qimage(self._asset_path(image_type, image_key))
            if not image.isNull():
                size = (image.width(), image.height())
        if not size or size[0] <= 0 or size[1] <= 0:
            # A visible placeholder also gives legacy/incomplete tags a stable
            # location in the editor without claiming that an asset was found.
            size = (720, VIRTUAL_HEIGHT)
        self._size_cache[cache_key] = size
        return size

    @staticmethod
    def _empty_state():
        return {
            "background": None,
            "characters": {},
        }

    def _display_size(self, character, torso=None, zoom=None):
        torso = torso if torso is not None else character.get("torso", "")
        zoom = zoom if zoom is not None else character.get("zoom", 1.0)
        width, height = self._image_size("torso", torso)
        base_scale = VIRTUAL_HEIGHT / max(height, 1)
        return width * base_scale * zoom, height * base_scale * zoom

    def _set_character_placement(self, character, center_x, center_y, zoom):
        character["zoom"] = zoom
        display_width, display_height = self._display_size(character, zoom=zoom)
        character["left"] = VIRTUAL_WIDTH * center_x - display_width / 2
        character["top"] = VIRTUAL_HEIGHT * center_y - display_height / 2
        character["x"] = center_x
        character["y"] = center_y

    def _update_character_center(self, character):
        display_width, display_height = self._display_size(character)
        character["x"] = (
            character.get("left", 0.0) + display_width / 2
        ) / VIRTUAL_WIDTH
        character["y"] = (
            character.get("top", 0.0) + display_height / 2
        ) / VIRTUAL_HEIGHT

    @staticmethod
    def _background_limits(zoom):
        if zoom >= 1.0:
            return (
                VIRTUAL_WIDTH * (zoom - 1.0) / 2,
                VIRTUAL_HEIGHT * (zoom - 1.0) / 2,
            )
        return (
            VIRTUAL_WIDTH * (1.0 - zoom) / 4,
            VIRTUAL_HEIGHT * (1.0 - zoom) / 4,
        )

    def _show_background(self, params):
        zoom = max(0.5, min(3.0, _to_float(params.get("bg_zoom"), 1.0)))
        center_x = max(0.0, min(1.0, _to_float(params.get("bg_x"), 0.5)))
        center_y = max(0.0, min(1.0, _to_float(params.get("bg_y"), 0.5)))
        limit_x, limit_y = self._background_limits(zoom)
        return {
            "storage": params.get("storage", ""),
            "x": center_x,
            "y": center_y,
            "zoom": zoom,
            "offset_x": (center_x - 0.5) * limit_x * 2,
            "offset_y": (center_y - 0.5) * limit_y * 2,
        }

    def _move_background(self, background, params):
        if not background:
            return background
        next_background = dict(background)
        zoom = max(0.5, min(3.0, _to_float(params.get("bg_zoom"), 1.0)))
        relative_x = max(-0.3, min(0.3, _to_float(params.get("bg_left"), 0.0)))
        relative_y = max(-0.3, min(0.3, _to_float(params.get("bg_top"), 0.0)))
        limit_x, limit_y = self._background_limits(zoom)
        target_x = next_background.get("offset_x", 0.0) + relative_x * limit_x * 2
        target_y = next_background.get("offset_y", 0.0) + relative_y * limit_y * 2
        next_background["offset_x"] = max(-limit_x, min(limit_x, target_x))
        next_background["offset_y"] = max(-limit_y, min(limit_y, target_y))
        next_background["zoom"] = zoom
        return next_background

    def _apply_action(self, state, tag, params, changes=None):
        changes = changes if changes is not None else {}

        if tag == "bg":
            background_params = {
                "storage": params.get("storage", ""),
                "bg_x": 0.5,
                "bg_y": 0.5,
                "bg_zoom": 1.0,
            }
            state["background"] = self._show_background(background_params)
            changes["background"] = "show"
            return

        if tag == "bg_show":
            state["background"] = self._show_background(params)
            changes["background"] = "show"
            return

        if tag == "bg_move":
            state["background"] = self._move_background(
                state.get("background"), params
            )
            changes["background"] = "move"
            return

        if tag not in ("chara_show", "chara_shift", "chara_move", "chara_hide"):
            return

        name = (params.get("name") or "").strip()
        if not name:
            return

        characters = state["characters"]
        if tag == "chara_hide":
            characters.pop(name, None)
            changes[name] = "hide"
            return

        if tag == "chara_show":
            character = {
                "name": name,
                **{part: params.get(part, "") for part in CHARACTER_PARTS},
                "blink": params.get("blink", "true"),
            }
            character["torso"] = character.get("torso") or name
            self._set_character_placement(
                character,
                _to_float(params.get("x"), 0.5),
                _to_float(params.get("y"), 0.5),
                _to_float(params.get("size"), 1.0),
            )
            characters[name] = character
            changes[name] = "show"
            return

        character = characters.get(name)
        if character is None:
            character = {
                "name": name,
                **{part: "" for part in CHARACTER_PARTS},
                "torso": name,
                "blink": "true",
            }
            self._set_character_placement(character, 0.5, 0.5, 1.0)
            characters[name] = character

        if tag == "chara_move":
            character["left"] += _to_float(params.get("left"), 0.0) * VIRTUAL_WIDTH
            character["top"] += _to_float(params.get("top"), 0.0) * VIRTUAL_HEIGHT
            character["zoom"] = _to_float(params.get("zoom"), 1.0)
            self._update_character_center(character)
            changes[name] = "move"
            return

        # chara_shift keeps unspecified parts.  Position is only recomputed
        # when x/y/size is explicitly present, matching the runtime handler.
        old_display_width, old_display_height = self._display_size(character)
        current_center_x = (
            character.get("left", 0.0) + old_display_width / 2
        ) / VIRTUAL_WIDTH
        current_center_y = (
            character.get("top", 0.0) + old_display_height / 2
        ) / VIRTUAL_HEIGHT

        for part in CHARACTER_PARTS:
            if part in params:
                character[part] = params.get(part, "")
        if "blink" in params:
            character["blink"] = params.get("blink", "true")

        if any(key in params for key in ("x", "y", "size")):
            self._set_character_placement(
                character,
                _to_float(params.get("x"), current_center_x),
                _to_float(params.get("y"), current_center_y),
                _to_float(params.get("size"), character.get("zoom", 1.0)),
            )
        else:
            self._update_character_center(character)
        changes[name] = "shift"

    def build(self, action_steps, step_index):
        """Return ``before`` and ``after`` states for a visible editor step."""

        action_steps = list(action_steps or [])
        target = max(0, min(int(step_index or 0), max(len(action_steps) - 1, 0)))
        timeline_signature = tuple(tuple(actions or ()) for actions in action_steps)
        cache_key = (
            target,
            timeline_signature,
        )
        cached = self._build_cache.get(cache_key)
        if cached is not None:
            self._build_cache.move_to_end(cache_key)
            return cached

        # Preserve every unchanged prefix state.  Paging from N to N+1 then
        # applies only one step instead of reparsing and replaying steps 0..N.
        if timeline_signature != self._timeline_signature:
            common_prefix = 0
            for old_actions, new_actions in zip(
                self._timeline_signature, timeline_signature
            ):
                if old_actions != new_actions:
                    break
                common_prefix += 1
            self._timeline_states = self._timeline_states[:common_prefix]
            self._timeline_signature = timeline_signature

        while len(self._timeline_states) < target:
            prefix_index = len(self._timeline_states)
            state = (
                copy.deepcopy(self._timeline_states[-1])
                if self._timeline_states
                else self._empty_state()
            )
            for action in timeline_signature[prefix_index]:
                tag, pairs = parse_step_action(action)
                self._apply_action(state, tag, dict(pairs))
            self._timeline_states.append(copy.deepcopy(state))

        before = (
            copy.deepcopy(self._timeline_states[target - 1])
            if target > 0 and target - 1 < len(self._timeline_states)
            else self._empty_state()
        )
        state = copy.deepcopy(before)
        changes = {}
        current_actions = timeline_signature[target] if target < len(timeline_signature) else ()
        for action in current_actions or []:
            tag, pairs = parse_step_action(action)
            self._apply_action(state, tag, dict(pairs), changes=changes)

        if target < len(timeline_signature):
            if len(self._timeline_states) == target:
                self._timeline_states.append(copy.deepcopy(state))
            elif target < len(self._timeline_states):
                self._timeline_states[target] = copy.deepcopy(state)

        inherited_names = set(before["characters"])
        for name, character in state["characters"].items():
            change = changes.get(name)
            if change == "show" or name not in inherited_names:
                character["origin"] = "current"
            elif change:
                character["origin"] = "modified"
            else:
                character["origin"] = "inherited"

        background = state.get("background")
        if background:
            if changes.get("background"):
                background["origin"] = "current" if not before.get("background") else "modified"
            else:
                background["origin"] = "inherited"

        result = {
            "step_index": target,
            "before": before,
            "after": copy.deepcopy(state),
            "changes": changes,
        }
        self._build_cache[cache_key] = result
        self._build_cache.move_to_end(cache_key)
        while len(self._build_cache) > self._build_cache_limit:
            self._build_cache.popitem(last=False)
        return result


class StepSceneCanvas(QGraphicsView):
    """4:3 object scene used by the step editor's interactive preview tab."""

    object_selected = pyqtSignal(str, str, str)
    object_moved = pyqtSignal(str, float, float, object)
    object_scaled = pyqtSignal(str, float, object)
    context_requested = pyqtSignal(str, str, str, object, object)
    step_navigation_requested = pyqtSignal(int)

    def __init__(self, image_manager=None, parent=None):
        super().__init__(parent)
        self._image_manager = image_manager
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self.setSceneRect(0, 0, VIRTUAL_WIDTH, VIRTUAL_HEIGHT)
        self.setMinimumSize(400, 300)
        self.setBackgroundBrush(QColor(18, 18, 18))
        self.setFrameShape(QGraphicsView.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        self._scene.selectionChanged.connect(self._on_selection_changed)
        self._selected_key = None
        self._drag_item = None
        self._drag_start_pos = None
        self._drag_press_scene_pos = None
        self._drag_axis_lock = None
        self._resize_handles = []
        self._resize_item = None
        self._resize_start_zoom = None
        self._resize_start_item_scale = None
        self._resize_start_center = None
        self._resize_start_distance = None
        self._resize_current_zoom = None
        self._labels_by_key = {}
        self._character_pixmap_cache = OrderedDict()
        self._character_pixmap_cache_limit = 48
        self._background_pixmap_cache = OrderedDict()
        self._background_pixmap_cache_limit = 24
        self._pending_scale = None
        self._scale_commit_timer = QTimer(self)
        self._scale_commit_timer.setSingleShot(True)
        self._scale_commit_timer.setInterval(120)
        self._scale_commit_timer.timeout.connect(self.flush_pending_scale)

    def _asset_path(self, image_type, image_key):
        return _resolve_asset_path(self._image_manager, image_type, image_key)

    @staticmethod
    def _tag_item(item, object_type, object_name, origin, metadata=None):
        item.setData(0, object_type)
        item.setData(1, object_name)
        item.setData(2, origin)
        item.setData(3, metadata or {})
        item.setFlag(QGraphicsItem.ItemIsSelectable, True)
        item.setToolTip(f"{object_type}: {object_name}")

    def _compose_character(self, character):
        cache_key = tuple(
            (
                part,
                (character.get(part) or "").strip(),
                _image_cache_key(
                    self._asset_path(part, (character.get(part) or "").strip())
                ),
            )
            for part in CHARACTER_PARTS
        )
        cached = self._character_pixmap_cache.get(cache_key)
        if cached is not None:
            self._character_pixmap_cache.move_to_end(cache_key)
            return cached

        result = None
        for part in CHARACTER_PARTS:
            file_id = (character.get(part) or "").strip()
            if not file_id:
                continue
            image = load_qimage(self._asset_path(part, file_id))
            if image.isNull():
                continue
            if result is None:
                result = QImage(image.size(), QImage.Format_ARGB32)
                result.fill(0)
            painter = QPainter(result)
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
            painter.drawImage(0, 0, image)
            painter.end()
        pixmap = QPixmap.fromImage(result) if result is not None else QPixmap()
        self._character_pixmap_cache[cache_key] = pixmap
        self._character_pixmap_cache.move_to_end(cache_key)
        while len(self._character_pixmap_cache) > self._character_pixmap_cache_limit:
            self._character_pixmap_cache.popitem(last=False)
        return pixmap

    def _add_background(self, background):
        storage = (background.get("storage") or "").strip()
        path = self._asset_path("bg", storage)
        cache_key = (storage, _image_cache_key(path))
        pixmap = self._background_pixmap_cache.get(cache_key)
        if pixmap is None:
            image = load_qimage(path)
            if image.isNull():
                return
            pixmap = QPixmap.fromImage(image).scaled(
                VIRTUAL_WIDTH,
                VIRTUAL_HEIGHT,
                Qt.IgnoreAspectRatio,
                Qt.SmoothTransformation,
            )
            self._background_pixmap_cache[cache_key] = pixmap
            self._background_pixmap_cache.move_to_end(cache_key)
            while len(self._background_pixmap_cache) > self._background_pixmap_cache_limit:
                self._background_pixmap_cache.popitem(last=False)
        else:
            self._background_pixmap_cache.move_to_end(cache_key)
        item = QGraphicsPixmapItem(pixmap)
        zoom = background.get("zoom", 1.0)
        item.setScale(zoom)
        item.setPos(
            VIRTUAL_WIDTH / 2 - VIRTUAL_WIDTH * zoom / 2 + background.get("offset_x", 0.0),
            VIRTUAL_HEIGHT / 2 - VIRTUAL_HEIGHT * zoom / 2 + background.get("offset_y", 0.0),
        )
        item.setZValue(0)
        self._tag_item(
            item,
            "background",
            storage,
            background.get("origin", "inherited"),
            background,
        )
        self._scene.addItem(item)

    def _add_character(self, character, z_value):
        name = character.get("name", "")
        origin = character.get("origin", "inherited")
        pixmap = self._compose_character(character)
        if not pixmap.isNull():
            item = QGraphicsPixmapItem(pixmap)
            scale = VIRTUAL_HEIGHT / max(pixmap.height(), 1) * character.get("zoom", 1.0)
            item.setScale(scale)
        else:
            item = QGraphicsRectItem(0, 0, 720, VIRTUAL_HEIGHT)
            item.setBrush(QColor(80, 80, 90, 120))
            item.setPen(QPen(QColor(220, 180, 80), 4, Qt.DashLine))
        item.setPos(character.get("left", 0.0), character.get("top", 0.0))
        item.setZValue(z_value)
        self._tag_item(item, "character", name, origin, character)
        item.setFlag(QGraphicsItem.ItemIsMovable, True)
        self._scene.addItem(item)

        # Labels stay at screen scale instead of inheriting the large source
        # image scale used by character sprites.
        origin_label = {
            "current": "このstepで表示",
            "modified": "このstepで変更",
            "inherited": "引き継ぎ",
        }.get(origin, origin)
        label = QGraphicsSimpleTextItem(f"{name}  [{origin_label}]")
        label.setBrush(QColor(255, 255, 255))
        label.setFlag(QGraphicsItem.ItemIgnoresTransformations, True)
        label.setAcceptedMouseButtons(Qt.NoButton)
        label.setPos(character.get("left", 0.0) + 8, max(0, character.get("top", 0.0) + 8))
        label.setZValue(100 + z_value)
        self._scene.addItem(label)
        self._labels_by_key[("character", name)] = label

    def set_scene_state(self, state):
        selected_key = self._selected_key
        self._scene.clear()
        self._labels_by_key = {}
        self._drag_item = None
        self._drag_start_pos = None
        self._drag_press_scene_pos = None
        self._drag_axis_lock = None
        self._resize_handles = []
        self._resize_item = None
        self._scene.setSceneRect(0, 0, VIRTUAL_WIDTH, VIRTUAL_HEIGHT)
        border = self._scene.addRect(
            0,
            0,
            VIRTUAL_WIDTH,
            VIRTUAL_HEIGHT,
            QPen(QColor(90, 90, 90), 2),
            QColor(0, 0, 0),
        )
        border.setZValue(-100)

        state = state or {}
        background = state.get("background")
        if background:
            self._add_background(background)

        for index, character in enumerate(state.get("characters", {}).values()):
            self._add_character(character, 10 + index)

        if not background and not state.get("characters"):
            empty = self._scene.addText("このstepまでに表示されるオブジェクトはありません")
            empty.setDefaultTextColor(QColor(170, 170, 170))
            empty.setPos(VIRTUAL_WIDTH / 2 - 250, VIRTUAL_HEIGHT / 2 - 20)

        if selected_key:
            for item in self._scene.items():
                if (item.data(0), item.data(1)) == selected_key:
                    item.setSelected(True)
                    break
        self.fit_stage()

    def _clear_resize_handles(self):
        for handle in self._resize_handles:
            if handle.scene() is self._scene:
                self._scene.removeItem(handle)
        self._resize_handles = []

    def _update_resize_handles(self):
        self._clear_resize_handles()
        selected = next(
            (
                item
                for item in self._scene.selectedItems()
                if item.data(0) == "character"
            ),
            None,
        )
        if selected is None:
            return
        rect = selected.sceneBoundingRect()
        corners = {
            "top_left": rect.topLeft(),
            "top_right": rect.topRight(),
            "bottom_left": rect.bottomLeft(),
            "bottom_right": rect.bottomRight(),
        }
        for corner, position in corners.items():
            handle = QGraphicsRectItem(-7, -7, 14, 14)
            handle.setBrush(QColor(255, 255, 255))
            handle.setPen(QPen(QColor(10, 36, 106), 2))
            handle.setFlag(QGraphicsItem.ItemIgnoresTransformations, True)
            handle.setData(0, "resize_handle")
            handle.setData(1, str(selected.data(1) or ""))
            handle.setData(4, corner)
            handle.setPos(position)
            handle.setZValue(250)
            self._scene.addItem(handle)
            self._resize_handles.append(handle)

    def _resize_handle_at(self, viewport_pos):
        return next(
            (item for item in self.items(viewport_pos) if item.data(0) == "resize_handle"),
            None,
        )

    def _character_item_by_name(self, name):
        return next(
            (
                item
                for item in self._scene.items()
                if item.data(0) == "character" and str(item.data(1) or "") == name
            ),
            None,
        )

    def fit_stage(self):
        self.fitInView(self.sceneRect(), Qt.KeepAspectRatio)

    def flush_pending_scale(self):
        """Commit only the last value from a burst of wheel input."""
        self._scale_commit_timer.stop()
        pending = self._pending_scale
        self._pending_scale = None
        if pending is not None:
            self.object_scaled.emit(*pending)

    def discard_pending_scale(self):
        self._scale_commit_timer.stop()
        self._pending_scale = None

    def mark_character_modified(self, name):
        """Update origin metadata without rebuilding all character layers."""
        for item in self._scene.items():
            if item.data(0) != "character" or item.data(1) != name:
                continue
            item.setData(2, "modified")
            metadata = dict(item.data(3) or {})
            metadata["origin"] = "modified"
            item.setData(3, metadata)
            label = self._labels_by_key.get(("character", name))
            if label is not None:
                label.setText(f"{name}  [このstepで変更]")
            return

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.fit_stage()

    def wheelEvent(self, event):
        if event.modifiers() & Qt.ShiftModifier:
            item = self._character_item_at(event.pos())
            if item is None:
                item = next(
                    (
                        selected
                        for selected in self._scene.selectedItems()
                        if selected.data(0) == "character"
                    ),
                    None,
                )
            if item is not None and event.angleDelta().y():
                metadata = dict(item.data(3) or {})
                current_zoom = float(metadata.get("zoom", 1.0))
                wheel_steps = event.angleDelta().y() / 120.0
                new_zoom = max(0.1, min(5.0, current_zoom * (1.08 ** wheel_steps)))
                if current_zoom > 0:
                    item.setScale(item.scale() * new_zoom / current_zoom)
                metadata["zoom"] = new_zoom
                item.setData(3, metadata)
                self._update_resize_handles()
                self._pending_scale = (
                    str(item.data(1) or ""),
                    float(new_zoom),
                    metadata,
                )
                self._scale_commit_timer.start()
                event.accept()
                return
        super().wheelEvent(event)

    def keyPressEvent(self, event):
        """Nudge a selected character, or page steps when the stage is empty."""

        key = event.key()
        modifiers = event.modifiers()
        allowed_modifiers = Qt.ShiftModifier | Qt.KeypadModifier
        if key not in (Qt.Key_Left, Qt.Key_Right, Qt.Key_Up, Qt.Key_Down):
            super().keyPressEvent(event)
            return
        if modifiers & ~allowed_modifiers:
            super().keyPressEvent(event)
            return

        selected_character = next(
            (
                item
                for item in self._scene.selectedItems()
                if item.data(0) == "character"
            ),
            None,
        )
        if selected_character is not None:
            amount = 10.0 if modifiers & Qt.ShiftModifier else 1.0
            delta_x = -amount if key == Qt.Key_Left else amount if key == Qt.Key_Right else 0.0
            delta_y = -amount if key == Qt.Key_Up else amount if key == Qt.Key_Down else 0.0
            selected_character.moveBy(delta_x, delta_y)
            key_tuple = ("character", str(selected_character.data(1) or ""))
            label = self._labels_by_key.get(key_tuple)
            if label is not None:
                label.setPos(
                    selected_character.pos().x() + 8,
                    max(0, selected_character.pos().y() + 8),
                )
            self.object_moved.emit(
                key_tuple[1],
                delta_x,
                delta_y,
                dict(selected_character.data(3) or {}),
            )
            event.accept()
            return

        if not self._scene.selectedItems() and key in (Qt.Key_Left, Qt.Key_Right):
            self.step_navigation_requested.emit(-1 if key == Qt.Key_Left else 1)
            event.accept()
            return

        super().keyPressEvent(event)

    def contextMenuEvent(self, event):
        self.flush_pending_scale()
        # Backgrounds normally fill the entire stage, so ordinary right-click
        # treats every non-character point as stage space.  Background editing
        # remains an explicit entry in the stage menu instead of stealing the
        # empty-space menu everywhere.
        item = self._character_item_at(event.pos())
        if item is not None:
            self._scene.clearSelection()
            item.setSelected(True)
            self.context_requested.emit(
                "character",
                str(item.data(1) or ""),
                str(item.data(2) or ""),
                event.globalPos(),
                dict(item.data(3) or {}),
            )
        else:
            self.context_requested.emit("stage", "", "", event.globalPos(), {})
        event.accept()

    def _character_item_at(self, viewport_pos):
        for item in self.items(viewport_pos):
            if item.data(0) == "character":
                return item
        return None

    def _sync_dragged_label(self):
        if self._drag_item is None:
            return
        self._sync_dragged_label_for_item(self._drag_item)

    def _sync_dragged_label_for_item(self, item):
        key = ("character", str(item.data(1) or ""))
        label = self._labels_by_key.get(key)
        if label is not None:
            label.setPos(
                item.pos().x() + 8,
                max(0, item.pos().y() + 8),
            )

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            handle = self._resize_handle_at(event.pos())
            if handle is not None:
                item = self._character_item_by_name(str(handle.data(1) or ""))
                if item is not None:
                    metadata = dict(item.data(3) or {})
                    center = item.sceneBoundingRect().center()
                    press_pos = self.mapToScene(event.pos())
                    distance = ((press_pos.x() - center.x()) ** 2 + (press_pos.y() - center.y()) ** 2) ** 0.5
                    self._resize_item = item
                    self._resize_start_zoom = float(metadata.get("zoom", 1.0))
                    self._resize_start_item_scale = float(item.scale())
                    self._resize_start_center = center
                    self._resize_start_distance = max(distance, 0.001)
                    self._resize_current_zoom = self._resize_start_zoom
                    event.accept()
                    return
            item = self._character_item_at(event.pos())
            if item is not None:
                self._drag_item = item
                self._drag_start_pos = item.pos()
                self._drag_press_scene_pos = self.mapToScene(event.pos())
                self._drag_axis_lock = None
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._resize_item is not None and event.buttons() & Qt.LeftButton:
            scene_pos = self.mapToScene(event.pos())
            center = self._resize_start_center
            distance = ((scene_pos.x() - center.x()) ** 2 + (scene_pos.y() - center.y()) ** 2) ** 0.5
            factor = max(0.01, distance / self._resize_start_distance)
            new_zoom = max(0.1, min(5.0, self._resize_start_zoom * factor))
            self._resize_item.setScale(
                self._resize_start_item_scale * new_zoom / self._resize_start_zoom
            )
            shifted_center = self._resize_item.sceneBoundingRect().center()
            self._resize_item.moveBy(
                center.x() - shifted_center.x(),
                center.y() - shifted_center.y(),
            )
            metadata = dict(self._resize_item.data(3) or {})
            metadata["zoom"] = new_zoom
            self._resize_item.setData(3, metadata)
            self._resize_current_zoom = new_zoom
            self._sync_dragged_label_for_item(self._resize_item)
            self._update_resize_handles()
            event.accept()
            return
        if (
            self._drag_item is not None
            and self._drag_start_pos is not None
            and self._drag_press_scene_pos is not None
            and event.buttons() & Qt.LeftButton
        ):
            scene_delta = self.mapToScene(event.pos()) - self._drag_press_scene_pos
            if event.modifiers() & Qt.ShiftModifier:
                if self._drag_axis_lock is None:
                    if abs(scene_delta.x()) >= abs(scene_delta.y()):
                        self._drag_axis_lock = "x"
                    else:
                        self._drag_axis_lock = "y"
                if self._drag_axis_lock == "x":
                    scene_delta.setY(0.0)
                else:
                    scene_delta.setX(0.0)
            self._drag_item.setPos(self._drag_start_pos + scene_delta)
            self._sync_dragged_label()
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._resize_item is not None and event.button() == Qt.LeftButton:
            item = self._resize_item
            new_zoom = float(self._resize_current_zoom or self._resize_start_zoom or 1.0)
            old_zoom = float(self._resize_start_zoom or new_zoom)
            self._resize_item = None
            self._resize_start_zoom = None
            self._resize_start_item_scale = None
            self._resize_start_center = None
            self._resize_start_distance = None
            self._resize_current_zoom = None
            self._update_resize_handles()
            if abs(new_zoom - old_zoom) >= 0.0001:
                self.object_scaled.emit(
                    str(item.data(1) or ""),
                    new_zoom,
                    dict(item.data(3) or {}),
                )
            event.accept()
            return
        super().mouseReleaseEvent(event)
        item = self._drag_item
        start_pos = self._drag_start_pos
        self._sync_dragged_label()
        self._drag_item = None
        self._drag_start_pos = None
        self._drag_press_scene_pos = None
        self._drag_axis_lock = None
        if item is None or start_pos is None or event.button() != Qt.LeftButton:
            return
        delta = item.pos() - start_pos
        if abs(delta.x()) < 0.01 and abs(delta.y()) < 0.01:
            return
        self.object_moved.emit(
            str(item.data(1) or ""),
            float(delta.x()),
            float(delta.y()),
            dict(item.data(3) or {}),
        )

    def _on_selection_changed(self):
        selected = [item for item in self._scene.selectedItems() if item.data(0)]
        if not selected:
            self._selected_key = None
            self._clear_resize_handles()
            self.object_selected.emit("", "", "")
            return
        item = selected[0]
        object_type = str(item.data(0) or "")
        object_name = str(item.data(1) or "")
        origin = str(item.data(2) or "")
        self._selected_key = (object_type, object_name)
        self._update_resize_handles()
        self.object_selected.emit(object_type, object_name, origin)
