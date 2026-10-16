# -*- coding: utf-8 -*-
"""整份稿的核对和展示：
  python export_slides.py check deck.pptx out.mp4 sheet_prefix [每隔几秒=1] [高度=720]
      导出放映视频，每隔 N 秒抽一帧拼联系表（40 格一张）。
  python export_slides.py split deck.pptx outdir [--strip 形状名1,形状名2]
      每一页单独导出成一段视频（剪展示动图、看某一页的完整节奏用）。--strip 先删掉这些形状
      （比如封面上的姓名学号），备注栏也清空，然后再导出，原文件不动。
  python export_slides.py webp in.mp4 out.webp 起秒 止秒 [宽=640] [高=360]
      剪一段动图 WebP（README 展示用，12 帧每秒）。
"""
import os, sys, time, shutil, subprocess
import numpy as np, cv2


def _app():
    import win32com.client as wc, pythoncom
    pythoncom.CoInitialize()
    return wc.Dispatch('PowerPoint.Application')


def _video(pres, mp4, height=720, sec=2):
    if os.path.exists(mp4):
        os.remove(mp4)
    pres.CreateVideo(mp4, True, sec, height, 25, 88)
    t = 0
    while pres.CreateVideoStatus in (1, 2) and t < 3000:
        time.sleep(3); t += 3
    return pres.CreateVideoStatus


def check(deck, mp4, prefix, every=1.0, height=720):
    app = _app()
    p = app.Presentations.Open(os.path.abspath(deck), True, False, False)
    try:
        print('status', _video(p, os.path.abspath(mp4), height))
    finally:
        p.Close()
    cap = cv2.VideoCapture(mp4); fps = cap.get(cv2.CAP_PROP_FPS) or 25; n = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    tiles, t = [], 0.0
    while t * fps < n:
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(t * fps)); ok, f = cap.read()
        if not ok:
            break
        f = cv2.resize(f, (480, 270)); cv2.putText(f, f'{t:.0f}s', (6, 18), 0, 0.55, (0, 255, 255), 1)
        tiles.append(f); t += every
    for s in range(0, len(tiles), 40):
        chunk = tiles[s:s + 40]
        while len(chunk) % 5:
            chunk.append(np.zeros_like(tiles[0]))
        img = np.vstack([np.hstack(chunk[i:i + 5]) for i in range(0, len(chunk), 5)])
        cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 80])[1].tofile(f'{prefix}_{s // 40:02d}.jpg')
    print('duration', n / fps)


def split(deck, outdir, strip=()):
    os.makedirs(outdir, exist_ok=True)
    app = _app()
    show = os.path.join(outdir, '_clean.pptx')
    p = app.Presentations.Open(os.path.abspath(deck), False, False, False)
    try:
        for s in p.Slides:
            for nm in strip:
                try:
                    s.Shapes.Item(nm).Delete()
                except Exception:
                    pass
            try:
                s.NotesPage.Shapes.Placeholders(2).TextFrame.TextRange.Text = ''
            except Exception:
                pass
        n = p.Slides.Count
        p.SaveAs(show)
    finally:
        p.Close()
    for k in range(1, n + 1):
        tmp = os.path.join(outdir, f'_s{k:02d}.pptx'); shutil.copy(show, tmp)
        q = app.Presentations.Open(tmp, False, False, False)
        try:
            for i in range(q.Slides.Count, 0, -1):
                if i != k:
                    q.Slides.Item(i).Delete()
            q.Save()
            print(k, _video(q, os.path.join(outdir, f's{k:02d}.mp4'), 720, 3), flush=True)
        finally:
            q.Close()
        os.remove(tmp)


def webp(src, out, a, b, w=640, h=360):
    flt = f'trim={a}:{b},setpts=PTS-STARTPTS,fps=12,scale={w}:{h}:flags=lanczos'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', src, '-vf', flt, '-c:v', 'libwebp_anim', '-lossless', '0',
                    '-q:v', '62', '-compression_level', '6', '-loop', '0', '-an', out], check=True)
    print(out, os.path.getsize(out) // 1024, 'KB')


if __name__ == '__main__':
    c = sys.argv[1]
    if c == 'check':
        check(sys.argv[2], sys.argv[3], sys.argv[4], float(sys.argv[5]) if len(sys.argv) > 5 else 1.0,
              int(sys.argv[6]) if len(sys.argv) > 6 else 720)
    elif c == 'split':
        strip = []
        if '--strip' in sys.argv:
            strip = sys.argv[sys.argv.index('--strip') + 1].split(',')
        split(sys.argv[2], sys.argv[3], strip)
    elif c == 'webp':
        webp(sys.argv[2], sys.argv[3], float(sys.argv[4]), float(sys.argv[5]),
             *(int(v) for v in sys.argv[6:8]))
