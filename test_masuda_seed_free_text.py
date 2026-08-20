"""Standalone GUI for testing MASUDA_TP1 with every seed already acquired.

Run the interactive prompt:
    python test_masuda_seed_free_text.py

Run one answer without opening a window:
    python test_masuda_seed_free_text.py --judge "増田は真性包茎なんだ"
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
from pathlib import Path

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from core.path_utils import get_font_path
from core.services.seed_manager import SeedManager
from dialogue.seed_answer_overlay import SeedAnswerOverlay


TURNING_POINT_ID = "MASUDA_TP1"
WINDOW_SIZE = (1440, 1080)
TEST_GAME_DATE = "1999-06-02"


class StandaloneTextRenderer:
    """Small font adapter matching what SeedAnswerOverlay needs."""

    def __init__(self):
        self.pygame_fonts = {
            "name": pygame.font.Font(get_font_path("MPLUS1p-Bold.ttf"), 42),
            "text": pygame.font.Font(get_font_path("MPLUS1p-Medium.ttf"), 36),
        }


def assume_all_turning_point_seeds(manager, turning_point_id=TURNING_POINT_ID):
    """Acquire every matching seed in memory without touching save files."""
    acquired_ids = []
    for seed_id, seed in manager.seeds.items():
        if seed.get("turning_point_id") != turning_point_id:
            continue
        manager.state["acquired"][seed_id] = {
            "acquired_game_date": TEST_GAME_DATE,
            "journaled_game_date": TEST_GAME_DATE,
            "source_event_id": "STANDALONE_TEST",
        }
        acquired_ids.append(seed_id)
    acquired_ids.sort(key=manager._seed_sort_key)
    manager.state["journal_days"] = [
        {"game_date": TEST_GAME_DATE, "seed_ids": list(acquired_ids)}
    ]
    return acquired_ids


def dependency_report():
    names = ("numpy", "onnxruntime", "sentencepiece")
    return {name: importlib.util.find_spec(name) is not None for name in names}


def print_runtime_diagnostics():
    print("=== MASUDA seed free-text test ===")
    print(f"Python: {sys.executable}")
    print(f"Version: {sys.version.split()[0]}")
    print(f"Project: {Path(__file__).resolve().parent}")
    print(f"Dependencies: {dependency_report()}")


def judge_once(manager, answer):
    verdict = manager.judge_answer(TURNING_POINT_ID, answer)
    print(json.dumps(verdict, ensure_ascii=False, indent=2))
    if verdict.get("result") == "error":
        print("\nInstall into the Python shown above with:")
        print(
            f'  "{sys.executable}" -m pip install '
            "-r requirements-semantic-judge.txt"
        )
    return verdict


def feedback_message(verdict):
    result = verdict.get("result", "error")
    score = verdict.get("semantic_score")
    if result == "correct":
        label = "正解"
    elif result == "borderline":
        label = "惜しい／再入力"
    elif result == "incorrect":
        label = "不正解"
    else:
        label = "モデル読込エラー（コンソール参照）"
    return f"{label}  score={score:.4f}" if isinstance(score, float) else label


def run_gui(manager):
    pygame.init()
    pygame.display.set_caption("増田のタネ - 自由記述判定テスト（全タネ取得済み）")
    screen = pygame.display.set_mode(WINDOW_SIZE)
    clock = pygame.time.Clock()
    renderer = StandaloneTextRenderer()
    overlay = SeedAnswerOverlay(
        screen,
        TURNING_POINT_ID,
        manager,
        renderer,
    )

    warmup = judge_once(manager, "増田は真性包茎なんだ")
    if warmup.get("result") == "error":
        overlay.show_judge_feedback("error", feedback_message(warmup))

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                continue
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
                continue
            answer = overlay.handle_event(event)
            if answer:
                verdict = judge_once(manager, answer)
                overlay.show_judge_feedback(
                    verdict.get("result", "error"),
                    feedback_message(verdict),
                )

        screen.fill((12, 17, 25))
        overlay.render()
        pygame.display.flip()
        clock.tick(60)

    overlay.close()
    pygame.quit()


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="全タネ取得済みで増田の自由記述判定をテストする"
    )
    parser.add_argument("--judge", metavar="TEXT", help="GUIを開かず1回判定する")
    args = parser.parse_args(argv)

    print_runtime_diagnostics()
    manager = SeedManager()
    acquired_ids = assume_all_turning_point_seeds(manager)
    required_ids = manager.turning_points[TURNING_POINT_ID].get(
        "required_seed_ids", []
    )
    print(f"Acquired seeds: {acquired_ids}")
    if set(acquired_ids) != set(required_ids):
        print(f"WARNING: required_seed_ids differs: {required_ids}")

    if args.judge is not None:
        verdict = judge_once(manager, args.judge)
        return 2 if verdict.get("result") == "error" else 0
    run_gui(manager)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
