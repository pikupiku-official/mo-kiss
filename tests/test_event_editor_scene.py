import os
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5.QtCore import QEvent, QPoint, QPointF, Qt
from PyQt5.QtGui import QColor, QImage, QKeyEvent, QMouseEvent
from PyQt5.QtWidgets import QApplication, QDialog, QGraphicsItem, QLineEdit, QWidget

from core.config import VIRTUAL_HEIGHT, VIRTUAL_WIDTH
from event_editor import StepEditorDialog
from tools.event_editor_scene import (
    FitPixmapLabel,
    StepSceneCanvas,
    StepSceneStateBuilder,
)


APP = QApplication.instance() or QApplication([])


def _size_lookup(_image_type, image_key):
    return {
        "MMK_T00": (500, 1000),
        "MMK_T01": (600, 1000),
    }.get(image_key, (500, 1000))


def test_scene_builder_distinguishes_before_and_after_objects():
    builder = StepSceneStateBuilder(image_size_lookup=_size_lookup)
    action_steps = [
        [
            'bg_show storage="room" bg_x="0.5" bg_y="0.5" bg_zoom="1.0"',
            'chara_show name="桃子" torso="MMK_T00" eye="eye_a" x="0.25" y="0.5" size="1.0"',
        ],
        [
            'chara_shift name="桃子" torso="MMK_T01" eye="eye_b"',
            'chara_move name="桃子" left="0.1" top="-0.2" zoom="1.5" time="600"',
            'chara_show name="静" torso="MMK_T00" x="0.75" y="0.5" size="1.0"',
        ],
    ]

    states = builder.build(action_steps, 1)

    assert list(states["before"]["characters"]) == ["桃子"]
    assert states["before"]["characters"]["桃子"]["eye"] == "eye_a"
    assert states["after"]["characters"]["桃子"]["eye"] == "eye_b"
    assert states["after"]["characters"]["桃子"]["origin"] == "modified"
    assert states["after"]["characters"]["静"]["origin"] == "current"

    # chara_move is relative to the settled top-left position.
    assert states["after"]["characters"]["桃子"]["left"] == 234.0
    assert states["after"]["characters"]["桃子"]["top"] == -216.0
    assert states["after"]["characters"]["桃子"]["zoom"] == 1.5


def test_scene_builder_removes_hidden_character_from_after_state():
    builder = StepSceneStateBuilder(image_size_lookup=_size_lookup)
    states = builder.build(
        [
            ['chara_show name="桃子" torso="MMK_T00"'],
            ['chara_hide name="桃子" fade="0.3"'],
        ],
        1,
    )

    assert "桃子" in states["before"]["characters"]
    assert "桃子" not in states["after"]["characters"]
    assert states["changes"]["桃子"] == "hide"


def test_scene_builder_reuses_an_unchanged_step_state_from_memory():
    builder = StepSceneStateBuilder(image_size_lookup=_size_lookup)
    action_steps = [
        ['chara_show name="A" torso="MMK_T00"'],
        ['chara_move name="A" left="0.1" top="0.0" zoom="1.0"'],
    ]

    first = builder.build(action_steps, 1)
    second = builder.build(action_steps, 1)

    assert second is first


def test_scene_builder_pages_forward_from_the_cached_prefix(monkeypatch):
    builder = StepSceneStateBuilder(image_size_lookup=_size_lookup)
    action_steps = [
        ['chara_show name="A" torso="MMK_T00"'],
        ['chara_move name="A" left="0.1" top="0.0" zoom="1.0"'],
        ['chara_move name="A" left="0.0" top="0.1" zoom="1.0"'],
    ]
    original_apply = builder._apply_action
    calls = []

    def counted_apply(*args, **kwargs):
        calls.append(args[1])
        return original_apply(*args, **kwargs)

    monkeypatch.setattr(builder, "_apply_action", counted_apply)
    builder.build(action_steps, 1)
    calls_after_first_build = len(calls)
    builder.build(action_steps, 2)

    assert calls_after_first_build == 2
    assert len(calls) == calls_after_first_build + 1


