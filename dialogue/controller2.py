import pygame
from .model import advance_dialogue
from core.config import get_ui_button_positions, DEBUG, FONT_EFFECTS
from .character_manager import update_character_animations
from .background_manager import update_background_animation
from .fade_manager import update_fade_animation

def _to_virtual_mouse_pos(mouse_pos, screen, game_state):
    """Translate screen mouse coords to virtual coords when needed."""
    if not screen or not game_state or 'screen' not in game_state:
        return mouse_pos

    if screen == game_state['screen']:
        return mouse_pos

    from core.config import CONTENT_WIDTH, CONTENT_HEIGHT, VIRTUAL_WIDTH, VIRTUAL_HEIGHT, DISPLAY_WIDTH, DISPLAY_HEIGHT

    x, y = mouse_pos
    # DialogueSubsystem.on_enter() が OFFSET_X/Y を 0 にリセットするため
    # 常に DISPLAY サイズから実オフセットを再計算する（option_overlay と同じ対処）
    real_offset_x = (DISPLAY_WIDTH  - CONTENT_WIDTH)  // 2
    real_offset_y = (DISPLAY_HEIGHT - CONTENT_HEIGHT) // 2
    offset_x = game_state.get('_original_offset_x', real_offset_x)
    offset_y = game_state.get('_original_offset_y', real_offset_y)
    x -= offset_x
    y -= offset_y

    if CONTENT_WIDTH and CONTENT_HEIGHT:
        x = x * VIRTUAL_WIDTH / CONTENT_WIDTH
        y = y * VIRTUAL_HEIGHT / CONTENT_HEIGHT

    return (int(x), int(y))

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
    if game_state.get("use_ir"):
        fast_until = game_state.get("ir_fast_forward_until")
        if fast_until is not None and pygame.time.get_ticks() < fast_until:
            return
    # バックログが開いている時は無効化
    if game_state['backlog_manager'].is_showing_backlog():
        return

    # テキストが非表示の時は無効化
    if not game_state['show_text']:
        return

    # 選択肢が表示中の場合、選択肢をクリック処理
    choice_renderer = game_state['choice_renderer']
    if choice_renderer.is_choice_showing():
        selected_choice = choice_renderer.handle_mouse_click(mouse_pos)
        if selected_choice >= 0:
            # 選択された選択肢をバックログに追加
            selected_text = choice_renderer.get_last_selected_text()
            if selected_text and game_state['backlog_manager']:
                game_state['backlog_manager'].add_entry("橘純一", f"〇{selected_text}")
                print(f"[CHOICE] 選択: {selected_text}")

            # 選択肢履歴に記録（次のテキスト処理前に実行）
            if 'dialogue_loader' in game_state and selected_text:
                dialogue_loader = game_state['dialogue_loader']
                choice_number = dialogue_loader.record_choice(selected_choice, selected_text)

                # name_managerに即座に反映（テキスト置換用）
                from .name_manager import get_name_manager
                name_manager = get_name_manager()
                name_manager.set_dialogue_loader(dialogue_loader)

            # 選択肢を非表示にして次に進む
            choice_renderer.hide_choices()
            advance_to_next_dialogue(game_state)
            return
        else:
            return
    
    # UI画像とボタン位置を取得
    images = game_state.get('images', {})
    ui_images = images.get('ui', {})
    button_positions = get_ui_button_positions(screen)
    
    # Autoボタンのクリック判定
    if 'auto' in ui_images and ui_images['auto'] and 'auto' in button_positions:
        auto_btn = ui_images['auto']
        auto_pos = button_positions['auto']
        from core.config import UI_BUTTON_SCALE
        auto_size = (int(auto_btn.get_width() * UI_BUTTON_SCALE), int(auto_btn.get_height() * UI_BUTTON_SCALE))
        
        if is_point_in_rect(mouse_pos, auto_pos, auto_size):
            auto_mode = game_state['text_renderer'].toggle_auto_mode()
            print(f"自動モード: {'ON' if auto_mode else 'OFF'}")
            return
    
    # Skipボタンのクリック判定
    if 'skip' in ui_images and ui_images['skip'] and 'skip' in button_positions:
        skip_btn = ui_images['skip']
        skip_pos = button_positions['skip']
        from core.config import UI_BUTTON_SCALE
        skip_size = (int(skip_btn.get_width() * UI_BUTTON_SCALE), int(skip_btn.get_height() * UI_BUTTON_SCALE))
        
        if is_point_in_rect(mouse_pos, skip_pos, skip_size):
            skip_mode = game_state['text_renderer'].toggle_skip_mode()
            print(f"スキップモード: {'ON' if skip_mode else 'OFF'}")
            return
    
    # 選択肢が表示中でない場合のみ、UI以外の場所をクリックした場合にEnterキーと同じ処理を実行
    if not game_state['choice_renderer'].is_choice_showing():
        print("[CLICK] 通常クリック処理（Enterキーと同様）")
        handle_enter_key(game_state)
    else:
        print("[CLICK] 選択肢表示中のため通常クリック処理は無効")

