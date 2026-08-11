"""
KSファイル専用プレビュースクリプト
event_editor_mac.pyから別プロセスで起動され、指定された.ksファイルをプレビュー表示する

event_editor.pyのPreviewWindowクラスの実装をベースにしています
"""

import pygame
import sys
import os
import argparse
import json
import copy
import traceback

# tools/ の親ディレクトリ（プロジェクトルート）を sys.path に追加
# こうしないと `from core.config import *` 等が tools/ を基準に探してしまい失敗する
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from core.config import *
from dialogue.ir_builder import build_ir_from_normalized, dump_ir_json, get_ir_dump_path
from dialogue.dialogue_loader import DialogueLoader
from dialogue.text_renderer import TextRenderer
from dialogue.choice_renderer import ChoiceRenderer
from dialogue.character_manager import draw_characters, update_character_animations, init_blink_system
from dialogue.background_manager import draw_background, update_background_animation
from dialogue.fade_manager import draw_fade_overlay
from dialogue.notification_manager import NotificationManager
from dialogue.backlog_manager import BacklogManager
from dialogue.name_manager import get_name_manager
from dialogue.controller2 import handle_events as dialogue_handle_events, draw_input_blocked_notice
from dialogue.controller2 import update_game, is_ir_idle
from dialogue.scenario_manager import _ir_dispatch_action
from dialogue.model import change_bgm
from dialogue.event_datetime import apply_event_datetime
from core.services.bgm_manager import BGMManager
from core.services.se_manager import SEManager
from core.services.image_manager import ImageManager
from core.path_utils import get_font_path

def create_step_preview_runtime():
    """Create the expensive, reusable part of step preview rendering."""
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    pygame.init()
    try:
        pygame.mixer.init()
        pygame.mixer.music.set_volume(0.0)
    except Exception:
        pass

    hidden_flag = getattr(pygame, "HIDDEN", 0)
    pygame.display.set_mode((1, 1), hidden_flag)

    from core import config as cfg
    cfg.OFFSET_X = 0
    cfg.OFFSET_Y = 0
    cfg.SCALE = 1.0

    virtual_screen = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT))
    image_manager = ImageManager(DEBUG, cache_size=200)
    image_manager.scan_image_paths(VIRTUAL_WIDTH, VIRTUAL_HEIGHT)
    images = image_manager.load_essential_images(VIRTUAL_WIDTH, VIRTUAL_HEIGHT)
    return {
        "virtual_screen": virtual_screen,
        "image_manager": image_manager,
        "images": images,
    }


def settle_step_preview_animations(game_state):
    """Seek animations to their final frame without sleeping in real time."""
    now = pygame.time.get_ticks()

    for anim in game_state.get("character_anim", {}).values():
        anim["start_time"] = now - max(int(anim.get("duration", 0)), 0)

    background_anim = game_state.get("background_state", {}).get("anim")
    if background_anim:
        background_anim["start_time"] = (
            now - max(int(background_anim.get("duration", 0)), 0)
        )

    for part_map in game_state.get("character_part_fades", {}).values():
        for fade in part_map.values():
            fade["start_time"] = now - max(int(fade.get("duration", 0)), 0)

    for character_name in list(game_state.get("character_hide_pending", {})):
        game_state["character_hide_pending"][character_name] = now

    fade_state = game_state.get("fade_state", {})
    if fade_state.get("active"):
        fade_state["start_time"] = now - max(int(fade_state.get("duration", 0)), 0)

    for anim in game_state.get("ir_active_anims", []):
        anim["end_time"] = now

    # One update commits the final positions/alphas and clears IR pending flags.
    update_game(game_state)