def test_scene_canvas_resolves_legacy_partial_background_id(tmp_path):
    background_path = tmp_path / "classroom.png"
    image = QImage(320, 240, QImage.Format_ARGB32)
    image.fill(QColor(40, 100, 160))
    assert image.save(str(background_path))

    manager = SimpleNamespace(
        image_paths={
            "bg": {"教室昼": str(background_path)},
            "torso": {},
            "brow": {},
            "cheek": {},
            "eye": {},
            "mouth": {},
            "accessory": {},
            "effect": {},
        }
    )
    canvas = StepSceneCanvas(manager)
    canvas.set_scene_state(
        {
            "background": {
                "storage": "教室",
                "zoom": 1.0,
                "offset_x": 0.0,
                "offset_y": 0.0,
                "origin": "current",
            },
            "characters": {},
        }
    )

    background_items = [
        item for item in canvas.scene().items() if item.data(0) == "background"
    ]
    assert len(background_items) == 1
    assert background_items[0].data(1) == "教室"


def test_scene_canvas_keeps_character_as_selectable_object(tmp_path):
    torso_path = tmp_path / "torso.png"
    image = QImage(100, 200, QImage.Format_ARGB32)
    image.fill(QColor(220, 80, 120))
    assert image.save(str(torso_path))

    manager = SimpleNamespace(
        image_paths={
            "bg": {},
            "torso": {"MMK_T00": str(torso_path)},
            "brow": {},
            "cheek": {},
            "eye": {},
            "mouth": {},
            "accessory": {},
            "effect": {},
        }
    )
    canvas = StepSceneCanvas(manager)
    selected = []
    moved = []
    scaled = []
    context_requests = []
    canvas.object_selected.connect(lambda *args: selected.append(args))
    canvas.object_moved.connect(lambda *args: moved.append(args))
    canvas.object_scaled.connect(lambda *args: scaled.append(args))
    canvas.context_requested.connect(lambda *args: context_requests.append(args))
    canvas.set_scene_state(
        {
            "background": None,
            "characters": {
                "桃子": {
                    "name": "桃子",
                    "torso": "MMK_T00",
                    "left": VIRTUAL_WIDTH / 2 - 270,
                    "top": 0,
                    "zoom": 1.0,
                    "origin": "inherited",
                }
            },
        }
    )

    character_items = [
        item for item in canvas.scene().items() if item.data(0) == "character"
    ]
    assert len(character_items) == 1
    assert character_items[0].flags() & QGraphicsItem.ItemIsMovable
    character_items[0].setSelected(True)
    APP.processEvents()

    assert selected[-1] == ("character", "桃子", "inherited")

    canvas.resize(400, 300)
    canvas.show()
    APP.processEvents()
    start = canvas.mapFromScene(character_items[0].sceneBoundingRect().center())
    end = start + QPoint(20, 0)
    assert canvas._character_item_at(start) is character_items[0]
    QApplication.sendEvent(
        canvas.viewport(),
        QMouseEvent(
            QEvent.MouseButtonPress,
            QPointF(start),
            Qt.LeftButton,
            Qt.LeftButton,
            Qt.NoModifier,
        ),
    )
    QApplication.sendEvent(
        canvas.viewport(),
        QMouseEvent(
            QEvent.MouseMove,
            QPointF(end),
            Qt.NoButton,
            Qt.LeftButton,
            Qt.NoModifier,
        ),
    )
    QApplication.sendEvent(
        canvas.viewport(),
        QMouseEvent(
            QEvent.MouseButtonRelease,
            QPointF(end),
            Qt.LeftButton,
            Qt.NoButton,
            Qt.NoModifier,
        ),
    )
    APP.processEvents()

    assert moved
    assert moved[-1][0] == "桃子"
    assert moved[-1][1] > 0

    # Shift-drag chooses the dominant first direction and locks to that axis.
    moved.clear()
    start = canvas.mapFromScene(character_items[0].sceneBoundingRect().center())
    end = start + QPoint(10, 30)
    QApplication.sendEvent(
        canvas.viewport(),
        QMouseEvent(
            QEvent.MouseButtonPress,
            QPointF(start),
            Qt.LeftButton,
            Qt.LeftButton,
            Qt.ShiftModifier,
        ),
    )
    QApplication.sendEvent(
        canvas.viewport(),
        QMouseEvent(
            QEvent.MouseMove,
            QPointF(end),
            Qt.NoButton,
            Qt.LeftButton,
            Qt.ShiftModifier,
        ),
    )
    QApplication.sendEvent(
        canvas.viewport(),
        QMouseEvent(
            QEvent.MouseButtonRelease,
            QPointF(end),
            Qt.LeftButton,
            Qt.NoButton,
            Qt.ShiftModifier,
        ),
    )
    APP.processEvents()
    assert moved
    assert abs(moved[-1][1]) < 0.01
    assert moved[-1][2] > 0

    class FakeWheelEvent:
        def __init__(self, pos):
            self._pos = pos
            self.accepted = False

        def modifiers(self):
            return Qt.ShiftModifier

        def angleDelta(self):
            return QPoint(0, 120)

        def pos(self):
            return self._pos

        def accept(self):
            self.accepted = True

    wheel_pos = canvas.mapFromScene(character_items[0].sceneBoundingRect().center())
    wheel_event = FakeWheelEvent(wheel_pos)
    canvas.wheelEvent(wheel_event)
    canvas.wheelEvent(FakeWheelEvent(wheel_pos))
    assert wheel_event.accepted
    assert not scaled
    canvas.flush_pending_scale()
    assert len(scaled) == 1
    assert scaled[-1][0] == "桃子"
    assert scaled[-1][1] > 1.08

    class FakeContextEvent:
        def __init__(self, pos):
            self._pos = pos
            self.accepted = False

        def pos(self):
            return self._pos

        def globalPos(self):
            return self._pos

        def accept(self):
            self.accepted = True

    character_context = FakeContextEvent(wheel_pos)
    canvas.contextMenuEvent(character_context)
    assert character_context.accepted
    assert context_requests[-1][0:2] == ("character", "桃子")

    stage_context = FakeContextEvent(canvas.mapFromScene(10, 10))
    canvas.contextMenuEvent(stage_context)
    assert stage_context.accepted
    assert context_requests[-1][0] == "stage"


