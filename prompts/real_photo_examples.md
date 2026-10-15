# 写实底图的提示词例子

接在 `real_photo_head.txt` 后面用，按"图之间的关系"分组。照着关系写自己的内容，不要照抄题材。`examples/lighthouse/prompt_gen.txt` 是一份完整、原样跑通的提示词（阴天底片 → 雨夜 → 清晨）。

每个文件名后面的方括号说明这张图是哪一种；`[EDIT of …]` 和 `[NIGHT of …]` 必须指向同一次任务里已经保存的文件。

## 白天底片 → 夜景 → 清晨（同一机位）

```
IMAGE 1 -> gen/_day.png [DAY] A wide photograph from a neighbouring headland of an old white-and-red striped stone lighthouse standing on a steep dark rocky cape, in a rising storm. LAYOUT (keep it exactly, later images are edits of this one): the lighthouse stands in the RIGHT third of the frame, its lantern room at about 30% of the frame height from the top; the tower is fairly small in the frame so the scene feels huge. The LEFT half of the frame is open rough sea with a low far horizon at about 52% of the frame height. The upper 45% is heavy, dark, low storm cloud. The bottom 18% of the frame is dark wet foreground rock (space for captions later).

IMAGE 2 -> gen/night.png [NIGHT of gen/_day.png] Heavy rain storm at night. Light sources: the lighthouse LANTERN ROOM glows with one strong warm-white lamp (NO light beam drawn in the air - the beam will be added later); one warm lit window in the keeper's hut.

IMAGE 3 -> gen/dawn.png [EDIT of gen/_day.png] The SAME place and camera the next morning just after sunrise, the storm has passed (this edit changes weather and light everywhere, but camera, framing, rocks and buildings stay identical). ... The lighthouse lamp is OFF. On the sea at the far left-centre, small in the frame, ONE fishing boat heading toward the cape.
```

要点：夜景那张只列光源，别的什么都不说；要后期合成的光（光束、光柱）写明"不要画出来"，否则和合成的打架。

## 同一个机位，很多年

```
IMAGE 1 -> out/y1.png [DUSK] SUMMER, late dusk in light rain. A wide photograph of <一个地方>. LAYOUT (keep it exactly, later images are edits of this one): the upper 40% of the frame is dark cloud above one simple distant ridge line. In the RIGHT-CENTRE, in the middle distance, stands exactly ONE <设备或物件>, a small GREEN status lamp lit. To the right of it is open ground (space for two more later). Across the foreground runs one thin fresh crack in the wet ground. The bottom 18% of the frame is dark foreground.

IMAGE 2 -> out/y2.png [EDIT of out/y1.png] The SAME place and camera about three years later, in AUTUMN, a dry late dusk with thin mist (this edit changes the season everywhere, but camera, framing, terrain and the positions of all objects stay identical). The original <设备> is still standing in the same place but is now DEAD: lamp OFF, slightly rusty. About two metres to its RIGHT a SECOND, clearly different one has been installed, its green lamp lit. The foreground crack is clearly wider.
```

要点：第一张把"以后要加东西的地方"先留出来；后面每张开头都重复"同一地点同一机位，位置不变"。

## 留白：屏幕、空桌面

```
IMAGE 1 -> out/room.png [DUSK] Interior at night: an ordinary real control room / meeting room, photographed from just behind the seated participants, camera low and close, perfectly frontal and level. On the far wall ONE very large flat LED video wall, exactly 16:9, centred, about 64% of the frame width; top edge at about 11% of the frame height, bottom edge at about 75%; edges perfectly horizontal and vertical. It shows a completely plain, uniform, bright WHITE-GREY blank screen (content is added later). In the foreground five or six people seen from BEHIND, only dark heads and shoulders, looking up at the screen. The room is lit only by the screen. Not futuristic.

IMAGE 2 -> out/room2.png [EDIT of out/room.png] ONE change only: the people are now LARGER and HIGHER in the frame, their heads overlapping the BOTTOM 15-18% of the white screen as dark silhouettes with a thin rim of screen light on hair and shoulders. The video wall itself stays EXACTLY identical.
```

```
IMAGE 1 -> out/desk.png [DUSK] Interior at night. An OVERHEAD photograph (camera looking STRAIGHT DOWN, flat-lay) of an ordinary dark wood-veneer office desk lit by one desk lamp from the upper left. Objects ONLY near the left edge and the corners: the lamp base; a brown kraft-paper folder; a round tin of red seal ink paste and a wooden-handled seal; a lidded tea cup at the top-right corner. The whole CENTRE and CENTRE-RIGHT of the desk - at least 46% of the frame width and 80% of the height - is completely EMPTY bare desk inside the lamp light (a sheet of paper will be added later; do NOT put any paper there).
```

要点：屏幕要"正对、水平、白"；桌面要"正俯拍"，之后放上去的截图和扫描件透视才对。第二张房间图用来合成，第一张留着取屏幕亮度的均匀度。

## 两段状态：灯全亮、灯全灭且搬空

```
IMAGE 1 -> out/arc_lit.png [DUSK] Interior at night: an ARCHIVE ROOM, exact one-point perspective looking straight down one long central aisle. Rows of grey steel open shelving recede to a vanishing point at the exact centre; EVERY shelf is packed with uniform box files. One row of fluorescent tubes along the ceiling, ALL switched ON.

IMAGE 2 -> out/arc_dark.png [EDIT of out/arc_lit.png] Two changes, everything else identical. (1) ALL the ceiling lights are OFF, the room nearly dark but dimly readable. (2) In the FARTHER two-thirds of the aisle the shelves are now EMPTY, bare dusty shelves with pale rectangular dust outlines where the boxes stood. The NEAREST third is still packed exactly as before.
```

要点：两张图之间按透视里的嵌套矩形分区混合，就能做出"一段段熄灯搬空"和"一格格亮到底"。

## 把旧图当版式参考重拍

```
IMAGE 1 -> out/r1.png [DUSK] Interior at night. Two reference files: COMPOSITION reference old/r1.png (an AI-looking illustration - copy ONLY its composition: over-the-shoulder view, a person seen from behind in the left third, ONE very large monitor that DOMINATES the centre and right of the frame). STYLE reference try/room.png (copy its look exactly: an ordinary slightly shabby real room, fluorescent light, no cinematic lighting). The monitor shows exactly one simple chart on a black background: a single thin jagged white line crossed by one horizontal red line. No text.
```

要点："构图不变，只换成写实风格"时用这个写法。轻度修图（"保持不变，修得真实一点"）几乎没有变化。
