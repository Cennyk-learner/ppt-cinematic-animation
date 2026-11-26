"""Build the branch's 16:9 PowerPoint test and a matching playback preview."""

import argparse
import importlib.util
import math
import os
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_CONNECTOR
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.xmlchemy import OxmlElement
from pptx.oxml import parse_xml
from pptx.util import Emu, Pt

ROOT = Path(__file__).resolve().parent
SCREEN = (1280, 720)
PAPER = "ECE9DF"
INK = "272A27"
GRAPHITE = "222A2A"
CREAM = "F2EDDC"
RED = "FF7959"
DIM = "84908B"
TYPE = os.environ.get("PAPER_TYPEFACE", "Microsoft YaHei")
TITLE = [
    ["一张纸，", "能撑住它吗？"],
    ["平放时，", "纸面向下弯。"],
    ["把同一张纸", "折出四道脊。"],
    ["折起后，截面有多高？"],
    ["同一枚砝码，", "纸桥弯得更少。"],
]
NOTES = [
    "看这张架在两个支座间的纸。先预测一下，把这枚砝码放到中央会怎样？停留直到观众作出判断。单击进入下一页。",
    "看纸桥中段和两端。砝码落下时，两端仍然搭在支座上，中段明显下弯。让最后一帧停一下，再翻页。这是同一模型的定性运动示意。",
    "收起砝码，看同一张纸的形状。每一条折脊都顺着两支座之间的跨度延伸。纸宽方向折成八个斜面，端部能数到四个峰。请在折完后翻页。",
    "从端部看。设每个折面的截线长 20 mm，斜面与水平线成 60°。峰谷高度 h = 20 × sin(60°) ≈ 17.3 mm。八个折面对应四个完整锯齿，投影总宽为 80 mm。折痕抬高了截面，让部分纸材远离弯曲中性轴，有助于提高沿跨度方向的抗弯刚度。这里的 17.3 mm 是几何计算值。",
    "回到开场的机位，砝码、支座和跨度相同，改变的是纸的截面。对照第 2 页，弯曲的差别直接可见。画面用预设位移作定性示意，没有测量承重或计算挠度。纸桥对比实验背景：University of Manchester, Different cross-sections of a paper bridge. https://www.mub.eps.manchester.ac.uk/wp-content/uploads/sites/86/2021/10/Different-cross-sections-of-a-paper-bridge.pdf",
]
SCENES = ["cover", "flat", "fold", "diagram", "return"]
HOLDS = [3.4, 4.0, 4.0, 4.6, 4.0]
SOURCE_FPS = 20


def emu(px):
    return Emu(round(px * 9525))


def rgb(hex_color):
    return RGBColor.from_string(hex_color)


def native_label(slide, name, text, x, y, w, h, size, color, bold=False):
    box = slide.shapes.add_textbox(emu(x), emu(y), emu(w), emu(h))
    box.name = name
    tf = box.text_frame
    tf.word_wrap = False
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = Emu(0)
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    par = tf.paragraphs[0]
    par.alignment = PP_ALIGN.LEFT
    par.space_before = par.space_after = Pt(0)
    run = par.add_run()
    run.text = text
    run.font.name = TYPE
    run.font.bold = bold
    run.font.size = Pt(size * 0.75)
    run.font.color.rgb = rgb(color)
    rpr = run._r.get_or_add_rPr()
    rpr.set("lang", "zh-CN")
    ea = OxmlElement("a:ea")
    ea.set("typeface", TYPE)
    rpr.append(ea)
    return box.shape_id


def polyline(slide, name, pts, color, width):
    origin = pts[0]
    path = slide.shapes.build_freeform(emu(origin[0]), emu(origin[1]))
    path.add_line_segments([(emu(x), emu(y)) for x, y in pts[1:]], close=False)
    shape = path.convert_to_shape()
    shape.name = name
    shape.fill.background()
    shape.line.color.rgb = rgb(color)
    shape.line.width = Pt(width * 0.75)
    return shape.shape_id


