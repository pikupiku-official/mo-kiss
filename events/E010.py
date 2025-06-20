import pygame
import os
import sys
# 現在のディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from event_base import EventBase

class E010(EventBase):
    """E010: 積極的ルート - デートイベント"""
    
    def run_event(self, event_id, event_title, heroine_name):
        """E010イベントを実行"""
        print(f"🎬 E010イベント実行: 積極的ルート")
        
        self.running = True
        current_text = 0
        
        # E010専用イベントテキスト（積極的ルート）
        event_texts = [
            {"speaker": "システム", "text": "【積極的ルート: デートイベント】"},
            {"speaker": "烏丸神無", "text": "積極的なあなたを見込んで、今度一緒に出かけませんか？"},
            {"speaker": "主人公", "text": "え、本当ですか！？"},
            {"speaker": "烏丸神無", "text": "フッ、面白い反応ね。"},
            {"speaker": "烏丸神無", "text": "でも、嫌いじゃないわ。"},
            {"speaker": "主人公", "text": "ありがとうございます！"},
            {"speaker": "烏丸神無", "text": "じゃあ、今度の休日、街で待ち合わせしましょう。"},
            {"speaker": "システム", "text": "積極的な選択により、特別なデートイベントが解放されました！"},
            {"speaker": "システム", "text": "神無との関係が進展しています。"}
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

def run_event(event_id, event_title, heroine_name):
    """E010イベント実行関数"""
    event = E010()
    return event.run_event(event_id, event_title, heroine_name)
