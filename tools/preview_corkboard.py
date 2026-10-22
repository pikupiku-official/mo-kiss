"""Preview the production board without changing the player's progress.

Examples:
  .venv-gd/Scripts/python.exe tools/preview_corkboard.py --sample
  .venv-gd/Scripts/python.exe tools/preview_corkboard.py --sample --snapshot outputs/board.png
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample", action="store_true", help="Use an isolated profile and the six existing tutorial clues")
    parser.add_argument("--animate", action="store_true", help="Preview the skippable arrival animation")
    parser.add_argument("--snapshot", type=Path, help="Write a PNG and its scaled window version, then exit")
    parser.add_argument("--tab", choices=("all", "momoko", "sanako", "other"), default="all")
    parser.add_argument("--hover", help="Focus and highlight a clue without opening its speech panel")
    parser.add_argument("--select", help="Focus a clue and open its recorded speech panel")
    args = parser.parse_args()
    previous_profile = os.environ.get("MOKISS_PROFILE_ROOT")
    previous_qt_platform = os.environ.get("QT_QPA_PLATFORM")
    with tempfile.TemporaryDirectory(prefix="mokiss-board-preview-") as profile:
        if args.sample:
            os.environ["MOKISS_PROFILE_ROOT"] = profile
        try:
            run(args)
        finally:
            if previous_profile is None:
                os.environ.pop("MOKISS_PROFILE_ROOT", None)
            else:
                os.environ["MOKISS_PROFILE_ROOT"] = previous_profile
            if previous_qt_platform is None:
                os.environ.pop("QT_QPA_PLATFORM", None)
            else:
                os.environ["QT_QPA_PLATFORM"] = previous_qt_platform


def run(args):
    # This preview has an SDL window, not a Qt window. core.config and
    # TextRenderer support this mode without initializing QApplication or
    # loading platform plugins. Set it BEFORE importing either module; leave
    # SDL_VIDEODRIVER alone so the interactive Pygame window remains visible.
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    import pygame
    from core import config
    from core.services.seed_manager import SeedManager
    from dialogue.dialogue_loader import DialogueLoader
    from dialogue.text_renderer import TextRenderer
    from home.corkboard import CorkboardView

    pygame.init()
    window = pygame.display.set_mode((960, 720), pygame.RESIZABLE)
    pygame.display.set_caption("コルクボード確認" + ("（サンプル）" if args.sample else ""))
    surface = pygame.Surface((1440, 1080))
    config.OFFSET_X = config.OFFSET_Y = 0
    config.SCALE = 1.0
    renderer = TextRenderer(surface)
    manager = SeedManager(str(ROOT))
    new_ids = []
    if args.sample:
        for name in ("TANE_MASUDA_01", "TANE_MASUDA_02", "TANE_MASUDA_03", "DEV_MOMOKO_SEEDS"):
            loader = DialogueLoader(debug=False)
            lines = loader.load_dialogue_from_ks(str(ROOT / "events" / f"{name}.ks"))
            manager.begin_event(name)
            renderer.configure_seed_context(manager, name)
            # These sample scripts have a linear main route; optional annotations
            # are separated by the loader and deliberately never visited here.
            for line in lines:
                if line.get("type") == "dialogue":
                    renderer.set_dialogue(line.get("text", ""), line.get("character", ""),
                                          force_female=bool(line.get("force_female", False)))
            manager.complete_event(name, "1999-06-01")
        new_ids = manager.finalize_day("1999-06-01")
    board = CorkboardView(surface, manager, renderer, new_ids if args.animate else ())
    if not args.animate:
        board.tab = args.tab
        board.fit()
    focus_id = args.select or args.hover
    if focus_id and focus_id in board.entries:
        board.focus(board.entries[focus_id])
        point = board.screen_rect(board.entries[focus_id]).center
        board.handle_events([pygame.event.Event(pygame.MOUSEMOTION, pos=point, rel=(0, 0), buttons=(0, 0, 0))])
        if args.select:
            board.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=point, button=1)])
    if args.snapshot:
        board.render()
        args.snapshot.parent.mkdir(parents=True, exist_ok=True)
        pygame.image.save(surface, str(args.snapshot))
        scaled = pygame.transform.smoothscale(surface, window.get_size())
        window.blit(scaled, (0, 0))
        pygame.display.flip()
        scaled_path = args.snapshot.with_name(args.snapshot.stem + "-window.png")
        pygame.image.save(window, str(scaled_path))
        print(f"Saved {args.snapshot} and {scaled_path} (SDL: {pygame.display.get_driver()})")
        pygame.quit()
        return
    clock = pygame.time.Clock()
    running = True
    while running:
        events = []
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                running = False
                continue
            if hasattr(event, "pos"):
                attrs = event.dict.copy()
                sx, sy = 1440 / window.get_width(), 1080 / window.get_height()
                attrs["pos"] = (round(event.pos[0] * sx), round(event.pos[1] * sy))
                if hasattr(event, "rel"):
                    attrs["rel"] = (round(event.rel[0] * sx), round(event.rel[1] * sy))
                event = pygame.event.Event(event.type, attrs)
            events.append(event)
        if board.handle_events(events) == "back":
            running = False
        board.update()
        board.render()
        window.blit(pygame.transform.smoothscale(surface, window.get_size()), (0, 0))
        pygame.display.flip()
        clock.tick(60)
    pygame.quit()


if __name__ == "__main__":
    main()
