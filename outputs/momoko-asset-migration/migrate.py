"""One-time, reviewed Momoko asset migration; preview by default.

Run with --apply once. Original bytes and an audit report are retained here.
This is an ID migration, not an expression draft or expression reselection.
"""

from collections import Counter
from pathlib import Path
import hashlib
import json
import re
import sys


ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
PARTS = "torso|brow|cheek|eye|mouth|effect|accessory"
TAG = re.compile(rb'\[chara_(?:show|shift)\b[^\]\r\n]*\]')
ATTRIBUTE = re.compile(
    rb'[ \t]+(?P<part>' + PARTS.encode() + rb')='
    rb'(?P<quote>[\x22\x27])(?P<value>MMK_[A-Za-z0-9_]+)(?P=quote)'
)
JSON_PART = re.compile(
    rb'(?P<prefix>"(?:' + PARTS.encode() + rb')"[ \t]*:[ \t]*")'
    rb'(?P<value>MMK_[A-Za-z0-9_]+)(?P<suffix>")'
)
REFERENCE = re.compile(rb'MMK_[A-Za-z0-9_]+')
CHANGES = {}


def add(pose, part, rows):
    for row in rows.split():
        old, new = row.split('>')
        source = f'MMK_{pose}_{part}{old}'
        target = f'MMK_{pose}_{part}{new}'
        assert source not in CHANGES, source
        CHANGES[source] = target


add('F00', 'BRO', '00_00>01_00 01_00>00_00')
add('F00', 'CHE', '00_00>03_00 04_00>00_00')
add('F00', 'EYE', '04_00>06_00 05_00>04_00 05_01>04_01 05_02>04_02 06_00>05_00')
add('F00', 'MOU', '''
00_01>04_02 04_02>05_02 06_00>10_00 07_00>13_00 08_00>13_00
09_00>06_02 10_00>06_00 11_00>07_00 03_00>01_00 12_00>03_00
13_00>08_00 14_00>12_00 15_00>11_00 16_00>14_00 17_00>15_00
18_00>16_00 19_00>09_00
''')
add('F01', 'BRO', '01_00>00_00 00_00>01_00 02_00>03_00 03_00>02_00')
# User confirmed the actual filenames, correcting CHE00_03 and MOU06_02.
add('F01', 'CHE', '00_00>03_00 03_00>00_00')
add('F01', 'EYE', '04_00>06_00 05_00>04_00 05_01>04_01 05_02>04_02 06_00>05_00')
add('F01', 'MOU', '''
00_00>02_00 00_01>02_02 01_00>03_00 02_00>00_00 03_00>03_00
03_01>04_02 03_02>02_02 04_00>06_00 04_01>04_02 04_02>03_02
05_00>10_00 06_00>06_01 08_00>13_00 09_00>14_00 10_00>15_00
11_00>13_00 12_00>01_00 13_00>08_00 14_00>12_00 15_00>11_00
16_00>00_01 17_00>01_02 18_00>04_00 19_00>04_01 20_00>09_00
21_00>16_00 011_00>13_00
''')
# The second BRO/CHE/EYE block in the instruction refers to old F03.
add('F03', 'BRO', '01_00>03_00 03_00>01_00 04_00>05_00 05_00>04_00')
add('F03', 'CHE', '00_00>03_00 03_00>00_00')
add('F03', 'EYE', '04_00>06_00 05_00>04_00 05_01>04_01 05_02>04_02 06_00>05_00')
add('F03', 'MOU', '''
00_01>02_02 00_10>15_00 01_00>03_00 01_01>02_02 01_02>00_02
02_03>00_01 03_00>05_00 03_02>03_01 03_03>00_01 04_00>06_00
04_01>03_02 04_02>05_02 05_00>10_00 06_00>06_02 07_00>07_00
08_00>13_00 09_00>14_00 11_00>13_00 12_00>01_00 13_00>08_00
14_00>12_00 15_00>11_00 16_00>01_02 17_00>06_00 18_00>04_00
19_00>04_02 20_00>10_00 21_00>16_00
''')
add('T00', 'ARM', '''
02_CLO00>03_CLO00 03_CLO00>02_CLO00 05_CLO00>00_CLO01
06_CLO00>01_CLO01 07_CLO00>03_CLO01 08_CLO00>02_CLO01
09_CLO00>04_CLO01 11_CLO00>05_CLO00 12_CLO00>05_CLO01
14_CLO00>06_CLO00 17_CLO00>07_CLO00 18_CLO00>08_CLO00
19_CLO00>09_CLO00 24_CLO00>09_CLO01 25_CLO00>03_CLO01
26_CLO00>07_CLO01 29_CLO00>08_CLO00 30_CLO00>06_CLO00
''')
add('T01', 'ARM', '''
01_CLO00>02_CLO00 02_CLO00>06_CLO00 03_CLO00>01_CLO00
05_CLO00>07_CLO00 06_CLO00>06_CLO01 10_CLO00>07_CLO01
11_CLO00>03_CLO00 12_CLO00>08_CLO00 13_CLO00>08_CLO01
18_CLO00>04_CLO00 21_CLO00>05_CLO00 22_CLO00>02_CLO01
23_CLO00>03_CLO01 26_CLO00>01_CLO01 25_CLO00>00_CLO01
31_CLO00>04_CLO01 34_CLO00>05_CLO01
''')
add('T03', 'ARM', '''
03_CLO00>01_CLO01 04_CLO00>03_CLO00 05_CLO00>02_CLO00
10_CLO00>05_CLO00 18_CLO00>05_CLO01 19_CLO00>04_CLO01
21_CLO00>00_CLO01 22_CLO00>02_CLO01 23_CLO00>03_CLO01
24_CLO00>01_CLO01 27_CLO00>04_CLO01
''')


