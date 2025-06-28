import pygame
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from config import init_game, SCREEN_WIDTH, SCREEN_HEIGHT, scale_pos, scale_size
from .main_menu_config import (
    COLORS, FONT_SIZES, LAYOUT, MenuState, DEFAULT_AUDIO_SETTINGS
)
from .ui_components import Button, Slider, Panel, VolumeIndicator, ToggleButton

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
            # 絶対パスでフォントを指定
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            font_dir = os.path.join(project_root, "mo-kiss", "fonts")
            project_font_path = os.path.join(font_dir, "MPLUSRounded1c-Regular.ttf")
            project_font_path = os.path.abspath(project_font_path)
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
        # メインメニューボタン（全て緑色、もっと左に配置）
        button_y = LAYOUT['main_menu_start_y']
        button_spacing = 100
        button_x = 100  # より左に配置
        self.buttons['start'] = Button(
            button_x, button_y, 300, 70, 
            "はじめから", self.fonts['medium'], 'green'
        )
        
        self.buttons['continue'] = Button(
            button_x, button_y + button_spacing, 300, 70,
            "つづきから", self.fonts['medium'], 'green'
        )
        
        self.buttons['settings'] = Button(
            button_x, button_y + button_spacing * 2, 300, 70,
            "設定", self.fonts['medium'], 'green'
        )
        
        # 右上のボタン（全て緑色、大きく調整）
        self.buttons['test'] = Button(
            LAYOUT['right_buttons_x'], LAYOUT['right_buttons_y'], 150, 60,
            "テスト", self.fonts['small'], 'green'
        )
        
        self.buttons['back'] = Button(
            LAYOUT['right_buttons_x'], LAYOUT['right_buttons_y'] + 80, 150, 60,
            "戻る", self.fonts['small'], 'green'
        )
        
        # 設定パネル
        self.panels['settings'] = Panel(
            LAYOUT['settings_panel_x'], LAYOUT['settings_panel_y'],
            LAYOUT['settings_panel_width'], LAYOUT['settings_panel_height']
        )
        
        # 設定用スライダー（横長パネルに合わせて調整）
        slider_x = LAYOUT['settings_panel_x'] + 150
        slider_y = LAYOUT['settings_panel_y'] + 120
        slider_spacing = 90
        
        self.sliders['bgm'] = Slider(
            slider_x, slider_y, 300, 30, 0, 100, self.audio_settings['bgm_volume']
        )
        
        self.sliders['voice'] = Slider(
            slider_x, slider_y + slider_spacing, 300, 30, 0, 100, self.audio_settings['voice_volume']
        )
        
        # 音量インジケーター（音符が入り切るよう調整）
        indicator_x = slider_x + 320  # スライダーの右端から少し離す
        self.volume_indicators['bgm'] = VolumeIndicator(
            indicator_x, slider_y - 5, self.audio_settings['bgm_volume']
        )
        
        self.volume_indicators['voice'] = VolumeIndicator(
            indicator_x, slider_y + slider_spacing - 5, self.audio_settings['voice_volume']
        )
        
        # 振動切り替えボタン（横長パネルに合わせて調整）
        vibration_button_x = LAYOUT['settings_panel_x'] + 150
        vibration_button_y = LAYOUT['settings_panel_y'] + 60
        self.toggle_buttons['vibration'] = ToggleButton(
            vibration_button_x, vibration_button_y, 120, 45, 
            self.fonts['small'], self.audio_settings['vibration']
        )
        
        # 初期設定に戻すボタン（少し上に移動）
        reset_button_x = LAYOUT['settings_panel_x'] + 50
        reset_button_y = LAYOUT['settings_panel_y'] + 350
        self.buttons['reset'] = Button(
            reset_button_x, reset_button_y, 240, 60,
            "初期設定に戻す", self.fonts['small'], 'green'
        )
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            # ボタンイベント処理
            for button_name, button in self.buttons.items():
                result = button.handle_event(event)
                if result == 'click':
                    self._handle_button_click(button_name)
            
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
        elif button_name == 'test':
            print("テスト機能")
            # ここにテスト機能のロジックを追加
        elif button_name == 'back':
            if self.state == MenuState.SETTINGS:
                self.state = MenuState.MAIN
                self._update_button_selection()
            else:
                self.running = False
        elif button_name == 'reset':
            self._reset_to_defaults()
    
    def handle_event(self, event):
        """単一のイベントを処理して結果を返す（main.pyからの呼び出し用）"""
        if event.type == pygame.QUIT:
            return "quit"
        
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
            return "start_game"
        elif button_name == 'continue':
            print("ゲームを続行")
            return "start_game"
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
        return None
    
    def _update_button_selection(self):
        """現在の状態に応じてボタンの選択状態を更新"""
        # 全ボタンの選択状態をリセット
        for button in self.buttons.values():
            button.is_selected = False
        
        # 現在の状態に応じて選択状態を設定
        if self.state == MenuState.SETTINGS:
            self.buttons['settings'].is_selected = True
    
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
    
    def draw(self):
        # 背景
        self.screen.fill(COLORS['bg_main'])
        
        # タイトル
        title_text = self.fonts['title'].render("メインメニュー", True, COLORS['text_title'])
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, LAYOUT['title_y']))
        self.screen.blit(title_text, title_rect)
        
        # メインメニューボタン（常に表示）
        self.buttons['start'].draw(self.screen)
        self.buttons['continue'].draw(self.screen)
        self.buttons['settings'].draw(self.screen)
        
        # 右上ボタン
        self.buttons['test'].draw(self.screen)
        self.buttons['back'].draw(self.screen)
        
        # 設定画面
        if self.state == MenuState.SETTINGS:
            self._draw_settings_panel()
        
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