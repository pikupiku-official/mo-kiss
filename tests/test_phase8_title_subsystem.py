"""
フェーズ8 テスト: TitleSubsystem

テスト対象:
- title_subsystem.py (新規) の TitleSubsystem クラス
- SubsystemBase 継承
- handle_events() が任意キー/クリックで "go_to_menu" を返す
- QUIT イベントで "quit" を返す
- on_enter() が BGM 再生
- cleanup() が BGM 停止
- main.py が show_title_screen() ではなく TitleSubsystem を使う

実行方法:
    python -m pytest tests/test_phase8_title_subsystem.py -v
"""

import os, sys
import unittest.mock as mock
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


# ─────────────────────────────────────────────
# グループ1: クラス構造
# ─────────────────────────────────────────────

class TestTitleSubsystemStructure:

    def test_module_importable(self):
        import core.title_subsystem as title_subsystem  # noqa

    def test_class_exists(self):
        from core.title_subsystem import TitleSubsystem
        assert TitleSubsystem is not None

    def test_inherits_subsystembase(self):
        from core.title_subsystem import TitleSubsystem
        from core.subsystem_base import SubsystemBase
        assert issubclass(TitleSubsystem, SubsystemBase)

    def test_instantiable(self, pygame_screen):
        from core.title_subsystem import TitleSubsystem
        ts = TitleSubsystem(pygame_screen)
        assert ts is not None

    def test_screen_stored(self, pygame_screen):
        from core.title_subsystem import TitleSubsystem
        ts = TitleSubsystem(pygame_screen)
        assert ts.screen is pygame_screen


# ─────────────────────────────────────────────
# グループ2: SubsystemBase I/F 実装
# ─────────────────────────────────────────────

class TestTitleSubsystemInterface:

    def test_handle_events_callable(self, pygame_screen):
        from core.title_subsystem import TitleSubsystem
        ts = TitleSubsystem(pygame_screen)
        result = ts.handle_events([])
        assert result is None or isinstance(result, str)

    def test_keydown_returns_go_to_menu(self, pygame_screen):
        """任意のキー押下で 'go_to_menu' を返す"""
        import pygame
        from core.title_subsystem import TitleSubsystem
        ts = TitleSubsystem(pygame_screen)
        event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN, mod=0, unicode='', scancode=0)
        result = ts.handle_events([event])
        assert result == "go_to_menu"

    def test_mousebuttondown_returns_go_to_menu(self, pygame_screen):
        """マウスクリックで 'go_to_menu' を返す"""
        import pygame
        from core.title_subsystem import TitleSubsystem
        ts = TitleSubsystem(pygame_screen)
        event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(960, 540))
        result = ts.handle_events([event])
        assert result == "go_to_menu"

    def test_quit_returns_quit(self, pygame_screen):
        """QUIT イベントで 'quit' を返す"""
        import pygame
        from core.title_subsystem import TitleSubsystem
        ts = TitleSubsystem(pygame_screen)
        event = pygame.event.Event(pygame.QUIT)
        result = ts.handle_events([event])
        assert result == "quit"

    def test_no_input_returns_none(self, pygame_screen):
        """入力なしで None を返す"""
        from core.title_subsystem import TitleSubsystem
        ts = TitleSubsystem(pygame_screen)
        result = ts.handle_events([])
        assert result is None

    def test_update_callable(self, pygame_screen):
        from core.title_subsystem import TitleSubsystem
        ts = TitleSubsystem(pygame_screen)
        ts.update()

    def test_render_callable(self, pygame_screen):
        from core.title_subsystem import TitleSubsystem
        ts = TitleSubsystem(pygame_screen)
        ts.render()


# ─────────────────────────────────────────────
# グループ3: BGM ライフサイクル
# ─────────────────────────────────────────────

class TestTitleSubsystemBGM:

    def test_on_enter_plays_bgm(self, pygame_screen):
        """on_enter() が BGM 再生を試みる"""
        from core.title_subsystem import TitleSubsystem
        ts = TitleSubsystem(pygame_screen)
        with mock.patch.object(ts, '_play_bgm') as m:
            ts.on_enter()
            m.assert_called_once()

    def test_cleanup_stops_bgm(self, pygame_screen):
        """cleanup() が BGM 停止を試みる"""
        from core.title_subsystem import TitleSubsystem
        ts = TitleSubsystem(pygame_screen)
        with mock.patch.object(ts, '_stop_bgm') as m:
            ts.cleanup()
            m.assert_called_once()

    def test_cleanup_safe_without_on_enter(self, pygame_screen):
        """on_enter() なしで cleanup() しても例外なし"""
        from core.title_subsystem import TitleSubsystem
        ts = TitleSubsystem(pygame_screen)
        ts.cleanup()


# ─────────────────────────────────────────────
# グループ4: main.py 統合
# ─────────────────────────────────────────────

class TestTitleSubsystemMainIntegration:

    def test_main_imports_title_subsystem(self):
        """main.py が TitleSubsystem をインポートしている"""
        assert 'TitleSubsystem' in MAIN_SRC

    def test_main_does_not_call_show_title_screen(self):
        """main.py が show_title_screen() を呼ばなくなっている"""
        # show_title_screen の import は残っていても呼び出しがなければOK
        assert 'show_title_screen(' not in MAIN_SRC

    def test_initialize_sets_title_as_first_subsystem(self):
        """initialize() の最後で current_subsystem が TitleSubsystem になる"""
        assert 'TitleSubsystem' in MAIN_SRC
        # initialize() 内に TitleSubsystem の生成があること
        def _get_method(name):
            lines = MAIN_SRC.splitlines()
            result, in_m, indent = [], False, None
            for line in lines:
                if f'def {name}(' in line:
                    in_m = True; indent = len(line) - len(line.lstrip())
                    result.append(line); continue
                if in_m:
                    if line.strip() == '': result.append(line); continue
                    ci = len(line) - len(line.lstrip())
                    if ci <= indent and line.strip().startswith('def '): break
                    result.append(line)
            return '\n'.join(result)
        init_src = _get_method('initialize')
        assert 'TitleSubsystem' in init_src

    def test_handle_transition_routes_go_to_menu_from_title(self):
        """_handle_transition('go_to_menu') が switch_to_menu() を呼ぶ（既存テスト継続）"""
        assert 'go_to_menu' in MAIN_SRC
        assert 'switch_to_menu' in MAIN_SRC
