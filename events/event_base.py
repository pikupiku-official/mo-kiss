import pygame
import sys
import os

class EventBase:
    """イベントベースクラス"""
    
    def __init__(self, screen_width=1600, screen_height=900):
        pygame.init()
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.screen = pygame.display.set_mode((screen_width, screen_height))
        pygame.display.set_caption("イベント実行中")
        
        # フォント設定
        self.load_fonts()
        
        # 色定義
        self.colors = {
            'background': (20, 25, 35),
            'text_box': (40, 45, 60, 200),
            'text_color': (255, 255, 255),
            'name_color': (255, 215, 0),
            'button_color': (70, 130, 180),
            'button_hover': (100, 149, 237)
        }
        
        # デバッグ用初期描画
        if hasattr(self, 'screen'):
            self.screen.fill(self.colors['background'])
            if hasattr(self, 'fonts'):
                test_text = self.fonts.get('medium', pygame.font.Font(None, 20)).render("EventBase初期化完了", True, self.colors['text_color'])
                self.screen.blit(test_text, (50, 50))
            pygame.display.flip()
        
        self.clock = pygame.time.Clock()
        self.running = False
        
    def load_fonts(self):
        """フォントを読み込み（クロスプラットフォーム対応）"""
        import platform
        
        # プロジェクトフォントの正しいパス（path_utils使用）
        from core.path_utils import get_font_path
        project_font_path = get_font_path("MPLUSRounded1c-Regular.ttf")
        
        # プラットフォーム別システムフォントパス
        system_font_paths = []
        system_name = platform.system()
        
        if system_name == "Darwin":  # macOS
            system_font_paths = [
                "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc",
                "/Library/Fonts/ヒラギノ角ゴ ProN W3.otf",
                "/System/Library/Fonts/Arial Unicode MS.ttf"
            ]
        elif system_name == "Windows":  # Windows
            system_font_paths = [
                "C:/Windows/Fonts/msgothic.ttc",  # MS ゴシック
                "C:/Windows/Fonts/meiryo.ttc",    # メイリオ
                "C:/Windows/Fonts/arial.ttf"      # Arial
            ]
        else:  # Linux
            system_font_paths = [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
            ]
        
        # 試行するフォントパスリスト
        font_paths = [project_font_path] + system_font_paths
        
        font_loaded = False
        
        for path in font_paths:
            try:
                if os.path.exists(path):
                    self.fonts = {
                        'large': pygame.font.Font(path, 28),
                        'medium': pygame.font.Font(path, 20),
                        'small': pygame.font.Font(path, 16)
                    }
                    font_loaded = True
                    print(f"EventBase フォント読み込み成功: {path}")
                    break
            except Exception as e:
                print(f"EventBase フォント読み込み失敗: {path} - {e}")
                continue
        
        if not font_loaded:
            # システムフォントから日本語対応フォントを探す
            japanese_fonts = []
            if system_name == "Darwin":  # macOS
                japanese_fonts = [
                    'hiraginosans',         # ヒラギノサンス（内部名）
                    'hiraginokakugothicpro', # ヒラギノ角ゴ Pro
                    'arialunicodems',       # Arial Unicode MS
                    'applesdgothicneo',     # Apple SD ゴシック Neo
                    'geneva'                # Geneva
                ]
            elif system_name == "Windows":  # Windows
                japanese_fonts = [
                    'msgothic',     # MS Gothic
                    'meiryo',       # Meiryo  
                    'yugothic',     # Yu Gothic
                    'msmincho',     # MS Mincho
                    'arial'         # Arial
                ]
            else:  # Linux
                japanese_fonts = [
                    'dejavu sans',
                    'liberation sans', 
                    'noto sans cjk jp',
                    'arial'
                ]
            
            # 日本語対応システムフォントを試行
            for font_name in japanese_fonts:
                try:
                    test_font = pygame.font.SysFont(font_name, 16)
                    # 日本語文字のテスト描画
                    test_surface = test_font.render('あ', True, (0, 0, 0))
                    if test_surface.get_width() > 5:  # 最小サイズチェック
                        self.fonts = {
                            'large': pygame.font.SysFont(font_name, 28, bold=True),
                            'medium': pygame.font.SysFont(font_name, 20),
                            'small': pygame.font.SysFont(font_name, 16)
                        }
                        font_loaded = True
                        print(f"EventBase システムフォント使用: {font_name}")
                        break
                except Exception as e:
                    print(f"EventBase フォント試行失敗: {font_name} - {e}")
                    continue
            
            # 最終的なフォールバック
            if not font_loaded:
                self.fonts = {
                    'large': pygame.font.Font(None, 28),
                    'medium': pygame.font.Font(None, 20),
                    'small': pygame.font.Font(None, 16)
                }
                print("⚠️ EventBase デフォルトフォント使用（日本語表示に問題がある可能性があります）")
    
    def run_event(self, event_id, event_title, heroine_name):
        """イベントを実行（サブクラスでオーバーライド）"""
        return self.run_default_event(event_id, event_title, heroine_name)
    
    def run_default_event(self, event_id, event_title, heroine_name):
        """デフォルトイベント実行"""
        print(f"🎬 イベント実行: {event_id} - {event_title}")
        
        self.running = True
        current_text = 0
        
        # デフォルトイベントテキスト
        event_texts = [
            {"speaker": "システム", "text": f"【{event_title}】"},
            {"speaker": heroine_name, "text": f"こんにちは。私は{heroine_name}です。"},
            {"speaker": "システム", "text": "これは仮のイベント実行画面です。"},
            {"speaker": "システム", "text": f"実際の{event_id}.pyファイルが作成されたら、"},
            {"speaker": "システム", "text": "このテキストは置き換えられます。"},
            {"speaker": "システム", "text": "スペースキーで次へ、Escキーでマップに戻ります。"}
        ]
        
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    return "quit"
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                        return "back_to_map"
                    elif event.key == pygame.K_SPACE:
                        current_text += 1
                        if current_text >= len(event_texts):
                            self.running = False
                            return "back_to_map"
            
            # 画面描画
            self.draw_event_screen(event_texts, current_text)
            
            pygame.display.flip()
            self.clock.tick(60)
        
        return "back_to_map"
    
    def draw_event_screen(self, event_texts, current_text):
        """イベント画面を描画"""
        self.screen.fill(self.colors['background'])
        
        # テキストボックス描画
        text_box_rect = pygame.Rect(50, self.screen_height - 200, 
                                  self.screen_width - 100, 150)
        pygame.draw.rect(self.screen, self.colors['text_box'], text_box_rect)
        pygame.draw.rect(self.screen, self.colors['button_color'], text_box_rect, 3)
        
        # 現在のテキストを表示
        if current_text < len(event_texts):
            current_dialog = event_texts[current_text]
            
            # 話者名表示
            speaker_text = self.fonts['medium'].render(
                current_dialog["speaker"], True, self.colors['name_color']
            )
            self.screen.blit(speaker_text, (text_box_rect.x + 20, text_box_rect.y + 10))
            
            # 本文表示
            main_text = self.fonts['medium'].render(
                current_dialog["text"], True, self.colors['text_color']
            )
            self.screen.blit(main_text, (text_box_rect.x + 20, text_box_rect.y + 50))
        
        # 操作説明
        help_text = "Space: 次へ | Esc: マップに戻る"
        help_surface = self.fonts['small'].render(help_text, True, self.colors['text_color'])
        self.screen.blit(help_surface, (10, 10))
        
        # 進行状況表示
        if current_text < len(event_texts):
            progress_text = f"{current_text + 1}/{len(event_texts)}"
            progress_surface = self.fonts['small'].render(progress_text, True, self.colors['text_color'])
            self.screen.blit(progress_surface, (self.screen_width - 100, 10))