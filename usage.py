import pygame
from config import *
from text_renderer import TextRenderer
from backlog_manager import BacklogManager

# 使用例：これはゲームの初期化部分で呼び出されるコードの例です
def initialize_text_system(screen):
    # TextRendererとBacklogManagerを初期化
    text_renderer = TextRenderer(screen)
    backlog_manager = BacklogManager(screen, text_renderer.fonts)
    
    # TextRendererにBacklogManagerを設定
    text_renderer.set_backlog_manager(backlog_manager)
    
    return text_renderer, backlog_manager

# ゲームの更新ループでの使用例
def update(text_renderer, backlog_manager):
    # テキスト表示の更新
    text_renderer.update()

# イベント処理での使用例
def handle_event(event, text_renderer, backlog_manager):
    # バックログ関連の入力処理
    backlog_manager.handle_input(event)
    
    # その他のテキスト関連の入力処理
    if event.type == pygame.KEYDOWN:
        # スペースキーでテキストスキップ
        if event.key == pygame.K_SPACE and text_renderer.is_displaying():
            text_renderer.skip_text()

# 描画ループでの使用例
def render(text_renderer, backlog_manager):
    # バックログの描画
    backlog_manager.render()
    
    # テキストの描画（バックログが表示されていなければ）
    text_renderer.render()

# 新しいダイアログを設定
def set_new_dialogue(text_renderer, character_name, text):
    text_renderer.set_dialogue(text, character_name)