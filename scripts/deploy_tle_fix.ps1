$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$f = Join-Path $root "backend\app\tasks\tle_tasks.py"
foreach ($c in "eyesky_worker", "eyesky_beat", "eyesky_api") {
    docker cp $f "${c}:/app/app/tasks/tle_tasks.py"
}
docker restart eyesky_worker eyesky_beat | Out-Null
Start-Sleep -Seconds 15
"--- triggering a normal refresh (should be skipped because the cache is fresh)"
docker exec eyesky_worker celery -A app.worker.celery_app call app.tasks.tle_tasks.fetch_and_store_tle | Out-Null
Start-Sleep -Seconds 5
docker logs eyesky_worker --tail 6
