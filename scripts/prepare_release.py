"""
Prepares the Android project for a Play Store release build (run from the repo root):
  python scripts\\prepare_release.py
- default server = the live HTTPS address (BuildConfig.DEFAULT_SERVER)
- release builds block plain-HTTP traffic (debug builds still allow it)
- release signing is read from android\\keystore.properties (never committed)
Safe to run twice. Nothing is written unless every change can be made.
"""
import re
import sys
from pathlib import Path

SERVER = "https://postinfective-shelia-crowingly.ngrok-free.dev"
root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
android = root / "android"
src = android / "app" / "src" / "main"
files = {
    "gradle": android / "app" / "build.gradle.kts",
    "manifest": src / "AndroidManifest.xml",
    "api": src / "java" / "ke" / "eyesky" / "app" / "Api.kt",
    "main": src / "java" / "ke" / "eyesky" / "app" / "MainActivity.kt",
}
for k, p in files.items():
    if not p.exists():
        sys.exit("Missing file: %s  (run this from the repo root, F:\\devops\\Eye-in-the-Sky)" % p)

text = {k: p.read_text(encoding="utf-8") for k, p in files.items()}
orig = dict(text)
problems = []

# ---- app/build.gradle.kts ----
g = text["gradle"]
if "DEFAULT_SERVER" not in g:
    m = re.search(r'^([ \t]*)versionName\s*=.*$', g, re.M)
    if not m:
        problems.append("build.gradle.kts: could not find the versionName line")
    else:
        ind = m.group(1)
        add = ('\n%sbuildConfigField("String", "DEFAULT_SERVER", "\\"%s\\"")'
               '\n%smanifestPlaceholders["usesCleartext"] = "false"') % (ind, SERVER, ind)
        g = g[:m.end()] + add + g[m.end():]
if "buildConfig = true" not in g:
    m = re.search(r'(buildFeatures\s*\{[^}]*?)(compose\s*=\s*true)', g)
    if not m:
        problems.append("build.gradle.kts: could not find buildFeatures { compose = true }")
    else:
        g = g[:m.end()] + "\n        buildConfig = true" + g[m.end():]
if "keystoreProps" not in g:
    m = re.search(r'^([ \t]*)buildTypes\s*\{', g, re.M)
    if not m:
        problems.append("build.gradle.kts: could not find buildTypes {")
    else:
        block = '''    val keystoreProps = java.util.Properties().apply {
        val f = rootProject.file("keystore.properties")
        if (f.exists()) f.inputStream().use { load(it) }
    }
    signingConfigs {
        if (keystoreProps.containsKey("storeFile")) {
            create("release") {
                storeFile = file(keystoreProps.getProperty("storeFile"))
                storePassword = keystoreProps.getProperty("storePassword")
                keyAlias = keystoreProps.getProperty("keyAlias")
                keyPassword = keystoreProps.getProperty("keyPassword")
            }
        }
    }

'''
        g = g[:m.start()] + block + g[m.start():]
if 'signingConfigs.findByName("release")' not in g:
    new_bt, n = re.subn(
        r'release\s*\{\s*isMinifyEnabled\s*=\s*false\s*\}',
        'release {\n            isMinifyEnabled = false\n'
        '            signingConfig = signingConfigs.findByName("release")\n        }\n'
        '        debug {\n            manifestPlaceholders["usesCleartext"] = "true"\n        }', g)
    if n != 1:
        problems.append("build.gradle.kts: could not find the release { isMinifyEnabled = false } block")
    else:
        g = new_bt
text["gradle"] = g

# ---- AndroidManifest.xml ----
mf = text["manifest"]
if "${usesCleartext}" not in mf:
    mf, n = re.subn(r'android:usesCleartextTraffic="[^"]*"', 'android:usesCleartextTraffic="${usesCleartext}"', mf)
    if n != 1:
        problems.append("AndroidManifest.xml: could not find android:usesCleartextTraffic")
text["manifest"] = mf

# ---- Api.kt and MainActivity.kt ----
a = text["api"]
if "BuildConfig.DEFAULT_SERVER" not in a:
    a, n = re.subn(r'(@Volatile\s+var\s+baseUrl(?:\s*:\s*String)?\s*=\s*)"http://localhost:8000"', r'\1BuildConfig.DEFAULT_SERVER', a)
    if n != 1:
        problems.append("Api.kt: could not find the baseUrl default")
text["api"] = a
mn = text["main"]
if "Api.baseUrl = BuildConfig.DEFAULT_SERVER" not in mn:
    mn, n = re.subn(r'Api\.baseUrl\s*=\s*"http://localhost:8000"', 'Api.baseUrl = BuildConfig.DEFAULT_SERVER', mn)
    if n < 1:
        problems.append("MainActivity.kt: could not find the Reset line (Api.baseUrl = \"http://localhost:8000\")")
text["main"] = mn

if problems:
    print("Nothing was changed. Problems:")
    for p in problems:
        print("  - " + p)
    sys.exit(1)

for k, p in files.items():
    if text[k] != orig[k]:
        p.write_text(text[k], encoding="utf-8", newline="")
        print("updated  " + str(p.relative_to(root)))
    else:
        print("already  " + str(p.relative_to(root)))

example = android / "keystore.properties.example"
example.write_text("storeFile=F:/devops/eyesky-upload.jks\nstorePassword=\nkeyAlias=eyesky\nkeyPassword=\n", encoding="utf-8")

gi = root / ".gitignore"
cur = gi.read_text(encoding="utf-8") if gi.exists() else ""
need = [l for l in ("android/keystore.properties", "keystore.properties", "*.jks", "*.keystore") if l not in cur.split()]
if need:
    gi.write_text(cur.rstrip("\n") + "\n" + "\n".join(need) + "\n", encoding="utf-8")
    print("gitignore: added " + ", ".join(need))
print("Done. Default server is " + SERVER)
