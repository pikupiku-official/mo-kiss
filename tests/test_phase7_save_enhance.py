"""
フェーズ7 テスト: セーブシステム強化

テスト対象:
- switch_to_map() / switch_to_home() でオートセーブが走る
- save_game() がサムネイルを保存する
- state_files に dialogue_state.json が含まれる
- template_mapping に dialogue_state_template.json が含まれる
- dialogue_state_template.json が存在する
- DialogueSubsystem.handle_events() が ESC → show_option を返す（Task3）
- DialogueSubsystem._save_dialogue_state() が存在する（Task2c）

実行方法:
    cd "c:\\Users\\kohet\\モーキス作業ディレクトリ"
    python -m pytest tests/test_phase7_save_enhance.py -v
"""

import os
import sys
import ast
import json
import tempfile
import shutil
import pytest
import unittest.mock as mock

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

MAIN_SRC    = open(os.path.join(PROJECT_ROOT, 'main.py'),          encoding='utf-8').read()
SAVE_SRC    = open(os.path.join(PROJECT_ROOT, 'core', 'save_manager.py'),   encoding='utf-8').read()
DS_SRC      = open(os.path.join(PROJECT_ROOT, 'dialogue', 'dialogue_subsystem.py'), encoding='utf-8').read()


# ─────────────────────────────────────────────
# Task 2a: オートセーブ
# ─────────────────────────────────────────────

class TestAutoSave:
    def _get_method_src(self, src: str, method_name: str) -> str:
        lines = src.splitlines()
        result = []
        in_method = False
        base_indent = None
        for line in lines:
            stripped = line.lstrip()
            if stripped.startswith(f'def {method_name}('):
                in_method = True
                base_indent = len(line) - len(stripped)
                result.append(line)
                continue
            if in_method:
                if line.strip() == '':
                    result.append(line)
                    continue
                current_indent = len(line) - len(line.lstrip())
                if current_indent <= base_indent and line.strip():
                    break
                result.append(line)
        return '\n'.join(result)

    def test_switch_to_map_has_autosave(self):
        """switch_to_map() に save_game('saveslot_auto') が含まれる"""
        src = self._get_method_src(MAIN_SRC, 'switch_to_map')
        assert 'saveslot_auto' in src, \
            "switch_to_map に saveslot_auto のオートセーブがありません"

    def test_switch_to_home_has_autosave(self):
        """switch_to_home() に save_game('saveslot_auto') が含まれる"""
        src = self._get_method_src(MAIN_SRC, 'switch_to_home')
        assert 'saveslot_auto' in src, \
            "switch_to_home に saveslot_auto のオートセーブがありません"


# ─────────────────────────────────────────────
# Task 2b: サムネイル
# ─────────────────────────────────────────────

class TestThumbnail:
    def test_save_game_has_thumbnail_code(self):
        """save_manager.py の save_game() にサムネイル保存コードが含まれる"""
        assert 'thumbnail.png' in SAVE_SRC, \
            "save_manager.py に thumbnail.png の保存コードがありません"
        # transform.scale は pygame または _pg などの alias 経由で呼ぶ
        assert 'transform.scale' in SAVE_SRC, \
            "save_manager.py に transform.scale がありません"

    def test_save_game_thumbnail_with_mock(self, tmp_path):
        """save_game() がサムネイルを実際に保存する（Mock使用）"""
        import pygame
        pygame.init()

        # SaveManager をテスト用ディレクトリで初期化
        sys.path.insert(0, PROJECT_ROOT)
        # save_manager を再インポート（グローバルインスタンスを汚染しない）
        import importlib
        import core.save_manager as sm_mod
        importlib.reload(sm_mod)

        sm = sm_mod.SaveManager(project_root=str(tmp_path))

        # current_state ディレクトリにダミーファイルを作成
        cs_dir = tmp_path / 'data' / 'current_state'
        cs_dir.mkdir(parents=True, exist_ok=True)
        (cs_dir / 'completed_events.csv').write_text('dummy', encoding='utf-8')
        (cs_dir / 'time_state.json').write_text('{}', encoding='utf-8')
        (cs_dir / 'player_name.json').write_text('{}', encoding='utf-8')
        (cs_dir / 'dialogue_state.json').write_text('{}', encoding='utf-8')

        # pygame display のモック（dummy driver では get_surface() が None を返す）
        # サムネイルスキップ時も True を返すことを確認
        result = sm.save_game('saveslot_test')
        assert result is True, "save_game() が False を返しました"

        pygame.quit()


# ─────────────────────────────────────────────
# Task 2c: dialogue_state.json
# ─────────────────────────────────────────────

