<div align="center">

# PPT Cinematic Animation

**An agent skill that turns a static PowerPoint slide into a cinematic one, while keeping it an editable `.pptx`: no embedded video, and every word stays editable.**

English · [中文](README.md)

![Claude Code Skill](https://img.shields.io/badge/Claude_Code-Skill-d97757)
![PowerPoint](https://img.shields.io/badge/PowerPoint-COM-b7472a)
![Windows](https://img.shields.io/badge/Windows-only-0078d4)
![License](https://img.shields.io/badge/license-MIT-green)

<img src="assets/pearl-hero.webp" width="800" alt="Highlights from a classroom deck on Vermeer's Girl with a Pearl Earring">

<sub>↑ A classroom deck about Vermeer's <i>Girl with a Pearl Earring</i>. Every frame is real PowerPoint slideshow output.</sub>

</div>

---

Most AI slide tools stop at layout: pick a template, fill in text and images. This skill handles the next step, which is making a slide **play** like a film scene, with light and pacing.

It is a skill package for AI coding agents (Claude Code, or any agent that can read `SKILL.md`). Inside:

- **Taste and collaboration principles** distilled from many rounds of real rejections: what reads as high-end and what instantly looks cheap.
- A **library of 50+ techniques** that were actually built. Each entry lists the film reference, what it is good for and how to build it. **The ones that were rejected are recorded too, along with the reasons.**
- A **working pipeline**: generate a set of pixel-aligned base images → composite seamless loop GIFs in Python → assemble native animations through PowerPoint COM → export the slideshow to video and check contact sheets.
- A **typography guide**: which look gives a deck away as AI-made, and for Chinese subjects how to find, compare and set brush, Fangsong and seal-script fonts in vertical columns with carved seals.
- A **pitfall list**. One example: an animated GIF in PowerPoint starts playing when the slide is entered, not when the GIF appears. Miss that and every narrative animation ends up out of sync.
- Ready-to-use **Python / PowerShell helpers** and a complete end-to-end example.

> The skill text itself is written in Chinese. Modern agents follow it fine whatever language you prompt in.

## Showcase

### Built from scratch: a lighthouse in a storm

<img src="assets/lighthouse.webp" width="800" alt="Lighthouse demo: rotating beam in the rain, push-in, fog transition to dawn, a route drawn on the sea">

Source and base images are in [`examples/lighthouse/`](examples/lighthouse/). You can re-run it yourself.

| When | What happens | How |
|---|---|---|
| Slide enters | Rainy night. The lighthouse beam sweeps the sea and lights up the calligraphy in the sky as it passes | One night photo, with the beam, rain, lantern flare and text brightness computed frame by frame in Python and baked into a seamless loop GIF |
| Click 1 | The camera slowly pushes in toward the lantern | Native PowerPoint scale plus a matching motion path, so the focal point stays fixed |
| Click 2 | Fog rolls across; dawn. A gold route is drawn from the fishing boat to the cape, and a spark travels along it | Fog PNG on a native motion path, dawn GIF fades in, the route is revealed with a wipe and the spark follows a polyline path |

The three base images ("overcast plate → same camera at night → same camera at dawn") come from a single image-generation run, so they line up pixel for pixel. All caption text is native text boxes.

### A full classroom deck: *Girl with a Pearl Earring*

<table>
<tr>
<td width="50%"><img src="assets/pearl-gallery.webp" alt="Gallery opening"><br><b>Gallery opening</b>: black → the picture light comes on → title and wall label rise in</td>
<td width="50%"><img src="assets/pearl-morph.webp" alt="Morph push-in"><br><b>Into the painting</b>: a Morph transition grows the painting from the gallery wall to full frame</td>
</tr>
<tr>
<td><img src="assets/pearl-light.webp" alt="Light from the left"><br><b>Light from the left</b>: a soft-edged shadow retreats left to right, then a push-in to the face</td>
<td><img src="assets/pearl-lapis.webp" alt="Ultramarine"><br><b>A blue dearer than gold</b>: push into the turban, then dissolve to lapis lazuli and pigment</td>
</tr>
<tr>
<td><img src="assets/pearl-pearl.webp" alt="Pearl close-up"><br><b>One pearl, two brushstrokes</b>: extreme close-up with leader-line callouts</td>
<td><img src="assets/pearl-delft.webp" alt="Map to landscape"><br><b>Delft</b>: an old map slowly pushes in and dissolves into <i>View of Delft</i></td>
</tr>
<tr>
<td><img src="assets/pearl-works.webp" alt="Wall of works"><br><b>Thirty-odd paintings</b>: the works fill the wall, then only the ones lit from the left remain</td>
<td><img src="assets/pearl-ending.webp" alt="Ending"><br><b>Ending</b>: the painting fades until only the pearl's highlight is left</td>
</tr>
</table>

Each scene was found by starting from the one sentence that slide has to say. The method is in [`references/ideation.md`](references/ideation.md).

### A classroom deck on a Chinese painting: *This Land So Rich in Beauty* (1959)

<img src="assets/jiangshan-hero.webp" width="800" alt="Highlights from a classroom deck on the 1959 painting This Land So Rich in Beauty">

<sub>↑ An 8-minute, two-speaker art-appreciation talk, 16 slides. Every frame is real PowerPoint slideshow output (presenter names removed).</sub>

The brief asked for "lots of different elements, not five slides propped up by animation" and something grand. So every slide brings a new material and a new kind of motion. Half the material is real (the painting, Mao Zedong's handwritten poem, archive photos of the Great Hall being built, the full *A Thousand Li of Rivers and Mountains* scroll, NASA satellite imagery); the other half is generated, pixel-aligned photography. Type got its own round: the first sample frames passed, but the type was called out as "looking like every AI-made deck". Brush calligraphy, vertical columns with ruled lines, a classical Fangsong for captions and carved seals fixed it. See [`references/typography.md`](references/typography.md) (in Chinese).

<table>
<tr>
<td width="50%"><img src="assets/jiangshan-sunrise.webp" alt="Sunrise opening"><br><b>A dot of cinnabar becomes the sun</b>: light spreads from the painting's own sun; the vertical title is brushed in</td>
<td width="50%"><img src="assets/jiangshan-manuscript.webp" alt="Manuscript written column by column"><br><b>Snow, 1936</b>: under a cave-house lamp, the poem's manuscript appears column by column</td>
</tr>
<tr>
<td><img src="assets/jiangshan-wall.webp" alt="The empty wall"><br><b>An empty wall</b>: the frame in the Great Hall lights up and the commission is written on it</td>
<td><img src="assets/jiangshan-inscription.webp" alt="Inscription match cut"><br><b>The inscription</b>: written on a desk, then a pull-back lands it exactly on the painting's inscription</td>
</tr>
<tr>
<td><img src="assets/jiangshan-redsun.webp" alt="Red sun in a cold night"><br><b>Waiting for a clear day</b>: the painting sinks into a cold night, only the sun stays red; a band of light sweeps warmth back</td>
<td><img src="assets/jiangshan-dawn.webp" alt="Storm to sunrise"><br><b>Storm to sunrise</b>: four lighting states from one camera; each click brings dawn closer and pins a photo to the timeline</td>
</tr>
<tr>
<td><img src="assets/jiangshan-gallery.webp" alt="Gallery of emperors"><br><b>All are past and gone</b>: spotlights find five emperors one by one, then go out one by one</td>
<td><img src="assets/jiangshan-today.webp" alt="The painting becomes today"><br><b>Today</b>: the painted landscape bleeds, patch by patch like ink, into a photo of China today; the sun stays put</td>
</tr>
</table>

## How it differs from "ask the AI to add animations"

| Typical result | This skill |
|---|---|
| Fly-in, bounce and spin presets | Photo-real scenes, motivated light and native camera moves, each tied to a specific film reference |
| Generated images that scream "AI": teal/orange grading, bloom, god rays | Prompts written as *"an ordinary news-agency photo"* with cinematic grading explicitly banned; night scenes made in two steps |
| Every image generated separately, so nothing lines up | One run produces a whole set (plate → edits → segmentation mask), pixel-aligned for dissolves and local motion |
| An embedded video that has to be re-rendered for every text change | Loop GIFs plus native PowerPoint animation, with all text kept as editable text boxes |
| Ship it once the script runs | Export the slideshow to video, build contact sheets, and check order, occlusion and text scene by scene |
| The same trick on every slide | The library records rejected ideas and why, and no visual is repeated within a deck |
| The default dark background, thin gold rule and wide-tracked serif | Type that comes from the subject: download brush and classical fonts, compare them on a specimen sheet, set them vertically with seals |

## Quick start

**Requirements**: Windows + Microsoft PowerPoint (assembly goes through COM), Python 3.10+, ffmpeg. For base images you need an image tool that can edit images (the author uses Codex CLI's built-in image generation). Your own photos work too.

```bash
git clone https://github.com/Cennyk-learner/ppt-cinematic-animation ~/.claude/skills/ppt-cinematic-animation
pip install numpy opencv-python-headless python-pptx pillow
pip install pywin32 fonttools playwright   # whole-deck assembly, glyph checks, image search
```

Fonts: the defaults are open-source ([Ma Shan Zheng](https://fonts.google.com/specimen/Ma+Shan+Zheng), [Source Han Serif](https://github.com/adobe-fonts/source-han-serif), [Source Han Sans](https://github.com/adobe-fonts/source-han-sans)). You can change them at the top of `scripts/ppt_tools.ps1`. `scripts/pptkit.py` defaults to the set used in the 1959-painting deck (SlideTownsoul brush, [ChillCalligraphy ChunQiu](https://github.com/Warren2060/ChillCalligraphy), [Zhuque Fangsong](https://github.com/TrionesType/zhuque)); where to get fonts and how to install them is in `references/typography.md`.

Run the bundled examples to check your setup:

```powershell
cd ~/.claude/skills/ppt-cinematic-animation
python scripts/demo_assets.py D:\work\demo
pwsh -NoProfile -File scripts/build_page_example.ps1 -Work D:\work\demo

python examples/lighthouse/render.py D:\work\lighthouse
pwsh -NoProfile -File examples/lighthouse/build.ps1 -Work D:\work\lighthouse
```

Then just talk to your agent:

> Slide 8 of my pitch deck lists three causes in three columns. It's flat. Give me a few cinematic directions.

> Animate it: click to dive into one column, play it out, then return to the overview automatically.

> This background looks too AI-generated. Make it photo-real and keep all the animation.

The skill asks clarifying questions first, proposes three or four distinct directions, and walks through every beat. After you confirm, it makes sample frames, builds the slide, then exports and verifies it.

## What's inside

```
SKILL.md                  entry point: when to use, taste baseline, workflow, hard constraints
references/
  taste.md                taste & collaboration principles
  ideation.md             how to find images in the content, how to pitch directions, two worked examples
  typography.md           type: the look that reads as AI-made; finding, comparing and setting Chinese fonts, seals
  style-library.md        40+ techniques: openings & transitions, light, time, contrast, screens & documents,
                          Morph push-ins, charts & type, endings, and the rejected ones
  pipeline.md             generate → composite → real web UI inside a photographed screen → assemble → verify
  pitfalls.md             PowerPoint, COM, Morph, image generation, compositing, fonts, sourcing & music, GIF size
prompts/                  photo-real prompt template and examples
scripts/
  render_tools.py         loop GIFs, alpha layers, lines, beams & light reveal, lit text, screen compositing
  ppt_tools.ps1           one-click-per-scene COM helpers: paths, push-in, zoom-out, fog cut, captions, export
  pptkit.py               the same helpers in Python for whole decks: vertical CJK text, seals, match-cut zoom-out, music, notes
  scene_tools.py          seamless snow, light spreading from a point, colour bloom, ink-bleed transition, loupe, old prints,
                          selective tint, watermark removal
  typo.py                 type drawn into images: manuscripts to layers, column cuts, carved seals, ruled columns, glyph checks
  fetch_images.py         real-source images: image search + bulk download + contact sheet, Wikimedia Commons originals
  specimen.py             font specimen sheet with missing glyphs flagged
  export_slides.py        whole-deck export & contact sheets, per-slide export with private shapes stripped, WebP clips
  capture_page.py         run a single-file HTML UI headless, click through steps, capture frames
  cap_show.py             capture a live slideshow in the background
examples/lighthouse/      a complete example, from prompt to finished slide
```

## The most valuable lessons

- **GIFs in PowerPoint start playing when the slide is entered**, not when they appear. A narrative that runs after a click has to be split into per-state transparent layers driven by native animations.
- **Writing "cinematic" in a prompt gets you the AI look.** For realism, describe a news photo and explicitly ban grading, bloom and god rays.
- **Shakes, white flashes and impact blur look cheap.** Real weight comes from camera moves and light.
- **Morph's COM `EntryEffect` is 3954** (3953 is Origami). Pairing is by shape name (`!!` prefix), and every other shape name must be unique across the deck, or same-named text will fly around during the transition.
- **Video export auto-advances** and leaves each scene as soon as its last effect ends. `Hold` keeps each scene on screen long enough in the preview.
- **One image plus one loop looks empty.** Give every scene at least two different kinds of motion.
- **Type gives the AI look away too.** Dark background, thin gold rule, wide-tracked Source Han / Noto serif and a thin Arabic-numeral year read as a template. For Chinese subjects, download real calligraphy and classical fonts and compare them on a specimen sheet.
- **Vertical CJK text boxes need orientation 4** (`msoTextOrientationVerticalFarEast`); orientation 5 runs columns left to right. Horizontal boxes with word wrap off collapse in width, and centring stops working.

## FAQ

**macOS?** Assembly and export depend on PowerPoint's COM API, so Windows only. The technique library, the principles and the compositing scripts are useful anywhere.

**Claude Code only?** No. `SKILL.md` and `references/` are plain Markdown, so any agent that can read files and run commands can follow them.

**No image generator?** Use your own photos or stock images. Compositing and assembly don't depend on generation; generation just makes "same camera, different states" easy to align.

**Whole decks?** Whole talks, yes: the 1959-painting deck was built as 16 slides at once (`pipeline.md` §8–9). It is not a general layout-template tool; for decks that only need tidy layout, other tools are faster.

## Credits

- Vermeer's works and the old map of Delft are public domain (Wikimedia Commons). Other imagery in the deck (gallery, pigments) is AI-generated or the author's own photos.
- Base images for the lighthouse example are AI-generated and free to use with this repo.
- Images of *This Land So Rich in Beauty* (Fu Baoshi & Guan Shanyue, 1959), Mao Zedong's manuscript and the archive photos come from public reports and are used here only to document a classroom talk; rights remain with their holders. *A Thousand Li of Rivers and Mountains* and the imperial portraits are public domain (Wikimedia Commons); satellite imagery is NASA Blue Marble. The snowy plateau, the empty hall, the gallery, the Great Wall in snow, the mountain dawn, the display case and "China today" are AI-generated. The music used in class is not distributed with this repo.
- The default fonts of `ppt_tools.ps1` are under the SIL Open Font License; other Chinese fonts follow their own licenses.

## License

[MIT](LICENSE)
