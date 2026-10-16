# -*- coding: utf-8 -*-
"""围绕一幅画、一张老照片做动画时反复用到的合成函数。画面是 1920x1080 的浮点 BGR（0..1）。

    from scene_tools import *
    snow = Snow(n=32, count=1200)                       # 正好 32 帧一圈的雪
    frames = [plate * (1 - s[..., None] * .8) + s[..., None] * .92 for s in (snow.frame(i) for i in range(32))]

函数一览：
  cover / fit / radial / vignette / shade_bottom / grain    取景、光、暗角、底部压暗、颗粒
  Snow                         无缝循环的雪：每片雪在一圈里正好落整数个屏高，首尾天然接上
  mist_field                   横向可平铺的雾气噪声（np.roll 平移即无缝）
  light_spread_frames          "一点光长成太阳，光从它铺开照亮整幅画"的开场帧
  bloom_frames                 灰 → 彩色从一点晕开（只放一遍的进页动图）
  bleed_layers                 A 画面像墨晕一样一块块变成 B：出 n 张逐级扩大的透明图层，原生淡入依次叠
  loupe_png                    圆形放大镜（带边和投影）
  photo_print                  老照片：灰阶 + 冷调 + 白边
  selective_tint               只给老照片里的某样东西上色（如红旗），其余保持黑白
  unblend_watermark            去掉半透明白色水印（百科、图库的 logo）
"""
import numpy as np, cv2

W, H = 1920, 1080
Y, X = np.mgrid[0:H, 0:W].astype(np.float32)


def blur(img, r):
    return cv2.GaussianBlur(img, (0, 0), r) if r > 0 else img


def cover(img, w=W, h=H, cx=0.5, cy=0.5, zoom=1.0):
    """铺满 w x h，(cx, cy) 是原图里想放在画面中心的位置（比例），zoom>1 推近"""
    ih, iw = img.shape[:2]
    s = max(w / iw, h / ih) * zoom
    nw, nh = int(round(iw * s)), int(round(ih * s))
    r = cv2.resize(img, (nw, nh), interpolation=cv2.INTER_AREA if s < 1 else cv2.INTER_CUBIC)
    x0 = int(np.clip(cx * nw - w / 2, 0, nw - w)); y0 = int(np.clip(cy * nh - h / 2, 0, nh - h))
    return r[y0:y0 + h, x0:x0 + w]


def fit(img, w, h):
    ih, iw = img.shape[:2]
    s = min(w / iw, h / ih)
    return cv2.resize(img, (int(iw * s), int(ih * s)), interpolation=cv2.INTER_AREA if s < 1 else cv2.INTER_CUBIC)


def radial(cx, cy, r, p=1.6):
    return np.exp(-(np.sqrt((X - cx) ** 2 + (Y - cy) ** 2) / r) ** p)


def vignette(strength=0.5, power=2.2):
    d = np.sqrt(((X - W / 2) / (W / 2)) ** 2 + ((Y - H / 2) / (H / 2)) ** 2) / np.sqrt(2)
    return (1 - strength * d ** power)[..., None]


def shade_bottom(img, start=0.62, k=0.8):
    a = np.clip((Y / H - start) / (1 - start), 0, 1)[..., None] ** 1.2
    return img * (1 - k * a)


def grain(img, amt=0.018, seed=1):
    """胶片颗粒。动图里每帧用同一个 seed：逐帧换颗粒会让 GIF 体积翻几倍"""
    r = np.random.default_rng(seed)
    return np.clip(img + blur(r.normal(0, 1, (H, W)).astype(np.float32), 0.7)[..., None] * amt, 0, 1)


