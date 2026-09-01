"""
KSファイル専用エディタ - PyQt5版(macOS対応)

画面構成:
- 左側:ファイルリストとテキストエディタ
- 右側:使用方法とヘルプ情報
- ツールバー:保存、編集支援機能

注意: macOSでは技術的制限によりPygameプレビュー機能は利用できません。
      編集後は main.py でゲーム本体を起動してプレビュー確認してください。
"""

import os
import sys
import csv
import math
import re
import pygame
import threading
import tempfile
import queue
import platform
import traceback
import logging
import subprocess
import json
from collections import OrderedDict
from datetime import datetime
from pathlib import Path

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QListWidget, QListWidgetItem, QPushButton, QLabel, QSplitter,
    QLineEdit, QMessageBox, QToolBar, QAction, QGroupBox,
    QFormLayout, QDialog, QDialogButtonBox, QMenu, QCheckBox,
    QAbstractItemView, QComboBox, QTableWidget, QTableWidgetItem,
    QFileDialog, QInputDialog, QTabWidget, QSlider, QDoubleSpinBox,
    QStyleFactory, QAbstractButton,
)
from PyQt5.QtCore import (
    Qt, QTimer, pyqtSignal, QObject, QRect, QPoint, QProcess, QEvent, QSize,
    QEasingCurve, QParallelAnimationGroup, QPropertyAnimation,
)
from PyQt5.QtGui import (
    QFont, QTextCursor, QTextCharFormat, QColor, QPixmap, QImage, QPainter,
    QPalette, QLinearGradient,
)

# プロジェクトルートをパスに追加
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# ログファイルの設定
log_file = os.path.join(project_root, "debug/event_editor.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
logger.info("=" * 60)
logger.info("イベントエディタ (PyQt5版) 起動")
logger.info("=" * 60)

from dialogue.dialogue_loader import DialogueLoader
from dialogue.data_normalizer import normalize_dialogue_data
from dialogue.ir_builder import build_ir_from_normalized, dump_ir_json, get_ir_dump_path
from dialogue.ir_model import STANDALONE_STEP_MARKER
from dialogue.controller2 import (
    handle_events as handle_dialogue_events,
    update_game,
    draw_input_blocked_notice,
)
from dialogue.text_renderer import TextRenderer
from dialogue.character_manager import draw_characters
from dialogue.background_manager import draw_background
from dialogue.choice_renderer import ChoiceRenderer
from dialogue.fade_manager import draw_fade_overlay
from dialogue.backlog_manager import BacklogManager
from dialogue.notification_manager import NotificationManager
from dialogue.event_datetime import (
    EVENT_DATETIME_FORMAT,
    EVENT_DATETIME_HEADER,
    apply_event_datetime,
    parse_event_datetime,
)
from core.config import VIRTUAL_WIDTH, VIRTUAL_HEIGHT, DEBUG, USE_IR, IR_DUMP_JSON, IR_DUMP_DIR
from core.services.bgm_manager import BGMManager
from core.services.se_manager import SEManager
from core.services.image_manager import ImageManager
from tools.event_editor_scene import (
    FitPixmapLabel,
    StepSceneCanvas,
    StepSceneStateBuilder,
    parse_step_action,
)
from tools.event_editor_part_templates import CharaPartTemplateStore


def apply_windows_2000_style(app):
    """Use Qt's real classic-Windows controls with the Windows 2000 palette."""
    if app is None:
        return False

    available_styles = {name.lower(): name for name in QStyleFactory.keys()}
    windows_style_name = available_styles.get("windows")
    if windows_style_name:
        windows_style = QStyleFactory.create(windows_style_name)
        if windows_style is not None:
            app.setStyle(windows_style)

    palette = QPalette()
    classic_colors = {
        QPalette.Window: QColor(212, 208, 200),       # COLOR_3DFACE
        QPalette.WindowText: QColor(0, 0, 0),
        QPalette.Base: QColor(255, 255, 255),         # COLOR_WINDOW
        QPalette.AlternateBase: QColor(232, 228, 220),
        QPalette.ToolTipBase: QColor(255, 255, 225),
        QPalette.ToolTipText: QColor(0, 0, 0),
        QPalette.Text: QColor(0, 0, 0),
        QPalette.Button: QColor(212, 208, 200),
        QPalette.ButtonText: QColor(0, 0, 0),
        QPalette.BrightText: QColor(255, 255, 255),
        QPalette.Light: QColor(255, 255, 255),
        QPalette.Midlight: QColor(223, 220, 212),
        QPalette.Mid: QColor(160, 160, 160),
        QPalette.Dark: QColor(128, 128, 128),
        QPalette.Shadow: QColor(0, 0, 0),
        QPalette.Highlight: QColor(10, 36, 106),       # COLOR_HIGHLIGHT
        QPalette.HighlightedText: QColor(255, 255, 255),
        QPalette.Link: QColor(0, 0, 255),
        QPalette.LinkVisited: QColor(128, 0, 128),
    }
    for role, color in classic_colors.items():
        palette.setColor(QPalette.Active, role, color)
        palette.setColor(QPalette.Inactive, role, color)

    disabled_text = QColor(128, 128, 128)
    for role in (QPalette.WindowText, QPalette.Text, QPalette.ButtonText):
        palette.setColor(QPalette.Disabled, role, disabled_text)
    palette.setColor(QPalette.Disabled, QPalette.Window, QColor(212, 208, 200))
    palette.setColor(QPalette.Disabled, QPalette.Base, QColor(212, 208, 200))
    palette.setColor(QPalette.Disabled, QPalette.Button, QColor(212, 208, 200))
    palette.setColor(QPalette.Disabled, QPalette.Highlight, QColor(212, 208, 200))
    palette.setColor(QPalette.Disabled, QPalette.HighlightedText, disabled_text)

    app.setPalette(palette)
    return windows_style_name is not None


class Win2000CaptionButton(QAbstractButton):
    """Pixel-drawn Windows 2000 caption button."""

    def __init__(self, role, parent=None):
        super().__init__(parent)
        self.role = role
        self._caption_size = 18
        self.setFixedSize(self._caption_size, self._caption_size)
        self.setFocusPolicy(Qt.NoFocus)
        self.setCursor(Qt.ArrowCursor)
        labels = {
            "minimize": "最小化",
            "maximize": "最大化",
            "restore": "元に戻す",
            "close": "閉じる",
        }
        self.setToolTip(labels.get(role, role))
        self.setAccessibleName(labels.get(role, role))

    def sizeHint(self):
        return QSize(self._caption_size, self._caption_size)

    def set_caption_size(self, size):
        size = max(18, int(size))
        if size == self._caption_size:
            return
        self._caption_size = size
        self.setFixedSize(size, size)
        self.updateGeometry()
        self.update()

    def set_role(self, role):
        if role == self.role:
            return
        self.role = role
        label = "元に戻す" if role == "restore" else "最大化"
        self.setToolTip(label)
        self.setAccessibleName(label)
        self.update()

    @staticmethod
    def _draw_bevel(painter, rect, sunken):
        left = rect.left()
        top = rect.top()
        right = rect.right()
        bottom = rect.bottom()
        if sunken:
            painter.setPen(QColor(0, 0, 0))
            painter.drawLine(left, top, right, top)
            painter.drawLine(left, top, left, bottom)
            painter.setPen(QColor(128, 128, 128))
            painter.drawLine(left + 1, top + 1, right - 1, top + 1)
            painter.drawLine(left + 1, top + 1, left + 1, bottom - 1)
            painter.setPen(QColor(255, 255, 255))
            painter.drawLine(left + 1, bottom, right, bottom)
            painter.drawLine(right, top + 1, right, bottom)
        else:
            painter.setPen(QColor(255, 255, 255))
            painter.drawLine(left, top, right, top)
            painter.drawLine(left, top, left, bottom)
            painter.setPen(QColor(128, 128, 128))
            painter.drawLine(left + 1, bottom - 1, right - 1, bottom - 1)
            painter.drawLine(right - 1, top + 1, right - 1, bottom - 1)
            painter.setPen(QColor(0, 0, 0))
            painter.drawLine(left, bottom, right, bottom)
            painter.drawLine(right, top, right, bottom)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, False)
        painter.fillRect(self.rect(), QColor(212, 208, 200))
        self._draw_bevel(painter, self.rect().adjusted(0, 0, -1, -1), self.isDown())

        glyph_scale = min(self.width(), self.height()) / 18.0
        painter.save()
        painter.scale(glyph_scale, glyph_scale)
        offset = 1 if self.isDown() else 0
        painter.setPen(QColor(0, 0, 0))
        painter.setBrush(QColor(0, 0, 0))
        if self.role == "minimize":
            painter.fillRect(5 + offset, 12 + offset, 8, 2, QColor(0, 0, 0))
        elif self.role == "maximize":
            painter.drawRect(4 + offset, 4 + offset, 9, 8)
            painter.fillRect(5 + offset, 5 + offset, 8, 2, QColor(0, 0, 0))
        elif self.role == "restore":
            painter.drawRect(6 + offset, 4 + offset, 7, 7)
            painter.fillRect(7 + offset, 5 + offset, 6, 2, QColor(0, 0, 0))
            painter.fillRect(4 + offset, 7 + offset, 2, 2, QColor(0, 0, 0))
            painter.drawRect(4 + offset, 7 + offset, 7, 6)
        elif self.role == "close":
            for delta in range(2):
                painter.drawLine(
                    5 + offset + delta,
                    5 + offset,
                    12 + offset,
                    12 + offset - delta,
                )
                painter.drawLine(
                    12 + offset - delta,
                    5 + offset,
                    5 + offset,
                    12 + offset - delta,
                )
        painter.restore()
        painter.end()


class Win2000TitleBar(QWidget):
    """Windows 2000 caption bar with native system move behavior."""

    def __init__(self, window):
        super().__init__(window)
        self._window = window
        self._drag_offset = None
        self._screen_signal_bound = False
        self.setFixedHeight(22)
        self.setMouseTracking(True)

        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(4, 2, 2, 2)
        self._layout.setSpacing(2)
        self.title_label = QLabel(window.windowTitle())
        self.title_label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        title_font = QFont("MS UI Gothic", 9)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        self._layout.addWidget(self.title_label, 1)

        self.minimize_button = Win2000CaptionButton("minimize", self)
        self.maximize_button = Win2000CaptionButton("maximize", self)
        self.close_button = Win2000CaptionButton("close", self)
        self._layout.addWidget(self.minimize_button)
        self._layout.addWidget(self.maximize_button)
        self._layout.addWidget(self.close_button)

        self.minimize_button.clicked.connect(window.showMinimized)
        self.maximize_button.clicked.connect(self.toggle_maximize)
        close_handler = getattr(window, "reject", window.close)
        self.close_button.clicked.connect(close_handler)
        self.update_screen_metrics()
        self.sync_window_state()

    @staticmethod
    def caption_button_size_for_physical_size(width_mm, height_mm):
        """Choose accessible caption controls from the panel's real diagonal."""
        try:
            width_mm = float(width_mm)
            height_mm = float(height_mm)
        except (TypeError, ValueError):
            return 24
        if width_mm <= 0 or height_mm <= 0:
            return 24
        diagonal_inches = math.hypot(width_mm, height_mm) / 25.4
        if diagonal_inches <= 18.5:
            return 28
        if diagonal_inches <= 22.0:
            return 24
        return 18

    def _current_screen(self):
        handle = self._window.windowHandle()
        if handle is not None and handle.screen() is not None:
            return handle.screen()
        app = QApplication.instance()
        return app.primaryScreen() if app is not None else None

    def update_screen_metrics(self, screen=None):
        screen = screen or self._current_screen()
        physical_size = screen.physicalSize() if screen is not None else QSize()
        button_size = self.caption_button_size_for_physical_size(
            physical_size.width(),
            physical_size.height(),
        )
        for button in (
            self.minimize_button,
            self.maximize_button,
            self.close_button,
        ):
            button.set_caption_size(button_size)
        vertical_margin = 2
        side_margin = max(2, round(button_size / 9))
        self._layout.setContentsMargins(
            max(4, side_margin * 2),
            vertical_margin,
            side_margin,
            vertical_margin,
        )
        self._layout.setSpacing(max(2, round(button_size / 9)))
        self.setFixedHeight(button_size + vertical_margin * 2)
        title_font = QFont("MS UI Gothic", 10 if button_size >= 24 else 9)
        title_font.setBold(True)
        self.title_label.setFont(title_font)

    def _bind_screen_tracking(self):
        if self._screen_signal_bound:
            return
        handle = self._window.windowHandle()
        if handle is None:
            return
        handle.screenChanged.connect(self.update_screen_metrics)
        self._screen_signal_bound = True

    def showEvent(self, event):
        super().showEvent(event)
        self._bind_screen_tracking()
        self.update_screen_metrics()

    def set_title(self, title):
        self.title_label.setText(title)

    def sync_window_state(self):
        self.maximize_button.set_role(
            "restore" if self._window.isMaximized() else "maximize"
        )
        active = self._window.isActiveWindow()
        color = QColor(255, 255, 255) if active else QColor(212, 208, 200)
        palette = self.title_label.palette()
        palette.setColor(QPalette.WindowText, color)
        self.title_label.setPalette(palette)
        self.update()

    def toggle_maximize(self):
        if self._window.isMaximized():
            self._window.showNormal()
        else:
            self._window.showMaximized()
        self.sync_window_state()

    def paintEvent(self, event):
        painter = QPainter(self)
        gradient = QLinearGradient(0, 0, self.width(), 0)
        if self._window.isActiveWindow():
            gradient.setColorAt(0.0, QColor(10, 36, 106))
            gradient.setColorAt(1.0, QColor(166, 202, 240))
        else:
            gradient.setColorAt(0.0, QColor(128, 128, 128))
            gradient.setColorAt(1.0, QColor(192, 192, 192))
        painter.fillRect(self.rect(), gradient)
        painter.end()

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.toggle_maximize()
            event.accept()
            return
        super().mouseDoubleClickEvent(event)

    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton:
            super().mousePressEvent(event)
            return
        if self._window.isMaximized():
            self._drag_offset = None
            event.accept()
            return

        handle = self._window.windowHandle()
        started = bool(
            handle
            and hasattr(handle, "startSystemMove")
            and handle.startSystemMove()
        )
        if not started:
            self._drag_offset = event.globalPos() - self._window.frameGeometry().topLeft()
        event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_offset is not None and event.buttons() & Qt.LeftButton:
            self._window.move(event.globalPos() - self._drag_offset)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_offset = None
        super().mouseReleaseEvent(event)


class Win2000FramelessDialog(QDialog):
    """Reusable frameless dialog with a Windows 2000 non-client frame."""

    FRAME_WIDTH = 4
    RESIZE_MARGIN = 7

    def __init__(self, parent=None):
        super().__init__(parent)
        flags = self.windowFlags()
        flags &= ~Qt.WindowContextHelpButtonHint
        flags |= Qt.FramelessWindowHint | Qt.WindowSystemMenuHint
        flags |= Qt.WindowMinMaxButtonsHint | Qt.WindowCloseButtonHint
        self.setWindowFlags(flags)
        self.setMouseTracking(True)

        self._frame_layout = QVBoxLayout(self)
        self._frame_layout.setContentsMargins(
            self.FRAME_WIDTH,
            self.FRAME_WIDTH,
            self.FRAME_WIDTH,
            self.FRAME_WIDTH,
        )
        self._frame_layout.setSpacing(0)
        self.title_bar = Win2000TitleBar(self)
        self._frame_layout.addWidget(self.title_bar)

        self.client_widget = QWidget(self)
        self.client_widget.setAutoFillBackground(True)
        self.client_layout = QVBoxLayout(self.client_widget)
        self._frame_layout.addWidget(self.client_widget, 1)

    def setWindowTitle(self, title):
        super().setWindowTitle(title)
        if hasattr(self, "title_bar"):
            self.title_bar.set_title(title)

    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() in (QEvent.ActivationChange, QEvent.WindowStateChange):
            margin = 0 if self.isMaximized() else self.FRAME_WIDTH
            self._frame_layout.setContentsMargins(margin, margin, margin, margin)
            self.title_bar.sync_window_state()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(212, 208, 200))
        if self.isMaximized():
            painter.end()
            return
        rect = self.rect().adjusted(0, 0, -1, -1)
        painter.setPen(QColor(255, 255, 255))
        painter.drawLine(rect.left(), rect.top(), rect.right(), rect.top())
        painter.drawLine(rect.left(), rect.top(), rect.left(), rect.bottom())
        painter.setPen(QColor(0, 0, 0))
        painter.drawLine(rect.left(), rect.bottom(), rect.right(), rect.bottom())
        painter.drawLine(rect.right(), rect.top(), rect.right(), rect.bottom())
        inner = rect.adjusted(1, 1, -1, -1)
        painter.setPen(QColor(223, 220, 212))
        painter.drawLine(inner.left(), inner.top(), inner.right(), inner.top())
        painter.drawLine(inner.left(), inner.top(), inner.left(), inner.bottom())
        painter.setPen(QColor(128, 128, 128))
        painter.drawLine(inner.left(), inner.bottom(), inner.right(), inner.bottom())
        painter.drawLine(inner.right(), inner.top(), inner.right(), inner.bottom())
        painter.end()

    def _resize_edges_at(self, pos):
        if self.isMaximized():
            return Qt.Edges()
        margin = self.RESIZE_MARGIN
        edges = Qt.Edges()
        if pos.x() <= margin:
            edges |= Qt.LeftEdge
        elif pos.x() >= self.width() - margin:
            edges |= Qt.RightEdge
        if pos.y() <= margin:
            edges |= Qt.TopEdge
        elif pos.y() >= self.height() - margin:
            edges |= Qt.BottomEdge
        return edges

    @staticmethod
    def _cursor_for_edges(edges):
        if edges in (
            Qt.LeftEdge | Qt.TopEdge,
            Qt.RightEdge | Qt.BottomEdge,
        ):
            return Qt.SizeFDiagCursor
        if edges in (
            Qt.RightEdge | Qt.TopEdge,
            Qt.LeftEdge | Qt.BottomEdge,
        ):
            return Qt.SizeBDiagCursor
        if edges & (Qt.LeftEdge | Qt.RightEdge):
            return Qt.SizeHorCursor
        if edges & (Qt.TopEdge | Qt.BottomEdge):
            return Qt.SizeVerCursor
        return Qt.ArrowCursor

    def mouseMoveEvent(self, event):
        if not event.buttons():
            self.setCursor(self._cursor_for_edges(self._resize_edges_at(event.pos())))
        super().mouseMoveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            edges = self._resize_edges_at(event.pos())
            handle = self.windowHandle()
            if edges and handle and hasattr(handle, "startSystemResize"):
                if handle.startSystemResize(edges):
                    event.accept()
                    return
        super().mousePressEvent(event)


class Win2000FramelessMainWindow(QMainWindow):
    """QMainWindow variant of the reusable Windows 2000 frame."""

    FRAME_WIDTH = Win2000FramelessDialog.FRAME_WIDTH
    RESIZE_MARGIN = Win2000FramelessDialog.RESIZE_MARGIN

    def __init__(self, parent=None):
        super().__init__(parent)
        flags = self.windowFlags()
        flags &= ~Qt.WindowContextHelpButtonHint
        flags |= Qt.FramelessWindowHint | Qt.WindowSystemMenuHint
        flags |= Qt.WindowMinMaxButtonsHint | Qt.WindowCloseButtonHint
        self.setWindowFlags(flags)
        self.setMouseTracking(True)
        self.setContentsMargins(
            self.FRAME_WIDTH,
            self.FRAME_WIDTH,
            self.FRAME_WIDTH,
            self.FRAME_WIDTH,
        )
        self.title_bar = Win2000TitleBar(self)
        self.setMenuWidget(self.title_bar)

    def setWindowTitle(self, title):
        super().setWindowTitle(title)
        if hasattr(self, "title_bar"):
            self.title_bar.set_title(title)

    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() in (QEvent.ActivationChange, QEvent.WindowStateChange):
            margin = 0 if self.isMaximized() else self.FRAME_WIDTH
            self.setContentsMargins(margin, margin, margin, margin)
            self.title_bar.sync_window_state()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(212, 208, 200))
        if self.isMaximized():
            painter.end()
            return
        rect = self.rect().adjusted(0, 0, -1, -1)
        painter.setPen(QColor(255, 255, 255))
        painter.drawLine(rect.left(), rect.top(), rect.right(), rect.top())
        painter.drawLine(rect.left(), rect.top(), rect.left(), rect.bottom())
        painter.setPen(QColor(0, 0, 0))
        painter.drawLine(rect.left(), rect.bottom(), rect.right(), rect.bottom())
        painter.drawLine(rect.right(), rect.top(), rect.right(), rect.bottom())
        inner = rect.adjusted(1, 1, -1, -1)
        painter.setPen(QColor(223, 220, 212))
        painter.drawLine(inner.left(), inner.top(), inner.right(), inner.top())
        painter.drawLine(inner.left(), inner.top(), inner.left(), inner.bottom())
        painter.setPen(QColor(128, 128, 128))
        painter.drawLine(inner.left(), inner.bottom(), inner.right(), inner.bottom())
        painter.drawLine(inner.right(), inner.top(), inner.right(), inner.bottom())
        painter.end()

    def _resize_edges_at(self, pos):
        if self.isMaximized():
            return Qt.Edges()
        margin = self.RESIZE_MARGIN
        edges = Qt.Edges()
        if pos.x() <= margin:
            edges |= Qt.LeftEdge
        elif pos.x() >= self.width() - margin:
            edges |= Qt.RightEdge
        if pos.y() <= margin:
            edges |= Qt.TopEdge
        elif pos.y() >= self.height() - margin:
            edges |= Qt.BottomEdge
        return edges

    def mouseMoveEvent(self, event):
        if not event.buttons():
            self.setCursor(
                Win2000FramelessDialog._cursor_for_edges(
                    self._resize_edges_at(event.pos())
                )
            )
        super().mouseMoveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            edges = self._resize_edges_at(event.pos())
            handle = self.windowHandle()
            if edges and handle and hasattr(handle, "startSystemResize"):
                if handle.startSystemResize(edges):
                    event.accept()
                    return
        super().mousePressEvent(event)


