# 合成用的通用小工具。画面一律是 1920x1080 的浮点 BGR（0..1），和 fx.py 放在同一目录：
#     from render_tools import *
# 这里只放反复要用、而且容易写错的东西；每一幕具体怎么合成，请按内容自己写。
import os, json, math, subprocess
import numpy as np, cv2
from fx import *            # W, H, load, save, blur, vignette, Rain ...

Y, X = np.mgrid[0:H, 0:W].astype(np.float32)
_rng = np.random.default_rng(11)
NOISE = cv2.resize(_rng.random((9, 32)).astype(np.float32), (W * 2, H), interpolation=cv2.INTER_CUBIC)
NOISE2 = cv2.resize(_rng.random((20, 70)).astype(np.float32), (W * 2, H), interpolation=cv2.INTER_CUBIC)


# ---------------- 收尾：顶部压暗（给标题栏留位置）+ 暗角 ----------------
def top_dark(h=190, k=0.88):
    return (1 - k * np.clip((h - Y) / h, 0, 1) ** 1.3)[..., None]


GL, VIG = top_dark(), vignette(0.45)


def fin(f, gl=None):
    return np.clip(f * (GL if gl is None else gl) * VIG, 0, 1)


def small(f, size=(1280, 720)):
    return cv2.resize(f, size, interpolation=cv2.INTER_AREA)


def still(path, img, gl=None):
    save(path, small(fin(img, gl)))


# ---------------- 氛围 ----------------
def haze(t, speed=40.0):
    """横向漂移的雾气噪声，HxW 0..1"""
    o1 = int(t * speed) % W; o2 = int(t * speed * 1.7) % W
    return NOISE[:, o1:o1 + W] * 0.65 + NOISE2[:, o2:o2 + W] * 0.35


def pool(cx, cy, r, sq=1.0):
    """一团柔光，中心 1，向外衰减"""
    d2 = ((X - cx) / r) ** 2 + ((Y - cy) / (r * sq)) ** 2
    return 1.0 / (1.0 + d2) ** 1.6


def blink(i, n, pulses=1, width=0.22, ph0=0.0):
    """第 i 帧（共 n 帧一圈）的闪烁强度，一圈闪 pulses 次；首尾相接"""
    ph = (i / n * pulses + ph0) % 1.0
    d = min(abs(ph - 0.3), 1 - abs(ph - 0.3))
    return math.exp(-(d / width) ** 2 * 4)