def handle_events(game_state, screen):
    """イベント処理を行う"""
    # KSファイル終了チェック
    if game_state.get('ks_finished', False):
        print("[EVENTS] KSファイル終了フラグ検知")
        return False  # KSファイル終了を通知
    
    for event in pygame.event.get():
        # バックログ関連のイベント処理
        game_state['backlog_manager'].handle_input(event)
        
        if event.type == pygame.QUIT:
            return False
            
        elif event.type == pygame.MOUSEMOTION:
            # マウス移動の処理（選択肢のハイライト）
            # event.posを使用（event_editorから座標変換されたイベントに対応）
            mouse_pos = _to_virtual_mouse_pos(event.pos, screen, game_state)
            game_state['choice_renderer'].handle_mouse_motion(mouse_pos)

        elif event.type == pygame.MOUSEBUTTONDOWN:
            # マウスクリックの処理
            if event.button == 1:  # 左クリック
                # event.posを使用（event_editorから座標変換されたイベントに対応）
                mouse_pos = _to_virtual_mouse_pos(event.pos, screen, game_state)
                handle_mouse_click(game_state, mouse_pos, screen)
            
        elif event.type == pygame.KEYDOWN:
            # ESC は dialogue_subsystem 側で処理する（OPTION オーバーレイ）のでスキップ
            if event.key == pygame.K_ESCAPE:
                pass

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
                pixelate_factor = FONT_EFFECTS.get('pixelate_factor', 2)
                print(f"🔲 ピクセル化効果: {'ON' if FONT_EFFECTS['enable_pixelated'] else 'OFF'} (1/{pixelate_factor}→{pixelate_factor}倍, アンチエイリアス付き)")
                
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
                shadow_offset = FONT_EFFECTS.get('shadow_offset', (6, 6))
                print(f"🎨 影効果: {'ON' if FONT_EFFECTS.get('enable_shadow', False) else 'OFF'} (オフセット: {shadow_offset}px, 完全不透明)")
                pixelate_factor = FONT_EFFECTS.get('pixelate_factor', 2)
                print(f"🔲 ピクセル化: {'ON' if FONT_EFFECTS.get('enable_pixelated', False) else 'OFF'} (1/{pixelate_factor}→{pixelate_factor}倍拡大, アンチエイリアス付き)")
                stretch_factor = FONT_EFFECTS.get('stretch_factor', 1.25)
                print(f"↔️  横引き延ばし: {'ON' if FONT_EFFECTS.get('enable_stretched', False) else 'OFF'} (x{stretch_factor})")
                print("=====================================")
                print("🎮 操作方法: F1(影), F2(ピクセル化), F3(引き延ばし), F4(全効果), F5(状態表示)")
                        
            elif event.key == pygame.K_RETURN and game_state['show_text']:
                handle_enter_key(game_state)
    
    return True

def _flush_scroll_line_to_backlog(game_state):
    """スクロールモード中の現在行をバックログに追加（advance直前に呼ぶ）"""
    text_renderer = game_state.get('text_renderer')
    backlog_mgr = game_state.get('backlog_manager')
    if not (text_renderer and backlog_mgr):
        return
    if not text_renderer.scroll_manager.is_scroll_mode():
        return
    if not text_renderer.current_text:
        return
    backlog_mgr.add_entry(
        text_renderer.current_character_name or None,
        text_renderer.current_text,
        getattr(text_renderer, 'current_force_female', False),
    )

