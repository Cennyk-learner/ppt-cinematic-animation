# Capture the PowerPoint slide-show window in the background (no focus stealing) every 0.5 s.
import ctypes, ctypes.wintypes as wt, time, sys
import numpy as np, cv2

u, g = ctypes.windll.user32, ctypes.windll.gdi32
u.SetProcessDPIAware()
dur = float(sys.argv[1]); out = sys.argv[2]


def find():
    res = []

    @ctypes.WINFUNCTYPE(ctypes.c_bool, wt.HWND, wt.LPARAM)
    def cb(h, l):
        b = ctypes.create_unicode_buffer(400)
        u.GetWindowTextW(h, b, 400)
        if u.IsWindowVisible(h) and ("幻灯片放映" in b.value or "Slide Show" in b.value):
            res.append(h)
        return True
    u.EnumWindows(cb, 0)
    return res[0] if res else None


t0 = time.time(); h = None
while h is None and time.time() - t0 < 15:
    h = find(); time.sleep(0.1)
if h is None:
    sys.exit("no slideshow window")
u.ShowWindow(h, 4); time.sleep(0.5)
start = time.time(); shots = []
while time.time() - start < dur:
    r = wt.RECT(); u.GetClientRect(h, ctypes.byref(r))
    w, hh = r.right, r.bottom
    dc = u.GetDC(h); mdc = g.CreateCompatibleDC(dc); bmp = g.CreateCompatibleBitmap(dc, w, hh)
    g.SelectObject(mdc, bmp)
    u.PrintWindow(h, mdc, 3)
    buf = ctypes.create_string_buffer(w * hh * 4)
    g.GetBitmapBits(bmp, w * hh * 4, buf)
    im = np.frombuffer(buf, np.uint8).reshape(hh, w, 4)[..., :3].copy()
    g.DeleteObject(bmp); g.DeleteDC(mdc); u.ReleaseDC(h, dc)
    im = cv2.resize(im, (400, int(400 * hh / w)))
    cv2.putText(im, f"{time.time() - start:4.1f}s", (6, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
    shots.append(im)
    time.sleep(0.5)
n = len(shots); cols = 6
while len(shots) % cols: shots.append(np.zeros_like(shots[0]))
sheet = np.vstack([np.hstack(shots[i:i + cols]) for i in range(0, len(shots), cols)])
cv2.imencode(".png", sheet)[1].tofile(out)
print("captured", n)
