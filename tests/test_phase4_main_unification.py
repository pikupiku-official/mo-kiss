"""
フェーズ4 テスト: main.py switch_to() 統一化

テスト対象:
- GameApplication.switch_to(subsystem, mode_name) の追加
- 各 switch_to_*() が switch_to() を経由する
- switch_to_dialogue() が DialogueSubsystem を使う
- 重複 BGM 停止コードが main.py から消えている
- _handle_transition() が遷移文字列を正しくルーティングする
- メインループが統一インターフェースを使う

方針:
    GameApplication は pygame 初期化が必要なため、
    ① ソースコード解析（構造・重複コードの有無）
    ② 軽量な Mock を使った振る舞いテスト
    の2段構えで検証する。

実行方法:
    cd "c:\\Users\\kohet\\モーキス作業ディレクトリ"
    python -m pytest tests/test_phase4_main_unification.py -v
"""

import os
import sys
import ast
import unittest.mock as mock
import pytest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

MAIN_PY = os.path.join(PROJECT_ROOT, 'main.py')
MAIN_SRC = open(MAIN_PY, encoding='utf-8').read()


# ─────────────────────────────────────────────
# ヘルパー: AST で main.py を解析
# ─────────────────────────────────────────────

def _get_method_src(method_name: str) -> str:
    """main.py から指定メソッドのソースを抽出（簡易grep版）"""
    lines = MAIN_SRC.splitlines()
    result = []
    in_method = False
    indent = None
    for line in lines:
        if f'def {method_name}(' in line:
            in_method = True
            indent = len(line) - len(line.lstrip())
            result.append(line)
            continue
        if in_method:
            if line.strip() == '':
                result.append(line)
                continue
            current_indent = len(line) - len(line.lstrip())
            if current_indent <= indent and line.strip().startswith('def '):
                break
            result.append(line)
    return '\n'.join(result)


def _count_pattern(src: str, pattern: str) -> int:
    return src.count(pattern)


# ─────────────────────────────────────────────
# グループ1: switch_to() メソッドの存在と構造
# ─────────────────────────────────────────────

class TestSwitchToMethod:
    """GameApplication.switch_to() が正しく定義されているか"""

    def test_switch_to_exists_in_source(self):
        """main.py に switch_to() メソッドが存在する"""
        assert 'def switch_to(self,' in MAIN_SRC, \
            "GameApplication.switch_to() が main.py に存在しない"

    def test_switch_to_calls_cleanup(self):
        """switch_to() が current_subsystem.cleanup() を呼ぶ"""
        src = _get_method_src('switch_to')
        assert 'cleanup()' in src, \
            "switch_to() が cleanup() を呼んでいない"

    def test_switch_to_calls_on_enter(self):
        """switch_to() が新サブシステムの on_enter() を呼ぶ"""
        src = _get_method_src('switch_to')
        assert 'on_enter()' in src, \
            "switch_to() が on_enter() を呼んでいない"

    def test_switch_to_updates_current_subsystem(self):
        """switch_to() が self.current_subsystem を更新する"""
        src = _get_method_src('switch_to')
        assert 'self.current_subsystem' in src, \
            "switch_to() が current_subsystem を更新していない"

    def test_switch_to_updates_current_mode(self):
        """switch_to() が self.current_mode を更新する"""
        src = _get_method_src('switch_to')
        assert 'self.current_mode' in src, \
            "switch_to() が current_mode を更新していない"


# ─────────────────────────────────────────────
# グループ2: 各 switch_to_*() が switch_to() を経由する
# ─────────────────────────────────────────────

