# PowerPoint COM 动画小工具。版面按 960x540 pt（16:9）。
#
# 用法：在自己的组装脚本开头点源引入，然后一幕一幕往下写：
#     . "$PSScriptRoot\ppt_tools.ps1"
#     $deck = Open-Deck "<底稿.pptx>" "<素材目录>"
#     try { UseSlide 1 -ClearExcept @('标题形状名'); ...; Finish; Save-Deck "<成品.pptx>" } finally { Close-Deck }
# 完整的最小例子见 build_page_example.ps1。
#
# 写法约定：
#   Click            开始新的一幕（一次点击）。之后的效果都是"与上一动画同时"，用延时排先后。
#   Beat <秒>        同一次点击里的下一拍：之后所有延时都从点击后第 <秒> 算起。
#   Keep $shape      登记"这一层之后会被盖住"；Retire <秒> 让登记过的层在那时退场，免得一堆动图在底下空转。
#   Finish           一页写完时调用：把雾、暗带、文字、标题提到最上面。
#
# 注意：含中文的 .ps1 要存成带 BOM 的 UTF-8。PowerShell 变量不分大小写，自己的变量别叫 $gold、$white 这类名字
# （会和别处的常量撞车，报错位置还很远）；这里的内部状态都带 PT_ 前缀，常量带 C_ / FX_ / FONT_ 前缀。

$C_GOLD = 0x30BEFF; $C_WHITE = 0xFFFFFF; $C_RED = 0x3C3CF0; $C_GREY = 0xD8D8D8      # COM 的颜色是 0xBBGGRR
$FX_FADE = 10; $FX_WIPE = 22; $FX_APPEAR = 1; $FX_SCALE = 59
$WIPE_FROM_TOP = 1; $WIPE_FROM_RIGHT = 2; $WIPE_FROM_BOTTOM = 3; $WIPE_FROM_LEFT = 4
# 默认字体都是可免费商用的开源字体（Ma Shan Zheng、思源宋体、思源黑体），换字体在点源引入之后改这几个变量即可。
if (-not $FONT_BRUSH) { $FONT_BRUSH = 'Ma Shan Zheng' }
if (-not $FONT_SONG) { $FONT_SONG = '思源宋体 CN Heavy' }
if (-not $FONT_HEI) { $FONT_HEI = '思源黑体 CN Bold' }
if (-not $FONT_HEI_M) { $FONT_HEI_M = '思源黑体 CN Medium' }
# 页面切换效果。平滑切换（Morph）是 3954；3953 是"折纸"，会出碎片，别填错。
$TR_MORPH = 3954; $TR_FADE_SMOOTH = 3849; $TR_FADE_BLACK = 1793
$PT_inv = [cultureinfo]::InvariantCulture

function Open-Deck([string]$basePath, [string]$assetDir) {
  $script:PT_app = New-Object -ComObject PowerPoint.Application
  $script:PT_pres = $script:PT_app.Presentations.Open($basePath, $false, $false, $false)
  $script:PT_assets = $assetDir
  $script:PT_off = 0.0
  $script:PT_pend = New-Object System.Collections.ArrayList      # 排队的缩放
  $script:PT_txt = New-Object System.Collections.ArrayList       # 当前屏幕上的字
  $script:PT_allTxt = New-Object System.Collections.ArrayList    # 这一页所有要压在最上面的东西
  $script:PT_top = New-Object System.Collections.ArrayList       # 雾、暗带
  $script:PT_live = New-Object System.Collections.ArrayList      # 之后会被盖住、可以退场的层
  $script:PT_keep = @()
  return $script:PT_pres
}

function Close-Deck { if ($script:PT_pres) { $script:PT_pres.Saved = -1; $script:PT_pres.Close(); $script:PT_pres = $null } }

