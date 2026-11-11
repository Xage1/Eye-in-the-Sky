$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
foreach ($f in "lite_scheduler.py", "lite_main.py") {
    docker cp (Join-Path $root "backend\app\$f") "eyesky_api:/app/app/$f"
}
"How the API container normally starts:"
docker inspect eyesky_api --format "{{json .Config.Cmd}}"
docker exec eyesky_api sh -c "pkill -f 'port 8001' || true" | Out-Null
docker exec -d eyesky_api uvicorn app.lite_main:app --host 127.0.0.1 --port 8001 --workers 1
"Starting the lite server inside the container (about 40 s) ..."
$ok = $false
for ($i = 0; $i -lt 30 -and -not $ok; $i++) {
    Start-Sleep -Seconds 4
    docker exec eyesky_api python -c "import urllib.request;urllib.request.urlopen('http://127.0.0.1:8001/skyinfo/object/jupiter',timeout=5).read()" 2>$null
    if ($LASTEXITCODE -eq 0) { $ok = $true }
}
if (-not $ok) { throw "lite server did not answer; try: docker exec eyesky_api python -c ""import app.lite_main""" }
"lite server answers. Memory of each python process (kB):"
docker exec eyesky_api sh -c "grep -H VmRSS /proc/[0-9]*/status"
"Waiting 3 min for the background jobs to run ..."
Start-Sleep -Seconds 180
docker exec eyesky_api sh -c "grep -H VmRSS /proc/[0-9]*/status"
"done. Stop the test server with:  docker exec eyesky_api pkill -f 'port 8001'"
