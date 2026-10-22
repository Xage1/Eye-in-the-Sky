# scripts/smoke_payments.ps1 - forged / replayed / unauthenticated requests against the payment endpoints.
# Every check here must be REJECTED or have no effect. Exit code 1 if any check fails.
$base = "http://localhost:8000"
$script:fail = 0

function Call([string]$method, [string]$path, $headers = @{}, [string]$body = "") {
  try {
    if ($body) { $r = Invoke-WebRequest -Uri "$base$path" -Method $method -Headers $headers -Body $body -ContentType "application/json" -UseBasicParsing -TimeoutSec 90 }
    else       { $r = Invoke-WebRequest -Uri "$base$path" -Method $method -Headers $headers -UseBasicParsing -TimeoutSec 90 }
    return @{ code = [int]$r.StatusCode; body = $r.Content }
  } catch {
    $code = 0
    if ($_.Exception.Response) { $code = [int]$_.Exception.Response.StatusCode }
    return @{ code = $code; body = "$($_.ErrorDetails.Message)" }
  }
}
function Check([string]$name, $got, [int[]]$want) {
  $ok = $want -contains $got
  if (-not $ok) { $script:fail++ }
  "{0,-6} {1,-74} got {2} (want {3})" -f $(if ($ok) { "PASS" } else { "FAIL" }), $name, $got, ($want -join "/")
}

$email = "paysmoke$(Get-Random)@example.com"; $pw = "Sm0keTest!2026xyz"
$null = Call POST "/auth/signup" @{} (@{ name = "Pay Smoke"; email = $email; password = $pw } | ConvertTo-Json)
$login = Call POST "/auth/login" @{} (@{ email = $email; password = $pw } | ConvertTo-Json)
$lj = $login.body | ConvertFrom-Json
$tok = if ($lj.access_token) { $lj.access_token } else { $lj.token }
if (-not $tok) { "login failed: $($login.body)"; exit 2 }
$auth = @{ Authorization = "Bearer $tok" }
$me = (Call GET "/auth/me" $auth).body | ConvertFrom-Json

$fakeHook = '{"event":"charge.success","data":{"reference":"EYESKY-PREMIUM-1-FORGED","metadata":{"user_id":"1","plan":"premium","interval":"yearly"}}}'
Check "webhook with NO signature header"            (Call POST "/payments/webhook" @{} $fakeHook).code 401
Check "webhook with a wrong signature"              (Call POST "/payments/webhook" @{ "x-paystack-signature" = "deadbeef" } $fakeHook).code 401
Check "old open mpesa callback URL is gone"         (Call POST "/payments/mpesa/callback" @{} "{}").code 404, 405
Check "mpesa callback with a wrong secret"          (Call POST "/payments/mpesa/callback/not-the-secret" @{} "{}").code 404
Check "verify without a token"                      (Call POST "/payments/verify" @{} '{"reference":"EYESKY-PRO-1-AAAAAAAA"}').code 401
Check "verify an unknown reference"                 (Call POST "/payments/verify" $auth '{"reference":"EYESKY-PRO-1-AAAAAAAA"}').code 404
Check "mpesa status without a token"                (Call POST "/payments/mpesa/status" @{} '{"checkout_request_id":"ws_CO_000000"}').code 401
Check "mpesa status for an unknown checkout id"     (Call POST "/payments/mpesa/status" $auth '{"checkout_request_id":"ws_CO_000000"}').code 404

# The real exploit: plant a pending Premium-yearly transaction, then send a forged SUCCESS callback with the real secret.
$envFile = @("backend\.env", ".env") | Where-Object { Test-Path $_ } | Select-Object -First 1
$sec = $null
if ($envFile) {
  $line = Get-Content $envFile | Where-Object { $_ -match '^MPESA_CALLBACK_SECRET=' } | Select-Object -Last 1
  if ($line) { $sec = ($line -split '=', 2)[1].Trim() }
}
if (-not $sec) {
  "SKIP   forged-callback test: MPESA_CALLBACK_SECRET not found in .env"
} else {
  $cid = "ws_CO_FORGE_" + [guid]::NewGuid().ToString("N")
  $sql = "INSERT INTO transactions (user_id, provider, status, plan, interval, amount, currency, mpesa_checkout_request_id, mpesa_merchant_request_id, description) VALUES ($($me.id), 'mpesa', 'pending', 'premium', 'yearly', 5990, 'KES', '$cid', 'forge-test', 'forgery test')"
  docker exec eyesky_postgres psql -U postgres -d eye_db -q -c $sql | Out-Null
  $forged = '{"Body":{"stkCallback":{"MerchantRequestID":"forge-test","CheckoutRequestID":"' + $cid + '","ResultCode":0,"ResultDesc":"The service request is processed successfully.","CallbackMetadata":{"Item":[{"Name":"Amount","Value":5990},{"Name":"MpesaReceiptNumber","Value":"FORGED123"},{"Name":"PhoneNumber","Value":254700000000}]}}}}'
  $cb = Call POST "/payments/mpesa/callback/$sec" @{} $forged
  Check "forged SUCCESS callback is acknowledged (no 5xx)" $cb.code 200
  $sub = Call GET "/payments/subscription" $auth
  $plan = if ($sub.code -eq 200) { ($sub.body | ConvertFrom-Json).plan } else { "none" }
  Check "forged callback did NOT upgrade the user (plan=$plan)" $(if ($plan -in @("none", "free")) { 200 } else { 0 }) 200
  $st = (docker exec eyesky_postgres psql -U postgres -d eye_db -t -A -c "select status from transactions where mpesa_checkout_request_id='$cid'").Trim()
  Check "planted transaction is still pending (status=$st)" $(if ($st -eq "pending") { 200 } else { 0 }) 200
}

""
if ($script:fail -eq 0) { "ALL PAYMENT NEGATIVE TESTS PASSED" } else { "$($script:fail) FAILED"; exit 1 }