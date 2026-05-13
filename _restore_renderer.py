with open(r'dialogue\text_renderer.py.orig', encoding='utf-8') as f:
    orig = f.read()

# git版の元のRUBY定数行を探して確認
for i, line in enumerate(orig.splitlines(), 1):
    if 'RUBY' in line and i < 25:
        print(f'git line {i}: {repr(line)}')

# inline_markup import と RUBY定数定義を追加する（git版にはない）
# git版のimport pygame の後に挿入
old_imports = """import pygame
from config import *
from .scroll_manager import ScrollManager
from .name_manager import get_name_manager
from .date_manager import get_current_game_date
import os"""

new_imports = """import pygame
from config import *
from .scroll_manager import ScrollManager
from .name_manager import get_name_manager
from .date_manager import get_current_game_date
from .inline_markup import (
    parse_inline_markup, has_inline_markup, wrap_markup_text,
    PlainChar, RubySpan, BotenSpan,
)
import os"""

if old_imports in orig:
    orig = orig.replace(old_imports, new_imports)
    print('imports: OK')
else:
    print('imports: MISS')

# RUBY定数（git版には存在しないはずなので追加）
ruby_const = """RUBY_FONT_RATIO = float(TEXT_RENDERER_CONFIG.get('ruby_font_ratio', 0.45))
RUBY_MARGIN_PX  = int(TEXT_RENDERER_CONFIG.get('ruby_margin_px', 2))

class TextRenderer:"""
if 'RUBY_FONT_RATIO' not in orig:
    orig = orig.replace('\nclass TextRenderer:', '\n' + ruby_const)
    print('ruby const: inserted')
else:
    print('ruby const: already present')

with open(r'dialogue\text_renderer.py', 'w', encoding='utf-8') as f:
    f.write(orig)
print('written OK')