class PreviewWindow:
    """Pygameプレビューウィンドウ(別スレッドで実行)"""

    def __init__(self, command_queue, status_queue):
        self.command_queue = command_queue
        self.status_queue = status_queue
        self.running = False
        self.window = None
        self.virtual_screen = None
        self.clock = None
        self.game_state = None
        self.current_file = None
        self.current_paragraph = 0

        self.window_width = 960
        self.window_height = 540
        self.last_activity_time = pygame.time.get_ticks() if pygame.get_init() else 0

    def initialize_pygame(self):
        """Pygameを初期化"""
        logger.info("Pygame初期化開始")
        try:
            pygame.init()
            pygame.mixer.init()

            self.window = pygame.display.set_mode(
                (self.window_width, self.window_height),
                pygame.RESIZABLE
            )
            pygame.display.set_caption("KSファイル プレビュー(リサイズ可能)")

            self.virtual_screen = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT))
            self.clock = pygame.time.Clock()
            self.status_queue.put(("initialized", True))
            logger.info(f"Pygame初期化完了 (仮想: {VIRTUAL_WIDTH}x{VIRTUAL_HEIGHT})")
            return True
        except Exception as e:
            logger.error(f"Pygame初期化エラー: {e}", exc_info=True)
            self.status_queue.put(("error", str(e)))
            return False

    def initialize_game_state(self):
        """ゲーム状態を初期化"""
        logger.info("ゲーム状態初期化開始")

        from core import config
        config.OFFSET_X = 0
        config.OFFSET_Y = 0
        config.SCALE = 1.0

        try:
            bgm_manager = BGMManager(DEBUG)
            se_manager = SEManager(DEBUG)
            dialogue_loader = DialogueLoader(DEBUG)
            image_manager = ImageManager(DEBUG)
            text_renderer = TextRenderer(self.virtual_screen, DEBUG)
            choice_renderer = ChoiceRenderer(self.virtual_screen, DEBUG)
            notification_manager = NotificationManager(self.virtual_screen, DEBUG)
            backlog_manager = BacklogManager(self.virtual_screen, text_renderer.fonts, DEBUG)

            text_renderer.set_backlog_manager(backlog_manager)
            dialogue_loader.notification_system = notification_manager

            image_manager.scan_image_paths(VIRTUAL_WIDTH, VIRTUAL_HEIGHT)
            images = image_manager.load_essential_images(VIRTUAL_WIDTH, VIRTUAL_HEIGHT)

            game_state = {
                'screen': self.virtual_screen,
                'bgm_manager': bgm_manager,
                'se_manager': se_manager,
                'dialogue_loader': dialogue_loader,
                'image_manager': image_manager,
                'text_renderer': text_renderer,
                'choice_renderer': choice_renderer,
                'backlog_manager': backlog_manager,
                'notification_manager': notification_manager,
                'images': images,
                'dialogue_data': [],
                'ir_data': None,
                'ir_step_index': -1,
                'ir_anim_pending': False,
                'ir_anim_end_time': None,
                'ir_active_anims': [],
                'ir_waiting_for_anim': False,
                'ir_fast_forward_until': None,
        'ir_fast_forward_active': False,
                'use_ir': USE_IR,
                'character_pos': {},
                'character_anim': {},
                'character_zoom': {},
                'character_expressions': {},
                'character_blink_enabled': {},
                'character_blink_state': {},
                'character_blink_timers': {},
                'character_part_fades': {},
                'character_hide_pending': {},
                'fade_state': {
                    'type': None,
                    'start_time': 0,
                    'duration': 0,
                    'color': (0, 0, 0),
                    'alpha': 0,
                    'active': False
                },
                'background_state': {
                    'current_bg': None,
                    'pos': [0, 0],
                    'zoom': 1.0,
                    'anim': None
                },
                'show_face_parts': True,
                'show_text': True,
                'current_paragraph': -1,
                'active_characters': [],
                'last_dialogue_logged': False
            }

            return game_state
        except Exception as e:
            logger.error(f"ゲーム状態初期化エラー: {e}", exc_info=True)
            raise

    def load_event(self, ks_file_path, jump_to_paragraph=None):
        """KSファイルを読み込む"""
        logger.info(f"load_event開始: {ks_file_path}, 段落: {jump_to_paragraph}")
        try:
            self.game_state = self.initialize_game_state()
            if not self.game_state:
                raise Exception("ゲーム状態の初期化に失敗")

            apply_event_datetime(
                self.game_state["text_renderer"],
                ks_file_path=ks_file_path,
            )
            dialogue_loader = self.game_state['dialogue_loader']
            raw_dialogue_data = dialogue_loader.load_dialogue_from_ks(ks_file_path)

            if not raw_dialogue_data:
                raise Exception("ダイアログデータの読み込みに失敗")

            dialogue_data = normalize_dialogue_data(raw_dialogue_data)
            if not dialogue_data:
                raise Exception("ダイアログデータの正規化に失敗")

            self.game_state['ir_data'] = build_ir_from_normalized(dialogue_data)
            self.game_state['ir_step_index'] = -1
            self.game_state['ir_anim_pending'] = False
            self.game_state['ir_anim_end_time'] = None
            self.game_state['ir_active_anims'] = []
            self.game_state['ir_waiting_for_anim'] = False
            self.game_state['ir_fast_forward_until'] = None
            self.game_state['ir_fast_forward_active'] = False
            if IR_DUMP_JSON:
                try:
                    dump_dir = IR_DUMP_DIR
                    if not os.path.isabs(dump_dir):
                        dump_dir = os.path.join(project_root, dump_dir)
                    dump_ir_json(
                        self.game_state['ir_data'],
                        get_ir_dump_path(ks_file_path, dump_dir),
                    )
                    if DEBUG:
                        logger.info(f"IR JSON dumped: {get_ir_dump_path(ks_file_path, dump_dir)}")
                except Exception as e:
                    logger.warning(f"IR JSON dump failed: {e}")

            image_manager = self.game_state['image_manager']
            image_manager.preload_characters_from_dialogue(dialogue_data)

            self.game_state['dialogue_data'] = dialogue_data
            self.game_state['current_paragraph'] = -1

            if jump_to_paragraph is not None and jump_to_paragraph > 0:
                from dialogue.model import advance_dialogue
                for i in range(jump_to_paragraph):
                    if self.game_state['current_paragraph'] < len(dialogue_data) - 1:
                        advance_dialogue(self.game_state)
                self.current_paragraph = self.game_state.get('current_paragraph', 0)
            else:
                from dialogue.model import advance_dialogue
                advance_dialogue(self.game_state)
                self.current_paragraph = self.game_state.get('current_paragraph', 0)

            self.current_file = ks_file_path
            self.status_queue.put(("loaded", True))
            logger.info(f"KSファイル読み込み完了: {ks_file_path}")

        except Exception as e:
            logger.error(f"KSファイル読み込みエラー: {e}", exc_info=True)
            self.status_queue.put(("error", str(e)))
            self.game_state = None

    def reload_current_event(self, keep_position=True):
        """現在のイベントをリロード"""
        if self.current_file:
            if keep_position and self.game_state:
                current_para = self.game_state.get('current_paragraph', 0)
                self.load_event(self.current_file, jump_to_paragraph=current_para)
            else:
                self.load_event(self.current_file)

    def get_scale_and_offset(self):
        """スケーリング係数とオフセットを計算"""
        virtual_screen_width = self.virtual_screen.get_width()
        virtual_screen_height = self.virtual_screen.get_height()

        window_aspect = self.window_width / self.window_height
        virtual_aspect = virtual_screen_width / virtual_screen_height

        if window_aspect > virtual_aspect:
            scale = self.window_height / virtual_screen_height
            scaled_width = int(virtual_screen_width * scale)
            scaled_height = self.window_height
            offset_x = (self.window_width - scaled_width) // 2
            offset_y = 0
        else:
            scale = self.window_width / virtual_screen_width
            scaled_width = self.window_width
            scaled_height = int(virtual_screen_height * scale)
            offset_x = 0
            offset_y = (self.window_height - scaled_height) // 2

        return scale, scaled_width, scaled_height, offset_x, offset_y

    def render_preview(self):
        """プレビュー画面を描画"""
        try:
            if not self.game_state:
                self.virtual_screen.fill((20, 20, 40))
            else:
                if self.game_state.get('screen') != self.virtual_screen:
                    self.game_state['screen'] = self.virtual_screen

                draw_background(self.game_state)
                draw_characters(self.game_state)
                draw_fade_overlay(self.game_state)

                if 'image_manager' in self.game_state:
                    image_manager = self.game_state['image_manager']
                    images = self.game_state['images']
                    show_text = self.game_state.get('show_text', True)
                    image_manager.draw_ui_elements(self.virtual_screen, images, show_text)

                choice_showing = False
                if 'choice_renderer' in self.game_state:
                    choice_renderer = self.game_state['choice_renderer']
                    choice_showing = choice_renderer.is_choice_showing()

                if 'text_renderer' in self.game_state:
                    text_renderer = self.game_state['text_renderer']
                    if not choice_showing:
                        text_renderer.render_text_window(self.game_state)
                    else:
                        # 選択肢表示中はトーク文を隠し、日付時刻だけ表示
                        text_renderer.render_date()

                if choice_showing:
                    choice_renderer.render()

                if 'notification_manager' in self.game_state:
                    notification_manager = self.game_state['notification_manager']
                    notification_manager.render()

                draw_input_blocked_notice(self.game_state, self.virtual_screen)

                if 'backlog_manager' in self.game_state:
                    backlog_manager = self.game_state['backlog_manager']
                    backlog_manager.render()

            scale, scaled_width, scaled_height, offset_x, offset_y = self.get_scale_and_offset()
            self.window.fill((0, 0, 0))

            if scaled_width > 0 and scaled_height > 0:
                scaled_surface = pygame.transform.smoothscale(
                    self.virtual_screen,
                    (scaled_width, scaled_height)
                )
                self.window.blit(scaled_surface, (offset_x, offset_y))

        except Exception as e:
            logger.error(f"render_preview エラー: {e}", exc_info=True)

    def run(self):
        """プレビューウィンドウのメインループ"""
        logger.info("プレビューウィンドウ起動開始")

        try:
            if not self.initialize_pygame():
                return

            self.running = True
            logger.info("メインループ開始")

            while self.running:
                try:
                    # コマンドキューをチェック
                    try:
                        command = self.command_queue.get_nowait()
                        cmd_type = command.get('type')

                        if cmd_type == 'load':
                            ks_file = command.get('file')
                            jump_to = command.get('jump_to_paragraph')
                            self.load_event(ks_file, jump_to_paragraph=jump_to)
                        elif cmd_type == 'reload':
                            keep_pos = command.get('keep_position', True)
                            self.reload_current_event(keep_position=keep_pos)
                        elif cmd_type == 'jump':
                            paragraph_num = command.get('paragraph')
                            if paragraph_num is not None and self.game_state:
                                self.load_event(self.current_file, jump_to_paragraph=paragraph_num)
                        elif cmd_type == 'stop':
                            self.running = False
                    except queue.Empty:
                        pass

                    # イベント処理
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            self.running = False
                            self.status_queue.put(("quit", True))
                        elif event.type == pygame.VIDEORESIZE:
                            self.window_width = event.w
                            self.window_height = event.h
                            self.window = pygame.display.set_mode(
                                (self.window_width, self.window_height),
                                pygame.RESIZABLE
                            )

                    # ゲーム状態を更新
                    if self.game_state:
                        old_paragraph = self.current_paragraph
                        handle_dialogue_events(self.game_state, self.virtual_screen)
                        update_game(self.game_state)

                        new_paragraph = self.game_state.get('current_paragraph', 0)
                        if new_paragraph != old_paragraph:
                            self.current_paragraph = new_paragraph
                            self.status_queue.put(("paragraph_update", new_paragraph))

                    # 描画
                    self.render_preview()
                    pygame.display.flip()
                    self.clock.tick(30)

                except Exception as e:
                    logger.error(f"メインループ内エラー: {e}", exc_info=True)

            logger.info("メインループ終了")

        except Exception as e:
            logger.critical(f"プレビューウィンドウの致命的エラー: {e}", exc_info=True)
        finally:
            pygame.quit()
            self.status_queue.put(("stopped", True))


class StatusSignal(QObject):
    """シグナル用のQObject"""
    status_received = pyqtSignal(str, object)


class PreviewSignal(QObject):
    """プレビュー生成完了通知用のQObject"""
    preview_ready = pyqtSignal(object, str, bool, str)


# ---------------------------------------------------------------------------
# 立ち絵合成プレビュー — CharaPreviewCanvas / CharaCompositePreviewDialog
# ---------------------------------------------------------------------------

class CharaPreviewCanvas(QWidget):
    """ズーム・パン可能な立ち絵合成プレビューキャンバス"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._image = None
        self._scale = 1.0
        self._offset_x = 0
        self._offset_y = 0
        self._drag_start = None
        self.setMinimumSize(300, 400)
        self.setStyleSheet("background: #1e1e1e;")
        self.setMouseTracking(True)

    def set_image(self, qimage, reset_view=False):
        """画像を設定。reset_view=True の時だけズーム・パンをリセット。"""
        first_load = self._image is None and qimage is not None
        self._image = qimage
        if (first_load or reset_view) and qimage and not qimage.isNull():
            w_ratio = self.width() / max(qimage.width(), 1)
            h_ratio = self.height() / max(qimage.height(), 1)
            self._scale = min(w_ratio, h_ratio) * 0.9
            self._offset_x = 0
            self._offset_y = 0
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(30, 30, 30))
        if not self._image or self._image.isNull():
            painter.setPen(QColor(120, 120, 120))
            painter.drawText(self.rect(), Qt.AlignCenter, "画像なし / ファイルIDを入力してください")
            return
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        w = int(self._image.width() * self._scale)
        h = int(self._image.height() * self._scale)
        x = (self.width() - w) // 2 + self._offset_x
        y = (self.height() - h) // 2 + self._offset_y
        painter.drawImage(QRect(x, y, w, h), self._image)

    def wheelEvent(self, event):
        factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        self._scale = max(0.02, min(10.0, self._scale * factor))
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_start = (event.x() - self._offset_x, event.y() - self._offset_y)

    def mouseMoveEvent(self, event):
        if self._drag_start:
            self._offset_x = event.x() - self._drag_start[0]
            self._offset_y = event.y() - self._drag_start[1]
            self.update()

    def mouseReleaseEvent(self, event):
        self._drag_start = None

    def resizeEvent(self, event):
        if self._image and not self._image.isNull():
            w_ratio = self.width() / max(self._image.width(), 1)
            h_ratio = self.height() / max(self._image.height(), 1)
            self._scale = min(w_ratio, h_ratio) * 0.9
        super().resizeEvent(event)


class CharaCompositePreviewDialog(QDialog):
    """立ち絵合成プレビュー・パーツ選択ダイアログ

    chara_show / chara_shift 編集時に開く。
    左: レイヤー合成プレビュー（ズーム・パン対応）
    右: コンボボックスによるパーツ選択（リアルタイムプレビュー）
         - トルソー選択時に顔パーツ(brow/eye/mouth/cheek)をFXX番号でフィルタ
         - 不一致パーツは⚠️付き黄色ハイライト
    """

    # 描画レイヤー順（下から上）
    LAYER_ORDER = ['torso', 'brow', 'cheek', 'eye', 'mouth', 'accessory', 'effect']
    PART_LABELS = {
        'torso':     '体 (T)',
        'brow':      '眉 (BRO)',
        'cheek':     '頬 (CHE)',
        'eye':       '目 (EYE)',
        'mouth':     '口 (MOU)',
        'effect':    'エフェクト (E)',
        'accessory': '装飾 (A)',
    }
    # トルソー番号に依存する顔パーツ (FXX番号フィルタ)
    FACE_PARTS = {'brow', 'cheek', 'eye', 'mouth'}
    # effect/accessory もトルソー番号連動（E0x / A0x）
    TORSO_LINKED_PARTS = {'brow', 'cheek', 'eye', 'mouth', 'effect', 'accessory'}

    def __init__(self, parent, image_manager, initial_fields,
                 char_name, is_shift=False, prev_fields=None,
                 char_name_options=None, require_name=False,
                 state_by_name=None, action_overrides=None,
                 template_store=None, step_speaker="", step_body="",
                 step_force_female=False):
        super().__init__(parent)
        self._image_manager = image_manager
        self._fields = {p: initial_fields.get(p, '') for p in self.LAYER_ORDER}
        self._char_name = (char_name or '').strip()
        self._is_shift = is_shift
        self._prev_fields = {p: (prev_fields or {}).get(p, '') for p in self.LAYER_ORDER}
        self._char_name_options = list(dict.fromkeys(
            name for name in (char_name_options or []) if name and str(name).strip()
        ))
        self._require_name = require_name
        self._state_by_name = {
            (name or '').strip(): {part: fields.get(part, '') for part in self.LAYER_ORDER}
            for name, fields in (state_by_name or {}).items()
            if (name or '').strip()
        }
        self._action_overrides = {
            part: (action_overrides or {}).get(part, '')
            for part in self.LAYER_ORDER
        }
        self._prev_fields = self._sanitize_fields_for_character(self._prev_fields)
        self._fields = self._sanitize_fields_for_character(self._fields)
        self._action_overrides = self._sanitize_fields_for_character(self._action_overrides)
        self._blink = str(initial_fields.get('blink', 'true')).lower() != 'false'
        self._prev_blink = str((prev_fields or {}).get('blink', 'true')).lower() != 'false'
        self._template_store = template_store or CharaPartTemplateStore(
            os.path.join(project_root, "editor_data", "chara_part_templates.json")
        )
        self._applied_template_name = ""
        self._step_speaker = (step_speaker or "").strip()
        self._step_body = (step_body or "").strip()
        self._step_force_female = bool(step_force_female)
        self._apply_btn = None
        self._name_combo = None
        self._template_combo = None
        self._blink_combo = None

        self.setWindowTitle(f"立ち絵プレビュー: {self._char_name or '未選択'}")
        self.resize(1200, 780)
        self._build_ui()
        self._update_preview()

    # ------------------------------------------------------------------
    # ヘルパー
    # ------------------------------------------------------------------

    def _get_face_num(self, torso_stem):
        """トルソーのステムから対応するFXX番号を返す。例: MMK_T01_... → '01'"""
        m = re.search(r'_T(\d+)', torso_stem)
        return m.group(1) if m else None

    def _get_char_options(self, part):
        """パーツカテゴリから、このキャラのステム一覧を返す（全件）"""
        from core.config import CHAR_CODE
        if self._require_name and not self._char_name:
            return []
        code = CHAR_CODE.get(self._char_name, '')
        paths = self._image_manager.image_paths.get(part, {})
        if code:
            return sorted(k for k in paths if k.startswith(code + '_'))
        return sorted(paths.keys())

    def _sanitize_fields_for_character(self, fields):
        """選択中キャラクター以外のパーツ値を除外する。"""
        from core.config import CHAR_CODE

        code = CHAR_CODE.get(self._char_name, '')
        if not code:
            return dict(fields)
        prefix = code + '_'
        return {
            part: value if not str(value).strip() or str(value).strip().startswith(prefix) else ''
            for part, value in fields.items()
        }

    def _sync_apply_enabled(self):
        if self._apply_btn:
            self._apply_btn.setEnabled(bool(self._char_name.strip()))

    def _compose_fields_for_name(self, char_name):
        base_fields = {
            part: self._state_by_name.get((char_name or '').strip(), {}).get(part, '')
            for part in self.LAYER_ORDER
        }
        merged = dict(base_fields)
        for part, value in self._action_overrides.items():
            if str(value).strip():
                merged[part] = value
        return (
            self._sanitize_fields_for_character(base_fields),
            self._sanitize_fields_for_character(merged),
        )

    def _get_filtered_options(self, part):
        """トルソー番号でフィルタした選択肢を返す。
        FACE_PARTS: _F{num}_ フィルタ
        effect:     _E{num}_ フィルタ
        accessory:  _A{num}_ フィルタ
        マッチなければ全件返却。
        """
        all_opts = self._get_char_options(part)
        torso = self._fields.get('torso', '')
        face_num = self._get_face_num(torso) if torso else None
        if face_num is None or part not in self.TORSO_LINKED_PARTS:
            return all_opts
        if part in self.FACE_PARTS:
            pattern = f'_F{face_num}_'
        elif part == 'effect':
            pattern = f'_E{face_num}_'
        elif part == 'accessory':
            pattern = f'_A{face_num}_'
        else:
            return all_opts
        filtered = [k for k in all_opts if pattern in k]
        return filtered if filtered else all_opts

    def _combo_style_for(self, part, current_text):
        """コンボのスタイルシートを決定する"""
        # ⚠️ 不一致（トルソー番号とパーツ番号不一致）
        if part in self.TORSO_LINKED_PARTS and current_text.strip():
            torso = self._fields.get('torso', '')
            face_num = self._get_face_num(torso) if torso else None
            if face_num:
                if part in self.FACE_PARTS:
                    pattern = f'_F{face_num}_'
                elif part == 'effect':
                    pattern = f'_E{face_num}_'
                elif part == 'accessory':
                    pattern = f'_A{face_num}_'
                else:
                    pattern = None
                if pattern and pattern not in current_text:
                    return 'mismatch'
        # chara_shift: 変更あり
        if self._is_shift and current_text.strip() != self._prev_fields.get(part, ''):
            return 'changed'
        return 'normal'

    def _apply_combo_style(self, combo, label_widget, style_key, part):
        if style_key == 'mismatch':
            combo.setStyleSheet("QComboBox { background: #4a3a00; border: 1px solid #ffcc00; }")
            label_widget.setText('⚠️ ' + self.PART_LABELS[part])
        elif style_key == 'changed':
            combo.setStyleSheet("QComboBox { background: #2a4a2a; }")
            label_widget.setText(self.PART_LABELS[part])
        else:
            combo.setStyleSheet("")
            label_widget.setText(self.PART_LABELS[part])

    # ------------------------------------------------------------------
    # UI構築
    # ------------------------------------------------------------------

    def _build_ui(self):
        main_layout = QHBoxLayout(self)
        splitter = QSplitter(Qt.Horizontal)

        # --- 左: プレビューキャンバス + 現在stepのセリフ ---
        preview_panel = QWidget()
        preview_layout = QVBoxLayout(preview_panel)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        self.canvas = CharaPreviewCanvas()
        preview_layout.addWidget(self.canvas, 1)

        dialogue_group = QGroupBox("このstepのセリフ")
        dialogue_layout = QVBoxLayout(dialogue_group)
        self.dialogue_speaker_label = QLabel(self._step_speaker or "（話者なし）")
        self.dialogue_speaker_label.setObjectName("charaPreviewSpeaker")
        self.dialogue_body_label = QLabel(self._step_body or "（セリフなし）")
        self.dialogue_body_label.setObjectName("charaPreviewBody")
        self.dialogue_body_label.setWordWrap(True)
        text_color = "#d00070" if self._step_force_female else "#202020"
        self.dialogue_speaker_label.setStyleSheet(f"font-weight: bold; color: {text_color};")
        self.dialogue_body_label.setStyleSheet(f"color: {text_color};")
        dialogue_layout.addWidget(self.dialogue_speaker_label)
        dialogue_layout.addWidget(self.dialogue_body_label)
        preview_layout.addWidget(dialogue_group)
        splitter.addWidget(preview_panel)

        # --- 右: パーツ選択パネル ---
        right = QWidget()
        right_layout = QVBoxLayout(right)

        parts_group = QGroupBox("パーツ選択")
        parts_form = QFormLayout(parts_group)

        self._combos = {}
        self._label_widgets = {}

        self._name_combo = QComboBox()
        self._name_combo.setEditable(True)
        self._name_combo.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)
        self._name_combo.addItems(self._char_name_options)
        self._name_combo.setCurrentText(self._char_name)
        if self._name_combo.lineEdit():
            self._name_combo.lineEdit().setPlaceholderText("先にキャラクター名を入力または選択")
        self._name_combo.currentTextChanged.connect(self._on_name_changed)
        parts_form.addRow("name", self._name_combo)

        template_group = QGroupBox("キャラパーツテンプレート（保存・呼び出し）")
        template_layout = QVBoxLayout(template_group)
        template_help = QLabel("体・表情・装飾・blinkを保存します（位置・サイズは含みません）")
        template_help.setStyleSheet("color: #888;")
        template_layout.addWidget(template_help)
        self._template_combo = QComboBox()
        self._template_combo.setObjectName("partTemplateCombo")
        template_layout.addWidget(self._template_combo)
        template_primary_buttons = QHBoxLayout()
        template_manage_buttons = QHBoxLayout()
        load_template_btn = QPushButton("選択テンプレを呼び出し")
        save_template_btn = QPushButton("現在のパーツを保存")
        rename_template_btn = QPushButton("名前変更")
        duplicate_template_btn = QPushButton("複製")
        delete_template_btn = QPushButton("削除")
        load_template_btn.setObjectName("loadPartTemplateButton")
        save_template_btn.setObjectName("savePartTemplateButton")
        load_template_btn.clicked.connect(self._apply_selected_template)
        save_template_btn.clicked.connect(self._save_current_template)
        rename_template_btn.clicked.connect(self._rename_selected_template)
        duplicate_template_btn.clicked.connect(self._duplicate_selected_template)
        delete_template_btn.clicked.connect(self._delete_selected_template)
        template_primary_buttons.addWidget(load_template_btn)
        template_primary_buttons.addWidget(save_template_btn)
        template_manage_buttons.addWidget(rename_template_btn)
        template_manage_buttons.addWidget(duplicate_template_btn)
        template_manage_buttons.addWidget(delete_template_btn)
        template_layout.addLayout(template_primary_buttons)
        template_layout.addLayout(template_manage_buttons)
        parts_form.addRow(template_group)
        self._refresh_template_combo()

        for part in self.LAYER_ORDER:
            current_val = self._fields[part]

            # コンボボックス（編集可能 = キーボード検索も可）
            combo = QComboBox()
            combo.setEditable(True)
            combo.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)
            combo.addItem('')  # 空選択

            opts = (self._get_filtered_options(part)
                    if part in self.TORSO_LINKED_PARTS
                    else self._get_char_options(part))
            combo.addItems(opts)

            # 現在値をセット
            idx = combo.findText(current_val)
            if idx >= 0:
                combo.setCurrentIndex(idx)
            elif current_val:
                combo.setCurrentText(current_val)

            combo.currentTextChanged.connect(
                lambda text, p=part: self._on_field_changed(p, text))
            self._combos[part] = combo

            # ラベル（スタイル変更でアイコンを出す）
            label = QLabel(self.PART_LABELS[part])
            self._label_widgets[part] = label

            style_key = self._combo_style_for(part, current_val)
            self._apply_combo_style(combo, label, style_key, part)

            parts_form.addRow(label, combo)

        self._blink_combo = QComboBox()
        self._blink_combo.addItems(['true', 'false'])
        self._blink_combo.setCurrentText('true' if self._blink else 'false')
        self._blink_combo.currentTextChanged.connect(
            lambda value: setattr(self, '_blink', value == 'true')
        )
        parts_form.addRow('blink', self._blink_combo)

        right_layout.addWidget(parts_group)

        # chara_shift: 差分のみ適用オプション
        self._diff_only = None
        if self._is_shift:
            self._diff_only = QCheckBox('変更パーツのみをタグに適用（差分自動検出）')
            self._diff_only.setChecked(True)
            right_layout.addWidget(self._diff_only)

        # ボタン行
        btn_layout = QHBoxLayout()
        self._apply_btn = QPushButton('✅ スクリプトに適用')
        self._apply_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton('キャンセル')
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self._apply_btn)
        btn_layout.addWidget(cancel_btn)
        right_layout.addLayout(btn_layout)
        right_layout.addStretch()

        splitter.addWidget(right)
        splitter.setSizes([750, 450])
        main_layout.addWidget(splitter)
        self._sync_apply_enabled()

    # ------------------------------------------------------------------
    # イベントハンドラ
    # ------------------------------------------------------------------

    def _on_name_changed(self, text):
        self._char_name = text.strip()
        self._applied_template_name = ""
        self._prev_fields, self._fields = self._compose_fields_for_name(self._char_name)
        self.setWindowTitle(f"立ち絵プレビュー: {self._char_name or '未選択'}")
        self._refresh_all_combos()
        self._refresh_template_combo()
        self._sync_apply_enabled()

    def _refresh_template_combo(self, selected_id=None):
        if self._template_combo is None:
            return
        self._template_combo.blockSignals(True)
        self._template_combo.clear()
        for template in self._template_store.for_character(self._char_name):
            self._template_combo.addItem(template.get('name', ''), template)
        if selected_id:
            for index in range(self._template_combo.count()):
                item = self._template_combo.itemData(index) or {}
                if item.get('id') == selected_id:
                    self._template_combo.setCurrentIndex(index)
                    break
        self._template_combo.blockSignals(False)

    def _selected_template(self):
        if self._template_combo is None or self._template_combo.currentIndex() < 0:
            return None
        return self._template_combo.currentData()

    def _apply_selected_template(self):
        template = self._selected_template()
        if not template:
            return
        self._applied_template_name = str(template.get('name', '')).strip()
        self._fields = self._sanitize_fields_for_character(template.get('parts', {}))
        self._blink = bool(template.get('blink', True))
        if self._blink_combo is not None:
            self._blink_combo.setCurrentText('true' if self._blink else 'false')
        self._refresh_all_combos()

    def _save_current_template(self):
        if not self._char_name:
            QMessageBox.warning(self, "テンプレート保存", "先にキャラクターを選択してください")
            return
        matching = self._template_store.find_matching_parts(
            self._char_name,
            self._fields,
            self._blink,
        )
        if matching:
            QMessageBox.information(
                self,
                "テンプレート保存",
                f"現在のパターンは既存テンプレート「{matching.get('name', '')}」と同じです。\n"
                "新しいテンプレートは作成されません。",
            )
            return
        name, accepted = QInputDialog.getText(self, "テンプレート保存", "テンプレート名")
        if not accepted or not name.strip():
            return
        try:
            template = self._template_store.create(
                name, self._char_name, self._fields, self._blink
            )
        except (OSError, ValueError) as exc:
            QMessageBox.critical(self, "テンプレート保存", str(exc))
            return
        self._refresh_template_combo(template.get('id'))

    def _rename_selected_template(self):
        template = self._selected_template()
        if not template:
            return
        name, accepted = QInputDialog.getText(
            self,
            "テンプレート名変更",
            "新しい名前",
            text=template.get('name', ''),
        )
        if not accepted or not name.strip():
            return
        try:
            updated = self._template_store.rename(template.get('id'), name)
        except (OSError, ValueError) as exc:
            QMessageBox.critical(self, "テンプレート名変更", str(exc))
            return
        self._refresh_template_combo(updated.get('id') if updated else None)

    def _duplicate_selected_template(self):
        template = self._selected_template()
        if not template:
            return
        name, accepted = QInputDialog.getText(
            self,
            "テンプレート複製",
            "複製後の名前",
            text=f"{template.get('name', '')} コピー",
        )
        if not accepted or not name.strip():
            return
        try:
            duplicated = self._template_store.duplicate(template.get('id'), name)
        except (OSError, ValueError) as exc:
            QMessageBox.critical(self, "テンプレート複製", str(exc))
            return
        self._refresh_template_combo(duplicated.get('id') if duplicated else None)

    def _delete_selected_template(self):
        template = self._selected_template()
        if not template:
            return
        reply = QMessageBox.question(
            self,
            "テンプレート削除",
            f"「{template.get('name', '')}」を削除しますか？",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        try:
            self._template_store.delete(template.get('id'))
        except OSError as exc:
            QMessageBox.critical(self, "テンプレート削除", str(exc))
            return
        self._refresh_template_combo()

    def _on_field_changed(self, part, text):
        self._fields[part] = text.strip()

        combo = self._combos[part]
        label = self._label_widgets[part]
        style_key = self._combo_style_for(part, text)
        self._apply_combo_style(combo, label, style_key, part)

        # トルソー変更 → 顔パーツをFXX番号でフィルタし直す
        if part == 'torso':
            self._refresh_face_combos()

        self._update_preview()

    def _refresh_all_combos(self):
        for part in self.LAYER_ORDER:
            combo = self._combos[part]
            label = self._label_widgets[part]
            current = self._fields.get(part, '')
            opts = (self._get_filtered_options(part)
                    if part in self.TORSO_LINKED_PARTS
                    else self._get_char_options(part))
            combo.blockSignals(True)
            combo.clear()
            combo.addItem('')
            combo.addItems(opts)
            idx = combo.findText(current)
            if idx >= 0:
                combo.setCurrentIndex(idx)
            elif current.strip():
                combo.setCurrentText(current)
            combo.blockSignals(False)
            style_key = self._combo_style_for(part, current)
            self._apply_combo_style(combo, label, style_key, part)
        self._update_preview()

    def _refresh_face_combos(self):
        """トルソー変更後、顔パーツのコンボを再フィルタ。
        現在値がリストにない場合は⚠️ハイライト。
        """
        for part in self.TORSO_LINKED_PARTS:
            combo = self._combos[part]
            label = self._label_widgets[part]
            current = combo.currentText()

            new_opts = self._get_filtered_options(part)

            combo.blockSignals(True)
            combo.clear()
            combo.addItem('')
            combo.addItems(new_opts)

            idx = combo.findText(current)
            if idx >= 0:
                combo.setCurrentIndex(idx)
            elif current.strip():
                combo.setCurrentText(current)  # リストにないが保持

            combo.blockSignals(False)

            # スタイル再適用（不一致チェック含む）
            style_key = self._combo_style_for(part, current)
            self._apply_combo_style(combo, label, style_key, part)

    # ------------------------------------------------------------------
    # プレビュー合成
    # ------------------------------------------------------------------

    def _update_preview(self):
        result = None
        for part in self.LAYER_ORDER:
            file_id = self._fields.get(part, '').strip()
            if not file_id:
                continue
            paths = self._image_manager.image_paths.get(part, {})
            path = paths.get(file_id)
            if not path or not os.path.exists(path):
                continue
            img = QImage(path)
            if img.isNull():
                # Fallback to pygame loading for WebP support in Qt5
                try:
                    surf = pygame.image.load(path)
                    try:
                        rgba_data = pygame.image.tobytes(surf, "RGBA")
                    except AttributeError:
                        rgba_data = pygame.image.tostring(surf, "RGBA")
                    w, h = surf.get_size()
                    img = QImage(rgba_data, w, h, QImage.Format_RGBA8888).copy()
                except Exception as e:
                    logger.error(f"Fallback pygame loading failed for {path}: {e}")
                    continue
            if img.isNull():
                continue
            img = img.convertToFormat(QImage.Format_ARGB32)
            if result is None:
                result = QImage(img.size(), QImage.Format_ARGB32)
                result.fill(0)
            painter = QPainter(result)
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
            painter.drawImage(0, 0, img)
            painter.end()
        self.canvas.set_image(result)

    # ------------------------------------------------------------------
    # 結果取得
    # ------------------------------------------------------------------

    def get_result_fields(self):
        """スクリプトに適用するフィールド辞書を返す。
        chara_shift 且つ差分のみモードの場合は変更パーツのみ。
        """
        result_name = self._char_name.strip()
        if self._diff_only and self._diff_only.isChecked():
            result = {
                p: v for p, v in self._fields.items()
                if v.strip() != self._prev_fields.get(p, '').strip()
            }
            if self._blink != self._prev_blink:
                result['blink'] = 'true' if self._blink else 'false'
            if result_name:
                result['name'] = result_name
            if self._is_shift and self._applied_template_name:
                result['template'] = self._applied_template_name
            return result
        result = dict(self._fields)
        result['blink'] = 'true' if self._blink else 'false'
        if result_name:
            result['name'] = result_name
        if self._is_shift and self._applied_template_name:
            result['template'] = self._applied_template_name
        return result


# ---------------------------------------------------------------------------


class StepSlideViewport(QWidget):
    """Keep the step editor alive while giving step changes a short slide."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.content = QWidget(self)
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self._animation = None
        self._old_frame = None

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if not self._animation or self._animation.state() != self._animation.Running:
            self.content.setGeometry(self.rect())

    def capture_content(self):
        if not self.isVisible() or self.width() <= 0 or self.height() <= 0:
            return QPixmap()
        return self.content.grab()

    def slide_in(self, direction, previous_pixmap=None):
        """Slide the new content in from the navigation direction."""
        if direction not in (-1, 1) or self.width() <= 0:
            self.content.setGeometry(self.rect())
            return

        if self._animation and self._animation.state() == self._animation.Running:
            self._animation.stop()
        if self._old_frame:
            self._old_frame.deleteLater()
            self._old_frame = None

        # Treat adjacent steps as full pages on one continuous horizontal roll:
        # the old page leaves by one viewport width while the new page enters
        # from the immediately adjoining position.
        distance = self.width()
        self.content.resize(self.size())
        self.content.move(direction * distance, 0)
        self.content.show()
        self.content.raise_()

        old_frame = None
        if previous_pixmap is not None and not previous_pixmap.isNull():
            old_frame = QLabel(self)
            old_frame.setPixmap(previous_pixmap)
            old_frame.setScaledContents(True)
            old_frame.setGeometry(self.rect())
            old_frame.show()
            old_frame.raise_()
            self._old_frame = old_frame

        group = QParallelAnimationGroup(self)
        incoming = QPropertyAnimation(self.content, b"pos", group)
        incoming.setDuration(140)
        incoming.setStartValue(QPoint(direction * distance, 0))
        incoming.setEndValue(QPoint(0, 0))
        incoming.setEasingCurve(QEasingCurve.InOutCubic)
        group.addAnimation(incoming)

        if old_frame is not None:
            outgoing = QPropertyAnimation(old_frame, b"pos", group)
            outgoing.setDuration(140)
            outgoing.setStartValue(QPoint(0, 0))
            outgoing.setEndValue(QPoint(-direction * distance, 0))
            outgoing.setEasingCurve(QEasingCurve.InOutCubic)
            group.addAnimation(outgoing)

        def finish_animation():
            self.content.setGeometry(self.rect())
            if self._old_frame:
                self._old_frame.deleteLater()
                self._old_frame = None
            self._animation = None

        group.finished.connect(finish_animation)
        self._animation = group
        group.start()


