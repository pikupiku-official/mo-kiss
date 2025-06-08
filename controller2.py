import pygame
from model import advance_dialogue
from config import get_ui_button_positions

def is_point_in_rect(point, rect_pos, rect_size):
    """点が矩形の範囲内にあるかどうかを判定する"""
    x, y = point
    rect_x, rect_y = rect_pos
    rect_width, rect_height = rect_size
    
    return (rect_x <= x <= rect_x + rect_width and 
            rect_y <= y <= rect_y + rect_height)

def setup_text_renderer_settings(game_state):
    """TextRendererの新しい遅延設定を初期化"""
    text_renderer = game_state.get('text_renderer')
    if text_renderer:
        # ScrollManagerとTextRendererの相互参照を設定
        text_renderer.scroll_manager.set_text_renderer(text_renderer)
        
        # デフォルトの遅延設定（必要に応じて調整）
        text_renderer.set_punctuation_delay(500)  # 句読点での遅延: 500ms
        text_renderer.set_paragraph_transition_delay(1000)  # 段落切り替え遅延: 1000ms

def handle_mouse_click(game_state, mouse_pos, screen):
    """マウスクリックの処理"""
    # バックログが開いている時は無効化
    if game_state['backlog_manager'].is_showing():
        return
    
    # テキストが非表示の時は無効化
    if not game_state['show_text']:
        return
    
    # UI画像とボタン位置を取得
    images = game_state.get('images', {})
    ui_images = images.get('ui', {})
    button_positions = get_ui_button_positions(screen)
    
    # Autoボタンのクリック判定
    if 'auto' in ui_images and ui_images['auto'] and 'auto' in button_positions:
        auto_btn = ui_images['auto']
        auto_pos = button_positions['auto']
        auto_size = (auto_btn.get_width(), auto_btn.get_height())
        
        if is_point_in_rect(mouse_pos, auto_pos, auto_size):
            auto_mode = game_state['text_renderer'].toggle_auto_mode()
            print(f"自動モード: {'ON' if auto_mode else 'OFF'}")
            return
    
    # Skipボタンのクリック判定
    if 'skip' in ui_images and ui_images['skip'] and 'skip' in button_positions:
        skip_btn = ui_images['skip']
        skip_pos = button_positions['skip']
        skip_size = (skip_btn.get_width(), skip_btn.get_height())
        
        if is_point_in_rect(mouse_pos, skip_pos, skip_size):
            if game_state['text_renderer'].is_displaying():
                game_state['text_renderer'].skip_text()
                print("テキスト表示をスキップしました")
            return

def handle_events(game_state, screen):
    """イベント処理を行う"""
    for event in pygame.event.get():
        # バックログ関連のイベント処理
        game_state['backlog_manager'].handle_input(event)
        
        if event.type == pygame.QUIT:
            return False
            
        elif event.type == pygame.MOUSEBUTTONDOWN:
            # マウスクリックの処理
            if event.button == 1:  # 左クリック
                mouse_pos = pygame.mouse.get_pos()
                handle_mouse_click(game_state, mouse_pos, screen)
            
        elif event.type == pygame.KEYDOWN:
            # ESCキーの処理：バックログが開いている場合は閉じるだけ
            if event.key == pygame.K_ESCAPE:
                if game_state['backlog_manager'].is_showing():
                    game_state['backlog_manager'].toggle_backlog()
                    print("バックログを閉じました")
                else:
                    return False
                    
            elif event.key == pygame.K_t:
                # バックログが開いている時は無効化
                if not game_state['backlog_manager'].is_showing():
                    game_state['show_text'] = not game_state['show_text']
                    print(f"テキストを{'表示' if game_state['show_text'] else '非表示に'}しました")

            elif event.key == pygame.K_a:
                if not game_state['backlog_manager'].is_showing():
                    auto_mode = game_state['text_renderer'].toggle_auto_mode()
                    print(f"自動モード: {'ON' if auto_mode else 'OFF'}")
                    
            elif event.key == pygame.K_SPACE and game_state['show_text']:
                # バックログが開いている時は無効化
                if not game_state['backlog_manager'].is_showing():
                    if game_state['text_renderer'].is_displaying():
                        game_state['text_renderer'].skip_text()
                        print("テキスト表示をスキップしました")
                        
            elif event.key == pygame.K_RETURN and game_state['show_text']:
                handle_enter_key(game_state)
    
    return True

