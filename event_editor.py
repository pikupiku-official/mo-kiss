"""
KSファイル専用エディタ - リアルタイムプレビュー機能付き

画面構成：
- 左側：ファイルリストとテキストエディタ
- 右側：Pygameプレビューウィンドウ（実際のゲーム画面）
- ツールバー：保存、リロード、実行、停止
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import os
import pygame
import threading
import queue
import sys
from pathlib import Path
import platform

# Windows DPI設定の修正（高DPI対応）
if platform.system() == 'Windows':
    try:
        from ctypes import windll
        # DPI awareness を設定（Windows 8.1以降）
        # PROCESS_PER_MONITOR_DPI_AWARE (2) を設定
        windll.shcore.SetProcessDpiAwareness(2)
        print("✓ DPI awareness設定: Per-Monitor DPI Aware")
    except Exception as e:
        try:
            # Windows Vista/7の場合
            windll.user32.SetProcessDPIAware()
            print("✓ DPI awareness設定: System DPI Aware")
        except Exception as e2:
            print(f"⚠ DPI awareness設定失敗: {e}, {e2}")

# プロジェクトルートをパスに追加
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

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
        self.window = None  # 実際のウィンドウ
        self.virtual_screen = None  # 仮想画面（1920x1080）
        self.clock = None
        self.game_state = None
        self.current_file = None

        # ウィンドウサイズ（リサイズ可能）
        self.window_width = 960  # デフォルト: 仮想画面の半分
        self.window_height = 540

    def initialize_pygame(self):
        """Pygameを初期化"""
        try:
            pygame.init()
            pygame.mixer.init()

            # リサイズ可能なプレビューウィンドウを作成
            self.window = pygame.display.set_mode(
                (self.window_width, self.window_height),
                pygame.RESIZABLE
            )
            pygame.display.set_caption("KSファイル プレビュー（リサイズ可能）")

            # 仮想画面を作成（1920x1080の固定サイズ）
            self.virtual_screen = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT))

            self.clock = pygame.time.Clock()
            self.status_queue.put(("initialized", True))
            print(f"✅ Pygameプレビュー初期化完了 (仮想: {VIRTUAL_WIDTH}x{VIRTUAL_HEIGHT}, ウィンドウ: {self.window_width}x{self.window_height})")
            return True
        except Exception as e:
            print(f"❌ Pygameプレビュー初期化エラー: {e}")
            self.status_queue.put(("error", str(e)))
            return False

    def initialize_game_state(self):
        """プレビュー用のゲーム状態を初期化（新しいウィンドウを作らない）"""
        print("[INIT] ゲーム状態を初期化中...")

        # 各マネージャーの初期化
        bgm_manager = BGMManager(DEBUG)
        se_manager = SEManager(DEBUG)
        dialogue_loader = DialogueLoader(DEBUG)
        image_manager = ImageManager(DEBUG)
        text_renderer = TextRenderer(self.virtual_screen, DEBUG)
        choice_renderer = ChoiceRenderer(self.virtual_screen, DEBUG)
        notification_manager = NotificationManager(self.virtual_screen, DEBUG)

        # バックログマネージャーの初期化
        backlog_manager = BacklogManager(self.virtual_screen, text_renderer.fonts, DEBUG)

        # TextRendererにBacklogManagerを設定
        text_renderer.set_backlog_manager(backlog_manager)

        # DialogueLoaderに通知システムを設定
        dialogue_loader.notification_system = notification_manager

        # 画像パスのスキャンと必須画像のみロード
        print("[INIT] 画像をロード中...")
        image_manager.scan_image_paths(VIRTUAL_WIDTH, VIRTUAL_HEIGHT)
        images = image_manager.load_essential_images(VIRTUAL_WIDTH, VIRTUAL_HEIGHT)

        # キャラクター関連の初期化
        character_pos = {}
        character_anim = {}
        character_zoom = {}
        character_expressions = {}
        character_blink_enabled = {}
        character_blink_state = {}
        character_blink_timers = {}

        # 背景の位置とズーム管理
        background_state = {
            'current_bg': None,
            'pos': [0, 0],
            'zoom': 1.0,
            'anim': None
        }

        # フェード関連の初期化
        fade_state = {
            'type': None,
            'start_time': 0,
            'duration': 0,
            'color': (0, 0, 0),
            'alpha': 0,
            'active': False
        }

        # ゲーム状態を辞書として作成（game_manager.pyと同じ構造）
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
            'character_pos': character_pos,
            'character_anim': character_anim,
            'character_zoom': character_zoom,
            'character_expressions': character_expressions,
            'character_blink_enabled': character_blink_enabled,
            'character_blink_state': character_blink_state,
            'character_blink_timers': character_blink_timers,
            'fade_state': fade_state,
            'background_state': background_state,
            'show_face_parts': True,
            'show_text': True,
            'current_paragraph': -1,
            'active_characters': [],
            'last_dialogue_logged': False
        }

        print(f"[INIT] ✓ ゲーム状態初期化完了 (screen={VIRTUAL_WIDTH}x{VIRTUAL_HEIGHT})")
        return game_state

    def load_event(self, ks_file_path):
        """KSファイルを読み込んでゲーム状態を初期化"""
        try:
            print(f"📂 KSファイル読み込み開始: {ks_file_path}")

            # ゲーム状態を初期化（新しいウィンドウを作らない）
            self.game_state = self.initialize_game_state()
            if not self.game_state:
                raise Exception("ゲーム状態の初期化に失敗")

            # 確認
            if self.game_state['screen'] == self.virtual_screen:
                print("[LOAD] ✓ game_state['screen']は仮想画面を指しています")
            else:
                print("[LOAD] ✗ game_state['screen']の設定に失敗！")

            # KSファイルを読み込み
            print("[LOAD] KSファイルをパース中...")
            dialogue_loader = self.game_state['dialogue_loader']
            raw_dialogue_data = dialogue_loader.load_dialogue_from_ks(ks_file_path)

            if not raw_dialogue_data:
                raise Exception("ダイアログデータの読み込みに失敗")
            print(f"[LOAD] パース完了: {len(raw_dialogue_data)}個のエントリ")

            # データを正規化
            print("[LOAD] データを正規化中...")
            dialogue_data = normalize_dialogue_data(raw_dialogue_data)
            if not dialogue_data:
                raise Exception("ダイアログデータの正規化に失敗")
            print(f"[LOAD] 正規化完了: {len(dialogue_data)}個のエントリ")

            # キャラクター画像を事前ロード
            try:
                print("[LOAD] キャラクター画像を事前ロード中...")
                image_manager = self.game_state['image_manager']
                image_manager.preload_characters_from_dialogue(dialogue_data)
                print("[LOAD] ✓ キャラクター画像事前ロード完了")
            except Exception as e:
                print(f"[LOAD] ⚠ キャラクター画像事前ロードエラー（続行）: {e}")

            # ゲーム状態にセット
            self.game_state['dialogue_data'] = dialogue_data
            self.game_state['current_paragraph'] = -1

            # 最初の会話を表示
            print("[LOAD] advance_dialogue()を呼び出し中...")
            from dialogue.model import advance_dialogue
            advance_dialogue(self.game_state)
            print(f"[LOAD] ✓ 現在の段落: {self.game_state.get('current_paragraph', -1)}")

            self.current_file = ks_file_path
            self.status_queue.put(("loaded", True))
            print(f"✅ KSファイル読み込み完了: {ks_file_path}")

        except Exception as e:
            print(f"❌ KSファイル読み込みエラー: {e}")
            import traceback
            traceback.print_exc()
            self.status_queue.put(("error", str(e)))
            self.game_state = None

    def reload_current_event(self):
        """現在のイベントをリロード"""
        if self.current_file:
            print(f"🔄 リロード: {self.current_file}")
            self.load_event(self.current_file)

    def get_scale_and_offset(self):
        """スケーリング係数とオフセットを計算（アスペクト比維持）"""
        # ウィンドウのアスペクト比
        window_aspect = self.window_width / self.window_height
        # 仮想画面のアスペクト比
        virtual_aspect = VIRTUAL_WIDTH / VIRTUAL_HEIGHT

        if window_aspect > virtual_aspect:
            # ウィンドウの方が横長 → 高さに合わせる
            scale = self.window_height / VIRTUAL_HEIGHT
            scaled_width = int(VIRTUAL_WIDTH * scale)
            scaled_height = self.window_height
            offset_x = (self.window_width - scaled_width) // 2
            offset_y = 0
        else:
            # ウィンドウの方が縦長 → 幅に合わせる
            scale = self.window_width / VIRTUAL_WIDTH
            scaled_width = self.window_width
            scaled_height = int(VIRTUAL_HEIGHT * scale)
            offset_x = 0
            offset_y = (self.window_height - scaled_height) // 2

        return scale, scaled_width, scaled_height, offset_x, offset_y

    def screen_to_virtual_coords(self, screen_x, screen_y):
        """ウィンドウ座標を仮想画面座標に変換"""
        scale, scaled_width, scaled_height, offset_x, offset_y = self.get_scale_and_offset()

        # オフセットを考慮
        virtual_x = (screen_x - offset_x) / scale
        virtual_y = (screen_y - offset_y) / scale

        # 範囲外チェック
        if virtual_x < 0 or virtual_x >= VIRTUAL_WIDTH or virtual_y < 0 or virtual_y >= VIRTUAL_HEIGHT:
            return None, None

        return int(virtual_x), int(virtual_y)

    def render_preview(self):
        """プレビュー画面を描画"""
        # 仮想画面に描画
        if not self.game_state:
            # ゲーム状態がない場合は黒い画面を表示
            self.virtual_screen.fill((20, 20, 40))  # デバッグ用に濃い青

            # デバッグテキスト表示
            font = pygame.font.Font(None, 48)
            text = font.render("No Game State - Waiting...", True, (255, 255, 255))
            text_rect = text.get_rect(center=(VIRTUAL_WIDTH // 2, VIRTUAL_HEIGHT // 2))
            self.virtual_screen.blit(text, text_rect)
        else:
            # game_state['screen']が仮想画面を指しているか確認
            if self.game_state.get('screen') != self.virtual_screen:
                print(f"[WARNING] game_state['screen']が仮想画面を指していません！")
                self.game_state['screen'] = self.virtual_screen

            # 背景描画
            draw_background(self.game_state)

            # キャラクター描画
            draw_characters(self.game_state)

            # フェードオーバーレイ描画
            draw_fade_overlay(self.game_state)

            # UIエレメント描画
            if 'image_manager' in self.game_state and 'images' in self.game_state:
                image_manager = self.game_state['image_manager']
                images = self.game_state['images']
                show_text = self.game_state.get('show_text', True)
                image_manager.draw_ui_elements(self.virtual_screen, images, show_text)

            # 選択肢が表示中かチェック
            choice_showing = False
            if 'choice_renderer' in self.game_state:
                choice_renderer = self.game_state['choice_renderer']
                choice_showing = choice_renderer.is_choice_showing()

            # テキスト描画
            if not choice_showing and 'text_renderer' in self.game_state:
                text_renderer = self.game_state['text_renderer']
                text_renderer.render_text_window(self.game_state)

            # 選択肢描画
            if choice_showing:
                choice_renderer.render()

            # バックログ描画
            if 'backlog_manager' in self.game_state:
                backlog_manager = self.game_state['backlog_manager']
                backlog_manager.render()

            # 通知システム描画
            if 'notification_manager' in self.game_state:
                notification_manager = self.game_state['notification_manager']
                notification_manager.render()

        # 仮想画面をウィンドウにスケーリングして描画
        scale, scaled_width, scaled_height, offset_x, offset_y = self.get_scale_and_offset()

        # デバッグ出力（最初の数フレームのみ）
        if not hasattr(self, '_debug_count'):
            self._debug_count = 0
        if self._debug_count < 5:
            print(f"[RENDER] ウィンドウ: {self.window_width}x{self.window_height}, スケール: {scale:.2f}, 表示サイズ: {scaled_width}x{scaled_height}, オフセット: ({offset_x}, {offset_y})")
            self._debug_count += 1

        # ウィンドウを黒で塗りつぶし（レターボックス用）
        self.window.fill((0, 0, 0))

        # 仮想画面をスケーリングして表示
        if scaled_width > 0 and scaled_height > 0:
            scaled_surface = pygame.transform.smoothscale(
                self.virtual_screen,
                (scaled_width, scaled_height)
            )
            self.window.blit(scaled_surface, (offset_x, offset_y))
        else:
            print(f"[ERROR] スケーリングサイズが不正: {scaled_width}x{scaled_height}")

    def run(self):
        """プレビューウィンドウのメインループ"""
        if not self.initialize_pygame():
            return

        self.running = True

        while self.running:
            # コマンドキューをチェック
            try:
                command = self.command_queue.get_nowait()
                cmd_type = command.get('type')

                if cmd_type == 'load':
                    ks_file = command.get('file')
                    self.load_event(ks_file)
                elif cmd_type == 'reload':
                    self.reload_current_event()
                elif cmd_type == 'stop':
                    self.running = False

            except queue.Empty:
                pass

            # イベント処理
            # pygame.event.get()を呼ぶ前に、ウィンドウイベントだけを先に処理
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    self.status_queue.put(("quit", True))

                elif event.type == pygame.VIDEORESIZE:
                    # ウィンドウがリサイズされた
                    self.window_width = event.w
                    self.window_height = event.h
                    self.window = pygame.display.set_mode(
                        (self.window_width, self.window_height),
                        pygame.RESIZABLE
                    )
                    print(f"🔄 ウィンドウリサイズ: {self.window_width}x{self.window_height}")

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    # マウス座標を仮想座標に変換
                    virtual_x, virtual_y = self.screen_to_virtual_coords(event.pos[0], event.pos[1])
                    print(f"[MOUSE] ウィンドウ座標: {event.pos} → 仮想座標: ({virtual_x}, {virtual_y})")
                    if virtual_x is not None and virtual_y is not None:
                        # 仮想座標でイベントを作成してキューに追加
                        virtual_event = pygame.event.Event(
                            pygame.MOUSEBUTTONDOWN,
                            {'pos': (virtual_x, virtual_y), 'button': event.button}
                        )
                        pygame.event.post(virtual_event)

                elif event.type == pygame.MOUSEMOTION:
                    # マウス座標を仮想座標に変換
                    virtual_x, virtual_y = self.screen_to_virtual_coords(event.pos[0], event.pos[1])
                    if virtual_x is not None and virtual_y is not None:
                        # 仮想座標でイベントを作成してキューに追加
                        virtual_event = pygame.event.Event(
                            pygame.MOUSEMOTION,
                            {'pos': (virtual_x, virtual_y), 'rel': event.rel, 'buttons': event.buttons}
                        )
                        pygame.event.post(virtual_event)

                elif event.type == pygame.KEYDOWN:
                    # キーボードイベントはそのままキューに戻す
                    pygame.event.post(event)

            # ゲーム状態を更新（controller2.pyを使用）
            if self.game_state:
                # controller2.pyのhandle_eventsを呼ぶ（内部でpygame.event.get()が呼ばれる）
                handle_dialogue_events(self.game_state, self.virtual_screen)
                update_game(self.game_state)

            # 描画
            self.render_preview()
            pygame.display.flip()
            self.clock.tick(30)

        # 終了処理
        pygame.quit()
        self.status_queue.put(("stopped", True))


class EventEditorGUI:
    """KSファイルエディタのGUI"""

    def __init__(self, root):
        self.root = root
        self.root.title("KSファイル イベントエディタ")
        self.root.geometry("1600x900")

        # 現在編集中のファイル
        self.current_file = None
        self.current_file_path = None

        # プレビューウィンドウ用のキュー
        self.command_queue = queue.Queue()
        self.status_queue = queue.Queue()

        # プレビュースレッド
        self.preview_thread = None
        self.preview_running = False

        # eventsフォルダのパス
        self.events_dir = os.path.join(project_root, "events")

        # GUIを構築
        self.build_gui()

        # ファイルリストを読み込み
        self.load_file_list()

        # 定期的にステータスキューをチェック
        self.check_status_queue()

    def build_gui(self):
        """GUIを構築"""
        # メニューバー
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="ファイル", menu=file_menu)
        file_menu.add_command(label="保存", command=self.save_file, accelerator="Ctrl+S")
        file_menu.add_command(label="リロード", command=self.reload_preview, accelerator="F5")
        file_menu.add_separator()
        file_menu.add_command(label="終了", command=self.on_closing)

        preview_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="プレビュー", menu=preview_menu)
        preview_menu.add_command(label="プレビュー開始", command=self.start_preview)
        preview_menu.add_command(label="プレビュー停止", command=self.stop_preview)

        # キーバインド
        self.root.bind("<Control-s>", lambda e: self.save_file())
        self.root.bind("<F5>", lambda e: self.reload_preview())

        # ツールバー
        toolbar = ttk.Frame(self.root)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        ttk.Button(toolbar, text="💾 保存", command=self.save_file).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="🔄 リロード", command=self.reload_preview).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="▶ プレビュー開始", command=self.start_preview).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="⏹ プレビュー停止", command=self.stop_preview).pack(side=tk.LEFT, padx=2)

        self.status_label = ttk.Label(toolbar, text="準備完了", foreground="green")
        self.status_label.pack(side=tk.RIGHT, padx=10)

        # メインコンテナ（左右分割）
        main_container = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 左側パネル（ファイルリストとエディタ）
        left_panel = ttk.Frame(main_container)
        main_container.add(left_panel, weight=1)

        # 左側パネル内でも上下分割（リサイズ可能）
        left_paned = ttk.PanedWindow(left_panel, orient=tk.VERTICAL)
        left_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # ファイルリスト
        file_list_frame = ttk.LabelFrame(left_paned, text="KSファイル一覧")
        left_paned.add(file_list_frame, weight=1)

        # スクロールバー付きリストボックス
        scrollbar = ttk.Scrollbar(file_list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.file_listbox = tk.Listbox(file_list_frame, yscrollcommand=scrollbar.set)
        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.file_listbox.yview)

        self.file_listbox.bind('<<ListboxSelect>>', self.on_file_select)

        # テキストエディタ
        editor_frame = ttk.LabelFrame(left_paned, text="KSファイル編集")
        left_paned.add(editor_frame, weight=4)  # エディタに4倍の重みをつける

        self.text_editor = scrolledtext.ScrolledText(
            editor_frame,
            wrap=tk.NONE,
            font=("Consolas", 11),
            undo=True,
            maxundo=-1
        )
        self.text_editor.pack(fill=tk.BOTH, expand=True)

        # 行番号を表示するための設定
        self.text_editor.config(tabs=('2c',))

        # 右側パネル（プレビュー情報）
        right_panel = ttk.Frame(main_container)
        main_container.add(right_panel, weight=1)

        # プレビュー情報
        preview_info_frame = ttk.LabelFrame(right_panel, text="プレビュー情報")
        preview_info_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        info_text = """
        【プレビュー使用方法】

        1. 左側のファイルリストからKSファイルを選択
        2. 「▶ プレビュー開始」をクリック
        3. 別ウィンドウでPygameプレビューが起動
        4. エディタで編集後、「💾 保存」→「🔄 リロード」
        5. プレビューウィンドウで変更が反映される

        【キーボードショートカット】
        - Ctrl+S: ファイル保存
        - F5: プレビューをリロード

        【プレビューウィンドウの操作】
        - クリック: 次へ進む
        - スペース: 次へ進む
        - Esc: プレビューを閉じる
        - ウィンドウ端をドラッグ: サイズ変更（リサイズ可能）

        【パネルのリサイズ】
        - ファイルリストとエディタの境界をドラッグして高さ調整
        - 左右のパネルの境界をドラッグして幅調整
        - 編集領域を広くしたい場合は、リストを小さくできます

        【仮想画面システム】
        - 1920x1080の仮想画面で常にレンダリング
        - ウィンドウサイズに自動スケーリング
        - アスペクト比維持（UI要素の位置がズレない）
        - 小さくしても大きくしても正しく表示されます

        ※ プレビューウィンドウは別スレッドで動作します。
        ※ 実際のゲームと同じように音声・エフェクトが再生されます。
        """

        info_label = tk.Text(
            preview_info_frame,
            wrap=tk.WORD,
            font=("メイリオ", 10),
            background="#f0f0f0",
            relief=tk.FLAT,
            state=tk.NORMAL
        )
        info_label.insert("1.0", info_text)
        info_label.config(state=tk.DISABLED)
        info_label.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def load_file_list(self):
        """eventsフォルダからKSファイル一覧を読み込み"""
        self.file_listbox.delete(0, tk.END)

        if not os.path.exists(self.events_dir):
            messagebox.showerror("エラー", f"eventsフォルダが見つかりません: {self.events_dir}")
            return

        # KSファイルを検索
        ks_files = sorted([f for f in os.listdir(self.events_dir) if f.endswith('.ks')])

        for ks_file in ks_files:
            self.file_listbox.insert(tk.END, ks_file)

        print(f"📁 {len(ks_files)}個のKSファイルを読み込みました")

    def on_file_select(self, event):
        """ファイルが選択された時の処理"""
        selection = self.file_listbox.curselection()
        if not selection:
            return

        filename = self.file_listbox.get(selection[0])
        filepath = os.path.join(self.events_dir, filename)

        self.load_file(filepath)

    def load_file(self, filepath):
        """ファイルを読み込んでエディタに表示"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            self.text_editor.delete('1.0', tk.END)
            self.text_editor.insert('1.0', content)

            self.current_file = os.path.basename(filepath)
            self.current_file_path = filepath

            self.status_label.config(text=f"読み込み完了: {self.current_file}", foreground="green")
            print(f"📖 ファイル読み込み: {filepath}")

        except Exception as e:
            messagebox.showerror("エラー", f"ファイル読み込みエラー:\n{e}")
            print(f"❌ ファイル読み込みエラー: {e}")

    def save_file(self):
        """現在のファイルを保存"""
        if not self.current_file_path:
            messagebox.showwarning("警告", "保存するファイルが選択されていません")
            return

        try:
            content = self.text_editor.get('1.0', tk.END)

            with open(self.current_file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            self.status_label.config(text=f"保存完了: {self.current_file}", foreground="green")
            print(f"💾 ファイル保存: {self.current_file_path}")

            messagebox.showinfo("成功", f"{self.current_file} を保存しました")

        except Exception as e:
            messagebox.showerror("エラー", f"ファイル保存エラー:\n{e}")
            print(f"❌ ファイル保存エラー: {e}")

    def start_preview(self):
        """プレビューウィンドウを起動"""
        if self.preview_running:
            messagebox.showinfo("情報", "プレビューは既に起動しています")
            return

        if not self.current_file_path:
            messagebox.showwarning("警告", "プレビューするファイルが選択されていません")
            return

        # プレビュースレッドを起動
        preview_window = PreviewWindow(self.command_queue, self.status_queue)
        self.preview_thread = threading.Thread(target=preview_window.run, daemon=True)
        self.preview_thread.start()
        self.preview_running = True

        # 少し待ってからファイルをロード
        self.root.after(1000, lambda: self.command_queue.put({
            'type': 'load',
            'file': self.current_file_path
        }))

        self.status_label.config(text="プレビュー起動中...", foreground="orange")
        print(f"▶ プレビュー起動: {self.current_file_path}")

    def stop_preview(self):
        """プレビューウィンドウを停止"""
        if not self.preview_running:
            messagebox.showinfo("情報", "プレビューは起動していません")
            return

        self.command_queue.put({'type': 'stop'})
        self.preview_running = False
        self.status_label.config(text="プレビュー停止", foreground="gray")
        print("⏹ プレビュー停止")

    def reload_preview(self):
        """プレビューをリロード"""
        if not self.preview_running:
            messagebox.showwarning("警告", "プレビューが起動していません")
            return

        self.command_queue.put({'type': 'reload'})
        self.status_label.config(text="リロード中...", foreground="orange")
        print("🔄 プレビューをリロード")

    def check_status_queue(self):
        """ステータスキューを定期的にチェック"""
        try:
            while True:
                status_type, status_value = self.status_queue.get_nowait()

                if status_type == "initialized":
                    self.status_label.config(text="プレビュー初期化完了", foreground="green")
                elif status_type == "loaded":
                    self.status_label.config(text="KSファイル読み込み完了", foreground="green")
                elif status_type == "error":
                    self.status_label.config(text=f"エラー: {status_value}", foreground="red")
                elif status_type == "quit":
                    self.preview_running = False
                    self.status_label.config(text="プレビュー終了", foreground="gray")
                elif status_type == "stopped":
                    self.preview_running = False

        except queue.Empty:
            pass

        # 100msごとにチェック
        self.root.after(100, self.check_status_queue)

    def on_closing(self):
        """ウィンドウが閉じられる時の処理"""
        if self.preview_running:
            self.stop_preview()

        self.root.destroy()


def main():
    """メイン関数"""
    root = tk.Tk()
    app = EventEditorGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