class StepEditorDialog(Win2000FramelessDialog):
    """step編集用ダイアログ"""

    CHARA_PREVIEW_PARTS = tuple(CharaCompositePreviewDialog.LAYER_ORDER)

    TAG_NAMES = [
        "bg",
        "bg_show",
        "bg_move",
        "chara_show",
        "chara_shift",
        "chara_move",
        "chara_hide",
        "bgm",
        "bgmend",
        "bgmstop",
        "bgmstart",
        "se",
        "sestop",
        "fadeout",
        "fadein",
        "choice",
        "flag_set",
        "if",
        "endif",
        "event_control",
    ]
    PARAM_TEMPLATES = {
        "bg": [("storage", "")],
        "bg_show": [("storage", ""), ("bg_x", "0.5"), ("bg_y", "0.5"), ("bg_zoom", "1.0")],
        "bg_move": [("storage", ""), ("bg_left", "0.0"), ("bg_top", "0.0"), ("bg_zoom", "1.0"), ("time", "600")],
        "chara_show": [
            ("name", ""),
            ("template", ""),
            ("torso", ""),
            ("eye", ""),
            ("mouth", ""),
            ("brow", ""),
            ("cheek", ""),
            ("effect", ""),
            ("accessory", ""),
            ("blink", "true"),
            ("x", "0.5"),
            ("y", "0.5"),
            ("size", "1.0"),
            ("fade", "0.15"),
        ],
        "chara_shift": [
            ("name", ""),
            ("template", ""),
            ("torso", ""),
            ("eye", ""),
            ("mouth", ""),
            ("brow", ""),
            ("cheek", ""),
            ("effect", ""),
            ("accessory", ""),
            ("x", ""),
            ("y", ""),
            ("size", ""),
            ("fade", "0.15"),
        ],
        "chara_move": [("name", ""), ("left", "0.0"), ("top", "0.0"), ("zoom", "1.0"), ("time", "600")],
        "chara_hide": [("name", ""), ("fade", "0.15")],
        "bgm": [("bgm", ""), ("volume", "0.5"), ("loop", "true"), ("fade", "0.0")],
        "bgmend": [("time", "1.0")],
        "bgmstop": [("time", "1.0")],
        "bgmstart": [("time", "1.0")],
        "se": [("se", ""), ("volume", "0.5"), ("frequency", "1"), ("block", "false")],
        "sestop": [],
        "sewait": [],
        "fadeout": [("color", "black"), ("time", "1.0")],
        "fadein": [("time", "1.0")],
        "choice": [("option1", ""), ("option2", "")],
        "flag_set": [("name", ""), ("value", "")],
        "if": [("condition", "")],
        "event_control": [("unlock", ""), ("lock", "")],
    }
    CUSTOM_EDITORS = {
        "bg": [("storage", "storage", "bg_asset")],
        "bg_show": [
            ("storage", "storage", "bg_asset"),
            ("bg_x", "bg_x", "text"),
            ("bg_y", "bg_y", "text"),
            ("bg_zoom", "bg_zoom", "text"),
        ],
        "bg_move": [
            ("storage", "storage", "bg_asset"),
            ("bg_left", "bg_left", "text"),
            ("bg_top", "bg_top", "text"),
            ("bg_zoom", "bg_zoom", "text"),
            ("time", "time", "text"),
        ],
        "chara_show": [
            ("name", "name", "text"),
            ("template", "template", "text"),
            ("torso", "torso", "text"),
            ("eye", "eye", "text"),
            ("mouth", "mouth", "text"),
            ("brow", "brow", "text"),
            ("cheek", "cheek", "text"),
            ("effect", "effect", "text"),
            ("accessory", "accessory", "text"),
            ("blink", "blink", "bool"),
            ("x", "x", "text"),
            ("y", "y", "text"),
            ("size", "size", "text"),
            ("fade", "fade", "text"),
        ],
        "chara_shift": [
            ("name", "name", "text"),
            ("template", "template", "text"),
            ("torso", "torso", "text"),
            ("eye", "eye", "text"),
            ("mouth", "mouth", "text"),
            ("brow", "brow", "text"),
            ("cheek", "cheek", "text"),
            ("effect", "effect", "text"),
            ("accessory", "accessory", "text"),
            ("x", "x", "text"),
            ("y", "y", "text"),
            ("size", "size", "text"),
            ("fade", "fade", "text"),
        ],
        "chara_move": [
            ("name", "name", "text"),
            ("left", "left", "text"),
            ("top", "top", "text"),
            ("zoom", "zoom", "text"),
            ("time", "time", "text"),
        ],
        "chara_hide": [
            ("name", "name", "text"),
            ("fade", "fade", "text"),
        ],
        "bgm": [
            ("bgm", "bgm", "bgm_asset"),
            ("volume", "volume", "volume_slider"),
            ("loop", "loop", "bool"),
            ("fade", "fade", "text"),
        ],
        "se": [
            ("se", "se", "se_asset"),
            ("volume", "volume", "volume_slider"),
            ("frequency", "frequency", "text"),
            ("block", "block", "bool"),
        ],
    }
    # storage → BGディレクトリ、キャラクターパーツ → キャラクターディレクトリ (01MMK 等) 内
    BROWSE_KEYS = {
        "storage":   "BG",
        "torso":     "char",
        "eye":       "char",
        "mouth":     "char",
        "brow":      "char",
        "cheek":     "char",
        "effect":    "char",
        "accessory": "char",
    }

    def __init__(
        self,
        parent,
        step,
        actions=None,
        all_steps=None,
        all_step_actions=None,
        step_index=None,
        image_manager=None,
    ):
        super().__init__(parent)
        self.step = step or {}
        self.actions = actions or []
        self._all_steps = all_steps or []
        self._all_step_actions = all_step_actions or []
        self._step_index = step_index
        self._image_manager = image_manager
        self._scene_state_builder = StepSceneStateBuilder(image_manager)
        self._loading_step = True
        self._baseline_signature = None
        self._outline_navigation = False
        self.navigation_offset = 0
        self._direct_scene_edit = False
        self._bgm_preview_manager = None
        self._se_preview_manager = None
        self._volume_sliders = {}
        # Keep recently visited final renders in memory.  The interactive scene
        # already changes immediately; this avoids restarting snapshot work
        # when the user pages back to an unchanged step.
        self._final_preview_cache = OrderedDict()
        self._final_preview_cache_limit = 24

        self.setWindowTitle("step編集")
        self.resize(1400, 850)

        main_layout = self.client_layout

        navigation_layout = QHBoxLayout()
        self.prev_step_btn = QPushButton("← 前のstep")
        self.prev_step_btn.setToolTip("現在の編集内容を適用して、前のstep編集へ移動します")
        self.step_position_label = QLabel()
        self.step_position_label.setAlignment(Qt.AlignCenter)
        self.unsaved_label = QLabel()
        self.unsaved_label.setStyleSheet("color: #800000;")
        self.preview_from_step_btn = QPushButton("▶ このstepからプレビュー")
        self.preview_from_step_btn.setToolTip(
            "編集中の内容を適用し、このstepを開始位置にして対話プレビューを起動します"
        )
        self.next_step_btn = QPushButton("次のstep →")
        self.next_step_btn.setToolTip("現在の編集内容を適用して、次のstep編集へ移動します")
        navigation_layout.addWidget(self.prev_step_btn)
        navigation_layout.addStretch()
        navigation_layout.addWidget(self.step_position_label)
        navigation_layout.addWidget(self.unsaved_label)
        navigation_layout.addWidget(self.preview_from_step_btn)
        navigation_layout.addStretch()
        navigation_layout.addWidget(self.next_step_btn)
        main_layout.addLayout(navigation_layout)

        main_splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(main_splitter)

        # 左カラム: step目次。クリックで同じ編集window内を移動する。
        outline_group = QGroupBox("step目次")
        outline_layout = QVBoxLayout(outline_group)
        self.step_outline = QListWidget()
        self.step_outline.setAlternatingRowColors(True)
        self.step_outline.setMinimumWidth(210)
        outline_layout.addWidget(self.step_outline)
        outline_buttons = QHBoxLayout()
        self.insert_before_btn = QPushButton("＋ 前に")
        self.insert_after_btn = QPushButton("後に ＋")
        outline_buttons.addWidget(self.insert_before_btn)
        outline_buttons.addWidget(self.insert_after_btn)
        outline_layout.addLayout(outline_buttons)
        main_splitter.addWidget(outline_group)

        # 中央・右カラムは1つのviewportに載せ、step切替時だけ短くスライドする。
        self.slide_viewport = StepSlideViewport()
        editor_splitter = QSplitter(Qt.Horizontal)
        self.slide_viewport.content_layout.addWidget(editor_splitter)
        main_splitter.addWidget(self.slide_viewport)

        # 中央カラム: 大きなプレビュー + セリフ
        left_panel = QWidget()
        left_panel_layout = QVBoxLayout(left_panel)
        left_panel_layout.setContentsMargins(0, 0, 0, 0)
        left_splitter = QSplitter(Qt.Vertical)
        left_panel_layout.addWidget(left_splitter)
        editor_splitter.addWidget(left_panel)

        preview_group = QGroupBox("プレビュー (4:3)")
        preview_layout = QVBoxLayout()

        self.preview_tabs = QTabWidget()
        self.scene_canvas = StepSceneCanvas(self._image_manager)
        self.preview_tabs.addTab(self.scene_canvas, "オブジェクト")

        self.preview_label = FitPixmapLabel("このタブを開くと最終確認画像を生成します")
        self.preview_label.setStyleSheet("border: 1px solid #888; background: #111; color: #ddd;")
        self.preview_tabs.addTab(self.preview_label, "最終確認画像")
        preview_layout.addWidget(self.preview_tabs)

        self.scene_selection_label = QLabel(
            "選択した立ち絵はドラッグ移動、四隅ドラッグで拡大縮小できます"
        )
        self.scene_selection_label.setStyleSheet("color: #404040;")
        preview_layout.addWidget(self.scene_selection_label)

        self.preview_refresh_btn = QPushButton("Preview Update")
        preview_layout.addWidget(self.preview_refresh_btn, alignment=Qt.AlignCenter)
        preview_group.setLayout(preview_layout)
        left_splitter.addWidget(preview_group)

        dialogue_group = QGroupBox("セリフ")
        dialogue_layout = QFormLayout()
        self.speaker_input = QLineEdit()
        self.speaker_input.setText(self.step.get("speaker", ""))
        dialogue_layout.addRow("speaker", self.speaker_input)

        self.body_input = QLineEdit()
        self.body_input.setText(self.step.get("body", ""))
        dialogue_layout.addRow("body", self.body_input)

        self.scroll_checkbox = QCheckBox("scroll-stop")
        self.scroll_checkbox.setChecked(bool(self.step.get("has_scroll_stop")))
        dialogue_layout.addRow(self.scroll_checkbox)

        self.female_checkbox = QCheckBox("female（話者名とセリフを桃色）")
        self.female_checkbox.setChecked(bool(self.step.get("force_female")))
        dialogue_layout.addRow(self.female_checkbox)

        self.standalone_checkbox = QCheckBox("セリフなしの単独stepとして区切る")
        self.standalone_checkbox.setChecked(bool(self.step.get("standalone")))
        self.standalone_checkbox.setToolTip(
            "すべてのタグを、次のセリフへ結合せず1stepにできます"
        )
        dialogue_layout.addRow(self.standalone_checkbox)

        self.memo_input = QLineEdit()
        self.memo_input.setText(self.step.get("memo", ""))
        self.memo_input.setPlaceholderText("このstepへの備考を入力...")
        dialogue_layout.addRow("備考 (メモ)", self.memo_input)

        dialogue_group.setLayout(dialogue_layout)
        left_splitter.addWidget(dialogue_group)

        # 右カラム: アクション編集
        right_panel = QWidget()
        right_panel_layout = QVBoxLayout(right_panel)
        right_panel_layout.setContentsMargins(0, 0, 0, 0)
        right_splitter = QSplitter(Qt.Vertical)
        right_panel_layout.addWidget(right_splitter)
        editor_splitter.addWidget(right_panel)

        actions_group = QGroupBox("アクション一覧")
        actions_layout = QVBoxLayout()

        self.actions_list = QListWidget()
        for action in self.actions:
            self.actions_list.addItem(action)
        self.actions_list.setEditTriggers(
            QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed
        )
        actions_layout.addWidget(self.actions_list)

        actions_buttons = QHBoxLayout()
        self.add_btn = QPushButton("+ 追加")
        self.remove_btn = QPushButton("削除")
        self.up_btn = QPushButton("↑")
        self.down_btn = QPushButton("↓")
        actions_buttons.addWidget(self.add_btn)
        actions_buttons.addWidget(self.remove_btn)
        actions_buttons.addWidget(self.up_btn)
        actions_buttons.addWidget(self.down_btn)
        actions_layout.addLayout(actions_buttons)

        actions_group.setLayout(actions_layout)
        right_splitter.addWidget(actions_group)

        editor_group = QGroupBox("アクション編集")
        editor_layout = QFormLayout()

        self.tag_combo = QComboBox()
        self.tag_combo.addItems(self.TAG_NAMES)
        editor_layout.addRow("tag", self.tag_combo)

        self.custom_editor_widget = QWidget()
        self.custom_editor_layout = QFormLayout(self.custom_editor_widget)
        editor_layout.addRow(self.custom_editor_widget)

        self.advanced_toggle = QCheckBox("詳細パラメータを表示")
        editor_layout.addRow(self.advanced_toggle)

        self.params_table = QTableWidget(0, 2)
        self.params_table.setHorizontalHeaderLabels(["key", "value"])
        self.params_table.horizontalHeader().setStretchLastSection(True)
        self.params_table.verticalHeader().setVisible(False)
        editor_layout.addRow(self.params_table)

        params_buttons = QHBoxLayout()
        self.param_add_btn = QPushButton("+ 行追加")
        self.param_remove_btn = QPushButton("削除")
        self.apply_action_btn = QPushButton("選択中に適用")
        params_buttons.addWidget(self.param_add_btn)
        params_buttons.addWidget(self.param_remove_btn)
        params_buttons.addWidget(self.apply_action_btn)
        editor_layout.addRow(params_buttons)

        editor_group.setLayout(editor_layout)
        right_splitter.addWidget(editor_group)

        main_splitter.setSizes([250, 1150])
        editor_splitter.setSizes([760, 390])
        left_splitter.setSizes([620, 180])
        right_splitter.setSizes([240, 520])

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        apply_button = buttons.button(QDialogButtonBox.Ok)
        cancel_button = buttons.button(QDialogButtonBox.Cancel)
        apply_button.setText("保存/適用")
        cancel_button.setText("キャンセル")
        # A QDialog clicks its default/auto-default button for an unhandled
        # Enter key.  Text fields deliberately leave Enter unhandled, so the
        # old defaults closed the entire step editor while typing.
        apply_button.setAutoDefault(False)
        apply_button.setDefault(False)
        cancel_button.setAutoDefault(False)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        main_layout.addWidget(buttons)

        self.add_btn.clicked.connect(self._add_action)
        self.remove_btn.clicked.connect(self._remove_action)
        self.up_btn.clicked.connect(self._move_action_up)
        self.down_btn.clicked.connect(self._move_action_down)
        self.param_add_btn.clicked.connect(self._add_param_row)
        self.param_remove_btn.clicked.connect(self._remove_param_row)
        self.apply_action_btn.clicked.connect(self._apply_action_editor)
        self.actions_list.currentItemChanged.connect(self._on_action_selected)
        self.tag_combo.currentTextChanged.connect(self._apply_param_template)
        self.advanced_toggle.stateChanged.connect(self._on_advanced_toggle)
        self.preview_refresh_btn.clicked.connect(self._request_preview_update)
        self.prev_step_btn.clicked.connect(lambda: self._navigate_step(-1))
        self.next_step_btn.clicked.connect(lambda: self._navigate_step(1))
        self.preview_from_step_btn.clicked.connect(self._preview_from_current_step)
        self.insert_before_btn.clicked.connect(lambda: self._create_adjacent_step(-1))
        self.insert_after_btn.clicked.connect(lambda: self._create_adjacent_step(1))
        self.step_outline.currentRowChanged.connect(self._on_outline_step_changed)
        self.scene_canvas.object_selected.connect(self._on_scene_object_selected)
        self.scene_canvas.object_moved.connect(self._on_scene_object_moved)
        self.scene_canvas.object_scaled.connect(self._on_scene_object_scaled)
        self.scene_canvas.context_requested.connect(self._show_scene_context_menu)
        self.scene_canvas.step_navigation_requested.connect(self._page_step)
        self.preview_tabs.currentChanged.connect(self._on_preview_tab_changed)

        # Editing software-style live preview: coalesce a burst of keystrokes into
        # one render instead of launching work for every individual change.
        self._preview_debounce_timer = QTimer(self)
        self._preview_debounce_timer.setSingleShot(True)
        self._preview_debounce_timer.setInterval(300)
        self._preview_debounce_timer.timeout.connect(self._request_preview_update)
        self.speaker_input.textChanged.connect(self._schedule_preview_update)
        self.body_input.textChanged.connect(self._schedule_preview_update)
        self.scroll_checkbox.stateChanged.connect(self._schedule_preview_update)
        self.female_checkbox.stateChanged.connect(self._schedule_preview_update)
        self.standalone_checkbox.stateChanged.connect(self._on_edit_state_changed)
        self.memo_input.textChanged.connect(self._on_edit_state_changed)
        self.speaker_input.textChanged.connect(self._on_edit_state_changed)
        self.body_input.textChanged.connect(self._on_edit_state_changed)
        self.scroll_checkbox.stateChanged.connect(self._on_edit_state_changed)
        self.female_checkbox.stateChanged.connect(self._on_edit_state_changed)
        action_model = self.actions_list.model()
        action_model.dataChanged.connect(self._schedule_scene_preview_update)
        action_model.rowsInserted.connect(self._schedule_scene_preview_update)
        action_model.rowsRemoved.connect(self._schedule_scene_preview_update)
        action_model.rowsMoved.connect(self._schedule_scene_preview_update)
        action_model.dataChanged.connect(self._on_edit_state_changed)
        action_model.rowsInserted.connect(self._on_edit_state_changed)
        action_model.rowsRemoved.connect(self._on_edit_state_changed)
        action_model.rowsMoved.connect(self._on_edit_state_changed)
        action_model.dataChanged.connect(self._sync_standalone_control)
        action_model.rowsInserted.connect(self._sync_standalone_control)
        action_model.rowsRemoved.connect(self._sync_standalone_control)
        action_model.rowsMoved.connect(self._sync_standalone_control)
        self.body_input.textChanged.connect(self._sync_standalone_control)

        if self.actions_list.count() > 0:
            self.actions_list.setCurrentRow(0)
        else:
            self._apply_param_template(self.tag_combo.currentText())
        self._refresh_scene_preview()
        self._sync_standalone_control()
        self._loading_step = False
        self._baseline_signature = self._current_step_signature()
        self._refresh_step_outline()
        self._update_navigation_controls()
        for widget in self.findChildren(QWidget):
            widget.installEventFilter(self)

    def get_dialogue_values(self):
        """セリフ編集の値を取得"""
        speaker = self.speaker_input.text().strip()
        body = self.body_input.text().replace("\n", " ").replace("\r", " ").strip()
        scroll_stop = self.scroll_checkbox.isChecked()
        force_female = self.female_checkbox.isChecked()
        return speaker, body, scroll_stop, force_female

    def get_actions(self):
        """アクション一覧を取得"""
        actions = []
        for i in range(self.actions_list.count()):
            text = self.actions_list.item(i).text().strip()
            if text:
                actions.append(text)
        return actions

    def get_memo(self):
        """備考を取得"""
        return self.memo_input.text().strip()

    def get_standalone(self):
        return self.standalone_checkbox.isChecked()

    def _sync_standalone_control(self, *args):
        eligible = not self.body_input.text().strip() and bool(self.get_actions())
        self.standalone_checkbox.setEnabled(eligible)
        if not eligible and self.standalone_checkbox.isChecked() and not self._loading_step:
            self.standalone_checkbox.setChecked(False)

    def _current_step_signature(self):
        speaker, body, scroll_stop, force_female = self.get_dialogue_values()
        return (
            speaker,
            body,
            scroll_stop,
            force_female,
            self.get_memo(),
            tuple(self.get_actions()),
            self.get_standalone(),
        )

    def _is_step_dirty(self):
        return (
            self._baseline_signature is not None
            and self._current_step_signature() != self._baseline_signature
        )

    @staticmethod
    def _outline_text(step, dirty=False):
        index = step.get("step_index", 0) + 1
        speaker = (step.get("speaker") or "（話者なし）").strip()
        body = re.sub(r"\s+", " ", (step.get("body") or "").strip())
        if len(body) > 28:
            body = body[:27] + "…"
        memo_mark = " ◆" if step.get("memo") else ""
        dirty_mark = " ●" if dirty else ""
        if step.get("standalone"):
            cached_actions = step.get("_actions_cache") or []
            action_name = cached_actions[0].get("tag", "action") if cached_actions else "action"
            summary = f"単独｜{action_name}"
        else:
            summary = f"{speaker}｜{body}" if body else speaker
        return f"{index:03d}{dirty_mark}{memo_mark}  {summary}"

    def _refresh_step_outline(self):
        self._outline_navigation = True
        self.step_outline.blockSignals(True)
        try:
            if self.step_outline.count() != len(self._all_steps):
                self.step_outline.clear()
                for _ in self._all_steps:
                    self.step_outline.addItem(QListWidgetItem())
            for index, step in enumerate(self._all_steps):
                dirty = index == self._step_index and self._is_step_dirty()
                item = self.step_outline.item(index)
                text = self._outline_text(step, dirty=dirty)
                if item.text() != text:
                    item.setText(text)
                item.setData(Qt.UserRole, index)
                tooltip = step.get("body", "") or "セリフなし"
                if step.get("memo"):
                    tooltip += f"\n備考: {step['memo']}"
                if item.toolTip() != tooltip:
                    item.setToolTip(tooltip)
            if self._step_index is not None and 0 <= self._step_index < self.step_outline.count():
                self.step_outline.setCurrentRow(self._step_index)
        finally:
            self.step_outline.blockSignals(False)
            self._outline_navigation = False

    def _select_current_outline_step(self):
        """Update only the active outline row during lightweight paging."""
        if self._step_index is None:
            return
        if self.step_outline.count() != len(self._all_steps):
            self._refresh_step_outline()
            return
        self._outline_navigation = True
        self.step_outline.blockSignals(True)
        try:
            item = self.step_outline.item(self._step_index)
            if item is not None:
                item.setText(self._outline_text(self.step, dirty=self._is_step_dirty()))
                tooltip = self.step.get("body", "") or "セリフなし"
                if self.step.get("memo"):
                    tooltip += f"\n備考: {self.step['memo']}"
                item.setToolTip(tooltip)
            self.step_outline.setCurrentRow(self._step_index)
        finally:
            self.step_outline.blockSignals(False)
            self._outline_navigation = False

    def _update_navigation_controls(self):
        total_steps = len(self._all_steps)
        has_current = (
            self._step_index is not None
            and 0 <= self._step_index < total_steps
        )
        display_index = self._step_index + 1 if has_current else 0
        self.step_position_label.setText(f"step {display_index} / {total_steps}")
        self.unsaved_label.setText("変更あり ●" if self._is_step_dirty() else "")
        self.prev_step_btn.setEnabled(has_current)
        self.next_step_btn.setEnabled(has_current)
        self.insert_before_btn.setEnabled(has_current)
        self.insert_after_btn.setEnabled(has_current)
        self.preview_from_step_btn.setEnabled(has_current)
        if not has_current:
            self.prev_step_btn.setText("← 前のstep")
            self.next_step_btn.setText("次のstep →")
        else:
            self.prev_step_btn.setText(
                "← 前のstep" if self._step_index > 0 else "＋ 前に新規step"
            )
            self.next_step_btn.setText(
                "次のstep →"
                if self._step_index + 1 < total_steps
                else "次に新規step ＋"
            )

    def _update_current_outline_item(self):
        if self._step_index is None:
            return
        item = self.step_outline.item(self._step_index)
        if item is None:
            return
        display_step = dict(self.step)
        display_step.update({
            "speaker": self.speaker_input.text().strip(),
            "body": self.body_input.text().strip(),
            "memo": self.memo_input.text().strip(),
        })
        item.setText(self._outline_text(display_step, dirty=self._is_step_dirty()))
        tooltip = display_step.get("body", "") or "セリフなし"
        if display_step.get("memo"):
            tooltip += f"\n備考: {display_step['memo']}"
        item.setToolTip(tooltip)

    def _on_edit_state_changed(self, *args):
        if self._loading_step:
            return
        self._update_current_outline_item()
        self._update_navigation_controls()

    def _sync_steps_from_parent(self):
        parent = self.parent()
        parent_steps = getattr(parent, "current_steps", None) if parent else None
        if parent_steps is not None:
            self._all_steps = list(parent_steps)

        all_actions = []
        extractor = getattr(parent, "_extract_actions_from_step", None) if parent else None
        source_lines = None
        parent_editor = getattr(parent, "text_editor", None) if parent else None
        if extractor and parent_editor is not None:
            source_lines = parent_editor.toPlainText().splitlines()
        for index, parsed_step in enumerate(self._all_steps):
            if extractor:
                actions = extractor(parsed_step, source_lines=source_lines)
            elif index < len(self._all_step_actions):
                actions = list(self._all_step_actions[index])
            else:
                actions = []
            all_actions.append(actions)
            parsed_step["_actions_cache"] = [
                {"tag": tag, "params": params}
                for tag, params in (parse_step_action(action) for action in actions)
                if tag
            ]
        self._all_step_actions = all_actions

    def _apply_current_step_to_parent(self):
        self.scene_canvas.flush_pending_scale()
        speaker, body, scroll_stop, force_female = self.get_dialogue_values()
        actions = self.get_actions()
        memo = self.get_memo()
        standalone = self.get_standalone()
        parent = self.parent()
        apply_update = getattr(parent, "_apply_step_update", None) if parent else None
        if apply_update:
            apply_update(
                self.step,
                speaker,
                body,
                scroll_stop,
                force_female,
                actions,
                memo,
                standalone=standalone,
            )

            self._sync_steps_from_parent()
            if self._all_steps:
                current = min(self._step_index, len(self._all_steps) - 1)
                self._step_index = current
                self.step = self._all_steps[current]
        else:
            self.step.update({
                "speaker": speaker,
                "body": body,
                "has_scroll_stop": scroll_stop,
                "force_female": force_female,
                "memo": memo,
                "standalone": standalone,
            })
            if self._step_index is not None:
                while len(self._all_step_actions) <= self._step_index:
                    self._all_step_actions.append([])
                self._all_step_actions[self._step_index] = list(actions)
        self._baseline_signature = self._current_step_signature()
        return True

    def _preview_from_current_step(self):
        if self._step_index is None:
            return
        if self._is_step_dirty() and not self._apply_current_step_to_parent():
            return
        parent = self.parent()
        if parent is None or not hasattr(parent, "start_preview"):
            QMessageBox.warning(self, "警告", "プレビュー起動先が見つかりません")
            return
        parent.preview_step_entry.setText(str(self._step_index + 1))
        parent.start_preview()

    def _load_step_index(self, target_index):
        if target_index < 0 or target_index >= len(self._all_steps):
            return False

        self._loading_step = True
        self._preview_debounce_timer.stop()
        self._stop_audio_preview()
        self._step_index = target_index
        self.step = self._all_steps[target_index]
        self.actions = (
            list(self._all_step_actions[target_index])
            if target_index < len(self._all_step_actions)
            else []
        )

        fields = (
            (self.speaker_input, self.step.get("speaker", "")),
            (self.body_input, self.step.get("body", "")),
            (self.memo_input, self.step.get("memo", "")),
        )
        for field, value in fields:
            field.blockSignals(True)
            field.setText(value)
            field.blockSignals(False)
        for checkbox, value in (
            (self.scroll_checkbox, bool(self.step.get("has_scroll_stop"))),
            (self.female_checkbox, bool(self.step.get("force_female"))),
            (self.standalone_checkbox, bool(self.step.get("standalone"))),
        ):
            checkbox.blockSignals(True)
            checkbox.setChecked(value)
            checkbox.blockSignals(False)

        action_model = self.actions_list.model()
        action_model.blockSignals(True)
        self.actions_list.blockSignals(True)
        self.actions_list.clear()
        self.actions_list.addItems(self.actions)
        if self.actions_list.count():
            self.actions_list.setCurrentRow(0)
        self.actions_list.blockSignals(False)
        action_model.blockSignals(False)
        if self.actions_list.currentItem():
            self._on_action_selected(self.actions_list.currentItem(), None)
        else:
            self._apply_param_template(self.tag_combo.currentText())

        self._loading_step = False
        self._sync_standalone_control()
        self._refresh_scene_preview()
        self._baseline_signature = self._current_step_signature()
        self._select_current_outline_step()
        self._update_navigation_controls()

        has_cached_preview = self._restore_cached_final_preview()
        if not has_cached_preview:
            self.preview_label.clear()
            self.preview_label.setText("このタブを開くと最終確認画像を生成します")
        if self.preview_tabs.currentIndex() == 1 and not has_cached_preview:
            self._request_preview_update()
        return True

    def _prepare_step_transition(self):
        if not self._is_step_dirty():
            return True
        return self._apply_current_step_to_parent()

    def _change_step(self, target_index, direction):
        if target_index == self._step_index:
            return True
        if not self._prepare_step_transition():
            return False
        if target_index < 0 or target_index >= len(self._all_steps):
            self._refresh_step_outline()
            return False

        if not self._load_step_index(target_index):
            return False
        return True

    def _on_outline_step_changed(self, row):
        if self._outline_navigation or self._loading_step or row < 0:
            return
        direction = 1 if row > self._step_index else -1
        self._change_step(row, direction)

    def _navigate_step(self, offset):
        """Move inside this window, creating a step at either edge on request."""
        if offset not in (-1, 1) or self._step_index is None:
            return
        target = self._step_index + offset
        if target < 0 or target >= len(self._all_steps):
            self._create_adjacent_step(offset)
            return
        self._change_step(target, offset)

    def _page_step(self, offset):
        """Move to an existing adjacent step; keyboard paging never creates one."""
        if offset not in (-1, 1) or self._step_index is None:
            return False
        target = self._step_index + offset
        if target < 0 or target >= len(self._all_steps):
            return False
        return self._change_step(target, offset)

    def _confirm_create_step(self, offset):
        side = "前" if offset < 0 else "後ろ"
        result = QMessageBox.question(
            self,
            "新しいstepを作成",
            f"現在のstepの{side}に新しいstepを作成しますか？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes,
        )
        return result == QMessageBox.Yes

    def _create_adjacent_step(self, offset):
        if offset not in (-1, 1) or self._step_index is None:
            return False
        if not self._confirm_create_step(offset):
            return False
        if not self._prepare_step_transition():
            return False

        current_index = self._step_index
        parent = self.parent()
        insert_step = getattr(parent, "_insert_step_template", None) if parent else None
        if insert_step:
            insert_step(self.step, insert_before=offset < 0)
            self._sync_steps_from_parent()
        else:
            insert_at = current_index if offset < 0 else current_index + 1
            new_step = {
                "step_index": insert_at,
                "speaker": "speaker",
                "body": "セリフ",
                "memo": "",
            }
            self._all_steps.insert(insert_at, new_step)
            self._all_step_actions.insert(insert_at, [])
            for index, step in enumerate(self._all_steps):
                step["step_index"] = index

        target_index = current_index if offset < 0 else current_index + 1
        if not self._load_step_index(target_index):
            return False
        return True

    def accept(self):
        self.scene_canvas.flush_pending_scale()
        self._stop_audio_preview()
        super().accept()

    def showEvent(self, event):
        super().showEvent(event)
        # The scene owns ordinary left/right paging when no object is selected.
        # Give it the initial focus so paging works immediately after opening.
        QTimer.singleShot(0, self.scene_canvas.setFocus)

    def eventFilter(self, watched, event):
        if (
            event.type() == QEvent.KeyPress
            and event.key() in (Qt.Key_Left, Qt.Key_Right)
            and event.modifiers() in (Qt.NoModifier, Qt.KeypadModifier)
        ):
            scene_handles_key = (
                watched is self.scene_canvas
                or self.scene_canvas.isAncestorOf(watched)
            )
            editing_widget = isinstance(
                watched,
                (
                    QLineEdit,
                    QTextEdit,
                    QComboBox,
                    QTableWidget,
                    QSlider,
                    QDoubleSpinBox,
                ),
            )
            if not scene_handles_key and not editing_widget:
                self._page_step(-1 if event.key() == Qt.Key_Left else 1)
                event.accept()
                return True
        return super().eventFilter(watched, event)

    def keyPressEvent(self, event):
        # QDialog treats Return/Enter as acceptance even when no button is the
        # default.  In this editor those keys must never apply and close a step
        # implicitly; saving remains an explicit button action.
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            event.accept()
            return
        if (
            event.key() in (Qt.Key_Left, Qt.Key_Right)
            and event.modifiers() in (Qt.NoModifier, Qt.KeypadModifier)
        ):
            self._page_step(-1 if event.key() == Qt.Key_Left else 1)
            event.accept()
            return
        super().keyPressEvent(event)

    def reject(self):
        if self._is_step_dirty():
            decision = QMessageBox.question(
                self,
                "step編集を閉じる",
                "現在のstepに未保存の変更があります。保存して閉じますか？",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Save,
            )
            if decision == QMessageBox.Cancel:
                return
            if decision == QMessageBox.Save and not self._apply_current_step_to_parent():
                return
        self.scene_canvas.discard_pending_scale()
        self._stop_audio_preview()
        super().reject()

    def _scene_action_steps(self):
        total = max(len(self._all_steps), (self._step_index or 0) + 1)
        action_steps = [list(actions) for actions in self._all_step_actions]
        while len(action_steps) < total:
            action_steps.append([])
        if self._step_index is not None:
            action_steps[self._step_index] = self.get_actions()
        return action_steps

    def _refresh_scene_preview(self):
        if self._step_index is None:
            self.scene_canvas.set_scene_state({})
            return
        scene_states = self._scene_state_builder.build(
            self._scene_action_steps(), self._step_index
        )
        self._scene_states = scene_states
        self.scene_canvas.set_scene_state(scene_states.get("after", {}))

    def _on_scene_object_selected(self, object_type, object_name, origin):
        if not object_type:
            self.scene_selection_label.setText(
                "オブジェクトをクリックすると選択できます（未選択時 ←/→: step移動）"
            )
            return

        origin_label = {
            "current": "このstepで表示",
            "modified": "このstepで変更",
            "inherited": "前のstepから引き継ぎ",
        }.get(origin, origin)
        type_label = "キャラ" if object_type == "character" else "背景"
        shortcut_hint = (
            "（矢印: 1px、Shift+矢印: 10px）"
            if object_type == "character"
            else ""
        )
        self.scene_selection_label.setText(
            f"選択: {type_label}「{object_name}」 / {origin_label} {shortcut_hint}"
        )

        # If the selected object already has an action in this step, expose the
        # last matching action in the existing inspector.  Inherited objects
        # deliberately remain explicit instead of guessing a different target.
        for row in range(self.actions_list.count() - 1, -1, -1):
            tag, pairs = self._parse_action(self.actions_list.item(row).text())
            params = dict(pairs)
            if object_type == "character":
                if tag.startswith("chara_") and params.get("name", "").strip() == object_name:
                    self.actions_list.setCurrentRow(row)
                    return
            elif object_type == "background" and tag in ("bg", "bg_show", "bg_move"):
                self.actions_list.setCurrentRow(row)
                return

    @staticmethod
    def _format_scene_number(value):
        value = round(float(value), 8)
        if abs(value) < 0.000000005:
            value = 0.0
        text = f"{value:.8f}".rstrip("0").rstrip(".")
        return text if "." in text else text + ".0"

    @staticmethod
    def _parse_scene_number(value, default):
        try:
            return float(value)
        except (TypeError, ValueError):
            return float(default)

    def _set_action_row(self, row, tag, params):
        action_text = self._build_action(tag, list(params.items()))
        self.actions_list.item(row).setText(action_text)
        self.actions_list.setCurrentRow(row)

    def _on_scene_object_moved(self, name, delta_x, delta_y, metadata):
        """Persist a canvas drag without splitting a current-step show."""
        name = (name or "").strip()
        if not name:
            return
        relative_x = float(delta_x) / VIRTUAL_WIDTH
        relative_y = float(delta_y) / VIRTUAL_HEIGHT
        target_x = self._parse_scene_number(metadata.get("x"), 0.5) + relative_x
        target_y = self._parse_scene_number(metadata.get("y"), 0.5) + relative_y
        target_size = self._parse_scene_number(metadata.get("zoom"), 1.0)
        self._direct_scene_edit = True

        last_placement_row = -1
        reusable_shift_row = -1
        parsed_by_row = {}
        for row in range(self.actions_list.count()):
            tag, pairs = self._parse_action(self.actions_list.item(row).text())
            params = dict(pairs)
            parsed_by_row[row] = (tag, params)
            if params.get("name", "").strip() != name:
                continue
            if tag in ("chara_show", "chara_move") or (
                tag == "chara_shift"
                and any(key in params for key in ("x", "y", "size"))
            ):
                last_placement_row = row
                reusable_shift_row = row if tag == "chara_shift" else -1

        placement_params = {
            "x": self._format_scene_number(target_x),
            "y": self._format_scene_number(target_y),
            "size": self._format_scene_number(target_size),
        }
        last_placement = parsed_by_row.get(last_placement_row)
        if last_placement is not None and last_placement[0] == "chara_show":
            tag, params = last_placement
            target_x = self._parse_scene_number(params.get("x"), 0.5) + relative_x
            target_y = self._parse_scene_number(params.get("y"), 0.5) + relative_y
            params["x"] = self._format_scene_number(target_x)
            params["y"] = self._format_scene_number(target_y)
            self._set_action_row(last_placement_row, tag, params)
            action_label = "chara_showのx/yを更新"
        elif reusable_shift_row == last_placement_row and reusable_shift_row >= 0:
            tag, params = parsed_by_row[reusable_shift_row]
            params.update(placement_params)
            self._set_action_row(reusable_shift_row, tag, params)
            action_label = "chara_shiftのx/y/sizeを更新"
        else:
            shift_params = {"name": name, **placement_params}
            action_text = self._build_action("chara_shift", list(shift_params.items()))
            self.actions_list.addItem(action_text)
            self.actions_list.setCurrentRow(self.actions_list.count() - 1)
            action_label = "chara_shiftを追加"

        self._direct_scene_edit = False
        self.scene_canvas.mark_character_modified(
            name,
            {"x": target_x, "y": target_y, "zoom": target_size},
        )
        self.scene_selection_label.setText(
            f"移動: キャラ「{name}」 / {action_label} "
            f"(Δx={self._format_scene_number(relative_x)}, "
            f"Δy={self._format_scene_number(relative_y)})"
        )

    def _on_scene_object_scaled(self, name, new_zoom, metadata):
        """Write direct scaling to the last effective scale action."""
        name = (name or "").strip()
        if not name:
            return

        self._direct_scene_edit = True
        scale_rows = []
        parsed_by_row = {}
        for row in range(self.actions_list.count()):
            tag, pairs = self._parse_action(self.actions_list.item(row).text())
            params = dict(pairs)
            parsed_by_row[row] = (tag, params)
            if params.get("name", "").strip() != name:
                continue
            if tag == "chara_show":
                scale_rows.append((row, "size"))
            elif tag == "chara_shift" and "size" in params:
                scale_rows.append((row, "size"))
            elif tag == "chara_move":
                scale_rows.append((row, "zoom"))

        formatted_zoom = self._format_scene_number(new_zoom)
        if scale_rows:
            row, scale_key = max(scale_rows, key=lambda value: value[0])
            tag, params = parsed_by_row[row]
            params[scale_key] = formatted_zoom
            self._set_action_row(row, tag, params)
            action_label = f"{tag}の{scale_key}を更新"
        else:
            move_params = {
                "name": name,
                "left": "0.0",
                "top": "0.0",
                "zoom": formatted_zoom,
                "time": "600",
            }
            action_text = self._build_action("chara_move", list(move_params.items()))
            self.actions_list.addItem(action_text)
            self.actions_list.setCurrentRow(self.actions_list.count() - 1)
            action_label = "拡大縮小用chara_moveを追加"

        self._direct_scene_edit = False
        self.scene_canvas.mark_character_modified(name)
        self.scene_selection_label.setText(
            f"拡大縮小: キャラ「{name}」 / {action_label} "
            f"(zoom={formatted_zoom})"
        )

    def _append_action_from_template(self, tag, overrides=None):
        params = dict(self.PARAM_TEMPLATES.get(tag, []))
        params.update(overrides or {})
        action_text = self._build_action(tag, list(params.items()))
        self.actions_list.addItem(action_text)
        row = self.actions_list.count() - 1
        self.actions_list.setCurrentRow(row)
        return row

    def _find_latest_character_action(self, tag, name):
        for row in range(self.actions_list.count() - 1, -1, -1):
            current_tag, pairs = self._parse_action(self.actions_list.item(row).text())
            if current_tag == tag and dict(pairs).get("name", "").strip() == name:
                return row
        return -1

    def _execute_scene_context_command(self, command, object_name="", metadata=None):
        if command == "character_move":
            self.scene_selection_label.setText(
                f"移動モード: キャラ「{object_name}」をドラッグしてください"
            )
            return
        if command == "character_shift":
            row = self._find_latest_character_action("chara_shift", object_name)
            if row < 0:
                row = self._append_action_from_template(
                    "chara_shift", {"name": object_name, "fade": "0.15"}
                )
            else:
                self.actions_list.setCurrentRow(row)
            QTimer.singleShot(0, lambda: self._open_chara_preview(True))
            return
        if command == "character_hide":
            self._append_action_from_template(
                "chara_hide", {"name": object_name, "fade": "0.15"}
            )
            return
        if command == "select_background":
            for row in range(self.actions_list.count() - 1, -1, -1):
                tag, _ = self._parse_action(self.actions_list.item(row).text())
                if tag in ("bg", "bg_show", "bg_move"):
                    self.actions_list.setCurrentRow(row)
                    return
            self.scene_selection_label.setText("このstepには背景アクションがありません")
            return
        if command == "chara_show":
            self._append_action_from_template(command)
            QTimer.singleShot(0, lambda: self._open_chara_preview(False))
            return
        if command:
            self._append_action_from_template(command)

    def _show_scene_context_menu(
        self, object_type, object_name, origin, global_pos, metadata
    ):
        menu = QMenu(self)
        action_map = {}

        if object_type == "character":
            move_action = menu.addAction("移動（ステージ上でドラッグ）")
            shift_action = menu.addAction("Shift：立ち絵・表情を変更...")
            menu.addSeparator()
            hide_action = menu.addAction("Hide：このキャラを非表示")
            action_map = {
                move_action: "character_move",
                shift_action: "character_shift",
                hide_action: "character_hide",
            }
        else:
            show_action = menu.addAction("キャラクターを表示（chara_show）...")

            background_menu = menu.addMenu("背景")
            select_bg_action = background_menu.addAction("現在の背景アクションを選択")
            bg_show_action = background_menu.addAction("背景を設定（bg_show）...")
            bg_move_action = background_menu.addAction("背景を移動（bg_move）...")

            audio_menu = menu.addMenu("音声")
            bgm_action = audio_menu.addAction("BGMを追加...")
            se_action = audio_menu.addAction("SEを追加...")
            audio_menu.addSeparator()
            se_stop_action = audio_menu.addAction("SEをすべて停止")
            bgm_end_action = audio_menu.addAction("BGMをフェード終了")
            bgm_stop_action = audio_menu.addAction("BGM停止")
            bgm_start_action = audio_menu.addAction("BGM再開")

            system_menu = menu.addMenu("システム／制御タグ")
            choice_action = system_menu.addAction("選択肢（choice）")
            fadeout_action = system_menu.addAction("フェードアウト")
            fadein_action = system_menu.addAction("フェードイン")
            flag_action = system_menu.addAction("フラグ設定")
            if_action = system_menu.addAction("条件分岐開始（if）")
            endif_action = system_menu.addAction("条件分岐終了（endif）")
            event_action = system_menu.addAction("イベント制御")

            action_map = {
                show_action: "chara_show",
                select_bg_action: "select_background",
                bg_show_action: "bg_show",
                bg_move_action: "bg_move",
                bgm_action: "bgm",
                se_action: "se",
                se_stop_action: "sestop",
                bgm_end_action: "bgmend",
                bgm_stop_action: "bgmstop",
                bgm_start_action: "bgmstart",
                choice_action: "choice",
                fadeout_action: "fadeout",
                fadein_action: "fadein",
                flag_action: "flag_set",
                if_action: "if",
                endif_action: "endif",
                event_action: "event_control",
            }

        selected = menu.exec_(global_pos)
        command = action_map.get(selected)
        if not command:
            return
        self._execute_scene_context_command(command, object_name, metadata)

    def _add_action(self):
        tag = self.tag_combo.currentText().strip() or "bg"
        self.actions_list.addItem(tag)
        self.actions_list.setCurrentRow(self.actions_list.count() - 1)

    def _remove_action(self):
        row = self.actions_list.currentRow()
        if row >= 0:
            self.actions_list.takeItem(row)

    def _move_action_up(self):
        row = self.actions_list.currentRow()
        if row > 0:
            item = self.actions_list.takeItem(row)
            self.actions_list.insertItem(row - 1, item)
            self.actions_list.setCurrentRow(row - 1)

    def _move_action_down(self):
        row = self.actions_list.currentRow()
        if 0 <= row < self.actions_list.count() - 1:
            item = self.actions_list.takeItem(row)
            self.actions_list.insertItem(row + 1, item)
            self.actions_list.setCurrentRow(row + 1)

    def _on_action_selected(self, current, previous):
        if not current:
            return
        tag, params = self._parse_action(current.text())
        if tag:
            self.tag_combo.setCurrentText(tag)
        self._load_action_into_editors(tag, params)

    def _apply_param_template(self, tag):
        if not tag:
            return
        params = self.PARAM_TEMPLATES.get(tag, [])
        self._load_action_into_editors(tag, params, from_template=True)

    def _add_param_row(self):
        row = self.params_table.rowCount()
        self.params_table.insertRow(row)
        self.params_table.setItem(row, 0, QTableWidgetItem(""))
        self.params_table.setItem(row, 1, QTableWidgetItem(""))

    def _remove_param_row(self):
        row = self.params_table.currentRow()
        if row >= 0:
            self.params_table.removeRow(row)

    def _load_params(self, params):
        self.params_table.setRowCount(0)
        for key, value in params:
            row = self.params_table.rowCount()
            self.params_table.insertRow(row)
            self.params_table.setItem(row, 0, QTableWidgetItem(key))
            self.params_table.setItem(row, 1, QTableWidgetItem(value))

    def _merge_with_template(self, tag, params):
        template = self.PARAM_TEMPLATES.get(tag, [])
        if not template:
            return params

        merged = []
        used_keys = set()
        param_map = {k: v for k, v in params}

        for key, default in template:
            if key in param_map:
                merged.append((key, param_map[key]))
                used_keys.add(key)
            else:
                merged.append((key, default))

        for key, value in params:
            if key in used_keys:
                continue
            merged.append((key, value))

        return merged

    def _collect_params(self):
        params = []
        for row in range(self.params_table.rowCount()):
            key_item = self.params_table.item(row, 0)
            value_item = self.params_table.item(row, 1)
            key = key_item.text().strip() if key_item else ""
            value = value_item.text().strip() if value_item else ""
            if key:
                params.append((key, value))
        return params

    def _apply_action_editor(self):
        current_row = self.actions_list.currentRow()
        if current_row < 0:
            return
        tag = self.tag_combo.currentText().strip()
        if self._is_custom_tag(tag) and not self.advanced_toggle.isChecked():
            params = self._collect_custom_params()
        else:
            params = self._collect_params()
        text = self._build_action(tag, params)
        self.actions_list.item(current_row).setText(text)

    def _schedule_preview_update(self, *args):
        if self._loading_step or self.preview_tabs.currentIndex() != 1:
            return
        self._preview_debounce_timer.start()

    def _schedule_scene_preview_update(self, *args):
        if self._loading_step or self._direct_scene_edit:
            return
        self._refresh_scene_preview()
        self._schedule_preview_update()

    def _request_preview_update(self, *args):
        if self._loading_step:
            return
        self._preview_debounce_timer.stop()
        parent = self.parent()
        if not parent:
            return
        if hasattr(parent, "_preview_step_from_dialog"):
            parent._preview_step_from_dialog(self.step, self)

    def _on_preview_tab_changed(self, index):
        if self._loading_step or index != 1:
            return
        if not self._restore_cached_final_preview():
            self._request_preview_update()

    def _parse_action(self, text):
        return parse_step_action(text)

    def _build_action(self, tag, params):
        tag = tag.strip()
        if not tag:
            return ""
        parts = [tag]
        template = self.PARAM_TEMPLATES.get(tag, [])
        template_order = [key for key, _ in template]
        param_map = {key: value for key, value in params}

        ordered_keys = []
        for key in template_order:
            if key in param_map:
                ordered_keys.append(key)
        for key in param_map.keys():
            if key not in ordered_keys:
                ordered_keys.append(key)

        for key in ordered_keys:
            value = param_map.get(key, "")
            if value == "":
                continue
            parts.append(f'{key}="{value}"')
        return " ".join(parts)

    def set_preview_image(self, image_path):
        if not image_path or not os.path.exists(image_path):
            return
        pixmap = QPixmap(image_path)
        if pixmap.isNull():
            return
        self.preview_label.set_source_pixmap(pixmap)
        cache_key = self._final_preview_cache_key()
        if cache_key is not None:
            self._final_preview_cache[cache_key] = pixmap
            self._final_preview_cache.move_to_end(cache_key)
            while len(self._final_preview_cache) > self._final_preview_cache_limit:
                self._final_preview_cache.popitem(last=False)

    def _final_preview_cache_key(self):
        if self._step_index is None:
            return None
        return self._step_index, self._current_step_signature()

    def _restore_cached_final_preview(self):
        cache_key = self._final_preview_cache_key()
        if cache_key is None:
            return False
        pixmap = self._final_preview_cache.get(cache_key)
        if pixmap is None or pixmap.isNull():
            return False
        self._final_preview_cache.move_to_end(cache_key)
        # Invalidate an older in-flight request so it cannot replace the image
        # belonging to the step we just restored.
        self._preview_request_id = None
        self.preview_label.set_source_pixmap(pixmap)
        return True

    def _is_custom_tag(self, tag):
        return tag in self.CUSTOM_EDITORS

    def _clear_custom_editor(self):
        while self.custom_editor_layout.rowCount():
            for role in (QFormLayout.LabelRole, QFormLayout.FieldRole):
                item = self.custom_editor_layout.itemAt(0, role)
                if not item:
                    continue
                widget = item.widget()
                layout = item.layout()
                if widget:
                    widget.deleteLater()
                if layout:
                    while layout.count():
                        child = layout.takeAt(0)
                        child_widget = child.widget()
                        if child_widget:
                            child_widget.deleteLater()
                    layout.deleteLater()
            self.custom_editor_layout.removeRow(0)
        self.custom_fields = {}
        self._volume_sliders = {}
        self.custom_editor_widget.adjustSize()
        self.custom_editor_widget.updateGeometry()

    def _empty_chara_preview_state(self):
        return {part: "" for part in self.CHARA_PREVIEW_PARTS}

    def _expand_chara_template_params(self, params):
        """Expand a script template for editor-side composite previews."""
        expanded = dict(params or {})
        char_name = str(expanded.get("name", "")).strip()
        template_name = str(expanded.get("template", "")).strip()
        if not char_name or not template_name:
            return expanded

        store = CharaPartTemplateStore(
            os.path.join(project_root, "editor_data", "chara_part_templates.json")
        )
        template = store.find(char_name, template_name)
        if not template:
            return expanded

        # The template supplies defaults; explicit tag attributes win.
        resolved = dict(template.get("parts", {}))
        resolved["blink"] = "true" if template.get("blink", True) else "false"
        resolved.update(expanded)
        return resolved

    def _apply_chara_preview_action(self, states_by_name, tag, params):
        params = self._expand_chara_template_params(params)
        char_name = params.get("name", "").strip()
        if not char_name:
            return states_by_name
        next_states = {
            name: dict(fields) for name, fields in states_by_name.items()
        }
        if tag == "chara_hide":
            next_states.pop(char_name, None)
            return next_states
        if tag == "chara_show":
            next_states[char_name] = self._empty_chara_preview_state()
        if tag in ("chara_show", "chara_shift"):
            current_state = next_states.get(char_name, self._empty_chara_preview_state())
            merged = dict(current_state)
            for part in self.CHARA_PREVIEW_PARTS:
                if part in params:
                    merged[part] = params.get(part, "")
            next_states[char_name] = merged
        return next_states

    def _iter_prior_chara_actions(self):
        if self._step_index is not None and self._all_steps:
            for step in self._all_steps:
                si = step.get("step_index", -1)
                if si >= self._step_index:
                    continue
                for action in step.get("_actions_cache", []):
                    yield action.get("tag", ""), dict(action.get("params", []))

        current_row = self.actions_list.currentRow()
        if current_row > 0:
            for row in range(current_row):
                item = self.actions_list.item(row)
                if not item:
                    continue
                tag, params = self._parse_action(item.text())
                yield tag, dict(params)

    def _resolve_chara_preview_name_context(self, current_tag, explicit_name=""):
        from core.config import CHAR_CODE

        known_names = list(CHAR_CODE.keys())
        states_by_name = {}
        last_name = ""

        def add_known(name):
            if name and name not in known_names:
                known_names.append(name)

        for tag, params in self._iter_prior_chara_actions():
            name = params.get("name", "").strip()
            if not name:
                continue
            add_known(name)
            states_by_name = self._apply_chara_preview_action(states_by_name, tag, params)
            last_name = name

        active_names = list(states_by_name.keys())

        explicit_name = (explicit_name or "").strip()
        restricted = current_tag in ("chara_shift", "chara_move", "chara_hide")
        default_name = explicit_name
        if not default_name and restricted:
            default_name = active_names[0] if active_names else last_name

        candidates = list(active_names) if restricted else list(known_names)
        if default_name and default_name not in candidates:
            candidates.insert(0, default_name)
        if explicit_name and explicit_name not in candidates:
            candidates.insert(0, explicit_name)

        return {
            "candidates": candidates,
            "default_name": default_name,
            "active_names": active_names,
            "last_name": last_name,
            "states_by_name": states_by_name,
        }

    def _find_prev_char_fields(self, char_name):
        """現在選択中アクション直前の表示状態を返す"""
        context = self._resolve_chara_preview_name_context(
            self.tag_combo.currentText().strip(),
            char_name,
        )
        return dict(context.get("states_by_name", {}).get(char_name, {}))

    def _open_chara_preview(self, is_shift):
        """立ち絵合成プレビューダイアログを開く"""
        image_manager = self._image_manager
        if not image_manager:
            QMessageBox.warning(self, 'エラー',
                '画像マネージャーが初期化されていません。'
                'エディタでファイルを開いてから実行してください。')
            return

        # 現在のフィールド値を収集
        current = {k: (f.currentText() if isinstance(f, QComboBox) else f.text().strip())
                   for k, f in self.custom_fields.items()}
        current = self._expand_chara_template_params(current)
        current_tag = self.tag_combo.currentText().strip() or ("chara_shift" if is_shift else "chara_show")
        name_context = self._resolve_chara_preview_name_context(current_tag, current.get('name', ''))
        char_name = name_context["default_name"] or current.get('name', '').strip()
        prev_fields = dict(name_context.get("states_by_name", {}).get(char_name, {}))
        action_overrides = {
            part: current.get(part, "").strip()
            for part in self.CHARA_PREVIEW_PARTS
        }
        initial_fields = dict(prev_fields)
        for part, value in action_overrides.items():
            if value:
                initial_fields[part] = value
        initial_fields['blink'] = current.get('blink', 'true') or 'true'

        dlg = CharaCompositePreviewDialog(
            self, image_manager, initial_fields,
            char_name=char_name, is_shift=is_shift, prev_fields=prev_fields,
            char_name_options=name_context["candidates"],
            require_name=not bool(current.get("name", "").strip()),
            state_by_name=name_context.get("states_by_name", {}),
            action_overrides=action_overrides,
            step_speaker=self.get_dialogue_values()[0],
            step_body=self.get_dialogue_values()[1],
            step_force_female=self.get_dialogue_values()[3],
        )
        if dlg.exec_() == QDialog.Accepted:
            result = dlg.get_result_fields()
            for part, val in result.items():
                if part in self.custom_fields:
                    field = self.custom_fields[part]
                    if isinstance(field, QLineEdit):
                        field.setText(val)
                    elif isinstance(field, QComboBox):
                        idx = field.findText(val)
                        if idx >= 0:
                            field.setCurrentIndex(idx)
                        else:
                            field.setCurrentText(val)
            # custom_fields の値を actions_list に書き戻す
            self._apply_action_editor()

    def _build_custom_editor(self, tag):
        self._clear_custom_editor()
        schema = self.CUSTOM_EDITORS.get(tag)
        if not schema:
            self.custom_editor_widget.hide()
            self.advanced_toggle.hide()
            self.params_table.show()
            return

        for key, label, field_type in schema:
            if field_type == "bool":
                field = QComboBox()
                field.addItems(["true", "false"])
                field.setProperty("booleanField", True)
            elif field_type == "volume_slider":
                field = QDoubleSpinBox()
                field.setRange(0.0, 1.0)
                field.setDecimals(2)
                field.setSingleStep(0.01)
                field.setMaximumWidth(76)
            elif field_type in ("bg_asset", "bgm_asset", "se_asset"):
                field = QComboBox()
                field.setEditable(True)
                field.addItem("")
                field.addItems(self._editor_asset_options(field_type))
            else:
                field = QLineEdit()
            self.custom_fields[key] = field
            if field_type == "volume_slider":
                wrapper = QWidget()
                wrapper_layout = QHBoxLayout(wrapper)
                wrapper_layout.setContentsMargins(0, 0, 0, 0)
                slider = QSlider(Qt.Horizontal)
                slider.setRange(0, 100)
                slider.setSingleStep(1)
                slider.setPageStep(5)
                slider.setTracking(True)
                slider.setObjectName(f"{key}Slider")
                self._volume_sliders[key] = slider
                slider.valueChanged.connect(
                    lambda value, k=key: self._on_volume_slider_changed(k, value)
                )
                field.valueChanged.connect(
                    lambda value, k=key: self._on_volume_number_changed(k, value)
                )
                wrapper_layout.addWidget(slider, 1)
                wrapper_layout.addWidget(field)
                self.custom_editor_layout.addRow(label, wrapper)
            elif field_type in ("bgm_asset", "se_asset"):
                wrapper = QWidget()
                wrapper_layout = QHBoxLayout(wrapper)
                wrapper_layout.setContentsMargins(0, 0, 0, 0)
                wrapper_layout.addWidget(field, 1)
                play_btn = QPushButton("▶ 試聴")
                stop_btn = QPushButton("■")
                play_btn.setObjectName(f"{key}PreviewButton")
                stop_btn.setObjectName(f"{key}PreviewStopButton")
                if field_type == "bgm_asset":
                    play_btn.clicked.connect(self._preview_selected_bgm)
                    stop_btn.clicked.connect(self._stop_bgm_preview)
                else:
                    play_btn.clicked.connect(self._preview_selected_se)
                    stop_btn.clicked.connect(self._stop_se_preview)
                wrapper_layout.addWidget(play_btn)
                wrapper_layout.addWidget(stop_btn)
                self.custom_editor_layout.addRow(label, wrapper)
            elif field_type == "text" and key in self.BROWSE_KEYS:
                wrapper = QWidget()
                wrapper_layout = QHBoxLayout(wrapper)
                wrapper_layout.setContentsMargins(0, 0, 0, 0)
                wrapper_layout.addWidget(field, 1)
                browse_btn = QPushButton("Browse")
                browse_btn.clicked.connect(lambda _=False, k=key: self._browse_for_asset(k))
                wrapper_layout.addWidget(browse_btn)
                self.custom_editor_layout.addRow(label, wrapper)
            else:
                self.custom_editor_layout.addRow(label, field)

        # chara_show / chara_shift: 立ち絵プレビューボタンを追加
        if tag in ('chara_show', 'chara_shift'):
            is_shift = (tag == 'chara_shift')
            preview_btn = QPushButton('🎨 立ち絵プレビュー & パーツ選択')
            preview_btn.clicked.connect(lambda: self._open_chara_preview(is_shift))
            self.custom_editor_layout.addRow('', preview_btn)

        self.custom_editor_widget.show()
        self.advanced_toggle.show()
        self.params_table.setVisible(self.advanced_toggle.isChecked())
        self.custom_editor_widget.adjustSize()
        self.custom_editor_widget.updateGeometry()

    def _set_custom_values(self, params):
        param_map = {key: value for key, value in params}
        for key, field in self.custom_fields.items():
            value = param_map.get(key, "")
            if isinstance(field, QComboBox):
                default = "true" if field.property("booleanField") else ""
                field.setCurrentText(value if value else default)
            elif isinstance(field, QDoubleSpinBox):
                try:
                    numeric_value = float(value)
                except (TypeError, ValueError):
                    numeric_value = 0.5
                field.blockSignals(True)
                field.setValue(max(0.0, min(1.0, numeric_value)))
                field.blockSignals(False)
                slider = self._volume_sliders.get(key)
                if slider is not None:
                    slider.blockSignals(True)
                    slider.setValue(round(field.value() * 100))
                    slider.blockSignals(False)
            else:
                field.setText(value)

    def _on_volume_slider_changed(self, key, value):
        volume = max(0.0, min(1.0, float(value) / 100.0))
        field = self.custom_fields.get(key)
        if isinstance(field, QDoubleSpinBox):
            field.blockSignals(True)
            field.setValue(volume)
            field.blockSignals(False)
        self._apply_live_preview_volume(volume)

    def _on_volume_number_changed(self, key, value):
        volume = max(0.0, min(1.0, float(value)))
        slider = self._volume_sliders.get(key)
        if slider is not None:
            slider.blockSignals(True)
            slider.setValue(round(volume * 100))
            slider.blockSignals(False)
        self._apply_live_preview_volume(volume)

    def _apply_live_preview_volume(self, volume):
        tag = self.tag_combo.currentText().strip().lower()
        if tag == "bgm" and self._bgm_preview_manager is not None:
            self._bgm_preview_manager.set_volume(volume)
        elif tag == "se" and self._se_preview_manager is not None:
            self._se_preview_manager.set_current_volume(volume)

    def _editor_asset_options(self, field_type):
        if field_type == "bg_asset":
            paths = getattr(self._image_manager, "image_paths", {}) or {}
            return sorted((paths.get("bg", {}) or {}).keys())
        audio_subdirs = {
            "bgm_asset": "bgms",
            "se_asset": "ses",
        }
        if field_type in audio_subdirs:
            audio_dir = os.path.join(project_root, "sounds", audio_subdirs[field_type])
            if not os.path.isdir(audio_dir):
                return []
            extensions = (".wav", ".mp3", ".ogg", ".m4a")
            return sorted(
                filename
                for filename in os.listdir(audio_dir)
                if filename.lower().endswith(extensions)
            )
        return []

    @staticmethod
    def _custom_text_value(field, default=""):
        if isinstance(field, QComboBox):
            value = field.currentText().strip()
        elif isinstance(field, QDoubleSpinBox):
            value = f"{field.value():.2f}".rstrip("0").rstrip(".")
        elif isinstance(field, QLineEdit):
            value = field.text().strip()
        else:
            value = ""
        return value if value else default

    def _preview_selected_bgm(self):
        filename = self._custom_text_value(self.custom_fields.get("bgm"))
        if not filename:
            self.scene_selection_label.setText("BGMを選択してください")
            return
        try:
            volume = float(self._custom_text_value(self.custom_fields.get("volume"), "0.5"))
        except (TypeError, ValueError):
            volume = 0.5
        loop = self._custom_text_value(self.custom_fields.get("loop"), "true").lower() == "true"
        try:
            fade_time = float(self._custom_text_value(self.custom_fields.get("fade"), "0.0"))
        except (TypeError, ValueError):
            fade_time = 0.0
        if self._bgm_preview_manager is None:
            self._bgm_preview_manager = BGMManager(False)
            self._bgm_preview_manager.BGM_PATH = os.path.join(project_root, "sounds", "bgms")
        self._bgm_preview_manager.stop_bgm()
        if self._bgm_preview_manager.play_bgm(
            filename,
            volume,
            loop,
            fade_time=fade_time,
        ):
            self.scene_selection_label.setText(f"BGM試聴中: {filename}")
        else:
            self.scene_selection_label.setText(f"BGMを再生できません: {filename}")

    def _stop_bgm_preview(self):
        if self._bgm_preview_manager is not None:
            self._bgm_preview_manager.stop_bgm()

    def _preview_selected_se(self):
        field = self.custom_fields.get("se")
        filename = field.currentText().strip() if isinstance(field, QComboBox) else ""
        if not filename:
            self.scene_selection_label.setText("SEを選択してください")
            return
        try:
            volume = float(self._custom_text_value(self.custom_fields.get("volume"), "0.5"))
        except (TypeError, ValueError):
            volume = 0.5
        if self._se_preview_manager is None:
            self._se_preview_manager = SEManager(False)
            self._se_preview_manager.SE_PATH = os.path.join(project_root, "sounds", "ses")
        self._se_preview_manager.stop_all_se()
        play_result = self._se_preview_manager.play_se(filename, volume, 1)
        if play_result is not False and play_result is not None:
            self.scene_selection_label.setText(f"SE試聴中: {filename}")
        else:
            self.scene_selection_label.setText(f"SEを再生できません: {filename}")

    def _stop_se_preview(self):
        if self._se_preview_manager is not None:
            self._se_preview_manager.stop_all_se()

    def _stop_audio_preview(self):
        self._stop_bgm_preview()
        self._stop_se_preview()

    def _collect_custom_params(self):
        params = []
        for key, field in self.custom_fields.items():
            if isinstance(field, QComboBox):
                value = field.currentText().strip()
            elif isinstance(field, QDoubleSpinBox):
                value = f"{field.value():.2f}".rstrip("0").rstrip(".")
            else:
                value = field.text().strip()
            if value != "":
                params.append((key, value))
        return params

    def _browse_for_asset(self, key):
        from core.config import CHAR_CODE

        subdir = self.BROWSE_KEYS.get(key)
        if not subdir:
            return

        base_dir = os.path.join(project_root, "images")
        start_dir = base_dir

        if key == "storage":
            # 背景: images/BG/ を開く
            candidate = os.path.join(base_dir, "BG")
            if os.path.isdir(candidate):
                start_dir = candidate
        else:
            # キャラクターパーツ: nameフィールドの表示名からコードを引いてディレクトリを特定
            name_field = self.custom_fields.get("name")
            name_value = name_field.text().strip() if name_field else ""
            char_code = CHAR_CODE.get(name_value, "")
            if char_code and os.path.isdir(base_dir):
                for d in os.listdir(base_dir):
                    if d.endswith(char_code) and os.path.isdir(os.path.join(base_dir, d)):
                        start_dir = os.path.join(base_dir, d)
                        break

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select image",
            start_dir,
            "Images (*.png *.jpg *.jpeg *.webp)",
        )
        if not file_path:
            return

        stem = os.path.splitext(os.path.basename(file_path))[0]
        field = self.custom_fields.get(key)
        if field is not None:
            field.setText(stem)

    def _load_action_into_editors(self, tag, params, from_template=False):
        merged = self._merge_with_template(tag, params)
        self._build_custom_editor(tag)
        if self._is_custom_tag(tag):
            self._set_custom_values(merged)
            if self.advanced_toggle.isChecked():
                self._load_params(merged)
            elif from_template:
                self._load_params(merged)
        else:
            self._load_params(merged)

    def _on_advanced_toggle(self, state):
        tag = self.tag_combo.currentText().strip()
        if not self._is_custom_tag(tag):
            return
        if self.advanced_toggle.isChecked():
            params = self._collect_custom_params()
            self._load_params(self._merge_with_template(tag, params))
            self.params_table.show()
        else:
            params = self._collect_params()
            self._set_custom_values(self._merge_with_template(tag, params))
            self.params_table.hide()

