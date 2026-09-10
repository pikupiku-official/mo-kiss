"""Lightweight CG asset browser used by the step editor."""

from __future__ import annotations

import os
import re
from collections import defaultdict

from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QImageReader, QPixmap
from PyQt5.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
)


CG_ASSET_RE = re.compile(r"^(?P<char>[A-Za-z]{3})_(?P<cg>\d{2})_(?P<diff>\d{3})$")


def list_cg_assets(image_manager):
    """Return CG assets grouped by character code and CG number."""
    grouped = defaultdict(list)
    if not image_manager:
        return grouped
    for stem, path in image_manager.image_paths.get("cg", {}).items():
        match = CG_ASSET_RE.fullmatch(os.path.splitext(stem)[0])
        if not match:
            continue
        grouped[(match.group("char").upper(), match.group("cg"))].append(
            (match.group("diff"), stem, path)
        )
    for items in grouped.values():
        items.sort(key=lambda item: item[0])
    return grouped


class CgDiffBrowserDialog(QDialog):
    """Select one CG asset without eagerly decoding the whole CG library."""

    def __init__(self, parent, image_manager, current_storage="", preferred_storage=""):
        super().__init__(parent)
        self.setWindowTitle("CG差分一覧")
        self.resize(720, 520)
        self._grouped = list_cg_assets(image_manager)
        self._current_storage = (current_storage or "").strip()
        self._preferred_storage = (preferred_storage or "").strip()
        self._selected_storage = self._current_storage

        layout = QVBoxLayout(self)
        selector_row = QHBoxLayout()
        selector_row.addWidget(QLabel("CG番号"))
        self.cg_combo = QComboBox()
        for char_code, cg_number in sorted(self._grouped):
            self.cg_combo.addItem(f"{char_code}_{cg_number}", (char_code, cg_number))
        selector_row.addWidget(self.cg_combo, 1)
        layout.addLayout(selector_row)

        content = QHBoxLayout()
        self.diff_list = QListWidget()
        self.diff_list.setSelectionMode(QListWidget.SingleSelection)
        self.diff_list.itemDoubleClicked.connect(lambda _item: self.accept())
        content.addWidget(self.diff_list, 1)

        self.preview = QLabel("差分を選択してください")
        self.preview.setAlignment(Qt.AlignCenter)
        self.preview.setMinimumSize(420, 300)
        self.preview.setStyleSheet("border: 1px solid #888; background: #111; color: #ddd;")
        content.addWidget(self.preview, 2)
        layout.addLayout(content, 1)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText("適用")
        buttons.button(QDialogButtonBox.Cancel).setText("キャンセル")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.cg_combo.currentIndexChanged.connect(lambda _index: self._populate_diffs())
        self.diff_list.currentItemChanged.connect(self._select_diff)
        self._select_initial_group()

    def _select_initial_group(self):
        match = CG_ASSET_RE.fullmatch(os.path.splitext(self._current_storage)[0])
        if match:
            wanted = (match.group("char").upper(), match.group("cg"))
            index = self.cg_combo.findData(wanted)
            if index >= 0:
                self.cg_combo.setCurrentIndex(index)
                self._populate_diffs()
                return
        # Keep newly-created CG actions on the set already used by the event.
        preferred_match = CG_ASSET_RE.fullmatch(os.path.splitext(self._preferred_storage)[0])
        if preferred_match:
            wanted = (preferred_match.group("char").upper(), preferred_match.group("cg"))
            index = self.cg_combo.findData(wanted)
            if index >= 0:
                self.cg_combo.setCurrentIndex(index)
                self._populate_diffs()
                return
        if self.cg_combo.count():
            self.cg_combo.setCurrentIndex(0)
            self._populate_diffs()
        else:
            self._populate_diffs()

    def _populate_diffs(self):
        self.diff_list.clear()
        key = self.cg_combo.currentData()
        for diff, stem, path in self._grouped.get(key, []):
            item = QListWidgetItem(f"差分 {diff}   ({stem})")
            item.setData(Qt.UserRole, (stem, path))
            self.diff_list.addItem(item)

        current_stem = os.path.splitext(self._current_storage)[0]
        for index in range(self.diff_list.count()):
            item = self.diff_list.item(index)
            stem, _ = item.data(Qt.UserRole)
            if stem == current_stem:
                self.diff_list.setCurrentRow(index)
                return
        if self.diff_list.count():
            self.diff_list.setCurrentRow(0)

    def _select_diff(self, current, _previous):
        if current is None:
            return
        stem, path = current.data(Qt.UserRole)
        self._selected_storage = stem
        reader = QImageReader(path)
        reader.setAutoTransform(True)
        reader.setScaledSize(QSize(480, 320))
        image = reader.read()
        pixmap = QPixmap.fromImage(image) if not image.isNull() else QPixmap()
        if pixmap.isNull():
            self.preview.setText(f"画像を読み込めません: {stem}")
            self.preview.setPixmap(QPixmap())
            return
        self.preview.setText("")
        self.preview.setPixmap(
            pixmap.scaled(self.preview.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        )

    def resizeEvent(self, event):
        super().resizeEvent(event)
        current = self.diff_list.currentItem()
        if current is not None:
            self._select_diff(current, None)

    @property
    def selected_storage(self):
        return self._selected_storage