def handle_enter_key(game_state):
    """Enterキーが押されたときの処理"""
    print("[ENTER] Enterキー処理開始")
    if game_state.get("use_ir"):
        fast_until = game_state.get("ir_fast_forward_until")
        if fast_until is not None and pygame.time.get_ticks() < fast_until:
            return
    
    # バックログが開いている時は無効化
    if game_state['backlog_manager'].is_showing_backlog():
        print("[ENTER] バックログが開いているため無効")
        return
    
    # 選択肢が表示中の時はEnterキーを無効にする
    if game_state['choice_renderer'].is_choice_showing():
        print("[ENTER] 選択肢表示中のため無効（マウスクリックで選択してください）")
        return
        
    text_renderer = game_state['text_renderer']
    
    if text_renderer.is_displaying():
        # テキスト表示中ならスキップ
        print("[ENTER] テキスト表示をスキップ")
        text_renderer.skip_text()
        return

    if game_state.get("use_ir") and not is_ir_idle(game_state):
        if _ir_has_blocking_anims(game_state):
            return
        _ir_fast_forward_animations(game_state, 300)

    if game_state.get("use_ir") and not is_ir_idle(game_state):
        return

    # テキスト/アニメがidleなら次の段落へ
    print("[ENTER] 次の段落に進む")
    _flush_scroll_line_to_backlog(game_state)  # スクロール中の現在行をバックログに追加
    can_continue = advance_to_next_dialogue(game_state)
    if not can_continue:
        print("[ENTER] KSファイル終了")
        # KSファイル終了をgame_stateに記録
        game_state['ks_finished'] = True

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

def is_ir_idle(game_state):
    """IRアニメーションがアイドルか判定する（暫定）"""
    if not game_state.get("use_ir"):
        return True
    return not game_state.get("ir_anim_pending", False)

def is_input_blocked(game_state):
    if not game_state.get("use_ir"):
        return False
    fast_until = game_state.get("ir_fast_forward_until")
    if fast_until is not None and pygame.time.get_ticks() < fast_until:
        return True
    return game_state.get("ir_anim_pending") and _ir_has_blocking_anims(game_state)

def draw_input_blocked_notice(game_state, surface):
    if not is_input_blocked(game_state):
        return
    text_renderer = game_state.get("text_renderer")
    font = None
    if text_renderer and hasattr(text_renderer, "fonts"):
        font = text_renderer.fonts.get("default") or text_renderer.fonts.get("text")
    if not font:
        font = pygame.font.SysFont("Arial", 20)
    label = font.render("INPUT BLOCKED", True, (255, 0, 0))
    x = surface.get_width() - label.get_width() - 8
    y = 8
    surface.blit(label, (x, y))

def _update_ir_active_anims(game_state):
    active_anims = game_state.get("ir_active_anims") or []
    fast_until = game_state.get("ir_fast_forward_until")
    if fast_until is not None and pygame.time.get_ticks() >= fast_until:
        if DEBUG:
            print("[IR] fast-forward ended")
        game_state["ir_fast_forward_until"] = None
    if not active_anims:
        game_state["ir_anim_pending"] = False
        game_state["ir_anim_end_time"] = None
        game_state["ir_fast_forward_active"] = False
        return
    now = pygame.time.get_ticks()

    def _anim_still_active(anim):
        # SEブロック: channelが再生中かつタイムアウト内のみ生存
        if anim.get("type") == "se_block":
            ch = anim.get("se_channel")
            if ch is None:
                return False
            if anim.get("end_time", 0) <= now:
                return False  # タイムアウト
            return ch.get_busy()
        # 通常の時間ベースアニメ
        return anim.get("end_time", 0) > now

    active_anims[:] = [anim for anim in active_anims if _anim_still_active(anim)]
    if active_anims:
        game_state["ir_anim_pending"] = True
        game_state["ir_anim_end_time"] = max(anim.get("end_time", 0) for anim in active_anims)
    else:
        game_state["ir_anim_pending"] = False
    game_state["ir_anim_end_time"] = None

