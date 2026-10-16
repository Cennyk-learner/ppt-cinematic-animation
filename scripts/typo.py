# -*- coding: utf-8 -*-
"""中文题材的字：在图里画的字、印章、乌丝栏。图层一律是浮点 BGRA（0..1），和 render_tools 的画面同一套。

PPT 里要改措辞的字用原生文本框（pptkit.Kit.text）；这里画的是"属于画面"的字：手迹、印章、
压在合成图里的大字。选字的思路见 references/typography.md。

    from typo import *
    lay = words('雪', find_font('演示镇魂行楷.ttf'), 330, vertical=False)
    s = seal('江山', 184, 'zhu')                         # 朱文印：红字红框
    s2 = seal('曹', 104, 'bai', font=find_font('王漢宗中魏碑簡.ttf'))   # 白文印：红底白字
    save_png('seal.png', s)
"""
import os
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont

FONT_DIRS = [os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\Windows\Fonts'), r'C:\Windows\Fonts',
             os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fonts')]
INKW = (240, 232, 216)       # 暗底上的暖白
CINNABAR = (196, 48, 30)     # 朱砂
SEAL_RED = (178, 34, 24)     # 印泥
DIM = (196, 184, 164)


def find_font(name):
    for d in FONT_DIRS:
        p = os.path.join(d, name)
        if os.path.exists(p):
            return p
    raise FileNotFoundError(name)


def missing_glyphs(font_path, text):
    """检查字库缺字：书法字体、篆书字体常缺简体字或生僻字，缺的字会被系统换成别的字体。"""
    from fontTools.ttLib import TTFont
    cmap = TTFont(font_path, lazy=True).getBestCmap()
    return [c for c in dict.fromkeys(text) if not c.isspace() and ord(c) not in cmap]


def bgr(c):
    return np.float32([c[2], c[1], c[0]]) / 255.0


def layer_from_alpha(a, rgb):
    c = bgr(rgb)
    return np.dstack([np.full_like(a, c[0]), np.full_like(a, c[1]), np.full_like(a, c[2]), a]).astype(np.float32)


def blur(img, r):
    return cv2.GaussianBlur(img, (0, 0), r) if r > 0 else img


def over(base, rgba, x=0, y=0, opacity=1.0):
    """把 BGRA 图层叠到 BGR 画面上 (x, y)"""
    h, w = rgba.shape[:2]; bh, bw = base.shape[:2]
    x0, y0, x1, y1 = max(0, x), max(0, y), min(bw, x + w), min(bh, y + h)
    if x1 <= x0 or y1 <= y0:
        return base
    l = rgba[y0 - y:y1 - y, x0 - x:x1 - x]; a = l[..., 3:4] * opacity
    base[y0:y1, x0:x1] = base[y0:y1, x0:x1] * (1 - a) + l[..., :3] * a
    return base


def save_png(path, rgba):
    cv2.imencode('.png', (np.clip(rgba, 0, 1) * 255).astype(np.uint8))[1].tofile(path)


def glyph_mask(txt, font, size, vertical=False, track=0.0, lead=1.0):
    """文字 → 0..1 蒙版（裁到字的外接框）。vertical：'\\n' 分列，列从右往左。"""
    f = ImageFont.truetype(font, size)
    cols = txt.split('\n')
    if vertical:
        n = max(len(c) for c in cols)
        w = int(size * (1 + lead) * len(cols) + size); h = int(n * size * (1 + track) + size)
        im = Image.new('L', (w, h), 0); d = ImageDraw.Draw(im)
        for ci, col in enumerate(cols):
            x = w - size * 1.5 - ci * size * (1 + lead)
            for k, ch in enumerate(col):
                bb = f.getbbox(ch)
                d.text((x + (size - (bb[2] - bb[0])) / 2 - bb[0], size * 0.5 + k * size * (1 + track)), ch, font=f, fill=255)
    else:
        w = int(sum(f.getlength(c) + track * size for c in max(cols, key=len)) + size * 2)
        h = int(size * (1 + lead) * len(cols) + size)
        im = Image.new('L', (w, h), 0); d = ImageDraw.Draw(im)
        for li, ln in enumerate(cols):
            x = size * 0.5
            for ch in ln:
                d.text((x, size * 0.3 + li * size * (1 + lead)), ch, font=f, fill=255)
                x += f.getlength(ch) + track * size
    a = np.asarray(im).astype(np.float32) / 255.0
    ys, xs = np.where(a > 0.02)
    return a[max(0, ys.min() - 3):ys.max() + 4, max(0, xs.min() - 3):xs.max() + 4] if len(xs) else a


def words(txt, font, size, rgb=INKW, vertical=False, track=0.0, lead=1.0, shadow=0.0, opacity=1.0):
    """文字图层（BGRA），可带一圈柔和的投影"""
    lay = layer_from_alpha(glyph_mask(txt, font, size, vertical, track, lead) * opacity, rgb)
    if shadow > 0:
        pad = int(size * 0.3)
        lay = cv2.copyMakeBorder(lay, pad, pad, pad, pad, cv2.BORDER_CONSTANT, value=0)
        sh = blur(lay[..., 3], max(2, size * 0.06)) * shadow
        a2 = lay[..., 3] + sh * (1 - lay[..., 3])
        lay = np.dstack([lay[..., :3] * (lay[..., 3] / np.maximum(a2, 1e-4))[..., None], a2])
    return lay


def seal(txt, size=160, kind='bai', font=None, seed=5, cols=None):
    """刻章。kind='bai' 白文（红底，字刻掉）；'zhu' 朱文（红字，红边框）。
    1–2 字一列，3–4 字两列，从右往左读。默认字体是说文篆书（全字庫說文解字），它缺很多简体字，
    名字、词句先用繁体或换成魏碑类字体（用 missing_glyphs 查）。字按实际墨迹的外接框缩放进格子，
    不靠字号估，否则篆书的空白会让字偏小偏一边。"""
    font = font or find_font('全字庫說文解字.ttf')
    n = len(txt)
    cols = cols or (1 if n <= 2 else 2)
    per = int(np.ceil(n / cols))
    S = size * 4
    m0 = S * (0.08 if kind == 'bai' else 0.14)
    cell_h = (S - 2 * m0) / per; cell_w = (S - 2 * m0) / cols
    m = Image.new('L', (S, S), 0)
    fs = int(min(cell_h, cell_w) * 1.2)
    f = ImageFont.truetype(font, fs)
    for i, ch in enumerate(txt):
        c = i // per; r = i % per
        cx = S - m0 - (c + 0.5) * cell_w; cy = m0 + (r + 0.5) * cell_h
        tmp = Image.new('L', (fs * 3, fs * 3), 0)
        ImageDraw.Draw(tmp).text((fs, fs), ch, font=f, fill=255)
        arr = np.asarray(tmp); ys, xs = np.where(arr > 30)
        if not len(xs):
            continue
        g0 = tmp.crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))
        fill = 0.92 if kind == 'bai' else 0.90
        k_ = min(cell_w * fill / g0.width, cell_h * fill / g0.height)
        g0 = g0.resize((max(1, int(g0.width * k_)), max(1, int(g0.height * k_))), Image.LANCZOS)
        m.paste(g0, (int(cx - g0.width / 2), int(cy - g0.height / 2)), g0)
    g = np.asarray(m).astype(np.float32) / 255.0
    kk = max(3, int(S * (0.028 if kind == 'bai' else 0.032)))      # 笔画加粗一点，像刻出来的
    g = blur(cv2.dilate((g > 0.4).astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kk, kk))).astype(np.float32), 1.2)
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
    edge = 0.035 * S + rng.normal(0, 0.006 * S, 4)
    box = blur(((xx > edge[0]) & (xx < S - edge[1]) & (yy > edge[2]) & (yy < S - edge[3])).astype(np.float32), 3)
    if kind == 'bai':
        a = np.clip(box - g, 0, 1)
    else:
        inner = ((xx > 0.11 * S) & (xx < 0.89 * S) & (yy > 0.11 * S) & (yy < 0.89 * S)).astype(np.float32)
        a = np.clip(np.clip(box - blur(inner, 2), 0, 1) + g * box, 0, 1)
    n1 = cv2.resize(rng.random((S // 6, S // 6)).astype(np.float32), (S, S))
    n2 = cv2.resize(rng.random((S // 40, S // 40)).astype(np.float32), (S, S), interpolation=cv2.INTER_CUBIC)
    a = a * np.clip(0.72 + 0.45 * n2, 0, 1) * (n1 > 0.06)          # 印泥不匀、边缘残破
    return layer_from_alpha(np.clip(cv2.resize(a, (size, size), interpolation=cv2.INTER_AREA) * 1.05, 0, 1), SEAL_RED)


def ink_to_alpha(img, lo=0.30, hi=0.80):
    """白纸黑字的扫描件（手迹、题字）→ 墨迹透明度。之后可以换成任意颜色、切成逐列的图层。"""
    l = img.mean(2) if img.ndim == 3 else img
    return np.clip((hi - l) / (hi - lo), 0, 1)


def column_cuts(alpha, min_gap=60, smooth=18, thr=None):
    """竖排手迹按列切：列与列之间墨迹最少的地方。返回切点列表（含 0 和宽度）。
    自动找完要看一眼：行书的长笔画会跨列，必要时手动补切点。"""
    prof = cv2.GaussianBlur(alpha.sum(0).reshape(1, -1).astype(np.float32), (0, 0), smooth).ravel()
    prof /= max(prof.max(), 1e-6)
    cuts = [0]
    for x in range(min_gap, len(prof) - min_gap):
        if prof[x] == prof[x - min_gap:x + min_gap + 1].min() and (thr is None or prof[x] < thr) and x - cuts[-1] > min_gap:
            cuts.append(x)
    return cuts + [alpha.shape[1]]


def ruled_columns(h, n, pitch, rgb=DIM, alpha=0.35, width=1):
    """乌丝栏：n+1 根细竖线"""
    a = np.zeros((h, int(pitch * n + 4)), np.float32)
    for i in range(n + 1):
        a[:, int(i * pitch) + 1:int(i * pitch) + 1 + width] = alpha
    return layer_from_alpha(a, rgb)