def preview_step_image(
    ks_file_path,
    step_index,
    out_path,
    runtime=None,
    output_size=None,
    transition_progress=1.0,
    event_id=None,
):
    """
    指定stepの静止画を出力する

    Args:
        ks_file_path: .ksファイルパス
        step_index: 1-based step index
        out_path: 出力PNGパス
        transition_progress: 1.0 renders the settled state. Values below 1.0
            explicitly request an intermediate frame of the selected shift.
    """
    PREVIEW_DEBUG = False
    owns_runtime = runtime is None

    if not 0.0 <= transition_progress <= 1.0:
        raise ValueError("transition_progress must be between 0.0 and 1.0")

    try:
        if runtime is None:
            runtime = create_step_preview_runtime()
        runtime.pop("last_error", None)
        virtual_screen = runtime["virtual_screen"]
        bgm_manager = BGMManager(PREVIEW_DEBUG)
        se_manager = SEManager(PREVIEW_DEBUG)
        dialogue_loader = DialogueLoader(PREVIEW_DEBUG)
        image_manager = runtime["image_manager"]
        text_renderer = TextRenderer(virtual_screen, PREVIEW_DEBUG)
        apply_event_datetime(
            text_renderer,
            event_id=event_id,
            ks_file_path=ks_file_path,
        )
        choice_renderer = ChoiceRenderer(virtual_screen, PREVIEW_DEBUG)
        notification_manager = NotificationManager(virtual_screen, PREVIEW_DEBUG)
        backlog_manager = BacklogManager(virtual_screen, text_renderer.fonts, PREVIEW_DEBUG)
        name_manager = get_name_manager()

        text_renderer.set_backlog_manager(backlog_manager)
        dialogue_loader.notification_system = notification_manager
        name_manager.set_dialogue_loader(dialogue_loader)

        images = runtime["images"]

        raw_dialogue_data = dialogue_loader.load_dialogue_from_ks(ks_file_path)
        if not raw_dialogue_data:
            print(f"エラー: KSファイルの読み込みに失敗しました: {ks_file_path}")
            return False

        from dialogue.data_normalizer import normalize_dialogue_data
        dialogue_data = normalize_dialogue_data(raw_dialogue_data)
        if not dialogue_data:
            print("エラー: データの正規化に失敗しました")
            return False

        ir_data = build_ir_from_normalized(dialogue_data)

        game_state = {
            'dialogue_data': dialogue_data,
            'ir_data': ir_data,
            'ir_step_index': -1,
            'ir_anim_pending': False,
            'ir_anim_end_time': None,
            'ir_active_anims': [],
            'ir_waiting_for_anim': False,
            'ir_fast_forward_until': None,
            'ir_fast_forward_active': False,
            'use_ir': USE_IR,
            'current_paragraph': 0,
            'show_text': True,
            'show_face_parts': True,
            'screen': virtual_screen,
            'bgm_manager': bgm_manager,
            'se_manager': se_manager,
            'dialogue_loader': dialogue_loader,
            'text_renderer': text_renderer,
            'choice_renderer': choice_renderer,
            'notification_manager': notification_manager,
            'backlog_manager': backlog_manager,
            'images': images,
            'image_manager': image_manager,
            'active_characters': [],
            'character_pos': {},
            'character_anim': {},
            'character_zoom': {},
            'character_expressions': {},
            'character_blink_enabled': {},
            'character_blink_state': {},
            'character_blink_timers': {},
            'character_part_fades': {},
            'character_hide_pending': {},
            'background_state': {
                'current_bg': None,
                'zoom': 1.0,
                'pos': [0, 0],
                'anim': None,
            },
            'fade_state': {
                'fading': False,
                'fade_type': None,
                'fade_color': (0, 0, 0),
                'fade_alpha': 0,
                'fade_target_alpha': 0,
                'fade_duration': 0,
                'fade_elapsed': 0,
            },
        }

        steps = (ir_data or {}).get("steps") or []
        visible_step_indices = []
        for idx, step in enumerate(steps):
            if not isinstance(step, dict):
                continue
            actions = step.get("actions") or []
            has_text = bool(step.get("text"))
            if not has_text and actions and all(
                action.get("action") == "scroll_stop" for action in actions
            ):
                continue
            visible_step_indices.append(idx)

        target_visible = max(step_index, 1) - 1
        if not visible_step_indices:
            target_index = -1
        else:
            if target_visible >= len(visible_step_indices):
                target_visible = len(visible_step_indices) - 1
            target_index = visible_step_indices[target_visible]

        text_renderer = game_state.get("text_renderer")
        choice_renderer = game_state.get("choice_renderer")
        target_step = steps[target_index] if target_index >= 0 and target_index < len(steps) else None
        # A normal snapshot represents the state after the selected step has
        # completed. Intermediate transition frames are opt-in.
        preserve_target_transition = 0.0 <= transition_progress < 1.0
        target_shift_fades = {}

        for idx in range(target_index + 1):
            step = steps[idx] if idx < len(steps) else None
            if not isinstance(step, dict):
                continue

            actions = step.get("actions") or []
            for action in actions:
                action_type = action.get("action")
                if action_type in (
                    "choice",
                    "if_start",
                    "if_end",
                    "flag_set",
                    "event_control",
                    "se_play",
                    "bgm_play",
                    "bgm_pause",
                    "bgm_unpause",
                ):
                    continue
                if action_type == "scroll_stop":
                    if text_renderer:
                        text_renderer.set_dialogue("_SCROLL_STOP", None)
                    continue
                _ir_dispatch_action(game_state, action)
                # A still image cannot play a transition. Preserve fades created
                # by the selected chara_shift so the preview can show its middle
                # frame after preceding actions have been settled.
                if (
                    preserve_target_transition
                    and idx == target_index
                    and action_type == "chara_shift"
                ):
                    target = action.get("target")
                    fade_map = game_state.get("character_part_fades", {}).get(target)
                    if fade_map:
                        target_shift_fades[target] = copy.deepcopy(fade_map)

            text = step.get("text")
            if text and text_renderer:
                speaker = text.get("speaker")
                body = text.get("body", "")
                should_scroll = bool(text.get("scroll", False))
                active_characters = game_state.get("active_characters", [])
                if isinstance(active_characters, dict):
                    active_characters = list(active_characters.keys())
                text_renderer.set_dialogue(
                    body,
                    speaker,
                    should_scroll=should_scroll,
                    background=None,
                    active_characters=active_characters,
                    force_female=bool(text.get("force_female", False)),
                )
            elif idx == target_index and text_renderer:
                active_characters = game_state.get("active_characters", [])
                if isinstance(active_characters, dict):
                    active_characters = list(active_characters.keys())
                text_renderer.set_dialogue(
                    "",
                    "",
                    should_scroll=False,
                    background=None,
                    active_characters=active_characters,
                )

        if text_renderer:
            text_renderer.skip_text()
            text_renderer.skip_mode = False
            text_renderer.auto_mode = False

        if isinstance(target_step, dict):
            source_index = target_step.get("source_index")
            if isinstance(source_index, int):
                game_state["current_paragraph"] = source_index

        settle_step_preview_animations(game_state)

        # Restore the selected transition only when an explicit intermediate
        # progress was requested. The default snapshot stays fully settled.
        if target_shift_fades:
            snapshot_time = pygame.time.get_ticks()
            fades = game_state.setdefault("character_part_fades", {})
            for character_name, part_map in target_shift_fades.items():
                fades[character_name] = part_map
                for fade in part_map.values():
                    duration = max(int(fade.get("duration", 0)), 0)
                    fade["start_time"] = (
                        snapshot_time - int(duration * transition_progress)
                    )

        if choice_renderer:
            choice_renderer.hide_choices()

        fade_state = game_state.get("fade_state")
        if isinstance(fade_state, dict) and fade_state.get("type") == "fadeout":
            fade_state["active"] = False
            fade_state["alpha"] = 0

        virtual_screen.fill((0, 0, 0))
        draw_background(game_state)
        draw_characters(game_state)
        draw_fade_overlay(game_state)

        if 'image_manager' in game_state and 'images' in game_state:
            image_manager.draw_ui_elements(virtual_screen, images, game_state.get('show_text', True))

        if game_state.get('show_text', True):
            text_renderer.render()

        # choiceはプレビュー静止画では非表示にする
        notification_manager.update()
        notification_manager.render()
        draw_input_blocked_notice(game_state, virtual_screen)

        output_surface = virtual_screen
        if output_size:
            output_surface = pygame.transform.smoothscale(
                virtual_screen,
                (int(output_size[0]), int(output_size[1])),
            )
        pygame.image.save(output_surface, out_path)
        return True

    except Exception as e:
        error_detail = traceback.format_exc()
        if runtime is not None:
            runtime["last_error"] = error_detail
        print(f"[SNAPSHOT_ERROR] {e}")
        print(error_detail)
        return False
    finally:
        if owns_runtime:
            pygame.quit()