def test_scene_canvas_arrow_keys_nudge_selection_and_page_when_unselected(tmp_path):
    torso_path = tmp_path / "torso.png"
    image = QImage(100, 200, QImage.Format_ARGB32)
    image.fill(QColor(220, 80, 120))
    assert image.save(str(torso_path))
    manager = _empty_image_manager()
    manager.image_paths["torso"]["body"] = str(torso_path)
    canvas = StepSceneCanvas(manager)
    canvas.set_scene_state(
        {
            "characters": {
                "A": {
                    "name": "A",
                    "torso": "body",
                    "left": 100.0,
                    "top": 200.0,
                    "zoom": 1.0,
                }
            }
        }
    )
    item = next(item for item in canvas.scene().items() if item.data(0) == "character")
    item.setSelected(True)
    moved = []
    navigated = []
    canvas.object_moved.connect(lambda *args: moved.append(args))
    canvas.step_navigation_requested.connect(navigated.append)

    canvas.keyPressEvent(QKeyEvent(QEvent.KeyPress, Qt.Key_Left, Qt.NoModifier))
    canvas.keyPressEvent(QKeyEvent(QEvent.KeyPress, Qt.Key_Down, Qt.ShiftModifier))

    assert item.pos() == QPointF(99.0, 210.0)
    assert [(entry[1], entry[2]) for entry in moved] == [(-1.0, 0.0), (0.0, 10.0)]
    assert not navigated

    canvas.scene().clearSelection()
    canvas.keyPressEvent(QKeyEvent(QEvent.KeyPress, Qt.Key_Right, Qt.NoModifier))
    assert navigated == [1]