def ease(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def seg(t, a, b):
    return float(np.clip((t - a) / (b - a), 0, 1))


class Snow:
    """无缝循环的雪。每层 (占比, 一圈落几个屏高, 半径, 模糊, 透明度)：近处的大、虚、快，远处的小、实、慢。
    一圈 24–32 帧就够；片数和层数直接决定 GIF 体积（1500 片 x 40 帧可以到 25 MB）。"""
    def __init__(self, n=32, count=1000, seed=3, wind=0.0, size=1.0, w=W, h=H,
                 layers=((0.6, 1, 1.0, 0.5, 0.5), (0.3, 2, 1.6, 0.9, 0.62), (0.1, 3, 2.5, 2.0, 0.45))):
        r = np.random.default_rng(seed)
        self.n, self.w, self.h, self.fl = n, w, h, []
        for frac, k, rad, bl, al in layers:
            m = int(count * frac)
            self.fl.append(dict(x=r.random(m) * w, y=r.random(m) * (h + 60), k=k, rad=rad * size, bl=bl * size,
                                ph=r.random(m) * 6.283, amp=r.random(m) * 10 * k, a=al * (0.5 + 0.5 * r.random(m)), wind=wind * k))

    def frame(self, i):
        out = np.zeros((self.h, self.w), np.float32)
        t = i / self.n
        for L in self.fl:
            lay = np.zeros((self.h, self.w), np.float32)
            y = (L['y'] + t * L['k'] * (self.h + 60)) % (self.h + 60) - 30
            x = (L['x'] + L['amp'] * np.sin(6.283 * t * 2 + L['ph']) + L['wind'] * t * self.w) % self.w
            r = L['rad']; streak = r * (0.2 + 0.12 * L['k'])
            for xx, yy, aa in zip(x, y, L['a']):
                cv2.ellipse(lay, (int(xx * 4), int(yy * 4)), (max(1, int(r * 4)), max(1, int((r + streak) * 4))),
                            0, 0, 360, float(aa), -1, cv2.LINE_AA, shift=2)
            out = np.maximum(out, blur(lay, L['bl']) * (1.0 + 0.4 * L['bl']))
        return np.clip(out, 0, 1)


def periodic_noise(h, w, cy, cx, seed=0):
    g = np.random.default_rng(seed).random((cy, cx)).astype(np.float32)
    return cv2.resize(np.hstack([g, g, g]), (w * 3, h), interpolation=cv2.INTER_CUBIC)[:, w:2 * w]


def mist_field(h, w, seed=0):
    n = periodic_noise(h, w, 6, 10, seed) * 0.6 + periodic_noise(h, w, 14, 24, seed + 1) * 0.3 + periodic_noise(h, w, 30, 52, seed + 2) * 0.1
    return np.clip((n - 0.35) * 2.2, 0, 1)


def light_spread_frames(lit, sun_xy, sun_r, sun_rgb_bgr, n=60, fps=12.5, t_dot=(0.4, 1.8), t_spread=(2.0, 4.8)):
    """开场：黑场里亮起一点，长成太阳（半径 sun_r），然后光从它向外铺开，揭示整张 lit。
    返回帧列表，配 gif(..., loop=-1) 只放一遍；之后让底下的静帧接住。"""
    sx, sy = sun_xy
    d = np.sqrt((X - sx) ** 2 + (Y - sy) ** 2)
    frames = []
    for i in range(n):
        t = i / fps
        f = np.zeros((H, W, 3), np.float32)
        g = ease(seg(t, *t_dot))
        if g > 0:
            disc = np.clip((sun_r * g - d) / 2.0, 0, 1)
            halo = np.exp(-(d / (sun_r * (1.5 + 3.5 * g))) ** 2) * 0.28 * g * (1 - disc)
            f = f + disc[..., None] * sun_rgb_bgr * (0.85 + 0.25 * g) + halo[..., None] * np.float32([0.10, 0.22, 0.62])
        r = ease(seg(t, *t_spread)) ** 1.1 * 2600
        if r > 1:
            m = np.clip(1 - (d - r) / (0.9 * r + 260), 0, 1)[..., None] ** 1.8
            f = np.maximum(f * (1 - seg(t, t_spread[0] + 0.6, t_spread[1] - 0.4)), lit * m)
        frames.append(f)
    return frames


def bloom_frames(color, cx, cy, n=46, fps=12.5, t=(0.3, 3.2), seed=4):
    """从 (cx, cy) 向外，灰阶画面带着不规则的边缘晕成彩色"""
    gray = color.mean(2, keepdims=True)
    gray = (gray - 0.5) * 0.9 + 0.48
    nz = cv2.resize(np.random.default_rng(seed).random((18, 32)).astype(np.float32), (W, H), interpolation=cv2.INTER_CUBIC)
    dist = np.sqrt((X - cx) ** 2 + ((Y - cy) / 0.8) ** 2) / 1400 + (nz - 0.5) * 0.25
    out = []
    for i in range(n):
        r = ease(seg(i / fps, *t)) * 1.35
        m = np.clip((r - dist) / 0.12, 0, 1)[..., None]
        out.append(gray * (1 - m) + color * m)
    return out


def bleed_layers(target, origin_xy, steps=6, seed=7):
    """A → B 的墨晕式转场：返回 steps 张 (BGR, alpha)，第 k 张露出更大一片 B。
    在 PPT 里把它们叠在 A 上面、依次淡入（间隔 0.7 秒、各 1.1 秒），最后一张是满幅。"""
    r = np.random.default_rng(seed)
    nz = cv2.resize(r.random((14, 25)).astype(np.float32), (W, H), interpolation=cv2.INTER_CUBIC) * 0.6 + \
        cv2.resize(r.random((48, 85)).astype(np.float32), (W, H), interpolation=cv2.INTER_CUBIC) * 0.4
    ox, oy = origin_xy
    field = np.sqrt((X - ox) ** 2 + (Y - oy) ** 2) / np.sqrt(W ** 2 + H ** 2) * 1.25 + (nz - 0.5) * 0.35
    out = []
    for k, th in enumerate(np.linspace(field.min() + 0.08, field.max() + 0.02, steps)):
        a = np.ones((H, W), np.float32) if k == steps - 1 else blur(np.clip((th - field) / 0.07, 0, 1), 3)
        out.append((target, a))
    return out


def loupe_png(src, cx, cy, R=210, zoom=2.0, ring_rgb_bgr=(0.85, 0.88, 0.92)):
    """圆形放大镜：取 src 里 (cx, cy) 附近，放大 zoom 倍，带细边和柔和投影。返回 BGRA。"""
    half = int(R / zoom)
    crop = src[cy - half:cy + half, cx - half:cx + half]
    big = cv2.resize(crop, (2 * R, 2 * R), interpolation=cv2.INTER_CUBIC)
    yy, xx = np.mgrid[0:2 * R, 0:2 * R].astype(np.float32)
    d = np.sqrt((xx - R) ** 2 + (yy - R) ** 2)
    disc = np.clip(R - 6 - d, 0, 1); ring = np.clip(1 - np.abs(d - (R - 4)) / 2.5, 0, 1)
    pad = 40; S = 2 * R + 2 * pad
    out = np.zeros((S, S, 4), np.float32)
    sh = np.zeros((S, S), np.float32); cv2.circle(sh, (S // 2 + 6, S // 2 + 12), R, 1.0, -1)
    out[..., 3] = blur(sh, 18) * 0.7
    reg = out[pad:pad + 2 * R, pad:pad + 2 * R]
    reg[..., :3] = big * disc[..., None] + np.float32(ring_rgb_bgr) * ring[..., None] * (1 - disc[..., None])
    reg[..., 3] = np.maximum(reg[..., 3], np.maximum(disc, ring))
    return out


def photo_print(im, w, border=10, bw=True, paper=(0.86, 0.90, 0.93)):
    """一张老照片：等比缩到宽 w，灰阶略偏冷，带白边。返回 BGR（放进 PPT 后加投影、转一两度）"""
    h = int(round(w * im.shape[0] / im.shape[1]))
    c = cv2.resize(im, (w, h), interpolation=cv2.INTER_AREA)
    if bw:
        g = c.mean(2, keepdims=True)
        c = np.clip((g - 0.5) * 1.06 + 0.5, 0, 1) * np.float32([0.88, 0.95, 1.02])
    canvas = np.ones((h + 2 * border, w + 2 * border, 3), np.float32) * np.float32(paper)
    canvas[border:border + h, border:border + w] = c
    return canvas


def selective_tint(orig, tinted, rgb_bgr=(0.16, 0.20, 0.92), gain=3.0, bias=0.15):
    """只给黑白老照片里的某样东西上色。tinted 是生图工具"只把旗子染红、其余不动"的编辑结果；
    这里只取它红的那一块的位置，颜色加在原照片上，原照片其余像素一点不动（生成图对人脸、颗粒的改动不进成品）。"""
    tinted = cv2.resize(tinted, (orig.shape[1], orig.shape[0]), interpolation=cv2.INTER_AREA)
    m = blur(np.clip((tinted[..., 2] - np.maximum(tinted[..., 1], tinted[..., 0])) * gain - bias, 0, 1), 1.0)
    g = orig.mean(2, keepdims=True)
    base = np.clip((g - 0.5) * 1.06 + 0.5, 0, 1) * np.float32([0.88, 0.95, 1.02])
    col = np.clip(g * 1.25, 0, 1) * np.float32(rgb_bgr)
    return base * (1 - m[..., None]) + col * m[..., None]


def unblend_watermark(img, box, thr=24, pad=70):
    """去半透明白色水印。img 是 0..255 的 float BGR，box=(x0, y0, x1, y1) 圈住水印。
    水印 = alpha*白 + (1-alpha)*底；用局部亮度差找出 logo，估出 alpha 反推底色，边缘再补一圈。
    残影明显时，把这一块裁出来交给生图工具"只去水印"，再按 logo 外接框柔边贴回（颜色先匹配到周围）。"""
    x0, y0, x1, y1 = box
    reg = img[y0:y1, x0:x1].copy()
    big = cv2.copyMakeBorder(reg, pad, pad, pad, pad, cv2.BORDER_REFLECT)
    L = big.mean(2)
    bg = cv2.medianBlur(np.clip(L, 0, 255).astype(np.uint8), 81).astype(np.float32)
    m = ((L - bg)[pad:-pad, pad:-pad] > thr).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
    inner = cv2.erode(m, np.ones((3, 3), np.uint8)).astype(bool)
    bgc = cv2.inpaint(reg.astype(np.uint8), cv2.dilate(m, np.ones((9, 9), np.uint8)), 9, cv2.INPAINT_NS).astype(np.float32)
    alpha = float(np.median(np.clip((reg - bgc) / np.maximum(255 - bgc, 1), 0, 0.9).mean(2)[inner])) if inner.any() else 0.5
    soft = cv2.GaussianBlur(m.astype(np.float32), (0, 0), 0.8)[..., None]
    unb = (reg - alpha * soft * 255.0) / (1 - alpha * soft)
    unb = unb + cv2.GaussianBlur(bgc - unb, (0, 0), 4) * soft * 0.85
    ring = cv2.dilate(m, np.ones((5, 5), np.uint8)) - cv2.erode(m, np.ones((3, 3), np.uint8))
    img[y0:y1, x0:x1] = cv2.inpaint(np.clip(unb, 0, 255).astype(np.uint8), ring, 4, cv2.INPAINT_TELEA).astype(np.float32)
    return img, m
