# 最小的组装例子：一页两幕。先跑 demo_assets.py 生成素材，再跑这个脚本：
#     python demo_assets.py D:\work\demo
#     pwsh -NoProfile -File build_page_example.ps1 -Work D:\work\demo
# 成品 demo.pptx 和导出的 _demo.mp4 都在 <Work>\out\ 里。正式的页面照这个骨架写，每一幕的内容自己设计。
param([string]$Work = $PSScriptRoot, [string]$Out = "demo.pptx", [switch]$NoVideo)
$ErrorActionPreference = "Stop"
. "$PSScriptRoot\ppt_tools.ps1"
$assets = Join-Path $Work "out"
$pos = Get-Content -Raw (Join-Path $assets "pos.json") -Encoding UTF8 | ConvertFrom-Json
$deck = Open-Deck (Join-Path $assets "base.pptx") $assets
try {
  UseSlide 1 -ClearExcept @()          # 正式页面里把要保留的标题形状名写进来，其余清空

  # ---- 第一幕：进页就在的循环动图。没有 Click，所以进页自动播 ----
  [void](Band)
  $a = AddPic "scene_a.gif" "第一幕-雨夜"
  [void](BigC '小标题' 0.8); [void](KeyC '关键词一' 1.6 0); [void](KeyC '关键词二' 2.4 1)
  AddGrow $a 104 0 6
  Keep $a

  # ---- 第二幕：点一下。雾扫过去，换底图，线从左到右画出来，一根红色虚线从上往下落 ----
  Click; FogCut "雾-1"; ClearWords 0
  $b = AddPic "scene_b.png" "第二幕-底图"; FIn $b 0.35 0.6
  Retire 1.0; Keep $b
  $ln = PicAt "line.png" "第二幕-曲线" $pos.line; WipeIn $ln 1.2 1.8 $WIPE_FROM_LEFT
  $mk = PicAt "mark.png" "第二幕-标记" $pos.mark; WipeIn $mk 2.6 0.8 $WIPE_FROM_TOP
  [void](KeyC '换了一组词' 1.4 0); [void](NoteC '说明小字' 306 484 2.2 15)
  # 同一次点击里的下一拍
  Beat 4.6
  ClearWords 0
  [void](Tag '小签' 640 96 $C_GOLD 0.3)

  Finish
  Save-Deck (Join-Path $assets $Out)
  if (-not $NoVideo) { Export-Video (Join-Path $assets "_demo.mp4") }
}
finally { Close-Deck }
