import sys, math, os
from pathlib import Path
import numpy as np
from PIL import Image
from multiprocessing import Pool

W, H = 1280, 720
Q = 1.25
NX, NY = int(W * Q), int(H * Q)
F = 1990 * Q
CX, CY = 0.654 * NX, 0.606 * NY
HP, R = 54.0, 21.2
SECTIONS = {"cover": 1, "flat": 44, "fold": 48, "return": 40}
pi = math.pi


def v(a):
    return np.asarray(a, dtype=np.float32)


def unit(a):
    return a / (np.linalg.norm(a, axis=-1, keepdims=True) + 1e-12)


D = unit(v([-0.425, 0.817, -0.415]))
E = v([0, 0, 39]) - D * 816
RGT = unit(np.cross(D, v([0, 0, 1])))
UP = unit(np.cross(RGT, D))
Y, X = np.mgrid[:NY, :NX].astype("f")
X += 0.5
Y += 0.5
ray = (
    D[None, None, :]
    + ((X - CX) / F)[:, :, None] * RGT
    + ((CY - Y) / F)[:, :, None] * UP
)
G = E + ray * (-E[2] / ray[:, :, 2])[:, :, None]
SX = (E[0] - G[:, :, 0]) / E[2]
SY = (E[1] - G[:, :, 1]) / E[2]
NOISE = np.random.default_rng(121).uniform(-0.8, 0.8, (NY, NX)).astype("f")


def ease(a, b, t):
    s = np.clip((t - a) / (b - a), 0, 1)
    return s * s * (3 - 2 * s)


def pose(s, t):
    if s == "flat":
        return 0.0, 34 * ease(0.98, 1.95, t), 36 * (1 - ease(0.1, 0.98, t))
    if s == "fold":
        a = ease(0.84, 2.46, t) * pi / 3
        return (
            a,
            34 * (1 - ease(0, 0.65, t)),
            36 * ease(0.50, 1.02, t) - 20 * math.sin(a),
        )
    if s == "return":
        return (
            pi / 3,
            3.4 * ease(1.01, 1.54, t),
            (36 - 20 * math.sin(pi / 3)) * (1 - ease(0.13, 1.01, t)),
        )
    return 0.0, 0.0, 36.0


def env(x):
    return 0.5 + 0.5 * np.cos(pi * np.clip((np.abs(x) - R) / (109 - 13.8 - R), 0, 1))


