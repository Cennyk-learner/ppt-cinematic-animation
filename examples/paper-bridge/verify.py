"""Check the motion, native geometry, slide order, file integrity and video stream."""

import io
import json
import subprocess
from pathlib import Path
from zipfile import ZipFile

from PIL import Image, ImageChops
from pptx import Presentation

HERE = Path(__file__).resolve().parent
output = HERE / "output"
deck_file = next(output.glob("*.pptx"))
movie = next(output.glob("*.mp4"))
prs = Presentation(deck_file)
assert len(prs.slides) == 5
for slide in prs.slides:
    assert slide.notes_slide.notes_text_frame.text
    assert any(shape.has_text_frame and shape.text.strip() for shape in slide.shapes)
with ZipFile(deck_file) as archive:
    assert archive.testzip() is None
    gifs = [path for path in archive.namelist() if path.lower().endswith(".gif")]
    assert len(gifs) == 3
    for path in gifs:
        with Image.open(io.BytesIO(archive.read(path))) as image:
            assert (
                image.size == (1280, 720)
                and image.n_frames > 10
                and "loop" not in image.info
            )
            first = image.convert("RGB")
            image.seek(image.n_frames - 1)
            assert ImageChops.difference(first, image.convert("RGB")).getbbox()
    diagram = archive.read("ppt/slides/slide4.xml")
    assert b"<p:timing" in diagram and b"17.3" in diagram and b"20 mm" in diagram
print(
    "Five slides, three one-shot animated illustrations, editable dimension diagram and speaker notes."
)
stream = json.loads(
    subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_streams", "-of", "json", str(movie)]
    )
)["streams"][0]
assert stream["codec_name"] == "h264" and (stream["width"], stream["height"]) == (
    1280,
    720,
)
assert 19 <= float(stream["duration"]) <= 21
print(
    f"{movie.name}: {stream['duration']} s, {stream['codec_name']}, {stream['width']} x {stream['height']}"
)
