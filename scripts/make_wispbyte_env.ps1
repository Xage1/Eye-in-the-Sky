$ErrorActionPreference = "Stop"
function Read-Secret($prompt) {
    Write-Host $prompt
    $s = Read-Host -AsSecureString
    $b = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($s)
    try { return [Runtime.InteropServices.Marshal]::PtrToStringAuto($b) } finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($b) }
}
$root = Split-Path -Parent $PSScriptRoot
$out = Join-Path (Split-Path -Parent $root) "wispbyte_bundle"
if (-not (Test-Path $out)) { throw "Run make_wispbyte_bundle.ps1 first" }

# current settings from the running backend (values are never printed)
$cur = @{}
docker exec eyesky_api printenv | ForEach-Object { if ($_ -match '^([A-Za-z0-9_]+)=(.*)$') { $cur[$matches[1]] = $matches[2] } }
$keep = @("ACCESS_TOKEN_EXPIRE_MINUTES", "ADMIN_EMAILS", "ALGORITHM", "ASTRONOMY_APP_ID", "ASTRONOMY_APP_SECRET_KEY",
    "CELESTRAK_URL", "MPESA_CALLBACK_SECRET", "MPESA_CALLBACK_URL", "MPESA_CONSUMER_KEY", "MPESA_CONSUMER_SECRET",
    "MPESA_ENV", "MPESA_PASSKEY", "MPESA_SHORTCODE", "N2YO_API_KEY", "NASA_API_KEY", "OPEN_NOTIFY_ISS_URL",
    "PAYSTACK_CALLBACK_URL", "PAYSTACK_PUBLIC_KEY", "PAYSTACK_SECRET_KEY", "SECRET_KEY", "WEATHER_API_KEY")
$lines = @()
foreach ($k in $keep) { if ($cur.ContainsKey($k)) { $lines += "$k=$($cur[$k])" } else { "note: $k not set locally, skipped" } }

$neonRaw = Read-Secret "Paste the NEW Neon connection string (direct one, pooling off). Nothing shows while you paste. Right-click, then Enter:"
if ([string]::IsNullOrWhiteSpace($neonRaw)) { throw "Nothing was pasted. Right-click in the window to paste, then press Enter." }
if ($neonRaw -notmatch "postgres(?:ql)?://[^\s'`"]+") { throw "No postgresql:// address found in what you pasted (it should start with postgresql://)" }
$neon = $matches[0]
if ($neon -notmatch '^postgres(?:ql)?://([^:]+):([^@]+)@([^/]+)/([^?\s]+)') { throw "Found the address but could not read user, password, host and database from it" }
$u = $matches[1]; $p = $matches[2]; $h = ($matches[3] -replace '-pooler', ''); $d = $matches[4]
$scheme = "postgresql"
if ($cur.ContainsKey("DATABASE_URL_SYNC")) { $scheme = ($cur["DATABASE_URL_SYNC"] -split "://")[0] }
$lines += "DATABASE_URL=postgresql+asyncpg://${u}:${p}@${h}/${d}?ssl=require"
$lines += "DATABASE_URL_SYNC=${scheme}://${u}:${p}@${h}/${d}?sslmode=require"

$rRaw = Read-Secret "Paste the NEW Upstash Redis URL (nothing shows while you paste). Right-click, then Enter:"
if ([string]::IsNullOrWhiteSpace($rRaw)) { throw "Nothing was pasted. Right-click in the window to paste, then press Enter." }
if ($rRaw -notmatch "rediss?://[^\s'`"]+") { throw "No redis:// or rediss:// address found in what you pasted" }
$r = $matches[0] -replace '^redis://', 'rediss://'
$lines += "REDIS_URL=$r"

$tok = (Read-Secret "Paste the NEW ngrok authtoken (nothing shows). Right-click, then Enter:").Trim()
"Your ngrok domain [postinfective-shelia-crowingly.ngrok-free.dev], then Enter:"
$dom = (Read-Host).Trim()
if (-not $dom) { $dom = "postinfective-shelia-crowingly.ngrok-free.dev" }
$lines += "NGROK_AUTHTOKEN=$tok"
$lines += "NGROK_DOMAIN=$dom"
$lines += "LITE_MODE=1"

[System.IO.File]::WriteAllLines((Join-Path $out ".env"), [string[]]$lines)
"Wrote $($lines.Count) settings to $out\.env (keys only):"
($lines | ForEach-Object { $_.Split("=")[0] }) -join ", "
"Keep that .env private. Never commit it or paste it anywhere."
