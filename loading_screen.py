"""
ローディング画面モジュール
シンプルな「＊＊を読み込み中…」表示機能を提供
"""

import pygame
import os
import sys

class LoadingScreen:
    """ローディング画面を管理するクラス"""
    
    def __init__(self, screen):
        """
        Args:
            screen: pygame.display.set_mode()で作成されたスクリーンオブジェクト
        """
        self.screen = screen
        self.font = None
        self.background_color = (0, 0, 0)  # 真っ黒
        self.text_color = (255, 255, 255)  # 白文字
        self.font_size = 48
        self._initialize_font()
        
    def _initialize_font(self):
        """日本語対応フォントを初期化"""
        font_initialized = False
        
        # 第1段階: プロジェクト専用フォント (M PLUS Rounded 1c)
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            font_dir = os.path.join(current_dir, "fonts")
            project_font_path = os.path.join(font_dir, "MPLUS1p-Regular.ttf")
            project_font_path = os.path.abspath(project_font_path)
            
            if os.path.exists(project_font_path):
                test_font = pygame.font.Font(project_font_path, 16)
                test_surface = test_font.render('テスト', True, (0, 0, 0))
                
                if test_surface.get_width() > 10:
                    self.font = pygame.font.Font(project_font_path, self.font_size)
                    font_initialized = True
                    print("ローディング画面: プロジェクト専用フォント (M PLUS Rounded 1c) を使用")
        except Exception as e:
            print(f"ローディング画面: プロジェクトフォント読み込みエラー: {e}")
        
        # 第2段階: プラットフォーム固有のフォント
        if not font_initialized:
            platform = sys.platform.lower()
            if 'win' in platform:
                platform_fonts = ['yugothi', 'meiryo', 'msgothic']
            elif 'darwin' in platform:
                platform_fonts = ['hiraginokakugothicpronw3', 'hiraginokakugothicpro']
            else:  # Linux
                platform_fonts = ['notosanscjk', 'takao', 'vlgothic']
            
            for font_name in platform_fonts:
                try:
                    test_font = pygame.font.SysFont(font_name, 16)
                    test_surface = test_font.render('テスト', True, (0, 0, 0))
                    if test_surface.get_width() > 5:
                        self.font = pygame.font.SysFont(font_name, self.font_size)
                        font_initialized = True
                        print(f"ローディング画面: プラットフォーム固有フォント ({font_name}) を使用")
                        break
                except Exception:
                    continue
        
        # 第3段階: 利用可能フォントから日本語対応を検索
        if not font_initialized:
            try:
                available_fonts = pygame.font.get_fonts()
                japanese_keywords = ['hiragino', 'gothic', 'meiryo', 'yu', 'noto', 'sans', 'mincho']
                
                for keyword in japanese_keywords:
                    matching_fonts = [f for f in available_fonts if keyword in f.lower()]
                    for font_name in matching_fonts:
                        try:
                            test_font = pygame.font.SysFont(font_name, 16)
                            test_surface = test_font.render('あ', True, (0, 0, 0))
                            if test_surface.get_width() > 5:
                                self.font = pygame.font.SysFont(font_name, self.font_size)
                                font_initialized = True
                                print(f"ローディング画面: 動的検索フォント ({font_name}) を使用")
                                break
                        except Exception:
                            continue
                    if font_initialized:
                        break
            except Exception:
                pass
        
        # 第4段階: デフォルトフォント（フォールバック）
        if not font_initialized:
            print("ローディング画面: 警告: 適切な日本語フォントが見つかりません。デフォルトフォントを使用します。")
            try:
                self.font = pygame.font.Font(None, self.font_size)
            except Exception:
                # 最終的なフォールバック
                default_font = pygame.font.get_default_font()
                self.font = pygame.font.Font(default_font, self.font_size)
    
    def show(self, message="読み込み中..."):
        """
        ローディング画面を表示
        
        Args:
            message (str): 表示するメッセージ（デフォルト: "読み込み中..."）
        """
        # 画面を真っ黒にクリア
        self.screen.fill(self.background_color)
        
        # テキストを描画
        if self.font:
            text_surface = self.font.render(message, True, self.text_color)
            
            # 画面中央に配置
            screen_rect = self.screen.get_rect()
            text_rect = text_surface.get_rect(center=screen_rect.center)
            
            self.screen.blit(text_surface, text_rect)
        
        # 画面更新
        pygame.display.flip()
    
    def hide(self):
        """ローディング画面を終了（画面をクリア）"""
        self.screen.fill(self.background_color)
        pygame.display.flip()
    
    def update_message(self, message):
        """メッセージを更新して再描画"""
        self.show(message)

# グローバルインスタンス管理
_loading_screen = None

def get_loading_screen(screen=None):
    """LoadingScreenのグローバルインスタンスを取得"""
    global _loading_screen
    if _loading_screen is None and screen is not None:
        _loading_screen = LoadingScreen(screen)
    return _loading_screen

def show_loading(message="読み込み中...", screen=None):
    """簡単にローディング画面を表示する便利関数"""
    loading_screen = get_loading_screen(screen)
    if loading_screen:
        loading_screen.show(message)

def hide_loading():
    """ローディング画面を非表示にする便利関数"""
    global _loading_screen
    if _loading_screen:
        _loading_screen.hide()