# scripts/fetch_hyg.ps1 - download the HYG star database (v4.2) used for real star facts.
# Not committed to git. Licence CC BY-SA 4.0, credit: astronexus.com/hyg
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"
$dir = Join-Path $PSScriptRoot "..\backend\app\data\hyg"
New-Item -ItemType Directory -Force $dir | Out-Null
$gz = Join-Path $dir "hygdata_v42.csv.gz"
$csv = Join-Path $dir "hygdata_v42.csv"
Invoke-WebRequest -Uri "https://astronexus.com/downloads/catalogs/hygdata_v42.csv.gz" -OutFile $gz -UseBasicParsing -Headers @{ "User-Agent" = "Mozilla/5.0 EyeSky/0.1" }
$in = [System.IO.File]::OpenRead($gz)
$gs = New-Object System.IO.Compression.GzipStream($in, [System.IO.Compression.CompressionMode]::Decompress)
$out = [System.IO.File]::Create($csv)
$gs.CopyTo($out)
$out.Close(); $gs.Close(); $in.Close()
Remove-Item $gz
"HYG saved: {0}  ({1} MB)" -f $csv, [math]::Round((Get-Item $csv).Length / 1MB, 1)
"header: " + (Get-Content $csv -TotalCount 1)
"rows:   " + ((Get-Content $csv | Measure-Object -Line).Lines - 1)
