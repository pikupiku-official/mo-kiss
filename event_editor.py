"""
KSファイル専用エディタ - PyQt5版（macOS対応）

画面構成：
- 左側：ファイルリストとテキストエディタ
- 右側：使用方法とヘルプ情報
- ツールバー：保存、編集支援機能

注意: macOSでは技術的制限によりPygameプレビュー機能は利用できません。
      編集後は main.py でゲーム本体を起動してプレビュー確認してください。
"""

import os
import sys
import csv
import re
import pygame
import threading
import tempfile
import queue
import platform
import traceback
import logging
import subprocess
from datetime import datetime
from pathlib import Path

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QListWidget, QPushButton, QLabel, QSplitter,
    QLineEdit, QMessageBox, QToolBar, QAction, QGroupBox,
    QFormLayout, QDialog, QDialogButtonBox, QMenu, QCheckBox,
    QAbstractItemView, QComboBox, QTableWidget, QTableWidgetItem,
    QFileDialog
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt5.QtGui import QFont, QTextCursor, QTextCharFormat, QColor, QPixmap

# プロジェクトルートをパスに追加
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# ログファイルの設定
log_file = os.path.join(project_root, "event_editor_mac.log")
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
from config import VIRTUAL_WIDTH, VIRTUAL_HEIGHT, DEBUG, USE_IR, IR_DUMP_JSON, IR_DUMP_DIR
from bgm_manager import BGMManager
from se_manager import SEManager
from image_manager import ImageManager


class PreviewWindow:
    """Pygameプレビューウィンドウ（別スレッドで実行）"""

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
            pygame.display.set_caption("KSファイル プレビュー（リサイズ可能）")

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

        import config
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

                if not choice_showing and 'text_renderer' in self.game_state:
                    text_renderer = self.game_state['text_renderer']
                    text_renderer.render_text_window(self.game_state)

                if choice_showing:
                    choice_renderer.render()

                if 'backlog_manager' in self.game_state:
                    backlog_manager = self.game_state['backlog_manager']
                    backlog_manager.render()

                if 'notification_manager' in self.game_state:
                    notification_manager = self.game_state['notification_manager']
                    notification_manager.render()

                draw_input_blocked_notice(self.game_state, self.virtual_screen)

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


