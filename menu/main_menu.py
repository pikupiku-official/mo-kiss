import pygame
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from config import init_game, SCREEN_WIDTH, SCREEN_HEIGHT, scale_pos, scale_size
from .main_menu_config import (
    COLORS, FONT_SIZES, LAYOUT, MenuState, DEFAULT_AUDIO_SETTINGS
)
from .ui_components import Button, Slider, Panel, VolumeIndicator, ToggleButton, TextInput
from loading_screen import show_loading, hide_loading
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from dialogue.name_manager import get_name_manager
from save_manager import get_save_manager

class MainMenu:
    def __init__(self, screen=None):
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = MenuState.MAIN
        
        # フォントは後で初期化
        self.fonts = {}
        
        # 音声設定
        self.audio_settings = DEFAULT_AUDIO_SETTINGS.copy()
        
        # UIコンポーネント
        self.buttons = {}
        self.sliders = {}
        self.panels = {}
        self.volume_indicators = {}
        self.toggle_buttons = {}
        self.text_inputs = {}
        
        # 名前管理
        self.name_manager = get_name_manager()
        
        # セーブ管理
        self.save_manager = get_save_manager()
        self.save_slots = []
        self.selected_slot = 0
        
        # screen が提供されている場合は即座に初期化
        if self.screen:
            self._initialize_for_main_app()
    
    def _initialize_for_main_app(self):
        """main.pyから使用される場合の初期化"""
        pygame.font.init()
        self._init_fonts()
        self._create_ui_components()
        self._update_button_selection()
    
    def _init_fonts(self):
        """mapと同じフォント初期化ロジックを使用"""
        import platform
        
        # 段階的にフォントを試行
        self.fonts = {}
        font_initialized = False
        
        # 第1段階: プロジェクト専用フォント
        try:
            # 絶対パスでフォントを指定（path_utils使用）
            from path_utils import get_font_path
            project_font_path = get_font_path("MPLUS1p-Regular.ttf")
            print(f"フォントパスを試行中: {project_font_path}")
            print(f"フォントファイル存在確認: {os.path.exists(project_font_path)}")
            
            test_font = pygame.font.Font(project_font_path, 16)
            # 日本語テスト
            test_surface = test_font.render('テスト', True, (0, 0, 0))
            print(f"日本語テスト描画幅: {test_surface.get_width()}")
            
            if test_surface.get_width() > 10:
                self.fonts = {
                    'title': pygame.font.Font(project_font_path, FONT_SIZES['title']),
                    'large': pygame.font.Font(project_font_path, FONT_SIZES['large']),
                    'medium': pygame.font.Font(project_font_path, FONT_SIZES['medium']),
                    'small': pygame.font.Font(project_font_path, FONT_SIZES['small'])
                }
                font_initialized = True
                print("プロジェクト専用フォント (M PLUS Rounded 1c) を使用")
        except Exception as e:
            print(f"プロジェクト専用フォント読み込み失敗: {e}")
        
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
                        self.fonts = {
                            'title': pygame.font.SysFont(font_name, FONT_SIZES['title']),
                            'large': pygame.font.SysFont(font_name, FONT_SIZES['large']),
                            'medium': pygame.font.SysFont(font_name, FONT_SIZES['medium']),
                            'small': pygame.font.SysFont(font_name, FONT_SIZES['small'])
                        }
                        font_initialized = True
                        print(f"プラットフォーム固有フォント ({font_name}) を使用")
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
                            self.fonts = {
                                'title': pygame.font.SysFont(font_name, FONT_SIZES['title']),
                                'large': pygame.font.SysFont(font_name, FONT_SIZES['large']),
                                'medium': pygame.font.SysFont(font_name, FONT_SIZES['medium']),
                                'small': pygame.font.SysFont(font_name, FONT_SIZES['small'])
                            }
                            font_initialized = True
                            print(f"動的検索フォント ({font_name}) を使用")
                            break
                    except:
                        continue
                if font_initialized:
                    break
        
        # 第4段階: デフォルトフォント（最終フォールバック）
        if not font_initialized:
            print("警告: 適切な日本語フォントが見つかりません。デフォルトフォントを使用します。")
            try:
                self.fonts = {
                    'title': pygame.font.Font(None, FONT_SIZES['title']),
                    'large': pygame.font.Font(None, FONT_SIZES['large']),
                    'medium': pygame.font.Font(None, FONT_SIZES['medium']),
                    'small': pygame.font.Font(None, FONT_SIZES['small'])
                }
            except:
                # 最終的なフォールバック
                default_font = pygame.font.get_default_font()
                self.fonts = {
                    'title': pygame.font.Font(default_font, FONT_SIZES['title']),
                    'large': pygame.font.Font(default_font, FONT_SIZES['large']),
                    'medium': pygame.font.Font(default_font, FONT_SIZES['medium']),
                    'small': pygame.font.Font(default_font, FONT_SIZES['small'])
                }
    
    def _create_ui_components(self):
        from config import SCALE  # SCALEをインポート

        # メインメニューボタン（全て緑色、4:3コンテンツ基準で配置）
        # 仮想座標（1440x1080基準）で位置を定義
        virtual_button_x = 75  # 100 * 0.75（4:3基準）
        virtual_button_y = LAYOUT['main_menu_start_y']
        virtual_button_spacing = 75  # 100 * 0.75

        # scale_pos()で実座標に変換
        button_x, button_y = scale_pos(virtual_button_x, virtual_button_y)
        _, spacing_offset = scale_pos(0, virtual_button_spacing)

        self.buttons['start'] = Button(
            button_x, button_y, 300, 70,
            "はじめから", self.fonts['medium'], 'green'
        )

        self.buttons['continue'] = Button(
            button_x, button_y + spacing_offset, 300, 70,
            "つづきから", self.fonts['medium'], 'green'
        )

        self.buttons['save'] = Button(
            button_x, button_y + spacing_offset * 2, 300, 70,
            "セーブ", self.fonts['medium'], 'green'
        )

        self.buttons['load'] = Button(
            button_x, button_y + spacing_offset * 3, 300, 70,
            "ロード", self.fonts['medium'], 'green'
        )

        self.buttons['settings'] = Button(
            button_x, button_y + spacing_offset * 4, 300, 70,
            "設定", self.fonts['medium'], 'green'
        )

        self.buttons['home'] = Button(
            button_x, button_y + spacing_offset * 5, 300, 70,
            "家", self.fonts['medium'], 'green'
        )

        # 右上のボタン（4:3コンテンツ基準で配置）
        right_btn_x, right_btn_y = scale_pos(LAYOUT['right_buttons_x'], LAYOUT['right_buttons_y'])
        _, right_btn_spacing = scale_pos(0, 60)  # 80 * 0.75 = 60

        self.buttons['test'] = Button(
            right_btn_x, right_btn_y, 150, 60,
            "テスト", self.fonts['small'], 'green'
        )

        self.buttons['back'] = Button(
            right_btn_x, right_btn_y + right_btn_spacing, 150, 60,
            "戻る", self.fonts['small'], 'green'
        )
        
        # 設定パネル（4:3コンテンツ基準）
        panel_x, panel_y = scale_pos(LAYOUT['settings_panel_x'], LAYOUT['settings_panel_y'])
        panel_w, panel_h = scale_size(LAYOUT['settings_panel_width'], LAYOUT['settings_panel_height'])

        self.panels['settings'] = Panel(panel_x, panel_y, panel_w, panel_h)

        # 設定用スライダー（4:3コンテンツ基準）
        slider_x, slider_y = scale_pos(LAYOUT['settings_panel_x'] + 113, LAYOUT['settings_panel_y'] + 90)  # 150*0.75=113, 120*0.75=90
        _, slider_spacing = scale_pos(0, 68)  # 90 * 0.75 = 68

        self.sliders['bgm'] = Slider(
            slider_x, slider_y, 300, 30, 0, 100, self.audio_settings['bgm_volume']
        )

        self.sliders['voice'] = Slider(
            slider_x, slider_y + slider_spacing, 300, 30, 0, 100, self.audio_settings['voice_volume']
        )

        # 音量インジケーター（4:3コンテンツ基準）
        indicator_x = slider_x + 320
        self.volume_indicators['bgm'] = VolumeIndicator(
            indicator_x, slider_y - 5, self.audio_settings['bgm_volume']
        )

        self.volume_indicators['voice'] = VolumeIndicator(
            indicator_x, slider_y + slider_spacing - 5, self.audio_settings['voice_volume']
        )

        # 振動切り替えボタン（4:3コンテンツ基準）
        vib_btn_x, vib_btn_y = scale_pos(LAYOUT['settings_panel_x'] + 113, LAYOUT['settings_panel_y'] + 45)  # 150*0.75=113, 60*0.75=45
        self.toggle_buttons['vibration'] = ToggleButton(
            vib_btn_x, vib_btn_y, 120, 45,
            self.fonts['small'], self.audio_settings['vibration']
        )

        # 初期設定に戻すボタン（4:3コンテンツ基準）
        reset_btn_x, reset_btn_y = scale_pos(LAYOUT['settings_panel_x'] + 38, LAYOUT['settings_panel_y'] + 263)  # 50*0.75=38, 350*0.75=263
        self.buttons['reset'] = Button(
            reset_btn_x, reset_btn_y, 240, 60,
            "初期設定に戻す", self.fonts['small'], 'green'
        )

        # 名前入力欄（「はじめから」ボタンの右側、4:3コンテンツ基準）
        name_input_x = button_x + int(320 * SCALE)  # 「はじめから」ボタンの右側
        name_input_y = button_y

        self.text_inputs['surname'] = TextInput(
            name_input_x, name_input_y, 120, 40,
            self.fonts['small'], max_length=3, placeholder="苗字"
        )

        self.text_inputs['name'] = TextInput(
            name_input_x + 130, name_input_y, 120, 40,
            self.fonts['small'], max_length=3, placeholder="名前"
        )
        
        # 保存された名前を設定
        self.text_inputs['surname'].set_text(self.name_manager.get_surname())
        self.text_inputs['name'].set_text(self.name_manager.get_name())
        
        # SDL2テキスト入力の初期化（IME対応）
        pygame.key.set_repeat()  # キーリピート設定をリセット
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            # ボタンイベント処理
            for button_name, button in self.buttons.items():
                result = button.handle_event(event)
                if result == 'click':
                    self._handle_button_click(button_name)
            
            # テキスト入力イベント処理
            for input_name, text_input in self.text_inputs.items():
                result = text_input.handle_event(event)
                if result == 'focus':
                    # 新しいフィールドがフォーカスされた場合、他のフィールドのフォーカスを外す
                    for other_name, other_input in self.text_inputs.items():
                        if other_name != input_name and other_input.is_focused:
                            other_input.is_focused = False
                            other_input.composition_text = ""
                            other_input.is_composing = False
                            pygame.key.stop_text_input()
                elif result == 'text_changed':
                    # 名前が変更されたら即座に保存
                    surname = self.text_inputs['surname'].get_text()
                    name = self.text_inputs['name'].get_text()
                    self.name_manager.set_names(surname, name)
            
            # スライダーイベント処理（設定画面でのみ）
            if self.state == MenuState.SETTINGS:
                for slider_name, slider in self.sliders.items():
                    if slider.handle_event(event):
                        self._handle_slider_change(slider_name, slider.val)
                
                # トグルボタンイベント処理
                for toggle_name, toggle_button in self.toggle_buttons.items():
                    result = toggle_button.handle_event(event)
                    if result == 'toggle':
                        self._handle_toggle_change(toggle_name, toggle_button.is_enabled)
    
    def _handle_button_click(self, button_name):
        if button_name == 'start':
            print("新しいゲームを開始")
            # ここにゲーム開始のロジックを追加
        elif button_name == 'continue':
            print("ゲームを続行")
            # ここにゲーム続行のロジックを追加
        elif button_name == 'settings':
            self.state = MenuState.SETTINGS
            self._update_button_selection()
        elif button_name == 'save':
            self.state = MenuState.SAVE
            self._load_save_slots()
            self._update_button_selection()
        elif button_name == 'load':
            self.state = MenuState.LOAD
            self._load_save_slots()
            self._update_button_selection()
        elif button_name == 'test':
            print("テスト機能")
            # ここにテスト機能のロジックを追加
        elif button_name == 'back':
            if self.state == MenuState.SETTINGS:
                self.state = MenuState.MAIN
                self._update_button_selection()
            elif self.state == MenuState.SAVE or self.state == MenuState.LOAD:
                self.state = MenuState.MAIN
                self._update_button_selection()
            else:
                self.running = False
        elif button_name == 'reset':
            self._reset_to_defaults()
        elif button_name.startswith('slot_'):
            slot_num = int(button_name.split('_')[1])
            self._handle_slot_click(slot_num)
    
    def handle_event(self, event):
        """単一のイベントを処理して結果を返す（main.pyからの呼び出し用）"""
        if event.type == pygame.QUIT:
            return "quit"
        
        # テキスト入力イベント処理
        for input_name, text_input in self.text_inputs.items():
            result = text_input.handle_event(event)
            if result == 'focus':
                # 新しいフィールドがフォーカスされた場合、他のフィールドのフォーカスを外す
                for other_name, other_input in self.text_inputs.items():
                    if other_name != input_name and other_input.is_focused:
                        other_input.is_focused = False
                        other_input.composition_text = ""
                        other_input.is_composing = False
                        pygame.key.stop_text_input()
            elif result == 'text_changed':
                # 名前が変更されたら即座に保存
                surname = self.text_inputs['surname'].get_text()
                name = self.text_inputs['name'].get_text()
                self.name_manager.set_names(surname, name)
        
        # ボタンイベント処理
        for button_name, button in self.buttons.items():
            result = button.handle_event(event)
            if result == 'click':
                return self._handle_button_click_with_result(button_name)
        
        # スライダーイベント処理（設定画面でのみ）
        if self.state == MenuState.SETTINGS:
            for slider_name, slider in self.sliders.items():
                if slider.handle_event(event):
                    self._handle_slider_change(slider_name, slider.val)
            
            # トグルボタンイベント処理
            for toggle_name, toggle_button in self.toggle_buttons.items():
                result = toggle_button.handle_event(event)
                if result == 'toggle':
                    self._handle_toggle_change(toggle_name, toggle_button.is_enabled)
        
        return None
    
    def _handle_button_click_with_result(self, button_name):
        """ボタンクリック処理（main.py用に結果を返す）"""
        if button_name == 'start':
            print("新しいゲームを開始")
            return "new_game"
        elif button_name == 'continue':
            print("ゲームを続行")
            return "continue_game"
        elif button_name == 'settings':
            self.state = MenuState.SETTINGS
            self._update_button_selection()
            return None
        elif button_name == 'test':
            print("テスト機能")
            return "dialogue_test"
        elif button_name == 'back':
            if self.state == MenuState.SETTINGS:
                self.state = MenuState.MAIN
                self._update_button_selection()
                return None
            else:
                return "quit"
        elif button_name == 'reset':
            self._reset_to_defaults()
            return None
        elif button_name == 'save':
            self.state = MenuState.SAVE
            self._load_save_slots()
            self._update_button_selection()
            return None
        elif button_name == 'load':
            self.state = MenuState.LOAD
            self._load_save_slots()
            self._update_button_selection()
            return None
        elif button_name == 'home':
            print("家モジュールへ移動")
            return "go_to_home"
        elif button_name.startswith('slot_'):
            slot_num = int(button_name.split('_')[1])
            result = self._handle_slot_click(slot_num)
            if result == 'game_loaded':
                return "continue_game"
            return None
        return None
    
    def _update_button_selection(self):
        """現在の状態に応じてボタンの選択状態を更新"""
        # 全ボタンの選択状態をリセット
        for button in self.buttons.values():
            button.is_selected = False
        
        # 現在の状態に応じて選択状態を設定
        if self.state == MenuState.SETTINGS:
            self.buttons['settings'].is_selected = True
        elif self.state == MenuState.SAVE:
            if 'save' in self.buttons:
                self.buttons['save'].is_selected = True
        elif self.state == MenuState.LOAD:
            if 'load' in self.buttons:
                self.buttons['load'].is_selected = True
    
    def _handle_slider_change(self, slider_name, value):
        self.audio_settings[f'{slider_name}_volume'] = int(value)
        self.volume_indicators[slider_name].volume_level = int(value)
        print(f"{slider_name}音量: {int(value)}")
    
    def _handle_toggle_change(self, toggle_name, is_enabled):
        self.audio_settings[toggle_name] = is_enabled
        print(f"{toggle_name}: {'有効' if is_enabled else '無効'}")
    
    def _reset_to_defaults(self):
        """設定を初期値に戻す"""
        self.audio_settings = DEFAULT_AUDIO_SETTINGS.copy()
        
        # スライダーの値を更新
        self.sliders['bgm'].val = self.audio_settings['bgm_volume']
        self.sliders['voice'].val = self.audio_settings['voice_volume']
        
        # 音量インジケーターを更新
        self.volume_indicators['bgm'].volume_level = self.audio_settings['bgm_volume']
        self.volume_indicators['voice'].volume_level = self.audio_settings['voice_volume']
        
        # トグルボタンを更新
        self.toggle_buttons['vibration'].is_enabled = self.audio_settings['vibration']
        
        print("設定を初期状態に戻しました")
    
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
        
        # セーブ/ロード画面用のボタンを作成
        self._create_save_load_buttons()
    
    def _create_save_load_buttons(self):
        """セーブ/ロード画面のボタンを作成（4:3コンテンツ基準）"""
        # 既存のスロットボタンを削除
        for key in list(self.buttons.keys()):
            if key.startswith('slot_'):
                del self.buttons[key]

        # スロットボタンを作成（5列x2行、4:3コンテンツ基準）
        # 仮想座標（1440基準）
        virtual_start_x = 113  # 150 * 0.75
        virtual_start_y = 150  # 200 * 0.75
        button_width = 200
        button_height = 120
        virtual_margin_x = 165  # 220 * 0.75
        virtual_margin_y = 105  # 140 * 0.75

        for i, slot_info in enumerate(self.save_slots):
            row = i // 5
            col = i % 5
            virtual_x = virtual_start_x + col * virtual_margin_x
            virtual_y = virtual_start_y + row * virtual_margin_y

            # scale_pos()で実座標に変換
            x, y = scale_pos(virtual_x, virtual_y)
            
            slot_text = f"スロット {slot_info['slot']}"
            if slot_info['exists']:
                slot_text += f"\n{slot_info['player_name']}\n{slot_info['date']}"
            else:
                slot_text += "\n空きスロット"
            
            self.buttons[f"slot_{slot_info['slot']}"] = Button(
                x, y, button_width, button_height,
                slot_text, self.fonts['small'], 'green' if slot_info['exists'] else 'normal'
            )
    
    def _handle_slot_click(self, slot_num):
        """スロットクリック処理"""
        slot_name = f"saveslot_{slot_num:02d}"
        
        if self.state == MenuState.SAVE:
            # セーブ処理
            try:
                show_loading("データを保存中...", self.screen)
                self.save_manager.save_game(slot_name)
                print(f"スロット {slot_num} にセーブしました")
                # スロット情報を再読み込み
                self._load_save_slots()
                hide_loading()
                return 'game_saved'
            except Exception as e:
                print(f"セーブに失敗しました: {e}")
                hide_loading()
                return 'save_failed'
        
        elif self.state == MenuState.LOAD:
            # ロード処理
            if self.save_manager.has_save(slot_name):
                try:
                    show_loading("データを読み込み中...", self.screen)
                    self.save_manager.load_game(slot_name)
                    print(f"スロット {slot_num} からロードしました")
                    hide_loading()
                    return 'game_loaded'
                except Exception as e:
                    print(f"ロードに失敗しました: {e}")
                    hide_loading()
                    return 'load_failed'
            else:
                print(f"スロット {slot_num} にセーブデータがありません")
                return 'no_save_data'
        
        return None
    
    def draw(self):
        # 全画面を黒で塗りつぶし（ピラーボックス用）
        self.screen.fill((0, 0, 0))

        # 4:3コンテンツ領域に背景色を塗る
        from config import CONTENT_WIDTH, CONTENT_HEIGHT, OFFSET_X, OFFSET_Y
        content_rect = pygame.Rect(OFFSET_X, OFFSET_Y, CONTENT_WIDTH, CONTENT_HEIGHT)
        self.screen.fill(COLORS['bg_main'], content_rect)

        # ★ピラーボックスを「奈落」にする：4:3コンテンツ領域にクリッピング設定★
        self.screen.set_clip(content_rect)

        # タイトル（4:3コンテンツ基準）
        from config import VIRTUAL_WIDTH
        title_text = self.fonts['title'].render("メインメニュー", True, COLORS['text_title'])
        title_center_x, title_center_y = scale_pos(VIRTUAL_WIDTH // 2, LAYOUT['title_y'])
        title_rect = title_text.get_rect(center=(title_center_x, title_center_y))
        self.screen.blit(title_text, title_rect)
        
        # メインメニューボタン（常に表示）
        self.buttons['start'].draw(self.screen)
        self.buttons['continue'].draw(self.screen)
        self.buttons['save'].draw(self.screen)
        self.buttons['load'].draw(self.screen)
        self.buttons['settings'].draw(self.screen)
        self.buttons['home'].draw(self.screen)
        
        # 名前入力欄（「はじめから」ボタンの横に表示）
        self.text_inputs['surname'].draw(self.screen)
        self.text_inputs['name'].draw(self.screen)
        
        # ラベルを表示
        surname_label = self.fonts['small'].render("苗字:", True, COLORS['text_main'])
        name_label = self.fonts['small'].render("名前:", True, COLORS['text_main'])
        self.screen.blit(surname_label, (self.text_inputs['surname'].rect.x, self.text_inputs['surname'].rect.y - 25))
        self.screen.blit(name_label, (self.text_inputs['name'].rect.x, self.text_inputs['name'].rect.y - 25))
        
        # 右上ボタン
        self.buttons['test'].draw(self.screen)
        self.buttons['back'].draw(self.screen)
        
        # 設定画面
        if self.state == MenuState.SETTINGS:
            self._draw_settings_panel()
        elif self.state == MenuState.SAVE:
            self._draw_save_load_panel("セーブ")
        elif self.state == MenuState.LOAD:
            self._draw_save_load_panel("ロード")

        # ★クリッピング解除★
        self.screen.set_clip(None)

        pygame.display.flip()
    
    def _draw_settings_panel(self):
        # 設定パネル
        self.panels['settings'].draw(self.screen)
        
        # 設定項目のテキスト
        panel_x = LAYOUT['settings_panel_x']
        panel_y = LAYOUT['settings_panel_y']
        
        # 振動設定（大きく調整）
        vibration_text = self.fonts['medium'].render("振動", True, COLORS['text_main'])
        self.screen.blit(vibration_text, (panel_x + 50, panel_y + 60))
        
        # 振動切り替えボタンを描画
        self.toggle_buttons['vibration'].draw(self.screen)
        
        # BGM設定（大きく調整）
        bgm_text = self.fonts['medium'].render("BGM", True, COLORS['text_main'])
        self.screen.blit(bgm_text, (panel_x + 50, panel_y + 120))
        self.sliders['bgm'].draw(self.screen)
        self.volume_indicators['bgm'].draw(self.screen)
        
        # 音声設定（大きく調整）
        voice_text = self.fonts['medium'].render("音声", True, COLORS['text_main'])
        self.screen.blit(voice_text, (panel_x + 50, panel_y + 210))
        self.sliders['voice'].draw(self.screen)
        self.volume_indicators['voice'].draw(self.screen)
        
        # 初期設定に戻すボタンを描画
        self.buttons['reset'].draw(self.screen)
    
    def _draw_save_load_panel(self, title):
        """セーブ/ロード画面を描画（4:3コンテンツ基準）"""
        from config import VIRTUAL_WIDTH

        # セーブ/ロードタイトル
        title_text = self.fonts['title'].render(f"{title}画面", True, COLORS['text_title'])
        title_center_x, title_center_y = scale_pos(VIRTUAL_WIDTH // 2, 113)  # 150 * 0.75 = 113
        title_rect = title_text.get_rect(center=(title_center_x, title_center_y))
        self.screen.blit(title_text, title_rect)

        # スロットボタンを描画
        for button_name, button in self.buttons.items():
            if button_name.startswith('slot_'):
                button.draw(self.screen)

        # 説明テキスト
        if self.state == MenuState.SAVE:
            instruction_text = "セーブしたいスロットを選択してください"
        else:
            instruction_text = "ロードしたいスロットを選択してください"

        instruction_surface = self.fonts['medium'].render(instruction_text, True, COLORS['text_main'])
        instr_center_x, instr_center_y = scale_pos(VIRTUAL_WIDTH // 2, 375)  # 500 * 0.75 = 375
        instruction_rect = instruction_surface.get_rect(center=(instr_center_x, instr_center_y))
        self.screen.blit(instruction_surface, instruction_rect)
    
    def update(self):
        """ゲーム状態の更新（main.pyからの呼び出し用）"""
        # UI要素のアニメーション更新
        for button in self.buttons.values():
            if hasattr(button, 'update'):
                button.update()
        
        # スライダーの状態更新
        for slider in self.sliders.values():
            if hasattr(slider, 'update'):
                slider.update()
        
        # 音量インジケーターの更新
        for indicator in self.volume_indicators.values():
            if hasattr(indicator, 'update'):
                indicator.update()
    
    def render(self):
        """画面描画（main.pyからの呼び出し用）"""
        self.draw()
    
    def run(self):
        self.screen = init_game()
        
        # pygame初期化後にフォントとUIコンポーネントを初期化
        pygame.font.init()
        self._init_fonts()
        self._create_ui_components()
        self._update_button_selection()  # 初期選択状態を設定
        
        while self.running:
            self.handle_events()
            self.draw()
            self.clock.tick(60)
        
        pygame.quit()

def main():
    menu = MainMenu()
    menu.run()

if __name__ == "__main__":
    main()