def geom(a, sag, gap):
    shapes = []

    def quad(pts, mat, normal=None):
        p = v(pts)
        n = (
            unit(np.cross(p[1] - p[0], p[2] - p[0]))
            if normal is None
            else unit(v(normal))
        )
        shapes.append((p, mat, n))

    def loft(rings, mat, center=(0, 0)):
        for k in range(len(rings) - 1):
            loop0, z0 = rings[k]
            loop1, z1 = rings[k + 1]
            for i in range(len(loop0)):
                j = (i + 1) % len(loop0)
                pts = [
                    [*loop0[i], z0],
                    [*loop0[j], z0],
                    [*loop1[j], z1],
                    [*loop1[i], z1],
                ]
                quad(pts, mat)
        loop, z = rings[-1]
        p = [[*q, z] for q in loop]
        shapes.append((v(p), mat, v([0, 0, 1])))

    for cen in [-109, 109]:

        def outline(inset):
            bx, by, rad = 13.8 - inset, 85 - inset, max(0.25, 2 - inset)
            out = []
            for cx, cy, start in [
                (bx - rad, by - rad, 0),
                (-bx + rad, by - rad, 90),
                (-bx + rad, -by + rad, 180),
                (bx - rad, -by + rad, 270),
            ]:
                for deg in np.linspace(start, start + 90, 5):
                    z = math.radians(deg)
                    out.append([cen + cx + rad * math.cos(z), cy + rad * math.sin(z)])
            return out

        loft(
            [
                (outline(1), 0),
                (outline(0), 1),
                (outline(0), HP - 1.2),
                (outline(0.3), HP - 0.35),
                (outline(1.2), HP),
            ],
            1,
        )
    ex = 139 - (
        np.hypot(
            np.diff(np.linspace(0, 95.2, 129)),
            np.diff(sag * env(np.linspace(0, 95.2, 129))),
        ).sum()
        - 95.2
    )
    xx = np.linspace(-ex, ex, 49)
    co, si = math.cos(a), math.sin(a)
    for i in range(8):
        ya, yb = -80 + 20 * i, -60 + 20 * i
        za, zb = (0, 20 * si) if i % 2 == 0 else (20 * si, 0)
        for x0, x1 in zip(xx[:-1], xx[1:]):

            def pt(x, y, z):
                return [
                    x,
                    y * co,
                    HP + 0.22 + z - sag * env(x) * (1 - 0.1 * ease(25, 78, abs(y))),
                ]

            quad([pt(x0, ya, za), pt(x1, ya, za), pt(x1, yb, zb), pt(x0, yb, zb)], 2)
            if x0 == xx[0] or x1 == xx[-1]:
                xx0 = x0 if x0 == xx[0] else x1
                A = v(pt(xx0, ya, za))
                B = v(pt(xx0, yb, zb))
                dz = v([0, 0, 0.35])
                quad([A, B, B - dz, A - dz], 3, [-1 if x0 == xx[0] else 1, 0, 0])
    base = HP + 0.22 + 20 * si - sag + gap

    def circle(r):
        return [
            [r * math.cos(t), r * math.sin(t)]
            for t in np.linspace(0, 2 * pi, 80, endpoint=False)
        ]

    loft(
        [
            (circle(r), base + z)
            for r, z in [
                (20, 0),
                (21.05, 0.4),
                (R, 0.9),
                (R, 2),
                (20.98, 2.25),
                (R, 2.55),
                (R, 26),
                (21, 26.65),
                (20.55, 27.1),
                (19.9, 27.3),
            ]
        ],
        4,
    )
    return shapes, base, ex


