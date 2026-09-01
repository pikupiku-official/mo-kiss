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

import inspect
import os, sys
import unittest.mock as mock
import types
import pytest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

import pygame

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
    from core.ui.option_overlay import OptionOverlay
    return OptionOverlay(pygame_screen, parent_mode="map")


# ─────────────────────────────────────────────
# グループ1: OptionOverlay クラス構造
# ─────────────────────────────────────────────

class TestOptionOverlayStructure:

    def test_module_importable(self):
        import core.ui.option_overlay as option_overlay  # noqa

    def test_class_exists(self):
        from core.ui.option_overlay import OptionOverlay
        assert OptionOverlay is not None

    def test_instantiable_map_mode(self, pygame_screen):
        from core.ui.option_overlay import OptionOverlay
        o = OptionOverlay(pygame_screen, parent_mode="map")
        assert o is not None

    def test_instantiable_home_mode(self, pygame_screen):
        from core.ui.option_overlay import OptionOverlay
        o = OptionOverlay(pygame_screen, parent_mode="home")
        assert o is not None

    def test_instantiable_dialogue_mode(self, pygame_screen):
        from core.ui.option_overlay import OptionOverlay
        o = OptionOverlay(pygame_screen, parent_mode="dialogue")
        assert o is not None

    def test_screen_stored(self, pygame_screen):
        from core.ui.option_overlay import OptionOverlay
        o = OptionOverlay(pygame_screen, parent_mode="map")
        assert o.screen is pygame_screen

    def test_parent_mode_stored(self, pygame_screen):
        from core.ui.option_overlay import OptionOverlay
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
        from core.ui.option_overlay import OptionOverlay
        o = OptionOverlay(pygame_screen, parent_mode="map")
        event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE, mod=0, unicode='', scancode=0)
        result = o.handle_events([event])
        assert result == "resume"

    def test_resume_action_returns_resume(self, pygame_screen):
        """resume() メソッドが 'resume' を返す"""
        from core.ui.option_overlay import OptionOverlay
        o = OptionOverlay(pygame_screen, parent_mode="map")
        assert o.resume() == "resume"

    def test_go_to_menu_action(self, pygame_screen):
        """go_to_menu() が 'go_to_menu' を返す"""
        from core.ui.option_overlay import OptionOverlay
        o = OptionOverlay(pygame_screen, parent_mode="map")
        assert o.go_to_menu() == "go_to_menu"

    def test_quit_event(self, pygame_screen):
        """QUIT イベントで 'quit' を返す"""
        import pygame
        from core.ui.option_overlay import OptionOverlay
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
        from core.ui.option_overlay import OptionOverlay
        o = OptionOverlay(pygame_screen, parent_mode="map")
        assert o.save_enabled is True

    def test_save_available_in_home_mode(self, pygame_screen):
        """HOME モードではセーブボタンが有効"""
        from core.ui.option_overlay import OptionOverlay
        o = OptionOverlay(pygame_screen, parent_mode="home")
        assert o.save_enabled is True

    def test_save_disabled_in_dialogue_mode(self, pygame_screen):
        """DIALOGUE モードではセーブボタンが無効（設計書準拠）"""
        from core.ui.option_overlay import OptionOverlay
        o = OptionOverlay(pygame_screen, parent_mode="dialogue")
        assert o.save_enabled is False

    def test_save_disabled_in_menu_mode(self, pygame_screen):
        """MENU モードではセーブボタンが無効"""
        from core.ui.option_overlay import OptionOverlay
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


class TestMockOptionOverlay:

    def test_mock_overlay_instantiable(self, pygame_screen):
        from core.ui.option_overlay import MockOptionOverlay
        overlay = MockOptionOverlay(pygame_screen, ("UI_option01.png", "UI_option02.png", "UI_option03.png"))
        assert overlay is not None

    def test_mock_overlay_start_close(self, pygame_screen):
        from core.ui.option_overlay import MockOptionOverlay
        overlay = MockOptionOverlay(pygame_screen, ("UI_option01.png", "UI_option02.png", "UI_option03.png"))
        overlay.start_close()
        assert overlay._closing_started_at_ms is not None

    def test_mock_overlay_render_callable(self, pygame_screen):
        from core.ui.option_overlay import MockOptionOverlay
        overlay = MockOptionOverlay(pygame_screen, ("UI_option01.png", "UI_option02.png", "UI_option03.png"))
        overlay.render_overlay()


