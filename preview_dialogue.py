"""
KSファイル専用プレビュースクリプト
event_editor_mac.pyから別プロセスで起動され、指定された.ksファイルをプレビュー表示する

event_editor.pyのPreviewWindowクラスの実装をベースにしています
"""

import pygame
import sys
import os
from config import *
from dialogue.dialogue_loader import DialogueLoader
from dialogue.text_renderer import TextRenderer
from dialogue.choice_renderer import ChoiceRenderer
from dialogue.character_manager import draw_characters, update_character_animations, init_blink_system
from dialogue.background_manager import draw_background, update_background_animation
from dialogue.notification_manager import NotificationManager
from dialogue.backlog_manager import BacklogManager
from dialogue.name_manager import get_name_manager
from dialogue.controller2 import handle_events as dialogue_handle_events
from dialogue.model import change_bgm
from bgm_manager import BGMManager
from se_manager import SEManager
from image_manager import ImageManager
from path_utils import get_font_path

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
    import config as cfg
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
        image_manager = ImageManager(PREVIEW_DEBUG)
        text_renderer = TextRenderer(virtual_screen, PREVIEW_DEBUG)
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
        # イベント処理：QUITとVIDEORESIZEのみここで処理し、他は全てdialogue_handle_events()に任せる
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.VIDEORESIZE:
                # ウィンドウリサイズ処理
                window_width, window_height = event.size
                window = pygame.display.set_mode((window_width, window_height), pygame.RESIZABLE)
            else:
                # その他のイベントは再度キューに戻す（dialogue_handle_events用）
                pygame.event.post(event)

        # dialogueサブシステムのイベント処理
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

        # テキスト描画
        if game_state.get('show_text', True):
            text_renderer.render()

        # 選択肢描画
        choice_renderer.render()

        # 通知描画
        notification_manager.update()
        notification_manager.render()

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

def main():
    """メイン関数"""
    if len(sys.argv) < 2:
        print("使用方法: python3 preview_dialogue.py <ksファイルパス>")
        sys.exit(1)

    ks_file_path = sys.argv[1]

    if not os.path.exists(ks_file_path):
        print(f"エラー: ファイルが見つかりません: {ks_file_path}")
        sys.exit(1)

    if not ks_file_path.endswith('.ks'):
        print(f"警告: .ksファイルではありません: {ks_file_path}")

    success = preview_ks_file(ks_file_path)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
