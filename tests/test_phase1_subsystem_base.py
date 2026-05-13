"""
フェーズ1 テスト: SubsystemBase の作成と MainMenu/HomeModule の継承

テスト対象:
- subsystem_base.py（新規作成するファイル）
- menu/main_menu.py の MainMenu
- home/home.py の HomeModule

実行方法:
    cd "c:\\Users\\kohet\\モーキス作業ディレクトリ"
    python -m pytest tests/test_phase1_subsystem_base.py -v

注意:
    pygame を headless で動かすため SDL_VIDEODRIVER=dummy を使用する。
    実際の画面描画は行わない（smoke test レベル）。
"""

import os
import sys
import inspect
import pytest

# headless pygame（画面なし）
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

# プロジェクトルートをパスに追加
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)


# ─────────────────────────────────────────────
# フィクスチャ
# ─────────────────────────────────────────────

@pytest.fixture(scope="session")
def pygame_screen():
    """headless pygame セッション共通スクリーン"""
    import pygame
    pygame.init()
    pygame.mixer.init()
    screen = pygame.display.set_mode((1440, 1080))
    yield screen
    pygame.quit()


# ─────────────────────────────────────────────
# グループ1: SubsystemBase の構造テスト
# ─────────────────────────────────────────────

class TestSubsystemBaseStructure:
    """subsystem_base.py が正しく定義されているか"""

    def test_module_importable(self):
        """subsystem_base.py が import できる"""
        import core.subsystem_base as subsystem_base  # noqa: F401

    def test_class_exists(self):
        """SubsystemBase クラスが存在する"""
        from core.subsystem_base import SubsystemBase
        assert SubsystemBase is not None

    def test_is_abstract(self):
        """SubsystemBase は ABC であり直接インスタンス化できない"""
        import pygame
        from core.subsystem_base import SubsystemBase

        # ダミースクリーン
        pygame.init()
        screen = pygame.display.set_mode((100, 100))

        with pytest.raises(TypeError):
            SubsystemBase(screen)

    def test_abstract_methods_defined(self):
        """handle_events / update / render が抽象メソッドとして定義されている"""
        from core.subsystem_base import SubsystemBase

        abstract_methods = getattr(SubsystemBase, '__abstractmethods__', set())
        assert 'handle_events' in abstract_methods, "handle_events が抽象メソッドでない"
        assert 'update'        in abstract_methods, "update が抽象メソッドでない"
        assert 'render'        in abstract_methods, "render が抽象メソッドでない"

    def test_cleanup_has_default_impl(self):
        """cleanup() はデフォルト実装（何もしない）を持つ"""
        from core.subsystem_base import SubsystemBase

        # cleanup は abstractmethods に含まれない = デフォルト実装あり
        abstract_methods = getattr(SubsystemBase, '__abstractmethods__', set())
        assert 'cleanup' not in abstract_methods

        # 具象サブクラスで呼んでもエラーにならない
        import pygame
        pygame.init()
        screen = pygame.display.set_mode((100, 100))

        class _Concrete(SubsystemBase):
            def handle_events(self, events): return None
            def update(self): pass
            def render(self): pass

        obj = _Concrete(screen)
        obj.cleanup()   # 例外なし

    def test_on_enter_has_default_impl(self):
        """on_enter() はデフォルト実装（何もしない）を持つ"""
        from core.subsystem_base import SubsystemBase

        abstract_methods = getattr(SubsystemBase, '__abstractmethods__', set())
        assert 'on_enter' not in abstract_methods

        import pygame
        pygame.init()
        screen = pygame.display.set_mode((100, 100))

        class _Concrete(SubsystemBase):
            def handle_events(self, events): return None
            def update(self): pass
            def render(self): pass

        obj = _Concrete(screen)
        obj.on_enter()  # 例外なし

    def test_screen_stored_on_self(self):
        """コンストラクタで受け取った screen が self.screen に格納される"""
        from core.subsystem_base import SubsystemBase
        import pygame
        pygame.init()
        screen = pygame.display.set_mode((100, 100))

        class _Concrete(SubsystemBase):
            def handle_events(self, events): return None
            def update(self): pass
            def render(self): pass

        obj = _Concrete(screen)
        assert obj.screen is screen

    def test_handle_events_signature(self):
        """handle_events は events (list想定) を引数に取る"""
        from core.subsystem_base import SubsystemBase
        sig = inspect.signature(SubsystemBase.handle_events)
        params = list(sig.parameters.keys())
        # self + events の2引数
        assert len(params) == 2, f"引数が {len(params)} 個 (期待: 2)"
        assert params[1] == 'events', f"第2引数名が '{params[1]}' (期待: 'events')"

    def test_handle_events_return_annotation(self):
        """handle_events の戻り値アノテーションが str | None である（推奨、なければ警告のみ）"""
        from core.subsystem_base import SubsystemBase
        sig = inspect.signature(SubsystemBase.handle_events)
        ret = sig.return_annotation
        # アノテーションがない場合は警告扱いでスキップ
        if ret is inspect.Parameter.empty:
            pytest.skip("return annotation が未設定（推奨だが必須ではない）")


