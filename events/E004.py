import pygame
import os
import sys
# 現在のディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from event_base import EventBase

class E004(EventBase):
    """E004: つっけんどんな先輩登場"""
    
    def run_event(self, event_id, event_title, heroine_name):
        """E004イベントを実行"""
        print(f"🎬 E004イベント実行: {event_title}")
        
        self.running = True
        current_text = 0
        
        # E004専用イベントテキスト
        event_texts = [
            {"speaker": "システム", "text": "【つっけんどんな先輩登場】"},
            {"speaker": "主人公", "text": "図書館で静かに本を読んでいると..."},
            {"speaker": "舞田沙那子", "text": "...（無言で本を探している）"},
            {"speaker": "主人公", "text": "（あの人は...舞田沙那子先輩？）"},
            {"speaker": "主人公", "text": "あの、舞田先輩..."},
            {"speaker": "舞田沙那子", "text": "...何？"},
            {"speaker": "主人公", "text": "えっと、はじめまして。よろしくお願いします。"},
            {"speaker": "舞田沙那子", "text": "...ふーん。"},
            {"speaker": "主人公", "text": "（うわあ、本当につっけんどんだな...）"},
            {"speaker": "舞田沙那子", "text": "何をじろじろ見てるの？"},
            {"speaker": "主人公", "text": "あ、すみません！何も見てません！"},
            {"speaker": "舞田沙那子", "text": "...変なやつ。"},
            {"speaker": "主人公", "text": "（でも、なんだか気になる先輩だな...）"},
            {"speaker": "システム", "text": "舞田沙那子との初対面イベントが終了しました。"}
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
    """E004イベント実行関数"""
    event = E004()
    return event.run_event(event_id, event_title, heroine_name)