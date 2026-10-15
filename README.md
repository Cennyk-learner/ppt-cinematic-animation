<div align="center">

# PPT Cinematic Animation

**让 AI 把一页静态 PPT 做成电影感的动画页。成品仍是可编辑的 `.pptx`，不嵌视频，文字都能改。**

[English](README_EN.md) · 中文

![Claude Code Skill](https://img.shields.io/badge/Claude_Code-Skill-d97757)
![PowerPoint](https://img.shields.io/badge/PowerPoint-COM-b7472a)
![Windows](https://img.shields.io/badge/Windows-only-0078d4)
![License](https://img.shields.io/badge/license-MIT-green)

<img src="assets/pearl-hero.webp" width="800" alt="《戴珍珠耳环的少女》课堂讲解 PPT 的放映效果混剪">

<sub>↑ 一份讲维米尔《戴珍珠耳环的少女》的课堂 PPT，全部是 PowerPoint 放映时的真实画面（导出视频截取）</sub>

</div>

---

现在的 AI 做 PPT，大多停在"排版"：给一套模板，填上字和图。这个 skill 解决的是下一步：**让一页在放映时有画面、有光、有节奏**。

它是一个给 AI 编程助手（Claude Code，或任何能读 `SKILL.md` 的 agent）用的技能包，里面装着：

- 一套从多轮真实返工里总结出来的**审美与协作原则**：什么样的动画显得高级，什么样的一看就廉价；
- 一份 **40 多种做过的动画手法库**，每条都写了参考的电影、适合讲什么、怎么做，**也写了被否掉的那些和原因**；
- 一条跑通的**制作流程**：生图出成套同构底图 → Python 逐帧合成循环动图 → PowerPoint COM 组装原生动画 → 导出视频抽帧核对；
- 一份**踩坑清单**，比如"PPT 里的 GIF 从进入这一页就开始播放，不等它出现"。不知道这件事，叙事动画一定会错位；
- 可以直接用的 **Python / PowerShell 工具函数**，和一个从生图到成品的完整例子。

## 效果

### 从零做一页：风暴夜的灯塔

<img src="assets/lighthouse.webp" width="800" alt="灯塔演示页：雨夜光束扫过、推近、雾转场到清晨、航线画出">

这一页完全由 skill 的流程做出来，源码和底图都在 [`examples/lighthouse/`](examples/lighthouse/)，可以自己重跑：

| 时刻 | 发生什么 | 怎么做的 |
|---|---|---|
| 进页 | 雨夜，灯塔的光束一圈圈扫过海面，扫过天上的"一束光"时字被照亮 | 一张同机位的夜景 + Python 逐帧算光束、雨、灯笼眩光和字的亮度，烧成无缝循环 GIF |
| 点 1 | 镜头缓缓推向灯笼，关键词换掉 | PowerPoint 原生缩放 + 同步位移（焦点不动） |
| 点 2 | 雾从左漫过，天亮了；一条金色航线从渔船画到灯塔脚下，一个光点沿航线走 | 雾 PNG 走原生路径，清晨 GIF 淡入，航线用擦除"画"出来，光点沿折线路径走 |

三张底图是一次生图任务里出的"阴天底片 → 同机位雨夜 → 同机位清晨"，所以逐像素对得上。字幕条里的字都是原生文本框。

### 一份完整的课堂 PPT：《戴珍珠耳环的少女》

<table>
<tr>
<td width="50%"><img src="assets/pearl-gallery.webp" alt="展厅开场"><br><b>展厅开场</b>：黑场 → 画框的灯亮起 → 标题和展签依次浮现</td>
<td width="50%"><img src="assets/pearl-morph.webp" alt="平滑切换推进"><br><b>推进画里</b>：平滑切换，展厅里的画放大成整页</td>
</tr>
<tr>
<td><img src="assets/pearl-light.webp" alt="光从左边来"><br><b>光从左边来</b>：软边暗层从左往右退开，再推近到脸</td>
<td><img src="assets/pearl-lapis.webp" alt="头巾到群青"><br><b>比黄金还贵的蓝</b>：推近头巾，叠化成青金石和颜料粉</td>
</tr>
<tr>
<td><img src="assets/pearl-pearl.webp" alt="珍珠特写"><br><b>一颗珍珠，两笔颜料</b>：极近特写 + 引线标注</td>
<td><img src="assets/pearl-delft.webp" alt="地图到风景"><br><b>代尔夫特</b>：老地图缓推，叠化成《代尔夫特一景》</td>
</tr>
<tr>
<td><img src="assets/pearl-works.webp" alt="作品墙"><br><b>三十几幅</b>：作品错落铺满，再只留下光从左边来的那几幅</td>
<td><img src="assets/pearl-ending.webp" alt="结尾"><br><b>结尾</b>：画慢慢暗下去，只剩珍珠那一点光</td>
</tr>
</table>

每一页的画面都是从"这一页要讲的那句话"里找出来的，找法写在 [`references/ideation.md`](references/ideation.md)。

## 它和"让 AI 加个动画"有什么不同

| 常见做法 | 这个 skill |
|---|---|
| 飞入、弹跳、旋转这类预设动画 | 实拍质感的场景 + 有来源的光 + 原生运镜，参考具体的电影镜头 |
| 生成图一眼"AI 感"：青橙调色、光晕、体积光 | 提示词写成"通讯社记者随手拍的新闻照片"，把电影调色点名排除；夜景分两步出 |
| 每张图单独生成，前后对不上 | 一次任务出整套同构图（底片 → 编辑变体 → 分割蒙版），逐像素对齐，可以叠化、做局部动作 |
| 嵌一段视频，改字要回去重渲 | 循环 GIF + PowerPoint 原生动画，文字全是可编辑的文本框 |
| 写完脚本就交付 | 导出放映视频、抽帧拼联系表、逐幕核对顺序、遮挡和字 |
| 一种手法用到底 | 手法库里记着"被否掉的做法和原因"，同一份稿不重复同一种画面 |

## 快速开始

**环境**：Windows + 微软 PowerPoint（流程靠 COM 组装）、Python 3.10+、ffmpeg。生图环节需要一个能"以图改图"的生图工具（作者用 Codex CLI 的内置生图），没有的话也可以用自己的照片或素材。

```bash
# 1. 装进 Claude Code 的 skills 目录
git clone https://github.com/Cennyk-learner/ppt-cinematic-animation ~/.claude/skills/ppt-cinematic-animation

# 2. Python 依赖
pip install numpy opencv-python-headless python-pptx pillow
```

字体：默认用开源字体 [Ma Shan Zheng](https://fonts.google.com/specimen/Ma+Shan+Zheng)（书法）、[思源宋体](https://github.com/adobe-fonts/source-han-serif)、[思源黑体](https://github.com/adobe-fonts/source-han-sans)，在 `scripts/ppt_tools.ps1` 开头可以换。

**先跑一遍自带的例子**，确认环境没问题（不需要生图工具）：

```powershell
cd ~/.claude/skills/ppt-cinematic-animation
python scripts/demo_assets.py D:\work\demo
pwsh -NoProfile -File scripts/build_page_example.ps1 -Work D:\work\demo     # 出 demo.pptx 和预览视频

python examples/lighthouse/render.py D:\work\lighthouse
pwsh -NoProfile -File examples/lighthouse/build.ps1 -Work D:\work\lighthouse  # 出上面那页灯塔
```

**然后直接跟 AI 说**：

> 这是我答辩 PPT 的第 8 页，三栏讲三个原因，太平淡了。帮我发散几个电影感的方向。

> 把这页做成动画：点一下进入一栏，演完自动回到总览。

> 这张底图 AI 感太强了，换成写实的，动画都保留。

skill 会先问清需求、提三四个类型不同的方向、把每一拍讲清楚，确认后再出样张、制作、导出核对。

## 里面有什么

```
SKILL.md                       入口：什么时候用、审美底线、协作顺序、硬约束、流程
references/
  taste.md                     审美与协作原则（每条都对应过一次整体返工）
  ideation.md                  怎么从内容里找画面、怎么写提案，附一个完整例子
  style-library.md             40+ 种做过的手法：开场转场 / 用光讲事 / 用时间讲事 / 对照 /
                               屏幕文件房间 / 平滑切换推近 / 图表文字 / 收尾 / 被否的做法
  pipeline.md                  生图 → 合成 → 把真实网页界面放进实景屏幕 → 组装 → 核对 → 多版本
  pitfalls.md                  PowerPoint、COM、平滑切换、生图、合成里踩过的坑
prompts/                       写实底图的提示词模板和例子
scripts/
  render_tools.py              循环动图、透明图层、画线、光束与光照揭示、被照亮的字、屏幕合成、联系表
  ppt_tools.ps1                COM 动画工具：一次点击一幕、路径、推近、拉远、雾转场、字幕条、导出视频
  capture_page.py              把单文件 HTML 界面无头跑起来、按步骤点击、逐帧截图
  cap_show.py                  真实放映时后台截屏
  demo_assets.py / build_page_example.ps1   不靠生图工具的最小例子
examples/lighthouse/           从生图提示词到成品的完整例子
```

## 几条最值钱的经验

摘自 [`pitfalls.md`](references/pitfalls.md) 和 [`taste.md`](references/taste.md)：

- **PPT 里的 GIF 从进入这一页就开始走，不等点击，也不等它出现。** 所以点击之后才发生的叙事过程不能做成一整条 GIF，要拆成逐状态的透明图层，用原生动画按顺序切。
- **"电影感"写进提示词，得到的是 AI 感。** 要真，就写成新闻照片，并点名排除调色、光晕、体积光。
- **震动、闪白、冲击模糊显得廉价。** 有分量的冲击来自运镜和光。
- **平滑切换的 COM 编号是 3954**，3953 是"折纸"。配对靠形状名（`!!` 开头），其余形状名必须全稿唯一，否则同名的字会在切换时乱飞。
- **导出视频会自动往下点**，每一幕只停到最后一个效果。所以加了 `Hold`，让预览视频里每一幕留够时间。
- **一幕只有一张图加一个循环动作，会显得空。** 每一幕至少要有两种不同的动作。

## 常见问题

**Mac 能用吗？** 组装和导出依赖 PowerPoint 的 COM 接口，只能在 Windows 上跑。手法库、审美原则和合成脚本在哪里都能看、能用。

**一定要用 Claude Code 吗？** 不一定。`SKILL.md` 和 `references/` 是普通的 Markdown，任何能读文件、跑命令的 agent 都能照着做。

**没有生图工具怎么办？** 用自己的照片、图库素材也行。合成和组装都不依赖生图；生图只是让"同一机位的几种状态"更容易对齐。

**能做整套 PPT 吗？** 这个 skill 专注于"把一页做出戏"。整套排版建议先用别的工具，再挑关键页交给它。

## 致谢与素材说明

- 《戴珍珠耳环的少女》《代尔夫特一景》等维米尔作品和代尔夫特老地图为公有领域，图像来自 Wikimedia Commons；展厅、颜料静物等其余画面为 AI 生成或作者自行拍摄。
- 灯塔例子的底图由 AI 生成，可随本仓库自由使用。
- 默认字体均为 SIL Open Font License。

## License

[MIT](LICENSE)
