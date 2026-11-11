$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$out = Join-Path (Split-Path -Parent $root) "wispbyte_bundle"
if (Test-Path $out) { Remove-Item -Recurse -Force $out }
New-Item -ItemType Directory -Path $out | Out-Null

"1/5 copying the backend code ..."
robocopy (Join-Path $root "backend\app") (Join-Path $out "app") /E /XD __pycache__ hyg tests .pytest_cache /XF *.pyc /NFL /NDL /NJH /NJS /NP | Out-Null

"2/5 trimming the star catalogue to the bright stars the app uses (about a minute) ..."
$csv = Join-Path $root "backend\app\data\hyg\hygdata_v42.csv"
if (-not (Test-Path $csv)) { throw "HYG csv missing: run scripts\fetch_hyg.ps1 first" }
New-Item -ItemType Directory -Path (Join-Path $out "app\data\hyg") -Force | Out-Null
Import-Csv $csv | Where-Object { $_.hr -ne "" } | Export-Csv (Join-Path $out "app\data\hyg\hygdata_v42.csv") -NoTypeInformation -Encoding UTF8

"3/5 writing requirements.txt from your running API container ..."
$req = docker exec eyesky_api pip freeze | Where-Object { $_ -and ($_ -notmatch " @ ") -and ($_ -notmatch "^(pytest|watchfiles|black|flake8)") }
$req = @($req) + "pyngrok"
[System.IO.File]::WriteAllLines((Join-Path $out "requirements.txt"), [string[]]$req)

"4/5 adding main.py ..."
Copy-Item (Join-Path $PSScriptRoot "wispbyte_main.py") (Join-Path $out "main.py")

"5/5 zipping ..."
$zip = "$out.zip"
if (Test-Path $zip) { Remove-Item -Force $zip }
Compress-Archive -Path (Join-Path $out "*") -DestinationPath $zip
$mb = [math]::Round(((Get-ChildItem $out -Recurse -File | Measure-Object Length -Sum).Sum) / 1MB, 1)
"Bundle folder: $out  ($mb MB of files, $($req.Count) packages)"
"Zip to upload: $zip"
"Next: powershell -ExecutionPolicy Bypass -File .\scripts\make_wispbyte_env.ps1"