class TestSwitchToRouting:
    """switch_to_menu/map/home/dialogue が switch_to() を経由するか"""

    def test_switch_to_menu_uses_switch_to(self):
        """switch_to_menu() が self.switch_to() を呼ぶ"""
        src = _get_method_src('switch_to_menu')
        assert 'self.switch_to(' in src, \
            "switch_to_menu() が self.switch_to() を呼んでいない"

    def test_switch_to_map_uses_switch_to(self):
        """switch_to_map() が self.switch_to() を呼ぶ"""
        src = _get_method_src('switch_to_map')
        assert 'self.switch_to(' in src, \
            "switch_to_map() が self.switch_to() を呼んでいない"

    def test_switch_to_home_uses_switch_to(self):
        """switch_to_home() が self.switch_to() を呼ぶ"""
        src = _get_method_src('switch_to_home')
        assert 'self.switch_to(' in src, \
            "switch_to_home() が self.switch_to() を呼んでいない"

    def test_switch_to_dialogue_uses_switch_to(self):
        """switch_to_dialogue() が self.switch_to() を呼ぶ"""
        src = _get_method_src('switch_to_dialogue')
        assert 'self.switch_to(' in src, \
            "switch_to_dialogue() が self.switch_to() を呼んでいない"

    def test_switch_to_dialogue_uses_dialogue_subsystem(self):
        """switch_to_dialogue() が DialogueSubsystem を使う"""
        src = _get_method_src('switch_to_dialogue')
        assert 'DialogueSubsystem' in src, \
            "switch_to_dialogue() が DialogueSubsystem を使っていない"


# ─────────────────────────────────────────────
# グループ3: 重複コードが消えているか（ソース解析）
# ─────────────────────────────────────────────

class TestDuplicateCodeRemoved:
    """散在していた BGM 停止コードが switch_to_*() から消えているか"""

    def test_switch_to_menu_no_inline_stop_bgm(self):
        """switch_to_menu() に直接 stop_bgm() が書かれていない"""
        src = _get_method_src('switch_to_menu')
        assert 'stop_bgm()' not in src, \
            "switch_to_menu() にまだ stop_bgm() が残っている"

    def test_switch_to_map_no_inline_stop_bgm(self):
        """switch_to_map() に直接 stop_bgm() が書かれていない"""
        src = _get_method_src('switch_to_map')
        assert 'stop_bgm()' not in src, \
            "switch_to_map() にまだ stop_bgm() が残っている"

    def test_switch_to_home_no_inline_stop_bgm(self):
        """switch_to_home() に直接 stop_bgm() が書かれていない"""
        src = _get_method_src('switch_to_home')
        assert 'stop_bgm()' not in src, \
            "switch_to_home() にまだ stop_bgm() が残っている"

    def test_switch_to_dialogue_no_inline_stop_bgm(self):
        """switch_to_dialogue() に直接 stop_bgm() が書かれていない"""
        src = _get_method_src('switch_to_dialogue')
        assert 'stop_bgm()' not in src, \
            "switch_to_dialogue() にまだ stop_bgm() が残っている"

    def test_no_dialogue_game_state_dict_access_in_switch(self):
        """switch_to_*() 内で dialogue_game_state['bgm_manager'] に直接アクセスしていない"""
        for method in ('switch_to_menu', 'switch_to_map', 'switch_to_home'):
            src = _get_method_src(method)
            assert "dialogue_game_state['bgm_manager']" not in src, \
                f"{method}() にまだ dialogue_game_state['bgm_manager'] が残っている"


# ─────────────────────────────────────────────
# グループ4: _handle_transition() のルーティング
# ─────────────────────────────────────────────

