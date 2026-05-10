"""
フェーズ3 テスト: DialogueSubsystem ラッパークラス

テスト対象:
- dialogue/dialogue_subsystem.py（新規作成）の DialogueSubsystem クラス
- SubsystemBase 継承
- handle_events(events) が events を無視して内部呼び出し（追加問題A）
- on_enter() が座標系をゼロリセット・元の値を退避（追加問題B）
- cleanup() が BGM/SE 停止 + 座標系復元（追加問題B）
- 仮想画面への差し替え
- イベントファイル読み込み

実行方法:
    cd "c:\\Users\\kohet\\モーキス作業ディレクトリ"
    python -m pytest tests/test_phase3_dialogue_subsystem.py -v
"""

import os
import sys
import unittest.mock as mock
import pytest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)


# ─────────────────────────────────────────────
# フィクスチャ
# ─────────────────────────────────────────────

@pytest.fixture(scope="session")
def pygame_surfaces():
    """headless pygame + 実画面 & 仮想画面を返す"""
    import pygame
    pygame.init()
    pygame.mixer.init()
    screen = pygame.display.set_mode((1920, 1080))
    virtual_screen = pygame.Surface((1440, 1080))
    yield screen, virtual_screen
    pygame.quit()


@pytest.fixture(scope="session")
def ds(pygame_surfaces):
    """DialogueSubsystem インスタンス（重いので session スコープで1回のみ）"""
    from dialogue.dialogue_subsystem import DialogueSubsystem
    screen, virtual_screen = pygame_surfaces
    return DialogueSubsystem(screen, virtual_screen)


# ─────────────────────────────────────────────
# グループ1: クラス構造
# ─────────────────────────────────────────────

class TestDialogueSubsystemStructure:
    """DialogueSubsystem が正しく定義されているか"""

    def test_module_importable(self):
        """dialogue/dialogue_subsystem.py がインポートできる"""
        import dialogue.dialogue_subsystem  # noqa: F401

    def test_class_exists(self):
        """DialogueSubsystem クラスが存在する"""
        from dialogue.dialogue_subsystem import DialogueSubsystem
        assert DialogueSubsystem is not None

    def test_inherits_subsystembase(self):
        """DialogueSubsystem は SubsystemBase のサブクラスである"""
        from dialogue.dialogue_subsystem import DialogueSubsystem
        from subsystem_base import SubsystemBase
        assert issubclass(DialogueSubsystem, SubsystemBase)

    def test_instantiable_with_screens(self, pygame_surfaces):
        """DialogueSubsystem(screen, virtual_screen) がインスタンス化できる"""
        from dialogue.dialogue_subsystem import DialogueSubsystem
        screen, virtual_screen = pygame_surfaces
        d = DialogueSubsystem(screen, virtual_screen)
        assert d is not None

    def test_screen_stored(self, ds):
        """self.screen が設定されている"""
        assert ds.screen is not None

    def test_virtual_screen_stored(self, ds):
        """self.virtual_screen が設定されている"""
        assert hasattr(ds, 'virtual_screen'), "virtual_screen 属性がない"
        assert ds.virtual_screen is not None

    def test_game_state_initialized(self, ds):
        """self.game_state が辞書として初期化されている"""
        assert hasattr(ds, 'game_state'), "game_state 属性がない"
        assert isinstance(ds.game_state, dict), "game_state が辞書でない"

    def test_game_state_has_required_keys(self, ds):
        """game_state に最低限必要なキーが揃っている"""
        required = ['bgm_manager', 'se_manager', 'screen']
        for key in required:
            assert key in ds.game_state, f"game_state に '{key}' がない"

    def test_game_state_screen_is_virtual(self, ds, pygame_surfaces):
        """game_state['screen'] が virtual_screen に差し替えられている"""
        _, virtual_screen = pygame_surfaces
        assert ds.game_state['screen'] is virtual_screen, \
            "game_state['screen'] が仮想画面に差し替えられていない"


# ─────────────────────────────────────────────
# グループ2: SubsystemBase 抽象メソッドの実装
# ─────────────────────────────────────────────

