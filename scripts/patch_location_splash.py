"""Location fix (#8) + splash hook (#5). Run from the repo root. Idempotent; writes nothing unless all anchors match."""
import pathlib, sys

APP = pathlib.Path("android/app/src/main/java/ke/eyesky/app")
sky_p, main_p = APP / "Sky.kt", APP / "MainActivity.kt"
for p in (sky_p, main_p):
    if not p.exists():
        sys.exit("missing " + str(p) + " - run this from the repo root (F:\\devops\\Eye-in-the-Sky)")
sky = sky_p.read_text(encoding="utf-8")
main = main_p.read_text(encoding="utf-8")

if "locPrefs" in sky and "SplashOverlay()" in main:
    print("already patched"); sys.exit(0)

START = "    fun applyLocation(l: Location) {"
END = "    DisposableEffect(Unit) {\n        onDispose {\n            listenerRef[0]?.let {"
a, b = sky.find(START), sky.find(END)
if a < 0 or b < 0 or b < a:
    sys.exit("Sky.kt anchors not found - nothing changed")

NEW = '''    val locPrefs = remember { ctx.getSharedPreferences("eyesky", Context.MODE_PRIVATE) }
    var accM by remember { mutableStateOf(Float.MAX_VALUE) }
    var manual by remember { mutableStateOf(locPrefs.getBoolean("loc_manual", false)) }
    var showManual by remember { mutableStateOf(false) }
    var manLat by remember { mutableStateOf("") }
    var manLon by remember { mutableStateOf("") }
    var manErr by remember { mutableStateOf("") }

    fun saveLoc(la: Double, lo: Double, al: Double, isManual: Boolean) {
        locPrefs.edit()
            .putString("loc_lat", la.toString())
            .putString("loc_lon", lo.toString())
            .putString("loc_alt", al.toString())
            .putBoolean("loc_manual", isManual)
            .apply()
    }

    fun applyLocation(l: Location) {
        if (manual) return
        val acc = if (l.hasAccuracy()) l.accuracy else 5000f
        val cl = lat
        val co = lon
        if (cl != null && co != null && accM != Float.MAX_VALUE) {
            val res = FloatArray(1)
            Location.distanceBetween(cl, co, l.latitude, l.longitude, res)
            // keep a better fix unless we have really moved; ignore jitter under 30 m
            if (acc > accM && res[0] < maxOf(accM, 100f)) return
            if (res[0] < 30f && acc >= accM * 0.8f) return
        }
        lat = l.latitude
        lon = l.longitude
        val alt = if (l.hasAltitude()) l.altitude else 0.0
        altM = alt
        accM = acc
        saveLoc(l.latitude, l.longitude, alt, false)
        locNote = if (acc <= 100f) "GPS \\u00b1" + acc.roundToInt() + " m"
        else "Approx \\u00b1" + acc.roundToInt() + " m - tap to set exactly"
    }

    fun loadSaved() {
        val sl = locPrefs.getString("loc_lat", null)?.toDoubleOrNull()
        val so = locPrefs.getString("loc_lon", null)?.toDoubleOrNull()
        if (sl != null && so != null && lat == null) {
            lat = sl
            lon = so
            altM = locPrefs.getString("loc_alt", null)?.toDoubleOrNull() ?: 0.0
            locNote = if (manual) "Manual location" else "Last known - updating"
        }
    }

    @SuppressLint("MissingPermission")
    fun startLocation() {
        if (manual) return
        val lm = ctx.getSystemService(Context.LOCATION_SERVICE) as LocationManager
        val last = listOf(
            LocationManager.GPS_PROVIDER, LocationManager.NETWORK_PROVIDER, LocationManager.PASSIVE_PROVIDER
        ).mapNotNull { p -> try { lm.getLastKnownLocation(p) } catch (e: Exception) { null } }
            .maxByOrNull { it.time }
        if (last != null && System.currentTimeMillis() - last.time < 10 * 60 * 1000L) applyLocation(last)
        listenerRef[0]?.let { try { lm.removeUpdates(it) } catch (e: Exception) { } }
        val l = object : LocationListener {
            override fun onLocationChanged(loc: Location) { applyLocation(loc) }
            override fun onStatusChanged(provider: String?, status: Int, extras: Bundle?) {}
            override fun onProviderEnabled(provider: String) {}
            override fun onProviderDisabled(provider: String) {}
        }
        listenerRef[0] = l
        for (p in listOf(LocationManager.GPS_PROVIDER, LocationManager.NETWORK_PROVIDER)) {
            try {
                if (lm.isProviderEnabled(p)) lm.requestLocationUpdates(p, 2000L, 0f, l, Looper.getMainLooper())
            } catch (e: Exception) { }
        }
    }

    fun hasLocPerm(): Boolean =
        ContextCompat.checkSelfPermission(ctx, Manifest.permission.ACCESS_FINE_LOCATION) == PackageManager.PERMISSION_GRANTED ||
            ContextCompat.checkSelfPermission(ctx, Manifest.permission.ACCESS_COARSE_LOCATION) == PackageManager.PERMISSION_GRANTED

    val permLauncher = rememberLauncherForActivityResult(ActivityResultContracts.RequestMultiplePermissions()) {
        if (hasLocPerm()) {
            startLocation()
        } else if (lat == null) {
            locNote = "Location off - tap to set"
            showManual = true
        }
    }

    LaunchedEffect(Unit) {
        loadSaved()
        if (!manual) {
            if (hasLocPerm()) startLocation()
            else permLauncher.launch(arrayOf(Manifest.permission.ACCESS_FINE_LOCATION, Manifest.permission.ACCESS_COARSE_LOCATION))
            delay(15000)
            if (lat == null) {
                locNote = "No GPS fix - tap to set"
                showManual = true
            }
        }
    }

    if (showManual) {
        androidx.compose.material3.AlertDialog(
            onDismissRequest = { showManual = false },
            title = { Text("Set your location") },
            text = {
                Column {
                    Text("Enter your exact coordinates (decimal degrees, e.g. -1.2921 and 36.8219). South and West are negative.")
                    androidx.compose.material3.OutlinedTextField(
                        value = manLat, onValueChange = { manLat = it; manErr = "" },
                        label = { Text("Latitude") }, singleLine = true,
                        keyboardOptions = androidx.compose.foundation.text.KeyboardOptions(
                            keyboardType = androidx.compose.ui.text.input.KeyboardType.Decimal)
                    )
                    androidx.compose.material3.OutlinedTextField(
                        value = manLon, onValueChange = { manLon = it; manErr = "" },
                        label = { Text("Longitude") }, singleLine = true,
                        keyboardOptions = androidx.compose.foundation.text.KeyboardOptions(
                            keyboardType = androidx.compose.ui.text.input.KeyboardType.Decimal)
                    )
                    if (manErr.isNotEmpty()) Text(manErr, color = MaterialTheme.colorScheme.error)
                    TextButton(onClick = {
                        manual = false
                        saveLoc(lat ?: 0.0, lon ?: 0.0, altM, false)
                        locPrefs.edit().remove("loc_lat").remove("loc_lon").putBoolean("loc_manual", false).apply()
                        accM = Float.MAX_VALUE
                        locNote = "Locating..."
                        showManual = false
                        if (hasLocPerm()) startLocation()
                        else permLauncher.launch(arrayOf(Manifest.permission.ACCESS_FINE_LOCATION, Manifest.permission.ACCESS_COARSE_LOCATION))
                    }) { Text("Use GPS") }
                    TextButton(onClick = {
                        manual = true
                        lat = NAIROBI_LAT; lon = NAIROBI_LON; altM = 1795.0; accM = 0f
                        saveLoc(NAIROBI_LAT, NAIROBI_LON, 1795.0, true)
                        locNote = "Manual: Nairobi"
                        showManual = false
                    }) { Text("Use Nairobi") }
                }
            },
            confirmButton = {
                TextButton(onClick = {
                    val la = manLat.trim().replace(',', '.').toDoubleOrNull()
                    val lo = manLon.trim().replace(',', '.').toDoubleOrNull()
                    if (la == null || lo == null || la < -90.0 || la > 90.0 || lo < -180.0 || lo > 180.0) {
                        manErr = "Enter valid numbers (lat -90..90, lon -180..180)"
                    } else {
                        manual = true
                        lat = la; lon = lo; accM = 0f
                        saveLoc(la, lo, altM, true)
                        locNote = "Manual location"
                        showManual = false
                    }
                }) { Text("Save") }
            },
            dismissButton = { TextButton(onClick = { showManual = false }) { Text("Cancel") } }
        )
    }

'''
sky = sky[:a] + NEW + sky[b:]

OLD_NOTE = "Text(locNote, color = dim, style = MaterialTheme.typography.labelSmall)"
if sky.count(OLD_NOTE) != 1:
    sys.exit("top-bar anchor not found - nothing changed")
sky = sky.replace(OLD_NOTE,
    "Text(locNote, color = dim, style = MaterialTheme.typography.labelSmall,\n"
    "                    modifier = Modifier.clickable { manLat = lat?.toString() ?: \"\"; manLon = lon?.toString() ?: \"\"; showManual = true })")
if "import androidx.compose.foundation.clickable" not in sky:
    sky = sky.replace("import androidx.compose.material3.MaterialTheme\n",
        "import androidx.compose.foundation.clickable\nimport androidx.compose.material3.MaterialTheme\n", 1)

OLD_APP = "                        App(prefs, night) {\n                            night = it\n                            prefs.edit().putBoolean(\"night\", it).apply()\n                        }\n"
if main.count(OLD_APP) != 1:
    sys.exit("MainActivity anchor not found - nothing changed")
main = main.replace(OLD_APP, OLD_APP + "                        SplashOverlay()\n")

sky_p.write_text(sky, encoding="utf-8")
main_p.write_text(main, encoding="utf-8")
print("patched Sky.kt and MainActivity.kt")
