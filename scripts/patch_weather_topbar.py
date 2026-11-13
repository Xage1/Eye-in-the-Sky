"""Adds a Weather button to the sky view and fixes the crowded top bar. Run from repo root. Idempotent."""
import pathlib, sys
p = pathlib.Path("android/app/src/main/java/ke/eyesky/app/Sky.kt")
if not p.exists(): sys.exit("run from the repo root")
s = p.read_text(encoding="utf-8")
if "WeatherDialog(" in s:
    print("already patched"); sys.exit(0)

reps = [
("    var showManual by remember { mutableStateOf(false) }\n",
 "    var showManual by remember { mutableStateOf(false) }\n    var showWeather by remember { mutableStateOf(false) }\n"),
("""        Row(
            Modifier.fillMaxWidth().systemBarsPadding().padding(horizontal = 8.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            TextButton(onClick = onBack) { Text("‹ Back", color = ink) }
            Spacer(Modifier.weight(1f))
            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                Text(hud, color = ink, style = MaterialTheme.typography.titleMedium)
                Text(locNote, color = dim, style = MaterialTheme.typography.labelSmall,
                    modifier = Modifier.clickable { manLat = lat?.toString() ?: ""; manLon = lon?.toString() ?: ""; showManual = true })
            }
            Spacer(Modifier.weight(1f))
""",
"""        Column(Modifier.fillMaxWidth().systemBarsPadding().padding(horizontal = 8.dp)) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            TextButton(onClick = onBack) { Text("‹ Back", color = ink, maxLines = 1, softWrap = false) }
            Spacer(Modifier.weight(1f))
"""),
("""            }) { Text(if (arOn) "Map" else "Camera", color = cyan) }
        }
""",
"""            }) { Text(if (arOn) "Map" else "Camera", color = cyan, maxLines = 1, softWrap = false) }
            TextButton(onClick = { showWeather = true }) { Text("Weather", color = ink, maxLines = 1, softWrap = false) }
        }
        Column(Modifier.fillMaxWidth(), horizontalAlignment = Alignment.CenterHorizontally) {
            Text(hud, color = ink, style = MaterialTheme.typography.titleMedium)
            Text(locNote, color = dim, style = MaterialTheme.typography.labelSmall,
                modifier = Modifier.clickable { manLat = lat?.toString() ?: ""; manLon = lon?.toString() ?: ""; showManual = true })
        }
        }
        if (showWeather) WeatherDialog(lat, lon) { showWeather = false }
"""),
("}) { Text(\"Align\", color = gold) }", "}) { Text(\"Align\", color = gold, maxLines = 1, softWrap = false) }"),
("}) { Text(\"Reset\", color = dim) }", "}) { Text(\"Reset\", color = dim, maxLines = 1, softWrap = false) }"),
]
for old, new in reps:
    if s.count(old) != 1:
        sys.exit("anchor not found, nothing changed:\n" + old[:80])
    s = s.replace(old, new)
p.write_text(s, encoding="utf-8"); print("patched Sky.kt")