# 切到第 idx 页。给了 -ClearExcept 就删掉这一页上除列出名字以外的所有形状（名字用 COM 报的那个），并把背景设成黑色。
function UseSlide([int]$idx, [string[]]$ClearExcept = $null, [bool]$BlackBg = $true) {
  $script:PT_slide = $script:PT_pres.Slides.Item($idx); $script:PT_seq = $script:PT_slide.TimeLine.MainSequence
  $script:PT_txt.Clear(); $script:PT_allTxt.Clear(); $script:PT_top.Clear(); $script:PT_live.Clear(); $script:PT_pend.Clear(); $script:PT_off = 0.0
  if ($null -ne $ClearExcept) {
    $script:PT_keep = $ClearExcept
    $all = @($script:PT_slide.Shapes | ForEach-Object { $_.Name })
    foreach ($nm in $all) { if ($ClearExcept -notcontains $nm) { $script:PT_slide.Shapes.Item($nm).Delete() } }
    if ($BlackBg) { $script:PT_slide.FollowMasterBackground = 0; $script:PT_slide.Background.Fill.ForeColor.RGB = 0 }
  }
}

# ---------------- 基本效果 ----------------
function AddFx($shape, [int]$effect, [double]$delay, [double]$dur, [bool]$isExit, [bool]$onClick, [int]$dir = 0) {
  if ($null -eq $shape) { throw "null shape (line $($MyInvocation.ScriptLineNumber))" }
  if ($onClick) { FlushGrow }
  $e = $script:PT_seq.AddEffect($shape, $effect, 0, $(if ($onClick) { 1 } else { 2 }))
  if ($isExit) { $e.Exit = -1 }
  if ($dir -gt 0) { $e.EffectParameters.Direction = $dir }
  $e.Timing.TriggerDelayTime = [single]($delay + $script:PT_off); if ($dur -gt 0) { $e.Timing.Duration = [single]$dur }
}
function FIn($shape, [double]$delay, [double]$dur = 0.6) { AddFx $shape $FX_FADE $delay $dur $false $false }
function FOut($shape, [double]$delay, [double]$dur = 0.4) { AddFx $shape $FX_FADE $delay $dur $true $false }
function Cut($shape, [double]$delay) { AddFx $shape $FX_APPEAR $delay 0 $false $false }
# 擦除进入。同一位置叠两张只差一点的图，用它露出上面那张，看起来就是"那一点被画出来"。
function WipeIn($shape, [double]$delay, [double]$dur, [int]$dir) { AddFx $shape $FX_WIPE $delay $dur $false $false $dir }

# 一次点击：用一个画外的小方块承接点击，后面的效果全部"与上一动画同时"
function Click() {
  $d = $script:PT_slide.Shapes.AddShape(1, -40, -40, 6, 6); $d.Line.Visible = 0; $d.Fill.Transparency = 1; $d.Name = "拍-$($script:PT_seq.Count)"
  $script:PT_off = 0.0; AddFx $d $FX_APPEAR 0 0 $false $true
}
function Beat([double]$t) { $script:PT_off = $t }
# 这一幕停到点击后第 t 秒才算结束：用一个看不见的形状在那时"出现"。放映时观众本来就会停留，
# 但导出视频只停到最后一个效果，加它能让预览视频里每一幕留够看清的时间。
function Hold([double]$t) {
  $d = $script:PT_slide.Shapes.AddShape(1, -40, -40, 6, 6); $d.Line.Visible = 0; $d.Fill.Transparency = 1; $d.Name = "停-$($script:PT_seq.Count)"
  AddFx $d $FX_APPEAR $t 0 $false $false
}

