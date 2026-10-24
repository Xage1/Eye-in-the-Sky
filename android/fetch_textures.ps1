# android/fetch_textures.ps1 - download the planet / Moon / Sun textures into the app's assets.
# Textures are not committed to git; run this once after cloning. Credits are in android\CREDITS.md.
$ErrorActionPreference = "Continue"
$ProgressPreference = "SilentlyContinue"
Add-Type -AssemblyName System.Drawing

$dst = Join-Path $PSScriptRoot "app\src\main\assets\textures"
$tmp = Join-Path $env:TEMP "eyesky_tex"
New-Item -ItemType Directory -Force $dst, $tmp | Out-Null
$ua = @{ "User-Agent" = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) EyeSky/0.1" }

function Save-Jpeg([string]$src, [string]$out, [int]$maxW) {
  $img = [System.Drawing.Image]::FromFile($src)
  try {
    $w = $img.Width; $h = $img.Height
    if ($w -gt $maxW) { $h = [int]($h * $maxW / $w); $w = $maxW }
    $bmp = New-Object System.Drawing.Bitmap($w, $h, [System.Drawing.Imaging.PixelFormat]::Format24bppRgb)
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
    $g.DrawImage($img, 0, 0, $w, $h)
    $g.Dispose()
    $codec = [System.Drawing.Imaging.ImageCodecInfo]::GetImageEncoders() | Where-Object { $_.MimeType -eq "image/jpeg" }
    $p = New-Object System.Drawing.Imaging.EncoderParameters(1)
    $p.Param[0] = New-Object System.Drawing.Imaging.EncoderParameter([System.Drawing.Imaging.Encoder]::Quality, [long]92)
    $bmp.Save($out, $codec, $p)
    $bmp.Dispose()
    return ("{0}x{1}" -f $w, $h)
  } finally { $img.Dispose() }
}

$sss = "https://www.solarsystemscope.com/textures/download"
$nasa = "https://svs.gsfc.nasa.gov/vis/a000000/a004700/a004720"
# name, then candidate URLs best-first (first one that downloads and decodes wins)
$items = @(
  @{ n = "moon";        u = @("$nasa/lroc_color_16bit_srgb_4k.tif", "$nasa/lroc_color_2k.jpg") },
  @{ n = "moon_height"; u = @("$nasa/ldem_3_8bit.jpg") },
  @{ n = "sun";         u = @("$sss/8k_sun.jpg", "$sss/2k_sun.jpg") },
  @{ n = "mercury";     u = @("$sss/8k_mercury.jpg", "$sss/2k_mercury.jpg") },
  @{ n = "venus";       u = @("$sss/4k_venus_atmosphere.jpg", "$sss/2k_venus_atmosphere.jpg") },
  @{ n = "earth";       u = @("$sss/8k_earth_daymap.jpg", "$sss/2k_earth_daymap.jpg") },
  @{ n = "mars";        u = @("$sss/8k_mars.jpg", "$sss/2k_mars.jpg") },
  @{ n = "jupiter";     u = @("$sss/8k_jupiter.jpg", "$sss/2k_jupiter.jpg") },
  @{ n = "saturn";      u = @("$sss/8k_saturn.jpg", "$sss/2k_saturn.jpg") },
  @{ n = "uranus";      u = @("$sss/2k_uranus.jpg") },
  @{ n = "neptune";     u = @("$sss/2k_neptune.jpg") },
  @{ n = "milkyway";    u = @("$sss/8k_stars_milky_way.jpg", "$sss/2k_stars_milky_way.jpg") }
)

$rows = @()
foreach ($it in $items) {
  $out = Join-Path $dst ($it.n + ".jpg")
  $done = $false
  foreach ($u in $it.u) {
    $ext = [System.IO.Path]::GetExtension($u)
    $file = Join-Path $tmp ($it.n + $ext)
    try {
      Invoke-WebRequest -Uri $u -OutFile $file -UseBasicParsing -Headers $ua -TimeoutSec 600
      $size = Save-Jpeg $file $out 4096
      $kb = [int]((Get-Item $out).Length / 1KB)
      $rows += [pscustomobject]@{ Texture = $it.n; Size = $size; KB = $kb; Source = ($u -replace "https://", "") }
      $done = $true
      break
    } catch {
      $code = ""
      if ($_.Exception.Response) { $code = [int]$_.Exception.Response.StatusCode }
      Write-Host ("  {0}: {1} failed {2} {3}" -f $it.n, ($u -replace "https://", ""), $code, $_.Exception.Message.Split("`n")[0])
    }
  }
  if (-not $done) { $rows += [pscustomobject]@{ Texture = $it.n; Size = "MISSING"; KB = 0; Source = "none worked" } }
}

# Saturn's rings need transparency, so the PNG is copied as it is
$ringOut = Join-Path $dst "saturn_ring.png"
foreach ($u in @("$sss/2k_saturn_ring_alpha.png")) {
  try {
    Invoke-WebRequest -Uri $u -OutFile $ringOut -UseBasicParsing -Headers $ua -TimeoutSec 300
    $rows += [pscustomobject]@{ Texture = "saturn_ring"; Size = "png"; KB = [int]((Get-Item $ringOut).Length / 1KB); Source = ($u -replace "https://", "") }
  } catch {
    $rows += [pscustomobject]@{ Texture = "saturn_ring"; Size = "MISSING"; KB = 0; Source = "failed" }
  }
}

Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue
$rows | Format-Table -AutoSize
$total = (Get-ChildItem $dst -File | Measure-Object Length -Sum).Sum
"total in assets: {0} MB" -f [math]::Round($total / 1MB, 1)
