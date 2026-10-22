# scripts/backup_db.ps1 - dump the Postgres database to F:\devops\backups, keep the newest 14.
# Needs Docker Desktop running. Exit code 1 on any failure.
$dir = "F:\devops\backups"
New-Item -ItemType Directory -Force $dir | Out-Null
$out = Join-Path $dir ("eye_db_{0}.dump" -f (Get-Date -Format yyyyMMdd_HHmm))

docker exec eyesky_postgres pg_dump -U postgres -Fc eye_db -f /tmp/eye_db.dump
if ($LASTEXITCODE -ne 0) { Write-Error "pg_dump failed"; exit 1 }

# integrity check: pg_restore must be able to read the dump's table of contents
docker exec eyesky_postgres pg_restore -l /tmp/eye_db.dump | Out-Null
if ($LASTEXITCODE -ne 0) { Write-Error "dump is not readable"; exit 1 }

docker cp "eyesky_postgres:/tmp/eye_db.dump" $out
docker exec eyesky_postgres rm -f /tmp/eye_db.dump

if (-not (Test-Path $out) -or (Get-Item $out).Length -lt 10KB) { Write-Error "backup missing or too small"; exit 1 }

Get-ChildItem $dir -Filter "eye_db_*.dump" | Sort-Object LastWriteTime -Descending | Select-Object -Skip 14 | Remove-Item -Force
"OK  $out  ($([math]::Round((Get-Item $out).Length/1KB)) KB)"