# 直线移动 (dx, dy) pt
function AddPath($shape, [double]$dx, [double]$dy, [double]$delay, [double]$dur, [bool]$linear = $false) {
  $e = $script:PT_seq.AddEffect($shape, 0, 0, 2); $m = $e.Behaviors.Add(1)
  $m.MotionEffect.Path = "M 0 0 L {0} {1} E" -f ($dx / 960).ToString("0.#####", $PT_inv), ($dy / 540).ToString("0.#####", $PT_inv)
  $e.Timing.TriggerDelayTime = [single]($delay + $script:PT_off); $e.Timing.Duration = [single]$dur
  if ($linear) { $e.Timing.SmoothStart = 0; $e.Timing.SmoothEnd = 0 } else { $e.Timing.SmoothStart = -1; $e.Timing.SmoothEnd = -1 }
}
# 从偏移 (dx, dy) 处滑回原位。路径必须以显式的 M 开头，否则会从原位出发。
function SlideIn($shape, [double]$dx, [double]$dy, [double]$delay, [double]$dur) {
  $e = $script:PT_seq.AddEffect($shape, 0, 0, 2); $m = $e.Behaviors.Add(1)
  $m.MotionEffect.Path = "M {0} {1} L 0 0 E" -f ($dx / 960).ToString("0.#####", $PT_inv), ($dy / 540).ToString("0.#####", $PT_inv)
  $e.Timing.TriggerDelayTime = [single]($delay + $script:PT_off); $e.Timing.Duration = [single]$dur; $e.Timing.SmoothStart = 0; $e.Timing.SmoothEnd = -1
}
# 沿折线移动。$pts 是版面坐标的点列（形状中心依次经过），可以设重复次数，用来做"沿路线流动的光点"。
function PathAlong($shape, $pts, [double]$delay, [double]$dur, [int]$repeat = 1) {
  $p = "M 0 0"
  for ($k = 1; $k -lt $pts.Count; $k++) { $p += " L {0} {1}" -f (($pts[$k][0] - $pts[0][0]) / 960).ToString("0.#####", $PT_inv), (($pts[$k][1] - $pts[0][1]) / 540).ToString("0.#####", $PT_inv) }
  $e = $script:PT_seq.AddEffect($shape, 0, 0, 2); $m = $e.Behaviors.Add(1); $m.MotionEffect.Path = $p + " E"
  $e.Timing.TriggerDelayTime = [single]($delay + $script:PT_off); $e.Timing.Duration = [single]$dur; $e.Timing.SmoothStart = 0; $e.Timing.SmoothEnd = 0
  if ($repeat -gt 1) { $e.Timing.RepeatCount = $repeat }
}

# 沿一段三次贝塞尔曲线移动，让光斑、光点不规则地游走。$o 是形状中心的起点，$a 起点、$c1 $c2 控制点、$b 终点，都是版面坐标。
function CurvePath($shape, $o, $a, $c1, $c2, $b, [double]$delay, [double]$dur) {
  $e = $script:PT_seq.AddEffect($shape, 0, 0, 2); $m = $e.Behaviors.Add(1)
  $v = @((($a[0] - $o[0]) / 960), (($a[1] - $o[1]) / 540), (($c1[0] - $o[0]) / 960), (($c1[1] - $o[1]) / 540), (($c2[0] - $o[0]) / 960), (($c2[1] - $o[1]) / 540), (($b[0] - $o[0]) / 960), (($b[1] - $o[1]) / 540)) | ForEach-Object { ([double]$_).ToString("0.#####", $PT_inv) }
  $m.MotionEffect.Path = "M {0} {1} C {2} {3} {4} {5} {6} {7}" -f $v
  $e.Timing.TriggerDelayTime = [single]($delay + $script:PT_off); $e.Timing.Duration = [single]$dur; $e.Timing.SmoothStart = -1; $e.Timing.SmoothEnd = -1
}
# 镜头推近：形状绕版面上的焦点 (fx, fy) 放大 k 倍（缩放 + 同步位移，焦点在画面里不动）。只用在满幅的层上。
function PushIn($shape, [double]$k, [double]$fx, [double]$fy, [double]$t, [double]$dur) {
  $cx = $shape.Left + $shape.Width / 2; $cy = $shape.Top + $shape.Height / 2
  $e = $script:PT_seq.AddEffect($shape, $FX_SCALE, 0, 2); $e.Behaviors.Item(1).ScaleEffect.ByX = [single](100 * $k); $e.Behaviors.Item(1).ScaleEffect.ByY = [single](100 * $k)
  $e.Timing.TriggerDelayTime = [single]($t + $script:PT_off); $e.Timing.Duration = [single]$dur; $e.Timing.SmoothStart = -1; $e.Timing.SmoothEnd = 0
  $e = $script:PT_seq.AddEffect($shape, 0, 0, 2); $m = $e.Behaviors.Add(1)
  $m.MotionEffect.Path = "M 0 0 L {0} {1} E" -f ((($k - 1) * ($cx - $fx)) / 960).ToString("0.#####", $PT_inv), ((($k - 1) * ($cy - $fy)) / 540).ToString("0.#####", $PT_inv)
  $e.Timing.TriggerDelayTime = [single]($t + $script:PT_off); $e.Timing.Duration = [single]$dur; $e.Timing.SmoothStart = -1; $e.Timing.SmoothEnd = 0
}
# 设当前页的切换效果。平滑切换要配合"两页同名形状"，规则见 pitfalls.md。
function SetTransition([int]$effect, [double]$dur) { $t = $script:PT_slide.SlideShowTransition; $t.EntryEffect = $effect; $t.Duration = [single]$dur }

