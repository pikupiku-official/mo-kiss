"""
ローディング画面モジュール
シンプルな「＊＊を読み込み中…」表示機能を提供
"""

import pygame
import os
import sys
from contextlib import contextmanager
from contextvars import ContextVar
from core.path_utils import get_project_root

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
        font_dir = os.path.join(get_project_root(), "fonts")
        font_initialized = False
        
        # 第1段階: プロジェクト専用フォント (M PLUS Rounded 1c)
        try:
            project_font_path = os.path.join(font_dir, "MPLUSRounded1c-Regular.ttf")
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
    
    def show(self, message="読み込み中...", progress=None):
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

            if progress is not None:
                percent = max(0, min(100, int(progress)))
                progress_surface = self.font.render(f"{percent}%", True, self.text_color)
                progress_rect = progress_surface.get_rect(
                    midtop=(screen_rect.centerx, text_rect.bottom + 20)
                )
                self.screen.blit(progress_surface, progress_rect)
        
        # 画面更新
        pygame.display.flip()
        # Keep the window responsive during synchronous image preparation.
        # Pumping preserves QUIT and window events for the application loop.
        if progress is not None:
            pygame.event.pump()
    
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
    elif _loading_screen is not None and screen is not None:
        _loading_screen.screen = screen
    return _loading_screen

def show_loading(message="読み込み中...", screen=None, progress=None):
    """簡単にローディング画面を表示する便利関数"""
    loading_screen = get_loading_screen(screen)
    if loading_screen:
        loading_screen.show(message, progress=progress)


class _LoadingProgress:
    def __init__(self, screen, message):
        self.screen = screen
        self.message = message
        self.percent = -1

    def update(self, percent):
        percent = max(self.percent, max(0, min(100, int(percent))))
        if percent != self.percent:
            self.percent = percent
            if self.screen is not None:
                self.screen.show(self.message, progress=percent)


_active_progress = ContextVar("loading_progress", default=None)


@contextmanager
def loading_progress(message="読み込み中...", screen=None):
    """Show measured progress only for the active loading transition."""
    progress = _LoadingProgress(get_loading_screen(screen), message)
    token = _active_progress.set(progress)
    try:
        progress.update(0)
        yield progress
        progress.update(100)
    finally:
        _active_progress.reset(token)


def report_loading_progress(percent):
    """Report completed preparation work; inactive during ordinary playback."""
    progress = _active_progress.get()
    if progress is not None:
        progress.update(percent)

def hide_loading():
    """ローディング画面を非表示にする便利関数"""
    global _loading_screen
    if _loading_screen:
        _loading_screen.hide()