class KSTextEditor(QTextEdit):
    """カスタムショートカットを持つKSファイルテキストエディタ"""

    def _indent_selected_lines(self):
        """選択範囲に含まれるすべての行をタブ1つ分インデントする。"""
        cursor = self.textCursor()
        if not cursor.hasSelection():
            return False

        selection_forward = cursor.anchor() <= cursor.position()
        selection_start = cursor.selectionStart()
        selection_end = cursor.selectionEnd()
        first_block = self.document().findBlock(selection_start)
        last_block = self.document().findBlock(selection_end)

        # 選択終端が次行の行頭なら、その行自体は選択範囲に含めない。
        if (
            selection_end > selection_start
            and selection_end == last_block.position()
        ):
            last_block = last_block.previous()

        blocks = []
        block = first_block
        while block.isValid():
            blocks.append(block)
            if block == last_block:
                break
            block = block.next()

        cursor.beginEditBlock()
        for block in blocks:
            line_cursor = QTextCursor(block)
            line_cursor.insertText("\t")
        cursor.endEditBlock()

        # 挿入後も同じ文字範囲を選択状態に保ち、Tabを続けて押せるようにする。
        new_start = selection_start + 1
        new_end = selection_end + len(blocks)
        if selection_forward:
            cursor.setPosition(new_start)
            cursor.setPosition(new_end, QTextCursor.KeepAnchor)
        else:
            cursor.setPosition(new_end)
            cursor.setPosition(new_start, QTextCursor.KeepAnchor)
        self.setTextCursor(cursor)
        return True

    def keyPressEvent(self, event):
        # 範囲選択中のTab: 選択されたすべての行をまとめてインデント
        if (
            event.key() == Qt.Key_Tab
            and event.modifiers() == Qt.NoModifier
            and self._indent_selected_lines()
        ):
            return

        # Ctrl+/
        if event.key() == Qt.Key_Slash and event.modifiers() == Qt.ControlModifier:
            cursor = self.textCursor()
            block_text = cursor.block().text()
            pos_in_block = cursor.positionInBlock()
            text_before_cursor = block_text[:pos_in_block]

            if text_before_cursor.endswith("」"):
                # 」の後: 次の行にタブ+////挿入、カーソルを//と//の間に
                cursor.insertText("\n\t////")
                cursor.movePosition(cursor.Left, cursor.MoveAnchor, 2)
            else:
                # それ以外: その場にタブ+////挿入、カーソルを//と//の間に
                cursor.insertText("\t////")
                cursor.movePosition(cursor.Left, cursor.MoveAnchor, 2)

            self.setTextCursor(cursor)
            return

        # Enter (//またはの後): 次の行にタブ+「」挿入、カーソルを「と」の間に
        if event.key() == Qt.Key_Return and event.modifiers() == Qt.NoModifier:
            cursor = self.textCursor()
            block_text = cursor.block().text()
            pos_in_block = cursor.positionInBlock()
            text_before_cursor = block_text[:pos_in_block]
            if text_before_cursor.endswith("//") or text_before_cursor.endswith("」"):
                cursor.insertText("\n\t「」")
                cursor.movePosition(cursor.Left, cursor.MoveAnchor, 1)
                self.setTextCursor(cursor)
                return

        super().keyPressEvent(event)