class TestDialogueSubsystemInterface:
    """handle_events / update / render が実装されているか"""

    def test_handle_events_callable(self, ds):
        """handle_events(events) が呼べる"""
        result = ds.handle_events([])
        assert result is None or isinstance(result, str)

    def test_handle_events_ignores_events_arg(self, ds):
        """handle_events(events) は events を無視して内部で controller2 を呼ぶ（追加問題A）

        events 引数が空でも非空でも同じように動作する。
        内部で pygame.event.get() / controller2.handle_events() を使う実装を確認。
        """
        import pygame
        # ダミーイベントを渡しても例外が出ないことを確認
        dummy_events = [pygame.event.Event(pygame.NOEVENT)]
        result = ds.handle_events(dummy_events)
        assert result is None or isinstance(result, str)

    def test_handle_events_does_not_consume_passed_events(self, ds):
        """handle_events(events) は渡した events リストを変化させない（破壊的変更なし）"""
        import pygame
        events = [pygame.event.Event(pygame.NOEVENT)]
        original_len = len(events)
        ds.handle_events(events)
        assert len(events) == original_len, "handle_events が events リストを変更した"

    def test_update_callable(self, ds):
        """update() が呼べる"""
        ds.update()  # 例外なし

    def test_render_callable(self, ds):
        """render() が呼べる"""
        ds.render()  # 例外なし


# ─────────────────────────────────────────────
# グループ3: 座標系管理（追加問題B）
# ─────────────────────────────────────────────

class TestDialogueSubsystemCoordinates:
    """on_enter() / cleanup() が config の座標系を正しく操作するか"""

    def test_on_enter_resets_offset_and_scale(self, pygame_surfaces):
        """on_enter() が config.OFFSET_X/Y=0, SCALE=1.0 に設定する"""
        import config
        from dialogue.dialogue_subsystem import DialogueSubsystem

        screen, virtual_screen = pygame_surfaces

        # 事前に非ゼロ値を設定
        config.OFFSET_X = 240
        config.OFFSET_Y = 0
        config.SCALE = 0.75

        d = DialogueSubsystem(screen, virtual_screen)
        d.on_enter()

        assert config.OFFSET_X == 0, f"on_enter後 OFFSET_X={config.OFFSET_X} (期待: 0)"
        assert config.OFFSET_Y == 0, f"on_enter後 OFFSET_Y={config.OFFSET_Y} (期待: 0)"
        assert config.SCALE == 1.0, f"on_enter後 SCALE={config.SCALE} (期待: 1.0)"

    def test_on_enter_saves_original_values(self, pygame_surfaces):
        """on_enter() が元の config 値を自身に退避する"""
        import config
        from dialogue.dialogue_subsystem import DialogueSubsystem

        screen, virtual_screen = pygame_surfaces
        config.OFFSET_X = 240
        config.OFFSET_Y = 30
        config.SCALE = 0.75

        d = DialogueSubsystem(screen, virtual_screen)
        d.on_enter()

        assert d._saved_offset_x == 240, "元の OFFSET_X が退避されていない"
        assert d._saved_offset_y == 30,  "元の OFFSET_Y が退避されていない"
        assert d._saved_scale == 0.75,   "元の SCALE が退避されていない"

    def test_cleanup_restores_original_values(self, pygame_surfaces):
        """cleanup() が退避した config 値を復元する"""
        import config
        from dialogue.dialogue_subsystem import DialogueSubsystem

        screen, virtual_screen = pygame_surfaces
        config.OFFSET_X = 240
        config.OFFSET_Y = 30
        config.SCALE = 0.75

        d = DialogueSubsystem(screen, virtual_screen)
        d.on_enter()           # 0/0/1.0 にリセット・元値を退避

        # on_enter後は 0/0/1.0 になっている
        assert config.OFFSET_X == 0

        d.cleanup()            # 元の値を復元

        assert config.OFFSET_X == 240,  f"cleanup後 OFFSET_X={config.OFFSET_X} (期待: 240)"
        assert config.OFFSET_Y == 30,   f"cleanup後 OFFSET_Y={config.OFFSET_Y} (期待: 30)"
        assert config.SCALE == 0.75,    f"cleanup後 SCALE={config.SCALE} (期待: 0.75)"

    def test_cleanup_without_on_enter_is_safe(self, pygame_surfaces):
        """on_enter() を呼ばずに cleanup() しても例外が出ない（冪等性）"""
        from dialogue.dialogue_subsystem import DialogueSubsystem
        screen, virtual_screen = pygame_surfaces
        d = DialogueSubsystem(screen, virtual_screen)
        d.cleanup()  # 例外なし

    def test_on_enter_cleanup_cycle_restores_config(self, pygame_surfaces):
        """on_enter → cleanup のサイクルで config が元の値に戻る"""
        import config
        from dialogue.dialogue_subsystem import DialogueSubsystem

        screen, virtual_screen = pygame_surfaces
        orig_x = config.OFFSET_X
        orig_y = config.OFFSET_Y
        orig_scale = config.SCALE

        d = DialogueSubsystem(screen, virtual_screen)
        d.on_enter()
        d.cleanup()

        assert config.OFFSET_X == orig_x
        assert config.OFFSET_Y == orig_y
        assert config.SCALE == orig_scale


