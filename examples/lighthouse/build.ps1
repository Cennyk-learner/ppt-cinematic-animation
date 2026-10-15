# 灯塔演示页：一页三幕。先跑 render.py 出素材，再跑这个脚本组装并导出预览视频：
#     python render.py D:\work\lighthouse
#     pwsh -NoProfile -File build.ps1 -Work D:\work\lighthouse
# 成品 lighthouse.pptx 和 lighthouse.mp4 在 <Work>\out\ 里。
#
#   进页   雨夜。灯塔的光束一圈圈扫过海面，扫过天上的"一束光"时字被照亮（循环动图）；字幕条出"守望"
#   点 1   镜头缓缓推向灯笼（原生缩放 + 位移，焦点不动），关键词换掉
#   点 2   雾从左漫过，天亮了；一条金色航线从渔船画到灯塔脚下，一个光点沿航线走
param([string]$Work = $PSScriptRoot, [string]$Out = "lighthouse.pptx", [switch]$NoVideo)
$ErrorActionPreference = "Stop"
. "$PSScriptRoot\..\..\scripts\ppt_tools.ps1"
$assets = Join-Path $Work "out"
$pos = Get-Content -Raw (Join-Path $assets "pos.json") -Encoding UTF8 | ConvertFrom-Json
$deck = Open-Deck (Join-Path $assets "base.pptx") $assets
try {
  UseSlide 1 -ClearExcept @()
  SetTransition $TR_FADE_BLACK 1.0

  # ---- 进页：雨夜 ----
  [void](Band)
  $night = AddPic "night.gif" "第一幕-雨夜灯塔"
  [void](BigC '守望' 1.0)
  [void](KeyC '风暴夜' 1.8 0); [void](KeyC '灯塔不灭' 2.4 1)
  Keep $night
  Hold 6.5

  # ---- 点 1：推近灯笼 ----
  Click; ClearWords 0
  PushIn $night 1.7 702.5 160.5 0.1 4.5
  [void](KeyC '每一次闪光' 1.8 0); [void](KeyC '都在说：这里有岸' 2.6 1)
  Hold 6.0

  # ---- 点 2：雾过，天亮，归航 ----
  Click; FogCut "雾-1"; ClearText 0
  $dawn = AddPic "dawn.gif" "第三幕-清晨"; FIn $dawn 0.3 0.7
  Retire 1.1
  $route = PicAt "route.png" "第三幕-航线" $pos.route; WipeIn $route 1.6 2.6 $WIPE_FROM_LEFT
  $p0 = $pos.route_pts[0]
  $dot = AddPic "dot.png" "第三幕-光点" ($p0[0] - 7) ($p0[1] - 7) 14 14
  FIn $dot 1.6 0.3; PathAlong $dot $pos.route_pts 1.6 2.6
  OnTop $dot
  [void](BigC '归航' 1.2)
  [void](KeyC '天亮了' 2.0 0); [void](KeyC '船回来了' 2.6 1)
  Hold 7.5

  Finish
  Save-Deck (Join-Path $assets $Out)
  if (-not $NoVideo) { Export-Video (Join-Path $assets "lighthouse.mp4") 1080 }
}
finally { Close-Deck }
