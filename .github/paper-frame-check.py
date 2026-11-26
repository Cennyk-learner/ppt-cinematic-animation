from pathlib import Path
import importlib.util
import math
import tempfile
from PIL import Image,ImageDraw,ImageSequence
import sys
source=Path(sys.argv[1])
spec=importlib.util.spec_from_file_location("pack_frames", source)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
with tempfile.TemporaryDirectory() as td:
    root=Path(td)
    for i in range(9, 33):
        im=Image.new("RGB",(50,36),"#ededed")
        ImageDraw.Draw(im).rectangle((i-8,4,i-2,25),fill="#db391e")
        im.save(root/f"frame_{i}.png")
    frames=mod.numbered_frames(root)
    assert frames[0].stem=="frame_9" and frames[-1].stem=="frame_32"
    for repeat in [False,True]:
        out=root/("repeat.gif" if repeat else "once.gif")
        mod.pack(frames,out,23.976,repeat)
        with Image.open(out) as im:
            assert im.size==(50,36) and im.n_frames==24 and (im.info.get("loop")==0)==repeat
            assert abs(sum(p.info["duration"] for p in ImageSequence.Iterator(im))-1000)<11
    def rejected(invoke, expected):
        try: invoke()
        except ValueError as e: assert expected.lower() in str(e).lower(),str(e)
        else: raise AssertionError(expected)
    (root/"same_09.png").write_bytes(frames[0].read_bytes())
    rejected(lambda:mod.numbered_frames(root),"duplicate")
    (root/"same_09.png").unlink()
    frames[3].unlink()
    rejected(lambda:mod.numbered_frames(root),"consecutive")
    Image.new("RGBA",(50,36),(240,220,200,128)).save(frames[3])
    previous=(root/"once.gif").read_bytes()
    rejected(lambda:mod.pack(frames,root/"once.gif",20),"composite")
    assert (root/"once.gif").read_bytes()==previous
    Image.new("RGB",(11,11)).save(frames[3])
    rejected(lambda:mod.pack(frames,root/"once.gif",20),"size")
    rejected(lambda:mod.pack(frames,root/"once.gif",0),"frame rate")
    rejected(lambda:mod.pack(frames[:1],root/"once.gif",20),"two")
print("PASS: numeric ordering, timing at 23.976 fps, one-shot, loop, gaps, duplicate indices, alpha, size, fps and atomic failure")
