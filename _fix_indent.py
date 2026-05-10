import re, sys

path = r'c:\Users\kohet\モーキス作業ディレクトリ\main.py'
content = open(path, encoding='utf-8').read()

# 問題箇所: "        def handle_menu_events" (8スペース) を "    def handle_menu_events" (4スペース) に修正
fixed = content.replace(
    '        def handle_menu_events(self, events):\n        ',
    '    def handle_menu_events(self, events):\n        '
)

if fixed == content:
    print('NOT MATCHED - trying alternative')
    # 改行コードCRLFの場合
    fixed = content.replace(
        '        def handle_menu_events(self, events):\r\n        ',
        '    def handle_menu_events(self, events):\r\n        '
    )

if fixed == content:
    print('STILL NOT MATCHED')
    # デバッグ: 問題行を表示
    for i, line in enumerate(content.splitlines(), 1):
        if 'handle_menu_events' in line:
            print(f'L{i}: {repr(line)}')
    sys.exit(1)

open(path, 'w', encoding='utf-8').write(fixed)
print('OK')
