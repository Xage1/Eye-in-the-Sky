"""Location fix 2: stop lag (throttle updates) + always ask for precise permission + app-settings button. Run from repo root."""
import pathlib, sys
p = pathlib.Path("android/app/src/main/java/ke/eyesky/app/Sky.kt")
if not p.exists(): sys.exit("run from the repo root")
s = p.read_text(encoding="utf-8")
if "val moved = res[0]" in s:
    print("already patched"); sys.exit(0)

FINE = "Manifest.permission.ACCESS_FINE_LOCATION"
reps = [
("""        if (cl != null && co != null && accM != Float.MAX_VALUE) {
            val res = FloatArray(1)
            Location.distanceBetween(cl, co, l.latitude, l.longitude, res)
            // keep a better fix unless we have really moved; ignore jitter under 30 m
            if (acc > accM && res[0] < maxOf(accM, 100f)) return
            if (res[0] < 30f && acc >= accM * 0.8f) return
        }
""",
"""        if (cl != null && co != null) {
            val res = FloatArray(1)
            Location.distanceBetween(cl, co, l.latitude, l.longitude, res)
            val moved = res[0]
            // keep a better fix unless we have really moved
            if (accM != Float.MAX_VALUE && acc > accM && moved < maxOf(accM, 100f)) return
            // small moves: do NOT touch lat/lon (changing them reloads the whole sky)
            if (moved < 50f) {
                if (acc < accM * 0.7f) {
                    accM = acc
                    locNote = if (acc <= 100f) "GPS \\u00b1" + acc.roundToInt() + " m"
                    else "Approx \\u00b1" + acc.roundToInt() + " m - tap to set exactly"
                }
                return
            }
        }
"""),
("""        locNote = if (acc <= 100f) "GPS \\u00b1" + acc.roundToInt() + " m"
        else "Approx \\u00b1" + acc.roundToInt() + " m - tap to set exactly"
    }

    fun loadSaved""",
"""        locNote = if (acc <= 100f) "GPS \\u00b1" + acc.roundToInt() + " m"
        else "Approx \\u00b1" + acc.roundToInt() + " m - tap to set exactly"
        if (acc <= 25f) {
            // precise enough: stop listening so the app stops redrawing and saves battery
            listenerRef[0]?.let {
                try { (ctx.getSystemService(Context.LOCATION_SERVICE) as LocationManager).removeUpdates(it) } catch (e: Exception) { }
            }
        }
    }

    fun loadSaved"""),
("lm.requestLocationUpdates(p, 2000L, 0f, l, Looper.getMainLooper())",
 "lm.requestLocationUpdates(p, 5000L, 10f, l, Looper.getMainLooper())"),
("""            if (hasLocPerm()) startLocation()
            else permLauncher.launch(arrayOf(Manifest.permission.ACCESS_FINE_LOCATION, Manifest.permission.ACCESS_COARSE_LOCATION))
            delay(15000)""",
"""            if (hasLocPerm()) startLocation()
            // ask for PRECISE even if approximate was already granted
            if (ContextCompat.checkSelfPermission(ctx, Manifest.permission.ACCESS_FINE_LOCATION) != PackageManager.PERMISSION_GRANTED) {
                permLauncher.launch(arrayOf(Manifest.permission.ACCESS_FINE_LOCATION, Manifest.permission.ACCESS_COARSE_LOCATION))
            }
            delay(15000)"""),
("""                    TextButton(onClick = {
                        manual = true
                        lat = NAIROBI_LAT""",
"""                    TextButton(onClick = {
                        try {
                            ctx.startActivity(android.content.Intent(
                                android.provider.Settings.ACTION_APPLICATION_DETAILS_SETTINGS,
                                android.net.Uri.parse("package:" + ctx.packageName)))
                        } catch (e: Exception) { }
                    }) { Text("Open app settings (allow precise)") }
                    TextButton(onClick = {
                        manual = true
                        lat = NAIROBI_LAT"""),
]
for old, new in reps:
    if s.count(old) != 1:
        sys.exit("anchor not found, nothing changed:\n" + old[:80])
    s = s.replace(old, new)
p.write_text(s, encoding="utf-8")
print("patched Sky.kt")