def test_scene_canvas_corner_drag_scales_selected_character(tmp_path):
    torso_path = tmp_path / "torso.png"
    image = QImage(100, 200, QImage.Format_ARGB32)
    image.fill(QColor(220, 80, 120))
    assert image.save(str(torso_path))

    manager = _empty_image_manager()
    manager.image_paths["torso"]["body"] = str(torso_path)
    canvas = StepSceneCanvas(manager)
    canvas.resize(400, 300)
    canvas.show()
    canvas.set_scene_state(
        {
            "characters": {
                "A": {
                    "name": "A",
                    "torso": "body",
                    "left": 100.0,
                    "top": 100.0,
                    "zoom": 1.0,
                    "origin": "current",
                }
            }
        }
    )
    item = next(item for item in canvas.scene().items() if item.data(0) == "character")
    item.setSelected(True)
    APP.processEvents()
    handles = [item for item in canvas.scene().items() if item.data(0) == "resize_handle"]
    assert len(handles) == 4

    scaled = []
    canvas.object_scaled.connect(lambda *args: scaled.append(args))
    handle = next(item for item in handles if item.data(4) == "bottom_right")
    start = canvas.mapFromScene(handle.scenePos())
    center = canvas.mapFromScene(item.sceneBoundingRect().center())
    end = QPoint(
        center.x() + int((start.x() - center.x()) * 1.5),
        center.y() + int((start.y() - center.y()) * 1.5),
    )

    for event in (
        QMouseEvent(
            QEvent.MouseButtonPress,
            QPointF(start),
            Qt.LeftButton,
            Qt.LeftButton,
            Qt.NoModifier,
        ),
        QMouseEvent(
            QEvent.MouseMove,
            QPointF(end),
            Qt.NoButton,
            Qt.LeftButton,
            Qt.NoModifier,
        ),
        QMouseEvent(
            QEvent.MouseButtonRelease,
            QPointF(end),
            Qt.LeftButton,
            Qt.NoButton,
            Qt.NoModifier,
        ),
    ):
        QApplication.sendEvent(canvas.viewport(), event)
    APP.processEvents()

    assert scaled
    assert scaled[-1][0] == "A"
    assert scaled[-1][1] > 1.0
    canvas.close()


def test_final_preview_pixmap_refits_when_tab_gets_smaller():
    label = FitPixmapLabel()
    source = QImage(640, 480, QImage.Format_ARGB32)
    source.fill(QColor(20, 40, 80))
    label.resize(400, 300)
    label.show()
    label.set_source_pixmap(source)
    APP.processEvents()
    assert label.pixmap().size().width() <= label.contentsRect().width()
    assert label.pixmap().size().height() <= label.contentsRect().height()

    label.resize(200, 100)
    APP.processEvents()
    assert label.pixmap().width() == 133
    assert label.pixmap().height() == 100


def _empty_image_manager():
    return SimpleNamespace(
        image_paths={
            key: {}
            for key in (
                "bg",
                "torso",
                "brow",
                "cheek",
                "eye",
                "mouth",
                "accessory",
                "effect",
            )
        }
    )


def test_dragging_current_show_updates_its_absolute_position():
    steps = [{"step_index": 0}]
    dialog = StepEditorDialog(
        None,
        steps[0],
        actions=['chara_show name="桃子" torso="MMK_T00" x="0.5" y="0.6" size="2.3"'],
        all_steps=steps,
        all_step_actions=[[]],
        step_index=0,
        image_manager=_empty_image_manager(),
    )

    dialog._on_scene_object_moved("桃子", 144.0, -108.0, {"zoom": 2.3})

    tag, pairs = dialog._parse_action(dialog.get_actions()[0])
    params = dict(pairs)
    assert tag == "chara_show"
    assert params["x"] == "0.6"
    assert params["y"] == "0.5"
    assert not any(action.startswith("chara_move") for action in dialog.get_actions())


def test_dragging_inherited_character_adds_relative_move():
    steps = [{"step_index": 0}, {"step_index": 1}]
    prior_show = 'chara_show name="桃子" torso="MMK_T00" x="0.5" y="0.6" size="2.3"'
    dialog = StepEditorDialog(
        None,
        steps[1],
        actions=[],
        all_steps=steps,
        all_step_actions=[[prior_show], []],
        step_index=1,
        image_manager=_empty_image_manager(),
    )

    dialog._on_scene_object_moved("桃子", 72.0, 108.0, {"zoom": 2.3})

    assert dialog.get_actions() == [
        'chara_move name="桃子" left="0.05" top="0.1" zoom="2.3" time="600"'
    ]