# 缓慢放大（镜头缓推）。缩放效果排队，到下一次点击或 Finish 时再写入。
function AddGrow($shape, [double]$pct, [double]$delay, [double]$dur) { [void]$script:PT_pend.Add(@($shape, $pct, ($delay + $script:PT_off), $dur)) }
function FlushGrow {
  foreach ($g in @($script:PT_pend)) {
    $e = $script:PT_seq.AddEffect($g[0], $FX_SCALE, 0, 2)
    $e.Behaviors.Item(1).ScaleEffect.ByX = [single]$g[1]; $e.Behaviors.Item(1).ScaleEffect.ByY = [single]$g[1]
    $e.Timing.TriggerDelayTime = [single]$g[2]; $e.Timing.Duration = [single]$g[3]; $e.Timing.SmoothStart = 0; $e.Timing.SmoothEnd = -1
  }
  $script:PT_pend.Clear()
}
# 立即缩放到 pct%（以形状中心为准），用来做"一大团收紧成一小块"
function ScaleTo($shape, [double]$pct, [double]$delay, [double]$dur) {
  $e = $script:PT_seq.AddEffect($shape, $FX_SCALE, 0, 2); $e.Behaviors.Item(1).ScaleEffect.ByX = [single]$pct; $e.Behaviors.Item(1).ScaleEffect.ByY = [single]$pct
  $e.Timing.TriggerDelayTime = [single]($delay + $script:PT_off); $e.Timing.Duration = [single]$dur; $e.Timing.SmoothStart = -1; $e.Timing.SmoothEnd = -1
}
# 镜头拉远：$next 里的图层从放大 k 倍（焦点 fx, fy）缩回满幅，$prev 里的同时淡出。图层都按满幅 960x540 放。
function ZoomOut($prev, $next, [double]$k, [double]$fx, [double]$fy, [double]$t, [double]$dur) {
  foreach ($x in $next) {
    $x.Width = [single](960 * $k); $x.Height = [single](540 * $k); $x.Left = [single](480 - $k * $fx); $x.Top = [single](270 - $k * $fy)
    FIn $x $t ($dur * 0.45)
    $e = $script:PT_seq.AddEffect($x, $FX_SCALE, 0, 2); $e.Behaviors.Item(1).ScaleEffect.ByX = [single](100 / $k); $e.Behaviors.Item(1).ScaleEffect.ByY = [single](100 / $k)
    $e.Timing.TriggerDelayTime = [single]($t + $script:PT_off); $e.Timing.Duration = [single]$dur; $e.Timing.SmoothStart = 0; $e.Timing.SmoothEnd = -1
    $e = $script:PT_seq.AddEffect($x, 0, 0, 2); $m = $e.Behaviors.Add(1)
    $m.MotionEffect.Path = "M 0 0 L {0} {1} E" -f (($k * ($fx - 480)) / 960).ToString("0.#####", $PT_inv), (($k * ($fy - 270)) / 540).ToString("0.#####", $PT_inv)
    $e.Timing.TriggerDelayTime = [single]($t + $script:PT_off); $e.Timing.Duration = [single]$dur; $e.Timing.SmoothStart = 0; $e.Timing.SmoothEnd = -1
  }
  foreach ($x in $prev) { FOut $x ($t + $dur * 0.25) ($dur * 0.5) }
}

