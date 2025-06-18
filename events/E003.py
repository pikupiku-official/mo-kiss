import pygame
import os
import sys
# 現在のディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from event_base import EventBase

class E003(EventBase):
    """E003: ふわふわ少女の夜の散歩"""
    
    def run_event(self, event_id, event_title, heroine_name):
        """E003イベントを実行"""
        print(f"🎬 E003イベント実行: {event_title}")
        
        self.running = True
        current_text = 0
        
        # E003専用イベントテキスト
        event_texts = [
            {"speaker": "システム", "text": "【ふわふわ少女の夜の散歩】"},
            {"speaker": "主人公", "text": "夜の商店街を歩いていると..."},
            {"speaker": "愛沼桃子", "text": "あら？こんな時間にお散歩ですか？"},
            {"speaker": "主人公", "text": "あ、愛沼さん！こんばんは。"},
            {"speaker": "愛沼桃子", "text": "こんばんは〜♪私もお散歩中なんです。"},
            {"speaker": "主人公", "text": "夜のお散歩って珍しいですね。"},
            {"speaker": "愛沼桃子", "text": "えへへ、夜は静かで好きなんです。"},
            {"speaker": "愛沼桃子", "text": "昼間はみんなでワイワイしてるけど..."},
            {"speaker": "愛沼桃子", "text": "たまには一人の時間も大切ですよね。"},
            {"speaker": "主人公", "text": "そうですね。愛沼さんの意外な一面を見た気がします。"},
            {"speaker": "愛沼桃子", "text": "ふふ、秘密ですよ〜♪"},
            {"speaker": "主人公", "text": "（普段のふわふわした感じとは違う、落ち着いた愛沼さんも素敵だな）"},
            {"speaker": "システム", "text": "愛沼桃子との夜の散歩イベントが終了しました。"}
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
    """E003イベント実行関数"""
    event = E003()
    return event.run_event(event_id, event_title, heroine_name)