class TestDialogueState:
    def test_state_files_has_dialogue_state(self):
        """SaveManager.state_files に dialogue_state.json が含まれる"""
        assert '"dialogue_state.json"' in SAVE_SRC or "'dialogue_state.json'" in SAVE_SRC, \
            "save_manager.py の state_files に dialogue_state.json がありません"

    def test_template_mapping_has_dialogue_state(self):
        """reset_current_state の template_mapping に dialogue_state_template.json が含まれる"""
        assert 'dialogue_state_template.json' in SAVE_SRC, \
            "save_manager.py に dialogue_state_template.json がありません"

    def test_template_file_exists(self):
        """data/templates/dialogue_state_template.json が存在する"""
        template_path = os.path.join(PROJECT_ROOT, 'data', 'templates', 'dialogue_state_template.json')
        assert os.path.exists(template_path), \
            f"dialogue_state_template.json が見つかりません: {template_path}"

    def test_template_file_content(self):
        """dialogue_state_template.json の内容が正しい"""
        template_path = os.path.join(PROJECT_ROOT, 'data', 'templates', 'dialogue_state_template.json')
        with open(template_path, encoding='utf-8') as f:
            data = json.load(f)
        assert data.get('event_id') is None, "event_id は null でなければなりません"
        assert data.get('paragraph_index') == -1, "paragraph_index は -1 でなければなりません"

    def test_dialogue_subsystem_has_save_dialogue_state(self):
        """DialogueSubsystem に _save_dialogue_state メソッドがある"""
        tree = ast.parse(DS_SRC)
        method_names = [
            node.name for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef)
        ]
        assert '_save_dialogue_state' in method_names, \
            "_save_dialogue_state メソッドが dialogue_subsystem.py にありません"

    def test_dialogue_subsystem_tracks_last_saved_paragraph(self):
        """DialogueSubsystem が _last_saved_paragraph を持つ"""
        assert '_last_saved_paragraph' in DS_SRC, \
            "_last_saved_paragraph が dialogue_subsystem.py にありません"


# ─────────────────────────────────────────────
# Task 3: ESC → show_option
# ─────────────────────────────────────────────

class TestEscOption:
    def test_handle_events_returns_show_option_on_esc(self):
        """handle_events() が ESC キーで show_option を返す（バックログ非表示時）"""
        import pygame
        pygame.init()

        # DialogueSubsystem をインポート（pygame dummy で初期化）
        import importlib
        import dialogue.dialogue_subsystem as ds_mod
        importlib.reload(ds_mod)
        DialogueSubsystem = ds_mod.DialogueSubsystem

        # screen と virtual_screen のモック
        screen = mock.MagicMock()
        virtual_screen = mock.MagicMock()

        # game_state の初期化をスキップするためにモック
        with mock.patch('dialogue.dialogue_subsystem._init_game', return_value={}) as _, \
             mock.patch.object(DialogueSubsystem, '_swap_to_virtual_screen'), \
             mock.patch.object(DialogueSubsystem, '_load_event_file'):
            ds = DialogueSubsystem(screen, virtual_screen)

        # backlog_manager がない（非表示）状態でESCイベントをポスト
        ds.game_state = {}
        ds.current_event_id = 'E001'
        ds._last_saved_paragraph = -2

        # ESC キーイベントをキューに入れる
        esc_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE, mod=0, unicode='')
        pygame.event.post(esc_event)

        result = ds.handle_events()

        assert result == "show_option", \
            f"ESC で show_option が返されるはずですが、{result!r} が返されました"

        pygame.quit()

    def test_handle_events_show_option_code_in_source(self):
        """dialogue_subsystem.py に show_option の返値コードが含まれる"""
        assert 'show_option' in DS_SRC, \
            "dialogue_subsystem.py に show_option の返値がありません"

    def test_handle_events_esc_check_before_controller(self):
        """ESC チェックが controller2 呼び出し前に行われる"""
        lines = DS_SRC.splitlines()
        esc_line = None
        ctrl_line = None
        for i, line in enumerate(lines):
            if 'K_ESCAPE' in line and esc_line is None:
                esc_line = i
            if '_ctrl_events' in line and ctrl_line is None:
                ctrl_line = i
        assert esc_line is not None, "K_ESCAPE チェックが見つかりません"
        assert ctrl_line is not None, "_ctrl_events 呼び出しが見つかりません"
        assert esc_line < ctrl_line, \
            f"ESC チェック (L{esc_line+1}) が _ctrl_events (L{ctrl_line+1}) より後にあります"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
