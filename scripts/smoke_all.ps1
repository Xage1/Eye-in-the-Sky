$base = "http://localhost:8000"
$LAT = -1.2921; $LON = 36.8219
$script:results = @()

function Call-Api($method, $path, $body = $null, $token = $null, $extra = @{}) {
  $h = @{}
  foreach ($k in $extra.Keys) { $h[$k] = $extra[$k] }
  if ($token) { $h["Authorization"] = "Bearer $token" }
  $params = @{ Uri = "$base$path"; Method = $method; Headers = $h; UseBasicParsing = $true; TimeoutSec = 180 }
  if ($body -ne $null) { $params["Body"] = ($body | ConvertTo-Json -Depth 6); $params["ContentType"] = "application/json" }
  try {
    $r = Invoke-WebRequest @params
    return [pscustomobject]@{ Status = [int]$r.StatusCode; Body = [string]$r.Content }
  } catch {
    $resp = $_.Exception.Response
    $status = 0; $text = $_.Exception.Message
    if ($resp) {
      $sr = New-Object System.IO.StreamReader($resp.GetResponseStream())
      $text = $sr.ReadToEnd(); $status = [int]$resp.StatusCode
    }
    if ($_.ErrorDetails -and $_.ErrorDetails.Message) { $text = $_.ErrorDetails.Message }
    return [pscustomobject]@{ Status = $status; Body = [string]$text }
  }
}

function T($method, $path, $expect, $body = $null, $token = $null, $extra = @{}, $label = "") {
  $sw = [Diagnostics.Stopwatch]::StartNew()
  $r = Call-Api $method $path $body $token $extra
  $sw.Stop(); $ms = [int]$sw.ElapsedMilliseconds
  $ok = $r.Status -in $expect
  $note = ""
  $excerpt = ($r.Body -replace '\s+', ' ')
  if ($excerpt.Length -gt 160) { $excerpt = $excerpt.Substring(0, 160) }
  if ($ok) {
    $verdict = "PASS"
    if (($r.Status -ge 200) -and ($r.Status -lt 300) -and ($r.Body -match '"error"\s*:')) { $verdict = "WARN"; $note = "2xx but body has error: $excerpt" }
    elseif ($ms -gt 3000) { $verdict = "WARN"; $note = "slow" }
  } else { $verdict = "FAIL"; $note = $excerpt }
  $name = "$method $path"
  if ($label) { $name = "$name [$label]" }
  if ($name.Length -gt 70) { $name = $name.Substring(0, 70) }
  $script:results += [pscustomobject]@{ Verdict = $verdict; Test = $name; Status = $r.Status; Ms = $ms; Note = $note }
  return $r
}

$q = "?lat=$LAT&lon=$LON"

# ---------- public routes ----------
$null = T GET "/" @(200)
$null = T GET "/auth/health" @(200)
$null = T GET "/constellations/$q" @(200)
$null = T GET "/events/$q" @(200)
$null = T GET "/events/night-sky$q" @(200)
$null = T GET "/skyinfo/moon-phase$q" @(200)
$null = T GET "/skyinfo/visibility$q" @(200)
$null = T GET "/skyinfo/rise-set$q&date=2026-10-17" @(200)
$null = T GET "/skyinfo/scene$q&az=90&alt=45" @(200)
$null = T GET "/skyinfo/planets$q&az=90&alt=45" @(200)
$null = T GET "/skyinfo/iss$q" @(200)
$null = T GET "/skyinfo/events$q" @(200)
$null = T GET "/skyinfo/star/Sirius" @(200)
$null = T GET "/starmap/$q" @(200)
$null = T GET "/lessons/" @(200)
$null = T GET "/lessons/1" @(200,404)
$null = T GET "/lessons/by-category/astronomy" @(200)
$null = T GET "/sky/satellites/visible$q" @(200)
$null = T GET "/sky/focus$q&azimuth=90" @(200)
$null = T GET "/payments/plans" @(200)
$null = T GET "/quiz/" @(200)