def slide_content(index):
    # All coordinates refer to the same 1280 x 720 design space in PPT and video.
    if index != 3:
        size = 68 if index == 0 else 59
        y0 = 64 if index == 0 else 74
        return [
            (
                "text",
                "标题 " + str(i + 1),
                row,
                76,
                y0 + i * (size + 13),
                590,
                size + 19,
                size,
                INK,
                True,
            )
            for i, row in enumerate(TITLE[index])
        ]
    x0, bottom, dx = 98, 542, 87.5
    top = bottom - dx * math.sqrt(3)
    points = [(x0 + i * dx, top if i % 2 else bottom) for i in range(9)]
    ax, ay, radius = x0 + 2 * dx, bottom, 43
    arc = [
        (
            ax + radius * math.cos(math.radians(a)),
            ay - radius * math.sin(math.radians(a)),
        )
        for a in range(0, 61, 4)
    ]
    return [
        ("text", "标题", TITLE[index][0], 76, 68, 1100, 92, 63, CREAM, True),
        ("line", "截面基准线", [(80, bottom), (920, bottom)], "65716B", 1.4),
        ("line", "四道折脊 · 八个折面", points, CREAM, 7.2),
        ("line", "角度弧", arc, RED, 2.6),
        ("text", "折面与水平面的夹角", "60°", ax + 48, ay - 54, 77, 46, 29, RED, False),
        (
            "line",
            "折面引线",
            [
                (540, 321),
                (516, 321),
                (ax + 3.56 * dx, bottom - 0.44 * dx * math.sqrt(3) - 8),
            ],
            DIM,
            1.5,
        ),
        ("text", "折面长度", "折面 20 mm", 548, 296, 240, 47, 26, CREAM, False),
        ("line", "上方延伸线", [(x0 + 7 * dx + 13, top), (903, top)], "77847D", 1.25),
        ("line", "峰谷高度标尺", [(896, top), (896, bottom)], RED, 3),
        ("line", "标尺上端", [(887, top), (905, top)], RED, 3),
        ("line", "标尺下端", [(887, bottom), (905, bottom)], RED, 3),
        ("text", "高度数值", "17.3", 932, 392, 237, 106, 82, RED, True),
        ("text", "高度单位", "mm", 940, 491, 140, 53, 34, CREAM, False),
    ]


def add_native(slide, index):
    ids = []
    for item in slide_content(index):
        kind, name, *args = item
        shape_id = (
            native_label(slide, name, *args)
            if kind == "text"
            else polyline(slide, name, *args)
        )
        if name in {
            "峰谷高度标尺",
            "标尺上端",
            "标尺下端",
            "高度数值",
            "高度单位",
            "上方延伸线",
        }:
            ids.append(shape_id)
    return ids