# ---------------- 图层 ----------------
function AddPic($file, $nm, [double]$x = 0, [double]$y = 0, [double]$w = 960, [double]$h = 540) {
  $p = $script:PT_slide.Shapes.AddPicture((Join-Path $script:PT_assets $file), $false, $true, $x, $y, $w, $h); $p.Name = $nm; return $p
}
# $p 是 [x, y, w, h]（合成脚本裁透明图层时记下来的位置）
function PicAt($file, $nm, $p) { return (AddPic $file $nm $p[0] $p[1] $p[2] $p[3]) }
function AddBlack($nm, [double]$tr) {
  $r = $script:PT_slide.Shapes.AddShape(1, -2, -2, 964, 544); $r.Name = $nm; $r.Line.Visible = 0
  $r.Fill.ForeColor.RGB = 0; $r.Fill.Transparency = [single]$tr; return $r
}
# 一张纸：微微转一点角度，带投影。用在桌面上的文件、占位图。
function Paper($shape, [double]$rot, [bool]$shadow = $true) {
  $shape.Rotation = [single]$rot
  if ($shadow) { $sh = $shape.Shadow; $sh.Visible = -1; $sh.Blur = 16; $sh.OffsetX = 4; $sh.OffsetY = 7; $sh.ForeColor.RGB = 0; $sh.Transparency = 0.4 }
}
# 让一个图层在 Finish 时压到暗带上面（比如伸进底部暗带的文件）。记得在下一幕的雾扫过来之前让它退场。
function OnTop($shape) { [void]$script:PT_allTxt.Add($shape) }
function Keep($shape) { [void]$script:PT_live.Add($shape) }
function Retire([double]$delay) { foreach ($x in @($script:PT_live)) { AddFx $x $FX_APPEAR $delay 0 $true $false }; $script:PT_live.Clear() }
# 雾从左向右漫过画面的转场。素材目录里要有 fog.png。
function FogCut($nm) {
  $fg = AddPic "fog.png" $nm -1560 -90 1500 720
  FIn $fg 0 0.15; AddPath $fg 2560 0 0 1.0; [void]$script:PT_top.Add($fg)
}

