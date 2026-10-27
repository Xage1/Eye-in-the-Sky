$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$sky = Join-Path $root "backend\app\routers\skyinfo.py"
$snip = Join-Path $root "backend\app\routers\_object_routes.txt"
$csv = Join-Path $root "backend\app\data\hyg\hygdata_v42.csv"
if (-not (Test-Path $csv)) { throw "HYG csv missing: run scripts\fetch_hyg.ps1 first" }
if (-not (Select-String -Path $sky -Pattern "object_info" -Quiet)) {
    Add-Content -Path $sky -Value (Get-Content -Raw $snip)
    "routes appended to skyinfo.py"
} else { "routes already in skyinfo.py" }
docker exec eyesky_api mkdir -p /app/app/data/hyg
docker cp (Join-Path $root "backend\app\services\object_info.py") eyesky_api:/app/app/services/object_info.py
docker cp $sky eyesky_api:/app/app/routers/skyinfo.py
docker cp $csv eyesky_api:/app/app/data/hyg/hygdata_v42.csv
docker restart eyesky_api | Out-Null
"waiting for the API..."
$ok = $false
for ($i = 0; $i -lt 30 -and -not $ok; $i++) {
    Start-Sleep -Seconds 4
    try { Invoke-RestMethod "http://localhost:8000/skyinfo/object/jupiter" | Out-Null; $ok = $true } catch { }
}
if (-not $ok) { throw "API did not come back; run: docker logs eyesky_api --tail 40" }
"--- Jupiter"
(Invoke-RestMethod "http://localhost:8000/skyinfo/object/jupiter").sections[0].rows | ForEach-Object { "{0}: {1}" -f $_[0], $_[1] }
"--- Sirius"
(Invoke-RestMethod "http://localhost:8000/skyinfo/object/star/2491").sections | ForEach-Object { $_.title; $_.rows | ForEach-Object { "  {0}: {1}" -f $_[0], $_[1] } }
