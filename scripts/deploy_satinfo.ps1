$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$sky = Join-Path $root "backend\app\routers\skyinfo.py"
$snip = Join-Path $root "backend\app\routers\_sat_routes.txt"
if (-not (Select-String -Path $sky -Pattern "satinfo" -Quiet)) {
    Add-Content -Path $sky -Value (Get-Content -Raw $snip)
    "routes appended to skyinfo.py"
} else { "routes already in skyinfo.py" }
docker cp (Join-Path $root "backend\app\services\sat_info.py") eyesky_api:/app/app/services/sat_info.py
docker cp $sky eyesky_api:/app/app/routers/skyinfo.py
docker restart eyesky_api | Out-Null
"waiting for the API..."
$ok = $false
for ($i = 0; $i -lt 30 -and -not $ok; $i++) {
    Start-Sleep -Seconds 4
    try { Invoke-RestMethod "http://localhost:8000/skyinfo/object/jupiter" | Out-Null; $ok = $true } catch { }
}
if (-not $ok) { throw "API did not come back; run: docker logs eyesky_api --tail 40" }
try {
    $r = Invoke-RestMethod "http://localhost:8000/skyinfo/satinfo?name=ISS&lat=-1.2921&lon=36.8219"
    $r.sections | ForEach-Object { $_.title; $_.rows | Select-Object -First 6 | ForEach-Object { "  {0}: {1}" -f $_[0], $_[1] } }
    "passes found: " + $r.passes.Count
} catch { "ISS lookup failed: $($_.Exception.Message)"; "Check: docker logs eyesky_api --tail 40" }
