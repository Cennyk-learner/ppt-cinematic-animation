# 把一个本地 HTML 页面（真实系统界面的单文件版）无头跑起来，按步骤点击，逐帧截图。
# 截出来的帧再用 render_tools.screen_comp 放进实景里的屏幕。先用 --probe 看页面上有什么可点的，再写步骤。
#
# 用法:
#   python capture_page.py page.html --probe                      列出按钮文字、顶层结构，截一张图
#   python capture_page.py page.html out_dir steps.json [--size 1920x1080] [--dt 0.16] [--css "..."]
#
# steps.json 是一个列表，按顺序执行，每一步是下面之一：
#   {"shots": 6}                              连拍 6 帧（页面自己的定时器照常在走，所以能拍到"在运行"）
#   {"click_text": "开始"}                        点文字包含它的第一个按钮
#   {"click_css": "#eventBar .gen"}           点选择器命中的元素
#   {"until_css": "#report.show", "max": 70}  一直连拍，直到这个选择器出现（最多 max 帧）
#   {"scroll_css": ".drawer .db", "frames": 16}   在这个容器里平滑滚到底，边滚边拍
#   {"eval": "document.body.style.zoom = 1.2"}    执行一段脚本
#   每一步都可以加 "mark": "名字"，这一步开始时的帧号会记进 marks.json，组装时按它对时间。
#
# 输出: out_dir/f000.png ... 和 out_dir/marks.json（含 n 总帧数、dt 帧间隔）
# 依赖: pip install playwright（用本机已装的 Chrome 也行，脚本会自动回退）
import sys, os, json, time, pathlib, shutil, argparse
from playwright.sync_api import sync_playwright

ap = argparse.ArgumentParser()
ap.add_argument("html"); ap.add_argument("out", nargs="?"); ap.add_argument("steps", nargs="?")
ap.add_argument("--probe", action="store_true"); ap.add_argument("--size", default="1920x1080")
ap.add_argument("--dt", type=float, default=0.16); ap.add_argument("--css", default=""); ap.add_argument("--wait", type=float, default=2.5)
a = ap.parse_args()
vw, vh = [int(v) for v in a.size.lower().split("x")]
url = pathlib.Path(a.html).resolve().as_uri()

with sync_playwright() as p:
    try:
        b = p.chromium.launch()
    except Exception:
        b = p.chromium.launch(channel="chrome")
    pg = b.new_page(viewport={"width": vw, "height": vh})
    pg.goto(url); pg.wait_for_timeout(int(a.wait * 1000))
    if a.css:
        pg.add_style_tag(content=a.css); pg.wait_for_timeout(300)

    if a.probe:
        info = pg.evaluate("""() => ({
          title: document.title,
          buttons: [...document.querySelectorAll('button,[onclick],[role=button],.btn,.tab')].map(e => (e.innerText || '').trim().replace(/\\s+/g, ' ')).filter(t => t && t.length < 20).slice(0, 80),
          top: [...document.body.children].map(e => e.tagName + (e.id ? '#' + e.id : '') + (e.className ? '.' + String(e.className).trim().replace(/\\s+/g, '.') : '') + ' ' + Math.round(e.getBoundingClientRect().width) + 'x' + Math.round(e.getBoundingClientRect().height)),
          canvases: document.querySelectorAll('canvas').length, images: document.querySelectorAll('img').length })""")
        shot = str(pathlib.Path(a.html).with_suffix("")) + "_probe.png"
        pg.screenshot(path=shot)
        print(json.dumps(info, ensure_ascii=False, indent=1)); print("screenshot:", shot)
        b.close(); sys.exit(0)

    shutil.rmtree(a.out, ignore_errors=True); os.makedirs(a.out)
    steps = json.load(open(a.steps, encoding="utf-8"))
    marks = {}; n = 0; t0 = time.perf_counter()

    def shot(k=1):
        global n
        for _ in range(k):
            d = t0 + n * a.dt - time.perf_counter()
            if d > 0:
                time.sleep(d)
            pg.screenshot(path=os.path.join(a.out, f"f{n:03d}.png")); n += 1

    for st in steps:
        if "mark" in st:
            marks[st["mark"]] = n
        if "shots" in st:
            shot(st["shots"])
        elif "click_text" in st:
            pg.evaluate("(t) => [...document.querySelectorAll('button,[onclick],[role=button],.btn,.tab,a')].find(e => (e.innerText || '').includes(t)).click()", st["click_text"])
        elif "click_css" in st:
            pg.evaluate("(s) => document.querySelector(s).click()", st["click_css"])
        elif "until_css" in st:
            for _ in range(st.get("max", 80)):
                shot(1)
                if pg.evaluate("(s) => !!document.querySelector(s)", st["until_css"]):
                    break
        elif "scroll_css" in st:
            mx = pg.evaluate("(s) => { const e = document.querySelector(s); window.__sc = e; return e.scrollHeight - e.clientHeight; }", st["scroll_css"])
            K = st.get("frames", 16)
            for i in range(1, K + 1):
                u = i / K; u = u * u * (3 - 2 * u)
                pg.evaluate("(y) => { window.__sc.scrollTop = y; }", mx * u); shot(1)
        elif "eval" in st:
            pg.evaluate(st["eval"])
    marks["n"] = n; marks["dt"] = a.dt
    json.dump(marks, open(os.path.join(a.out, "marks.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(marks)
    b.close()
