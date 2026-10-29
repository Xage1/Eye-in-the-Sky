param([Parameter(Mandatory = $true)][string]$Domain)
# Exposes the local backend (port 8000) at https://<Domain> so the phone works anywhere.
$ng = Get-Command ngrok -ErrorAction SilentlyContinue
if (-not $ng) { throw "ngrok not found. Install it with: winget install ngrok.ngrok  (then open a NEW PowerShell window)" }
$running = docker ps --filter "name=eyesky_api" --format "{{.Status}}"
if (-not $running) { throw "eyesky_api is not running. Start it with: docker compose up -d" }
"Tunnel: https://$Domain  ->  http://localhost:8000   (leave this window open; Ctrl+C stops it)"
ngrok http "--url=$Domain" 8000