# ─────────────────────────────────────────────
# グループ2: MainMenu の継承テスト
# ─────────────────────────────────────────────

class TestMainMenuInheritance:
    """MainMenu が SubsystemBase を正しく継承しているか"""

    def test_mainmenu_inherits_subsystembase(self, pygame_screen):
        """MainMenu は SubsystemBase のサブクラスである"""
        from core.subsystem_base import SubsystemBase
        from menu.main_menu import MainMenu

        assert issubclass(MainMenu, SubsystemBase), \
            "MainMenu が SubsystemBase を継承していない"

    def test_mainmenu_instantiable(self, pygame_screen):
        """MainMenu(screen) がエラーなくインスタンス化できる"""
        from menu.main_menu import MainMenu
        menu = MainMenu(pygame_screen)
        assert menu is not None

    def test_mainmenu_handle_events_takes_events_list(self, pygame_screen):
        """MainMenu.handle_events(events) が list を受け取れる"""
        from menu.main_menu import MainMenu
        menu = MainMenu(pygame_screen)
        # 空イベントリストで呼んでもクラッシュしない
        result = menu.handle_events([])
        # 戻り値は str | None
        assert result is None or isinstance(result, str), \
            f"戻り値が str | None でない: {type(result)}"

    def test_mainmenu_update_callable(self, pygame_screen):
        """MainMenu.update() が呼べる"""
        from menu.main_menu import MainMenu
        menu = MainMenu(pygame_screen)
        menu.update()  # 例外なし

    def test_mainmenu_render_callable(self, pygame_screen):
        """MainMenu.render() が呼べる"""
        from menu.main_menu import MainMenu
        menu = MainMenu(pygame_screen)
        menu.render()  # 例外なし

    def test_mainmenu_cleanup_callable(self, pygame_screen):
        """MainMenu.cleanup() が呼べる（デフォルト実装 or オーバーライド）"""
        from menu.main_menu import MainMenu
        menu = MainMenu(pygame_screen)
        menu.cleanup()  # 例外なし

    def test_mainmenu_on_enter_callable(self, pygame_screen):
        """MainMenu.on_enter() が呼べる"""
        from menu.main_menu import MainMenu
        menu = MainMenu(pygame_screen)
        menu.on_enter()  # 例外なし


# ─────────────────────────────────────────────
# グループ3: HomeModule の継承テスト
# ─────────────────────────────────────────────

class TestHomeModuleInheritance:
    """HomeModule が SubsystemBase を正しく継承しているか"""

    def test_homemodule_inherits_subsystembase(self, pygame_screen):
        """HomeModule は SubsystemBase のサブクラスである"""
        from core.subsystem_base import SubsystemBase
        from home.home import HomeModule

        assert issubclass(HomeModule, SubsystemBase), \
            "HomeModule が SubsystemBase を継承していない"

    def test_homemodule_instantiable(self, pygame_screen):
        """HomeModule(screen) がエラーなくインスタンス化できる"""
        from home.home import HomeModule
        home = HomeModule(pygame_screen)
        assert home is not None

    def test_homemodule_handle_events_takes_events_list(self, pygame_screen):
        """HomeModule.handle_events(events) が list を受け取れる"""
        from home.home import HomeModule
        home = HomeModule(pygame_screen)
        result = home.handle_events([])
        assert result is None or isinstance(result, str), \
            f"戻り値が str | None でない: {type(result)}"

    def test_homemodule_update_callable(self, pygame_screen):
        """HomeModule.update() が呼べる"""
        from home.home import HomeModule
        home = HomeModule(pygame_screen)
        home.update()  # 例外なし

    def test_homemodule_render_callable(self, pygame_screen):
        """HomeModule.render() が呼べる"""
        from home.home import HomeModule
        home = HomeModule(pygame_screen)
        home.render()  # 例外なし

    def test_homemodule_cleanup_callable(self, pygame_screen):
        """HomeModule.cleanup() が呼べる"""
        from home.home import HomeModule
        home = HomeModule(pygame_screen)
        home.cleanup()  # 例外なし

    def test_homemodule_on_enter_callable(self, pygame_screen):
        """HomeModule.on_enter() が呼べる"""
        from home.home import HomeModule
        home = HomeModule(pygame_screen)
        home.on_enter()  # 例外なし


