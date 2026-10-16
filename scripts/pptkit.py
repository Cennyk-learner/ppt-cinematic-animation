# -*- coding: utf-8 -*-
"""PowerPoint COM 动画工具的 Python 版（和 ppt_tools.ps1 同一套写法，整份多页稿用它更顺手）。

版面按 960 x 540 pt（16:9）。颜色用 (r, g, b)。需要 pywin32：pip install pywin32

写法约定（和 ppt_tools.ps1 一样）：
  k.click()        开始新的一幕（一次点击）；之后的效果都是"与上一动画同时"，用延时排先后
  k.beat(t)        同一次点击里的下一拍：之后的延时从点击后第 t 秒算起
  k.keep(shape)    这一层之后会被盖住；k.retire(t) 让登记过的层在 t 秒时退场
  k.raise_top()    一页写完时把文字、线、印章提到最上面

最小例子：
    k = Kit(r'D:\\work\\base.pptx', r'D:\\work\\assets')
    try:
        k.use(1)
        bg = k.pic('scene.gif', '第一幕-底图')
        t = k.text('江山如此多娇', 116, 40, 70, FONT_BRUSH, vertical=True, h=455)
        k.wipe(t, 1.0, 1.6, WIPE_TOP)
        k.click()
        ...
        k.raise_top(); k.notes('讲稿……')
        print(k.save(r'D:\\work\\out.pptx'))
    finally:
        k.close()
"""
import os, time
import win32com.client as wc
import pythoncom

FX_APPEAR, FX_FADE, FX_WIPE, FX_ZOOM, FX_GROW, FX_CUSTOM, FX_MEDIA_PLAY = 1, 10, 22, 23, 59, 0, 83
WIPE_TOP, WIPE_RIGHT, WIPE_BOTTOM, WIPE_LEFT = 1, 2, 3, 4
TR_FADE_SMOOTH, TR_MORPH = 3844, 3954

# 字体：按题材换。中文题材的选字见 references/typography.md
FONT_BRUSH = '演示镇魂行楷'                          # 大标题、单个大字：干笔行楷
FONT_KAI = 'ChillCalligraphyChunQiu'                 # 诗句、副题：寒蝉春秋体（书法楷）
FONT_PRINT = 'Zhuque Fangsong (technical preview)'   # 说明小字：朱雀仿宋


def rgb(c):
    r, g, b = c
    return int(r) + int(g) * 256 + int(b) * 65536


def fmt(v):
    s = f"{v:.5f}".rstrip('0').rstrip('.')
    return s if s not in ('', '-0') else '0'