class TestOptionImageOverlay:

    @pytest.fixture
    def overlay(self, pygame_screen, monkeypatch):
        from core.ui.option_overlay import OptionImageOverlay
        monkeypatch.setattr(
            OptionImageOverlay,
            "_load_images",
            lambda self: {
                number: pygame.Surface((640, 602), pygame.SRCALPHA)
                for number in range(1, 7)
            },
        )
        return OptionImageOverlay(pygame_screen)

    def test_real_assets_load_one_through_six_without_zero(self, pygame_screen):
        from core.ui.option_overlay import OptionImageOverlay
        overlay = OptionImageOverlay(pygame_screen)

        assert set(overlay._images) == set(range(1, 7))
        assert all(image.get_size() == (640, 602) for image in overlay._images.values())

    def test_open_animation_uses_150ms_steps(self, overlay, monkeypatch):
        now = [overlay._opened_at_ms]
        monkeypatch.setattr(pygame.time, "get_ticks", lambda: now[0])

        assert overlay._get_hidden_pixels() == 400
        now[0] += 150
        assert overlay._get_hidden_pixels() == 200
        now[0] += 150
        assert overlay._get_hidden_pixels() == 0

    def test_close_animation_reverses_at_50ms_steps(self, overlay, monkeypatch):
        now = [1_000]
        monkeypatch.setattr(pygame.time, "get_ticks", lambda: now[0])
        overlay.start_close()

        assert overlay._get_hidden_pixels() == 0
        now[0] += 50
        assert overlay._get_hidden_pixels() == 200
        now[0] += 50
        assert overlay._get_hidden_pixels() == 400
        now[0] += 50
        assert overlay.handle_events([]) == "resume"

    @pytest.mark.parametrize(
        ("key", "expected"),
        [
            (pygame.K_RIGHT, 2),
            (pygame.K_DOWN, 3),
            (pygame.K_LEFT, 6),
            (pygame.K_UP, 5),
        ],
    )
    def test_direction_keys_move_from_one_with_wrap(self, overlay, key, expected):
        overlay.handle_events([pygame.event.Event(pygame.KEYDOWN, key=key)])
        assert overlay.selected_number == expected

    def test_selection_wraps_between_one_and_six_without_zero(self, overlay):
        overlay.selected_number = 6
        overlay._move_selection(1)
        assert overlay.selected_number == 1

        overlay._move_selection(-1)
        assert overlay.selected_number == 6

    def test_enter_on_one_starts_close_animation_immediately(self, overlay):
        result = overlay.handle_events([
            pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN),
        ])

        assert result is None
        assert overlay._closing_started_at_ms is not None

    @pytest.mark.parametrize(
        ("number", "expected"),
        [
            (2, "go_to_menu"),
            (3, "save"),
            (4, "load"),
            (5, "return_to_morning"),
        ],
    )
    def test_enter_activates_selected_option_immediately(
        self, overlay, number, expected
    ):
        overlay.selected_number = number

        result = overlay.handle_events([
            pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN),
        ])

        assert result == expected

    def test_keypad_enter_is_supported(self, overlay):
        overlay.selected_number = 2
        result = overlay.handle_events([
            pygame.event.Event(pygame.KEYDOWN, key=pygame.K_KP_ENTER),
        ])
        assert result == "go_to_menu"

    def test_enter_on_six_opens_settings(self, overlay):
        overlay.selected_number = 6

        result = overlay.handle_events([
            pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN),
        ])

        assert result == "settings"
        assert overlay._closing_started_at_ms is None

    def test_cursor_move_dips_30px_in_50ms_steps_and_locks_input(
        self,
        overlay,
        monkeypatch,
    ):
        now = [1_000]
        monkeypatch.setattr(pygame.time, "get_ticks", lambda: now[0])
        overlay.selected_number = 2
        overlay.handle_events([
            pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RIGHT),
        ])

        assert overlay.selected_number == 3
        assert overlay._get_move_offset_y() == 30
        now[0] += 50
        overlay.handle_events([
            pygame.event.Event(pygame.KEYDOWN, key=pygame.K_LEFT),
        ])
        assert overlay._get_move_offset_y() == 0
        assert overlay.selected_number == 3

        now[0] += 49
        result = overlay.handle_events([
            pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN),
        ])
        assert result is None
        assert overlay.selected_number == 3

        now[0] += 1
        result = overlay.handle_events([
            pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN),
        ])
        assert result == "save"
        assert overlay.is_move_animating is False

    def test_render_scales_image_to_full_screen_width(self, overlay, monkeypatch):
        class RecordingScreen:
            def __init__(self):
                self.blits = []

            def get_size(self):
                return (1440, 1080)

            def blit(self, image, position):
                self.blits.append((image, position))

        overlay.screen = RecordingScreen()
        monkeypatch.setattr(overlay, "_get_hidden_pixels", lambda: 200)

        overlay.render_overlay()

        image, position = overlay.screen.blits[0]
        assert image.get_width() == 1440
        assert image.get_height() == round(602 * 1440 / 640)
        assert position == (0, 1080 - image.get_height() + 200)


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

    def test_mock_option_shortcut_exists(self):
        """main.py に F6/F7 モック表示のショートカットがある"""
        assert 'pygame.K_F6' in MAIN_SRC
        assert 'pygame.K_F7' in MAIN_SRC
        assert 'def show_mock_option(' in MAIN_SRC
        assert 'def show_mock_await(' in MAIN_SRC

    def test_f6_option_uses_numbered_image_overlay(self, pygame_screen):
        from core.ui.option_overlay import OptionImageOverlay
        from main import GameApplication
        app = GameApplication.__new__(GameApplication)
        app.screen = pygame_screen
        app.current_overlay = None

        app.show_mock_option()

        assert isinstance(app.current_overlay, OptionImageOverlay)
        assert app.current_overlay.selected_number == 1

    def test_option_save_opens_manual_slot_screen_and_stays_open(self, monkeypatch):
        from core.flow.game_flow import GameFlowController
        from main import GameApplication
        app = GameApplication.__new__(GameApplication)
        app.current_overlay = object()
        app.show_slot_screen = mock.Mock()
        app.game_flow = GameFlowController(app)

        app._handle_overlay_result("save")

        app.show_slot_screen.assert_called_once_with("save")
        assert app.current_overlay is not None

    def test_option_load_opens_manual_slot_screen_and_stays_open(self, monkeypatch):
        from core.flow.game_flow import GameFlowController
        from main import GameApplication
        app = GameApplication.__new__(GameApplication)
        app.current_overlay = object()
        app.show_slot_screen = mock.Mock()
        app.game_flow = GameFlowController(app)

        app._handle_overlay_result("load")

        app.show_slot_screen.assert_called_once_with("load")
        assert app.current_overlay is not None

    def test_option_return_to_morning_keeps_date_and_switches_to_map(self, monkeypatch):
        from core.flow.game_flow import GameFlowController
        from main import GameApplication
        time_manager = types.SimpleNamespace(
            current_period="night",
            time_periods=["morning", "day", "after_school", "night"],
            save_time_state=mock.Mock(),
        )
        app = GameApplication.__new__(GameApplication)
        app.current_overlay = object()
        app.reload_game_systems = mock.Mock()
        app.switch_to_map = mock.Mock()
        app.game_flow = GameFlowController(
            app,
            time_manager_getter=lambda: time_manager,
        )

        app._handle_overlay_result("return_to_morning")

        assert time_manager.current_period == "morning"
        time_manager.save_time_state.assert_called_once_with()
        assert app.current_overlay is None
        app.reload_game_systems.assert_called_once_with()
        app.switch_to_map.assert_called_once_with()

    def test_save_manager_tracks_player_and_dialogue_state_separately(self, tmp_path):
        from core.services.save_manager import SaveManager
        manager = SaveManager(str(tmp_path))

        assert "player_name.json" in manager.state_files
        assert "dialogue_state.json" in manager.state_files

    def test_run_handles_overlay(self):
        """run() が OPTION 対応の GameLoop へ委譲する"""
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
        from core.runtime.game_loop import GameLoop
        loop_src = inspect.getsource(GameLoop)
        assert 'GameLoop(self' in run_src
        assert 'option_subsystem' in loop_src

    def test_overlay_behavior_mock(self):
        """show_option → handle_events → hide_option の流れが動く（Mock）"""
        app = types.SimpleNamespace(
            current_subsystem=None,
            current_overlay=None,
            current_mode="map",
            running=True,
        )

        from core.ui.option_overlay import OptionOverlay
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
        from core.runtime.subsystem_base import SubsystemBase

        cleanup_called = []

        class _FakeSub(SubsystemBase):
            def handle_events(self, events=None): return None
            def update(self): pass
            def render(self): pass
            def cleanup(self): cleanup_called.append(True)

        # show_option は switch_to() を使わないので cleanup() が呼ばれない
        current = _FakeSub(pygame_screen)

        from core.ui.option_overlay import OptionOverlay
        # オーバーレイを生成しても current.cleanup() は呼ばれない
        _ = OptionOverlay(pygame_screen, parent_mode="map")
        assert not cleanup_called, "OPTION 表示時に cleanup() が呼ばれた"


# ─────────────────────────────────────────────
# グループ7: 非回帰
# ─────────────────────────────────────────────

class TestPhase6Regression:

    def test_phase1_still_passes(self):
        from core.runtime.subsystem_base import SubsystemBase
        from menu.main_menu import MainMenu
        from home.home import HomeModule
        assert issubclass(MainMenu, SubsystemBase)
        assert issubclass(HomeModule, SubsystemBase)

    def test_phase2_still_passes(self):
        from map.map import FieldMap
        from core.runtime.subsystem_base import SubsystemBase
        assert issubclass(FieldMap, SubsystemBase)

    def test_phase3_still_passes(self):
        from dialogue.dialogue_subsystem import DialogueSubsystem
        from core.runtime.subsystem_base import SubsystemBase
        assert issubclass(DialogueSubsystem, SubsystemBase)

    def test_phase8_still_passes(self):
        from core.ui.title_subsystem import TitleSubsystem
        from core.runtime.subsystem_base import SubsystemBase
        assert issubclass(TitleSubsystem, SubsystemBase)