def timed_reveal(slide, ids):
    # Native visibility sets run on slide entry, followed by a short native fade.
    if not ids:
        return
    effects = []
    seq_id = 8
    for shape_id in ids:
        effects.append(
            f'<p:par><p:cTn id="{seq_id}" presetID="10" presetClass="entr" presetSubtype="0" fill="hold" nodeType="withEffect"><p:stCondLst><p:cond delay="0"/></p:stCondLst><p:childTnLst><p:set><p:cBhvr><p:cTn id="{seq_id + 1}" dur="1" fill="hold"/><p:tgtEl><p:spTgt spid="{shape_id}"/></p:tgtEl><p:attrNameLst><p:attrName>style.visibility</p:attrName></p:attrNameLst></p:cBhvr><p:to><p:strVal val="visible"/></p:to></p:set><p:animEffect transition="in" filter="fade"><p:cBhvr><p:cTn id="{seq_id + 2}" dur="420"/><p:tgtEl><p:spTgt spid="{shape_id}"/></p:tgtEl></p:cBhvr></p:animEffect></p:childTnLst></p:cTn></p:par>'
        )
        seq_id += 3
    timing = (
        '<p:timing xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"><p:tnLst><p:par><p:cTn id="1" dur="indefinite" restart="never" nodeType="tmRoot"><p:childTnLst><p:seq concurrent="1" nextAc="seek"><p:cTn id="2" dur="indefinite" nodeType="mainSeq"><p:childTnLst><p:par><p:cTn id="3" fill="hold"><p:stCondLst><p:cond delay="650"/></p:stCondLst><p:childTnLst><p:par><p:cTn id="4" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst><p:childTnLst>'
        + "".join(effects)
        + '</p:childTnLst></p:cTn></p:par></p:childTnLst></p:cTn></p:par></p:childTnLst></p:cTn><p:prevCondLst><p:cond evt="onPrev" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:prevCondLst><p:nextCondLst><p:cond evt="onNext" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:nextCondLst></p:seq></p:childTnLst></p:cTn></p:par></p:tnLst></p:timing>'
    )
    slide._element.append(parse_xml(timing))


def frame_paths(root, scene):
    folder = root / "frames" / scene
    return sorted(
        p for p in folder.iterdir() if p.suffix.lower() in {".jpg", ".jpeg", ".png"}
    )


def build(frames_root, tool, work, output):
    spec = importlib.util.spec_from_file_location("frames_pack", tool)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    deck = Presentation()
    deck.slide_width, deck.slide_height = map(emu, SCREEN)
    deck.core_properties.title = "一张纸，能撑住它吗？"
    deck.core_properties.subject = "纸桥横截面与弯曲的动画演示"
    for i, scene in enumerate(SCENES):
        s = deck.slides.add_slide(deck.slide_layouts[6])
        s.background.fill.solid()
        s.background.fill.fore_color.rgb = rgb(GRAPHITE if i == 3 else PAPER)
        if i != 3:
            if i == 0:
                media = frame_paths(frames_root, scene)[0]
            else:
                media = work / (scene + ".gif")
                mod.pack(
                    mod.numbered_frames(frames_root / "frames" / scene),
                    media,
                    SOURCE_FPS,
                )
            pic = s.shapes.add_picture(
                str(media), 0, 0, width=deck.slide_width, height=deck.slide_height
            )
            pic.name = "三维纸桥 · " + scene
        ids = add_native(s, i)
        if i == 3:
            timed_reveal(s, ids)
        s.notes_slide.notes_text_frame.text = NOTES[i]
    deck.save(output)


def font_for(bold, size):
    windows_fonts = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"
    prefix = "/Applications/Microsoft PowerPoint.app/Contents/Resources/DFonts/"
    candidates = [
        os.environ.get("PAPER_FONT_BOLD" if bold else "PAPER_FONT_REGULAR"),
        str(windows_fonts / ("msyhbd.ttc" if bold else "msyh.ttc")),
        prefix + ("msyhbd.ttc" if bold else "msyh.ttc"),
        "/usr/share/fonts/opentype/noto/NotoSansCJK-"
        + ("Bold" if bold else "Regular")
        + ".ttc",
        "/System/Library/Fonts/PingFang.ttc",
    ]
    for path in candidates:
        if path and Path(path).exists():
            index = 2 if "NotoSansCJK" in path else 0
            return ImageFont.truetype(path, round(size), index=index)
    raise RuntimeError("A Chinese font is required for the preview")


