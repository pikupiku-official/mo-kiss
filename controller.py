import pygame
from model import advance_dialogue

def handle_events(game_state):
    """イベント処理を行う"""
    for event in pygame.event.get():
        # バックログ関連のイベント処理
        game_state['backlog_manager'].handle_input(event)
        
        if event.type == pygame.QUIT:
            return False
            
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
                
            elif event.key == pygame.K_b:
                # バックログの開閉（既にhandle_inputで処理されているが、ログ出力のため、要らない）
                if game_state['backlog_manager'].is_showing():
                    print("バックログを開きました（↑↓でスクロール、ESC/Bで閉じる）")
                else:
                    print("バックログを閉じました")
    
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