# ---------------- 动图 ----------------
def gif(path, frames, fps=12.5, size=(1280, 720), colors=256, loop=0, bayer=4):
    """frames 是逐帧画面的迭代器。loop=0 无限循环；loop=-1 只放一遍停在最后一帧。
    注意：PPT 里的动图从进入这一页就开始走，只放一遍的动图只能用在进页第一幕。"""
    pr = None; n = 0
    for f in frames:
        if pr is None:
            h, w = f.shape[:2]
            pr = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{w}x{h}", "-r", str(fps), "-i", "-",
                                   "-filter_complex", f"scale={size[0]}:{size[1]}:flags=lanczos,split[a][b];[a]palettegen=max_colors={colors}:stats_mode=full[p];"
                                   f"[b][p]paletteuse=dither=bayer:bayer_scale={bayer}:diff_mode=rectangle", "-loop", str(loop), path], stdin=subprocess.PIPE)
        pr.stdin.write((np.clip(f, 0, 1) * 255).astype(np.uint8).tobytes()); n += 1
    pr.stdin.close(); pr.wait()
    print(os.path.basename(path), n, "frames", os.path.getsize(path) // 1024, "KB", flush=True)


def loop_gif(path, fn, n=20, nx=5, dt=0.08, **kw):
    """无缝循环动图：fn(i, t) 返回第 i 帧。多算 nx 帧，和开头交叉淡化，雨雪这类不成周期的运动也看不出接缝。"""
    fr = [fin(fn(i, 10 + i * dt)) for i in range(n + nx)]
    for i in range(nx):
        a = (i + 0.5) / nx
        fr[i] = fr[i] * a + fr[n + i] * (1 - a)
    gif(path, fr[:n], fps=1 / dt, **kw)


# ---------------- 透明图层 ----------------
def wrgba(path, bgr, a, crop=True, pad=6):
    """写透明 PNG。bgr 是 HxWx3 画面或一个 BGR 颜色；a 是 HxW 的 0..1 透明度。
    crop=True 时裁到不透明区域的外接框，返回它在 960x540 版面上的 [x, y, w, h]，组装时照这个位置摆。"""
    a = np.clip(a, 0, 1)
    if np.ndim(bgr) == 1:
        bgr = np.ones(a.shape + (3,), np.float32) * np.float32(bgr)
    x0, y0, x1, y1 = 0, 0, a.shape[1], a.shape[0]
    if crop:
        ys, xs = np.where(a > 0.01)
        x0, x1 = max(0, xs.min() - pad), min(a.shape[1], xs.max() + pad + 1)
        y0, y1 = max(0, ys.min() - pad), min(a.shape[0], ys.max() + pad + 1)
    out = np.dstack([np.clip(bgr, 0, 1), a])[y0:y1, x0:x1]
    cv2.imencode(".png", (out * 255).astype(np.uint8))[1].tofile(path)
    k = 960.0 / a.shape[1]
    return [round(x0 * k, 2), round(y0 * k, 2), round((x1 - x0) * k, 2), round((y1 - y0) * k, 2)]


def putpos(path, key, val):
    """把位置、时间点这类数字记进一个 JSON，组装脚本读它，不要手抄坐标"""
    d = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else {}
    d[key] = val
    txt = json.dumps(d, ensure_ascii=False, default=lambda o: o.item() if hasattr(o, "item") else o.tolist())   # 先序列化再写，numpy 数也能存
    with open(path, "w", encoding="utf-8") as f:
        f.write(txt)


# ---------------- 线 ----------------
def dense(pts, step=2.0):
    pts = np.float32(pts); out = [pts[0]]
    for a, b in zip(pts[:-1], pts[1:]):
        n = max(1, int(np.hypot(*(b - a)) / step))
        for i in range(1, n + 1):
            out.append(a + (b - a) * i / n)
    return np.float32(out)


def chaikin(pts, it=3, closed=False):
    """把手点的折线磨圆"""
    p = np.float32(pts)
    for _ in range(it):
        q = np.roll(p, -1, 0) if closed else p[1:]
        a = p if closed else p[:-1]
        new = np.empty((len(a) * 2, 2), np.float32)
        new[0::2] = a * 0.75 + q * 0.25; new[1::2] = a * 0.25 + q * 0.75
        p = new if closed else np.vstack([p[:1], new, p[-1:]])
    return p


def line_layer(pts, thick=3, dash=0, gap=0):
    """折线画成 HxW 的 0..1 图层；dash>0 时按弧长画虚线"""
    lay = np.zeros((H, W), np.float32)
    pts = np.float32(pts)
    if not dash:
        cv2.polylines(lay, [np.int32(np.round(pts * 4))], False, 1.0, thick, cv2.LINE_AA, shift=2)
        return lay
    pts = dense(pts, 2.0)
    d = np.r_[0, np.cumsum(np.hypot(*np.diff(pts, axis=0).T))]
    t = 0.0
    while t < d[-1]:
        sg = pts[(d >= t) & (d <= t + dash)]
        if len(sg) >= 2:
            cv2.polylines(lay, [np.int32(np.round(sg * 4))], False, 1.0, thick, cv2.LINE_AA, shift=2)
        t += dash + gap
    return lay


def glow(lay, r=7, g=0.9):
    """线条加一圈柔光后的透明度"""
    return np.clip(lay + blur(lay, r) * g, 0, 1)


def pct(pts):
    """画面百分比坐标 → 像素坐标。配合 grid_view 读出来的坐标用"""
    return np.float32([(a * W / 100.0, b * H / 100.0) for a, b in pts])


# ---------------- 成对图里找东西 ----------------
def slide_mask(before, after, mask_img=None, thr=0.05):
    """滑动体蒙版：有红色分割图就用它（红=会动的部分），否则用前后两张图的差。返回 HxW 0..1"""
    if mask_img is not None:
        m = ((mask_img[..., 2] > 0.5) & (mask_img[..., 1] < 0.35)).astype(np.float32)
        if 0.02 < m.mean() < 0.6:
            return blur(m, 6)
    d = blur(np.abs(before - after).mean(2), 9)
    m = (d > thr).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((41, 41), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(m)
    if n > 1:
        m = (lab == 1 + np.argmax(st[1:, cv2.CC_STAT_AREA])).astype(np.uint8)
    return blur(m.astype(np.float32), 10)


def light_points(off, on, k=41, thr=0.22, top=60):
    """从"灭灯图 / 亮灯图"的差里找每盏灯的位置，返回像素坐标列表（按亮度从大到小）"""
    d = np.clip((on - off).max(2), 0, 1)
    loc = (d == cv2.dilate(d, np.ones((k, k), np.uint8))) & (d > thr)
    ys, xs = np.where(loc)
    order = np.argsort(-d[ys, xs])[:top]
    return [(int(xs[i]), int(ys[i])) for i in order]


# ---------------- 字幕暗带、转场用的雾 ----------------
def make_band(path, start=0.60, strength=0.9):
    """底部向上渐隐的暗带。组装时拉满整页宽，字压在它上面。"""
    yy = np.linspace(0, 1, 540)[:, None] * np.ones((1, 16))
    a = strength * np.clip((yy - start) / (0.96 - start), 0, 1) ** 0.85
    cv2.imencode(".png", (np.dstack([np.zeros((540, 16, 3)), a]) * 255).astype(np.uint8))[1].tofile(path)


def make_fog(path, w=1500, h=720, seed=7):
    """过程生成的一团雾（透明 PNG），给雾转场用。有生图工具时，让它画一张"黑底尘云"再转透明度，质感更好。"""
    r = np.random.default_rng(seed)
    n = np.zeros((h, w), np.float32)
    for cells, wt in ((5, 0.55), (11, 0.30), (23, 0.15)):
        o = cv2.resize(r.random((cells, cells * 2)).astype(np.float32), (w, h), interpolation=cv2.INTER_CUBIC)
        n += cv2.GaussianBlur(o, (0, 0), h / cells / 3.0) * wt
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    env = np.clip(1 - ((xx - w / 2) / (w / 2)) ** 2, 0, 1) ** 0.8 * np.clip(1 - ((yy - h / 2) / (h / 2)) ** 4, 0, 1)
    a = np.clip((n - 0.36) * 4.0, 0, 1) * env
    col = (0.5 + 0.25 * n)[..., None] * np.float32([0.62, 0.60, 0.57])
    cv2.imencode(".png", (np.clip(np.dstack([col, cv2.GaussianBlur(a, (0, 0), 6)]), 0, 1) * 255).astype(np.uint8))[1].tofile(path)


# ---------------- 把一张页面截图放进实景里的屏幕 ----------------
def screen_matte(room, room_clean=None, lo=0.30):
    """room: 屏幕显示纯白的房间照片（屏幕前可以有人头剪影）。room_clean: 同一机位、屏幕前没有遮挡的那张（有就传，用来取屏幕亮度的均匀度）。
    返回 dict: x, y, w, h（屏幕外接框，像素），matte（HxWx1 软抠像，人头处为 0），shade（屏幕亮度不均匀度），white（屏幕白的颜色）。"""
    lum = room.mean(2); sat = room.max(2) - room.min(2)
    m0 = ((lum > 0.55) & (sat < 0.14)).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(m0)
    k0 = 1 + np.argmax(st[1:, cv2.CC_STAT_AREA]); x, y, w, h = [int(v) for v in st[k0][:4]]
    ref = (room if room_clean is None else room_clean).mean(2)
    wc = float(ref[y + h // 3, x + w // 2])
    shade = np.clip(blur(ref, 25) / max(1e-3, wc), 0.8, 1.04)[..., None]
    box = np.zeros((H, W), np.float32); box[y:y + h, x:x + w] = 1
    white = room[y + h // 5:y + h // 2, x + w // 4:x + 3 * w // 4].reshape(-1, 3).mean(0)
    # 按亮度做软抠像：头发边缘是"人 × (1-s) + 屏幕白 × s"，直接硬蒙版会留一圈白边
    matte = (np.clip((lum - lo) / max(1e-3, wc * 0.96 - lo), 0, 1) * box * (sat < 0.2))[..., None]
    return dict(x=x, y=y, w=w, h=h, matte=matte, shade=shade, white=white)


def screen_comp(room, page, sm, gain=0.95):
    """把 page（任意尺寸的页面截图，浮点 BGR）放进房间照片的屏幕里，人头保持在屏幕前面。返回未做 fin 的整幅画面。"""
    p = cv2.resize(page, (sm["w"], sm["h"]), interpolation=cv2.INTER_AREA)
    full = np.zeros_like(room); full[sm["y"]:sm["y"] + sm["h"], sm["x"]:sm["x"] + sm["w"]] = p
    return room + sm["matte"] * (full * gain - sm["white"]) * sm["shade"]


def screen_layer(path, frame, sm):
    """只含屏幕区域的透明图层（frame 是已经 fin 过的整幅画面）。返回它在 960x540 版面上的 [x, y, w, h]。
    每个界面状态出一张，交给原生动画按顺序淡入/擦除，时间完全可控。"""
    out = np.dstack([frame, sm["matte"][..., 0]])[sm["y"]:sm["y"] + sm["h"], sm["x"]:sm["x"] + sm["w"]]
    cv2.imencode(".png", (np.clip(out, 0, 1) * 255).astype(np.uint8))[1].tofile(path)
    return [sm["x"] / 2, sm["y"] / 2, sm["w"] / 2, sm["h"] / 2]


# ---------------- 检查用 ----------------
def grid_view(img_path, out_path, gain=1.0, size=(1600, 900)):
    """给底图打上每 5% 一格的网格并标数字，用来读"这条路、这面坡在画面的百分之几"，再用 pct() 换成像素。"""
    a = cv2.resize(cv2.imdecode(np.fromfile(img_path, np.uint8), 1), size).astype(np.float32) * gain
    a = np.clip(a, 0, 255).astype(np.uint8)
    for i in range(1, 20):
        x = i * size[0] // 20; y = i * size[1] // 20
        c = (0, 255, 255) if i % 2 == 0 else (90, 90, 90)
        cv2.line(a, (x, 0), (x, size[1] - 1), c, 1); cv2.line(a, (0, y), (size[0] - 1, y), c, 1)
        if i % 2 == 0:
            cv2.putText(a, str(i * 5), (x + 3, 14), 0, 0.45, (0, 255, 255), 1); cv2.putText(a, str(i * 5), (3, y - 3), 0, 0.45, (0, 255, 255), 1)
    cv2.imencode(".jpg", a)[1].tofile(out_path)


def contact_sheet(video, out_path, every=2.0, cols=4, width=500, start=0.0):
    """导出的放映视频每 every 秒取一帧，拼成联系表。核对顺序、时机和遮挡用。"""
    cap = cv2.VideoCapture(video); fps = cap.get(cv2.CAP_PROP_FPS) or 30; n = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    tiles = []; t = start
    while t * fps < n:
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(t * fps)); ok, f = cap.read()
        if not ok:
            break
        tiles.append(cv2.resize(f, (width, int(width * f.shape[0] / f.shape[1])))); t += every
    while len(tiles) % cols:
        tiles.append(np.zeros_like(tiles[0]))
    rows = [np.hstack(tiles[i:i + cols]) for i in range(0, len(tiles), cols)]
    cv2.imencode(".jpg", np.vstack(rows))[1].tofile(out_path)
    print(os.path.basename(out_path), len(tiles), "tiles", flush=True)


def frame_at(video, t, out_path, width=960):
    """取导出视频第 t 秒的一帧，看某一拍的细节用"""
    cap = cv2.VideoCapture(video); cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000); ok, f = cap.read()
    if ok:
        cv2.imencode(".jpg", cv2.resize(f, (width, int(width * f.shape[0] / f.shape[1]))))[1].tofile(out_path)
    return ok


# ---------------- 光在讲事：探照光束、光照揭示、被照亮的字 ----------------
def track(keys, t):
    """关键帧轨迹：keys = [(t0, x0, y0), (t1, x1, y1), ...]，段间缓入缓出。用来让光斑、光点按节奏游走。"""
    for (t0, x0, y0), (t1, x1, y1) in zip(keys, keys[1:]):
        if t <= t1:
            u = (t - t0) / max(1e-6, t1 - t0); u = u * u * (3 - 2 * u)
            return x0 + (x1 - x0) * u, y0 + (y1 - y0) * u
    return keys[-1][1], keys[-1][2]


def beam_cone(src, dst, w_src=6.0, w_dst=180.0, soft=28):
    """从 src 打到 dst 的一束光（梯形），HxW 0..1。乘上 haze(t) 就是雨雾里的光柱。"""
    (sx, sy), (dx, dy) = src, dst
    nx, ny = -(dy - sy), (dx - sx); ln = math.hypot(nx, ny) or 1.0; nx, ny = nx / ln, ny / ln
    poly = np.float32([(sx + nx * w_src, sy + ny * w_src), (dx + nx * w_dst, dy + ny * w_dst),
                       (dx - nx * w_dst, dy - ny * w_dst), (sx - nx * w_src, sy - ny * w_src)])
    lay = np.zeros((H, W), np.float32)
    cv2.fillConvexPoly(lay, np.int32(np.round(poly * 4)), 1.0, cv2.LINE_AA, shift=2)
    # 越远越淡
    along = np.clip(((X - sx) * (dx - sx) + (Y - sy) * (dy - sy)) / max(1.0, (dx - sx) ** 2 + (dy - sy) ** 2), 0, 1)
    return blur(lay, soft) * (1 - 0.55 * along)


def light_reveal(dark, lit, mask):
    """光照揭示：mask（HxW 0..1）为 1 的地方显示亮片，其余是暗片。暗片可以是 lit * 一个偏冷的系数。"""
    m = mask[..., None] if mask.ndim == 2 else mask
    return dark * (1 - m) + lit * m


def text_mask(text, font_path, size, x, y, angle=0.0, vertical=False, track_k=0.96):
    """把一组字画成 HxW 0..1 的蒙版，可横排、竖排、旋转。用在"光扫到哪里，哪里的字亮起"这类烧进动图的字。
    能用原生文本框的字一律用原生文本框；只有要和光照逐像素互动的字才烧进图里。"""
    from PIL import Image, ImageDraw, ImageFont
    f = ImageFont.truetype(font_path, size)
    im = Image.new("L", (W, H), 0); d = ImageDraw.Draw(im)
    cx, cy = x, y
    for ch in text:
        d.text((cx, cy), ch, font=f, fill=255)
        if vertical:
            cy += int(size * 0.92)
        else:
            cx += int(d.textlength(ch, font=f) * track_k)
    if angle:
        im = im.rotate(angle, resample=Image.BICUBIC, center=(x, y))
    return np.asarray(im).astype(np.float32) / 255


def lit_text(frame, mask, lum, color=(0.93, 0.96, 1.0), shadow=0.5):
    """把 text_mask 的字压进画面：lum（标量或 HxW）是字此刻的亮度，平时 0.2 左右，被光照到接近 1。"""
    sh = blur(mask, 14)
    frame = frame * (1 - shadow * sh[..., None])
    return frame * (1 - mask[..., None]) + (np.asarray(lum, np.float32) * mask)[..., None] * np.float32(color)


def text_img(lines, font_path, size, fill=(30, 30, 30, 255), spacing=1.35, w=None):
    """多行字渲染成 RGBA 的 PIL Image。用在纸面、屏幕里要看得清的字（生图工具画的字不可靠）：
    先画好一张"纸"，再把它贴上去；"逐行写出来"就渲染多版只差一行的图，叠在同一位置用擦除依次露出。"""
    from PIL import Image, ImageDraw, ImageFont
    f = ImageFont.truetype(font_path, size)
    wd = w or int(max(f.getlength(s) for s in lines)) + 8
    im = Image.new("RGBA", (wd, int(size * spacing * len(lines)) + 8), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for i, s in enumerate(lines):
        d.text((2, int(i * size * spacing)), s, font=f, fill=fill)
    return im
