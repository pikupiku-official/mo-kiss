import pygame
import os
import sys
# 現在のディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from event_base import EventBase

class E050(EventBase):
    """E050: イベント050"""
    
    def run_event(self, event_id, event_title, heroine_name):
        """E050イベントを実行"""
        print(f"🎬 E050イベント実行: {event_title}")
        
        self.running = True
        current_text = 0
        
        # E050専用イベントテキスト
        event_texts = [
            {"speaker": "システム", "text": f"【{event_title}】"},
            {"speaker": heroine_name, "text": f"こんにちは。{heroine_name}です。"},
            {"speaker": "主人公", "text": f"{heroine_name}さん、お疲れ様です。"},
            {"speaker": heroine_name, "text": "今日はいい天気ですね。"},
            {"speaker": "主人公", "text": "そうですね。とても過ごしやすいです。"},
            {"speaker": heroine_name, "text": "何か予定はありますか？"},
            {"speaker": "主人公", "text": "特にありませんが、時間を過ごしています。"},
            {"speaker": heroine_name, "text": "そうですか。では、また今度お話ししましょう。"},
            {"speaker": "主人公", "text": "はい、ぜひ。また会いましょう。"},
            {"speaker": "システム", "text": f"{heroine_name}とのイベント050が終了しました。"}
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
    """E050イベント実行関数"""
    event = E050()
    return event.run_event(event_id, event_title, heroine_name)