def test_repeated_drag_updates_existing_move_instead_of_adding_another():
    steps = [{"step_index": 0}, {"step_index": 1}]
    prior_show = 'chara_show name="桃子" torso="MMK_T00" size="2.3"'
    dialog = StepEditorDialog(
        None,
        steps[1],
        actions=['chara_move name="桃子" left="0.1" top="0.0" zoom="2.3" time="900"'],
        all_steps=steps,
        all_step_actions=[[prior_show], []],
        step_index=1,
        image_manager=_empty_image_manager(),
    )

    dialog._on_scene_object_moved("桃子", 72.0, -54.0, {"zoom": 2.3})

    assert dialog.get_actions() == [
        'chara_move name="桃子" left="0.15" top="-0.05" zoom="2.3" time="900"'
    ]


def test_shift_wheel_updates_show_size_or_adds_inherited_move():
    steps = [{"step_index": 0}, {"step_index": 1}]
    prior_show = 'chara_show name="桃子" torso="MMK_T00" size="2.3"'

    show_dialog = StepEditorDialog(
        None,
        steps[0],
        actions=[prior_show],
        all_steps=steps,
        all_step_actions=[[prior_show], []],
        step_index=0,
        image_manager=_empty_image_manager(),
    )
    show_dialog._on_scene_object_scaled("桃子", 2.5, {"zoom": 2.5})
    assert 'size="2.5"' in show_dialog.get_actions()[0]
    assert not any(action.startswith("chara_move") for action in show_dialog.get_actions())

    inherited_dialog = StepEditorDialog(
        None,
        steps[1],
        actions=[],
        all_steps=steps,
        all_step_actions=[[prior_show], []],
        step_index=1,
        image_manager=_empty_image_manager(),
    )
    inherited_dialog._on_scene_object_scaled("桃子", 2.5, {"zoom": 2.5})
    assert inherited_dialog.get_actions() == [
        'chara_move name="桃子" left="0.0" top="0.0" zoom="2.5" time="600"'
    ]


def test_stage_context_commands_insert_visual_audio_and_system_tags(monkeypatch):
    steps = [{"step_index": 0}]
    dialog = StepEditorDialog(
        None,
        steps[0],
        actions=[],
        all_steps=steps,
        all_step_actions=[[]],
        step_index=0,
        image_manager=_empty_image_manager(),
    )

    opened = []
    monkeypatch.setattr(dialog, "_open_chara_preview", lambda is_shift: opened.append(is_shift))
    for command in ("chara_show", "bg_show", "bgm", "se", "fadeout", "flag_set"):
        dialog._execute_scene_context_command(command)
    APP.processEvents()
    dialog._execute_scene_context_command("character_hide", "桃子")

    tags = [dialog._parse_action(action)[0] for action in dialog.get_actions()]
    assert tags == [
        "chara_show",
        "bg_show",
        "bgm",
        "se",
        "fadeout",
        "flag_set",
        "chara_hide",
    ]
    assert 'name="桃子"' in dialog.get_actions()[-1]
    assert opened == [False]


def test_dialog_arrow_nudge_persists_one_virtual_pixel():
    steps = [{"step_index": 0}]
    show = 'chara_show name="A" torso="missing" x="0.5" y="0.5" size="1.0"'
    dialog = StepEditorDialog(
        None,
        steps[0],
        actions=[show],
        all_steps=steps,
        all_step_actions=[[show]],
        step_index=0,
        image_manager=_empty_image_manager(),
    )
    item = next(
        item
        for item in dialog.scene_canvas.scene().items()
        if item.data(0) == "character"
    )
    item.setSelected(True)

    dialog.scene_canvas.keyPressEvent(
        QKeyEvent(QEvent.KeyPress, Qt.Key_Right, Qt.NoModifier)
    )

    tag, pairs = dialog._parse_action(dialog.get_actions()[0])
    assert tag == "chara_show"
    assert dict(pairs)["x"] == "0.50069444"


