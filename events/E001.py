import pygame
import os
import sys
# 現在のディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from event_base import EventBase

class E001(EventBase):
    """E001: 孤高のギャルとの初対面"""
    
    def run_event(self, event_id, event_title, heroine_name):
        """E001イベントを実行"""
        print(f"🎬 E001イベント実行: {event_title}")
        
        self.running = True
        current_text = 0
        
        # E001専用イベントテキスト
        event_texts = [
            {"speaker": "システム", "text": "【孤高のギャルとの初対面】"},
            {"speaker": "主人公", "text": "体育館に来てみたけれど..."},
            {"speaker": "烏丸神無", "text": "あ？なんか用？"},
            {"speaker": "主人公", "text": "（えっと、この人が烏丸神無さんかな？）"},
            {"speaker": "烏丸神無", "text": "じろじろ見んなよ、気持ち悪い。"},
            {"speaker": "主人公", "text": "あ、すみません！初めまして、よろしくお願いします。"},
            {"speaker": "烏丸神無", "text": "...ふーん。まあ、よろしく。"},
            {"speaker": "主人公", "text": "（思ったより話しかけやすい人かも？）"},
            {"speaker": "烏丸神無", "text": "でも、あたしに話しかけるのは珍しいね。"},
            {"speaker": "烏丸神無", "text": "みんな避けて通るのに。"},
            {"speaker": "システム", "text": "烏丸神無との初対面イベントが終了しました。"},
            {"speaker": "システム", "text": "Escキーでマップに戻ります。"}
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
    """E001イベント実行関数"""
    event = E001()
    return event.run_event(event_id, event_title, heroine_name)