def _ir_has_blocking_anims(game_state):
    active_anims = game_state.get("ir_active_anims") or []
    return any(anim.get("on_advance") == "block" for anim in active_anims)

def _ir_fast_forward_animations(game_state, duration_ms):
    now = pygame.time.get_ticks()
    fast_until = game_state.get("ir_fast_forward_until")
    if fast_until is not None and now < fast_until:
        return
    if fast_until is not None and now >= fast_until:
        game_state["ir_fast_forward_until"] = None
        game_state["ir_fast_forward_active"] = False
    duration_ms = max(int(duration_ms), 0)
    if DEBUG:
        print(f"[IR] fast-forward start duration_ms={duration_ms}")
    game_state["ir_fast_forward_until"] = now + duration_ms
    game_state["ir_fast_forward_active"] = True

    def retime(start_time, duration):
        if duration <= 0:
            return now, 0
        elapsed = max(0, now - start_time)
        if elapsed >= duration:
            return now, 0
        progress = elapsed / duration
        remaining = duration - elapsed
        new_duration = min(duration_ms, remaining)
        new_start = now - int(progress * new_duration)
        return new_start, int(new_duration)

    character_anim = game_state.get("character_anim", {})
    for anim in list(character_anim.values()):
        start, dur = retime(anim.get("start_time", now), anim.get("duration", 0))
        anim["start_time"] = start
        anim["duration"] = dur

    bg_state = game_state.get("background_state", {})
    bg_anim = bg_state.get("anim")
    if bg_anim:
        start, dur = retime(bg_anim.get("start_time", now), bg_anim.get("duration", 0))
        bg_anim["start_time"] = start
        bg_anim["duration"] = dur

    fades = game_state.get("character_part_fades", {})
    for part_map in fades.values():
        for fade in part_map.values():
            start, dur = retime(fade.get("start_time", now), fade.get("duration", 0))
            fade["start_time"] = start
            fade["duration"] = dur

    hide_pending = game_state.get("character_hide_pending", {})
    for char_name, end_time in list(hide_pending.items()):
        remaining = max(0, end_time - now)
        hide_pending[char_name] = now + min(remaining, duration_ms)

    fade_state = game_state.get("fade_state", {})
    if fade_state.get("active"):
        start, dur = retime(fade_state.get("start_time", now), fade_state.get("duration", 0))
        fade_state["start_time"] = start
        fade_state["duration"] = dur

    active_anims = game_state.get("ir_active_anims") or []
    for anim in active_anims:
        anim["end_time"] = now + duration_ms
    game_state["ir_anim_pending"] = bool(active_anims)
    game_state["ir_anim_end_time"] = (now + duration_ms) if active_anims else None


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
    
    # 通知システムの更新
    if 'notification_manager' in game_state:
        game_state['notification_manager'].update()

    if game_state.get("use_ir"):
        text_renderer = game_state.get("text_renderer")
        if text_renderer and text_renderer.skip_mode:
            if game_state.get("ir_anim_pending"):
                if _ir_has_blocking_anims(game_state):
                    if DEBUG:
                        print("[IR] skip blocked by on_advance=block")
                elif not game_state.get("ir_fast_forward_active"):
                    _ir_fast_forward_animations(game_state, 300)
        _update_ir_active_anims(game_state)
        if game_state.get("ir_waiting_for_anim") and is_ir_idle(game_state):
            game_state["ir_waiting_for_anim"] = False
            advance_to_next_dialogue(game_state)


    # 自動進行の処理（選択肢表示中は無効化）
    if (game_state['text_renderer'].is_ready_for_auto_advance() and 
        is_ir_idle(game_state) and
        not is_input_blocked(game_state) and
        not game_state['backlog_manager'].is_showing_backlog() and
        not game_state['choice_renderer'].is_choice_showing()):
        # 自動的に次の対話に進む
        _flush_scroll_line_to_backlog(game_state)  # スクロール中の現在行をバックログに追加
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
        if isinstance(current_dialogue, list) and len(current_dialogue) > 8:
            bgm_name = current_dialogue[7]
            bgm_volume = current_dialogue[8]
            bgm_loop = current_dialogue[9] if len(current_dialogue) > 9 else True
            
            # BGM?????????????????
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
