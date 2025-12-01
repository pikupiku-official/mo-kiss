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
import pygame
import threading
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
    QLineEdit, QMessageBox, QToolBar, QAction, QGroupBox
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt5.QtGui import QFont, QTextCursor

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
from dialogue.controller2 import handle_events as handle_dialogue_events, update_game
from dialogue.text_renderer import TextRenderer
from dialogue.character_manager import draw_characters
from dialogue.background_manager import draw_background
from dialogue.choice_renderer import ChoiceRenderer
from dialogue.fade_manager import draw_fade_overlay
from dialogue.backlog_manager import BacklogManager
from dialogue.notification_manager import NotificationManager
from config import VIRTUAL_WIDTH, VIRTUAL_HEIGHT, DEBUG
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
                'character_pos': {},
                'character_anim': {},
                'character_zoom': {},
                'character_expressions': {},
                'character_blink_enabled': {},
                'character_blink_state': {},
                'character_blink_timers': {},
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

        # 段落と行番号のマッピング
        self.paragraph_line_map = []

        # シグナルオブジェクト
        self.status_signal = StatusSignal()
        self.status_signal.status_received.connect(self.handle_status)

        # GUIを構築
        self.build_gui()

        # ファイルリストを読み込み
        self.load_file_list()

        # 定期的にステータスキューをチェック
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.check_status_queue)
        self.status_timer.start(100)  # 100ms

    def build_gui(self):
        """GUIを構築"""
        # メインウィジェット
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)

        # ツールバー
        toolbar = QToolBar()
        self.addToolBar(toolbar)

        save_action = QAction("💾 保存", self)
        save_action.triggered.connect(self.save_file)
        save_action.setShortcut("Ctrl+S")
        toolbar.addAction(save_action)

        reload_action = QAction("🔄 リロード", self)
        reload_action.triggered.connect(self.reload_preview)
        reload_action.setShortcut("F5")
        toolbar.addAction(reload_action)

        start_action = QAction("▶ プレビュー開始", self)
        start_action.triggered.connect(self.start_preview)
        toolbar.addAction(start_action)

        stop_action = QAction("⏹ プレビュー停止", self)
        stop_action.triggered.connect(self.stop_preview)
        toolbar.addAction(stop_action)

        toolbar.addSeparator()

        # 段落ジャンプ
        toolbar.addWidget(QLabel("段落:"))
        self.paragraph_entry = QLineEdit()
        self.paragraph_entry.setMaximumWidth(80)
        self.paragraph_entry.setText("1")
        toolbar.addWidget(self.paragraph_entry)

        jump_action = QAction("🔍 ジャンプ", self)
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

        # メインスプリッター（左右分割）
        main_splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(main_splitter)

        # 左側パネル
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        # ファイルリスト
        file_group = QGroupBox("KSファイル一覧")
        file_layout = QVBoxLayout()
        self.file_listbox = QListWidget()
        self.file_listbox.itemClicked.connect(self.on_file_select)
        file_layout.addWidget(self.file_listbox)
        file_group.setLayout(file_layout)
        left_layout.addWidget(file_group, 1)

        # テキストエディタ
        editor_group = QGroupBox("KSファイル編集")
        editor_layout = QVBoxLayout()
        self.text_editor = QTextEdit()
        self.text_editor.setFont(QFont("Consolas", 11))
        self.text_editor.setAcceptRichText(False)
        editor_layout.addWidget(self.text_editor)
        editor_group.setLayout(editor_layout)
        left_layout.addWidget(editor_group, 4)

        main_splitter.addWidget(left_panel)

        # 右側パネル（プレビュー情報）
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        preview_info_group = QGroupBox("プレビュー情報")
        preview_info_layout = QVBoxLayout()

        info_text = QTextEdit()
        info_text.setReadOnly(True)
        # macOSではヒラギノ角ゴシック、Windowsではメイリオを使用
        import platform
        if platform.system() == 'Darwin':
            info_text.setFont(QFont("Hiragino Sans", 10))
        else:
            info_text.setFont(QFont("メイリオ", 10))
        info_text.setPlainText("""
【プレビュー使用方法】

1. 左側のファイルリストからKSファイルを選択
2. 「▶ プレビュー開始」をクリック
3. 別ウィンドウでPygameプレビューが起動
4. エディタで編集後、「💾 保存」→「🔄 リロード」
5. プレビューウィンドウで変更が反映される

【キーボードショートカット】
- Ctrl+S: ファイル保存
- F5: プレビューをリロード（現在位置を保持）

【段落ジャンプ機能】
段落番号を入力して「🔍 ジャンプ」をクリック
リロード時は現在の段落位置を自動保持
「現在: X」で現在の段落番号を表示

【プレビューウィンドウの操作】
- クリック: 次へ進む
- スペース: 次へ進む
- Esc: プレビューを閉じる
- ウィンドウ端をドラッグ: サイズ変更

※ PyQt5版（macOS対応）
※ プレビューウィンドウは別スレッドで動作します
        """)
        preview_info_layout.addWidget(info_text)
        preview_info_group.setLayout(preview_info_layout)
        right_layout.addWidget(preview_info_group)

        main_splitter.addWidget(right_panel)
        main_splitter.setSizes([1200, 400])

    def load_file_list(self):
        """eventsフォルダからKSファイル一覧を読み込み"""
        self.file_listbox.clear()

        if not os.path.exists(self.events_dir):
            QMessageBox.critical(self, "エラー", f"eventsフォルダが見つかりません: {self.events_dir}")
            return

        ks_files = sorted([f for f in os.listdir(self.events_dir) if f.endswith('.ks')])

        for ks_file in ks_files:
            self.file_listbox.addItem(ks_file)

        print(f"📁 {len(ks_files)}個のKSファイルを読み込みました")

    def on_file_select(self, item):
        """ファイルが選択された時の処理"""
        filename = item.text()
        filepath = os.path.join(self.events_dir, filename)
        self.load_file(filepath)

    def load_file(self, filepath):
        """ファイルを読み込んでエディタに表示"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            self.text_editor.setPlainText(content)
            self.current_file = os.path.basename(filepath)
            self.current_file_path = filepath

            self.build_paragraph_line_map()

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

            self.status_label.setText(f"保存完了: {self.current_file}")
            self.status_label.setStyleSheet("color: green;")
            print(f"💾 ファイル保存: {self.current_file_path}")

            QMessageBox.information(self, "成功", f"{self.current_file} を保存しました")

        except Exception as e:
            QMessageBox.critical(self, "エラー", f"ファイル保存エラー:\n{e}")
            print(f"❌ ファイル保存エラー: {e}")

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