# ---------- sign up a fresh free-tier user ----------
$email = "smoke$(Get-Random -Maximum 99999)@example.com"
$pw = "Sm0keTest!2026xyz"
$null = T POST "/auth/signup" @(201) @{ name = "Smoke Test"; email = $email; password = $pw }
$r = T POST "/auth/login" @(200) @{ email = $email; password = $pw }
$token = $null
try { $token = ($r.Body | ConvertFrom-Json).access_token } catch {}

# ---------- authenticated routes ----------
$null = T GET "/auth/me" @(200) $null $token
$null = T PATCH "/auth/me" @(200) @{ bio = "smoke test" } $token
$null = T GET "/user/settings/" @(200) $null $token
$null = T PATCH "/user/settings/" @(200,422) @{} $token @{} "empty patch"
$null = T GET "/watchlist/" @(200) $null $token
$null = T POST "/watchlist/" @(200,201) @{ star_name = "Sirius"; description = "smoke test" } $token
$null = T GET "/watchlist/" @(200) $null $token @{} "after add"
$null = T GET "/notifications" @(200) $null $token
$null = T GET "/notifications/unread-count" @(200) $null $token
$null = T PATCH "/notifications/read-all" @(200) $null $token
$null = T PATCH "/notifications/999999/read" @(404) $null $token
$null = T POST "/location/store" @(200,201) @{ latitude = $LAT; longitude = $LON } $token
$null = T GET "/location/history" @(200) $null $token
$null = T GET "/payments/subscription" @(200) $null $token
$null = T GET "/payments/transactions" @(200) $null $token

# ---------- protected routes without a token ----------
foreach ($p in @("/auth/me", "/watchlist/", "/notifications", "/payments/subscription", "/jwst/images", "/location/history", "/quiz/history", "/user/settings/")) {
  $null = T GET $p @(401,403) $null $null @{} "no token"
}

# ---------- security checks ----------
$null = T POST "/lessons/" @(401,403) @{} $null @{} "SECURITY anonymous write"
$null = T POST "/lessons/" @(403) @{} $token @{} "SECURITY non-admin write"
$null = T GET "/auth/admin/users" @(403) $null $token @{} "SECURITY non-admin"
$null = T PATCH "/auth/admin/users/999999/role?role=admin" @(403) $null $token @{} "SECURITY escalation"
$forged = @{ event = "charge.success"; data = @{ reference = "smoke-nonexistent-ref"; status = "success"; amount = 100; customer = @{ email = "nobody@example.com" } } }
$null = T POST "/payments/webhook" @(400,401,403) $forged $null @{ "x-paystack-signature" = "deadbeef" } "SECURITY forged webhook"
$null = T POST "/payments/mpesa/callback" @(200,400,404,422) @{} $null @{} "garbage body, no 5xx"

# ---------- JWST Pro gate (free user) ----------
$null = T POST "/jwst/search" @(402) @{ target = "Carina Nebula" } $token @{} "free user gated"
$null = T GET "/jwst/images" @(402) $null $token @{} "free user gated"
$null = T POST "/jwst/images" @(402) @{ product_uri = "mast:JWST/x.fits"; filename = "x.fits"; obsid = "1" } $token @{} "free user gated"
$null = T GET "/jwst/images/1" @(402) $null $token @{} "free user gated"

# ---------- report ----------
$results | Format-Table Verdict, Test, Status, Ms -AutoSize
$g = $results | Group-Object Verdict
"Summary: " + (($g | ForEach-Object { "$($_.Name)=$($_.Count)" }) -join "   ") + "   (total $($results.Count))"
$bad = $results | Where-Object { $_.Verdict -ne "PASS" }
if ($bad) {
  "`n--- Needs attention ---"
  $bad | ForEach-Object { "{0} {1} -> {2} ({3} ms) {4}" -f $_.Verdict, $_.Test, $_.Status, $_.Ms, $_.Note }
}