def test_direct_canvas_scale_does_not_start_pygame_snapshot_timer():
    steps = [{"step_index": 0}]
    show = 'chara_show name="桃子" torso="MMK_T00" size="2.3"'
    dialog = StepEditorDialog(
        None,
        steps[0],
        actions=[show],
        all_steps=steps,
        all_step_actions=[[show]],
        step_index=0,
        image_manager=_empty_image_manager(),
    )

    dialog._on_scene_object_scaled("桃子", 2.5, {"zoom": 2.5})

    assert 'size="2.5"' in dialog.get_actions()[0]
    assert not dialog._preview_debounce_timer.isActive()


def test_drag_after_position_shift_appends_move_so_final_position_is_not_overridden():
    steps = [{"step_index": 0}, {"step_index": 1}]
    prior_show = 'chara_show name="桃子" torso="MMK_T00" size="2.3"'
    shift = 'chara_shift name="桃子" x="0.4" eye="eye_b"'
    dialog = StepEditorDialog(
        None,
        steps[1],
        actions=[shift],
        all_steps=steps,
        all_step_actions=[[prior_show], [shift]],
        step_index=1,
        image_manager=_empty_image_manager(),
    )

    dialog._on_scene_object_moved("桃子", 144.0, 0.0, {"zoom": 2.3})

    assert dialog.get_actions() == [
        shift,
        'chara_move name="桃子" left="0.1" top="0.0" zoom="2.3" time="600"',
    ]


def test_step_navigation_stays_in_same_dialog_and_loads_adjacent_step():
    manager = _empty_image_manager()
    steps = [
        {"step_index": 0, "speaker": "A", "body": "first"},
        {"step_index": 1, "speaker": "B", "body": "second"},
    ]
    dialog = StepEditorDialog(
        None,
        steps[0],
        actions=[],
        all_steps=steps,
        all_step_actions=[[], []],
        step_index=0,
        image_manager=manager,
    )

    assert dialog.prev_step_btn.isEnabled()
    assert "新規step" in dialog.prev_step_btn.text()
    assert dialog.next_step_btn.isEnabled()
    dialog._navigate_step(1)

    assert dialog.result() != QDialog.Accepted
    assert dialog._step_index == 1
    assert dialog.speaker_input.text() == "B"
    assert dialog.body_input.text() == "second"
    assert dialog.step_outline.currentRow() == 1
    assert "新規step" in dialog.next_step_btn.text()


def test_step_editor_can_start_preview_from_its_current_step():
    manager = _empty_image_manager()
    steps = [
        {"step_index": 0, "speaker": "A", "body": "first"},
        {"step_index": 1, "speaker": "B", "body": "second"},
    ]
    parent = QWidget()
    parent.preview_step_entry = QLineEdit()
    preview_calls = []
    parent.start_preview = lambda: preview_calls.append(True)
    dialog = StepEditorDialog(
        parent,
        steps[1],
        actions=[],
        all_steps=steps,
        all_step_actions=[[], []],
        step_index=1,
        image_manager=manager,
    )
    dialog.body_input.setText("edited draft")

    dialog.preview_from_step_btn.click()

    assert steps[1]["body"] == "edited draft"
    assert parent.preview_step_entry.text() == "2"
    assert preview_calls == [True]
    dialog.close()
    parent.close()


def test_unselected_canvas_arrow_pages_the_dialog_step():
    manager = _empty_image_manager()
    steps = [
        {"step_index": 0, "speaker": "A", "body": "first"},
        {"step_index": 1, "speaker": "B", "body": "second"},
    ]
    dialog = StepEditorDialog(
        None,
        steps[0],
        actions=[],
        all_steps=steps,
        all_step_actions=[[], []],
        step_index=0,
        image_manager=manager,
    )

    dialog.scene_canvas.scene().clearSelection()
    dialog.scene_canvas.keyPressEvent(
        QKeyEvent(QEvent.KeyPress, Qt.Key_Right, Qt.NoModifier)
    )

    assert dialog._step_index == 1
    assert dialog.body_input.text() == "second"


