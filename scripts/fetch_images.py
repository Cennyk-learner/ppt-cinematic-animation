# -*- coding: utf-8 -*-
"""找真实素材：Bing 图片搜索（无头浏览器）+ 批量下载 + 联系表；Wikimedia Commons 搜索和原图下载。

  python fetch_images.py bing  "江山如此多娇 傅抱石 关山月" outdir [60]     # 搜 → 下载 → outdir/_sheet.jpg, _index.json
  python fetch_images.py commons-search "A Thousand Li of Rivers and Mountains" [15]
  python fetch_images.py commons-get "File:xxx.jpg" out.jpg [宽度]

要点：
- 普通的 requests 拿不到 Bing 图片结果（页面靠脚本渲染），要用 playwright 打开再读 a.iusc 的 m 属性。
- 很多国内站点有防盗链，下载时把来源页放进 Referer，否则拿到的是一页 403 HTML。
- _index.json 按像素数从大到小排；先看联系表挑图，再用 Read 看大图确认有没有水印、是不是原作。
- 公有领域的古画、帝王像、老地图优先从 Commons 拿：分辨率高，来源清楚。
"""
import io, json, os, sys, hashlib, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"


def bing(query, outdir, mx=60):
    from playwright.sync_api import sync_playwright
    from PIL import Image, ImageDraw
    os.makedirs(outdir, exist_ok=True)
    url = "https://www.bing.com/images/search?q=" + urllib.parse.quote(query) + "&qft=+filterui:imagesize-large&form=IRFLTR"
    items = []
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(locale="zh-CN", viewport={"width": 1600, "height": 1200})
        pg.goto(url, wait_until="domcontentloaded", timeout=60000)
        pg.wait_for_timeout(3000)
        for _ in range(4):
            pg.mouse.wheel(0, 4000); pg.wait_for_timeout(1200)
        for m in pg.eval_on_selector_all("a.iusc", "els => els.map(e => e.getAttribute('m'))"):
            try:
                d = json.loads(m); items.append({"murl": d.get("murl"), "purl": d.get("purl"), "t": d.get("t")})
            except Exception:
                pass
        b.close()
    items = items[:mx]

    def fetch(i_it):
        i, it = i_it
        try:
            req = urllib.request.Request(it["murl"], headers={"User-Agent": UA, "Referer": it.get("purl") or it["murl"]})
            im = Image.open(io.BytesIO(urllib.request.urlopen(req, timeout=25).read())); im.load()
            name = f"{i:03d}_{hashlib.md5(it['murl'].encode()).hexdigest()[:6]}.jpg"
            im.convert("RGB").save(os.path.join(outdir, name), quality=95)
            return dict(file=name, size=im.size, url=it["murl"], page=it.get("purl"), title=it.get("t"))
        except Exception:
            return None

    with ThreadPoolExecutor(12) as ex:
        ok = [r for r in ex.map(fetch, enumerate(items)) if r]
    ok.sort(key=lambda r: -r["size"][0] * r["size"][1])
    json.dump(ok, open(os.path.join(outdir, "_index.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    cols, tw, th = 6, 320, 220
    sheet = Image.new("RGB", (cols * tw, max(1, (len(ok) + cols - 1) // cols) * (th + 18)), (30, 30, 30))
    d = ImageDraw.Draw(sheet)
    for k, r in enumerate(ok):
        im = Image.open(os.path.join(outdir, r["file"])); im.thumbnail((tw - 6, th - 6))
        x, y = (k % cols) * tw, (k // cols) * (th + 18)
        sheet.paste(im, (x + 3, y + 3)); d.text((x + 4, y + th), f"{r['file'][:3]} {r['size'][0]}x{r['size'][1]}", fill=(255, 255, 0))
    sheet.save(os.path.join(outdir, "_sheet.jpg"), quality=85)
    print(len(ok), "images ->", outdir)


API = "https://commons.wikimedia.org/w/api.php?"
CUA = "SlideAnimationSkill/1.0 (educational use)"


def _commons(params):
    req = urllib.request.Request(API + urllib.parse.urlencode(params), headers={"User-Agent": CUA})
    return json.loads(urllib.request.urlopen(req, timeout=40).read())


def commons_search(q, n=15):
    d = _commons({"action": "query", "format": "json", "generator": "search", "gsrsearch": q, "gsrnamespace": 6,
                  "gsrlimit": n, "prop": "imageinfo", "iiprop": "size|url"})
    for p in sorted(d.get("query", {}).get("pages", {}).values(), key=lambda p: p.get("index", 0)):
        ii = p.get("imageinfo", [{}])[0]
        print(f'{ii.get("width")}x{ii.get("height")}  {p["title"]}')


def commons_get(title, out, width=None):
    params = {"action": "query", "format": "json", "titles": title, "prop": "imageinfo", "iiprop": "url|size"}
    if width:
        params["iiurlwidth"] = width       # 几万像素宽的长卷用原图；巨幅照片给个宽度拿缩略图
    ii = list(_commons(params)["query"]["pages"].values())[0]["imageinfo"][0]
    url = ii.get("thumburl") or ii["url"]
    data = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": CUA}), timeout=300).read()
    open(out, "wb").write(data)
    print(out, len(data) // 1024, "KB", ii.get("width"), ii.get("height"))


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "bing":
        bing(sys.argv[2], sys.argv[3], int(sys.argv[4]) if len(sys.argv) > 4 else 60)
    elif cmd == "commons-search":
        commons_search(sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 15)
    elif cmd == "commons-get":
        commons_get(sys.argv[2], sys.argv[3], int(sys.argv[4]) if len(sys.argv) > 4 else None)
