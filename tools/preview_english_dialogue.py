"""Render English/mixed dialogue through the runtime and real presentation path.

Run with .venv-gd/Scripts/python.exe tools/preview_english_dialogue.py.
Only PNGs and a JSON report in the output directory are written; no scenario or
save data is modified. SDL dummy permits repeatable offscreen verification.
"""
import argparse
import json
import os
from pathlib import Path
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pygame

from core import config
from core.runtime.window_controller import WindowController
from dialogue.backlog_manager import BacklogManager
from dialogue.text_renderer import TextRenderer


ENGLISH = (
    'The rain had finally stopped, but the street was still empty. '
    'I could hear footsteps behind me, slow and steady. '
    '"Did you find the [seed id="LETTER"]blue envelope[/seed]?" she asked. '
    'Dr. Smith had left at 3.14, and nobody had seen him since. '
    'I looked back at the house. A single light was still burning in the window.'
)
MIXED = '彼は Good morning と言って、{封筒|ふうとう}を指した。中には [seed id="KEY"]small key[/seed] が入っていた。'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path,
                        default=Path('outputs/english-dialogue-preview'))
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    pygame.init()
    window = pygame.display.set_mode((640, 480))
    screen = pygame.Surface((1440, 1080))
    config._recalculate_screen_metrics(640, 480)
    presenter = WindowController(window, screen)
    presenter.pointer_image = None
    renderer = TextRenderer(screen)
    renderer.seed_manager = type('Seeds', (), {'can_show': lambda self, seed: True})()
    backlog = BacklogManager(screen)
    backlog.set_text_renderer(renderer)
    renderer.set_backlog_manager(backlog)
    title_font = pygame.font.Font(None, 32)
    frames = []

    def snapshot(name, label, *, history=False):
        screen.fill((24, 34, 48))
        screen.blit(title_font.render(label, True, (205, 216, 226)), (48, 170))
        renderer.render()
        if history:
            backlog.render()
        presenter.present_virtual_screen()
        pygame.display.flip()
        pygame.image.save(screen, str(args.output_dir / f'{name}-1440.png'))
        pygame.image.save(window, str(args.output_dir / f'{name}-640.png'))
        frames.append(screen.copy())

    renderer.set_dialogue(ENGLISH, 'Alex')
    layout = renderer._get_text_layout(ENGLISH)
    renderer.displayed_chars = layout.lines[2].end
    snapshot('english-page1', 'English / first three rows / no inserted hyphens')
    renderer.displayed_chars = layout.lines[3].activation
    snapshot('english-page2-start', 'English / fourth row starts the next page')
    renderer.skip_text()
    snapshot('english-complete', 'English / final paragraph row aligned left')
    renderer.set_dialogue(MIXED, '主人公')
    renderer.skip_text()
    snapshot('mixed', 'Mixed dialogue / existing font and grid / word wrapping')
    mixed_layout = renderer._get_text_layout(MIXED)
    backlog.open_backlog()
    snapshot('backlog', 'Backlog / identical full-dialogue layout', history=True)

    sheet = pygame.Surface((1440, 1620))
    sheet.fill((0, 0, 0))
    for i, frame in enumerate(frames):
        sheet.blit(pygame.transform.smoothscale(frame, (720, 540)),
                   ((i % 2) * 720, (i // 2) * 540))
    pygame.image.save(sheet, str(args.output_dir / 'contact-sheet.png'))
    report = {
        'english_font': config.ENGLISH_FONT_FILENAME,
        'english_font_size': config.ENGLISH_FONT_SIZE,
        'char_spacing_px': renderer.char_spacing,
        'dialogue_position': [renderer.text_start_x, renderer.text_start_y],
        'max_rows': renderer.max_display_lines,
        'char_delay_ms': renderer.char_delay,
        'line_width_px': renderer.text_grid_width() * renderer.max_chars_per_line,
        'english': [dict(text=line.markup, width=line.width,
                         justified=line.justified, paragraph_last=line.paragraph_last,
                         activation=line.activation) for line in layout.lines],
        'mixed': [dict(text=line.markup, english=line.english,
                       justified=line.justified) for line in mixed_layout.lines],
        'presentation': [640, 480],
    }
    (args.output_dir / 'report.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    pygame.quit()
    print(f'ENGLISH_DIALOGUE_PREVIEW_OK: {args.output_dir}')


if __name__ == '__main__':
    main()
