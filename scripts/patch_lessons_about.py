"""Adds Lessons + About buttons to the Home screen. Run from repo root. Idempotent."""
import pathlib, sys
p = pathlib.Path("android/app/src/main/java/ke/eyesky/app/MainActivity.kt")
if not p.exists(): sys.exit("run from the repo root")
s = p.read_text(encoding="utf-8")
if "LessonsScreen(" in s:
    print("already patched"); sys.exit(0)
reps = [
("    var inSky by remember { mutableStateOf(false) }\n",
 "    var inSky by remember { mutableStateOf(false) }\n    var page by remember { mutableStateOf(\"\") }\n"),
("    if (loggedIn && inSky) {",
 "    if (loggedIn && page == \"lessons\") {\n        LessonsScreen(onBack = { page = \"\" })\n    } else if (loggedIn && page == \"about\") {\n        AboutScreen(onBack = { page = \"\" })\n    } else if (loggedIn && inSky) {"),
("        HomeScreen(night = night, onNight = onNight, onOpenSky = { inSky = true }, onLogout = {",
 "        HomeScreen(night = night, onNight = onNight, onOpenSky = { inSky = true },\n            onLessons = { page = \"lessons\" }, onAbout = { page = \"about\" }, onLogout = {"),
("fun HomeScreen(night: Boolean, onNight: (Boolean) -> Unit, onOpenSky: () -> Unit, onLogout: () -> Unit) {",
 "fun HomeScreen(night: Boolean, onNight: (Boolean) -> Unit, onOpenSky: () -> Unit,\n               onLessons: () -> Unit, onAbout: () -> Unit, onLogout: () -> Unit) {"),
("        Button(onClick = onOpenSky, modifier = Modifier.fillMaxWidth()) { Text(\"Open sky view\") }\n",
 "        Button(onClick = onOpenSky, modifier = Modifier.fillMaxWidth()) { Text(\"Open sky view\") }\n"
 "        Spacer(Modifier.height(10.dp))\n"
 "        OutlinedButton(onClick = onLessons, modifier = Modifier.fillMaxWidth()) { Text(\"Lessons\") }\n"
 "        Spacer(Modifier.height(10.dp))\n"
 "        OutlinedButton(onClick = onAbout, modifier = Modifier.fillMaxWidth()) { Text(\"About & credits\") }\n"),
]
for old, new in reps:
    if s.count(old) != 1: sys.exit("anchor not found, nothing changed:\n" + old[:70])
    s = s.replace(old, new)
p.write_text(s, encoding="utf-8"); print("patched MainActivity.kt")
