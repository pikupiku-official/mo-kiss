import pygame
import os
import sys
# 現在のディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from event_base import EventBase

class E006(EventBase):
    """E006: 母性ある後輩との出会い"""
    
    def run_event(self, event_id, event_title, heroine_name):
        """E006イベントを実行"""
        print(f"🎬 E006イベント実行: {event_title}")
        
        self.running = True
        current_text = 0
        
        # E006専用イベントテキスト
        event_texts = [
            {"speaker": "システム", "text": "【母性ある後輩との出会い】"},
            {"speaker": "主人公", "text": "夜の駅前を歩いていると..."},
            {"speaker": "伊織紅", "text": "あら、先輩じゃないですか。"},
            {"speaker": "主人公", "text": "えっ？僕のこと知ってるの？"},
            {"speaker": "伊織紅", "text": "ええ、転校生として有名ですから。"},
            {"speaker": "伊織紅", "text": "私、一年生の伊織紅です。"},
            {"speaker": "主人公", "text": "伊織さんか。よろしく。"},
            {"speaker": "伊織紅", "text": "こんな時間に一人で歩いてて大丈夫ですか？"},
            {"speaker": "主人公", "text": "大丈夫って...僕の方が年上だよ？"},
            {"speaker": "伊織紅", "text": "年上でも心配になるものは心配なんです。"},
            {"speaker": "主人公", "text": "（なんだか、すごく大人っぽい後輩だな...）"},
            {"speaker": "伊織紅", "text": "気をつけて帰ってくださいね。"},
            {"speaker": "主人公", "text": "（母性を感じる...不思議な後輩だ）"},
            {"speaker": "システム", "text": "伊織紅との初対面イベントが終了しました。"}
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
    """E006イベント実行関数"""
    event = E006()
    return event.run_event(event_id, event_title, heroine_name)