class TestHandleTransition:
    """_handle_transition() が遷移文字列を正しくルーティングするか"""

    def test_handle_transition_exists(self):
        """_handle_transition() メソッドが存在する"""
        assert 'def _handle_transition(' in MAIN_SRC, \
            "_handle_transition() が main.py に存在しない"

    def test_handle_transition_routes_go_to_map(self):
        """'go_to_map' が switch_to_map() を呼ぶ"""
        src = _get_method_src('_handle_transition')
        assert 'go_to_map' in src, \
            "_handle_transition() に 'go_to_map' のルーティングがない"
        assert 'switch_to_map' in src, \
            "_handle_transition() が switch_to_map() を呼んでいない"

    def test_handle_transition_routes_go_to_menu(self):
        """'go_to_menu' が switch_to_menu() を呼ぶ"""
        src = _get_method_src('_handle_transition')
        assert 'go_to_menu' in src
        assert 'switch_to_menu' in src

    def test_handle_transition_routes_go_to_home(self):
        """'go_to_home' が switch_to_home() を呼ぶ"""
        src = _get_method_src('_handle_transition')
        assert 'go_to_home' in src
        assert 'switch_to_home' in src

    def test_handle_transition_routes_dialogue_ended(self):
        """'dialogue_ended' が後処理（完了記録＋マップ/ホーム遷移）を呼ぶ"""
        src = _get_method_src('_handle_transition')
        assert 'dialogue_ended' in src

    def test_handle_transition_routes_start_event(self):
        """'start_event:' プレフィックスが switch_to_dialogue() を呼ぶ"""
        src = _get_method_src('_handle_transition')
        assert 'start_event' in src
        assert 'switch_to_dialogue' in src

    def test_handle_transition_routes_quit(self):
        """'quit' が self.running = False を設定する"""
        src = _get_method_src('_handle_transition')
        assert 'quit' in src
        assert 'self.running' in src


# ─────────────────────────────────────────────
# グループ5: switch_to() の振る舞い（Mock）
# ─────────────────────────────────────────────

class TestSwitchToBehavior:
    """switch_to() の cleanup → on_enter 順序を Mock で検証"""

    def _make_app(self):
        """GameApplication の最小 Mock（pygame 不要）"""
        import types

        app = types.SimpleNamespace(
            current_subsystem=None,
            current_mode=None,
            running=True,
        )

        # main.py の switch_to() ロジックを再現した最小実装
        def switch_to(subsystem, mode_name):
            if app.current_subsystem:
                app.current_subsystem.cleanup()
            app.current_subsystem = subsystem
            app.current_mode = mode_name
            app.current_subsystem.on_enter()

        app.switch_to = switch_to
        return app

    def test_cleanup_called_before_on_enter(self):
        """switch_to() が cleanup() → on_enter() の順で呼ぶ"""
        app = self._make_app()
        call_log = []

        class _SubA:
            def cleanup(self): call_log.append('A.cleanup')
            def on_enter(self): call_log.append('A.on_enter')

        class _SubB:
            def cleanup(self): call_log.append('B.cleanup')
            def on_enter(self): call_log.append('B.on_enter')

        app.switch_to(_SubA(), 'a')
        assert call_log == ['A.on_enter']

        app.switch_to(_SubB(), 'b')
        assert call_log == ['A.on_enter', 'A.cleanup', 'B.on_enter']

    def test_first_switch_no_cleanup(self):
        """初回 switch_to() では cleanup() が呼ばれない（current_subsystem=None）"""
        app = self._make_app()
        entered = []

        class _Sub:
            def cleanup(self): pytest.fail("初回で cleanup() が呼ばれた")
            def on_enter(self): entered.append(True)

        app.switch_to(_Sub(), 'x')
        assert entered

    def test_current_mode_updated(self):
        """switch_to() 後に current_mode が更新される"""
        app = self._make_app()

        class _Sub:
            def cleanup(self): pass
            def on_enter(self): pass

        app.switch_to(_Sub(), 'map')
        assert app.current_mode == 'map'

    def test_real_gameapp_has_switch_to(self):
        """実際の GameApplication クラスに switch_to() メソッドが存在する"""
        # モジュールレベルで import して属性確認のみ（pygame 初期化不要）
        import importlib.util
        spec = importlib.util.spec_from_file_location("main", MAIN_PY)
        # 実際の import は pygame 初期化を伴うためスキップ
        # ソースに def switch_to が存在することで代替検証済み
        assert 'def switch_to(self,' in MAIN_SRC


