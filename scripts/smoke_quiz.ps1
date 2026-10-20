$base = "http://localhost:8000"
$script:results = @()

function Call-Api($method, $path, $body = $null, $token = $null) {
  $headers = @{}
  if ($token) { $headers["Authorization"] = "Bearer $token" }
  $params = @{ Uri = "$base$path"; Method = $method; Headers = $headers; UseBasicParsing = $true; TimeoutSec = 120 }
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
    return [pscustomobject]@{ Status = $status; Body = [string]$text }
  }
}

function Check($name, $ok, $detail = "") {
  $script:results += [pscustomobject]@{ Test = $name; Result = $(if ($ok) { "PASS" } else { "FAIL" }); Detail = $detail }
}

$rand = Get-Random -Maximum 99999
$email = "quizsmoke$rand@example.com"
$pw = "Sm0keTest!2026xyz"

$r = Call-Api POST "/auth/signup" @{ name = "Quiz Smoke"; email = $email; password = $pw }
Check "signup" ($r.Status -in 200,201) "HTTP $($r.Status) $($r.Body.Substring(0,[Math]::Min(100,$r.Body.Length)))"

$r = Call-Api POST "/auth/login" @{ email = $email; password = $pw }
$token = ($r.Body | ConvertFrom-Json).access_token
Check "login returns token" ([bool]$token) "HTTP $($r.Status)"

$r = Call-Api GET "/quiz/?difficulty=simple"
$qs = [object[]](ConvertFrom-Json -InputObject $r.Body)
Check "GET /quiz returns 5 questions" ($qs.Count -eq 5) "count=$($qs.Count)"
Check "answer key not leaked" ($r.Body -notmatch "correct_answer") ""

$ids = ($qs | ForEach-Object { $_.id }) -join ","
$rows = docker exec eyesky_postgres psql -U postgres -d eye_db -t -A -c "SELECT id || '::' || correct_answer FROM quiz_questions WHERE id IN ($ids)"
$key = @{}
foreach ($line in $rows) { if ($line -match "^(\d+)::(.*)$") { $key[[int]$Matches[1]] = $Matches[2] } }
Check "answer key read from DB" ($key.Count -eq 5) "keys=$($key.Count)"

$answers = @(); $i = 0
foreach ($q in $qs) {
  $correct = $key[[int]$q.id]
  if ($i -lt 3) { $sel = $correct } else { $sel = ($q.options | Where-Object { $_ -ne $correct } | Select-Object -First 1) }
  $answers += @{ question_id = [int]$q.id; selected_answer = $sel }
  $i++
}

$r = Call-Api POST "/quiz/submit" @{ answers = $answers } $token
$sub = $r.Body | ConvertFrom-Json
Check "submit returns 200" ($r.Status -eq 200) "HTTP $($r.Status) $(if ($r.Status -ne 200) { $r.Body })"
Check "server score is 3/5" (($sub.score -eq 3) -and ($sub.total_questions -eq 5)) "score=$($sub.score) total=$($sub.total_questions)"
Check "answers returned with key" (@($sub.answers).Count -eq 5) "answers=$(@($sub.answers).Count)"

$q0 = $qs[0]
$wrong = ($q0.options | Where-Object { $_ -ne $key[[int]$q0.id] } | Select-Object -First 1)
$r = Call-Api POST "/quiz/submit" @{ answers = @(@{ question_id = [int]$q0.id; selected_answer = $wrong; correct_answer = $wrong }) } $token
$tam = $r.Body | ConvertFrom-Json
Check "client-supplied correct_answer ignored" (($r.Status -eq 200) -and ($tam.score -eq 0)) "HTTP $($r.Status) score=$($tam.score)"

$r = Call-Api POST "/quiz/submit" @{ answers = @(@{ question_id = 1; selected_answer = "x" }) }
Check "submit without token rejected" ($r.Status -in 401,403) "HTTP $($r.Status)"

$r = Call-Api POST "/quiz/submit" @{ answers = @(@{ question_id = 999999; selected_answer = "x" }) } $token
Check "unknown question -> 404" ($r.Status -eq 404) "HTTP $($r.Status)"

$r = Call-Api POST "/quiz/submit" @{ answers = @(@{ question_id = [int]$q0.id; selected_answer = "a" }, @{ question_id = [int]$q0.id; selected_answer = "b" }) } $token
Check "duplicate question -> 400" ($r.Status -eq 400) "HTTP $($r.Status)"

$r = Call-Api POST "/quiz/submit" @{ answers = @() } $token
Check "empty submission -> 400" ($r.Status -eq 400) "HTTP $($r.Status)"

$r = Call-Api GET "/quiz/history" $null $token
$h = [object[]](ConvertFrom-Json -InputObject $r.Body)
Check "history: 2 submissions, newest first" (($h.Count -eq 2) -and ($h[0].total_questions -eq 1)) "HTTP $($r.Status) count=$($h.Count)"

$results | Format-Table -AutoSize -Wrap