import pygame
from config import *
from .character_manager import (
    move_character,
    hide_character,
    set_blink_enabled,
    init_blink_system,
    start_character_part_fade,
    start_character_hide_fade,
)
from .background_manager import show_background, move_background
from .fade_manager import start_fadeout, start_fadein

def advance_dialogue(game_state):
    """次の対話に進む"""
    if game_state.get("use_ir") and game_state.get("ir_data"):
        return advance_dialogue_ir(game_state)
    max_index = len(game_state['dialogue_data']) - 1

    if game_state['current_paragraph'] >= max_index:
        return False

    game_state['current_paragraph'] += 1

    # 境界チェック
    if game_state['current_paragraph'] >= len(game_state['dialogue_data']):
        print(f"[ERROR] 段落インデックス越界: {game_state['current_paragraph']} >= {len(game_state['dialogue_data'])}")
        return False

    current_dialogue = game_state['dialogue_data'][game_state['current_paragraph']]

    # 辞書タイプの場合はそのまま処理
    if isinstance(current_dialogue, dict):
        dialogue_text = ""
    else:
        # リストタイプの場合
        if len(current_dialogue) < 6:
            print(f"[ERROR] 対話データの形式が不正: 長さ={len(current_dialogue)}")
            return False
        dialogue_text = current_dialogue[6] if len(current_dialogue) > 6 else ""

    # スクロール停止コマンドかどうかチェック
    if dialogue_text and dialogue_text.startswith("_SCROLL_STOP"):
        return _handle_scroll_stop(game_state)

    # キャラクター登場コマンドかどうかチェック
    if dialogue_text and dialogue_text.startswith("_CHARA_NEW_"):
        return _handle_character_show(game_state, dialogue_text, current_dialogue)
    
    # キャラクター退場コマンドかどうかチェック
    elif dialogue_text and dialogue_text.startswith("_CHARA_HIDE_"):
        return _handle_character_hide(game_state, dialogue_text)

    # 移動コマンドかどうかチェック
    elif dialogue_text and dialogue_text.startswith("_MOVE_"):
        return _handle_character_move(game_state, dialogue_text, current_dialogue)
    
    # 背景表示コマンドかどうかチェック
    elif dialogue_text and dialogue_text.startswith("_BG_SHOW_"):
        return _handle_background_show(game_state, dialogue_text)
    
    # 背景移動コマンドかどうかチェック
    elif dialogue_text and dialogue_text.startswith("_BG_MOVE_"):
        return _handle_background_move(game_state, dialogue_text)

    # 選択肢コマンドかどうかチェック
    elif dialogue_text and dialogue_text.startswith("_CHOICE_"):
        return _handle_choice(game_state, dialogue_text, current_dialogue)
    
    # フェードアウトコマンドかどうかチェック
    elif dialogue_text and dialogue_text.startswith("_FADEOUT_"):
        return _handle_fadeout(game_state, dialogue_text)
    
    # フェードインコマンドかどうかチェック
    elif dialogue_text and dialogue_text.startswith("_FADEIN_"):
        return _handle_fadein(game_state, dialogue_text)
    
    # SE再生コマンドかどうかチェック
    elif dialogue_text and dialogue_text.startswith("_SE_PLAY_"):
        return _handle_se_play(game_state, dialogue_text)
    
    # BGM一時停止コマンドかどうかチェック
    elif dialogue_text and dialogue_text.startswith("_BGM_PAUSE"):
        return _handle_bgm_pause(game_state, current_dialogue)
    
    # BGM再生開始コマンドかどうかチェック
    elif dialogue_text and dialogue_text.startswith("_BGM_UNPAUSE"):
        return _handle_bgm_unpause(game_state, current_dialogue)
    
    else:
        # 特殊タイプのコマンドチェック
        if isinstance(current_dialogue, dict):
            command_type = current_dialogue.get('type')

            # if条件分岐開始
            if command_type == 'if_start':
                return _handle_if_start(game_state, current_dialogue)

            # if条件分岐終了
            elif command_type == 'if_end':
                return _handle_if_end(game_state, current_dialogue)

            # フラグ設定
            elif command_type == 'flag_set':
                return _handle_flag_set(game_state, current_dialogue)

            # イベント解禁
            elif command_type == 'event_unlock':
                return _handle_event_unlock(game_state, current_dialogue)

        # 通常の対話テキスト
        return _handle_dialogue_text(game_state, current_dialogue)
    
