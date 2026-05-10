"""
フェーズ2 テスト: AdvancedKimikissMap → FieldMap リネーム + SubsystemBase 継承

テスト対象:
- map/map.py の FieldMap クラス
- SubsystemBase 継承
- __init__(screen=None) 対応（追加問題C）
- cleanup() でBGM停止
- on_enter() でBGM再生
- 既存機能の非回帰

実行方法:
    cd "c:\\Users\\kohet\\モーキス作業ディレクトリ"
    python -m pytest tests/test_phase2_fieldmap.py -v
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
def pygame_screen():
    """headless pygame セッション（FieldMapは display.get_surface() を使うため必須）"""
    import pygame
    pygame.init()
    pygame.mixer.init()
    screen = pygame.display.set_mode((1440, 1080))
    yield screen
    pygame.quit()


@pytest.fixture(scope="session")
def fieldmap(pygame_screen):
    """FieldMap インスタンス（重いので session スコープで1回だけ生成）"""
    from map.map import FieldMap
    return FieldMap(pygame_screen)


# ─────────────────────────────────────────────
# グループ1: クラスリネームの確認
# ─────────────────────────────────────────────

class TestFieldMapRename:
    """AdvancedKimikissMap → FieldMap のリネームが正しく行われているか"""

    def test_fieldmap_importable(self):
        """FieldMap が map.map からインポートできる"""
        from map.map import FieldMap
        assert FieldMap is not None

    def test_old_name_not_exported(self):
        """AdvancedKimikissMap という名前が残っていない"""
        import map.map as map_module
        assert not hasattr(map_module, 'AdvancedKimikissMap'), \
            "AdvancedKimikissMap がまだ残っている（削除またはエイリアス解除が必要）"

    def test_class_name_is_fieldmap(self):
        """クラスの __name__ が FieldMap である"""
        from map.map import FieldMap
        assert FieldMap.__name__ == 'FieldMap'


# ─────────────────────────────────────────────
# グループ2: SubsystemBase 継承
# ─────────────────────────────────────────────

class TestFieldMapInheritance:
    """FieldMap が SubsystemBase を正しく継承しているか"""

    def test_inherits_subsystembase(self):
        """FieldMap は SubsystemBase のサブクラスである"""
        from map.map import FieldMap
        from subsystem_base import SubsystemBase
        assert issubclass(FieldMap, SubsystemBase), \
            "FieldMap が SubsystemBase を継承していない"

    def test_init_accepts_screen_arg(self, pygame_screen):
        """FieldMap(screen) が screen 引数ありでインスタンス化できる（追加問題C対応）"""
        from map.map import FieldMap
        fm = FieldMap(pygame_screen)
        assert fm is not None
        assert fm.screen is pygame_screen

    def test_init_screen_none_uses_display(self, pygame_screen):
        """FieldMap(screen=None) が pygame.display.get_surface() にフォールバックする"""
        from map.map import FieldMap
        fm = FieldMap()   # screen 引数なし
        assert fm.screen is not None

    def test_handle_events_implemented(self, fieldmap):
        """handle_events(events) が実装されている"""
        result = fieldmap.handle_events([])
        assert result is None or isinstance(result, str)

    def test_update_implemented(self, fieldmap):
        """update() が実装されている"""
        fieldmap.update()  # 例外なし

    def test_render_implemented(self, fieldmap):
        """render() が実装されている"""
        fieldmap.render()  # 例外なし


# ─────────────────────────────────────────────
# グループ3: cleanup() / on_enter() の動作
# ─────────────────────────────────────────────

class TestFieldMapLifecycle:
    """cleanup() / on_enter() が BGM を正しく制御するか"""

    def test_cleanup_method_exists(self, fieldmap):
        """cleanup() メソッドが存在する"""
        assert hasattr(fieldmap, 'cleanup'), "cleanup() が実装されていない"
        assert callable(fieldmap.cleanup)

    def test_on_enter_method_exists(self, fieldmap):
        """on_enter() メソッドが存在する"""
        assert hasattr(fieldmap, 'on_enter'), "on_enter() が実装されていない"
        assert callable(fieldmap.on_enter)

    def test_cleanup_stops_bgm(self, pygame_screen):
        """cleanup() を呼ぶと bgm_manager.stop_bgm() が呼ばれる"""
        from map.map import FieldMap
        fm = FieldMap(pygame_screen)

        with mock.patch.object(fm.bgm_manager, 'stop_bgm') as mock_stop:
            fm.cleanup()
            mock_stop.assert_called_once(), "cleanup() が stop_bgm() を呼んでいない"

    def test_on_enter_starts_bgm(self, pygame_screen):
        """on_enter() を呼ぶと BGM 再生処理が実行される"""
        from map.map import FieldMap
        fm = FieldMap(pygame_screen)

        with mock.patch.object(fm, 'update_bgm') as mock_bgm:
            fm.on_enter()
            mock_bgm.assert_called(), "on_enter() が update_bgm() を呼んでいない"

    def test_cleanup_does_not_raise(self, fieldmap):
        """cleanup() が例外を出さない"""
        # bgm が停止済みの状態でも安全に呼べる
        fieldmap.cleanup()  # 例外なし

    def test_on_enter_does_not_raise(self, fieldmap):
        """on_enter() が例外を出さない"""
        fieldmap.on_enter()  # 例外なし


# ─────────────────────────────────────────────
# グループ4: ライフサイクル統合（switch_to シナリオ）
# ─────────────────────────────────────────────

class TestFieldMapLifecycleIntegration:
    """switch_to() 経由の cleanup → on_enter フローが正しく動くか"""

    def test_switch_from_fieldmap_calls_cleanup(self, pygame_screen):
        """FieldMap から別サブシステムに切り替えると cleanup() が呼ばれる"""
        from map.map import FieldMap
        from subsystem_base import SubsystemBase

        class _DummySub(SubsystemBase):
            def handle_events(self, events): return None
            def update(self): pass
            def render(self): pass

        fm = FieldMap(pygame_screen)
        cleanup_called = []
        original_cleanup = fm.cleanup

        def tracked_cleanup():
            cleanup_called.append(True)
            original_cleanup()

        fm.cleanup = tracked_cleanup

        # switch_to の最小実装
        current = fm
        current.cleanup()
        next_sub = _DummySub(pygame_screen)
        next_sub.on_enter()

        assert cleanup_called, "FieldMap.cleanup() が呼ばれていない"

    def test_switch_to_fieldmap_calls_on_enter(self, pygame_screen):
        """FieldMap に切り替えると on_enter() が呼ばれ BGM が開始される"""
        from map.map import FieldMap

        fm = FieldMap(pygame_screen)
        with mock.patch.object(fm, 'update_bgm') as mock_bgm:
            fm.on_enter()
            assert mock_bgm.called, "on_enter() が update_bgm() を呼んでいない"

    def test_double_cleanup_safe(self, pygame_screen):
        """cleanup() を2回呼んでも例外が出ない（冪等性）"""
        from map.map import FieldMap
        fm = FieldMap(pygame_screen)
        fm.cleanup()
        fm.cleanup()  # 2回目も安全


# ─────────────────────────────────────────────
# グループ5: 既存機能の非回帰
# ─────────────────────────────────────────────

class TestFieldMapRegression:
    """リネーム・継承追加後も既存機能が壊れていないか"""

    def test_module_importable(self):
        """map/map.py がインポートできる"""
        import map.map  # noqa: F401

    def test_bgm_manager_exists(self, fieldmap):
        """bgm_manager 属性が存在する"""
        assert hasattr(fieldmap, 'bgm_manager'), "bgm_manager がない"

    def test_update_events_callable(self, fieldmap):
        """update_events() が呼べる（イベントリスト更新）"""
        fieldmap.update_events()  # 例外なし

    def test_handle_event_singular_callable(self, fieldmap):
        """handle_event(event) （単数形）が残っている（main.py 互換）"""
        assert hasattr(fieldmap, 'handle_event'), \
            "handle_event() が消えている（main.py が呼んでいるため必須）"

    def test_main_py_import_uses_fieldmap(self):
        """main.py が FieldMap をインポートしている（AdvancedKimikissMap ではない）"""
        main_path = os.path.join(PROJECT_ROOT, 'main.py')
        content = open(main_path, encoding='utf-8').read()
        assert 'FieldMap' in content, "main.py が FieldMap をインポートしていない"
        assert 'AdvancedKimikissMap' not in content, \
            "main.py にまだ AdvancedKimikissMap が残っている"

    def test_subsystem_base_comment_updated(self):
        """subsystem_base.py のコメントが FieldMap を参照している"""
        base_path = os.path.join(PROJECT_ROOT, 'subsystem_base.py')
        content = open(base_path, encoding='utf-8').read()
        assert 'AdvancedKimikissMap' not in content, \
            "subsystem_base.py のコメントが更新されていない"

    def test_screen_attribute_set_correctly(self, pygame_screen):
        """self.screen が渡した screen と同じオブジェクトである"""
        from map.map import FieldMap
        fm = FieldMap(pygame_screen)
        assert fm.screen is pygame_screen
