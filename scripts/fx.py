# 底层帧工具：读写图、缓动、推拉、雨、写 MP4。画面 1920x1080 浮点 BGR（0..1）。
# shake / zoom_blur 留着备用，但震动和冲击模糊通常显得廉价，慎用。
import subprocess, math
import numpy as np, cv2

W, H, FPS = 1920, 1080, 30
GOLD = (60, 190, 255)      # BGR
RED = (40, 60, 240)
CYAN = (255, 200, 90)
WHITE = (255, 255, 255)


def load(path, alpha=False):
    im = cv2.imdecode(np.fromfile(path, np.uint8), cv2.IMREAD_UNCHANGED if alpha else cv2.IMREAD_COLOR)
    im = cv2.resize(im, (W, H), interpolation=cv2.INTER_LANCZOS4)
    return im.astype(np.float32) / 255.0


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def seg(t, a, b):
    """0..1 progress of t inside [a, b]."""
    return clamp((t - a) / (b - a))


def smooth(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def ease_out(x, p=3):
    return 1 - (1 - clamp(x)) ** p


def ease_in(x, p=3):
    return clamp(x) ** p


def zoom(img, cx, cy, s, dx=0.0, dy=0.0, border=cv2.BORDER_REFLECT):
    """Scale by s around (cx, cy), keeping that point moving toward frame centre as s grows."""
    k = clamp((s - 1) / max(s, 1e-6) * 1.0)
    tx = cx + (W / 2 - cx) * k
    ty = cy + (H / 2 - cy) * k
    M = np.float32([[s, 0, tx - s * cx + dx], [0, s, ty - s * cy + dy]])
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=border)


def zoom_blur(img, amount, n=10):
    """Radial blur around frame centre. amount ~ 0..0.4"""
    if amount < 0.003:
        return img
    acc = np.zeros_like(img)
    for i in range(n):
        s = 1 + amount * i / (n - 1)
        M = np.float32([[s, 0, W / 2 * (1 - s)], [0, s, H / 2 * (1 - s)]])
        acc += cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    return acc / n


def shift(img, dx, dy):
    M = np.float32([[1, 0, dx], [0, 1, dy]])
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


def shake(t, t0, amp=26, freq=38, decay=7):
    """Damped shake offset after an impact at t0."""
    if t < t0:
        return 0.0, 0.0
    d = t - t0
    e = amp * math.exp(-decay * d)
    return e * math.sin(freq * d), e * math.cos(freq * d * 1.31 + 1.0)


def blur(img, r):
    if r <= 0:
        return img
    k = int(r * 3) | 1
    return cv2.GaussianBlur(img, (k, k), r)


def add_glow(frame, layer, color, strength=1.0, radius=14, core=1.0):
    """layer: float32 HxW 0..1 line art. Adds a coloured core plus a soft bloom."""
    c = np.float32(color) / 255.0
    g = blur(layer, radius) * 1.6 + blur(layer, radius * 3) * 0.9
    a = np.clip(layer * core + g * strength, 0, 2)[..., None]
    return frame + a * c


def vignette(strength=0.55):
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((x - W / 2) / (W / 2)) ** 2 + ((y - H / 2) / (H / 2)) ** 2)
    return (1 - strength * np.clip(r - 0.45, 0, 1) ** 1.6)[..., None]


class Rain:
    """Procedural streak rain. draw(t) -> float32 HxW additive layer."""

    def __init__(self, n=900, seed=3, angle=-0.22, speed=(1700, 2600), length=(26, 70)):
        r = np.random.default_rng(seed)
        self.x = r.uniform(-300, W + 300, n)
        self.y = r.uniform(0, H + 400, n)
        self.v = r.uniform(*speed, n)
        self.l = r.uniform(*length, n)
        self.a = r.uniform(0.10, 0.42, n)
        self.ang = angle

    def draw(self, t, density=1.0, region=None):
        lay = np.zeros((H, W), np.float32)
        n = int(len(self.x) * clamp(density))
        dx, dy = math.sin(self.ang), math.cos(self.ang)
        for i in range(n):
            y = (self.y[i] + self.v[i] * t) % (H + 400) - 200
            x = self.x[i] + (y * dx / dy)
            x2, y2 = x + dx * self.l[i], y + dy * self.l[i]
            cv2.line(lay, (int(x), int(y)), (int(x2), int(y2)), float(self.a[i]), 1, cv2.LINE_AA)
        lay = cv2.GaussianBlur(lay, (3, 3), 0.7)
        if region is not None:
            lay *= region
        return lay


class Writer:
    def __init__(self, path, crf=17):
        self.p = subprocess.Popen(
            ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}",
             "-r", str(FPS), "-i", "-", "-an", "-c:v", "libx264", "-preset", "slow", "-crf", str(crf),
             "-pix_fmt", "yuv420p", "-profile:v", "high", "-movflags", "+faststart", path],
            stdin=subprocess.PIPE)

    def write(self, frame):
        self.p.stdin.write((np.clip(frame, 0, 1) * 255).astype(np.uint8).tobytes())

    def close(self):
        self.p.stdin.close()
        self.p.wait()


def save(path, frame):
    cv2.imencode(".png", (np.clip(frame, 0, 1) * 255).astype(np.uint8))[1].tofile(path)