def render(section, number, output):
    a, sag, gap = pose(section, number / 16.0)
    meshes, base, ex = geom(a, sag, gap)
    Z = np.zeros((NY, NX), "f")
    N = np.zeros((NY, NX, 3), "f")
    N[:, :, 2] = 1
    M = np.zeros((NY, NX), np.uint8)
    # Perspective-correct z-buffer for the convex faces of the studio model.
    for points, mat, n in meshes:
        vec = points - E
        dep = vec @ D
        pp = np.stack([CX + F * (vec @ RGT) / dep, CY - F * (vec @ UP) / dep], axis=1)
        inv = 1 / dep
        for k in range(1, len(points) - 1):
            ids = [0, k, k + 1]
            p, q, r = pp[ids]
            sd = inv[ids]
            den = (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
            if abs(den) < 1e-7:
                continue
            x0 = max(0, int(math.ceil(min(p[0], q[0], r[0]) - 0.5)))
            x1 = min(NX, int(math.floor(max(p[0], q[0], r[0]) - 0.5)) + 1)
            y0 = max(0, int(math.ceil(min(p[1], q[1], r[1]) - 0.5)))
            y1 = min(NY, int(math.floor(max(p[1], q[1], r[1]) - 0.5)) + 1)
            if x1 <= x0 or y1 <= y0:
                continue
            sl = np.s_[y0:y1, x0:x1]
            px = X[sl] - p[0]
            py = Y[sl] - p[1]
            u = ((r[1] - p[1]) * px - (r[0] - p[0]) * py) / den
            w = (-(q[1] - p[1]) * px + (q[0] - p[0]) * py) / den
            z = E[2] + ray[sl][:, :, 2] / (
                sd[0] + u * (sd[1] - sd[0]) + w * (sd[2] - sd[0])
            )
            mask = (u >= -0.00004) & (w >= -0.00004) & (u + w <= 1.00004) & (z > Z[sl])
            Z[sl][mask] = z[mask]
            N[sl][mask] = n
            M[sl][mask] = mat
    px = G[:, :, 0] + SX * Z
    py = G[:, :, 1] + SY * Z
    rr = np.hypot(px, py)
    shell = (M == 4) & (np.abs(N[:, :, 2]) < 0.95)
    horiz = np.sqrt(np.maximum(0, 1 - N[:, :, 2] ** 2))
    N[:, :, 0][shell] = (px * horiz / np.maximum(rr, 0.01))[shell]
    N[:, :, 1][shell] = (py * horiz / np.maximum(rr, 0.01))[shell]
    l = unit(v([-0.58, -0.44, 0.81]))
    side = unit(np.cross(l, v([0, 0, 1])))
    vert = unit(np.cross(side, l))
    fill = unit(v([0.44, 0.71, 0.60]))
    lights = []
    for k in range(12):
        r = math.sqrt((k + 0.5) / 12)
        ang = k * 2.3999632
        lights.append(
            unit(
                l
                + side * (0.36 * r * math.cos(ang))
                + vert * (0.27 * r * math.sin(ang))
            )
        )
    # Segment intersection with the red cylinder and both blocks. The thin paper
    # casts onto the grounds at its mean local height. The area lamp softens edges.
    visible = np.zeros_like(Z)
    halfW = 80 * math.cos(a)
    for L in lights:
        lx, ly = L[:2] / L[2]
        tb = np.maximum(0, base - Z)
        tt = base + 27.3 - Z
        qx = px + tb * lx
        qy = py + tb * ly
        span = np.maximum(0, tt - tb)
        st = np.minimum(np.maximum(-(qx * lx + qy * ly) / (lx * lx + ly * ly), 0), span)
        occ = (
            (tt > 0.4) & (M != 4) & ((qx + st * lx) ** 2 + (qy + st * ly) ** 2 < R * R)
        )
        for cen in [-109, 109]:
            xa = (cen - 13.8 - px) / lx
            xb = (cen + 13.8 - px) / lx
            ya = (-85 - py) / ly
            yb = (85 - py) / ly
            near = np.maximum(np.minimum(xa, xb), np.minimum(ya, yb))
            far = np.minimum(np.maximum(xa, xb), np.maximum(ya, yb))
            occ |= np.minimum(far, HP - Z) > np.maximum(near, 0.65)
        zh = HP + 0.22 + 10 * math.sin(a) - sag * env(px)
        dz = zh - Z
        occ |= (
            (M < 2)
            & (dz > 0.4)
            & (np.abs(px + lx * dz) < ex)
            & (np.abs(py + ly * dz) < halfW)
        )
        visible += (~occ) / len(lights)
    light = np.maximum(0, N @ l)
    back = np.maximum(0, N @ fill)
    ambient = (
        0.285
        + 0.194 * np.maximum(0, N[:, :, 2])
        + 0.054 * np.maximum(0, -N[:, :, 1])
        + 0.055 * np.maximum(0, -N[:, :, 2])
    )
    ao = np.ones_like(Z)
    ispaper = M == 2
    isstand = M == 1
    ismass = M == 4
    ao[ispaper] -= (
        0.53 * np.exp(-np.maximum(0, base - Z) / 12 - np.maximum(0, rr - R) / 6.5)
    )[ispaper]
    if a > 0.001:
        f = np.mod(py / math.cos(a) + 80, 40)
        rise = np.minimum(f, 40 - f) * math.sin(a)
        ao[ispaper] -= (0.25 * math.sin(a) * np.exp(-rise / 4))[ispaper]
    ao[isstand] -= (
        0.25 * np.exp(-Z / 6)
        + 0.22 * np.exp(-np.maximum(0, np.abs(py) - halfW) / 9 - np.abs(54 - Z) / 11)
    )[isstand]
    ao[ismass] -= (0.16 * np.exp(-max(gap, 0) / 6 - np.maximum(0, Z - base) / 3))[
        ismass
    ]
    illum = ambient * np.maximum(0.18, ao) + 0.69 * light * visible + 0.115 * back
    albs = v(
        [
            [1, 1, 1],
            [0.084, 0.105, 0.110],
            [0.817, 0.793, 0.712],
            [0.52, 0.48, 0.38],
            [0.585, 0.068, 0.032],
        ]
    )
    alb = albs[M]
    texture = (
        1
        + 0.007 * np.sin(px * 0.9 + py * 0.45 + Z * 0.11) * np.sin(py * 1.4 + Z * 0.9)
        + 0.004 * np.sin(px * 0.17 - py * 0.25)
    )
    alb *= texture[:, :, None]
    ring = ismass & (N[:, :, 2] > 0.95)
    alb[ring] *= (1 - 0.21 * np.exp(-((rr[ring] - 18.05) ** 2) / 0.05))[:, None]
    matBase = np.zeros_like(Z)
    matBase[ispaper] = (0.012 * back + 0.014 * light * visible)[ispaper]
    matBase[isstand] = (0.028 * back**4 + 0.013 * light * visible)[isstand]
    if np.any(ismass):
        ns = N[ismass]
        q = np.stack([px[ismass], py[ismass], Z[ismass]], axis=1)
        vw = unit(E - q)
        re = ns * (2 * np.sum(ns * vw, axis=1))[:, None] - vw
        rh = unit(re[:, :2])
        strip = np.maximum(0, rh @ unit(v([-0.71, -0.70]))) ** 19 * np.exp(
            -(((re[:, 2] + 0.20) / 0.76) ** 4)
        )
        sheen = np.maximum(0, re @ unit(v([-0.50, 0.25, 0.83]))) ** 11
        fr = (1 - np.clip(np.sum(ns * vw, axis=1), 0, 1)) ** 4
        matBase[ismass] = (
            0.07 * strip + 0.064 * sheen + 0.032 * fr + 0.012 * back[ismass]
        )
    rgb = alb * illum[:, :, None] + matBase[:, :, None] * v([1, 0.967, 0.922])
    ground = M == 0
    bd = np.hypot(
        np.maximum(0, np.abs(np.abs(px) - 109) - 13.8), np.maximum(0, np.abs(py) - 85)
    )
    dx = np.maximum(0, np.abs(px) - 128)
    dy = np.maximum(0, np.abs(py) - halfW)
    touch = (
        0.245 * np.exp(-bd / 5.9)
        + 0.082 * np.exp(-bd / 26)
        + 0.078 * np.exp(-(dx * dx + dy * dy) / 1900)
    )
    br = 0.716 + 0.062 * (1 - Y / NY) + 0.020 * (1 - X / NX) - 0.035 * (X / NX) ** 2
    floor = br * (0.49 + 0.51 * visible) * (1 - touch)
    rgb[ground] = floor[ground, None] * v([1.025, 0.985, 0.921])
    rgb = np.clip(rgb, 0, 1)
    display = (
        np.where(rgb <= 0.0031308, 12.92 * rgb, 1.055 * rgb ** (1 / 2.4) - 0.055) * 255
        + NOISE[:, :, None]
    )
    target = Path(output) / section
    target.mkdir(parents=True, exist_ok=True)
    name = target / f"frame_{number:03d}.png"
    Image.fromarray(np.round(np.clip(display, 0, 255)).astype("uint8")).resize(
        (W, H), Image.Resampling.LANCZOS
    ).save(name, compress_level=2)
    return str(name)


def run(job):
    return render(*job)


if __name__ == "__main__":
    sec = sys.argv[1] if len(sys.argv) > 1 else "all"
    exact = int(sys.argv[2]) if len(sys.argv) > 2 else None
    out = os.getenv("BRIDGE_OUT", "frames")
    jobs = [
        (s, i, out)
        for s, n in SECTIONS.items()
        if sec in (s, "all")
        for i in (range(n) if exact is None else [exact])
    ]
    workers = int(os.getenv("BRIDGE_WORKERS", "2"))
    if len(jobs) == 1:
        print(run(jobs[0]), flush=True)
    else:
        with Pool(workers) as pool:
            for file in pool.imap_unordered(run, jobs):
                print(file, flush=True)