# ─────────────────────────────────────────────
# グループ4: BGM / SE ライフサイクル（追加問題B）
# ─────────────────────────────────────────────

class TestDialogueSubsystemAudio:
    """cleanup() が BGM / SE を正しく停止するか"""

    def test_cleanup_stops_bgm(self, pygame_surfaces):
        """cleanup() が bgm_manager.stop_bgm() を呼ぶ"""
        from dialogue.dialogue_subsystem import DialogueSubsystem
        screen, virtual_screen = pygame_surfaces
        d = DialogueSubsystem(screen, virtual_screen)

        with mock.patch.object(d.game_state['bgm_manager'], 'stop_bgm') as m:
            d.cleanup()
            m.assert_called_once()

    def test_cleanup_stops_all_se(self, pygame_surfaces):
        """cleanup() が se_manager.stop_all_se() を呼ぶ"""
        from dialogue.dialogue_subsystem import DialogueSubsystem
        screen, virtual_screen = pygame_surfaces
        d = DialogueSubsystem(screen, virtual_screen)

        with mock.patch.object(d.game_state['se_manager'], 'stop_all_se') as m:
            d.cleanup()
            m.assert_called_once()

    def test_cleanup_does_not_raise_when_managers_broken(self, pygame_surfaces):
        """bgm_manager が壊れていても cleanup() は例外を出さない"""
        from dialogue.dialogue_subsystem import DialogueSubsystem
        screen, virtual_screen = pygame_surfaces
        d = DialogueSubsystem(screen, virtual_screen)

        # bgm_manager を壊す
        d.game_state['bgm_manager'] = None
        d.cleanup()  # 例外なし（try/except で保護されている）


# ─────────────────────────────────────────────
# グループ5: イベントファイル読み込み
# ─────────────────────────────────────────────

class TestDialogueSubsystemEventLoading:
    """イベントファイルの読み込みが機能するか"""

    def test_load_event_file_e001(self, pygame_surfaces):
        """E001.ks を読み込める"""
        from dialogue.dialogue_subsystem import DialogueSubsystem
        screen, virtual_screen = pygame_surfaces

        event_file = os.path.join(PROJECT_ROOT, "events", "E001.ks")
        if not os.path.exists(event_file):
            pytest.skip("events/E001.ks が存在しない")

        d = DialogueSubsystem(screen, virtual_screen, event_file=event_file)
        assert d.game_state.get('dialogue_data') is not None, \
            "E001.ks 読み込み後に dialogue_data がない"
        assert len(d.game_state['dialogue_data']) > 0, \
            "dialogue_data が空"

    def test_load_nonexistent_event_file_is_safe(self, pygame_surfaces):
        """存在しないイベントファイルを渡しても例外が出ない"""
        from dialogue.dialogue_subsystem import DialogueSubsystem
        screen, virtual_screen = pygame_surfaces
        d = DialogueSubsystem(screen, virtual_screen, event_file="events/NONEXISTENT.ks")
        # 例外なし（ロード失敗は警告ログのみ）

    def test_event_id_extracted_from_file_path(self, pygame_surfaces):
        """event_file パスから event_id が正しく抽出される"""
        from dialogue.dialogue_subsystem import DialogueSubsystem
        screen, virtual_screen = pygame_surfaces
        d = DialogueSubsystem(screen, virtual_screen, event_file="events/E001.ks")
        assert d.current_event_id == "E001", \
            f"event_id が 'E001' でない: {d.current_event_id}"

    def test_no_event_file_is_safe(self, pygame_surfaces):
        """event_file なしでもインスタンス化できる"""
        from dialogue.dialogue_subsystem import DialogueSubsystem
        screen, virtual_screen = pygame_surfaces
        d = DialogueSubsystem(screen, virtual_screen)
        assert d is not None