def handle_enter_key(game_state):
    """Enterキーが押されたときの処理"""
    # バックログが開いている時は無効化
    if game_state['backlog_manager'].is_showing():
        return
        
    text_renderer = game_state['text_renderer']
    
    if text_renderer.is_displaying():
        # テキスト表示中ならスキップ
        text_renderer.skip_text()
        print("テキスト表示をスキップしました")
    else:
        # テキスト表示が完了していたら次の段落へ
        advance_to_next_dialogue(game_state)

def advance_to_next_dialogue(game_state):
    """次の対話に進む"""
    if game_state['current_paragraph'] < len(game_state['dialogue_data']) - 1:
        # model.pyのadvance_dialogue関数を使用
        success = advance_dialogue(game_state)
        if success:
            print(f"段落 {game_state['current_paragraph'] + 1}/{len(game_state['dialogue_data'])} に進みました")
            return True
        else:
            # 最後の段落に到達した場合の処理
            if not hasattr(game_state, 'last_dialogue_logged') or not game_state['last_dialogue_logged']:
                print("最後の段落です")
                game_state['last_dialogue_logged'] = True
            return False
    else:
        # 最後の段落に到達した場合の処理
        if not hasattr(game_state, 'last_dialogue_logged') or not game_state['last_dialogue_logged']:
            print("最後の段落です")
            game_state['last_dialogue_logged'] = True
        return False

def update_game(game_state):
    """ゲーム状態の更新"""
    # TextRendererの初期設定が完了していない場合は実行
    if not hasattr(game_state, 'text_renderer_initialized') or not game_state['text_renderer_initialized']:
        setup_text_renderer_settings(game_state)
        game_state['text_renderer_initialized'] = True
    
    # テキスト表示の更新
    game_state['text_renderer'].update()

    # 自動進行の処理
    if (game_state['text_renderer'].is_ready_for_auto_advance() and not game_state['backlog_manager'].is_showing()):
        # 自動的に次の対話に進む
        success = advance_to_next_dialogue(game_state)
        # 自動進行タイマーをリセット
        game_state['text_renderer'].reset_auto_timer()

        # 最後の段落に到達した場合は自動モードを無効化
        if not success:
            game_state['text_renderer'].auto_mode = False
            if game_state['text_renderer'].debug:
                print("最後の段落に到達したため自動モードを無効化しました")
    
    # 現在の会話データを取得
    if game_state['dialogue_data'] and game_state['current_paragraph'] < len(game_state['dialogue_data']):
        current_dialogue = game_state['dialogue_data'][game_state['current_paragraph']]
        
        # データの長さをチェック
        if len(current_dialogue) > 7:
            bgm_name = current_dialogue[6]
            bgm_volume = current_dialogue[7]
            bgm_loop = current_dialogue[8] if len(current_dialogue) > 8 else True
            
            # BGMの変更を確認（有効なBGMファイル名のみ）
            if (bgm_name and 
                game_state['bgm_manager'].is_valid_bgm_filename(bgm_name) and
                bgm_name != game_state['bgm_manager'].current_bgm):
                success = game_state['bgm_manager'].play_bgm(bgm_name, bgm_volume)
                if success and not bgm_loop:
                    game_state['bgm_manager'].stop_bgm()  # ループしない場合は停止

# 新しい遅延設定用のヘルパー関数
def configure_text_delays(game_state, punctuation_delay=None, paragraph_transition_delay=None):
    """テキスト表示の遅延設定を変更する"""
    text_renderer = game_state.get('text_renderer')
    if not text_renderer:
        return
    
    if punctuation_delay is not None:
        text_renderer.set_punctuation_delay(punctuation_delay)
    
    if paragraph_transition_delay is not None:
        text_renderer.set_paragraph_transition_delay(paragraph_transition_delay)

def get_current_text_delays(game_state):
    """現在の遅延設定を取得する"""
    text_renderer = game_state.get('text_renderer')
    if not text_renderer:
        return None
    
    return {
        'char_delay': text_renderer.char_delay,
        'punctuation_delay': text_renderer.punctuation_delay,
        'paragraph_transition_delay': text_renderer.paragraph_transition_delay
    }