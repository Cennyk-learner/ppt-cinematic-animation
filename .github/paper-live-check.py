"""Record an isolated Impress slideshow and compare its keyframes with the storyboard."""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageGrab

asset_dir, movie, work = map(Path, sys.argv[1:])
work = work.resolve()
work.mkdir(exist_ok=True, parents=True)
pptx = next(asset_dir.glob("*.pptx")).resolve()
env=dict(os.environ, DISPLAY=":92", SAL_USE_VCLPLUGIN="gen")
def run(args, **opts):
    return subprocess.run(args, env=env, check=True, **opts)
def shot():
    return ImageGrab.grab(xdisplay=env["DISPLAY"]).convert("RGB")
def centroid(pil):
    arr=np.asarray(pil).astype(int)
    region=arr[160:640,440:1200]
    mask=(region[:,:,0]>116)&(region[:,:,0]>region[:,:,1]*1.45)&(region[:,:,0]-region[:,:,2]>53)
    ys,xs=np.where(mask)
    return (float(xs.mean()+440),float(ys.mean()+160)) if len(ys)>280 else (-1.0,-1.0)
def frame(clip, at, dest):
    run(["ffmpeg","-loglevel","error","-y","-ss",str(at),"-i",str(clip),"-frames:v","1",str(dest)])
    return Image.open(dest).convert("RGB")
def dark_ratio(image):
    region=np.asarray(image)[24:240,650:1170]
    return float((region.mean(axis=-1)<80).mean())
capture=work/"slideshow.mp4"
xvfb=subprocess.Popen(["Xvfb",":92","-screen","0","1280x720x24","-nolisten","tcp"],env=env)
show=None
writer=None
control=None
wm=None
try:
    time.sleep(1.3)
    wm=subprocess.Popen(["openbox","--sm-disable"],env=env)
    profile=work/"lo-profile"
    profile_user=profile/"user"
    profile_user.mkdir(parents=True,exist_ok=True)
    (profile_user/"registrymodifications.xcu").write_text('<oor:items xmlns:oor="http://openoffice.org/2001/registry"><item oor:path="/org.openoffice.Office.Common/Misc"><prop oor:name="ShowTipOfTheDay" oor:op="fuse"><value>false</value></prop></item><item oor:path="/org.openoffice.Setup/Office"><prop oor:name="ooSetupInstCompleted" oor:op="fuse"><value>true</value></prop></item></oor:items>')
    show=subprocess.Popen(["soffice","-env:UserInstallation="+profile.as_uri(),"--nologo","--norestore","--nofirststartwizard","--accept=socket,host=127.0.0.1,port=2088;urp;StarOffice.ServiceManager"],env=env)
    control=subprocess.Popen(["/usr/bin/python3",".github/paper-uno.py",str(pptx),str(work)],env=env)
    for k in range(38):
        time.sleep(1)
        if (work/"uno-ready").exists() and centroid(shot())[0]>0:break
        if k in [8,16,26]:
            subprocess.run(["xdotool","key","Escape"],env=env) if not (work/"uno-ready").exists() else None
            view=shot()
            view.thumbnail((640,360))
            view.save(work/f"startup-{k}.jpg")
            tree=subprocess.run(["xwininfo","-root","-tree"],env=env,capture_output=True,text=True)
            print("Display windows",tree.stdout[-3700:],flush=True)
        if control.poll() is not None and control.returncode!=0:break
    else:raise RuntimeError("Slideshow cover was not displayed")
    if not (work/"uno-ready").exists() or centroid(shot())[0]<0:raise RuntimeError("Slideshow failed the cover visual check")
    writer=subprocess.Popen(["ffmpeg","-loglevel","error","-y","-f","x11grab","-draw_mouse","0","-framerate","20","-video_size","1280x720","-i",":92.0","-t","20","-c:v","libx264","-preset","veryfast","-crf","17","-pix_fmt","yuv420p","-movflags","+faststart",str(capture)],env=env)
    started=time.monotonic()
    for number,deadline in enumerate([3.4,7.4,11.4,16.0],start=1):
        time.sleep(max(0,started+deadline-time.monotonic()))
        (work/f"advance-{number}").touch()
    writer.wait(timeout=20)
    results=[]
    actual_frames=[]
    for i,t in enumerate([1.5,3.65,6.8,8.6,10.9,14.5,16.25,19.2]):
        actual=frame(capture,t,work/f"live{i}.jpg")
        ref=frame(movie,t,work/f"ref{i}.jpg")
        actual_frames.append(actual)
        region=(445,150,1225,650)
        a=np.asarray(actual.crop(region).resize((156,100)),dtype=float)
        b=np.asarray(ref.crop(region).resize((156,100)),dtype=float)
        ca,cb=centroid(actual),centroid(ref)
        results.append({"t":t,"photo_error":round(float(np.abs(a-b).mean()),2),"mass_y":round(ca[1],1),"reference_mass_y":round(cb[1],1),"dark":round(dark_ratio(actual),2)})
    independently_advanced=results[5]["dark"]>.88 and all(results[k]["mass_y"]>0 for k in [0,2,4,7])
    moving=results[2]["mass_y"]-results[1]["mass_y"]>32 and results[7]["mass_y"]-results[6]["mass_y"]>12
    matching=all(abs(results[k]["mass_y"]-results[k]["reference_mass_y"])<22 for k in [0,2,4,7]) and max(results[k]["photo_error"] for k in [0,2,4,7])<18
    accept=independently_advanced and moving and matching
    contact=Image.new("RGB",(960,1080),"#e8e5d9")
    for i,fr in enumerate(actual_frames): contact.paste(fr.resize((480,270)),((i%2)*480,(i//2)*270))
    contact.save(work/"live-contact.jpg",quality=88)
    print(json.dumps({"real_slideshow_verified":accept,"frames":results},indent=2),flush=True)
    (work/"receipt.json").write_text(json.dumps({"real_slideshow_verified":accept,"frames":results}))
finally:
    if writer and writer.poll() is None:writer.terminate()
    if show and show.poll() is None:show.terminate()
    if control and control.poll() is None:control.terminate()
    if wm and wm.poll() is None:wm.terminate()
    xvfb.terminate()
