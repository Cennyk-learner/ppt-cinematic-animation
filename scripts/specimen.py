# -*- coding: utf-8 -*-
"""字样表：把候选字体排在同一张暗底图上比，选字前先看这一张。

  python specimen.py out.jpg 字体文件或目录 [更多…] [--title 江山如此多娇] [--line 须晴日，看红装素裹，分外妖娆。一九三六]

每格：字体名、一行大标题、一行小字。缺字会被标红（换了字体回退的字在 PPT 里会变成别的字体）。
"""
import os, sys, glob
from PIL import Image, ImageDraw, ImageFont

args = sys.argv[1:]
title, line = '江山如此多娇', '须晴日，看红装素裹，分外妖娆。一九三六'
if '--title' in args:
    i = args.index('--title'); title = args[i + 1]; del args[i:i + 2]
if '--line' in args:
    i = args.index('--line'); line = args[i + 1]; del args[i:i + 2]
out, srcs = args[0], args[1:]
fonts = []
for s in srcs:
    fonts += sorted(glob.glob(os.path.join(s, '*.[ot]t[fc]'))) if os.path.isdir(s) else [s]

try:
    from fontTools.ttLib import TTFont
except ImportError:
    TTFont = None
BG, FG, ACC, GREY, RED = (22, 19, 16), (236, 226, 208), (205, 185, 150), (150, 140, 125), (220, 70, 50)
cw, ch = 960, 210
rows = (len(fonts) + 1) // 2
im = Image.new('RGB', (cw * 2, ch * max(rows, 1)), BG)
d = ImageDraw.Draw(im)
label = ImageFont.load_default()
for k, p in enumerate(fonts):
    x, y = (k % 2) * cw, (k // 2) * ch
    name = os.path.basename(p)
    miss = ''
    if TTFont:
        try:
            cmap = TTFont(p, fontNumber=0, lazy=True).getBestCmap()
            miss = ''.join(c for c in dict.fromkeys(title + line) if not c.isspace() and ord(c) not in cmap)
        except Exception:
            pass
    d.text((x + 24, y + 12), name + (f'   缺字: {miss}' if miss else ''), font=label, fill=RED if miss else GREY)
    try:
        d.text((x + 24, y + 40), title, font=ImageFont.truetype(p, 92), fill=FG)
        d.text((x + 24, y + 150), line, font=ImageFont.truetype(p, 34), fill=ACC)
    except Exception as e:
        d.text((x + 24, y + 60), str(e)[:60], font=label, fill=RED)
    d.line([(x, y + ch - 1), (x + cw, y + ch - 1)], fill=(45, 40, 35))
im.save(out, quality=88)
print(out, len(fonts), 'fonts')
