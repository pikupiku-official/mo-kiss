import pygame
import os
from config import *

class TitleScreen:
    """タイトル画面クラス"""
    
    def __init__(self, screen, debug=False):
        """
        タイトル画面を初期化する
        
        Args:
            screen: Pygameスクリーン
            debug: デバッグモード
        """
        self.screen = screen
        self.debug = debug
        
        # フォント設定
        self.title_font_size = int(SCREEN_HEIGHT * TITLE_FONT_SIZE_RATIO)
        self.title_font = pygame.font.SysFont("msgothic", self.title_font_size)
        
        # 背景画像の読み込み
        self.background_image = None
        self.load_title_image()
        
        # テキスト設定
        self.title_text = TITLE_TEXT
        self.title_color = TITLE_TEXT_COLOR
        
        # 位置計算
        self.calculate_positions()
        
        # 点滅効果用
        self.blink_timer = 0
        self.blink_visible = True
        self.blink_interval = 1000  # 1秒間隔で点滅
        
        # BGM設定
        self.bgm_loaded = False
        self.load_title_bgm()
    
    def load_title_image(self):
        """タイトル背景画像を読み込む"""
        try:
            if os.path.exists(TITLE_IMAGE_PATH):
                # 画像を読み込んで画面サイズにスケーリング
                original_image = pygame.image.load(TITLE_IMAGE_PATH)
                self.background_image = pygame.transform.scale(original_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
                if self.debug:
                    print(f"タイトル画像を読み込みました: {TITLE_IMAGE_PATH}")
            else:
                if self.debug:
                    print(f"タイトル画像が見つかりません: {TITLE_IMAGE_PATH}")
                self.background_image = None
        except Exception as e:
            if self.debug:
                print(f"タイトル画像の読み込みに失敗: {e}")
            self.background_image = None
    
    def load_title_bgm(self):
        """タイトル画面のBGMを読み込む"""
        try:
            pygame.mixer.init()
            bgm_path = os.path.join(os.path.dirname(__file__), "sounds", "bgms", "koi_no_dancesite.mp3")
            
            if os.path.exists(bgm_path):
                # m4aファイルの読み込みを試行
                try:
                    pygame.mixer.music.load(bgm_path)
                    self.bgm_loaded = True
                    if self.debug:
                        print(f"タイトルBGMを読み込みました: {bgm_path}")
                except pygame.error as e:
                    if self.debug:
                        print(f"m4aファイルの読み込みに失敗（フォーマット非対応の可能性）: {e}")
                        print("代替BGMファイルを探しています...")
                    
                    # 代替BGMファイルを探す
                    alternative_bgms = [
                        "maou_bgm_8bit29.mp3",
                        "maou_bgm_piano41.mp3",
                        "Mok1_Lap1.mp3"
                    ]
                    
                    for alt_bgm in alternative_bgms:
                        alt_path = os.path.join(os.path.dirname(__file__), "sounds", "bgms", alt_bgm)
                        if os.path.exists(alt_path):
                            try:
                                pygame.mixer.music.load(alt_path)
                                self.bgm_loaded = True
                                if self.debug:
                                    print(f"代替タイトルBGMを読み込みました: {alt_path}")
                                break
                            except pygame.error:
                                continue
            else:
                if self.debug:
                    print(f"タイトルBGMファイルが見つかりません: {bgm_path}")
                    
        except Exception as e:
            if self.debug:
                print(f"BGM初期化エラー: {e}")
            self.bgm_loaded = False
    
    def play_title_bgm(self):
        """タイトルBGMを再生"""
        if self.bgm_loaded:
            try:
                pygame.mixer.music.play(-1)  # ループ再生
                pygame.mixer.music.set_volume(0.3)  # 音量を30%に設定
                if self.debug:
                    print("タイトルBGM再生開始")
            except Exception as e:
                if self.debug:
                    print(f"BGM再生エラー: {e}")
    
    def stop_title_bgm(self):
        """タイトルBGMを停止"""
        try:
            pygame.mixer.music.stop()
            if self.debug:
                print("タイトルBGM停止")
        except Exception as e:
            if self.debug:
                print(f"BGM停止エラー: {e}")
    
    def calculate_positions(self):
        """テキスト位置を計算する"""
        # テキストのサーフェスを作成してサイズを取得
        text_surface = self.title_font.render(self.title_text, True, self.title_color)
        text_width = text_surface.get_width()
        text_height = text_surface.get_height()
        
        # 画面中央少し下に配置
        self.text_x = (SCREEN_WIDTH - text_width) // 2
        self.text_y = (SCREEN_HEIGHT // 2) + TITLE_TEXT_Y_OFFSET
    
    def update(self):
        """タイトル画面の更新（点滅効果）"""
        current_time = pygame.time.get_ticks()
        
        # 点滅効果の更新
        if current_time - self.blink_timer >= self.blink_interval:
            self.blink_visible = not self.blink_visible
            self.blink_timer = current_time
    
    def render(self):
        """タイトル画面を描画する"""
        # 背景を描画
        if self.background_image:
            self.screen.blit(self.background_image, (0, 0))
        else:
            # 背景画像がない場合は黒で塗りつぶし
            self.screen.fill((0, 0, 0))
        
        # "PRESS ANY KEY" テキストを点滅表示
        if self.blink_visible:
            # 影効果を適用（テキストレンダラーと同様）
            if FONT_EFFECTS.get("enable_shadow", False):
                # 影を描画
                shadow_color = (0, 0, 0)
                shadow_surface = self.title_font.render(self.title_text, True, shadow_color)
                
                # メインテキストを描画
                text_surface = self.title_font.render(self.title_text, True, self.title_color)
                
                # 影のオフセットを取得
                offx, offy = FONT_EFFECTS.get("shadow_offset", (6, 6))
                offx, offy = int(round(offx)), int(round(offy))
                
                # 影を先に描画
                shadow_x = self.text_x + offx
                shadow_y = self.text_y + offy
                self.screen.blit(shadow_surface, (shadow_x, shadow_y))
                
                # メインテキストを上に描画
                self.screen.blit(text_surface, (self.text_x, self.text_y))
            else:
                # 影効果なしの場合
                text_surface = self.title_font.render(self.title_text, True, self.title_color)
                self.screen.blit(text_surface, (self.text_x, self.text_y))
    
    def handle_input(self, event):
        """
        入力を処理する
        
        Args:
            event: Pygameイベント
            
        Returns:
            bool: キーが押されたかどうか
        """
        if event.type == pygame.KEYDOWN:
            # 任意のキーが押されたら True を返す
            return True
        elif event.type == pygame.MOUSEBUTTONDOWN:
            # マウスクリックでも進める
            return True
        return False
    
    def run(self):
        """
        タイトル画面のメインループ
        
        Returns:
            bool: 正常終了したかどうか
        """
        if self.debug:
            print("タイトル画面を開始")
        
        # BGMを再生開始
        self.play_title_bgm()
        
        clock = pygame.time.Clock()
        running = True
        
        while running:
            # イベント処理
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.stop_title_bgm()  # BGMを停止
                    return False  # ゲーム終了
                
                # キー入力またはマウスクリックでタイトル画面を終了
                if self.handle_input(event):
                    if self.debug:
                        print("タイトル画面を終了")
                    self.stop_title_bgm()  # BGMを停止
                    return True  # メインメニューへ進む
            
            # 更新
            self.update()
            
            # 描画
            self.render()
            pygame.display.flip()
            
            # フレームレート制御
            clock.tick(60)
        
        return False

def show_title_screen(screen, debug=False):
    """
    タイトル画面を表示する関数
    
    Args:
        screen: Pygameスクリーン
        debug: デバッグモード
        
    Returns:
        bool: 正常終了したかどうか
    """
    if not SHOW_TITLE_SCREEN:
        if debug:
            print("タイトル画面はスキップされました（SHOW_TITLE_SCREEN = False）")
        return True
    
    title_screen = TitleScreen(screen, debug)
    return title_screen.run()