# android/build_install.ps1 - build the debug APK and (if a phone is connected) install and launch it.
# Everything heavy lives on F: because C: is small.
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not $env:JAVA_HOME) {
  $j = Get-ChildItem "C:\Program Files\Microsoft" -Directory -Filter "jdk-17*" | Select-Object -First 1
  if ($j) { $env:JAVA_HOME = $j.FullName }
}
$env:ANDROID_HOME      = "F:\devops\android-sdk"
$env:GRADLE_USER_HOME  = "F:\devops\gradle-home"
$env:ANDROID_USER_HOME = "F:\devops\android-home"
New-Item -ItemType Directory -Force $env:GRADLE_USER_HOME, $env:ANDROID_USER_HOME | Out-Null

if (-not (Test-Path ".\gradlew.bat")) {
  "generating the Gradle wrapper (one time)"
  & "F:\devops\tools\gradle-8.9\bin\gradle.bat" wrapper --gradle-version 8.9 --no-daemon
  if ($LASTEXITCODE -ne 0) { "wrapper generation failed"; exit 1 }
}

& .\gradlew.bat assembleDebug
if ($LASTEXITCODE -ne 0) { "BUILD FAILED"; exit 1 }

$apk = Join-Path $PSScriptRoot "app\build\outputs\apk\debug\app-debug.apk"
"APK: $apk  (" + [math]::Round((Get-Item $apk).Length/1MB,1) + " MB)"

$ErrorActionPreference = "Continue"
$adb = "$env:ANDROID_HOME\platform-tools\adb.exe"
$dev = (& $adb devices | Select-String "\sdevice$")
if (-not $dev) {
  "No phone connected (or not authorised). Plug it in with USB debugging on and run this script again."
  exit 0
}
& $adb reverse tcp:8000 tcp:8000 | Out-Null
& $adb uninstall ke.eyeinthesky.app 2>&1 | Out-Null   # the old pre-rename app, if still installed
$out = & $adb install -r $apk 2>&1
$out
if ($out -match "Failure" -or $LASTEXITCODE -ne 0) {
  "INSTALL FAILED. Turn on Install via USB in Developer options (keep the phone unlocked), or install by hand from the phone Downloads folder."
  & $adb push $apk /sdcard/Download/eyesky.apk
  exit 1
}
& $adb shell am start -n ke.eyesky.app/.MainActivity
"Launched on the phone."