def overlay(index, show_result=True):
    # Render the native geometry at double resolution before downsampling.
    large = Image.new("RGBA", (2560, 1440))
    draw = ImageDraw.Draw(large)
    for kind, name, *args in slide_content(index):
        if not show_result and name in {
            "峰谷高度标尺",
            "标尺上端",
            "标尺下端",
            "高度数值",
            "高度单位",
            "上方延伸线",
        }:
            continue
        if kind == "line":
            points, color, width = args
            draw.line(
                [(round(x * 2), round(y * 2)) for x, y in points],
                fill="#" + color,
                width=max(1, round(width * 2)),
                joint="curve",
            )
        else:
            text, x, y, w, h, sz, color, bold = args
            f = font_for(bold, sz * 2)
            # Ascender and descender center a line box, matching text frame middle anchor.
            asc, desc = f.getmetrics()
            baseline = round(2 * (y + h / 2) + (asc - desc) / 2)
            draw.text(
                (round(2 * x), baseline), text, font=f, fill="#" + color, anchor="ls"
            )
    return large.resize(SCREEN, Image.Resampling.LANCZOS)


def video(frames_root, work, output, ffmpeg):
    fps = 20
    montage = []
    n = 0
    folder = work / "movie_frames"
    folder.mkdir(exist_ok=True)
    for i, scene in enumerate(SCENES):
        layers = overlay(i)
        if i == 3:
            initial = overlay(i, False)
        else:
            images = frame_paths(frames_root, scene)
        total = round(HOLDS[i] * fps)
        for j in range(total):
            if i == 3:
                bg = Image.new("RGBA", SCREEN, "#" + GRAPHITE)
                t = min(1, max(0, (j / fps - 0.65) / 0.42))
                layer = Image.blend(initial, layers, t) if t < 1 else layers
            else:
                with Image.open(
                    images[min(round(j * SOURCE_FPS / fps), len(images) - 1)]
                ) as src:
                    bg = src.convert("RGBA").resize(SCREEN, Image.Resampling.LANCZOS)
                layer = layers
            frame = Image.alpha_composite(bg, layer).convert("RGB")
            if j == total - 2 or (i in {1, 2, 4} and j == total // 4):
                thumb = frame.copy()
                thumb.thumbnail((480, 270))
                montage.append(thumb)
            frame.save(folder / f"{n:04d}.jpg", quality=90, subsampling=0)
            n += 1
    strip = Image.new("RGB", (960, 270 * math.ceil(len(montage) / 2)), "#e6e5df")
    for k, im in enumerate(montage):
        strip.paste(im, ((k % 2) * 480, (k // 2) * 270))
    strip.save(work / "review.jpg", quality=90)
    if ffmpeg and Path(ffmpeg).exists():
        subprocess.run(
            [
                ffmpeg,
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-framerate",
                str(fps),
                "-i",
                str(folder / "%04d.jpg"),
                "-c:v",
                "libx264",
                "-crf",
                "17",
                "-preset",
                "fast",
                "-pix_fmt",
                "yuv420p",
                "-movflags",
                "+faststart",
                str(output),
            ],
            check=True,
        )
    else:
        print("Movie frames are ready for the platform encoder.", flush=True)
    print(f"preview: {n} frames at {fps} fps", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--scene", type=Path, default=ROOT)
    parser.add_argument(
        "--tool",
        type=Path,
        default=ROOT.parents[1] / "scripts" / "pack_scene_frames.py",
    )
    parser.add_argument("--work", type=Path, default=ROOT / "assembled")
    parser.add_argument("--out", type=Path, default=ROOT / "output")
    parser.add_argument("--fps", type=int, default=16)
    parser.add_argument("--ffmpeg", default=shutil.which("ffmpeg"))
    parser.add_argument("--only", choices=["pptx", "preview", "all"], default="all")
    args = parser.parse_args()
    SOURCE_FPS = args.fps
    args.out.mkdir(parents=True, exist_ok=True)
    args.work.mkdir(parents=True, exist_ok=True)
    if args.only in {"pptx", "all"}:
        build(args.scene, args.tool, args.work, args.out / "纸桥_动画样片.pptx")
    if args.only in {"preview", "all"}:
        video(args.scene, args.work, args.out / "纸桥_放映预览.mp4", args.ffmpeg)