class StepEditorDialog(QDialog):
    """step編集用ダイアログ"""

    TAG_NAMES = [
        "bg",
        "bg_show",
        "bg_move",
        "chara_show",
        "chara_shift",
        "chara_move",
        "chara_hide",
        "bgm",
        "bgmstop",
        "bgmstart",
        "se",
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
            ("torso", ""),
            ("eye", ""),
            ("mouth", ""),
            ("brow", ""),
            ("cheek", ""),
            ("blink", "true"),
            ("x", "0.5"),
            ("y", "0.5"),
            ("size", "1.0"),
            ("fade", "0.3"),
        ],
        "chara_shift": [
            ("name", ""),
            ("torso", ""),
            ("eye", ""),
            ("mouth", ""),
            ("brow", ""),
            ("cheek", ""),
            ("x", ""),
            ("y", ""),
            ("size", ""),
            ("fade", "0.3"),
        ],
        "chara_move": [("name", ""), ("left", "0.0"), ("top", "0.0"), ("zoom", "1.0"), ("time", "600")],
        "chara_hide": [("name", ""), ("fade", "0.3")],
        "bgm": [("bgm", ""), ("volume", "0.5"), ("loop", "true")],
        "bgmstop": [("time", "1.0")],
        "bgmstart": [("time", "1.0")],
        "se": [("se", ""), ("volume", "0.5"), ("frequency", "1")],
        "fadeout": [("color", "black"), ("time", "1.0")],
        "fadein": [("time", "1.0")],
        "choice": [("option1", ""), ("option2", "")],
        "flag_set": [("name", ""), ("value", "")],
        "if": [("condition", "")],
        "event_control": [("unlock", ""), ("lock", "")],
    }
    CUSTOM_EDITORS = {
        "bg": [("storage", "storage", "text")],
        "bg_show": [
            ("storage", "storage", "text"),
            ("bg_x", "bg_x", "text"),
            ("bg_y", "bg_y", "text"),
            ("bg_zoom", "bg_zoom", "text"),
        ],
        "bg_move": [
            ("storage", "storage", "text"),
            ("bg_left", "bg_left", "text"),
            ("bg_top", "bg_top", "text"),
            ("bg_zoom", "bg_zoom", "text"),
            ("time", "time", "text"),
        ],
        "chara_show": [
            ("name", "name", "text"),
            ("torso", "torso", "text"),
            ("eye", "eye", "text"),
            ("mouth", "mouth", "text"),
            ("brow", "brow", "text"),
            ("cheek", "cheek", "text"),
            ("blink", "blink", "bool"),
            ("x", "x", "text"),
            ("y", "y", "text"),
            ("size", "size", "text"),
            ("fade", "fade", "text"),
        ],
        "chara_shift": [
            ("name", "name", "text"),
            ("torso", "torso", "text"),
            ("eye", "eye", "text"),
            ("mouth", "mouth", "text"),
            ("brow", "brow", "text"),
            ("cheek", "cheek", "text"),
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
    }
    BROWSE_KEYS = {
        "storage": "backgrounds",
        "torso": "characters",
        "eye": "eyes",
        "mouth": "mouths",
        "brow": "brows",
        "cheek": "cheeks",
    }

    def __init__(self, parent, step, actions=None):
        super().__init__(parent)
        self.step = step or {}
        self.actions = actions or []

        self.setWindowTitle("step編集")
        self.resize(1100, 700)

        main_layout = QVBoxLayout(self)
        main_splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(main_splitter)

        # 左カラム: プレビュー + セリフ
        left_panel = QWidget()
        left_panel_layout = QVBoxLayout(left_panel)
        left_panel_layout.setContentsMargins(0, 0, 0, 0)
        left_splitter = QSplitter(Qt.Vertical)
        left_panel_layout.addWidget(left_splitter)
        main_splitter.addWidget(left_panel)

        preview_group = QGroupBox("プレビュー (4:3)")
        preview_layout = QVBoxLayout()
        self.preview_label = QLabel("プレビュー未実装")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setFixedSize(400, 300)
        self.preview_label.setStyleSheet("border: 1px solid #888; background: #111; color: #ddd;")
        preview_layout.addWidget(self.preview_label, alignment=Qt.AlignCenter)
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

        dialogue_group.setLayout(dialogue_layout)
        left_splitter.addWidget(dialogue_group)

        # 右カラム: アクション編集
        right_panel = QWidget()
        right_panel_layout = QVBoxLayout(right_panel)
        right_panel_layout.setContentsMargins(0, 0, 0, 0)
        right_splitter = QSplitter(Qt.Vertical)
        right_panel_layout.addWidget(right_splitter)
        main_splitter.addWidget(right_panel)

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

        main_splitter.setSizes([500, 500])
        left_splitter.setSizes([300, 100])
        right_splitter.setSizes([200, 600])

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText("保存/適用")
        buttons.button(QDialogButtonBox.Cancel).setText("キャンセル")
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

        if self.actions_list.count() > 0:
            self.actions_list.setCurrentRow(0)
        else:
            self._apply_param_template(self.tag_combo.currentText())

    def get_dialogue_values(self):
        """セリフ編集の値を取得"""
        speaker = self.speaker_input.text().strip()
        body = self.body_input.text().replace("\n", " ").replace("\r", " ").strip()
        scroll_stop = self.scroll_checkbox.isChecked()
        return speaker, body, scroll_stop

    def get_actions(self):
        """アクション一覧を取得"""
        actions = []
        for i in range(self.actions_list.count()):
            text = self.actions_list.item(i).text().strip()
            if text:
                actions.append(text)
        return actions

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

    def _request_preview_update(self):
        parent = self.parent()
        if not parent:
            return
        if hasattr(parent, "_preview_step_from_dialog"):
            parent._preview_step_from_dialog(self.step, self)

    def _parse_action(self, text):
        text = text.strip()
        if text.startswith("[") and text.endswith("]"):
            text = text[1:-1].strip()
        if not text:
            return "", []
        parts = text.split(None, 1)
        tag = parts[0]
        params_text = parts[1] if len(parts) > 1 else ""
        params = []
        for match in re.finditer(r'(\w+)\s*=\s*"([^"]*)"', params_text):
            params.append((match.group(1), match.group(2)))
        return tag, params

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
        self.preview_label.setPixmap(
            pixmap.scaled(
                self.preview_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
        )

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
        self.custom_editor_widget.adjustSize()
        self.custom_editor_widget.updateGeometry()

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
            else:
                field = QLineEdit()
            self.custom_fields[key] = field
            if field_type != "bool" and key in self.BROWSE_KEYS:
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
                field.setCurrentText(value if value else "true")
            else:
                field.setText(value)

    def _collect_custom_params(self):
        params = []
        for key, field in self.custom_fields.items():
            if isinstance(field, QComboBox):
                value = field.currentText().strip()
            else:
                value = field.text().strip()
            if value != "":
                params.append((key, value))
        return params

    def _browse_for_asset(self, key):
        subdir = self.BROWSE_KEYS.get(key)
        if not subdir:
            return

        base_dir = os.path.join(project_root, "images")
        start_dir = base_dir

        if key == "storage":
            candidate = os.path.join(base_dir, subdir)
            if os.path.isdir(candidate):
                start_dir = candidate
        else:
            name_field = self.custom_fields.get("name")
            name_value = name_field.text().strip() if name_field else ""
            if name_value:
                candidate = os.path.join(base_dir, name_value, subdir)
                if os.path.isdir(candidate):
                    start_dir = candidate
            if start_dir == base_dir:
                candidate = os.path.join(base_dir, subdir)
                if os.path.isdir(candidate):
                    start_dir = candidate
                else:
                    for root, dirs, _files in os.walk(base_dir):
                        if os.path.basename(root) == subdir:
                            start_dir = root
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

class EventEditorGUI(QMainWindow):
    """PyQt5ベースのKSファイルエディタ"""

    def __init__(self):
        super().__init__()

        self.setWindowTitle("KSファイル イベントエディタ (PyQt5版)")
        self.setGeometry(100, 100, 1600, 900)

        # 現在編集中のファイル
        self.current_file = None
        self.current_file_path = None

        # プレビューウィンドウ用のキュー（未使用だがPreviewWindowクラスとの互換性のため残す）
        self.command_queue = queue.Queue()
        self.status_queue = queue.Queue()

        # プレビュースレッド（未使用だがPreviewWindowクラスとの互換性のため残す）
        self.preview_thread = None
        self.preview_running = False

        # プレビュープロセス管理（別プロセス方式用 - macOS専用）
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

        # events.csvを読み込み
        self.load_events_metadata()

        # GUIを構築
        self.build_gui()

        # stepハイライト更新用タイマー
        self.step_highlight_timer = QTimer()
        self.step_highlight_timer.setSingleShot(True)
        self.step_highlight_timer.timeout.connect(self.update_step_highlights)

        # ファイルリストを読み込み
        self.load_file_list()

        # 定期的にステータスキューをチェック
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.check_status_queue)
        self.status_timer.start(100)  # 100ms

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

        toolbar.addWidget(QLabel("段落:"))
        self.paragraph_entry = QLineEdit()
        self.paragraph_entry.setMaximumWidth(80)
        self.paragraph_entry.setText("1")
        toolbar.addWidget(self.paragraph_entry)

        jump_action = QAction("ジャンプ", self)
        jump_action.triggered.connect(self.jump_to_paragraph)
        toolbar.addAction(jump_action)

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
                metadata_layout.addRow(header, field)
                self.event_fields[header] = field
        else:
            metadata_layout.addRow(QLabel("events.csvが見つかりません"))
        metadata_group.setLayout(metadata_layout)
        right_splitter.addWidget(metadata_group)

        editor_group = QGroupBox("KSファイル編集")
        editor_layout = QVBoxLayout()
        self.text_editor = QTextEdit()
        self.text_editor.setFont(QFont("Consolas", 11))
        self.text_editor.setAcceptRichText(False)
        self.text_editor.textChanged.connect(self.schedule_step_highlights)
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
            f"{ks_filename} を削除しますか？\nKSファイルとevents.csvの行を削除します。",
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
                field.setText(row.get(header, ""))

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

    def on_file_select(self, item):
        """ファイルが選択された時の処理"""
        filename = item.text()
        filepath = os.path.join(self.events_dir, filename)
        self.load_file(filepath)
        event_id = os.path.splitext(filename)[0]
        self.load_event_metadata(event_id)

    def load_file(self, filepath):
        """ファイルを読み込んでエディタに表示"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            self.text_editor.setPlainText(content)
            self.current_file = os.path.basename(filepath)
            self.current_file_path = filepath

            self.build_paragraph_line_map()
            self.update_step_highlights()

            self.status_label.setText(f"読み込み完了: {self.current_file}")
            self.status_label.setStyleSheet("color: green;")
            print(f"📖 ファイル読み込み: {filepath}")

        except Exception as e:
            QMessageBox.critical(self, "エラー", f"ファイル読み込みエラー:\n{e}")
            print(f"❌ ファイル読み込みエラー: {e}")

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
        self.current_steps = steps

        selections = []
        colors = [QColor(255, 248, 220), QColor(235, 245, 255)]

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

        def add_step(start_line, end_line, speaker="", body="", has_scroll_stop=False, dialogue_line=None):
            step_index = len(steps)
            steps.append(
                {
                    "step_index": step_index,
                    "start_line": start_line,
                    "end_line": end_line,
                    "speaker": speaker,
                    "body": body,
                    "has_scroll_stop": has_scroll_stop,
                    "dialogue_line": dialogue_line,
                }
            )

        def flush_actions(end_line):
            nonlocal pending_action_lines
            if pending_action_lines:
                add_step(min(pending_action_lines), end_line)
                pending_action_lines = []

        for i, raw_line in enumerate(lines):
            line = raw_line.strip()
            if not line:
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
        actions = self._extract_actions_from_step(step)
        dialog = StepEditorDialog(self, step, actions=actions)
        step_index = step.get("step_index")
        if step_index is not None:
            self._generate_step_preview(step_index, dialog)
        if dialog.exec_() == QDialog.Accepted:
            speaker, body, scroll_stop = dialog.get_dialogue_values()
            actions = dialog.get_actions()
            self._apply_step_update(step, speaker, body, scroll_stop, actions)
            if step_index is not None:
                self._generate_step_preview(step_index, dialog)

    def _insert_step_template(self, step, insert_before=True):
        """指定stepの前後にテンプレートstepを挿入する"""
        if not step:
            return

        lines = self.text_editor.toPlainText().splitlines()
        start_line = step.get("start_line", 0)
        end_line = step.get("end_line", start_line)
        insert_at = start_line if insert_before else end_line + 1

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

        new_lines = lines[:insert_at] + template_lines + lines[insert_at:]
        self.text_editor.blockSignals(True)
        self.text_editor.setPlainText("\n".join(new_lines))
        self.text_editor.blockSignals(False)
        self.update_step_highlights()

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
        self.update_step_highlights()

    def _build_step_update_text(self, original_text, step, speaker, body, scroll_stop, actions, warn_scroll_stop=True):
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
        for line in region:
            stripped = line.strip()
            if not stripped:
                other_lines.append(line)
                continue
            if is_action_line(stripped):
                continue
            if is_speaker_line(stripped):
                continue
            if is_dialogue_line(stripped):
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

        if speaker:
            new_region.append(f"//{speaker}//")

        if body:
            line_text = f"「{body}」"
            if scroll_stop:
                line_text += "[scroll-stop]"
            new_region.append(line_text)
        elif scroll_stop and warn_scroll_stop:
            QMessageBox.warning(self, "Warning", "Cannot set scroll-stop without dialogue text.")

        new_lines = lines[:start_line] + new_region + lines[end_line + 1 :]
        return "\n".join(new_lines)

    def _apply_step_update(self, step, speaker, body, scroll_stop, actions):
        """step?????????????????"""
        new_text = self._build_step_update_text(
            self.text_editor.toPlainText(),
            step,
            speaker,
            body,
            scroll_stop,
            actions,
            warn_scroll_stop=True,
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
        self.update_step_highlights()

    def _run_step_preview(self, source_path, step_index, dialog, temp_path=None):
        preview_script = os.path.join(project_root, "preview_dialogue.py")
        if not os.path.exists(preview_script):
            return

        out_dir = os.path.join(project_root, "debug", "step_previews")
        os.makedirs(out_dir, exist_ok=True)
        basename = os.path.splitext(os.path.basename(self.current_file_path or source_path))[0]
        out_path = os.path.join(out_dir, f"{basename}_step_{step_index + 1:04d}.png")

        cmd = [
            sys.executable,
            preview_script,
            source_path,
            "--step",
            str(step_index + 1),
            "--out",
            out_path,
        ]

        dialog.preview_label.setText("Generating preview...")

        def worker():
            success = True
            message = ""
            try:
                subprocess.run(cmd, check=True, timeout=30)
            except Exception as e:
                success = False
                message = f"Preview failed: {e}"
            if temp_path:
                try:
                    os.remove(temp_path)
                except OSError:
                    pass
            self.preview_signal.preview_ready.emit(dialog, out_path, success, message)

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()

    def _on_preview_ready(self, dialog, image_path, success, message):
        if not dialog or not hasattr(dialog, "preview_label"):
            return
        if not dialog.isVisible():
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
        speaker, body, scroll_stop = dialog.get_dialogue_values()
        actions = dialog.get_actions()
        temp_text = self._build_step_update_text(
            self.text_editor.toPlainText(),
            step,
            speaker,
            body,
            scroll_stop,
            actions,
            warn_scroll_stop=False,
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

    def _extract_actions_from_step(self, step):
        """step????KS???????"""
        if not step:
            return []

        lines = self.text_editor.toPlainText().splitlines()
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

    def save_file(self):
        """現在のファイルを保存"""
        if not self.current_file_path:
            QMessageBox.warning(self, "警告", "保存するファイルが選択されていません")
            return

        try:
            content = self.text_editor.toPlainText()

            with open(self.current_file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            self.build_paragraph_line_map()
            if self.event_fields:
                self.save_event_metadata()

            self.status_label.setText(f"保存完了: {self.current_file}")
            self.status_label.setStyleSheet("color: green;")
            print(f"ファイル保存: {self.current_file_path}")

            QMessageBox.information(self, "成功", f"{self.current_file} を保存しました")

        except Exception as e:
            QMessageBox.critical(self, "エラー", f"ファイル保存エラー:\n{e}")
            print(f"ファイル保存エラー: {e}")

    def start_preview(self):
        """ダイアログプレビューを別プロセスとして起動（macOS専用）"""
        logger.info("start_preview呼び出し（preview_dialogue.py起動）")
        try:
            if not self.current_file_path:
                QMessageBox.warning(self, "警告", "ファイルが選択されていません")
                return

            # 既存のプレビュープロセスがあれば先に終了
            if self.preview_process and self.preview_process.poll() is None:
                reply = QMessageBox.question(
                    self,
                    "プレビュー起動",
                    "既にプレビューが起動中です。\n再起動しますか？",
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
                f"{self.current_file} を保存してからプレビューしますか？\n\n"
                "※ macOSではエディタ内プレビューは利用できないため、\n"
                "別ウィンドウでプレビューを起動します。",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
            )

            if reply == QMessageBox.Cancel:
                return
            elif reply == QMessageBox.Yes:
                self.save_file()

            # preview_dialogue.pyを別プロセスとして起動
            import subprocess
            preview_script = os.path.join(project_root, "preview_dialogue.py")

            if not os.path.exists(preview_script):
                QMessageBox.critical(
                    self,
                    "エラー",
                    f"プレビュースクリプトが見つかりません:\n{preview_script}"
                )
                return

            # プレビュープロセスを起動して保存
            if platform.system() == 'Darwin':  # macOS
                self.preview_process = subprocess.Popen(['python3', preview_script, self.current_file_path])
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
                self.preview_process = subprocess.Popen(['python', preview_script, self.current_file_path])
                self.preview_running = True
                self.status_label.setText(f"プレビュー起動中 (PID={self.preview_process.pid})")
                self.status_label.setStyleSheet("color: green;")
                logger.info(f"プレビュープロセス起動: PID={self.preview_process.pid}")

            print(f"▶ プレビュー起動: {preview_script} {self.current_file_path} (PID={self.preview_process.pid})")

        except Exception as e:
            logger.error(f"プレビュー起動エラー: {e}", exc_info=True)
            QMessageBox.critical(self, "エラー", f"プレビュー起動に失敗しました:\n{e}")

    def stop_preview(self):
        """プレビューウィンドウを停止（macOS専用 - プロセスを終了）"""
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
        """プレビューをリロード（macOS専用 - プロセスを再起動）"""
        logger.info("reload_preview呼び出し")
        try:
            if not self.current_file_path:
                QMessageBox.warning(self, "警告", "ファイルが選択されていません")
                return

            # 保存確認
            reply = QMessageBox.question(
                self,
                "リロード",
                f"{self.current_file} を保存してからリロードしますか？",
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
            preview_script = os.path.join(project_root, "preview_dialogue.py")

            if platform.system() == 'Darwin':  # macOS
                self.preview_process = subprocess.Popen(['python3', preview_script, self.current_file_path])
            else:
                self.preview_process = subprocess.Popen(['python', preview_script, self.current_file_path])

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
        """ステータスを処理（メインスレッドで実行）"""
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
        """ウィンドウが閉じられる時の処理（macOS専用 - プロセスをクリーンアップ）"""
        logger.info("アプリケーション終了処理開始")

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
        editor = EventEditorGUI()
        editor.show()
        sys.exit(app.exec_())
    except Exception as e:
        logger.critical(f"アプリケーション致命的エラー: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
