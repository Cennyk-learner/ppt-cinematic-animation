"""Pack an opaque, numbered render sequence for a PowerPoint picture.

The GIF plays once unless --loop is passed. Frames share one palette to keep
stationary objects stable when lighting or framing changes elsewhere.
"""

import argparse
import re
import tempfile
from pathlib import Path

from PIL import Image


def numbered_frames(folder):
    frames = {}
    for path in folder.iterdir():
        if not path.is_file() or path.suffix.lower() not in {".png", ".jpg", ".jpeg"}:
            continue
        match = re.search(r"(\d+)$", path.stem)
        if match is None:
            raise ValueError(f"Expected a frame number at the end of {path.name}")
        index = int(match.group(1))
        if index in frames:
            raise ValueError(f"Duplicate frame number {index}: {frames[index].name}, {path.name}")
        frames[index] = path
    indices = sorted(frames)
    if len(indices) < 2:
        raise ValueError("Provide at least two numbered frames")
    if indices[-1] - indices[0] != len(indices) - 1:
        raise ValueError("Frame numbers must be consecutive")
    return [frames[i] for i in indices]


def opaque_rgb(path, size):
    with Image.open(path) as source:
        if source.size != size:
            raise ValueError(f"Frame {path.name} has size {source.size}, expected {size}")
        if "A" in source.getbands() or "transparency" in source.info:
            if source.convert("RGBA").getchannel("A").getextrema()[0] < 255:
                raise ValueError(f"Composite {path.name} over its slide background first")
        return source.convert("RGB")


def pack(frames, output, fps, loop=False):
    if len(frames) < 2:
        raise ValueError("Provide at least two numbered frames")
    if not 1 <= fps <= 50:
        raise ValueError("Use a frame rate between 1 and 50 fps")
    with Image.open(frames[0]) as first:
        size = first.size
    sample_count = min(20, len(frames))
    sheet = Image.new("RGB", (120, 72 * sample_count))
    for i in range(sample_count):
        index = round(i * (len(frames) - 1) / (sample_count - 1))
        sample = opaque_rgb(frames[index], size).resize((120, 72), Image.Resampling.BOX)
        sheet.paste(sample, (0, i * 72))
    palette = sheet.quantize(colors=256)
    indexed = [opaque_rgb(path, size).quantize(palette=palette) for path in frames]
    # GIF delays are centiseconds. Round cumulative timestamps to avoid drift.
    durations = [
        10 * (round((i + 1) * 100 / fps) - round(i * 100 / fps))
        for i in range(len(frames))
    ]
    options = {"loop": 0} if loop else {}
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output.parent) as scratch:
        temporary = Path(scratch) / "frames.gif"
        indexed[0].save(
            temporary, format="GIF", save_all=True, append_images=indexed[1:],
            optimize=False, disposal=1, duration=durations, **options,
        )
        temporary.replace(output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("frames", type=Path, help="Folder containing consecutive numbered PNG/JPEG frames")
    parser.add_argument("output", type=Path)
    parser.add_argument("--fps", type=float, default=20)
    parser.add_argument("--loop", action="store_true", help="Repeat indefinitely instead of playing once")
    args = parser.parse_args()
    try:
        pack(numbered_frames(args.frames), args.output, args.fps, args.loop)
    except (OSError, ValueError) as exc:
        parser.exit(2, f"{parser.prog}: {exc}\n")


if __name__ == "__main__":
    main()
