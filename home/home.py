"""
家モジュール - プレイヤーの部屋画面

家では以下の選択肢が提供される：
- 寝る：次の日の朝に時間を進めてmapモジュールへ
- メインメニューへ：main_menuモジュールへ
"""

import pygame
import sys
import os
from time_manager import get_time_manager
from save_manager import get_save_manager
from loading_screen import show_loading, hide_loading

class HomeModule:
    def __init__(self, screen):
        self.screen = screen
        self.font = None
        self.large_font = None
        self._init_fonts()
        
        # 選択肢データ
        self.choices = [
            {"text": "寝る", "action": "sleep"},
            {"text": "セーブ", "action": "save"},
            {"text": "ロード", "action": "load"},
            {"text": "メインメニューへ", "action": "main_menu"}
        ]
        self.selected_choice = 0
        
        # 色設定
        self.bg_color = (20, 30, 50)
        self.text_color = (255, 255, 255)
        self.selected_color = (255, 220, 100)
        self.border_color = (100, 150, 200)
        
        # セーブ管理
        self.save_manager = get_save_manager()
        self.save_mode = None  # 'save' または 'load' または None
        self.save_slots = []
        self.selected_slot = 0
    
    def _init_fonts(self):
        """フォント初期化（日本語対応）"""
        import platform
        
        # 段階的にフォントを試行
        font_initialized = False
        
        # 第1段階: プロジェクト専用フォント
        try:
            # 絶対パスでフォントを指定
            project_root = os.path.dirname(os.path.dirname(__file__))
            font_dir = os.path.join(project_root, "fonts")
            project_font_path = os.path.join(font_dir, "MPLUS1p-Regular.ttf")
            project_font_path = os.path.abspath(project_font_path)
            
            test_font = pygame.font.Font(project_font_path, 16)
            # 日本語テスト
            test_surface = test_font.render('テスト', True, (0, 0, 0))
            
            if test_surface.get_width() > 10:
                self.font = pygame.font.Font(project_font_path, 48)
                self.large_font = pygame.font.Font(project_font_path, 64)
                font_initialized = True
                print("home.py: プロジェクト専用フォント (M PLUS Rounded 1c) を使用")
        except Exception as e:
            print(f"home.py: プロジェクト専用フォント読み込み失敗: {e}")
        
        # 第2段階: プラットフォーム別システムフォント
        if not font_initialized:
            platform_fonts = []
            system = platform.system()
            
            if system == "Darwin":  # macOS
                platform_fonts = [
                    "ヒラギノ角ゴシック",
                    "Hiragino Sans",
                    "Arial Unicode MS"
                ]
            elif system == "Windows":
                platform_fonts = [
                    "MS Gothic",
                    "Meiryo",
                    "Arial"
                ]
            else:  # Linux
                platform_fonts = [
                    "DejaVu Sans",
                    "Liberation Sans"
                ]
            
            for font_name in platform_fonts:
                try:
                    test_font = pygame.font.SysFont(font_name, 16)
                    test_surface = test_font.render('テスト', True, (0, 0, 0))
                    if test_surface.get_width() > 5:
                        self.font = pygame.font.SysFont(font_name, 48)
                        self.large_font = pygame.font.SysFont(font_name, 64)
                        font_initialized = True
                        print(f"home.py: プラットフォーム固有フォント ({font_name}) を使用")
                        break
                except:
                    continue
        
        # 第3段階: 利用可能フォントから日本語対応を検索
        if not font_initialized:
            available_fonts = pygame.font.get_fonts()
            japanese_keywords = ['hiragino', 'gothic', 'meiryo', 'yu', 'noto', 'sans', 'mincho']
            
            for keyword in japanese_keywords:
                matching_fonts = [f for f in available_fonts if keyword in f.lower()]
                for font_name in matching_fonts:
                    try:
                        test_font = pygame.font.SysFont(font_name, 16)
                        test_surface = test_font.render('あ', True, (0, 0, 0))
                        if test_surface.get_width() > 5:
                            self.font = pygame.font.SysFont(font_name, 48)
                            self.large_font = pygame.font.SysFont(font_name, 64)
                            font_initialized = True
                            print(f"home.py: 動的検索フォント ({font_name}) を使用")
                            break
                    except:
                        continue
                if font_initialized:
                    break
        
        # 第4段階: デフォルトフォント（最終フォールバック）
        if not font_initialized:
            print("home.py: 警告: 適切な日本語フォントが見つかりません。デフォルトフォントを使用します。")
            try:
                self.font = pygame.font.Font(None, 48)
                self.large_font = pygame.font.Font(None, 64)
            except:
                # 最終的なフォールバック
                default_font = pygame.font.get_default_font()
                self.font = pygame.font.Font(default_font, 48)
                self.large_font = pygame.font.Font(default_font, 64)
        
    def handle_events(self, events):
        """イベント処理"""
        for event in events:
            if event.type == pygame.KEYDOWN:
                if self.save_mode is None:
                    # メインメニュー状態
                    if event.key == pygame.K_UP:
                        self.selected_choice = (self.selected_choice - 1) % len(self.choices)
                        print(f"[HOME] 選択: {self.choices[self.selected_choice]['text']}")
                        
                    elif event.key == pygame.K_DOWN:
                        self.selected_choice = (self.selected_choice + 1) % len(self.choices)
                        print(f"[HOME] 選択: {self.choices[self.selected_choice]['text']}")
                        
                    elif event.key == pygame.K_RETURN:
                        selected_action = self.choices[self.selected_choice]["action"]
                        print(f"[HOME] 実行: {selected_action}")
                        
                        if selected_action == "sleep":
                            # 時間管理：次の日の朝に設定
                            time_manager = get_time_manager()
                            time_manager.set_to_morning()
                            print("[HOME] 睡眠完了 - mapモジュールへ遷移")
                            return "go_to_map"
                            
                        elif selected_action == "save":
                            self.save_mode = "save"
                            self._load_save_slots()
                            self.selected_slot = 0
                            print("[HOME] セーブモードに切り替え")
                            
                        elif selected_action == "load":
                            self.save_mode = "load"
                            self._load_save_slots()
                            self.selected_slot = 0
                            print("[HOME] ロードモードに切り替え")
                            
                        elif selected_action == "main_menu":
                            print("[HOME] メインメニューへ遷移")
                            return "go_to_main_menu"
                
                else:
                    # セーブ/ロードスロット選択状態
                    if event.key == pygame.K_UP:
                        self.selected_slot = (self.selected_slot - 1) % len(self.save_slots)
                        
                    elif event.key == pygame.K_DOWN:
                        self.selected_slot = (self.selected_slot + 1) % len(self.save_slots)
                        
                    elif event.key == pygame.K_RETURN:
                        return self._handle_slot_selection()
                        
                    elif event.key == pygame.K_ESCAPE:
                        # セーブ/ロードモードから戻る
                        self.save_mode = None
                        print("[HOME] メインメニューに戻る")
                        
        return None
    
    def update(self):
        """更新処理"""
        pass
    
    def _load_save_slots(self):
        """セーブスロット情報を読み込む"""
        self.save_slots = []
        for i in range(1, 11):  # saveslot_01 から saveslot_10 まで
            slot_name = f"saveslot_{i:02d}"
            if self.save_manager.has_save(slot_name):
                metadata = self.save_manager.get_save_metadata(slot_name)
                self.save_slots.append({
                    'slot': i,
                    'name': slot_name,
                    'exists': True,
                    'date': metadata.get('save_date', '不明'),
                    'player_name': metadata.get('player_name', '名前なし')
                })
            else:
                self.save_slots.append({
                    'slot': i,
                    'name': slot_name,
                    'exists': False,
                    'date': '',
                    'player_name': ''
                })
    
    def _handle_slot_selection(self):
        """スロット選択時の処理"""
        if not self.save_slots:
            return None
            
        slot_info = self.save_slots[self.selected_slot]
        slot_name = slot_info['name']
        slot_num = slot_info['slot']
        
        if self.save_mode == "save":
            try:
                show_loading("データを保存中...", self.screen)
                self.save_manager.save_game(slot_name)
                print(f"[HOME] スロット {slot_num} にセーブしました")
                # スロット情報を再読み込み
                self._load_save_slots()
                hide_loading()
                # メインメニューに戻る
                self.save_mode = None
            except Exception as e:
                print(f"[HOME] セーブに失敗しました: {e}")
                hide_loading()
        
        elif self.save_mode == "load":
            if slot_info['exists']:
                try:
                    show_loading("データを読み込み中...", self.screen)
                    self.save_manager.load_game(slot_name)
                    print(f"[HOME] スロット {slot_num} からロードしました")
                    hide_loading()
                    # ゲームを再開（mapに戻る）
                    self.save_mode = None
                    return "go_to_map"
                except Exception as e:
                    print(f"[HOME] ロードに失敗しました: {e}")
                    hide_loading()
            else:
                print(f"[HOME] スロット {slot_num} にセーブデータがありません")
        
        return None
    
    def render(self):
        """描画処理"""
        # 全画面を黒で塗りつぶし（ピラーボックス用）
        self.screen.fill((0, 0, 0))

        # 4:3コンテンツ領域に背景色を塗る
        from config import CONTENT_WIDTH, CONTENT_HEIGHT, OFFSET_X, OFFSET_Y
        content_rect = pygame.Rect(OFFSET_X, OFFSET_Y, CONTENT_WIDTH, CONTENT_HEIGHT)
        self.screen.fill(self.bg_color, content_rect)

        # ★ピラーボックスを「奈落」にする：4:3コンテンツ領域にクリッピング設定★
        self.screen.set_clip(content_rect)

        if self.save_mode is None:
            # メインメニュー描画
            self._render_main_menu()
        else:
            # セーブ/ロード画面描画
            self._render_save_load_screen()

        # ★クリッピング解除★
        self.screen.set_clip(None)
    
    def _render_main_menu(self):
        """メインメニュー描画"""
        # タイトル
        time_manager = get_time_manager()
        time_str = time_manager.get_full_time_string()
        title_text = self.large_font.render(f"家 - {time_str}", True, self.text_color)
        title_rect = title_text.get_rect(center=(self.screen.get_width() // 2, 100))
        self.screen.blit(title_text, title_rect)
        
        # 選択肢描画
        start_y = 250
        choice_height = 80
        
        for i, choice in enumerate(self.choices):
            y_pos = start_y + (i * choice_height)
            
            # 選択中の場合はハイライト
            if i == self.selected_choice:
                color = self.selected_color
                # 背景ボックス
                choice_rect = pygame.Rect(self.screen.get_width() // 2 - 200, y_pos - 20, 400, 60)
                pygame.draw.rect(self.screen, self.border_color, choice_rect, 3)
            else:
                color = self.text_color
            
            # テキスト描画
            choice_text = self.font.render(choice["text"], True, color)
            choice_rect = choice_text.get_rect(center=(self.screen.get_width() // 2, y_pos))
            self.screen.blit(choice_text, choice_rect)
        
        # 操作説明
        help_text = "↑↓キー: 選択  Enter: 決定"
        help_surface = self.font.render(help_text, True, (150, 150, 150))
        help_rect = help_surface.get_rect(center=(self.screen.get_width() // 2, self.screen.get_height() - 50))
        self.screen.blit(help_surface, help_rect)
    
    def _render_save_load_screen(self):
        """セーブ/ロード画面描画"""
        # タイトル
        mode_text = "セーブ" if self.save_mode == "save" else "ロード"
        title_text = self.large_font.render(f"{mode_text}画面", True, self.text_color)
        title_rect = title_text.get_rect(center=(self.screen.get_width() // 2, 80))
        self.screen.blit(title_text, title_rect)
        
        # スロット描画（5列x2行）
        if self.save_slots:
            start_x = 80
            start_y = 150
            slot_width = 220
            slot_height = 100
            margin_x = 240
            margin_y = 120
            
            for i, slot_info in enumerate(self.save_slots):
                row = i // 5
                col = i % 5
                x = start_x + col * margin_x
                y = start_y + row * margin_y
                
                # 選択中の場合はハイライト
                if i == self.selected_slot:
                    color = self.selected_color
                    # 背景ボックス
                    slot_rect = pygame.Rect(x - 10, y - 10, slot_width + 20, slot_height + 20)
                    pygame.draw.rect(self.screen, self.border_color, slot_rect, 3)
                else:
                    color = self.text_color
                
                # スロット情報描画
                slot_text = f"スロット {slot_info['slot']}"
                slot_surface = self.font.render(slot_text, True, color)
                self.screen.blit(slot_surface, (x, y))
                
                if slot_info['exists']:
                    # プレイヤー名
                    name_surface = self.font.render(slot_info['player_name'], True, color)
                    self.screen.blit(name_surface, (x, y + 30))
                    
                    # 日付
                    date_surface = self.font.render(slot_info['date'][:10], True, color)  # 日付部分のみ
                    self.screen.blit(date_surface, (x, y + 60))
                else:
                    # 空きスロット
                    empty_surface = self.font.render("空きスロット", True, (100, 100, 100))
                    self.screen.blit(empty_surface, (x, y + 30))
        
        # 操作説明
        instruction_text = f"{mode_text}したいスロットを選択してください"
        instruction_surface = self.font.render(instruction_text, True, self.text_color)
        instruction_rect = instruction_surface.get_rect(center=(self.screen.get_width() // 2, 420))
        self.screen.blit(instruction_surface, instruction_rect)
        
        help_text = "↑↓キー: 選択  Enter: 決定  ESC: 戻る"
        help_surface = self.font.render(help_text, True, (150, 150, 150))
        help_rect = help_surface.get_rect(center=(self.screen.get_width() // 2, self.screen.get_height() - 50))
        self.screen.blit(help_surface, help_rect)