def advance_dialogue_ir(game_state):
    """Advance dialogue using IR data."""
    ir_data = game_state.get("ir_data") or {}
    steps = ir_data.get("steps") or []
    if not steps:
        return False

    next_index = game_state.get("ir_step_index", -1) + 1
    if next_index >= len(steps):
        return False

    game_state["ir_step_index"] = next_index
    step = steps[next_index]
    if isinstance(step, dict) and "source_index" in step:
        game_state["current_paragraph"] = step.get("source_index", next_index)
    else:
        game_state["current_paragraph"] = next_index
    game_state["ir_anim_pending"] = False
    game_state["ir_anim_end_time"] = None

    actions = step.get("actions") if isinstance(step, dict) else None
    choice_shown = False
    if actions:
        for action in actions:
            action_type = action.get("action")
            params = action.get("params") or {}
            if action_type == "scroll_stop":
                _ir_handle_scroll_stop(game_state)
                return advance_dialogue_ir(game_state)
            if action_type == "if_start":
                return _handle_if_start(game_state, params)
            if action_type == "if_end":
                return _handle_if_end(game_state, params)
            if action_type == "flag_set":
                return _handle_flag_set(game_state, params)
            if action_type == "event_unlock":
                return _handle_event_unlock(game_state, params)
            if action_type == "choice":
                _ir_handle_choice(game_state, params)
                choice_shown = True
                continue
            _ir_dispatch_action(game_state, action)

    text = step.get("text") if isinstance(step, dict) else None
    if text:
        speaker = text.get("speaker")
        body = text.get("body", "")
        should_scroll = bool(text.get("scroll", False))
        text_renderer = game_state.get("text_renderer")
        if text_renderer:
            active_characters = game_state.get("active_characters", [])
            if isinstance(active_characters, dict):
                active_characters = list(active_characters.keys())
            text_renderer.set_dialogue(
                body,
                speaker,
                should_scroll=should_scroll,
                background=None,
                active_characters=active_characters,
            )
        return True

    if actions and not choice_shown:
        if game_state.get("ir_anim_pending"):
            game_state["ir_waiting_for_anim"] = True
            return True
        return advance_dialogue_ir(game_state)

    return True

def _ir_dispatch_action(game_state, action):
    action_type = action.get("action")
    target = action.get("target")
    params = action.get("params") or {}

    if action_type == "chara_show":
        _ir_handle_character_show(game_state, target, params)
    elif action_type == "chara_shift":
        _ir_handle_character_shift(game_state, target, params)
    elif action_type == "chara_hide":
        _ir_handle_character_hide(game_state, target, params)
    elif action_type == "chara_move":
        _ir_handle_character_move(game_state, target, params)
    elif action_type == "bg_show":
        _ir_handle_background_show(game_state, params)
    elif action_type == "bg_move":
        _ir_handle_background_move(game_state, params)
    elif action_type == "background":
        bg_name = params.get("value") or params.get("storage")
        if bg_name:
            show_background(game_state, bg_name, 0.5, 0.5, 1.0)
    elif action_type == "fadeout":
        color = params.get("color", "black")
        time = _to_float(params.get("time"), 1.0)
        start_fadeout(game_state, color, time)
    elif action_type == "fadein":
        time = _to_float(params.get("time"), 1.0)
        start_fadein(game_state, time)
    elif action_type == "se_play":
        _ir_handle_se_play(game_state, params)
    elif action_type == "bgm_pause":
        _ir_handle_bgm_pause(game_state, params)
    elif action_type == "bgm_unpause":
        _ir_handle_bgm_unpause(game_state, params)
    _ir_register_action_animation(game_state, action)

def _ir_handle_scroll_stop(game_state):
    text_renderer = game_state.get("text_renderer")
    if text_renderer:
        text_renderer.scroll_manager.process_scroll_stop_command()

def _ir_handle_choice(game_state, params):
    options = params.get("options") or []
    if not options:
        return
    choice_renderer = game_state.get("choice_renderer")
    if choice_renderer:
        choice_renderer.show_choices(options)

