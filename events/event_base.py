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
        
        self.clock = pygame.time.Clock()
        self.running = False
        
    def load_fonts(self):
        """フォントを読み込み"""
        try:
            font_path = os.path.join("fonts", "MPLUSRounded1c-Regular.ttf")
            self.fonts = {
                'large': pygame.font.Font(font_path, 28),
                'medium': pygame.font.Font(font_path, 20),
                'small': pygame.font.Font(font_path, 16)
            }
        except:
            # フォント読み込み失敗時はデフォルトフォントを使用
            self.fonts = {
                'large': pygame.font.Font(None, 28),
                'medium': pygame.font.Font(None, 20),
                'small': pygame.font.Font(None, 16)
            }
    
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