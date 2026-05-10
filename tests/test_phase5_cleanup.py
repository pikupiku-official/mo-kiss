"""
フェーズ5 テスト: 技術的負債解消

テスト対象:
- map.py から launch_main_game, update_game_state, render_game,
  reinitialize_ui_elements, run_ks_event_in_window が削除されている
- save_manager.py が get_project_root() を使っている
- loading_screen.py が get_project_root() を使っている
- dialogue/choice_renderer.py が get_project_root() / path_utils を使っている

実行方法:
    cd "c:\\Users\\kohet\\モーキス作業ディレクトリ"
    python -m pytest tests/test_phase5_cleanup.py -v
"""

import os
import sys
import ast
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

MAP_PY      = os.path.join(PROJECT_ROOT, 'map', 'map.py')
SAVE_PY     = os.path.join(PROJECT_ROOT, 'save_manager.py')
LOADING_PY  = os.path.join(PROJECT_ROOT, 'loading_screen.py')
CHOICE_PY   = os.path.join(PROJECT_ROOT, 'dialogue', 'choice_renderer.py')

MAP_SRC     = open(MAP_PY,     encoding='utf-8').read()
SAVE_SRC    = open(SAVE_PY,    encoding='utf-8').read()
LOADING_SRC = open(LOADING_PY, encoding='utf-8').read()
CHOICE_SRC  = open(CHOICE_PY,  encoding='utf-8').read()


# ─────────────────────────────────────────────
# Task 1a: map.py の旧 dialogue 実行コード削除
# ─────────────────────────────────────────────

class TestMapCleanup:
    def test_launch_main_game_deleted(self):
        """launch_main_game メソッドが map.py に存在しないこと"""
        tree = ast.parse(MAP_SRC)
        method_names = [
            node.name
            for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef)
        ]
        assert 'launch_main_game' not in method_names, \
            "launch_main_game はまだ map.py に存在します"

    def test_update_game_state_deleted(self):
        """update_game_state メソッドが map.py に存在しないこと"""
        tree = ast.parse(MAP_SRC)
        method_names = [
            node.name
            for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef)
        ]
        assert 'update_game_state' not in method_names, \
            "update_game_state はまだ map.py に存在します"

    def test_render_game_deleted(self):
        """render_game メソッドが map.py に存在しないこと"""
        tree = ast.parse(MAP_SRC)
        method_names = [
            node.name
            for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef)
        ]
        assert 'render_game' not in method_names, \
            "render_game はまだ map.py に存在します"

    def test_reinitialize_ui_elements_deleted(self):
        """reinitialize_ui_elements メソッドが map.py に存在しないこと"""
        tree = ast.parse(MAP_SRC)
        method_names = [
            node.name
            for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef)
        ]
        assert 'reinitialize_ui_elements' not in method_names, \
            "reinitialize_ui_elements はまだ map.py に存在します"

    def test_run_ks_event_in_window_deleted(self):
        """run_ks_event_in_window メソッドが map.py に存在しないこと"""
        tree = ast.parse(MAP_SRC)
        method_names = [
            node.name
            for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef)
        ]
        assert 'run_ks_event_in_window' not in method_names, \
            "run_ks_event_in_window はまだ map.py に存在します"

    def test_map_py_parses_ok(self):
        """map.py が有効な Python として解析できること"""
        try:
            ast.parse(MAP_SRC)
        except SyntaxError as e:
            pytest.fail(f"map.py の構文エラー: {e}")

    def test_execute_event_returns_launch_event(self):
        """execute_event が launch_event: プレフィックスを返すこと（簡易AST検証）"""
        assert 'launch_event:' in MAP_SRC, \
            "execute_event に launch_event: が含まれていません"


# ─────────────────────────────────────────────
# Task 1b: path_utils 統一
# ─────────────────────────────────────────────

class TestPathUtilsUnification:
    def test_save_manager_uses_get_project_root(self):
        """save_manager.py が get_project_root を使っている"""
        assert 'get_project_root' in SAVE_SRC, \
            "save_manager.py に get_project_root がありません"

    def test_save_manager_no_file_dirname(self):
        """save_manager.py の __init__ で __file__ による dirname を使っていない"""
        # 唯一許容されるのは from path_utils import ... の行のみ
        lines = SAVE_SRC.splitlines()
        for line in lines:
            if 'os.path.dirname' in line and '__file__' in line:
                pytest.fail(
                    f"save_manager.py に __file__ ベースのパスが残っています: {line.strip()}"
                )

    def test_loading_screen_uses_get_project_root(self):
        """loading_screen.py が get_project_root を使っている"""
        assert 'get_project_root' in LOADING_SRC, \
            "loading_screen.py に get_project_root がありません"

    def test_choice_renderer_uses_get_project_root(self):
        """dialogue/choice_renderer.py が get_project_root を使っている"""
        assert 'get_project_root' in CHOICE_SRC, \
            "choice_renderer.py に get_project_root がありません"

    def test_map_uses_get_project_root(self):
        """map/map.py が _get_project_root を使っている"""
        assert '_get_project_root' in MAP_SRC or 'get_project_root' in MAP_SRC, \
            "map.py に get_project_root がありません"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