def _ir_handle_character_show(game_state, target, params):
    if not target:
        return

    fade_ms = _get_fade_ms(params, CHARA_TRANSITION_DEFAULT_MS)
    torso_id = params.get("torso") or target
    show_x = _to_float(params.get("x"), 0.5)
    show_y = _to_float(params.get("y"), 0.5)
    size = _to_float(params.get("size"), 1.0)
    blink_enabled = params.get("blink", True)

    image_manager = game_state.get("image_manager")
    if not image_manager:
        return
    char_img = image_manager.get_image("characters", torso_id)
    if not char_img:
        return

    if "character_torso" not in game_state:
        game_state["character_torso"] = {}
    game_state["character_torso"][target] = torso_id
    hide_pending = game_state.get("character_hide_pending")
    if hide_pending and target in hide_pending:
        hide_pending.pop(target, None)

    is_new_character = target not in game_state.get("active_characters", [])
    if is_new_character:
        game_state["active_characters"].append(target)

        char_width = char_img.get_width()
        char_height = char_img.get_height()
        char_base_scale = VIRTUAL_HEIGHT / char_height
        virtual_width = char_width * char_base_scale * size
        virtual_height = char_height * char_base_scale * size
        virtual_center_x = VIRTUAL_WIDTH * show_x
        virtual_center_y = VIRTUAL_HEIGHT * show_y
        virtual_pos_x = int(virtual_center_x - virtual_width // 2)
        virtual_pos_y = int(virtual_center_y - virtual_height // 2)
        pos_x, pos_y = scale_pos(virtual_pos_x, virtual_pos_y)

        game_state["character_pos"][target] = [pos_x, pos_y]
        game_state["character_zoom"][target] = size

        set_blink_enabled(game_state, target, blink_enabled)
        if blink_enabled:
            init_blink_system(game_state, target)

    _ir_update_expressions(game_state, target, params)
    if fade_ms > 0:
        start_character_part_fade(game_state, target, "torso", None, torso_id, fade_ms)
        expressions = game_state.get("character_expressions", {}).get(target, {})
        if expressions.get("brow"):
            start_character_part_fade(game_state, target, "brow", None, expressions.get("brow"), fade_ms)
        if expressions.get("eye"):
            start_character_part_fade(game_state, target, "eye", None, expressions.get("eye"), fade_ms)
        if expressions.get("mouth"):
            start_character_part_fade(game_state, target, "mouth", None, expressions.get("mouth"), fade_ms)
        if expressions.get("cheek"):
            start_character_part_fade(game_state, target, "cheek", None, expressions.get("cheek"), fade_ms)

    try:
        image_manager.preload_character_set(target, {
            "eyes": [params.get("eye")] if params.get("eye") else [],
            "mouths": [params.get("mouth")] if params.get("mouth") else [],
            "brows": [params.get("brow")] if params.get("brow") else [],
            "cheeks": [params.get("cheek")] if params.get("cheek") else [],
        })
    except Exception:
        pass

def _ir_handle_character_shift(game_state, target, params):
    if not target:
        return
    active_characters = game_state.get("active_characters", [])
    if target not in active_characters:
        active_characters.append(target)
    hide_pending = game_state.get("character_hide_pending")
    if hide_pending and target in hide_pending:
        hide_pending.pop(target, None)
    fade_ms = _get_fade_ms(params, CHARA_TRANSITION_DEFAULT_MS)
    old_expressions = game_state.get("character_expressions", {}).get(target, {
        "eye": "",
        "mouth": "",
        "brow": "",
        "cheek": "",
    }).copy()
    old_torso = game_state.get("character_torso", {}).get(target)

    torso_id = params.get("torso")
    image_manager = game_state.get("image_manager")
    if torso_id and image_manager and not image_manager.get_image("characters", torso_id):
        torso_id = None
    if torso_id:
        if "character_torso" not in game_state:
            game_state["character_torso"] = {}
        game_state["character_torso"][target] = torso_id
    _ir_update_expressions(game_state, target, params)

    if fade_ms > 0:
        if "torso" in params and torso_id and torso_id != old_torso:
            start_character_part_fade(game_state, target, "torso", old_torso, torso_id, fade_ms)

        new_expressions = game_state.get("character_expressions", {}).get(target, {})
        for key, part in (("brow", "brow"), ("eye", "eye"), ("mouth", "mouth"), ("cheek", "cheek")):
            if key not in params:
                continue
            old_val = old_expressions.get(key, "")
            new_val = new_expressions.get(key, "")
            if old_val != new_val:
                start_character_part_fade(
                    game_state,
                    target,
                    part,
                    old_val or None,
                    new_val or None,
                    fade_ms,
                )

def _ir_handle_character_hide(game_state, target, params):
    if not target:
        return
    fade_ms = _get_fade_ms(params or {}, CHARA_TRANSITION_DEFAULT_MS)
    if fade_ms <= 0:
        hide_character(game_state, target)
        return
    start_character_hide_fade(game_state, target, fade_ms)

def _ir_handle_character_move(game_state, target, params):
    if not target:
        return
    left = _to_float(params.get("left"), 0.0)
    top = _to_float(params.get("top"), 0.0)
    duration = _to_int(params.get("time"), 600)
    zoom = _to_float(params.get("zoom"), 1.0)
    move_character(game_state, target, left, top, duration, zoom)

def _ir_handle_background_show(game_state, params):
    storage = params.get("storage")
    if not storage:
        return
    x = _to_float(params.get("x"), 0.5)
    y = _to_float(params.get("y"), 0.5)
    zoom = _to_float(params.get("zoom"), 1.0)
    show_background(game_state, storage, x, y, zoom)

def _ir_handle_background_move(game_state, params):
    left = _to_float(params.get("left"), 0.0)
    top = _to_float(params.get("top"), 0.0)
    duration = _to_int(params.get("time"), 600)
    zoom = _to_float(params.get("zoom"), 1.0)
    move_background(game_state, left, top, duration, zoom)

def _ir_handle_se_play(game_state, params):
    se_manager = game_state.get("se_manager")
    if not se_manager:
        return
    filename = params.get("file")
    if not filename:
        return
    volume = _to_float(params.get("volume"), 0.5)
    frequency = _to_int(params.get("frequency"), 1)
    se_manager.play_se(filename, volume, frequency)

def _ir_handle_bgm_pause(game_state, params):
    bgm_manager = game_state.get("bgm_manager")
    if not bgm_manager:
        return
    fade_time = _to_float(params.get("fade_time"), 0.0)
    if fade_time > 0:
        bgm_manager.pause_bgm_with_fade(fade_time)
    else:
        bgm_manager.pause_bgm()

def _ir_handle_bgm_unpause(game_state, params):
    bgm_manager = game_state.get("bgm_manager")
    if not bgm_manager:
        return
    fade_time = _to_float(params.get("fade_time"), 0.0)
    if fade_time > 0:
        bgm_manager.unpause_bgm_with_fade(fade_time)
    else:
        bgm_manager.unpause_bgm()

def _ir_update_expressions(game_state, target, params):
    existing_expressions = game_state.get("character_expressions", {}).get(target, {
        "eye": "",
        "mouth": "",
        "brow": "",
        "cheek": "",
    })
    expressions = existing_expressions.copy()
    if "eye" in params:
        expressions["eye"] = params.get("eye") or ""
    if "mouth" in params:
        expressions["mouth"] = params.get("mouth") or ""
    if "brow" in params:
        expressions["brow"] = params.get("brow") or ""
    if "cheek" in params:
        expressions["cheek"] = params.get("cheek") or ""
    game_state.setdefault("character_expressions", {})[target] = expressions

def _to_float(value, default):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default

def _to_int(value, default):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default

def _get_fade_ms(params, default_ms):
    if not isinstance(params, dict):
        return default_ms
    value = params.get("fade")
    if value is None:
        value = params.get("time")
    if value is None:
        return default_ms
    try:
        value = float(value)
    except (TypeError, ValueError):
        return default_ms
    if value > 10:
        return int(value)
    return int(value * 1000)

def _ir_get_action_duration_ms(action_type, params):
    if action_type in ("chara_show", "chara_shift", "chara_hide"):
        return _get_fade_ms(params or {}, CHARA_TRANSITION_DEFAULT_MS)
    if action_type == "chara_move":
        return _to_int((params or {}).get("time"), 600)
    if action_type == "bg_move":
        return _to_int((params or {}).get("time"), 600)
    if action_type in ("fadeout", "fadein"):
        return int(_to_float((params or {}).get("time"), 1.0) * 1000)
    return 0

def _ir_default_on_advance(action_type):
    if action_type in ("fadeout", "fadein"):
        return "complete"
    if action_type in ("chara_show", "chara_shift", "chara_hide", "chara_move", "bg_show", "bg_move"):
        return "complete"
    return None

def _ir_register_action_animation(game_state, action):
    action_type = action.get("action")
    anim = action.get("animation") or {}
    on_advance = anim.get("on_advance") or _ir_default_on_advance(action_type)
    if on_advance not in ("block", "complete", "interrupt"):
        return
    duration_ms = _ir_get_action_duration_ms(action_type, action.get("params") or {})
    if duration_ms <= 0:
        return
    end_time = pygame.time.get_ticks() + duration_ms
    active_anims = game_state.setdefault("ir_active_anims", [])
    active_anims.append({
        "action": action_type,
        "target": action.get("target"),
        "on_advance": on_advance,
        "end_time": end_time,
    })
    game_state["ir_anim_pending"] = True
    current_end = game_state.get("ir_anim_end_time")
    if current_end is None or end_time > current_end:
        game_state["ir_anim_end_time"] = end_time

def _handle_scroll_stop(game_state):
    """スクロール停止コマンドを処理"""
    if DEBUG:
        print("スクロール停止コマンド実行")
    
    game_state['text_renderer'].scroll_manager.process_scroll_stop_command()
    
    # スクロール停止コマンドの場合は次の対話に進む
    return advance_dialogue(game_state)

def _handle_character_show(game_state, dialogue_text, current_dialogue):
    """キャラクター登場コマンドを処理（スクロール状態に影響しない）"""
    parts = dialogue_text.split('_')
    if DEBUG:
        print(f"キャラクター登場コマンド解析: dialogue_text='{dialogue_text}'")
        print(f"分割結果: {parts}")

    if len(parts) >= 6:  # _CHARA_NEW,キャラクター名,x,y,size,blink
        # 新形式: _CHARA_NEW_T04_00_00_x_y_size_blink_fade_論理名
        if len(parts) >= 12:
            torso_id = f"{parts[3]}_{parts[4]}_{parts[5]}"  # 胴体パーツID（画像用）
            char_name = parts[11]  # キャラクター論理名（管理用）
            x_index = 6
            y_index = 7
            size_index = 8
            blink_index = 9
            # fade_index = 10  # 今後使用予定
        # 旧形式: _CHARA_NEW_T04_00_00_x_y_size_blink (論理名なし)
        elif len(parts) >= 10:
            torso_id = f"{parts[3]}_{parts[4]}_{parts[5]}"
            char_name = torso_id  # 後方互換性: 論理名=胴体ID
            x_index = 6
            y_index = 7
            size_index = 8
            blink_index = 9
        # さらに古い形式: _CHARA_NEW_名前_x_y_size_blink
        else:
            torso_id = parts[3]
            char_name = parts[3]
            x_index = 4
            y_index = 5
            size_index = 6
            blink_index = 7

        try:
            show_x = float(parts[x_index])
            show_y = float(parts[y_index])
            size = float(parts[size_index]) if len(parts) > size_index else 1.0
            blink_enabled = parts[blink_index].lower() == 'true' if len(parts) > blink_index else True
        except (ValueError, IndexError):
            show_x = 0.5
            show_y = 0.5
            size = 1.0
            blink_enabled = True

        # まず画像の存在を確認（遅延ロード対応）- torso_idを使用
        image_manager = game_state['image_manager']
        char_img = image_manager.get_image("characters", torso_id)
        if not char_img:
            if DEBUG:
                print(f"警告: キャラクター画像 '{char_name}' が見つかりません")
            return

        # キャラクター論理名 -> 胴体IDのマッピングを保存
        if 'character_torso' not in game_state:
            game_state['character_torso'] = {}
        game_state['character_torso'][char_name] = torso_id

        # キャラクターが新規登場か既存キャラクターの表情変更かを判定
        is_new_character = char_name not in game_state['active_characters']

        if is_new_character:
            game_state['active_characters'].append(char_name)
            if DEBUG:
                print(f"キャラクター '{char_name}' (胴体: {torso_id}) を active_characters に追加")

            # x,yパラメーターを使って位置を設定
            char_width = char_img.get_width()
            char_height = char_img.get_height()

            # 仮想解像度に対する基準スケールを計算
            char_base_scale = VIRTUAL_HEIGHT / char_height  # 高さ基準でスケール計算

            # 仮想座標系での描画サイズを計算
            virtual_width = char_width * char_base_scale * size
            virtual_height = char_height * char_base_scale * size

            # 0.0-1.0の値を仮想座標に変換
            # 指定位置に画像の中央が来るように座標を計算
            virtual_center_x = VIRTUAL_WIDTH * show_x
            virtual_center_y = VIRTUAL_HEIGHT * show_y
            virtual_pos_x = int(virtual_center_x - virtual_width // 2)
            virtual_pos_y = int(virtual_center_y - virtual_height // 2)

            # 仮想座標を実座標にスケーリング
            pos_x, pos_y = scale_pos(virtual_pos_x, virtual_pos_y)

            game_state['character_pos'][char_name] = [pos_x, pos_y]
            if DEBUG:
                print(f"キャラクター '{char_name}' の位置設定: ({pos_x}, {pos_y}), サイズ: {size}")

            # sizeパラメータをcharacter_zoomに設定
            game_state['character_zoom'][char_name] = size

            # まばたき機能を設定
            set_blink_enabled(game_state, char_name, blink_enabled)
            if blink_enabled:
                init_blink_system(game_state, char_name)
                if DEBUG:
                    print(f"キャラクター '{char_name}' のまばたき機能を有効にしました")
            else:
                if DEBUG:
                    print(f"キャラクター '{char_name}' のまばたき機能を無効にしました")

        else:
            if DEBUG:
                print(f"[CHARACTER] '{char_name}' は既に登場中 - 表情のみ更新します")

        # キャラクターの表情を更新（新規登場でも既存でも実行）
        if len(current_dialogue) >= 6:
            # 既存の表情を取得（存在しない場合は空の表情）
            existing_expressions = game_state['character_expressions'].get(char_name, {
                'eye': '', 'mouth': '', 'brow': '', 'cheek': ''
            })

            # 新しい表情データを構築（空でない場合のみ上書き）
            expressions = existing_expressions.copy()
            if current_dialogue[2]:  # 目
                expressions['eye'] = current_dialogue[2]
            if current_dialogue[3]:  # 口
                expressions['mouth'] = current_dialogue[3]
            if current_dialogue[4]:  # 眉
                expressions['brow'] = current_dialogue[4]
            if len(current_dialogue) > 5 and current_dialogue[5]:  # 頬
                expressions['cheek'] = current_dialogue[5]

            game_state['character_expressions'][char_name] = expressions

            print(f"[CHARACTER] '{char_name}' の表情{'設定' if is_new_character else '更新'}: {expressions}")
            print(f"[CHARACTER] まばたき有効: {blink_enabled}")

            # 表情パーツも事前ロード
            try:
                image_manager.preload_character_set(char_name, {
                    'eyes': [expressions['eye']] if expressions['eye'] else [],
                    'mouths': [expressions['mouth']] if expressions['mouth'] else [],
                    'brows': [expressions['brow']] if expressions['brow'] else [],
                    'cheeks': [expressions['cheek']] if expressions['cheek'] else []
                })
            except Exception as e:
                if DEBUG:
                    print(f"表情パーツ事前ロードエラー（続行）: {char_name}: {e}")
        
    # キャラクター登場コマンドの場合は次の対話に進む（スクロール状態維持）
    return advance_dialogue(game_state)

def _handle_character_hide(game_state, dialogue_text):
    """キャラクター退場コマンドを処理（スクロール状態に影響しない）"""
    parts = dialogue_text.split('_')
    if DEBUG:
        print(f"退場コマンド解析: dialogue_text='{dialogue_text}'")
        print(f"退場コマンド解析: parts={parts}")
    if len(parts) >= 4:  # _CHARA_HIDE_キャラクター名
        char_name = parts[3]
        if DEBUG:
            print(f"退場対象キャラクター名: '{char_name}'")
        hide_character(game_state, char_name)
    else:
        if DEBUG:
            print(f"エラー: 退場コマンドの形式が不正です: '{dialogue_text}'")
        
    # キャラクター退場コマンドの場合は次の対話に進む（スクロール状態維持）
    return advance_dialogue(game_state)

def _handle_character_move(game_state, dialogue_text, current_dialogue):
    """キャラクター移動コマンドを処理（スクロール状態に影響しない）"""
    parts = dialogue_text.split('_')
    if len(parts) >= 5:  # _MOVE_left_top_duration_zoom
        char_name = current_dialogue[1]
        left = float(parts[2])
        top = float(parts[3])
        duration = int(parts[4]) if parts[4].isdigit() else 600
        zoom = float(parts[5]) if len(parts) > 5 else 1.0
        move_character(game_state, char_name, left, top, duration, zoom)
        if DEBUG:
            print(f"移動コマンド実行: {char_name} -> ({left}, {top}, {zoom})")
    
    # 移動コマンドの場合は次の対話に進む（スクロール状態維持）
    return advance_dialogue(game_state)

def _handle_background_show(game_state, dialogue_text):
    """背景表示コマンドを処理（スクロール状態に影響しない）"""
    parts = dialogue_text.split('_')
    if DEBUG:
        print(f"背景表示コマンド解析: dialogue_text='{dialogue_text}'")
        print(f"分割結果: {parts}")

    if len(parts) >= 6:  # _BG_SHOW_,背景名,x,y,zoom
        bg_name = parts[3]
        
        try:
            bg_x = float(parts[4])
            bg_y = float(parts[5])
            bg_zoom = float(parts[6])
        except (ValueError, IndexError):
            bg_x = 0.5
            bg_y = 0.5
            bg_zoom = 1.0

        show_background(game_state, bg_name, bg_x, bg_y, bg_zoom)
        if DEBUG:
            print(f"背景 '{bg_name}' を表示しました (x={bg_x}, y={bg_y}, zoom={bg_zoom})")
        
    # 背景表示コマンドの場合は次の対話に進む（スクロール状態維持）
    return advance_dialogue(game_state)

def _handle_background_move(game_state, dialogue_text):
    """背景移動コマンドを処理（スクロール状態に影響しない）"""
    parts = dialogue_text.split('_')
    if DEBUG:
        print(f"背景移動コマンド解析: dialogue_text='{dialogue_text}'")
        print(f"分割結果: {parts}")
        
    if len(parts) >= 6:  # _BG_MOVE_left_top_duration_zoom
        bg_left = float(parts[3])
        bg_top = float(parts[4])
        bg_duration = int(parts[5]) if parts[5].isdigit() else 600
        bg_move_zoom = float(parts[6]) if len(parts) > 6 else 1.0
        move_background(game_state, bg_left, bg_top, bg_duration, bg_move_zoom)
        if DEBUG:
            print(f"背景移動コマンド実行: 相対移動({bg_left}, {bg_top}), zoom={bg_move_zoom}, 時間={bg_duration}ms")
    
    # 背景移動コマンドの場合は次の対話に進む（スクロール状態維持）
    return advance_dialogue(game_state)

def _handle_choice(game_state, dialogue_text, current_dialogue):
    """選択肢を処理"""
    try:
        options = []
        
        # 正規化された形式の場合（リスト形式）
        if isinstance(current_dialogue, list) and len(current_dialogue) > 12:
            if dialogue_text == "_CHOICE_":
                options = current_dialogue[12]  # 13番目の要素が選択肢リスト
                if DEBUG:
                    print(f"正規化された選択肢データを取得: {options}")
        
        # 辞書形式の場合（dialogue_loaderからの直接データ）
        elif isinstance(current_dialogue, dict) and current_dialogue.get('type') == 'choice':
            options = current_dialogue.get('options', [])
            if DEBUG:
                print(f"辞書形式の選択肢データを取得: {options}")
        
        # その他の形式から解析
        else:
            options = _parse_choice_from_text(dialogue_text)
            if DEBUG:
                print(f"テキストから選択肢を解析: {options}")
        
        if options and len(options) >= 2:
            # 選択肢を表示
            game_state['choice_renderer'].show_choices(options)
            if DEBUG:
                print(f"選択肢を表示しました: {options}")
            return True
        else:
            if DEBUG:
                print(f"選択肢の形式が正しくありません: {options}")
            return advance_dialogue(game_state)
    
    except Exception as e:
        if DEBUG:
            print(f"選択肢処理エラー: {e}")
            import traceback
            traceback.print_exc()
        return advance_dialogue(game_state)

def _parse_choice_from_text(dialogue_text):
    """テキストから選択肢を解析"""
    import re
    options = []
    
    # _CHOICE_option1_option2_option3形式を解析
    parts = dialogue_text.split('_')
    for i, part in enumerate(parts):
        if i >= 2:  # _CHOICE_の後の部分
            if part.strip():
                options.append(part.strip())
    
    return options

def _handle_dialogue_text(game_state, current_dialogue):
    """通常の対話テキストを処理"""
    # cheek追加でインデックスがシフト: [bg, char, eye, mouth, brow, cheek, text, bgm, volume, loop, speaker, scroll]
    dialogue_text = current_dialogue[6]  # textは6番目
    display_name = current_dialogue[10] if len(current_dialogue) > 10 and current_dialogue[10] else current_dialogue[1]  # speakerは10番目
    
    # 表示名の有効性をチェック（CHARACTER_IMAGE_MAPは削除済み）
    # ファイル名直接使用するためチェック不要
    # if display_name and display_name not in CHARACTER_IMAGE_MAP:
    #     display_name = None
    
    # スクロール継続フラグをチェック（リストの12番目の要素）
    should_scroll = False
    if len(current_dialogue) > 11:
        should_scroll = current_dialogue[11]
    
    # アクティブキャラクターリストを適切な形式で取得
    active_characters = game_state.get('active_characters', [])
    if isinstance(active_characters, dict):
        active_characters = list(active_characters.keys())
    
    # テキストレンダラーに対話を設定（スクロール情報も含む）
    game_state['text_renderer'].set_dialogue(
        dialogue_text, 
        display_name,
        should_scroll=should_scroll,
        background=current_dialogue[0],
        active_characters=active_characters
    )

    # 話し手の表情を更新（空でない場合のみ）
    if current_dialogue[1] and current_dialogue[1] in game_state['active_characters']:
        char_name = current_dialogue[1]
        if len(current_dialogue) >= 5:
            # 既存の表情を取得
            existing_expressions = game_state['character_expressions'].get(char_name, {
                'eye': '', 'mouth': '', 'brow': '', 'cheek': ''
            })
            
            # 新しい表情データがある場合のみ更新
            expressions = existing_expressions.copy()
            if current_dialogue[2]:  # 新しい目のデータがある場合
                expressions['eye'] = current_dialogue[2]
            if current_dialogue[3]:  # 新しい口のデータがある場合
                expressions['mouth'] = current_dialogue[3]
            if current_dialogue[4]:  # 新しい眉のデータがある場合
                expressions['brow'] = current_dialogue[4]
            if len(current_dialogue) > 5 and current_dialogue[5]:  # 新しい頬のデータがある場合
                expressions['cheek'] = current_dialogue[5]
            
            game_state['character_expressions'][char_name] = expressions
    
    return True

def reset_dialogue_state(game_state):
    """対話状態をリセット（スクロール状態は維持）"""
    if DEBUG:
        print("対話状態リセット実行（スクロール状態は維持）")
    # スクロール状態に影響しないようにコメントアウト
    # game_state['text_renderer'].scroll_manager.reset_state()

def force_end_scroll_mode(game_state):
    """スクロールモードを強制終了（機能無効化）"""
    if DEBUG:
        print("スクロールモード強制終了は無効化されています")
    # 強制終了機能を無効化
    # game_state['text_renderer'].scroll_manager.force_end_scroll_mode()

def _handle_fadeout(game_state, dialogue_text):
    """フェードアウトコマンドを処理"""
    parts = dialogue_text.split('_')
    if DEBUG:
        print(f"フェードアウトコマンド解析: dialogue_text='{dialogue_text}'")
        print(f"分割結果: {parts}")

    if len(parts) >= 4:  # _FADEOUT_color_time
        fade_color = parts[2]
        try:
            fade_time = float(parts[3])
        except (ValueError, IndexError):
            fade_time = 1.0
        
        start_fadeout(game_state, fade_color, fade_time)
        print(f"[FADE] フェードアウト実行: color={fade_color}, time={fade_time}s")
    else:
        if DEBUG:
            print(f"エラー: フェードアウトコマンドの形式が不正です: '{dialogue_text}'")
    
    # フェードアウトコマンドの場合は次の対話に進む
    return advance_dialogue(game_state)

def _handle_fadein(game_state, dialogue_text):
    """フェードインコマンドを処理"""
    parts = dialogue_text.split('_')
    if DEBUG:
        print(f"フェードインコマンド解析: dialogue_text='{dialogue_text}'")
        print(f"分割結果: {parts}")

    if len(parts) >= 3:  # _FADEIN_time
        try:
            fade_time = float(parts[2])
        except (ValueError, IndexError):
            fade_time = 1.0
        
        start_fadein(game_state, fade_time)
        print(f"[FADE] フェードイン実行: time={fade_time}s")
    else:
        if DEBUG:
            print(f"エラー: フェードインコマンドの形式が不正です: '{dialogue_text}'")
    
    # フェードインコマンドの場合は次の対話に進む
    return advance_dialogue(game_state)

def _handle_se_play(game_state, dialogue_text):
    """SE再生コマンドを処理"""
    parts = dialogue_text.split('_')
    if DEBUG:
        print(f"SE再生コマンド解析: dialogue_text='{dialogue_text}'")
        print(f"分割結果: {parts}")

    if len(parts) >= 5:  # _SE_PLAY_filename_volume_frequency
        se_filename = parts[3]
        try:
            se_volume = float(parts[4])
        except (ValueError, IndexError):
            se_volume = 0.5
        try:
            se_frequency = int(parts[5])
        except (ValueError, IndexError):
            se_frequency = 1
        
        # SEManagerを使ってSEを再生
        se_manager = game_state.get('se_manager')
        if se_manager:
            success = se_manager.play_se(se_filename, se_volume, se_frequency)
            if DEBUG:
                if success:
                    print(f"SE再生成功: {se_filename} (volume={se_volume}, frequency={se_frequency})")
                else:
                    print(f"SE再生失敗: {se_filename}")
        else:
            if DEBUG:
                print("エラー: SEManagerが見つかりません")
    else:
        if DEBUG:
            print(f"エラー: SE再生コマンドの形式が不正です: '{dialogue_text}'")
    
    # SE再生コマンドの場合は次の対話に進む
    return advance_dialogue(game_state)

def _handle_bgm_pause(game_state, current_dialogue):
    """BGM一時停止コマンドを処理"""
    # フェードタイム情報を取得
    fade_time = 0.0
    
    # 正規化されたデータの場合（リスト形式）
    if isinstance(current_dialogue, list) and len(current_dialogue) > 12:
        bgm_data = current_dialogue[12]
        if isinstance(bgm_data, dict):
            fade_time = bgm_data.get('fade_time', 0.0)
    # 辞書形式の場合
    elif isinstance(current_dialogue, dict):
        fade_time = current_dialogue.get('fade_time', 0.0)
    
    if DEBUG:
        print(f"BGM一時停止コマンド実行: fade_time={fade_time}")
    
    # BGMManagerを使ってBGMを一時停止
    bgm_manager = game_state.get('bgm_manager')
    if bgm_manager:
        if fade_time > 0:
            bgm_manager.pause_bgm_with_fade(fade_time)
            if DEBUG:
                print(f"BGMを{fade_time}秒でフェードアウト一時停止しました")
        else:
            bgm_manager.pause_bgm()
            if DEBUG:
                print("BGMを即座に一時停止しました")
    else:
        if DEBUG:
            print("エラー: BGMManagerが見つかりません")
    
    # BGM一時停止コマンドの場合は次の対話に進む
    return advance_dialogue(game_state)

def _handle_bgm_unpause(game_state, current_dialogue):
    """BGM再生開始コマンドを処理"""
    # フェードタイム情報を取得
    fade_time = 0.0
    
    # 正規化されたデータの場合（リスト形式）
    if isinstance(current_dialogue, list) and len(current_dialogue) > 12:
        bgm_data = current_dialogue[12]
        if isinstance(bgm_data, dict):
            fade_time = bgm_data.get('fade_time', 0.0)
    # 辞書形式の場合
    elif isinstance(current_dialogue, dict):
        fade_time = current_dialogue.get('fade_time', 0.0)
    
    if DEBUG:
        print(f"BGM再生開始コマンド実行: fade_time={fade_time}")
    
    # BGMManagerを使ってBGMの再生を再開
    bgm_manager = game_state.get('bgm_manager')
    if bgm_manager:
        if fade_time > 0:
            bgm_manager.unpause_bgm_with_fade(fade_time)
            if DEBUG:
                print(f"BGMを{fade_time}秒でフェードイン再開しました")
        else:
            bgm_manager.unpause_bgm()
            if DEBUG:
                print("BGMの再生を即座に再開しました")
    else:
        if DEBUG:
            print("エラー: BGMManagerが見つかりません")
    
    # BGM再生開始コマンドの場合は次の対話に進む
    return advance_dialogue(game_state)

def _handle_if_start(game_state, command_data):
    """if条件分岐開始を処理"""
    condition = command_data.get('condition', '')
    dialogue_loader = game_state.get('dialogue_loader')
    
    if DEBUG:
        print(f"条件分岐開始: condition='{condition}'")
    
    # 条件を評価
    condition_met = False
    if dialogue_loader:
        condition_met = dialogue_loader.check_condition(condition)
        if DEBUG:
            print(f"条件評価結果: {condition} -> {condition_met}")
    
    # 条件が満たされない場合、対応するendifまでスキップ
    if not condition_met:
        current_pos = game_state['current_paragraph']
        if_nesting = 1  # ネストレベル
        max_pos = len(game_state['dialogue_data']) - 1
        
        print(f"[DEBUG] 条件不一致でスキップ開始: 現在位置={current_pos}, 最大位置={max_pos}")
        
        while current_pos < max_pos:
            current_pos += 1
            
            # 境界チェック
            if current_pos >= len(game_state['dialogue_data']):
                print(f"[DEBUG] スキップ中に段落境界に到達: {current_pos}")
                break
                
            entry = game_state['dialogue_data'][current_pos]
            print(f"[DEBUG] スキップ中の段落{current_pos}をチェック: {type(entry)}")
            
            if isinstance(entry, dict):
                entry_type = entry.get('type')
                print(f"[DEBUG] dict型エントリ: type={entry_type}, nesting={if_nesting}")
                
                if entry_type == 'if_start':
                    if_nesting += 1
                elif entry_type == 'if_end':
                    if_nesting -= 1
                    if if_nesting == 0:
                        # 対応するendifに到達
                        game_state['current_paragraph'] = current_pos
                        if game_state.get("use_ir"):
                            ir_data = game_state.get("ir_data") or {}
                            source_to_step = ir_data.get("source_to_step") or {}
                            mapped_index = source_to_step.get(current_pos)
                            if mapped_index is not None:
                                game_state["ir_step_index"] = mapped_index
                        print(f"[DEBUG] 条件不一致により段落{current_pos}のendifまでスキップ完了")
                        # endifに到達したので、次の段落に進む
                        return advance_dialogue(game_state)
        
        # endifが見つからない場合
        if if_nesting > 0:
            print(f"[WARNING] 対応するendifが見つかりません。ネストレベル={if_nesting}")
            # 見つからない場合は最後まで進む
            game_state['current_paragraph'] = max_pos
            if game_state.get("use_ir"):
                ir_data = game_state.get("ir_data") or {}
                source_to_step = ir_data.get("source_to_step") or {}
                mapped_index = source_to_step.get(max_pos)
                if mapped_index is not None:
                    game_state["ir_step_index"] = mapped_index
            return False
    else:
        if DEBUG:
            print("条件一致により次の段落を実行")
    
    # 次の段落に進む
    return advance_dialogue(game_state)

def _handle_if_end(game_state, command_data):
    """if条件分岐終了を処理"""
    if DEBUG:
        print("条件分岐終了")
    
    # 単純に次の段落に進む
    return advance_dialogue(game_state)

def _handle_flag_set(game_state, command_data):
    """フラグ設定を処理"""
    flag_name = command_data.get('name')
    flag_value = command_data.get('value')
    dialogue_loader = game_state.get('dialogue_loader')
    
    if DEBUG:
        print(f"フラグ設定: {flag_name} = {flag_value}")
    
    if dialogue_loader and flag_name is not None:
        dialogue_loader.set_story_flag(flag_name, flag_value)
        if DEBUG:
            print(f"フラグ設定完了: {flag_name} = {flag_value}")
    
    # 次の段落に進む
    return advance_dialogue(game_state)

def _handle_event_unlock(game_state, command_data):
    """イベント解禁を処理"""
    events = command_data.get('events', [])
    dialogue_loader = game_state.get('dialogue_loader')
    
    print(f"[EVENT_UNLOCK] イベント解禁処理開始: {events}")
    
    if dialogue_loader and events:
        dialogue_loader.unlock_events(events)
        print(f"[EVENT_UNLOCK] イベント解禁完了: {events}")
    else:
        print(f"[EVENT_UNLOCK] 処理失敗: dialogue_loader={dialogue_loader}, events={events}")
    
    # 次の段落に進む
    return advance_dialogue(game_state)