# ---------------- 文字（都是原生文本框，之后可以直接改） ----------------
function AddWord($text, [double]$x, [double]$y, [double]$size, $font, [int]$rgb, $nm) {
  $tb = $script:PT_slide.Shapes.AddTextbox(1, $x, $y, 520, $size * 1.5); $tb.Name = $nm; $tb.TextFrame2.WordWrap = 0
  $rng = $tb.TextFrame2.TextRange; $rng.Text = $text
  $rng.Font.NameFarEast = $font; $rng.Font.Name = $font; $rng.Font.Size = [single]$size; $rng.Font.Fill.ForeColor.RGB = $rgb
  $sh = $rng.Font.Shadow; $sh.Visible = -1; $sh.Blur = 9; $sh.OffsetX = 0; $sh.OffsetY = 1; $sh.ForeColor.RGB = 0; $sh.Transparency = 0.05
  [void]$script:PT_allTxt.Add($tb); return $tb
}
# 底部字幕条版式：暗带 + 左下书法小标题和金色竖线 + 右侧宋体疏排关键词（两行，row 0 / 1）+ 说明小字
function Band() { $b = AddPic "band.png" "底部暗带" -2 0 964 542; [void]$script:PT_top.Add($b); return $b }
function BigC($text, [double]$delay, [double]$x = 48) {
  $b = AddWord $text $x 418 76 $FONT_BRUSH $C_WHITE "结论-$text-$($script:PT_seq.Count)"
  $ln = $script:PT_slide.Shapes.AddShape(1, $x + 238, 449, 1.5, 54); $ln.Fill.ForeColor.RGB = $C_GOLD; $ln.Line.Visible = 0; $ln.Name = "结论线-$text-$($script:PT_seq.Count)"
  [void]$script:PT_allTxt.Add($ln)
  WipeIn $b $delay 0.7 $WIPE_FROM_LEFT; WipeIn $ln ($delay + 0.5) 0.4 $WIPE_FROM_BOTTOM
  [void]$script:PT_txt.Add($b); [void]$script:PT_txt.Add($ln); return @($b, $ln)
}
function KeyC($text, [double]$delay, [int]$row = 0, [double]$x = 256) {
  $k = AddWord $text ($x + 48) (444 + 34 * $row) 24 $FONT_SONG $C_WHITE "词-$text-$($script:PT_seq.Count)"
  $k.TextFrame2.TextRange.Font.Bold = 0; $k.TextFrame2.TextRange.Font.Spacing = 4
  WipeIn $k $delay 0.5 $WIPE_FROM_LEFT; [void]$script:PT_txt.Add($k); return $k
}
function NoteC($text, [double]$x, [double]$y, [double]$delay, [double]$size = 14, [int]$rgb = 0xD8D8D8) {
  $t = AddWord $text $x $y $size $FONT_HEI_M $rgb "标-$text-$($script:PT_seq.Count)"; $t.TextFrame2.TextRange.Font.Bold = 0; $t.TextFrame2.TextRange.Font.Spacing = 1.5
  FIn $t $delay 0.35; [void]$script:PT_txt.Add($t); return $t
}
# 小签：一段色条 + 黑体词
function Tag($text, [double]$x, [double]$y, [int]$rgb, [double]$delay) {
  $bar = $script:PT_slide.Shapes.AddShape(1, $x, $y + 5, 4, 24); $bar.Fill.ForeColor.RGB = $rgb; $bar.Line.Visible = 0; $bar.Name = "标-签条-$text"
  $t = AddWord $text ($x + 8) $y 22 $FONT_HEI $C_WHITE "标-签-$text"; $t.TextFrame2.TextRange.Font.Bold = -1; $t.TextFrame2.TextRange.Font.Spacing = 5
  [void]$script:PT_allTxt.Add($bar); FIn $bar $delay 0.3; FIn $t $delay 0.3; [void]$script:PT_txt.Add($bar); [void]$script:PT_txt.Add($t)
}
# 退场：全部 / 只退关键词和说明 / 只退说明
function ClearText([double]$delay = 0) { foreach ($x in @($script:PT_txt)) { FOut $x $delay 0.3 }; $script:PT_txt.Clear() }
function ClearWords([double]$delay = 0) {
  foreach ($x in @($script:PT_txt)) { if ($x.Name -like '词-*' -or $x.Name -like '标-*') { FOut $x $delay 0.25; $script:PT_txt.Remove($x) } }
}
function ClearKeys([double]$delay = 0) {
  foreach ($x in @($script:PT_txt)) { if ($x.Name -like '标-*') { FOut $x $delay 0.3; $script:PT_txt.Remove($x) } }
}
# 手动让一段字退场，并从登记里拿掉。已经隐藏的形状再做一次退场，会先闪现一下，所以别退两次。
function Drop($t, [double]$delay) { FOut $t $delay 0.3; $script:PT_txt.Remove($t) }

# ---------------- 收尾与导出 ----------------
function Finish() {
  FlushGrow
  foreach ($x in @($script:PT_top)) { $x.ZOrder(0) }
  foreach ($x in @($script:PT_allTxt)) { try { $x.ZOrder(0) } catch {} }
  foreach ($nm in $script:PT_keep) { try { $script:PT_slide.Shapes.Item($nm).ZOrder(0) } catch {} }
}
function Save-Deck([string]$dst) {
  foreach ($s in $script:PT_pres.Slides) { $s.SlideShowTransition.AdvanceOnTime = 0; $s.SlideShowTransition.AdvanceOnClick = -1 }
  if (Test-Path $dst) { Remove-Item $dst }      # 文件正被 PowerPoint 开着时会失败：换个名字存
  $script:PT_pres.SaveAs($dst)
  "saved $(Split-Path $dst -Leaf)  slides=$($script:PT_pres.Slides.Count)  MB=$([math]::Round((Get-Item $dst).Length/1MB,1))"
}
# 导出放映视频，用来抽帧核对顺序、时机和遮挡。它会自动往下点，所以每一幕在视频里只停到最后一个效果结束。
function Export-Video([string]$mp4, [int]$height = 720) {
  Remove-Item $mp4 -ErrorAction SilentlyContinue
  $script:PT_pres.CreateVideo($mp4, $true, 3, $height, 30, 85)
  $waited = 0; while ($script:PT_pres.CreateVideoStatus -in 1, 2 -and $waited -lt 580) { Start-Sleep 5; $waited += 5 }
  "video status=$($script:PT_pres.CreateVideoStatus) after ${waited}s"
}