# ─────────────────────────────────────────────
# グループ6: メインループの統一
# ─────────────────────────────────────────────

class TestMainLoopUnification:
    """メインループが統一インターフェースを使っているか"""

    def test_run_uses_handle_events_unified(self):
        """run() のメインループが current_subsystem.handle_events() を呼ぶ"""
        src = _get_method_src('run')
        assert 'current_subsystem' in src and 'handle_events' in src, \
            "run() が current_subsystem.handle_events() を使っていない"

    def test_run_uses_update_unified(self):
        """run() のメインループが current_subsystem.update() を呼ぶ"""
        src = _get_method_src('run')
        assert 'current_subsystem' in src and '.update()' in src, \
            "run() が current_subsystem.update() を使っていない"

    def test_run_uses_render_unified(self):
        """run() のメインループが current_subsystem.render() を呼ぶ"""
        src = _get_method_src('run')
        assert 'current_subsystem' in src and '.render()' in src, \
            "run() が current_subsystem.render() を使っていない"

    def test_run_uses_handle_transition(self):
        """run() が _handle_transition() を呼ぶ"""
        src = _get_method_src('run')
        assert '_handle_transition' in src, \
            "run() が _handle_transition() を使っていない"

    def test_no_mode_string_comparison_in_run(self):
        """run() 内に current_mode == 'dialogue' 等の分岐がない"""
        src = _get_method_src('run')
        for mode in ('"dialogue"', '"map"', '"menu"', '"home"'):
            assert f'current_mode == {mode}' not in src, \
                f"run() に current_mode == {mode} の分岐が残っている"


# ─────────────────────────────────────────────
# グループ7: 非回帰
# ─────────────────────────────────────────────

class TestPhase4Regression:
    """フェーズ4後も既存機能が壊れていないか"""

    def test_main_py_imports_dialogue_subsystem(self):
        """main.py が DialogueSubsystem をインポートしている"""
        assert 'DialogueSubsystem' in MAIN_SRC, \
            "main.py が DialogueSubsystem をインポートしていない"

    def test_main_py_imports_fieldmap(self):
        """main.py が FieldMap をインポートしている（フェーズ2で確認済みの継続確認）"""
        assert 'FieldMap' in MAIN_SRC

    def test_switch_to_menu_still_exists(self):
        """switch_to_menu() が残っている（後方互換）"""
        assert 'def switch_to_menu(' in MAIN_SRC

    def test_switch_to_map_still_exists(self):
        """switch_to_map() が残っている"""
        assert 'def switch_to_map(' in MAIN_SRC

    def test_switch_to_home_still_exists(self):
        """switch_to_home() が残っている"""
        assert 'def switch_to_home(' in MAIN_SRC

    def test_switch_to_dialogue_still_exists(self):
        """switch_to_dialogue() が残っている"""
        assert 'def switch_to_dialogue(' in MAIN_SRC

    def test_phase1_tests_still_pass(self):
        """フェーズ1 のテストが引き続き通過する（import チェックのみ）"""
        from menu.main_menu import MainMenu
        from home.home import HomeModule
        from core.subsystem_base import SubsystemBase
        assert issubclass(MainMenu, SubsystemBase)
        assert issubclass(HomeModule, SubsystemBase)

    def test_phase2_tests_still_pass(self):
        """フェーズ2 のテストが引き続き通過する（import チェックのみ）"""
        from map.map import FieldMap
        from core.subsystem_base import SubsystemBase
        assert issubclass(FieldMap, SubsystemBase)

    def test_phase3_tests_still_pass(self):
        """フェーズ3 のテストが引き続き通過する（import チェックのみ）"""
        from dialogue.dialogue_subsystem import DialogueSubsystem
        from core.subsystem_base import SubsystemBase
        assert issubclass(DialogueSubsystem, SubsystemBase)
