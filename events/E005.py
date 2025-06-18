import pygame
import os
import sys
# 現在のディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from event_base import EventBase

class E005(EventBase):
    """E005: 隣の席の儚げな同級生"""
    
    def run_event(self, event_id, event_title, heroine_name):
        """E005イベントを実行"""
        print(f"🎬 E005イベント実行: {event_title}")
        
        self.running = True
        current_text = 0
        
        # E005専用イベントテキスト
        event_texts = [
            {"speaker": "システム", "text": "【隣の席の儚げな同級生】"},
            {"speaker": "主人公", "text": "教室に入ると、隣の席に誰かが座っている..."},
            {"speaker": "宮月深依里", "text": "...（静かに窓の外を眺めている）"},
            {"speaker": "主人公", "text": "あの...隣に座らせてもらいます。"},
            {"speaker": "宮月深依里", "text": "...はい。"},
            {"speaker": "主人公", "text": "僕、転校生なんです。よろしくお願いします。"},
            {"speaker": "宮月深依里", "text": "...宮月深依里です。よろしく。"},
            {"speaker": "主人公", "text": "（すごく静かで、儚げな感じの子だな...）"},
            {"speaker": "宮月深依里", "text": "...あの、お名前は？"},
            {"speaker": "主人公", "text": "あ、僕ですか？名前は..."},
            {"speaker": "宮月深依里", "text": "...覚えました。"},
            {"speaker": "主人公", "text": "（なんだか不思議な魅力のある人だな）"},
            {"speaker": "宮月深依里", "text": "...また、明日。"},
            {"speaker": "システム", "text": "宮月深依里との初対面イベントが終了しました。"}
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
    """E005イベント実行関数"""
    event = E005()
    return event.run_event(event_id, event_title, heroine_name)