def preview_ks_file(ks_file_path):
    """
    指定されたKSファイルをプレビュー表示する

    Args:
        ks_file_path: プレビューする.ksファイルの絶対パス
    """
    print(f"=== KSファイルプレビュー起動 ===")
    print(f"ファイル: {ks_file_path}")

    # Pygame初期化
    pygame.init()
    pygame.mixer.init()

    # 画面作成（リサイズ可能）
    window_width = 960  # デフォルトサイズ
    window_height = 540
    window = pygame.display.set_mode((window_width, window_height), pygame.RESIZABLE)
    pygame.display.set_caption(f"KSファイル プレビュー - {os.path.basename(ks_file_path)}")

    # 仮想画面作成（4:3固定）
    virtual_screen = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT))

    # エディタ専用設定：OFFSET_X/Yを加算しない
    from core import config as cfg
    cfg.OFFSET_X = 0
    cfg.OFFSET_Y = 0
    cfg.SCALE = 1.0

    clock = pygame.time.Clock()

    # プレビュー専用：DEBUGをオフにしてログを抑制
    PREVIEW_DEBUG = False

    # ゲーム状態の初期化（main.pyと同じフローを使用）
    try:
        print("[INIT] ゲーム状態を初期化中...")

        # 各マネージャーの初期化
        bgm_manager = BGMManager(PREVIEW_DEBUG)
        se_manager = SEManager(PREVIEW_DEBUG)
        dialogue_loader = DialogueLoader(PREVIEW_DEBUG)
        image_manager = ImageManager(DEBUG)
        text_renderer = TextRenderer(virtual_screen, PREVIEW_DEBUG)
        apply_event_datetime(text_renderer, ks_file_path=ks_file_path)
        choice_renderer = ChoiceRenderer(virtual_screen, PREVIEW_DEBUG)
        notification_manager = NotificationManager(virtual_screen, PREVIEW_DEBUG)
        backlog_manager = BacklogManager(virtual_screen, text_renderer.fonts, PREVIEW_DEBUG)
        name_manager = get_name_manager()

        # 相互連携設定
        text_renderer.set_backlog_manager(backlog_manager)
        dialogue_loader.notification_system = notification_manager
        name_manager.set_dialogue_loader(dialogue_loader)

        # 画像ロード
        print("[INIT] 画像をロード中...")
        image_manager.scan_image_paths(VIRTUAL_WIDTH, VIRTUAL_HEIGHT)
        images = image_manager.load_essential_images(VIRTUAL_WIDTH, VIRTUAL_HEIGHT)

        # KSファイルを読み込み
        print(f"[INIT] KSファイルを読み込み中: {ks_file_path}")
        raw_dialogue_data = dialogue_loader.load_dialogue_from_ks(ks_file_path)

        if not raw_dialogue_data:
            print(f"エラー: KSファイルの読み込みに失敗しました: {ks_file_path}")
            return False

        print(f"[INIT] 読み込み成功: {len(raw_dialogue_data)}行")

        # データ正規化（main.pyと同じ）
        from dialogue.data_normalizer import normalize_dialogue_data
        print("[INIT] データを正規化中...")
        dialogue_data = normalize_dialogue_data(raw_dialogue_data)

        ir_data = build_ir_from_normalized(dialogue_data)
        if IR_DUMP_JSON:
            try:
                project_root = os.path.dirname(os.path.abspath(__file__))
                dump_dir = IR_DUMP_DIR
                if not os.path.isabs(dump_dir):
                    dump_dir = os.path.join(project_root, dump_dir)
                dump_ir_json(ir_data, get_ir_dump_path(ks_file_path, dump_dir))
                if DEBUG:
                    print(f"[INIT] IR JSON dumped: {get_ir_dump_path(ks_file_path, dump_dir)}")
            except Exception as e:
                print(f"[INIT] IR JSON dump failed: {e}")

        if not dialogue_data:
            print("エラー: データの正規化に失敗しました")
            return False

        print(f"[INIT] 正規化完了: {len(dialogue_data)}行")

        # キャラクター事前ロード
        try:
            print("[INIT] キャラクター事前ロード中...")
            image_manager.preload_characters_from_dialogue(dialogue_data)
            print("[INIT] キャラクター事前ロード完了")
        except Exception as e:
            print(f"[INIT] キャラクター事前ロードエラー（続行）: {e}")

        # ゲーム状態の構築（main.pyと同じ構造）
        game_state = {
            'dialogue_data': dialogue_data,  # 正規化されたデータを使用
            'ir_data': ir_data,
            'ir_step_index': -1,
            'ir_anim_pending': False,
            'ir_anim_end_time': None,
            'ir_active_anims': [],
            'ir_waiting_for_anim': False,
            'ir_fast_forward_until': None,
        'ir_fast_forward_active': False,
            'use_ir': USE_IR,
            'current_paragraph': 0,
            'show_text': True,
            'show_face_parts': True,
            'screen': virtual_screen,
            'bgm_manager': bgm_manager,
            'se_manager': se_manager,
            'dialogue_loader': dialogue_loader,
            'text_renderer': text_renderer,
            'choice_renderer': choice_renderer,
            'notification_manager': notification_manager,
            'backlog_manager': backlog_manager,
            'images': images,
            'image_manager': image_manager,
            # キャラクター関連
            'active_characters': [],
            'character_pos': {},
            'character_anim': {},
            'character_zoom': {},
            'character_expressions': {},
            'character_blink_enabled': {},
            'character_blink_state': {},
            'character_blink_timers': {},
            'character_part_fades': {},
            'character_hide_pending': {},
            # 背景関連
            'background_state': {
                'current_bg': None,
                'zoom': 1.0,
                'pos': [0, 0],
                'anim': None,
            },
            # フェード関連
            'fade_state': {
                'fading': False,
                'fade_type': None,
                'fade_color': (0, 0, 0),
                'fade_alpha': 0,
                'fade_target_alpha': 0,
                'fade_duration': 0,
                'fade_elapsed': 0,
            },
        }

        print("[INIT] ゲーム状態初期化完了")

    except Exception as e:
        print(f"エラー: ゲーム状態の初期化に失敗しました: {e}")
        import traceback
        traceback.print_exc()
        return False

    # 初期シーンの初期化（main.pyと同じ）
    from dialogue.model import initialize_first_scene
    print("[INIT] 初期シーンを初期化中...")
    initialize_first_scene(game_state)
    print("[INIT] 初期シーン初期化完了")

    # エラーログ抑制フラグ（同じエラーを繰り返さないため）
    error_logged = {
        'background': False,
        'character': False,
        'text': False
    }

    # メインループ
    running = True
    frame_count = 0
    while running:
        frame_count += 1
        # スケーリング情報を計算（マウス座標変換用）
        window_aspect = window_width / window_height
        virtual_aspect = VIRTUAL_WIDTH / VIRTUAL_HEIGHT

        if window_aspect > virtual_aspect:
            # ウィンドウが横長 → 左右にピラーボックス
            scaled_height = window_height
            scaled_width = int(scaled_height * virtual_aspect)
            offset_x = (window_width - scaled_width) // 2
            offset_y = 0
        else:
            # ウィンドウが縦長 → 上下にレターボックス
            scaled_width = window_width
            scaled_height = int(scaled_width / virtual_aspect)
            offset_x = 0
            offset_y = (window_height - scaled_height) // 2

        # VIDEORESIZEのみ先に処理、その他は全てdialogue_handle_events()に任せる
        events_to_repost = []
        for event in pygame.event.get():
            if event.type == pygame.VIDEORESIZE:
                # ウィンドウリサイズ処理
                window_width, window_height = event.size
                window = pygame.display.set_mode((window_width, window_height), pygame.RESIZABLE)
            elif event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
                # マウスイベントの座標を仮想画面座標に変換
                window_mouse_x, window_mouse_y = event.pos

                # ピラーボックス領域外のクリックは無視
                if (window_mouse_x < offset_x or window_mouse_x >= offset_x + scaled_width or
                    window_mouse_y < offset_y or window_mouse_y >= offset_y + scaled_height):
                    continue

                # ウィンドウ座標から仮想画面座標に変換
                relative_x = window_mouse_x - offset_x
                relative_y = window_mouse_y - offset_y
                virtual_x = int(relative_x * VIRTUAL_WIDTH / scaled_width)
                virtual_y = int(relative_y * VIRTUAL_HEIGHT / scaled_height)

                # 新しいイベントを作成（座標を変換）
                new_event = pygame.event.Event(
                    event.type,
                    {'pos': (virtual_x, virtual_y),
                     'button': getattr(event, 'button', None),
                     'buttons': getattr(event, 'buttons', None),
                     'rel': getattr(event, 'rel', None)}
                )
                events_to_repost.append(new_event)
            else:
                # その他のイベント（QUIT含む）は再度キューに戻す
                events_to_repost.append(event)

        # イベントを再投稿
        for event in events_to_repost:
            pygame.event.post(event)

        # dialogueサブシステムのイベント処理（QUITもここで処理される）
        continue_running = dialogue_handle_events(game_state, virtual_screen)
        if not continue_running:
            running = False

        # ゲーム状態の更新（main.pyと同じ）
        from dialogue.controller2 import update_game
        update_game(game_state)

        # 描画処理（仮想画面に描画）
        # 背景描画（エラーログ抑制）
        try:
            # 5フレーム以降はログを抑制（print関数をモンキーパッチ）
            if frame_count > 5:
                import builtins
                original_print = builtins.print
                # [BG]と[IMG_ERROR]のログを抑制する関数
                def silent_print(*args, **kwargs):
                    # 引数を文字列に変換してチェック
                    if args:
                        msg = str(args[0])
                        if '[BG]' in msg or '[IMG_ERROR]' in msg:
                            return  # ログを抑制
                    # それ以外は通常通り出力
                    original_print(*args, **kwargs)

                builtins.print = silent_print
                draw_background(game_state)
                builtins.print = original_print
            else:
                draw_background(game_state)
                if frame_count == 5 and not error_logged['background']:
                    error_logged['background'] = True
                    print("[PREVIEW] 背景エラーログを抑制します (以降このエラーは非表示)")
        except Exception as e:
            if not error_logged['background']:
                print(f"[PREVIEW] draw_background error: {e} (以降このエラーは抑制)")
                error_logged['background'] = True

        # キャラクター描画（エラー回避のためtry-except）
        try:
            draw_characters(game_state)
        except (KeyError, IndexError, TypeError) as e:
            # character_manager.pyがリスト形式を期待しているが、
            # DialogueLoaderは辞書形式を返すため、エラーを無視
            if not error_logged['character']:
                print(f"[PREVIEW] draw_characters warning: {e} (以降このエラーは抑制)")
                error_logged['character'] = True

        draw_fade_overlay(game_state)

        # UI要素描画（テキストボックス、auto/skipボタン等）
        if 'image_manager' in game_state and 'images' in game_state:
            try:
                image_manager = game_state['image_manager']
                images = game_state['images']
                show_text = game_state.get('show_text', True)
                image_manager.draw_ui_elements(virtual_screen, images, show_text)
            except Exception as e:
                if not error_logged.get('ui_elements', False):
                    print(f"[PREVIEW] UI要素描画エラー: {e} (以降このエラーは抑制)")
                    error_logged['ui_elements'] = True

        # テキスト描画（選択肢表示中はトーク文を非表示にし、日付時刻のみ表示）
        if game_state.get('show_text', True):
            if not choice_renderer.is_showing_choices:
                text_renderer.render()
            else:
                text_renderer.render_date()

        # 選択肢描画
        choice_renderer.render()

        # 通知描画
        notification_manager.update()
        notification_manager.render()

        draw_input_blocked_notice(game_state, virtual_screen)

        # 日付表示はtext_renderer.render()内で自動的に処理される

        # バックログ描画
        if backlog_manager.is_showing_backlog():
            backlog_manager.render()

        # 仮想画面を実ウィンドウにスケーリング描画
        # アスペクト比を維持してピラーボックス表示
        window_aspect = window_width / window_height
        virtual_aspect = VIRTUAL_WIDTH / VIRTUAL_HEIGHT

        if window_aspect > virtual_aspect:
            # ウィンドウが横長 → 左右にピラーボックス
            scaled_height = window_height
            scaled_width = int(scaled_height * virtual_aspect)
            offset_x = (window_width - scaled_width) // 2
            offset_y = 0
        else:
            # ウィンドウが縦長 → 上下にレターボックス
            scaled_width = window_width
            scaled_height = int(scaled_width / virtual_aspect)
            offset_x = 0
            offset_y = (window_height - scaled_height) // 2

        # 黒背景でクリア（ピラーボックス用）
        window.fill((0, 0, 0))

        # スケーリングして描画
        scaled_surface = pygame.transform.scale(virtual_screen, (scaled_width, scaled_height))
        window.blit(scaled_surface, (offset_x, offset_y))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    print("プレビュー終了")
    return True

