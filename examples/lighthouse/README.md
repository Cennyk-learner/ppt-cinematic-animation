# 例子：风暴夜的灯塔

一页三幕，从生图到成品的完整流程。效果见仓库首页的 `assets/lighthouse.webp`。

| 文件 | 作用 |
|---|---|
| `prompt_gen.txt` | 一次生图任务的完整提示词：阴天底片 → 同机位雨夜 → 同机位清晨。原样跑通过 |
| `gen/*.jpg` | 这次生成的三张底图，没有生图工具也能直接跑后面的步骤 |
| `render.py` | 合成：雨夜光束扫动的循环动图（光束、雨、灯笼眩光、被照亮的字）、清晨海面碎光的循环动图、金色航线和光点、字幕暗带、雾 |
| `build.ps1` | COM 组装：进页自动播第一幕，点 1 推近灯笼，点 2 雾转场到清晨并画出航线；保存 `.pptx` 并导出预览视频 |

```powershell
python render.py D:\work\lighthouse
pwsh -NoProfile -File build.ps1 -Work D:\work\lighthouse
```

想重新生图：在一个空目录里放好 `prompt_gen.txt`，执行 `codex exec --skip-git-repo-check -s workspace-write - < prompt_gen.txt`，生成的 PNG 在 `gen/` 里。`render.py` 读的是 `gen/night.jpg` 和 `gen/dawn.jpg`，换成新图时改一下文件名，再按新图重新找灯笼的位置（`LX, LY`）。

这个例子用到的手法：光束巡扫并照亮字（`style-library.md` 第 1 节）、唯一的光源、夜到晨、镜头推向一点、雾转场、航拍图上画路线、底部字幕条。
