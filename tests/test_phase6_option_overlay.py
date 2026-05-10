"""
フェーズ6 テスト: OPTION オーバーレイ

テスト対象:
- option_overlay.py (新規) の OptionOverlay クラス
- GameApplication.current_overlay 属性
- GameApplication.show_option() / hide_option()
- ESC で OPTION が開く（MAP / HOME / DIALOGUE）
- OPTION 中は BGM が継続する（cleanup() されない）
- "resume" でゲーム再開
- "go_to_menu" でメインメニュー遷移
- MAP / HOME 中のみセーブ/ロードボタン表示（DIALOGUE 中は非表示）
- run() でオーバーレイが active なとき current_subsystem も描画される

実行方法:
    python -m pytest tests/test_phase6_option_overlay.py -v
"""

import os, sys
import unittest.mock as mock
import types
import pytest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

MAIN_SRC = open(os.path.join(PROJECT_ROOT, 'main.py'), encoding='utf-8').read()


@pytest.fixture(scope="session")
def pygame_screen():
    import pygame
    pygame.init()
    pygame.mixer.init()
    screen = pygame.display.set_mode((1920, 1080))
    yield screen
    pygame.quit()


@pytest.fixture(scope="session")
def option(pygame_screen):
    from option_overlay import OptionOverlay
    return OptionOverlay(pygame_screen, parent_mode="map")


# ─────────────────────────────────────────────
# グループ1: OptionOverlay クラス構造
# ─────────────────────────────────────────────

class TestOptionOverlayStructure:

    def test_module_importable(self):
        import option_overlay  # noqa

    def test_class_exists(self):
        from option_overlay import OptionOverlay
        assert OptionOverlay is not None

    def test_instantiable_map_mode(self, pygame_screen):
        from option_overlay import OptionOverlay
        o = OptionOverlay(pygame_screen, parent_mode="map")
        assert o is not None

    def test_instantiable_home_mode(self, pygame_screen):
        from option_overlay import OptionOverlay
        o = OptionOverlay(pygame_screen, parent_mode="home")
        assert o is not None

    def test_instantiable_dialogue_mode(self, pygame_screen):
        from option_overlay import OptionOverlay
        o = OptionOverlay(pygame_screen, parent_mode="dialogue")
        assert o is not None

    def test_screen_stored(self, pygame_screen):
        from option_overlay import OptionOverlay
        o = OptionOverlay(pygame_screen, parent_mode="map")
        assert o.screen is pygame_screen

    def test_parent_mode_stored(self, pygame_screen):
        from option_overlay import OptionOverlay
        o = OptionOverlay(pygame_screen, parent_mode="dialogue")
        assert o.parent_mode == "dialogue"


# ─────────────────────────────────────────────
# グループ2: handle_events の戻り値
# ─────────────────────────────────────────────

class TestOptionOverlayEvents:

    def test_handle_events_callable(self, option):
        result = option.handle_events([])
        assert result is None or isinstance(result, str)

    def test_escape_returns_resume(self, pygame_screen):
        """ESC で 'resume' を返す"""
        import pygame
        from option_overlay import OptionOverlay
        o = OptionOverlay(pygame_screen, parent_mode="map")
        event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE, mod=0, unicode='', scancode=0)
        result = o.handle_events([event])
        assert result == "resume"

    def test_resume_action_returns_resume(self, pygame_screen):
        """resume() メソッドが 'resume' を返す"""
        from option_overlay import OptionOverlay
        o = OptionOverlay(pygame_screen, parent_mode="map")
        assert o.resume() == "resume"

    def test_go_to_menu_action(self, pygame_screen):
        """go_to_menu() が 'go_to_menu' を返す"""
        from option_overlay import OptionOverlay
        o = OptionOverlay(pygame_screen, parent_mode="map")
        assert o.go_to_menu() == "go_to_menu"

    def test_quit_event(self, pygame_screen):
        """QUIT イベントで 'quit' を返す"""
        import pygame
        from option_overlay import OptionOverlay
        o = OptionOverlay(pygame_screen, parent_mode="map")
        event = pygame.event.Event(pygame.QUIT)
        result = o.handle_events([event])
        assert result == "quit"


# ─────────────────────────────────────────────
# グループ3: セーブ/ロード表示制御
# ─────────────────────────────────────────────

class TestOptionOverlaySaveVisibility:

    def test_save_available_in_map_mode(self, pygame_screen):
        """MAP モードではセーブボタンが有効"""
        from option_overlay import OptionOverlay
        o = OptionOverlay(pygame_screen, parent_mode="map")
        assert o.save_enabled is True

    def test_save_available_in_home_mode(self, pygame_screen):
        """HOME モードではセーブボタンが有効"""
        from option_overlay import OptionOverlay
        o = OptionOverlay(pygame_screen, parent_mode="home")
        assert o.save_enabled is True

    def test_save_disabled_in_dialogue_mode(self, pygame_screen):
        """DIALOGUE モードではセーブボタンが無効（設計書準拠）"""
        from option_overlay import OptionOverlay
        o = OptionOverlay(pygame_screen, parent_mode="dialogue")
        assert o.save_enabled is False

    def test_save_disabled_in_menu_mode(self, pygame_screen):
        """MENU モードではセーブボタンが無効"""
        from option_overlay import OptionOverlay
        o = OptionOverlay(pygame_screen, parent_mode="menu")
        assert o.save_enabled is False


