import pygame
import os
import sys
# 現在のディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from event_base import EventBase

class E021(EventBase):
    """E021: クラスのムードメーカー"""
    
    def run_event(self, event_id, event_title, heroine_name):
        """E021イベントを実行"""
        print(f"🎬 E021イベント実行: {event_title}")
        
        self.running = True
        current_text = 0
        
        # E021専用イベントテキスト
        event_texts = [
            {"speaker": "システム", "text": "【クラスのムードメーカー】"},
            {"speaker": "愛沼桃子", "text": "おはようございます〜♪"},
            {"speaker": "主人公", "text": "おはよう、愛沼さん。今日も元気だね。"},
            {"speaker": "愛沼桃子", "text": "えへへ、いつも元気が取り柄なんです♪"},
            {"speaker": "主人公", "text": "クラスの雰囲気が明るくなるよ。"},
            {"speaker": "愛沼桃子", "text": "そんな〜、照れちゃいます！"},
            {"speaker": "主人公", "text": "バドミントン部の調子はどう？"},
            {"speaker": "愛沼桃子", "text": "みんなと楽しく練習してます〜"},
            {"speaker": "愛沼桃子", "text": "今度見に来てくださいね♪"},
            {"speaker": "主人公", "text": "機会があったら、ぜひ。"},
            {"speaker": "愛沼桃子", "text": "約束ですよ〜♪"},
            {"speaker": "システム", "text": "愛沼桃子とのイベントが終了しました。"}
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
    """E021イベント実行関数"""
    event = E021()
    return event.run_event(event_id, event_title, heroine_name)