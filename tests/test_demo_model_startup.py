"""Exercise the launcher's DLL initialization order in a fresh process."""

import importlib.util
import os
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]


def test_demo_launcher_can_initialize_and_use_answer_model(tmp_path):
    for dependency in ("onnxruntime", "sentencepiece", "numpy", "PyQt5"):
        if importlib.util.find_spec(dependency) is None:
            pytest.skip(f"{dependency} is unavailable")
    if not (ROOT / "models/ruri-v3-30m-int8/model_int8.onnx").is_file():
        pytest.skip("bundled semantic model is unavailable")

    # Replace only the game window/loop. The real launcher initializes its DLLs,
    # Qt is then used as in the application, and the real model judges answers.
    script = """
import runpy
import sys
import types

application = types.ModuleType('demo.application')

class DemoApplication:
    def run(self):
        from PyQt5.QtWidgets import QApplication
        from core.services.seed_manager import SeedManager

        manager = SeedManager()
        manager.preload_answer_model()
        manager._preload_thread.join(30)
        assert manager.model_status() == 'ready', manager._answer_judge.load_error
        verdict = manager.judge_answer(
            'MOMOKO_GD_MONEY', '旅行のお土産で散財したから余裕がない'
        )
        assert verdict['result'] == 'correct', verdict
        assert verdict['reason_codes'] == ('semantic_match',), verdict
        verdict = manager.judge_answer('MOMOKO_GD_MONEY', '桃子は借金でお金がない')
        assert verdict['result'] == 'incorrect', verdict
        print('DEMO_STARTUP_REAL_MODEL_OK')
        return True

application.DemoApplication = DemoApplication
sys.modules['demo.application'] = application
runpy.run_path(sys.argv[1], run_name='__main__')
"""
    environment = dict(os.environ, PYTHONIOENCODING="utf-8")
    result = subprocess.run(
        [sys.executable, "-c", script, str(ROOT / "demo/demo.py")],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "DEMO_STARTUP_REAL_MODEL_OK" in result.stdout