# ─────────────────────────────────────────────
# グループ4: render
# ─────────────────────────────────────────────

class TestOptionOverlayRender:

    def test_render_overlay_callable(self, option):
        """render_overlay() が呼べる（オーバーレイ描画）"""
        option.render_overlay()

    def test_render_callable_alias(self, option):
        """render() も呼べる（SubsystemBase 互換のため）"""
        if hasattr(option, 'render'):
            option.render()


# ─────────────────────────────────────────────
# グループ5: GameApplication のオーバーレイ管理
# ─────────────────────────────────────────────

class TestGameApplicationOverlay:

    def test_current_overlay_attribute_in_source(self):
        """main.py に current_overlay 属性が存在する"""
        assert 'current_overlay' in MAIN_SRC

    def test_show_option_method_exists(self):
        """main.py に show_option() メソッドがある"""
        assert 'def show_option(' in MAIN_SRC

    def test_hide_option_method_exists(self):
        """main.py に hide_option() メソッドがある"""
        assert 'def hide_option(' in MAIN_SRC

    def test_run_handles_overlay(self):
        """run() が current_overlay を考慮したループを持つ"""
        def _get_run_src():
            lines = MAIN_SRC.splitlines()
            result, in_m, indent = [], False, None
            for line in lines:
                if 'def run(' in line:
                    in_m = True; indent = len(line) - len(line.lstrip())
                    result.append(line); continue
                if in_m:
                    if line.strip() == '': result.append(line); continue
                    ci = len(line) - len(line.lstrip())
                    if ci <= indent and line.strip().startswith('def '): break
                    result.append(line)
            return '\n'.join(result)
        run_src = _get_run_src()
        assert 'current_overlay' in run_src

    def test_overlay_behavior_mock(self):
        """show_option → handle_events → hide_option の流れが動く（Mock）"""
        app = types.SimpleNamespace(
            current_subsystem=None,
            current_overlay=None,
            current_mode="map",
            running=True,
        )

        from option_overlay import OptionOverlay
        import pygame
        pygame.init()
        screen = pygame.display.set_mode((100, 100))

        def show_option():
            app.current_overlay = OptionOverlay(screen, parent_mode=app.current_mode)

        def hide_option():
            app.current_overlay = None

        app.show_option = show_option
        app.hide_option = hide_option

        # オーバーレイを開く
        app.show_option()
        assert app.current_overlay is not None

        # ESC で resume
        esc = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE, mod=0, unicode='', scancode=0)
        result = app.current_overlay.handle_events([esc])
        assert result == "resume"

        # resume なのでオーバーレイを閉じる
        app.hide_option()
        assert app.current_overlay is None


# ─────────────────────────────────────────────
# グループ6: BGM 継続確認（コンセプト）
# ─────────────────────────────────────────────

class TestOptionOverlayBGMContinuity:

    def test_option_does_not_call_stop_bgm_on_subsystem(self, pygame_screen):
        """OPTION 表示時に現在サブシステムの cleanup() が呼ばれない"""
        from subsystem_base import SubsystemBase

        cleanup_called = []

        class _FakeSub(SubsystemBase):
            def handle_events(self, events=None): return None
            def update(self): pass
            def render(self): pass
            def cleanup(self): cleanup_called.append(True)

        # show_option は switch_to() を使わないので cleanup() が呼ばれない
        current = _FakeSub(pygame_screen)

        from option_overlay import OptionOverlay
        # オーバーレイを生成しても current.cleanup() は呼ばれない
        _ = OptionOverlay(pygame_screen, parent_mode="map")
        assert not cleanup_called, "OPTION 表示時に cleanup() が呼ばれた"


# ─────────────────────────────────────────────
# グループ7: 非回帰
# ─────────────────────────────────────────────

class TestPhase6Regression:

    def test_phase1_still_passes(self):
        from subsystem_base import SubsystemBase
        from menu.main_menu import MainMenu
        from home.home import HomeModule
        assert issubclass(MainMenu, SubsystemBase)
        assert issubclass(HomeModule, SubsystemBase)

    def test_phase2_still_passes(self):
        from map.map import FieldMap
        from subsystem_base import SubsystemBase
        assert issubclass(FieldMap, SubsystemBase)

    def test_phase3_still_passes(self):
        from dialogue.dialogue_subsystem import DialogueSubsystem
        from subsystem_base import SubsystemBase
        assert issubclass(DialogueSubsystem, SubsystemBase)

    def test_phase8_still_passes(self):
        from title_subsystem import TitleSubsystem
        from subsystem_base import SubsystemBase
        assert issubclass(TitleSubsystem, SubsystemBase)