class EventEditorGUI(Win2000FramelessMainWindow):
    """PyQt5ベースのKSファイルエディタ"""

    def __init__(self):
        super().__init__()

        self.setWindowTitle("KSファイル イベントエディタ (PyQt5版)")
        self.setGeometry(100, 100, 1600, 900)

        # 現在編集中のファイル
        self.current_file = None
        self.current_file_path = None
        # stepメモ {step_index: memo_text}
        self.step_memos = {}
        # メモ変更フラグ（テキスト変更は document().isModified() で追跡）
        self.memos_modified = False

        # プレビューウィンドウ用のキュー(未使用だがPreviewWindowクラスとの互換性のため残す)
        self.command_queue = queue.Queue()
        self.status_queue = queue.Queue()

        # プレビュースレッド(未使用だがPreviewWindowクラスとの互換性のため残す)
        self.preview_thread = None
        self.preview_running = False

        # プレビュープロセス管理(別プロセス方式用 - macOS専用)
        self.preview_process = None

        # eventsフォルダのパス
        self.events_dir = os.path.join(project_root, "events")
        self.events_csv_path = os.path.join(self.events_dir, "events.csv")
        self.events_headers = []
        self.events_rows = []
        self.event_fields = {}
        self.current_event_id = None
        self.current_steps = []

        # 段落と行番号のマッピング
        self.paragraph_line_map = []

        # シグナルオブジェクト
        self.status_signal = StatusSignal()
        self.status_signal.status_received.connect(self.handle_status)
        self.preview_signal = PreviewSignal()
        self.preview_signal.preview_ready.connect(self._on_preview_ready)
        self._step_preview_process = None
        self._step_preview_stdout = ""
        self._step_preview_busy = False
        self._step_preview_active = None
        self._step_preview_pending = None
        self._step_preview_request_seq = 0
        self._closing = False

        # events.csvを読み込み
        self.load_events_metadata()

        # GUIを構築
        self.build_gui()

        # stepハイライト更新用タイマー
        self.step_highlight_timer = QTimer()
        self.step_highlight_timer.setSingleShot(True)
        self.step_highlight_timer.timeout.connect(self.update_step_highlights)

        # 自動保存タイマー (60秒)
        self.realtime_save_timer = QTimer(self)
        self.realtime_save_timer.setSingleShot(True)
        self.realtime_save_timer.timeout.connect(self._autosave)

        # ImageManagerを初期化（立ち絵プレビュー用）
        try:
            self.image_manager = ImageManager(DEBUG)
            self.image_manager.scan_image_paths(VIRTUAL_WIDTH, VIRTUAL_HEIGHT)
            logger.info("ImageManager初期化完了")
        except Exception as e:
            logger.warning(f"ImageManager初期化失敗: {e}")
            self.image_manager = None

        # ファイルリストを読み込み
        self.load_file_list()

        # 定期的にステータスキューをチェック
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.check_status_queue)
        self.status_timer.start(100)  # 100ms

        # Warm the renderer after the editor becomes responsive so the first
        # step preview does not also pay Python/Pygame startup costs.
        QTimer.singleShot(750, self._ensure_step_preview_process)

    def build_gui(self):
        """GUIを構築"""
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)

        toolbar = QToolBar()
        self.addToolBar(toolbar)

        save_action = QAction("保存", self)
        save_action.triggered.connect(self.save_file)
        save_action.setShortcut("Ctrl+S")
        toolbar.addAction(save_action)

        meta_save_action = QAction("メタデータ保存", self)
        meta_save_action.triggered.connect(self.save_event_metadata)
        toolbar.addAction(meta_save_action)

        new_event_action = QAction("新規イベント", self)
        new_event_action.triggered.connect(self.open_new_event_dialog)
        new_event_action.setShortcut("Ctrl+N")
        toolbar.addAction(new_event_action)

        reload_action = QAction("リロード", self)
        reload_action.triggered.connect(self.reload_preview)
        reload_action.setShortcut("F5")
        toolbar.addAction(reload_action)

        start_action = QAction("プレビュー開始", self)
        start_action.triggered.connect(self.start_preview)
        toolbar.addAction(start_action)

        stop_action = QAction("プレビュー停止", self)
        stop_action.triggered.connect(self.stop_preview)
        toolbar.addAction(stop_action)

        toolbar.addSeparator()

        toolbar.addWidget(QLabel("開始step:"))
        self.preview_step_entry = QLineEdit()
        self.preview_step_entry.setMaximumWidth(80)
        self.preview_step_entry.setText("1")
        self.paragraph_entry = self.preview_step_entry
        toolbar.addWidget(self.preview_step_entry)

        current_step_action = QAction("現在stepを指定", self)
        current_step_action.triggered.connect(self.set_preview_step_from_cursor)
        toolbar.addAction(current_step_action)

        toolbar.addSeparator()

        speaker_action = QAction("//話者名// (F2)", self)
        speaker_action.setShortcut("F2")
        speaker_action.triggered.connect(self._insert_speaker_template)
        toolbar.addAction(speaker_action)

        dialogue_action = QAction("「」挿入 (F3)", self)
        dialogue_action.setShortcut("F3")
        dialogue_action.triggered.connect(self._insert_dialogue_template)
        toolbar.addAction(dialogue_action)

        toolbar.addSeparator()

        self.current_paragraph_label = QLabel("現在: -")
        self.current_paragraph_label.setStyleSheet("color: blue;")
        toolbar.addWidget(self.current_paragraph_label)

        toolbar.addSeparator()

        self.status_label = QLabel("準備完了")
        self.status_label.setStyleSheet("color: green;")
        toolbar.addWidget(self.status_label)

        main_splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(main_splitter)

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        file_group = QGroupBox("KSファイル一覧")
        file_layout = QVBoxLayout()
        self.file_listbox = QListWidget()
        self.file_listbox.itemClicked.connect(self.on_file_select)
        self.file_listbox.setContextMenuPolicy(Qt.CustomContextMenu)
        self.file_listbox.customContextMenuRequested.connect(self.show_file_context_menu)
        file_layout.addWidget(self.file_listbox)

        new_event_button = QPushButton("+ 新規イベント")
        new_event_button.clicked.connect(self.open_new_event_dialog)
        file_layout.addWidget(new_event_button)

        file_group.setLayout(file_layout)
        left_layout.addWidget(file_group)
        main_splitter.addWidget(left_panel)

        right_splitter = QSplitter(Qt.Vertical)
        main_splitter.addWidget(right_splitter)

        metadata_group = QGroupBox("イベントメタデータ")
        metadata_layout = QFormLayout()
        self.event_fields = {}
        if self.events_headers:
            for header in self.events_headers:
                field = QLineEdit()
                if header == EVENT_DATETIME_HEADER:
                    field.setPlaceholderText(EVENT_DATETIME_FORMAT)
                metadata_layout.addRow(header, field)
                self.event_fields[header] = field
        else:
            metadata_layout.addRow(QLabel("events.csvが見つかりません"))
        metadata_group.setLayout(metadata_layout)
        right_splitter.addWidget(metadata_group)

        editor_group = QGroupBox("KSファイル編集")
        editor_layout = QVBoxLayout()
        self.text_editor = KSTextEditor()
        self.text_editor.setFont(QFont("Consolas", 11))
        self.text_editor.setAcceptRichText(False)
        self.text_editor.textChanged.connect(self.schedule_step_highlights)
        self.text_editor.textChanged.connect(self._schedule_realtime_save)
        self.text_editor.setContextMenuPolicy(Qt.CustomContextMenu)
        self.text_editor.customContextMenuRequested.connect(self.show_step_context_menu)
        editor_layout.addWidget(self.text_editor)
        editor_group.setLayout(editor_layout)
        right_splitter.addWidget(editor_group)

        main_splitter.setSizes([400, 1200])
        right_splitter.setSizes([250, 650])

    def load_file_list(self):
        """eventsフォルダからKSファイル一覧を読み込み"""
        self.file_listbox.clear()

        if not os.path.exists(self.events_dir):
            QMessageBox.critical(self, "エラー", f"eventsフォルダが見つかりません: {self.events_dir}")
            return

        ks_files = sorted([f for f in os.listdir(self.events_dir) if f.endswith('.ks')])

        for ks_file in ks_files:
            self.file_listbox.addItem(ks_file)

        print(f"KSファイルを読み込みました: {len(ks_files)}件")

    def show_file_context_menu(self, pos):
        """KSファイル一覧の右クリックメニューを表示"""
        item = self.file_listbox.itemAt(pos)
        if not item:
            return

        menu = QMenu(self)
        delete_action = menu.addAction("イベントを削除")
        selected = menu.exec_(self.file_listbox.mapToGlobal(pos))
        if selected == delete_action:
            self.delete_event(item.text())

    def delete_event(self, ks_filename):
        """KSファイルとevents.csvの行を削除する"""
        if not ks_filename:
            return

        event_id = os.path.splitext(ks_filename)[0]
        ks_path = os.path.join(self.events_dir, ks_filename)

        reply = QMessageBox.question(
            self,
            "確認",
            f"{ks_filename} を削除しますか?\nKSファイルとevents.csvの行を削除します。",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        errors = []
        if os.path.exists(ks_path):
            try:
                os.remove(ks_path)
            except Exception as e:
                errors.append(f"KSファイル削除: {e}")

        id_key = "イベントID"
        if id_key not in self.events_headers:
            id_key = next((h for h in self.events_headers if "ID" in h or "id" in h.lower()), None)
        if id_key:
            before_count = len(self.events_rows)
            self.events_rows = [row for row in self.events_rows if row.get(id_key) != event_id]
            if len(self.events_rows) != before_count:
                if not self.save_events_csv():
                    errors.append("events.csvの保存に失敗しました")
        else:
            errors.append("events.csvのイベントID列が見つかりません")

        self.load_file_list()

        if self.current_file_path == ks_path:
            self._clear_current_event()

        if errors:
            QMessageBox.warning(self, "警告", "削除中に問題が発生しました:\n" + "\n".join(errors))
        else:
            self.status_label.setText(f"削除完了: {ks_filename}")
            self.status_label.setStyleSheet("color: green;")

    def _clear_current_event(self):
        """削除時に現在の表示をクリアする"""
        self.current_file = None
        self.current_file_path = None
        self.current_event_id = None
        self.current_steps = []
        self.paragraph_line_map = []

        if self.text_editor:
            self.text_editor.blockSignals(True)
            self.text_editor.setPlainText("")
            self.text_editor.blockSignals(False)

        for field in self.event_fields.values():
            field.setText("")

        self.update_step_highlights()

    def load_events_metadata(self):
        """events.csvを読み込み、メタデータを保持する"""
        self.events_headers = []
        self.events_rows = []

        if not os.path.exists(self.events_csv_path):
            return

        try:
            with open(self.events_csv_path, 'r', encoding='utf-8-sig', newline='') as f:
                reader = csv.DictReader(f)
                self.events_headers = reader.fieldnames or []
                self.events_rows = list(reader)
        except Exception as e:
            print(f"events.csv読み込みエラー: {e}")

    def save_events_csv(self):
        """events.csvへ保存する"""
        if not self.events_headers:
            return False

        try:
            with open(self.events_csv_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=self.events_headers)
                writer.writeheader()
                for row in self.events_rows:
                    writer.writerow(row)
            return True
        except Exception as e:
            print(f"events.csv保存エラー: {e}")
            return False

    def load_event_metadata(self, event_id):
        """指定イベントのメタデータをフォームに反映"""
        self.current_event_id = event_id

        for field in self.event_fields.values():
            field.setText("")

        if not self.events_headers:
            return

        event_id_field = self.event_fields.get("イベントID")
        if event_id_field is not None:
            event_id_field.setText(event_id)

        row = next((r for r in self.events_rows if r.get("イベントID") == event_id), None)
        if not row:
            return

        for header in self.events_headers:
            field = self.event_fields.get(header)
            if field is not None:
                field.setText(row.get(header) or "")

    def save_event_metadata(self):
        """フォームの内容をevents.csvに保存"""
        if not self.event_fields or not self.events_headers:
            QMessageBox.warning(self, "警告", "events.csvが読み込めませんでした")
            return

        event_id_field = self.event_fields.get("イベントID")
        event_id = event_id_field.text().strip() if event_id_field else ""
        if not event_id:
            QMessageBox.warning(self, "警告", "イベントIDが空です")
            return

        event_datetime_field = self.event_fields.get(EVENT_DATETIME_HEADER)
        if event_datetime_field is not None:
            try:
                parse_event_datetime(event_datetime_field.text())
            except ValueError as exc:
                QMessageBox.warning(
                    self,
                    "イベント日時の入力エラー",
                    f"{exc}\n例: 1999-06-01 夜",
                )
                event_datetime_field.setFocus()
                return

        row = next((r for r in self.events_rows if r.get("イベントID") == event_id), None)
        if not row:
            row = {header: "" for header in self.events_headers}
            self.events_rows.append(row)

        for header in self.events_headers:
            field = self.event_fields.get(header)
            if field is not None:
                row[header] = field.text()

        if self.save_events_csv():
            self.current_event_id = event_id
            self.status_label.setText("メタデータ保存完了")
            self.status_label.setStyleSheet("color: green;")
        else:
            QMessageBox.critical(self, "エラー", "events.csvの保存に失敗しました")

    def open_new_event_dialog(self):
        """新規イベントの作成"""
        if not self.events_headers:
            QMessageBox.warning(self, "警告", "events.csvが読み込めませんでした")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("新規イベント追加")
        layout = QFormLayout(dialog)

        fields = {}
        for header in self.events_headers:
            field = QLineEdit()
            if header == EVENT_DATETIME_HEADER:
                field.setPlaceholderText(EVENT_DATETIME_FORMAT)
            layout.addRow(header, field)
            fields[header] = field

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)

        if dialog.exec_() != QDialog.Accepted:
            return

        event_id = fields.get("イベントID").text().strip() if fields.get("イベントID") else ""
        if not event_id:
            QMessageBox.warning(self, "警告", "イベントIDが空です")
            return

        event_datetime_field = fields.get(EVENT_DATETIME_HEADER)
        if event_datetime_field is not None:
            try:
                parse_event_datetime(event_datetime_field.text())
            except ValueError as exc:
                QMessageBox.warning(
                    self,
                    "イベント日時の入力エラー",
                    f"{exc}\n例: 1999-06-01 夜",
                )
                return

        if not os.path.exists(self.events_dir):
            os.makedirs(self.events_dir, exist_ok=True)

        ks_filename = f"{event_id}.ks"
        ks_path = os.path.join(self.events_dir, ks_filename)
        if os.path.exists(ks_path):
            QMessageBox.warning(self, "警告", f"既に存在するKSファイルです: {ks_filename}")
            return

        try:
            with open(ks_path, 'w', encoding='utf-8') as f:
                f.write("//speaker//\n")
                f.write("「セリフ」\n")
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"KSファイル作成に失敗しました:\n{e}")
            return

        row = {header: fields[header].text() for header in self.events_headers}
        if "イベントID" in row:
            row["イベントID"] = event_id
        self.events_rows.append(row)

        if not self.save_events_csv():
            QMessageBox.critical(self, "エラー", "events.csvの保存に失敗しました")
            return

        self.load_file_list()
        for i in range(self.file_listbox.count()):
            item = self.file_listbox.item(i)
            if item.text() == ks_filename:
                self.file_listbox.setCurrentRow(i)
                self.on_file_select(item)
                break

    def _has_unsaved_changes(self):
        """未保存の変更があるか判定"""
        return self.text_editor.document().isModified() or self.memos_modified

    def _restore_file_list_selection(self):
        """ファイルリストの選択を現在ファイルに戻す"""
        if not self.current_file:
            return
        for i in range(self.file_listbox.count()):
            if self.file_listbox.item(i).text() == self.current_file:
                self.file_listbox.blockSignals(True)
                self.file_listbox.setCurrentRow(i)
                self.file_listbox.blockSignals(False)
                break

    def _schedule_realtime_save(self):
        """変更検知ごとに1秒デバウンスして自動保存"""
        if self.current_file_path:
            self.realtime_save_timer.start(1000)

    def _autosave(self):
        """自動保存（変更検知から1秒後）"""
        if not self.current_file_path:
            return
        if not self._has_unsaved_changes():
            return
        try:
            display_text = self.text_editor.toPlainText()
            content = self._inject_memos_into_text(display_text)
            with open(self.current_file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            self.text_editor.document().setModified(False)
            self.memos_modified = False
            self.status_label.setText(f"自動保存: {self.current_file}")
            self.status_label.setStyleSheet("color: gray;")
            print(f"[自動保存] {self.current_file_path}")
        except Exception as e:
            print(f"[自動保存エラー] {e}")

    def on_file_select(self, item):
        """ファイルが選択された時の処理"""
        filename = item.text()
        filepath = os.path.join(self.events_dir, filename)

        # 同じファイルの再選択はスキップ
        if filepath == self.current_file_path:
            return

        # 未保存チェック
        if self._has_unsaved_changes() and self.current_file_path:
            # A pending autosave must not fire against a different file while
            # the user is deciding whether to keep the current edit.
            self.realtime_save_timer.stop()
            reply = QMessageBox.question(
                self,
                "未保存の変更",
                f"{self.current_file} に未保存の変更があります。\n保存しますか？",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
            )
            if reply == QMessageBox.Save:
                if not self.save_file():
                    self._restore_file_list_selection()
                    return
            elif reply == QMessageBox.Cancel:
                # リストの選択を元に戻す
                self._restore_file_list_selection()
                return
            # Discard はそのままロードへ

        self.realtime_save_timer.stop()
        if not self.load_file(filepath):
            self._restore_file_list_selection()
            return
        event_id = os.path.splitext(filename)[0]
        self.load_event_metadata(event_id)
        self._open_initial_step_editor()

    def _open_initial_step_editor(self):
        """Open the first parsed step immediately after a KS file is loaded."""
        if not self.current_steps:
            return False
        self.open_step_editor(self.current_steps[0])
        return True

    def load_file(self, filepath):
        """ファイルを読み込んでエディタに表示"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                raw_content = f.read()

            # ;@memo:行を除去した表示用テキストをセット
            display_content = self._load_step_memos(raw_content)
            self.text_editor.setPlainText(display_content)
            self.text_editor.document().setModified(False)
            self.memos_modified = False
            self.current_file = os.path.basename(filepath)
            self.current_file_path = filepath

            self.build_paragraph_line_map()
            self.update_step_highlights()

            self.status_label.setText(f"読み込み完了: {self.current_file}")
            self.status_label.setStyleSheet("color: green;")
            print(f"📖 ファイル読み込み: {filepath}")
            return True

        except Exception as e:
            QMessageBox.critical(self, "エラー", f"ファイル読み込みエラー:\n{e}")
            print(f"❌ ファイル読み込みエラー: {e}")
            return False

    def build_paragraph_line_map(self):
        """KSファイルの行番号と段落番号のマッピングを構築"""
        if not self.current_file_path:
            return

        try:
            dialogue_loader = DialogueLoader(debug=False)
            raw_dialogue_data = dialogue_loader.load_dialogue_from_ks(self.current_file_path)

            if not raw_dialogue_data:
                return

            dialogue_data = normalize_dialogue_data(raw_dialogue_data)
            if not dialogue_data:
                return

            with open(self.current_file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            self.paragraph_line_map = []
            paragraph_count = 1

            for line_num, line in enumerate(lines, start=1):
                stripped = line.strip()
                if not stripped or stripped.startswith('//') or stripped.startswith(';'):
                    continue
                if stripped.startswith('「'):
                    self.paragraph_line_map.append((line_num, paragraph_count))
                    paragraph_count += 1

            print(f"[MAP] 段落マッピング構築完了: {len(self.paragraph_line_map)}個のテキスト行")

        except Exception as e:
            print(f"[MAP] 段落マッピング構築エラー: {e}")
            self.paragraph_line_map = []

    def schedule_step_highlights(self):
        """stepハイライトの更新をデバウンスする"""
        if not hasattr(self, "step_highlight_timer"):
            return
        self.step_highlight_timer.start(400)

    def update_step_highlights(self):
        """KSテキストからstep単位のハイライトを更新"""
        if not self.text_editor:
            return

        text = self.text_editor.toPlainText()
        steps = self._parse_steps_from_ks_text(text)
        # メモをステップにオーバーレイ
        for step in steps:
            idx = step["step_index"]
            step["memo"] = self.step_memos.get(idx, "")
        self.current_steps = steps

        selections = []
        colors = [QColor(255, 248, 220), QColor(235, 245, 255)]
        memo_color = QColor(180, 230, 180)

        for idx, step in enumerate(steps):
            start_line = step["start_line"]
            end_line = step["end_line"]
            if start_line is None or end_line is None:
                continue
            if end_line < start_line:
                continue

            cursor = QTextCursor(self.text_editor.document())
            start_block = self.text_editor.document().findBlockByNumber(start_line)
            end_block = self.text_editor.document().findBlockByNumber(end_line)
            if not start_block.isValid() or not end_block.isValid():
                continue

            cursor.setPosition(start_block.position())
            cursor.setPosition(end_block.position() + end_block.length(), QTextCursor.KeepAnchor)

            fmt = QTextCharFormat()
            if step.get("memo"):
                fmt.setBackground(memo_color)
            else:
                fmt.setBackground(colors[idx % 2])

            selection = QTextEdit.ExtraSelection()
            selection.cursor = cursor
            selection.format = fmt
            selections.append(selection)

        self.text_editor.setExtraSelections(selections)

    def _parse_steps_from_ks_text(self, text):
        """KSテキストを簡易解析してstepの行範囲を算出"""
        lines = text.splitlines()
        steps = []
        pending_action_lines = []
        last_speaker_line = None
        last_speaker = ""
        def add_step(
            start_line,
            end_line,
            speaker="",
            body="",
            has_scroll_stop=False,
            dialogue_line=None,
            force_female=False,
            standalone=False,
        ):
            step_index = len(steps)
            steps.append(
                {
                    "step_index": step_index,
                    "start_line": start_line,
                    "end_line": end_line,
                    "speaker": speaker,
                    "body": body,
                    "has_scroll_stop": has_scroll_stop,
                    "force_female": force_female,
                    "dialogue_line": dialogue_line,
                    "memo": "",
                    "standalone": bool(standalone),
                }
            )

        def flush_actions(end_line, standalone=False):
            nonlocal pending_action_lines
            if pending_action_lines:
                add_step(
                    min(pending_action_lines),
                    end_line,
                    standalone=standalone,
                )
                pending_action_lines = []

        for i, raw_line in enumerate(lines):
            line = raw_line.strip()
            if not line:
                continue
            if line.lower() == STANDALONE_STEP_MARKER:
                flush_actions(i, standalone=True)
                continue
            if line.startswith(";"):
                continue

            if line.startswith("//") and line.endswith("//") and len(line) > 4:
                last_speaker_line = i
                last_speaker = line.strip("/").strip()
                continue

            if line.startswith("[") and line.endswith("]"):
                tag_body = line[1:-1].strip()
                tag_name = tag_body.split()[0].lower() if tag_body else ""

                if tag_name in ("if", "endif", "flag_set", "choice", "event_control"):
                    start_line = min(pending_action_lines + [i]) if pending_action_lines else i
                    add_step(start_line, i)
                    pending_action_lines = []
                elif tag_name == "scroll-stop":
                    if steps:
                        prev = steps[-1]
                        prev["end_line"] = max(prev["end_line"], i)
                        prev["has_scroll_stop"] = True
                    else:
                        add_step(i, i)
                else:
                    pending_action_lines.append(i)
                continue

            if "「" in line and "」" in line:
                body = ""
                has_scroll_stop = "[scroll-stop]" in line
                force_female = "[female]" in line
                start_idx = line.find("「")
                end_idx = line.rfind("」")
                if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                    body = line[start_idx + 1 : end_idx]

                start_line = i
                if pending_action_lines:
                    start_line = min(start_line, min(pending_action_lines))
                if last_speaker_line is not None:
                    start_line = min(start_line, last_speaker_line)
                add_step(
                    start_line,
                    i,
                    speaker=last_speaker,
                    body=body,
                    has_scroll_stop=has_scroll_stop,
                    dialogue_line=i,
                    force_female=force_female,
                )
                pending_action_lines = []
                last_speaker_line = None
                continue

        if pending_action_lines:
            add_step(min(pending_action_lines), max(pending_action_lines))

        return steps

    def _find_step_for_line(self, line_number):
        """行番号から該当stepを取得する"""
        steps = getattr(self, "current_steps", None)
        if not steps:
            return None
        for step in steps:
            if step["start_line"] <= line_number <= step["end_line"]:
                return step
        return None

    def show_step_context_menu(self, pos):
        """step用の右クリックメニューを表示"""
        cursor = self.text_editor.cursorForPosition(pos)
        line_number = cursor.blockNumber()
        step = self._find_step_for_line(line_number)
        has_steps = bool(getattr(self, "current_steps", None))

        menu = QMenu(self)
        edit_action = menu.addAction("このstepを編集")
        add_before_action = menu.addAction("このstepの前に追加")
        add_after_action = menu.addAction("このstepの後に追加")
        add_here_action = None
        if not step and not has_steps:
            add_here_action = menu.addAction("ここにstepを追加")
        menu.addSeparator()
        toggle_scroll_action = menu.addAction("scroll-stopを付与/解除")

        if not step:
            edit_action.setEnabled(False)
            add_before_action.setEnabled(False)
            add_after_action.setEnabled(False)
            toggle_scroll_action.setEnabled(False)

        selected = menu.exec_(self.text_editor.mapToGlobal(pos))
        if not selected:
            return

        if selected == add_here_action:
            self._insert_step_template_at_line(line_number)
            return

        if not step:
            return

        if selected == edit_action:
            self.open_step_editor(step)
            return

        if selected == add_before_action or selected == add_after_action:
            insert_before = selected == add_before_action
            self._insert_step_template(step, insert_before=insert_before)
            return

        if selected == toggle_scroll_action:
            self._toggle_scroll_stop(step)

    def _toggle_scroll_stop(self, step):
        """scroll-stopの付与/解除を行う"""
        dialogue_line = step.get("dialogue_line")
        if dialogue_line is None:
            QMessageBox.warning(self, "警告", "セリフ行がないstepにはscroll-stopを付けられません。")
            return

        lines = self.text_editor.toPlainText().splitlines()
        if dialogue_line < 0 or dialogue_line >= len(lines):
            return

        line = lines[dialogue_line]
        if "[scroll-stop]" in line:
            lines[dialogue_line] = line.replace("[scroll-stop]", "").rstrip()
        else:
            lines[dialogue_line] = line.rstrip() + "[scroll-stop]"

        self.text_editor.blockSignals(True)
        self.text_editor.setPlainText("\n".join(lines))
        self.text_editor.blockSignals(False)
        self.update_step_highlights()

    def open_step_editor(self, step):
        """step編集ダイアログを開く"""
        target_index = step.get("step_index") if step else None
        if target_index is None:
            return

        current_step = self.current_steps[target_index]
        try:
            all_step_actions = []
            source_lines = self.text_editor.toPlainText().splitlines()
            for parsed_step in self.current_steps:
                parsed_actions = self._extract_actions_from_step(
                    parsed_step,
                    source_lines=source_lines,
                )
                all_step_actions.append(parsed_actions)
                # CharaCompositePreviewDialog consumes this explicit cache
                # when resolving the selected character's prior state.
                parsed_step["_actions_cache"] = [
                    {
                        "tag": tag,
                        "params": params,
                    }
                    for tag, params in (
                        parse_step_action(action) for action in parsed_actions
                    )
                    if tag
                ]

            actions = all_step_actions[target_index]
            im = getattr(self, 'image_manager', None)
            dialog = StepEditorDialog(
                self,
                current_step,
                actions=actions,
                all_steps=self.current_steps,
                all_step_actions=all_step_actions,
                step_index=target_index,
                image_manager=im,
            )
        except Exception as e:
            import traceback
            QMessageBox.critical(self, 'stepエディタエラー',
                f'エラーが発生しました：\n{e}\n\n{traceback.format_exc()}')
            return

        if dialog.exec_() != QDialog.Accepted:
            return

        speaker, body, scroll_stop, force_female = dialog.get_dialogue_values()
        memo = dialog.get_memo()
        actions = dialog.get_actions()
        self._apply_step_update(
            dialog.step,
            speaker,
            body,
            scroll_stop,
            force_female,
            actions,
            memo,
            standalone=dialog.get_standalone(),
        )

    def _insert_step_template(self, step, insert_before=True):
        """指定stepの前後にテンプレートstepを挿入する"""
        if not step:
            return None

        lines = self.text_editor.toPlainText().splitlines()
        start_line = step.get("start_line", 0)
        end_line = step.get("end_line", start_line)
        insert_at = start_line if insert_before else end_line + 1
        step_index = step.get("step_index", 0)
        inserted_step_index = step_index if insert_before else step_index + 1

        template_lines = [
            "; --- new step ---",
            "//speaker//",
            "「セリフ」",
            "",
        ]

        if insert_at < 0:
            insert_at = 0
        if insert_at > len(lines):
            insert_at = len(lines)

        # 備考はstep番号をキーにしているため、途中挿入より後ろを1つずらす。
        shifted_memos = {
            index + (1 if index >= inserted_step_index else 0): memo
            for index, memo in self.step_memos.items()
        }
        if shifted_memos != self.step_memos:
            self.step_memos = shifted_memos
            self.memos_modified = True

        new_lines = lines[:insert_at] + template_lines + lines[insert_at:]
        self.text_editor.blockSignals(True)
        self.text_editor.setPlainText("\n".join(new_lines))
        self.text_editor.blockSignals(False)
        self.text_editor.document().setModified(True)
        self.update_step_highlights()
        self._schedule_realtime_save()
        return inserted_step_index

    def _insert_step_template_at_line(self, line_number):
        """stepが無い場合に、指定行へテンプレートstepを挿入する"""
        if not self.text_editor:
            return

        lines = self.text_editor.toPlainText().splitlines()
        insert_at = max(0, min(line_number, len(lines)))

        template_lines = [
            "; --- new step ---",
            "//speaker//",
            "「セリフ」",
            "",
        ]

        new_lines = lines[:insert_at] + template_lines + lines[insert_at:]
        self.text_editor.blockSignals(True)
        self.text_editor.setPlainText("\n".join(new_lines))
        self.text_editor.blockSignals(False)
        self.text_editor.document().setModified(True)
        self.update_step_highlights()
        self._schedule_realtime_save()
        return 0

    def _build_step_update_text(
        self,
        original_text,
        step,
        speaker,
        body,
        scroll_stop,
        force_female,
        actions,
        warn_scroll_stop=True,
        memo="",
        standalone=False,
    ):
        if not step:
            return original_text

        lines = original_text.splitlines()
        start_line = step.get("start_line", 0)
        end_line = step.get("end_line", start_line)
        if start_line < 0 or start_line >= len(lines):
            return original_text
        region = lines[start_line : end_line + 1]

        def is_speaker_line(text):
            return text.startswith("//") and text.endswith("//") and len(text) > 4

        def is_dialogue_line(text):
            return "「" in text and "」" in text

        def is_action_line(text):
            return text.startswith("[") and text.endswith("]")

        other_lines = []
        speaker_indent = None
        dialogue_indent = None
        for line in region:
            stripped = line.strip()
            if not stripped:
                other_lines.append(line)
                continue
            if is_action_line(stripped):
                continue
            if is_speaker_line(stripped):
                if speaker_indent is None:
                    speaker_indent = line[: len(line) - len(line.lstrip())]
                continue
            if is_dialogue_line(stripped):
                if dialogue_indent is None:
                    dialogue_indent = line[: len(line) - len(line.lstrip())]
                continue
            if stripped.lower() == STANDALONE_STEP_MARKER:
                continue
            other_lines.append(line)

        new_region = []
        new_region.extend(other_lines)

        for action in actions or []:
            tag = action.strip()
            if not tag:
                continue
            if tag.startswith("[") and tag.endswith("]"):
                tag = tag[1:-1].strip()
            if tag.lower() == "scroll-stop":
                continue
            new_region.append(f"[{tag}]")

        if standalone and actions:
            new_region.append(STANDALONE_STEP_MARKER)

        if speaker:
            # Rebuilding a step must not discard indentation that was applied
            # to its speaker/dialogue lines in the source editor.
            indent = speaker_indent if speaker_indent is not None else (dialogue_indent or "")
            new_region.append(f"{indent}//{speaker}//")

        if body:
            indent = dialogue_indent if dialogue_indent is not None else (speaker_indent or "")
            line_text = f"{indent}「{body}」"
            if force_female:
                line_text += "[female]"
            if scroll_stop:
                line_text += "[scroll-stop]"
            new_region.append(line_text)
        elif scroll_stop and warn_scroll_stop:
            QMessageBox.warning(self, "Warning", "Cannot set scroll-stop without dialogue text.")

        new_lines = lines[:start_line] + new_region + lines[end_line + 1 :]
        return "\n".join(new_lines)

    # ------------------------------------------------------------------ #
    # デュアルバッファメモ管理
    # ------------------------------------------------------------------ #

    @staticmethod
    def _extract_memos_from_raw(raw_text):
        """生テキストから;@memo:行を除去した表示用テキストと
        {display_line_index: memo_text} のマップを返す"""
        lines = raw_text.splitlines(keepends=True)
        display_lines = []
        pending_memo = None
        memo_by_display_line = {}
        for line in lines:
            if line.strip().startswith(";@memo:"):
                pending_memo = line.strip()[7:].strip()
            else:
                if pending_memo is not None:
                    memo_by_display_line[len(display_lines)] = pending_memo
                    pending_memo = None
                display_lines.append(line)
        return "".join(display_lines), memo_by_display_line

    def _load_step_memos(self, raw_text):
        """生テキストから;@memo:行を抽出しself.step_memosを賭新、
        エディタ表示用テキストを返す"""
        display_text, memo_by_display_line = self._extract_memos_from_raw(raw_text)
        if not memo_by_display_line:
            self.step_memos = {}
            return display_text
        steps = self._parse_steps_from_ks_text(display_text)
        memos = {}
        for display_line, memo_text in memo_by_display_line.items():
            matched = False
            for step in steps:
                if step["start_line"] == display_line:
                    memos[step["step_index"]] = memo_text
                    matched = True
                    break
            if not matched:
                for step in steps:
                    if step["start_line"] <= display_line <= step["end_line"]:
                        memos[step["step_index"]] = memo_text
                        break
        self.step_memos = memos
        return display_text

    def _inject_memos_into_text(self, display_text):
        """表示用テキストにself.step_memosの;@memo:行を注入して
        KS保存用テキストを返す"""
        if not self.step_memos:
            return display_text
        steps = self._parse_steps_from_ks_text(display_text)
        insertions = {}
        for step in steps:
            idx = step["step_index"]
            if idx in self.step_memos and self.step_memos[idx]:
                insertions[step["start_line"]] = self.step_memos[idx]
        if not insertions:
            return display_text
        lines = display_text.splitlines(keepends=True)
        result = []
        for i, line in enumerate(lines):
            if i in insertions:
                result.append(f";@memo: {insertions[i]}\n")
            result.append(line)
        return "".join(result)

    def _apply_step_update(
        self,
        step,
        speaker,
        body,
        scroll_stop,
        force_female,
        actions,
        memo="",
        standalone=False,
    ):
        """stepを更新してエディタに反映"""
        old_text = self.text_editor.toPlainText()
        was_modified = self.text_editor.document().isModified()
        new_text = self._build_step_update_text(
            old_text,
            step,
            speaker,
            body,
            scroll_stop,
            force_female,
            actions,
            warn_scroll_stop=True,
            standalone=standalone,
        )

        scrollbar = self.text_editor.verticalScrollBar()
        old_scroll = scrollbar.value() if scrollbar else None
        cursor = self.text_editor.textCursor()
        old_pos = cursor.position()
        old_anchor = cursor.anchor()
        self.text_editor.blockSignals(True)
        self.text_editor.setPlainText(new_text)
        if scrollbar and old_scroll is not None:
            scrollbar.setValue(old_scroll)
        doc_len = max(0, self.text_editor.document().characterCount() - 1)
        new_pos = min(old_pos, doc_len)
        new_anchor = min(old_anchor, doc_len)
        cursor.setPosition(new_anchor)
        cursor.setPosition(new_pos, QTextCursor.KeepAnchor)
        self.text_editor.setTextCursor(cursor)
        self.text_editor.blockSignals(False)
        text_changed = new_text != old_text
        self.text_editor.document().setModified(was_modified or text_changed)
        # メモをメモリに保存（ディスクには保存時に注入される）
        step_index = step["step_index"]
        old_memo = self.step_memos.get(step_index, "")
        if memo:
            self.step_memos[step_index] = memo
        else:
            self.step_memos.pop(step_index, None)
        if memo != old_memo:
            self.memos_modified = True
        self.update_step_highlights()
        if text_changed or memo != old_memo:
            self._schedule_realtime_save()

    def _run_step_preview(self, source_path, step_index, dialog, temp_path=None):
        preview_script = os.path.join(
            project_root, "tools", "dialogue_snapshot_renderer.py"
        )
        if not os.path.exists(preview_script):
            return

        out_dir = os.path.join(project_root, "debug", "step_previews")
        os.makedirs(out_dir, exist_ok=True)
        basename = os.path.splitext(os.path.basename(self.current_file_path or source_path))[0]
        self._step_preview_request_seq += 1
        request_id = self._step_preview_request_seq
        out_path = os.path.join(
            out_dir,
            f".{basename}_step_{step_index + 1:04d}_{request_id}.png",
        )
        request = {
            "request_id": request_id,
            "source_path": source_path,
            "step_index": step_index + 1,
            "out_path": out_path,
            "dialog": dialog,
            "temp_path": temp_path,
        }
        dialog._preview_request_id = request_id

        dialog.preview_label.setText("Generating preview...")

        # Keep only the newest queued edit. The active render is allowed to
        # finish, but its result is ignored when a newer request exists.
        if self._step_preview_pending:
            self._discard_step_preview_request(self._step_preview_pending)
        self._step_preview_pending = request
        self._ensure_step_preview_process()
        self._dispatch_pending_step_preview()

    @staticmethod
    def _remove_preview_file(path):
        if not path:
            return
        try:
            os.remove(path)
        except OSError:
            pass

    def _discard_step_preview_request(self, request):
        if not request:
            return
        self._remove_preview_file(request.get("temp_path"))
        self._remove_preview_file(request.get("out_path"))

    def _ensure_step_preview_process(self):
        process = self._step_preview_process
        if process is not None and process.state() != QProcess.NotRunning:
            return

        process = QProcess(self)
        process.setWorkingDirectory(project_root)
        process.setProgram(sys.executable)
        process.setArguments([
            os.path.join(
                project_root, "tools", "dialogue_snapshot_renderer.py"
            ),
            "--server",
        ])
        process.started.connect(self._dispatch_pending_step_preview)
        process.readyReadStandardOutput.connect(self._read_step_preview_output)
        process.readyReadStandardError.connect(self._read_step_preview_error)
        process.finished.connect(self._step_preview_process_finished)
        self._step_preview_process = process
        self._step_preview_stdout = ""
        process.start()

    def _dispatch_pending_step_preview(self):
        process = self._step_preview_process
        if (
            self._step_preview_busy
            or not self._step_preview_pending
            or process is None
            or process.state() != QProcess.Running
        ):
            return

        request = self._step_preview_pending
        self._step_preview_pending = None
        self._step_preview_active = request
        self._step_preview_busy = True
        payload = {
            "request_id": request["request_id"],
            "source_path": request["source_path"],
            "event_id": self.current_event_id,
            "step_index": request["step_index"],
            "out_path": request["out_path"],
            # ゲーム画面の仮想解像度は4:3。16:9へ直接リサイズすると
            # スクリーンショット内の背景・立ち絵・UIが横に引き伸ばされる。
            "output_size": [640, 480],
        }
        # Keep the JSON-line protocol ASCII-safe. Windows child processes can
        # otherwise decode a UTF-8 workspace path with the active ANSI code
        # page before the snapshot worker gets a chance to use it.
        process.write((json.dumps(payload, ensure_ascii=True) + "\n").encode("ascii"))

    def _read_step_preview_output(self):
        process = self._step_preview_process
        if process is None:
            return
        chunk = bytes(process.readAllStandardOutput()).decode("utf-8", errors="replace")
        self._step_preview_stdout += chunk
        lines = self._step_preview_stdout.split("\n")
        self._step_preview_stdout = lines.pop()
        for line in lines:
            marker = "@@PREVIEW@@"
            if not line.startswith(marker):
                if line.strip():
                    image_markers = (
                        "[IMG_REQUEST]",
                        "[IMG_CACHE_HIT]",
                        "[IMG_LOAD]",
                        "[IMG_ERROR]",
                    )
                    if line.startswith(image_markers):
                        logger.info("step snapshot worker: %s", line)
                    else:
                        logger.debug("step snapshot worker: %s", line)
                continue
            try:
                message = json.loads(line[len(marker):])
            except json.JSONDecodeError:
                continue
            if message.get("type") == "result":
                logger.info(
                    "step snapshot result: request=%s success=%s exists=%s out=%s message=%s",
                    message.get("request_id"),
                    message.get("success"),
                    os.path.exists(message.get("out_path") or ""),
                    message.get("out_path"),
                    message.get("message") or "",
                )
                self._finish_step_preview_request(message)

    def _read_step_preview_error(self):
        process = self._step_preview_process
        if process is None:
            return
        output = bytes(process.readAllStandardError()).decode("utf-8", errors="replace").strip()
        if output:
            logger.debug("step preview worker: %s", output)

    def _finish_step_preview_request(self, result):
        request = self._step_preview_active
        if not request or result.get("request_id") != request.get("request_id"):
            return

        dialog = request.get("dialog")
        is_latest = (
            dialog is not None
            and getattr(dialog, "_preview_request_id", None) == request["request_id"]
        )
        if is_latest:
            self._on_preview_ready(
                dialog,
                result.get("out_path", request["out_path"]),
                bool(result.get("success")),
                result.get("message", ""),
            )
        # QPixmap normally loads synchronously, but deleting the worker output
        # immediately here can leave the label without a usable backing file
        # on some Qt/Windows combinations.  Keep the rendered PNG until the
        # next preview request (or editor shutdown); only the edited temp KS
        # file is safe to remove now.
        if result.get("success"):
            self._remove_preview_file(request.get("temp_path"))
            request["temp_path"] = None
        else:
            logger.error(
                "step snapshot failed; source kept for reproduction: %s",
                request.get("source_path"),
            )
        self._step_preview_active = None
        self._step_preview_busy = False
        self._dispatch_pending_step_preview()

    def _step_preview_process_finished(self, exit_code, exit_status):
        request = self._step_preview_active
        if request:
            dialog = request.get("dialog")
            if (
                dialog is not None
                and getattr(dialog, "_preview_request_id", None) == request["request_id"]
                and dialog.isVisible()
            ):
                dialog.preview_label.setText("Preview worker stopped unexpectedly.")
            self._discard_step_preview_request(request)
        self._step_preview_active = None
        self._step_preview_busy = False
        process = self._step_preview_process
        self._step_preview_process = None
        if process is not None:
            process.deleteLater()
        if self._step_preview_pending and not self._closing:
            self._ensure_step_preview_process()

    def _on_preview_ready(self, dialog, image_path, success, message):
        if not dialog or not hasattr(dialog, "preview_label"):
            return
        if not success:
            dialog.preview_label.setText(message)
            return
        dialog.set_preview_image(image_path)

    def _generate_step_preview(self, step_index, dialog):
        """step????????????????"""
        if not self.current_file_path:
            return
        if step_index is None:
            return
        self._run_step_preview(self.current_file_path, step_index, dialog)

    def _preview_step_from_dialog(self, step, dialog):
        if not step or step.get("step_index") is None:
            return
        if not self.current_file_path:
            return
        speaker, body, scroll_stop, force_female = dialog.get_dialogue_values()
        memo = dialog.get_memo()
        actions = dialog.get_actions()
        temp_text = self._build_step_update_text(
            self.text_editor.toPlainText(),
            step,
            speaker,
            body,
            scroll_stop,
            force_female,
            actions,
            warn_scroll_stop=False,
            memo=memo,
            standalone=dialog.get_standalone(),
        )
        out_dir = os.path.join(project_root, "debug", "step_previews")
        os.makedirs(out_dir, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            suffix=".ks",
            delete=False,
            dir=out_dir,
        ) as handle:
            handle.write(temp_text)
            temp_path = handle.name
        self._run_step_preview(temp_path, step["step_index"], dialog, temp_path=temp_path)

    def _extract_actions_from_step(self, step, source_lines=None):
        """step????KS???????"""
        if not step:
            return []

        lines = (
            source_lines
            if source_lines is not None
            else self.text_editor.toPlainText().splitlines()
        )
        start_line = step.get("start_line", 0)
        end_line = step.get("end_line", start_line)
        if start_line < 0 or start_line >= len(lines):
            return []

        actions = []
        for i in range(start_line, min(end_line + 1, len(lines))):
            stripped = lines[i].strip()
            if stripped.startswith("[") and stripped.endswith("]"):
                tag = stripped[1:-1].strip()
                if not tag:
                    continue
                tag_name = tag.split()[0].lower()
                if tag_name == "scroll-stop":
                    continue
                actions.append(tag)
        return actions

    def _insert_speaker_template(self):
        """//名前//を行頭に挿入し「名前」部分を選択状態にする"""
        if not self.text_editor.hasFocus():
            self.text_editor.setFocus()
        cursor = self.text_editor.textCursor()
        cursor.movePosition(QTextCursor.StartOfLine)
        insert_pos = cursor.position()
        cursor.insertText("//名前//\n")
        # 「名前」部分を選択
        cursor.setPosition(insert_pos + 2)
        cursor.setPosition(insert_pos + 4, QTextCursor.KeepAnchor)
        self.text_editor.setTextCursor(cursor)

    def _insert_dialogue_template(self):
        """「」をカーソル位置に挿入し内側にカーソルを置く"""
        if not self.text_editor.hasFocus():
            self.text_editor.setFocus()
        cursor = self.text_editor.textCursor()
        pos = cursor.position()
        cursor.insertText("「」")
        cursor.setPosition(pos + 1)
        self.text_editor.setTextCursor(cursor)

    def save_file(self):
        """現在のファイルを保存"""
        if not self.current_file_path:
            QMessageBox.warning(self, "警告", "保存するファイルが選択されていません")
            return False

        try:
            display_text = self.text_editor.toPlainText()
            # ;@memo:行を注入してから保存
            content = self._inject_memos_into_text(display_text)

            with open(self.current_file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            self.build_paragraph_line_map()
            if self.event_fields:
                self.save_event_metadata()

            self.text_editor.document().setModified(False)
            self.memos_modified = False
            self.status_label.setText(f"保存完了: {self.current_file}")
            self.status_label.setStyleSheet("color: green;")
            print(f"ファイル保存: {self.current_file_path}")

            QMessageBox.information(self, "成功", f"{self.current_file} を保存しました")
            return True

        except Exception as e:
            QMessageBox.critical(self, "エラー", f"ファイル保存エラー:\n{e}")
            print(f"ファイル保存エラー: {e}")
            return False

    def set_preview_step_from_cursor(self):
        cursor = self.text_editor.textCursor()
        step = self._find_step_for_line(cursor.blockNumber())
        if not step:
            QMessageBox.warning(self, "警告", "カーソル位置にstepがありません")
            return
        self.preview_step_entry.setText(str(step["step_index"] + 1))

    def _requested_preview_step(self):
        try:
            step_number = int(self.preview_step_entry.text().strip())
        except ValueError:
            QMessageBox.warning(self, "警告", "開始stepは整数で指定してください")
            return None
        total_steps = len(getattr(self, "current_steps", None) or [])
        if step_number < 1 or (total_steps and step_number > total_steps):
            QMessageBox.warning(
                self,
                "警告",
                f"開始stepは1～{total_steps or 1}で指定してください",
            )
            return None
        return step_number

    def _preview_player_command(self, preview_script, start_step):
        return [
            sys.executable,
            preview_script,
            self.current_file_path,
            "--step",
            str(start_step),
        ]

    def start_preview(self):
        """ダイアログプレビューを別プロセスとして起動(macOS専用)"""
        logger.info("start_preview呼び出し(dialogue_preview_player.py起動)")
        try:
            if not self.current_file_path:
                QMessageBox.warning(self, "警告", "ファイルが選択されていません")
                return

            start_step = self._requested_preview_step()
            if start_step is None:
                return

            # 既存のプレビュープロセスがあれば先に終了
            if self.preview_process and self.preview_process.poll() is None:
                reply = QMessageBox.question(
                    self,
                    "プレビュー起動",
                    "既にプレビューが起動中です。\n再起動しますか?",
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply == QMessageBox.No:
                    return

                # 既存プロセスを終了
                logger.info(f"既存プレビュープロセス (PID={self.preview_process.pid}) を終了")
                self.preview_process.terminate()
                try:
                    self.preview_process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    logger.warning("プレビュープロセスが応答しないため強制終了")
                    self.preview_process.kill()
                    self.preview_process.wait()
                self.preview_process = None

            # 保存確認
            reply = QMessageBox.question(
                self,
                "プレビュー",
                f"{self.current_file} を保存してからプレビューしますか?\n\n"
                "※ macOSではエディタ内プレビューは利用できないため、\n"
                "別ウィンドウでプレビューを起動します。",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
            )

            if reply == QMessageBox.Cancel:
                return
            elif reply == QMessageBox.Yes:
                self.save_file()

            # 対話再生専用プレイヤーを別プロセスとして起動
            preview_script = os.path.join(
                project_root, "tools", "dialogue_preview_player.py"
            )

            if not os.path.exists(preview_script):
                QMessageBox.critical(
                    self,
                    "エラー",
                    f"プレビュースクリプトが見つかりません:\n{preview_script}"
                )
                return

            # プレビュープロセスを起動して保存
            preview_command = self._preview_player_command(preview_script, start_step)
            if platform.system() == 'Darwin':  # macOS
                self.preview_process = subprocess.Popen(preview_command)
                self.preview_running = True
                self.status_label.setText(f"プレビュー起動中 (PID={self.preview_process.pid})")
                self.status_label.setStyleSheet("color: green;")
                logger.info(f"プレビュープロセス起動: PID={self.preview_process.pid}")
                QMessageBox.information(
                    self,
                    "プレビュー起動",
                    f"プレビューを起動しました。\n\n"
                    f"ファイル: {self.current_file}\n"
                    f"PID: {self.preview_process.pid}\n\n"
                    "別ウィンドウでダイアログをプレビューできます。"
                )
            else:
                self.preview_process = subprocess.Popen(preview_command)
                self.preview_running = True
                self.status_label.setText(f"プレビュー起動中 (PID={self.preview_process.pid})")
                self.status_label.setStyleSheet("color: green;")
                logger.info(f"プレビュープロセス起動: PID={self.preview_process.pid}")

            print(
                f"▶ プレビュー起動: {preview_script} {self.current_file_path} "
                f"--step {start_step} (PID={self.preview_process.pid})"
            )

        except Exception as e:
            logger.error(f"プレビュー起動エラー: {e}", exc_info=True)
            QMessageBox.critical(self, "エラー", f"プレビュー起動に失敗しました:\n{e}")

    def stop_preview(self):
        """プレビューウィンドウを停止(macOS専用 - プロセスを終了)"""
        logger.info("stop_preview呼び出し")
        try:
            if not self.preview_process:
                QMessageBox.information(self, "情報", "プレビューは起動していません")
                return

            # プロセスが実行中か確認
            if self.preview_process.poll() is not None:
                # 既に終了している
                self.preview_process = None
                self.preview_running = False
                QMessageBox.information(self, "情報", "プレビューは既に終了しています")
                self.status_label.setText("プレビュー終了済み")
                self.status_label.setStyleSheet("color: gray;")
                return

            # プロセスを終了
            pid = self.preview_process.pid
            logger.info(f"プレビュープロセス (PID={pid}) を終了")
            self.preview_process.terminate()

            try:
                self.preview_process.wait(timeout=3)
                logger.info(f"プレビュープロセス (PID={pid}) が正常に終了しました")
            except subprocess.TimeoutExpired:
                logger.warning(f"プレビュープロセス (PID={pid}) が応答しないため強制終了")
                self.preview_process.kill()
                self.preview_process.wait()

            self.preview_process = None
            self.preview_running = False
            self.status_label.setText("プレビュー停止")
            self.status_label.setStyleSheet("color: gray;")
            print(f"⏹ プレビュー停止 (PID={pid})")

            QMessageBox.information(self, "停止完了", f"プレビュー (PID={pid}) を停止しました")

        except Exception as e:
            logger.error(f"プレビュー停止エラー: {e}", exc_info=True)
            QMessageBox.critical(self, "エラー", f"プレビュー停止に失敗しました:\n{e}")

    def reload_preview(self):
        """プレビューをリロード(macOS専用 - プロセスを再起動)"""
        logger.info("reload_preview呼び出し")
        try:
            if not self.current_file_path:
                QMessageBox.warning(self, "警告", "ファイルが選択されていません")
                return

            start_step = self._requested_preview_step()
            if start_step is None:
                return

            # 保存確認
            reply = QMessageBox.question(
                self,
                "リロード",
                f"{self.current_file} を保存してからリロードしますか?",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
            )

            if reply == QMessageBox.Cancel:
                return
            elif reply == QMessageBox.Yes:
                self.save_file()

            # 既存プロセスを終了
            if self.preview_process and self.preview_process.poll() is None:
                old_pid = self.preview_process.pid
                logger.info(f"リロード: 既存プロセス (PID={old_pid}) を終了")
                self.preview_process.terminate()
                try:
                    self.preview_process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    logger.warning("プロセスが応答しないため強制終了")
                    self.preview_process.kill()
                    self.preview_process.wait()

            # 新しいプロセスを起動
            preview_script = os.path.join(
                project_root, "tools", "dialogue_preview_player.py"
            )

            self.preview_process = subprocess.Popen(
                self._preview_player_command(preview_script, start_step)
            )

            self.preview_running = True
            self.status_label.setText(f"プレビューをリロード (PID={self.preview_process.pid})")
            self.status_label.setStyleSheet("color: green;")
            logger.info(f"リロード完了: 新しいプロセス (PID={self.preview_process.pid})")
            print(f"🔄 プレビューをリロード (PID={self.preview_process.pid})")

        except Exception as e:
            logger.error(f"リロードエラー: {e}", exc_info=True)
            QMessageBox.critical(self, "エラー", f"リロードに失敗しました:\n{e}")

    def jump_to_paragraph(self):
        """指定された段落にジャンプ"""
        if not self.preview_running:
            QMessageBox.warning(self, "警告", "プレビューが起動していません")
            return

        try:
            paragraph_num = int(self.paragraph_entry.text())
            if paragraph_num < 1:
                QMessageBox.critical(self, "エラー", "段落番号は1以上の整数を入力してください")
                return

            self.command_queue.put({'type': 'jump', 'paragraph': paragraph_num})
            self.status_label.setText(f"段落 {paragraph_num} にジャンプ中...")
            self.status_label.setStyleSheet("color: orange;")
            print(f"🔍 段落 {paragraph_num} にジャンプ")

        except ValueError:
            QMessageBox.critical(self, "エラー", "段落番号は整数で入力してください")

    def check_status_queue(self):
        """ステータスキューを定期的にチェック"""
        try:
            while True:
                status_type, status_value = self.status_queue.get_nowait()
                self.status_signal.status_received.emit(status_type, status_value)
        except queue.Empty:
            pass

    def handle_status(self, status_type, status_value):
        """ステータスを処理(メインスレッドで実行)"""
        if status_type == "initialized":
            self.status_label.setText("プレビュー初期化完了")
            self.status_label.setStyleSheet("color: green;")
        elif status_type == "loaded":
            self.status_label.setText("KSファイル読み込み完了")
            self.status_label.setStyleSheet("color: green;")
        elif status_type == "paragraph_update":
            self.current_paragraph_label.setText(f"現在: {status_value}")
        elif status_type == "error":
            self.status_label.setText(f"エラー: {status_value}")
            self.status_label.setStyleSheet("color: red;")
        elif status_type == "quit":
            self.preview_running = False
            self.status_label.setText("プレビュー終了")
            self.status_label.setStyleSheet("color: gray;")
        elif status_type == "stopped":
            self.preview_running = False

    def closeEvent(self, event):
        """ウィンドウが閉じられる時の処理(macOS専用 - プロセスをクリーンアップ)"""
        logger.info("アプリケーション終了処理開始")
        self._closing = True

        if self._step_preview_pending:
            self._discard_step_preview_request(self._step_preview_pending)
            self._step_preview_pending = None
        step_process = self._step_preview_process
        if step_process is not None and step_process.state() != QProcess.NotRunning:
            step_process.terminate()
            if not step_process.waitForFinished(1000):
                step_process.kill()
                step_process.waitForFinished(1000)

        # プレビュープロセスが実行中なら終了
        if self.preview_process and self.preview_process.poll() is None:
            logger.info(f"終了処理: プレビュープロセス (PID={self.preview_process.pid}) を終了")
            try:
                self.preview_process.terminate()
                self.preview_process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                logger.warning("プロセスが応答しないため強制終了")
                self.preview_process.kill()
                self.preview_process.wait()
            except Exception as e:
                logger.error(f"プロセス終了エラー: {e}")

        event.accept()
        logger.info("アプリケーション終了")


def main():
    """メイン関数"""
    logger.info("=" * 60)
    logger.info("アプリケーション起動 (PyQt5版)")
    logger.info("=" * 60)

    try:
        app = QApplication(sys.argv)
        apply_windows_2000_style(app)
        editor = EventEditorGUI()
        editor.show()
        sys.exit(app.exec_())
    except Exception as e:
        logger.critical(f"アプリケーション致命的エラー: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