def test_final_preview_is_restored_from_memory_when_paging_back(tmp_path):
    manager = _empty_image_manager()
    steps = [
        {"step_index": 0, "speaker": "A", "body": "first"},
        {"step_index": 1, "speaker": "B", "body": "second"},
    ]
    dialog = StepEditorDialog(
        None,
        steps[0],
        actions=[],
        all_steps=steps,
        all_step_actions=[[], []],
        step_index=0,
        image_manager=manager,
    )
    preview_path = tmp_path / "preview.png"
    preview = QImage(64, 48, QImage.Format_ARGB32)
    preview.fill(QColor(10, 20, 30))
    assert preview.save(str(preview_path))
    dialog.set_preview_image(str(preview_path))

    dialog._navigate_step(1)
    dialog._navigate_step(-1)

    assert dialog._step_index == 0
    assert not dialog.preview_label._source_pixmap.isNull()


def test_step_navigation_can_apply_dirty_values_before_moving():
    manager = _empty_image_manager()
    steps = [
        {"step_index": 0, "speaker": "A", "body": "first"},
        {"step_index": 1, "speaker": "B", "body": "second"},
    ]
    dialog = StepEditorDialog(
        None,
        steps[0],
        actions=[],
        all_steps=steps,
        all_step_actions=[[], []],
        step_index=0,
        image_manager=manager,
    )
    dialog.body_input.setText("edited")
    dialog._confirm_step_transition = lambda: "apply"

    dialog._navigate_step(1)

    assert steps[0]["body"] == "edited"
    assert dialog._step_index == 1
    assert not dialog._is_step_dirty()


def test_outline_navigation_cancel_keeps_the_current_step_and_draft():
    manager = _empty_image_manager()
    steps = [
        {"step_index": 0, "speaker": "A", "body": "first"},
        {"step_index": 1, "speaker": "B", "body": "second"},
    ]
    dialog = StepEditorDialog(
        None,
        steps[0],
        actions=[],
        all_steps=steps,
        all_step_actions=[[], []],
        step_index=0,
        image_manager=manager,
    )
    dialog.body_input.setText("draft")
    dialog._confirm_step_transition = lambda: "cancel"

    dialog.step_outline.setCurrentRow(1)

    assert dialog._step_index == 0
    assert dialog.step_outline.currentRow() == 0
    assert dialog.body_input.text() == "draft"
    assert dialog._is_step_dirty()


def test_step_navigation_creates_a_new_step_at_the_edge_after_confirmation():
    manager = _empty_image_manager()
    steps = [{"step_index": 0, "speaker": "A", "body": "first"}]
    dialog = StepEditorDialog(
        None,
        steps[0],
        actions=[],
        all_steps=steps,
        all_step_actions=[[]],
        step_index=0,
        image_manager=manager,
    )
    dialog._confirm_create_step = lambda _offset: True

    dialog._navigate_step(1)

    assert len(dialog._all_steps) == 2
    assert dialog._step_index == 1
    assert dialog.speaker_input.text() == "speaker"
    assert dialog.body_input.text() == "セリフ"


def test_step_slide_moves_two_connected_pages_by_a_full_viewport_width():
    manager = _empty_image_manager()
    step = {"step_index": 0, "speaker": "A", "body": "first"}
    dialog = StepEditorDialog(
        None,
        step,
        actions=[],
        all_steps=[step],
        all_step_actions=[[]],
        step_index=0,
        image_manager=manager,
    )
    dialog.show()
    APP.processEvents()

    viewport = dialog.slide_viewport
    previous = viewport.capture_content()
    viewport.slide_in(1, previous)
    animation = viewport._animation
    incoming = animation.animationAt(0)
    outgoing = animation.animationAt(1)

    assert incoming.startValue() == QPoint(viewport.width(), 0)
    assert incoming.endValue() == QPoint(0, 0)
    assert incoming.duration() == 140
    assert outgoing.startValue() == QPoint(0, 0)
    assert outgoing.endValue() == QPoint(-viewport.width(), 0)
    assert outgoing.duration() == 140

    animation.stop()
    dialog.close()