def run_step_preview_server():
    """Render JSON-line requests while keeping Pygame and image caches warm."""
    runtime = None
    try:
        runtime = create_step_preview_runtime()
        print('@@PREVIEW@@{"type":"ready"}', flush=True)
        for line in sys.stdin:
            request = {}
            try:
                request = json.loads(line)
                success = preview_step_image(
                    request["source_path"],
                    int(request["step_index"]),
                    request["out_path"],
                    runtime=runtime,
                    output_size=request.get("output_size"),
                    transition_progress=float(
                        request.get("transition_progress", 1.0)
                    ),
                    event_id=request.get("event_id"),
                )
                result = {
                    "type": "result",
                    "request_id": request.get("request_id"),
                    "success": bool(success),
                    "out_path": request["out_path"],
                    "message": "" if success else "Preview renderer returned an error.",
                }
            except Exception as exc:
                result = {
                    "type": "result",
                    "request_id": request.get("request_id"),
                    "success": False,
                    "out_path": request.get("out_path", ""),
                    "message": f"Preview failed: {exc}",
                }
            print("@@PREVIEW@@" + json.dumps(result, ensure_ascii=False), flush=True)
    finally:
        if runtime is not None:
            pygame.quit()


def main():
    """?????"""
    parser = argparse.ArgumentParser(description="KS?????")
    parser.add_argument("ks_file", nargs="?", help="KS??????")
    parser.add_argument("--step", type=int, default=None, help="1-based step index")
    parser.add_argument("--out", default=None, help="??PNG??")
    parser.add_argument("--server", action="store_true", help="Run persistent step preview server")
    args = parser.parse_args()

    if args.server:
        run_step_preview_server()
        return

    ks_file_path = args.ks_file

    if not ks_file_path or not os.path.exists(ks_file_path):
        print(f"???: ????????????: {ks_file_path}")
        sys.exit(1)

    if not ks_file_path.endswith('.ks'):
        print(f"??: .ks???????????: {ks_file_path}")

    if args.step is not None and args.out:
        success = preview_step_image(ks_file_path, args.step, args.out)
    else:
        success = preview_ks_file(ks_file_path)

    sys.exit(0 if success else 1)

if __name__ == "__main__":

    main()