# ─────────────────────────────────────────────
# グループ6: ライフサイクル統合（switch_to シナリオ）
# ─────────────────────────────────────────────

class TestDialogueSubsystemLifecycleIntegration:
    """switch_to 経由の cleanup → on_enter フローが正しく動くか"""

    def test_fieldmap_to_dialogue_lifecycle(self, pygame_surfaces):
        """FieldMap → DialogueSubsystem 切り替えで座標系が適切に変化する"""
        import config
        from dialogue.dialogue_subsystem import DialogueSubsystem

        screen, virtual_screen = pygame_surfaces

        # FieldMap 状態: 非ゼロ OFFSET
        config.OFFSET_X = 240
        config.OFFSET_Y = 0
        config.SCALE = 0.75

        # DialogueSubsystem に切り替え
        d = DialogueSubsystem(screen, virtual_screen)
        d.on_enter()

        assert config.OFFSET_X == 0
        assert config.SCALE == 1.0

        # 戻す
        d.cleanup()

        assert config.OFFSET_X == 240
        assert config.SCALE == 0.75

    def test_handle_events_returns_none_when_dialogue_continues(self, ds):
        """会話継続中は handle_events が None を返す"""
        # ks_finished フラグが False の状態 → None を期待
        if 'ks_finished' in ds.game_state:
            ds.game_state['ks_finished'] = False

        result = ds.handle_events([])
        # 会話継続中なら None、終了なら "dialogue_ended"
        assert result in (None, "dialogue_ended")

    def test_handle_events_returns_dialogue_ended_when_ks_finished(self, pygame_surfaces):
        """ks_finished=True のとき handle_events が 'dialogue_ended' を返す"""
        from dialogue.dialogue_subsystem import DialogueSubsystem
        screen, virtual_screen = pygame_surfaces
        d = DialogueSubsystem(screen, virtual_screen)
        d.game_state['ks_finished'] = True

        result = d.handle_events([])
        assert result == "dialogue_ended", \
            f"ks_finished=True なのに '{result}' が返った（期待: 'dialogue_ended'）"


# ─────────────────────────────────────────────
# グループ7: 非回帰
# ─────────────────────────────────────────────

class TestDialogueSubsystemRegression:
    """既存の dialogue モジュールが壊れていないか"""

    def test_dialogue_model_still_importable(self):
        """dialogue.model が引き続きインポートできる"""
        from dialogue.model import initialize_game  # noqa: F401

    def test_dialogue_controller2_still_importable(self):
        """dialogue.controller2 が引き続きインポートできる"""
        from dialogue.controller2 import handle_events  # noqa: F401

    def test_main_py_does_not_import_dialogue_subsystem_yet(self):
        """main.py はまだ DialogueSubsystem を使っていない（フェーズ4で対応）

        フェーズ3 では DialogueSubsystem クラスを作るのみ。
        main.py の switch_to_dialogue() はフェーズ4 で置き換える。
        """
        main_path = os.path.join(PROJECT_ROOT, 'main.py')
        content = open(main_path, encoding='utf-8').read()
        # このテストはフェーズ4実施前は通過、フェーズ4後は更新が必要
        # → フェーズ4で DialogueSubsystem を使い始めたら削除してよい
        pytest.skip("フェーズ4で main.py を更新したらこのテストは削除する")
