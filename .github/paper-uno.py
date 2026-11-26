"""Drive the isolated LibreOffice slideshow through its presentation controller."""
import sys
import time
from pathlib import Path

import uno
from com.sun.star.beans import PropertyValue

deck, directory = Path(sys.argv[1]),Path(sys.argv[2])
local = uno.getComponentContext()
resolver = local.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver",local)
for _ in range(60):
    try:
        context = resolver.resolve("uno:socket,host=127.0.0.1,port=2088;urp;StarOffice.ComponentContext")
        break
    except Exception:
        time.sleep(.25)
else:
    raise RuntimeError("Impress did not offer its local presentation controller")
desktop = context.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", context)
read_only = PropertyValue()
read_only.Name, read_only.Value = "ReadOnly", True
document = desktop.loadComponentFromURL(uno.systemPathToFileUrl(str(deck.resolve())),"_blank",0,(read_only,))
presentation = document.getPresentation()
presentation.IsFullScreen = True
presentation.IsEndless = False
presentation.start()
for _ in range(80):
    time.sleep(.12)
    if presentation.isRunning():
        controller=presentation.getController()
        if controller is not None: break
else:
    raise RuntimeError("Impress presentation controller did not start")
print("Impress first page", controller.getCurrentSlideIndex(), flush=True)
(directory/"uno-ready").touch()
for idx in range(1,5):
    key = directory/f"advance-{idx}"
    for _ in range(650):
        if key.exists():break
        time.sleep(.05)
    else:break
    controller.gotoNextEffect()
    time.sleep(.22)
    print("Impress page after trigger",idx,controller.getCurrentSlideIndex(),flush=True)
time.sleep(4.5)
