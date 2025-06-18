import pygame
import os
import sys
# 現在のディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from event_base import EventBase

class E002(EventBase):
    """E002: 憧れの先輩を発見"""
    
    def run_event(self, event_id, event_title, heroine_name):
        """E002イベントを実行"""
        print(f"🎬 E002イベント実行: {event_title}")
        
        self.running = True
        current_text = 0
        
        # E002専用イベントテキスト
        event_texts = [
            {"speaker": "システム", "text": "【憧れの先輩を発見】"},
            {"speaker": "主人公", "text": "図書館で勉強でもしようかな..."},
            {"speaker": "主人公", "text": "あ、あの人は...！"},
            {"speaker": "桔梗美鈴", "text": "（静かに本を読んでいる）"},
            {"speaker": "主人公", "text": "（桔梗美鈴先輩だ！前から憧れていたんだよなあ）"},
            {"speaker": "主人公", "text": "（話しかけてみようかな...？）"},
            {"speaker": "桔梗美鈴", "text": "あら？あなたは..."},
            {"speaker": "主人公", "text": "あ、はい！桔梗先輩、いつもお疲れ様です！"},
            {"speaker": "桔梗美鈴", "text": "丁寧にありがとう。図書館に来るのね。"},
            {"speaker": "主人公", "text": "はい、勉強をしようと思って。"},
            {"speaker": "桔梗美鈴", "text": "真面目なのね。良いことよ。"},
            {"speaker": "主人公", "text": "（優しい先輩だなあ...）"},
            {"speaker": "システム", "text": "桔梗美鈴との初対面イベントが終了しました。"}
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
    """E002イベント実行関数"""
    event = E002()
    return event.run_event(event_id, event_title, heroine_name)