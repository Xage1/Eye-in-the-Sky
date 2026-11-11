$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$envf = Join-Path (Join-Path (Split-Path -Parent $root) "wispbyte_bundle") ".env"
if (-not (Test-Path $envf)) { throw "Run make_wispbyte_env.ps1 first" }
$line = Get-Content $envf | Where-Object { $_ -like "DATABASE_URL_SYNC=*" } | Select-Object -First 1
$url = $line.Substring("DATABASE_URL_SYNC=".Length) -replace '^postgresql\+[a-z0-9]+://', 'postgresql://'

"Local database size:"
docker exec eyesky_postgres psql -U postgres -d eye_db -t -c "select pg_size_pretty(pg_database_size('eye_db'))"
"Dumping the local database ..."
docker exec eyesky_postgres pg_dump -U postgres -Fc --no-owner --no-acl -f /tmp/eye.dump eye_db
"Restoring into Neon (warnings about existing objects are normal) ..."
docker exec eyesky_postgres pg_restore --no-owner --no-acl --clean --if-exists -d $url /tmp/eye.dump
"Check in Neon:"
docker exec eyesky_postgres psql $url -t -c "select count(*) as tables from information_schema.tables where table_schema='public'"
docker exec eyesky_postgres psql $url -t -c "select * from alembic_version"
docker exec eyesky_postgres rm -f /tmp/eye.dump
