"""Evaluate calibration or held-out answers with the actual bundled model."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.services.seed_manager import SeedManager


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--split', choices=['calibration', 'validation', 'holdout', 'all'], default='holdout')
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    dataset = json.loads((ROOT / 'data/evaluation/momoko_gd_money.json').read_text(encoding='utf-8'))
    manager = SeedManager()
    splits = ['calibration', 'validation', 'holdout'] if args.split == 'all' else [args.split]
    rows = []
    for split in splits:
        for expected, answers in dataset[split].items():
            for answer in answers:
                verdict = manager.judge_answer(dataset['turning_point_id'], answer)
                exact = verdict['result'] == expected
                # Both incorrect and borderline enter the authored retry scene.
                passed = exact or (expected == 'incorrect' and verdict['result'] == 'borderline')
                rows.append(dict(split=split, answer=answer, expected=expected,
                                 passed=passed, exact_result_match=exact, **verdict))
    report = dict(turning_point_id=dataset['turning_point_id'],
                  total=len(rows), passed=sum(row['passed'] for row in rows),
                  exact_result_matches=sum(row['exact_result_match'] for row in rows), rows=rows)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in report.items() if k != 'rows'}, ensure_ascii=False))
    for row in rows:
        if not row['passed']:
            print(json.dumps(row, ensure_ascii=False))
    return 0 if all(row['passed'] for row in rows) else 1


if __name__ == '__main__':
    raise SystemExit(main())