class Kit:
    def __init__(self, base, assets):
        pythoncom.CoInitialize()
        self.app = wc.Dispatch('PowerPoint.Application')
        self.pres = self.app.Presentations.Open(os.path.abspath(base), False, False, False)
        self.assets = os.path.abspath(assets)      # COM 只认反斜杠的绝对路径
        self.off = 0.0
        self.top = []
        self.live = []
        self.n = 0

    # ---------------- 页 ----------------
    def use(self, idx, bg=(8, 7, 6)):
        """切到第 idx 页，清空，设纯色底（暗色底，平滑切换时不会露白）"""
        self.slide = self.pres.Slides.Item(idx)
        self.seq = self.slide.TimeLine.MainSequence
        while self.slide.Shapes.Count:
            self.slide.Shapes.Item(1).Delete()
        self.slide.FollowMasterBackground = 0
        self.slide.Background.Fill.Solid()
        self.slide.Background.Fill.ForeColor.RGB = rgb(bg)
        self.off = 0.0; self.top = []; self.live = []
        return self.slide

    def transition(self, effect=TR_FADE_SMOOTH, dur=0.8):
        t = self.slide.SlideShowTransition
        t.EntryEffect = effect; t.Duration = dur
        t.AdvanceOnClick = -1; t.AdvanceOnTime = 0

    def notes(self, text):
        """讲稿写进备注栏，放映时演讲者视图里看得到"""
        self.slide.NotesPage.Shapes.Placeholders(2).TextFrame.TextRange.Text = text

    # ---------------- 效果 ----------------
    def fx(self, shape, effect, delay, dur=0, exit=False, on_click=False, direction=0):
        e = self.seq.AddEffect(shape, effect, 0, 1 if on_click else 2)
        if exit:
            e.Exit = -1
        if direction:
            e.EffectParameters.Direction = direction
        e.Timing.TriggerDelayTime = float(delay + self.off)
        if dur > 0:
            e.Timing.Duration = float(dur)
        return e

    def fin(self, s, delay, dur=0.6):
        return self.fx(s, FX_FADE, delay, dur)

    def fout(self, s, delay, dur=0.5):
        return self.fx(s, FX_FADE, delay, dur, exit=True)

    def cut(self, s, delay):
        return self.fx(s, FX_APPEAR, delay)

    def cut_out(self, s, delay):
        return self.fx(s, FX_APPEAR, delay, exit=True)

    def wipe(self, s, delay, dur, direction=WIPE_TOP):
        """擦除进入。竖排字用 WIPE_TOP，就是"一笔笔写下来"；横排用 WIPE_LEFT"""
        return self.fx(s, FX_WIPE, delay, dur, direction=direction)

    def zoom_in(self, s, delay, dur=0.5):
        """缩放进入（从小长大）：盖印章用"""
        return self.fx(s, FX_ZOOM, delay, dur)

    def click(self):
        d = self.slide.Shapes.AddShape(1, -40, -40, 6, 6)
        d.Line.Visible = 0; d.Fill.Transparency = 1.0
        self.n += 1; d.Name = f'拍-{self.n}'
        self.off = 0.0
        self.fx(d, FX_APPEAR, 0, on_click=True)

    def beat(self, t):
        self.off = t

    def move(self, s, dx, dy, delay, dur, ease=True):
        e = self.seq.AddEffect(s, FX_CUSTOM, 0, 2)
        e.Behaviors.Add(1).MotionEffect.Path = f'M 0 0 L {fmt(dx / 960)} {fmt(dy / 540)} E'
        e.Timing.TriggerDelayTime = float(delay + self.off); e.Timing.Duration = float(dur)
        e.Timing.SmoothStart = -1 if ease else 0; e.Timing.SmoothEnd = -1 if ease else 0
        return e

    def slide_in(self, s, dx, dy, delay, dur):
        """从偏移 (dx, dy) 处滑回原位（路径以显式的 M 开头）"""
        e = self.seq.AddEffect(s, FX_CUSTOM, 0, 2)
        e.Behaviors.Add(1).MotionEffect.Path = f'M {fmt(dx / 960)} {fmt(dy / 540)} L 0 0 E'
        e.Timing.TriggerDelayTime = float(delay + self.off); e.Timing.Duration = float(dur)
        e.Timing.SmoothStart = 0; e.Timing.SmoothEnd = -1
        return e

    def grow(self, s, pct, delay, dur):
        """缓推：只加在满幅的层上"""
        e = self.seq.AddEffect(s, FX_GROW, 0, 2)
        b = e.Behaviors.Item(1).ScaleEffect; b.ByX = float(pct); b.ByY = float(pct)
        e.Timing.TriggerDelayTime = float(delay + self.off); e.Timing.Duration = float(dur)
        e.Timing.SmoothStart = 0; e.Timing.SmoothEnd = -1
        return e

    def zoom_out(self, nxt, k, fx_, fy_, t, dur, prev=(), target=(480, 270)):
        """镜头拉远：nxt 里的满幅图层开始时放大 k 倍，并让它的点 (fx_, fy_) 落在页面上的 target，
        然后缩回满幅；prev 里的层同时淡出。target 对准上一幕里的同一样东西，就是一次匹配剪辑
        （例：桌上写好的题字 → 拉远成画上的题字）。"""
        tx, ty = target
        for x in nxt:
            x.Width = 960 * k; x.Height = 540 * k
            x.Left = tx - k * fx_; x.Top = ty - k * fy_
            self.fin(x, t, dur * 0.35)
            e = self.seq.AddEffect(x, FX_GROW, 0, 2)
            b = e.Behaviors.Item(1).ScaleEffect; b.ByX = float(100 / k); b.ByY = float(100 / k)
            e.Timing.TriggerDelayTime = float(t + self.off); e.Timing.Duration = float(dur)
            e.Timing.SmoothStart = 0; e.Timing.SmoothEnd = -1
            e = self.seq.AddEffect(x, FX_CUSTOM, 0, 2)
            e.Behaviors.Add(1).MotionEffect.Path = (f'M 0 0 L {fmt((k * (fx_ - 480) + 480 - tx) / 960)} '
                                                   f'{fmt((k * (fy_ - 270) + 270 - ty) / 540)} E')
            e.Timing.TriggerDelayTime = float(t + self.off); e.Timing.Duration = float(dur)
            e.Timing.SmoothStart = 0; e.Timing.SmoothEnd = -1
        for x in prev:
            self.fout(x, t + dur * 0.2, dur * 0.5)

    def keep(self, s):
        self.live.append(s)

    def retire(self, delay):
        for x in self.live:
            self.cut_out(x, delay)
        self.live = []

    # ---------------- 图层 ----------------
    def pic(self, file, name, x=0, y=0, w=960, h=540):
        p = self.slide.Shapes.AddPicture(os.path.join(self.assets, file), False, True, x, y, w, h)
        p.Name = name
        return p

    def rect(self, name, x, y, w, h, color=(0, 0, 0), transp=0.0):
        r = self.slide.Shapes.AddShape(1, x, y, w, h)
        r.Name = name; r.Line.Visible = 0
        r.Fill.Solid(); r.Fill.ForeColor.RGB = rgb(color); r.Fill.Transparency = float(transp)
        r.Shadow.Visible = 0
        return r

    def line(self, name, x0, y0, x1, y1, color=(196, 184, 164), weight=0.6, transp=0.0):
        ln = self.slide.Shapes.AddLine(x0, y0, x1, y1)
        ln.Name = name
        ln.Line.ForeColor.RGB = rgb(color); ln.Line.Weight = float(weight); ln.Line.Transparency = float(transp)
        self.top.append(ln)
        return ln

    def text(self, txt, x, y, size, font=FONT_PRINT, color=(240, 232, 216), name=None, vertical=False,
             w=None, h=None, spacing=0.0, line=1.0, align=1, shadow=0.35, bold=False):
        """原生文本框。
        vertical=True：中文竖排，'\\n' 分列，列从右往左（方向 4 = msoTextOrientationVerticalFarEast；
        方向 5 的列是从左往右排的，中文读序会反）。
        横排一律开自动换行并给足宽度：关掉换行的文本框宽度会塌成十几磅，居中/右对齐全部失效。
        align：1 左/上，2 居中，3 右/下。"""
        rows = txt.split('\n')
        longest = max(len(r) for r in rows)
        if w is None:
            w = size * 1.75 * len(rows) if vertical else size * (longest * (1.15 + spacing / max(size, 1)) + 2)
        if h is None:
            h = size * (longest + 1.2) if vertical else size * 1.6 * len(rows)
        tb = self.slide.Shapes.AddTextbox(4 if vertical else 1, x, y, w, h)
        tb.Name = name or f'字-{txt[:8]}'
        tf = tb.TextFrame2
        tf.WordWrap = -1
        tf.AutoSize = 0
        tf.MarginLeft = tf.MarginRight = tf.MarginTop = tf.MarginBottom = 0
        r = tf.TextRange
        r.Text = txt.replace('\n', '\r')
        f = r.Font
        f.NameFarEast = font; f.Name = font
        f.Size = float(size); f.Fill.ForeColor.RGB = rgb(color); f.Bold = -1 if bold else 0
        if spacing:
            f.Spacing = float(spacing)
        r.ParagraphFormat.Alignment = align
        r.ParagraphFormat.SpaceWithin = float(line)
        if shadow:
            sh = f.Shadow
            sh.Visible = -1; sh.Blur = 6; sh.OffsetX = 0; sh.OffsetY = 1.2
            sh.ForeColor.RGB = 0; sh.Transparency = float(1 - shadow)
        self.top.append(tb)
        return tb

    def media(self, file, name, delay=0.0, volume=0.7, stop_after=1):
        """配乐。图标放在页面外；stop_after=2 让开场音乐延续到下一页再自己淡完。"""
        m = self.slide.Shapes.AddMediaObject2(os.path.join(self.assets, file), False, True, -120, -120, 30, 30)
        m.Name = name; m.Left = -120; m.Top = -120
        try:
            m.MediaFormat.Volume = float(volume)
        except Exception:
            pass
        ps = m.AnimationSettings.PlaySettings
        ps.HideWhileNotPlaying = -1
        try:
            ps.StopAfterSlides = int(stop_after)
        except Exception:
            pass
        e = self.seq.AddEffect(m, FX_MEDIA_PLAY, 0, 2)
        e.Timing.TriggerDelayTime = float(delay + self.off)
        try:
            e.MoveTo(1)
        except Exception:
            pass
        return m

    def raise_top(self):
        for x in self.top:
            try:
                x.ZOrder(0)
            except Exception:
                pass

    # ---------------- 输出 ----------------
    def save(self, dst):
        dst = os.path.abspath(dst)
        for s in self.pres.Slides:
            s.SlideShowTransition.AdvanceOnTime = 0; s.SlideShowTransition.AdvanceOnClick = -1
        if os.path.exists(dst):
            os.remove(dst)      # 文件正被 PowerPoint 开着时会失败：换个名字存
        self.pres.SaveAs(dst)
        return f'saved {os.path.basename(dst)} slides={self.pres.Slides.Count} MB={os.path.getsize(dst) / 1e6:.1f}'

    def video(self, mp4, height=720, sec_per_slide=2, fps=25):
        """导出放映视频核对用。它会自动往下点，每一幕只停到最后一个效果结束。"""
        mp4 = os.path.abspath(mp4)
        if os.path.exists(mp4):
            os.remove(mp4)
        self.pres.CreateVideo(mp4, True, sec_per_slide, height, fps, 85)
        t = 0
        while self.pres.CreateVideoStatus in (1, 2) and t < 3000:
            time.sleep(4); t += 4
        return f'video status={self.pres.CreateVideoStatus} after {t}s'

    def close(self):
        try:
            self.pres.Saved = -1; self.pres.Close()
        except Exception:
            pass
