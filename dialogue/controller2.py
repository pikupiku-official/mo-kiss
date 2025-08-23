import pygame
from .model import advance_dialogue
from config import get_ui_button_positions, DEBUG, FONT_EFFECTS
from .character_manager import update_character_animations
from .background_manager import update_background_animation
from .fade_manager import update_fade_animation

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
    print(f"[CLICK] マウスクリック処理開始: pos={mouse_pos}")
    
    # バックログが開いている時は無効化
    if game_state['backlog_manager'].is_showing_backlog():
        print(f"[CLICK] バックログが開いているためクリック無効")
        return
    
    # テキストが非表示の時は無効化
    if not game_state['show_text']:
        print(f"[CLICK] テキストが非表示のためクリック無効")
        return
    
    # 選択肢が表示中の場合、選択肢をクリック処理
    choice_renderer = game_state['choice_renderer']
    if choice_renderer.is_choice_showing():
        print(f"[CLICK] 選択肢表示中、クリック処理開始")
        selected_choice = choice_renderer.handle_mouse_click(mouse_pos)
        print(f"[CLICK] 選択肢クリック結果: {selected_choice}")
        if selected_choice >= 0:
            # 選択された選択肢をバックログに追加
            selected_text = choice_renderer.get_last_selected_text()
            if selected_text and game_state['backlog_manager']:
                game_state['backlog_manager'].add_entry("橘純一", f"〇{selected_text}")
                print(f"[BACKLOG] 選択肢をバックログに追加: {selected_text}")
            
            # 選択肢を非表示にして次に進む
            print(f"[CLICK] 選択肢を非表示にして次に進む")
            choice_renderer.hide_choices()
            advance_to_next_dialogue(game_state)
            return
        else:
            print(f"[CLICK] 選択肢外をクリック")
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
            skip_mode = game_state['text_renderer'].toggle_skip_mode()
            print(f"スキップモード: {'ON' if skip_mode else 'OFF'}")
            return
    
    # UI以外の場所をクリックした場合、Enterキーと同じ処理を実行
    print(f"[CLICK] 通常クリック処理（Enterキーと同様）")
    handle_enter_key(game_state)

def handle_events(game_state, screen):
    """イベント処理を行う"""
    for event in pygame.event.get():
        # バックログ関連のイベント処理
        game_state['backlog_manager'].handle_input(event)
        
        if event.type == pygame.QUIT:
            return False
            
        elif event.type == pygame.MOUSEMOTION:
            # マウス移動の処理（選択肢のハイライト）
            mouse_pos = pygame.mouse.get_pos()
            game_state['choice_renderer'].handle_mouse_motion(mouse_pos)
            
        elif event.type == pygame.MOUSEBUTTONDOWN:
            # マウスクリックの処理
            if event.button == 1:  # 左クリック
                mouse_pos = pygame.mouse.get_pos()
                handle_mouse_click(game_state, mouse_pos, screen)
            
        elif event.type == pygame.KEYDOWN:
            # ESCキーの処理：バックログが開いている場合は閉じるだけ
            if event.key == pygame.K_ESCAPE:
                if game_state['backlog_manager'].is_showing_backlog():
                    game_state['backlog_manager'].toggle_backlog()
                    print("バックログを閉じました")
                else:
                    return False
                    
            elif event.key == pygame.K_t:
                # バックログが開いている時は無効化
                if not game_state['backlog_manager'].is_showing_backlog():
                    game_state['show_text'] = not game_state['show_text']
                    print(f"テキストを{'表示' if game_state['show_text'] else '非表示に'}しました")

            elif event.key == pygame.K_a:
                if not game_state['backlog_manager'].is_showing_backlog():
                    auto_mode = game_state['text_renderer'].toggle_auto_mode()
                    print(f"自動モード: {'ON' if auto_mode else 'OFF'}")
                    
            elif event.key == pygame.K_SPACE and game_state['show_text']:
                # バックログが開いている時は無効化
                if not game_state['backlog_manager'].is_showing_backlog():
                    skip_mode = game_state['text_renderer'].toggle_skip_mode()
                    print(f"スキップモード: {'ON' if skip_mode else 'OFF'}")
            
            # フォント効果テスト用キーボードショートカット
            elif event.key == pygame.K_F1:
                # F1: 影効果のオン/オフ
                FONT_EFFECTS["enable_shadow"] = not FONT_EFFECTS.get("enable_shadow", False)
                shadow_alpha = FONT_EFFECTS.get('shadow_alpha', 128)
                print(f"🎨 影効果: {'ON (透明度' + str(shadow_alpha) + ')' if FONT_EFFECTS['enable_shadow'] else 'OFF'}")
                
            elif event.key == pygame.K_F2:
                # F2: ピクセル化効果のオン/オフ
                FONT_EFFECTS["enable_pixelated"] = not FONT_EFFECTS.get("enable_pixelated", False)
                print(f"🔲 90年代風ピクセル化効果: {'ON (アンチエイリアス無効)' if FONT_EFFECTS['enable_pixelated'] else 'OFF'}")
                
            elif event.key == pygame.K_F3:
                # F3: 横引き延ばし効果のオン/オフ
                FONT_EFFECTS["enable_stretched"] = not FONT_EFFECTS.get("enable_stretched", False)
                stretch_factor = FONT_EFFECTS.get('stretch_factor', 1.25)
                print(f"↔️ 横引き延ばし効果: {'ON (x' + str(stretch_factor) + ')' if FONT_EFFECTS['enable_stretched'] else 'OFF'}")
                
            elif event.key == pygame.K_F4:
                # F4: 全フォント効果のオン/オフ
                all_on = all([FONT_EFFECTS.get("enable_shadow", False), 
                             FONT_EFFECTS.get("enable_pixelated", False), 
                             FONT_EFFECTS.get("enable_stretched", False)])
                new_state = not all_on
                FONT_EFFECTS["enable_shadow"] = new_state
                FONT_EFFECTS["enable_pixelated"] = new_state
                FONT_EFFECTS["enable_stretched"] = new_state
                print(f"✨ 全90年代風フォント効果: {'ON' if new_state else 'OFF'}")
                
            elif event.key == pygame.K_F5:
                # F5: フォント効果の現在の状態を表示
                print("=== 🕹️  90年代風フォント効果状態 ===")
                print(f"🎨 影効果: {'ON' if FONT_EFFECTS.get('enable_shadow', False) else 'OFF'} (透明度: {FONT_EFFECTS.get('shadow_alpha', 128)})")
                pixelate_factor = FONT_EFFECTS.get('pixelate_factor', 4)
                print(f"🔲 ピクセル化: {'ON' if FONT_EFFECTS.get('enable_pixelated', False) else 'OFF'} (1/{pixelate_factor} → {pixelate_factor}倍拡大, アンチエイリアス無効)")
                stretch_factor = FONT_EFFECTS.get('stretch_factor', 1.25)
                print(f"↔️  横引き延ばし: {'ON' if FONT_EFFECTS.get('enable_stretched', False) else 'OFF'} (x{stretch_factor})")
                print("=====================================")
                print("🎮 操作方法: F1(影), F2(ピクセル化), F3(引き延ばし), F4(全効果), F5(状態表示)")
                        
            elif event.key == pygame.K_RETURN and game_state['show_text']:
                handle_enter_key(game_state)
    
    return True