def renumber(stem):
    return re.sub(r'^MMK_([FTE])03_', r'MMK_\g<1>02_', stem)


CHANGES = {old: renumber(new) for old, new in CHANGES.items()}
ASSETS = {p.stem for p in (ROOT / 'images/01MMK').iterdir() if p.is_file()}


def destination(source):
    target = CHANGES.get(source, renumber(source))
    # User authorized removing every reference without a surviving destination,
    # including old F03_MOU06_00 (proposed F02_MOU06_02 does not exist).
    return target if target in ASSETS else ''


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def ks_signature(raw):
    return TAG.sub(lambda m: ATTRIBUTE.sub(b'', m.group()), raw)


def json_signature(raw):
    return JSON_PART.sub(lambda m: m['prefix'] + m['suffix'], raw)


def main():
    apply = sys.argv[1:] == ['--apply']
    assert not sys.argv[1:] or apply, 'Usage: migrate.py [--apply]'
    assert not (OUT / 'report.json').exists(), 'Migration already recorded; do not remap swapped IDs twice.'
    plans = []
    totals = Counter()
    deletions = Counter()
    missing_torso_shows = []
    for path in sorted((ROOT / 'events').glob('*.ks')) + [ROOT / 'editor_data/chara_part_templates.json']:
        before = path.read_bytes()
        counts = Counter()

        def replace_attribute(match):
            source = match['value'].decode('ascii')
            target = destination(source)
            if target == source:
                return match.group()
            counts['replaced' if target else 'removed'] += 1
            if not target:
                deletions[source] += 1
            if path.suffix == '.ks':
                if not target:
                    return b''
                a, b = match.span('value')
                a -= match.start()
                b -= match.start()
                return match.group()[:a] + target.encode() + match.group()[b:]
            return match['prefix'] + target.encode() + match['suffix']

        if path.suffix == '.ks':
            after = TAG.sub(lambda m: ATTRIBUTE.sub(replace_attribute, m.group()), before)
            assert ks_signature(before) == ks_signature(after), path
            assert before.count(b'\r\n') == after.count(b'\r\n'), path
            assert before.count(b'\n') == after.count(b'\n'), path
            for number, line in enumerate(after.splitlines(), 1):
                if b'[chara_show ' in line and b'MMK_' in line and not re.search(rb'\btorso=', line):
                    missing_torso_shows.append({'file': path.relative_to(ROOT).as_posix(), 'line': number})
        else:
            after = JSON_PART.sub(replace_attribute, before)
            assert json_signature(before) == json_signature(after), path
            json.loads(after.decode('utf-8-sig'))

        unresolved = sorted({s.decode() for s in REFERENCE.findall(after) if s.decode() not in ASSETS})
        assert not unresolved, (path, unresolved)
        assert not re.search(rb'MMK_[FTE]03_', after), path
        if before != after:
            plans.append((path, before, after, dict(counts)))
            totals.update(counts)

    report = {
        'status': 'preview',
        'scope': 'events/*.ks and editor_data/chara_part_templates.json; user authorized human_confirmed files',
        'totals': {'files': len(plans), **dict(totals)},
        'removed_references': dict(sorted(deletions.items())),
        'shows_without_torso_after_authorized_removal': missing_torso_shows,
        'mapping': dict(sorted(CHANGES.items())),
        'files': [
            {'path': path.relative_to(ROOT).as_posix(), 'before_sha256': digest(before),
             'after_sha256': digest(after), **counts}
            for path, before, after, counts in plans
        ],
    }
    print(json.dumps({k: v for k, v in report.items() if k != 'mapping'}, ensure_ascii=False, indent=2))
    if not apply:
        return
    # Retain all original bytes before changing any authored source.
    for path, before, after, counts in plans:
        backup = OUT / 'before' / path.relative_to(ROOT)
        assert not backup.exists(), backup
        backup.parent.mkdir(parents=True, exist_ok=True)
        backup.write_bytes(before)
    report['status'] = 'applying'
    report_path = OUT / 'report.json'
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    for path, before, after, counts in plans:
        assert path.read_bytes() == before, f'Source changed during migration: {path}'
        path.write_bytes(after)
    for path, before, after, counts in plans:
        assert digest(path.read_bytes()) == digest(after), path
    report['status'] = 'applied'
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Migration applied; original files are in', OUT / 'before')


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