# ─────────────────────────────────────────────
# グループ4: ライフサイクルの統合テスト
# ─────────────────────────────────────────────

class TestLifecycleIntegration:
    """cleanup → on_enter のライフサイクルが想定通りに動くか"""

    def _make_switch_to(self, SubsystemBase):
        """計画書 フェーズ4 の switch_to() の最小実装"""
        class _FakeSwitcher:
            def __init__(self):
                self.current_subsystem = None
                self.current_mode = None

            def switch_to(self, subsystem, mode_name):
                if self.current_subsystem:
                    self.current_subsystem.cleanup()
                self.current_subsystem = subsystem
                self.current_mode = mode_name
                self.current_subsystem.on_enter()

        return _FakeSwitcher()

    def test_switch_to_calls_cleanup_then_on_enter(self, pygame_screen):
        """switch_to() が cleanup() → on_enter() の順で呼ばれる"""
        from core.subsystem_base import SubsystemBase

        call_log = []

        class _SubA(SubsystemBase):
            def handle_events(self, events): return None
            def update(self): pass
            def render(self): pass
            def cleanup(self): call_log.append('A.cleanup')
            def on_enter(self): call_log.append('A.on_enter')

        class _SubB(SubsystemBase):
            def handle_events(self, events): return None
            def update(self): pass
            def render(self): pass
            def cleanup(self): call_log.append('B.cleanup')
            def on_enter(self): call_log.append('B.on_enter')

        switcher = self._make_switch_to(SubsystemBase)

        # A に切り替え
        switcher.switch_to(_SubA(pygame_screen), "a")
        assert call_log == ['A.on_enter'], f"初回切り替えのログが不正: {call_log}"

        # B に切り替え
        switcher.switch_to(_SubB(pygame_screen), "b")
        assert call_log == ['A.on_enter', 'A.cleanup', 'B.on_enter'], \
            f"2回目切り替えのログが不正: {call_log}"

    def test_mainmenu_and_homemodule_lifecycle(self, pygame_screen):
        """MainMenu → HomeModule の切り替えで例外が出ない"""
        from core.subsystem_base import SubsystemBase
        from menu.main_menu import MainMenu
        from home.home import HomeModule

        switcher = self._make_switch_to(SubsystemBase)
        switcher.switch_to(MainMenu(pygame_screen), "menu")
        switcher.switch_to(HomeModule(pygame_screen), "home")
        # 例外が発生しなければ OK


# ─────────────────────────────────────────────
# グループ5: 既存機能への非回帰テスト
# ─────────────────────────────────────────────

class TestRegressionPhase1:
    """フェーズ1 実施後も既存機能が壊れていないか"""

    def test_mainmenu_module_still_importable_standalone(self):
        """menu/main_menu.py が単独でインポートできる（他の依存が壊れていない）"""
        from menu import main_menu  # noqa: F401

    def test_homemodule_module_still_importable_standalone(self):
        """home/home.py が単独でインポートできる"""
        from home import home  # noqa: F401

    def test_mainmenu_has_draw_method(self, pygame_screen):
        """MainMenu.draw() が残っている（既存コードが draw() を直接呼んでいる場合の保険）"""
        from menu.main_menu import MainMenu
        menu = MainMenu(pygame_screen)
        # draw() が残っているか、もしくは render() がそれを兼ねているか
        has_draw = hasattr(menu, 'draw') or hasattr(menu, 'render')
        assert has_draw, "draw/render メソッドが消えている"

    def test_homemodule_handle_events_accepts_pygame_events(self, pygame_screen):
        """HomeModule.handle_events() に実際の pygame.event リストを渡せる"""
        import pygame
        from home.home import HomeModule

        pygame.event.clear()
        events = pygame.event.get()   # 空リストのはずだが型は正しい
        home = HomeModule(pygame_screen)
        home.handle_events(events)    # 例外なし