def handle_enter_key(game_state):
    """Enterキーが押されたときの処理"""
    print(f"[ENTER] Enterキー処理開始")
    
    # バックログが開いている時は無効化
    if game_state['backlog_manager'].is_showing_backlog():
        print(f"[ENTER] バックログが開いているため無効")
        return
    
    # 選択肢が表示中の時は選択肢をスキップして次に進む
    if game_state['choice_renderer'].is_choice_showing():
        print(f"[ENTER] 選択肢をスキップして次に進む")
        game_state['choice_renderer'].hide_choices()
        advance_to_next_dialogue(game_state)
        return
        
    text_renderer = game_state['text_renderer']
    
    if text_renderer.is_displaying():
        # テキスト表示中ならスキップ
        print(f"[ENTER] テキスト表示をスキップ")
        text_renderer.skip_text()
    else:
        # テキスト表示が完了していたら次の段落へ
        print(f"[ENTER] 次の段落に進む")
        advance_to_next_dialogue(game_state)

def advance_to_next_dialogue(game_state):
    """次の対話に進む"""
    if DEBUG:
        print(f"[ADVANCE] advance_to_next_dialogue呼び出し: current={game_state['current_paragraph']}, total={len(game_state['dialogue_data'])}")
    
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
    
    # テキスト表示の更新（選択肢表示中は停止）
    if not game_state['choice_renderer'].is_choice_showing():
        game_state['text_renderer'].update()
    
    # キャラクターアニメーションの更新
    update_character_animations(game_state)
    
    # 背景アニメーションの更新
    update_background_animation(game_state)
    
    # フェードアニメーションの更新
    update_fade_animation(game_state)

    # 自動進行の処理（選択肢表示中は無効化）
    if (game_state['text_renderer'].is_ready_for_auto_advance() and 
        not game_state['backlog_manager'].is_showing_backlog() and
        not game_state['choice_renderer'].is_choice_showing()):
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
        if len(current_dialogue) > 8:
            bgm_name = current_dialogue[7]
            bgm_volume = current_dialogue[8]
            bgm_loop = current_dialogue[9] if len(current_dialogue) > 9 else True
            
            # BGMの変更を確認（拡張子自動補完対応）
            if bgm_name:
                bgm_manager = game_state['bgm_manager']
                actual_bgm_filename = bgm_manager.get_bgm_for_scene(bgm_name)
                
                if (actual_bgm_filename and 
                    actual_bgm_filename != bgm_manager.current_bgm):
                    success = bgm_manager.play_bgm(actual_bgm_filename, bgm_volume, bgm_loop)

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