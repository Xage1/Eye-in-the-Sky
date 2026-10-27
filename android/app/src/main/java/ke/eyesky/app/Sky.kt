package ke.eyesky.app

import android.Manifest
import android.annotation.SuppressLint
import android.content.Context
import android.content.pm.PackageManager
import android.hardware.GeomagneticField
import android.hardware.Sensor
import android.hardware.SensorEvent
import android.hardware.SensorEventListener
import android.hardware.SensorManager
import android.location.Location
import android.location.LocationListener
import android.location.LocationManager
import android.os.Bundle
import android.os.Looper
import androidx.activity.ComponentActivity
import androidx.activity.compose.BackHandler
import android.hardware.camera2.CameraCharacteristics
import androidx.camera.camera2.interop.Camera2CameraInfo
import androidx.camera.camera2.interop.ExperimentalCamera2Interop
import androidx.camera.core.Camera
import androidx.camera.core.CameraSelector
import androidx.camera.core.Preview
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.camera.view.PreviewView
import androidx.compose.ui.viewinterop.AndroidView
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.gestures.detectTransformGestures
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.systemBarsPadding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.nativeCanvas
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.unit.dp
import androidx.core.content.ContextCompat
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.withContext
import org.json.JSONObject
import kotlin.math.acos
import kotlin.math.asin
import kotlin.math.atan
import kotlin.math.tan
import kotlin.math.atan2
import kotlin.math.cos
import kotlin.math.hypot
import kotlin.math.max
import kotlin.math.min
import kotlin.math.roundToInt
import kotlin.math.sin
import kotlin.math.sqrt

private const val NAIROBI_LAT = -1.2921
private const val NAIROBI_LON = 36.8219
private const val DEG = "°"

private val CARDINALS = arrayOf(
    "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
    "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"
)

// ---------------------------------------------------------------- data

class SkyStar(
    val hr: Int, val mag: Float, val ra: Double, val dec: Double,
    val name: String, val constellation: String
)

class SkyBody(val name: String, val az: Double, val alt: Double)

class Bodies(val planets: List<SkyBody>, val sats: List<SkyBody>, val iss: SkyBody?)

private class Marker(val x: Float, val y: Float, val title: String, val detail: String, val kind: String = "")

private val VIEWABLE = setOf("sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn", "uranus", "neptune", "star")

fun parseStars(j: JSONObject): List<SkyStar> {
    val arr = j.getJSONArray("stars")
    val names = j.optJSONObject("names")
    val out = ArrayList<SkyStar>(arr.length())
    for (i in 0 until arr.length()) {
        val r = arr.getJSONArray(i)
        val hr = r.getInt(0)
        val nm = names?.optJSONArray(hr.toString())
        out.add(
            SkyStar(
                hr, r.getDouble(1).toFloat(), r.getDouble(2), r.getDouble(3),
                nm?.optString(0).orEmpty(), nm?.optString(1).orEmpty()
            )
        )
    }
    return out
}

fun parseBodies(j: JSONObject): Bodies {
    fun list(key: String): List<SkyBody> {
        val a = j.optJSONArray(key) ?: return emptyList()
        val out = ArrayList<SkyBody>()
        for (i in 0 until a.length()) {
            val o = a.getJSONObject(i)
            out.add(SkyBody(o.optString("name"), o.optDouble("az"), o.optDouble("alt")))
        }
        return out
    }
    val iss = j.optJSONObject("iss")?.let {
        if (it.optBoolean("available")) SkyBody("ISS", it.optDouble("az"), it.optDouble("alt")) else null
    }
    return Bodies(list("planets"), list("satellites"), iss)
}

// ---------------------------------------------------------------- astronomy on the phone

/** Greenwich mean sidereal time in degrees (IAU 1982), same formula as the server. */
fun gmstDeg(nowMs: Long): Double {
    val jd = nowMs / 86400000.0 + 2440587.5
    val t = (jd - 2451545.0) / 36525.0
    val sec = 67310.54841 + (876600.0 * 3600.0 + 8640184.812866) * t + 0.093104 * t * t - 6.2e-6 * t * t * t
    return (((sec % 86400.0) + 86400.0) % 86400.0) / 240.0
}

/** Fill out[] with East/North/Up unit vectors for every star at the given time and place. */
fun starVectors(stars: List<SkyStar>, latDeg: Double, lonDeg: Double, nowMs: Long, out: FloatArray) {
    val lst = gmstDeg(nowMs) + lonDeg
    val phi = Math.toRadians(latDeg)
    val sp = sin(phi)
    val cp = cos(phi)
    for (i in stars.indices) {
        val s = stars[i]
        val h = Math.toRadians(lst - s.ra)
        val dec = Math.toRadians(s.dec)
        val cd = cos(dec)
        val sd = sin(dec)
        val sinAlt = (sd * sp + cd * cp * cos(h)).coerceIn(-1.0, 1.0)
        val ca = sqrt(1.0 - sinAlt * sinAlt)
        val az = atan2(-cd * sin(h), sd * cp - cd * sp * cos(h))
        out[3 * i] = (ca * sin(az)).toFloat()
        out[3 * i + 1] = (ca * cos(az)).toFloat()
        out[3 * i + 2] = sinAlt.toFloat()
    }
}

/** The camera: which way the phone's back points, and how world directions land on the screen. */
private class Cam {
    var xe = 0f; var xn = 0f; var xu = 0f      // screen-right in world East/North/Up
    var ye = 0f; var yn = 0f; var yu = 0f      // screen-up
    var fe = 0f; var fn = 0f; var fu = 0f      // pointing direction (out of the back)
    var w = 1f; var h = 1f
    var halfH = 1f; var halfV = 1f
    var cosCull = 0f
    var outX = 0f; var outY = 0f
    var focal = 0f   // > 0: camera (pinhole) projection in pixels; 0: map (equidistant) projection

    /** rot is Android's rotation matrix (device -> East/North/Up); decl is magnetic declination in radians. */
    fun set(rot: FloatArray, decl: Double, fovHDeg: Float, width: Float, height: Float, focalPx: Float) {
        focal = focalPx
        val c = cos(decl).toFloat()
        val s = sin(decl).toFloat()
        xe = rot[0] * c + rot[3] * s; xn = -rot[0] * s + rot[3] * c; xu = rot[6]
        ye = rot[1] * c + rot[4] * s; yn = -rot[1] * s + rot[4] * c; yu = rot[7]
        fe = -rot[2] * c - rot[5] * s; fn = rot[2] * s - rot[5] * c; fu = -rot[8]
        w = width
        h = height
        halfH = Math.toRadians(fovHDeg / 2.0).toFloat()
        halfV = halfH * height / width
        val diag = sqrt(halfH * halfH + halfV * halfV) * 1.15f
        cosCull = cos(min(diag, 1.75f))
    }

    /** Project a unit vector. Returns false when it is outside the view; otherwise sets outX/outY. */
    fun project(te: Float, tn: Float, tu: Float): Boolean {
        val dot = te * fe + tn * fn + tu * fu
        if (focal > 0f) {
            if (dot < 0.08f) return false
            outX = w / 2f + focal * (te * xe + tn * xn + tu * xu) / dot
            outY = h / 2f - focal * (te * ye + tn * yn + tu * yu) / dot
            return outX > -60f && outX < w + 60f && outY > -60f && outY < h + 60f
        }
        if (dot < cosCull) return false
        val ang = acos(dot.coerceIn(-1f, 1f))
        val k = if (ang < 1e-4f) 1f else ang / sin(ang)
        val ax = k * (te * xe + tn * xn + tu * xu)
        val ay = k * (te * ye + tn * yn + tu * yu)
        outX = w / 2f + ax / halfH * (w / 2f)
        outY = h / 2f - ay / halfV * (h / 2f)
        return true
    }
}

/** Field of view (degrees) along the camera sensor's long axis, which is the screen height in portrait. */
@OptIn(ExperimentalCamera2Interop::class)
private fun cameraFovLongDeg(camera: Camera): Double? {
    return try {
        val c2 = Camera2CameraInfo.from(camera.cameraInfo)
        val size = c2.getCameraCharacteristic(CameraCharacteristics.SENSOR_INFO_PHYSICAL_SIZE) ?: return null
        val focal = c2.getCameraCharacteristic(CameraCharacteristics.LENS_INFO_AVAILABLE_FOCAL_LENGTHS)
            ?.firstOrNull() ?: return null
        var longMm = max(size.width, size.height).toDouble()
        val pix = c2.getCameraCharacteristic(CameraCharacteristics.SENSOR_INFO_PIXEL_ARRAY_SIZE)
        val act = c2.getCameraCharacteristic(CameraCharacteristics.SENSOR_INFO_ACTIVE_ARRAY_SIZE)
        if (pix != null && act != null) {
            longMm *= max(act.width(), act.height()).toDouble() / max(pix.width, pix.height)
        }
        val deg = Math.toDegrees(2.0 * atan(longMm / (2.0 * focal)))
        if (deg in 40.0..100.0) deg else null
    } catch (e: Exception) {
        null
    }
}

private fun enuE(altDeg: Double, azDeg: Double) = (cos(Math.toRadians(altDeg)) * sin(Math.toRadians(azDeg))).toFloat()
private fun enuN(altDeg: Double, azDeg: Double) = (cos(Math.toRadians(altDeg)) * cos(Math.toRadians(azDeg))).toFloat()
private fun enuU(altDeg: Double) = sin(Math.toRadians(altDeg)).toFloat()

// ---------------------------------------------------------------- the screen

@Composable
fun SkyScreen(onBack: () -> Unit, onOpenObject: (String, String, String) -> Unit) {
    val ctx = LocalContext.current
    val density = LocalDensity.current.density
    BackHandler(onBack = onBack)

    val ink = MaterialTheme.colorScheme.onBackground
    val gold = MaterialTheme.colorScheme.primary
    val cyan = MaterialTheme.colorScheme.secondary
    val dim = MaterialTheme.colorScheme.onSurfaceVariant
    val bg = MaterialTheme.colorScheme.background
    val card = MaterialTheme.colorScheme.surface

    var lat by remember { mutableStateOf<Double?>(null) }
    var lon by remember { mutableStateOf<Double?>(null) }
    var altM by remember { mutableStateOf(0.0) }
    var locNote by remember { mutableStateOf("Locating...") }
    var stars by remember { mutableStateOf<List<SkyStar>>(emptyList()) }
    var bodies by remember { mutableStateOf(Bodies(emptyList(), emptyList(), null)) }
    var status by remember { mutableStateOf("Loading the sky...") }
    var hud by remember { mutableStateOf("") }
    var fov by remember { mutableStateOf(65f) }
    var declDeg by remember { mutableStateOf(0.0) }
    var selected by remember { mutableStateOf<Triple<String, String, String>?>(null) }
    var tick by remember { mutableIntStateOf(0) }
    var hasSensor by remember { mutableStateOf(true) }
    val rot = remember { floatArrayOf(1f, 0f, 0f, 0f, 1f, 0f, 0f, 0f, 1f) }

    var camGranted by remember {
        mutableStateOf(
            ContextCompat.checkSelfPermission(ctx, Manifest.permission.CAMERA) == PackageManager.PERMISSION_GRANTED
        )
    }
    var arOn by remember { mutableStateOf(camGranted) }
    var camReady by remember { mutableStateOf(false) }
    var fovLongDeg by remember { mutableStateOf(68.0) }
    var arZoom by remember { mutableStateOf(1f) }
    val camRef = remember { arrayOfNulls<Camera>(1) }
    val camPermLauncher = rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) { ok ->
        camGranted = ok
        if (ok) arOn = true
    }
    val arActive = arOn && camGranted && camReady

    DisposableEffect(arOn) {
        onDispose {
            if (camRef[0] != null) {
                camRef[0] = null
                camReady = false
                try {
                    ProcessCameraProvider.getInstance(ctx).get().unbindAll()
                } catch (e: Exception) { }
            }
        }
    }

    val vec = remember(stars) { FloatArray(stars.size * 3) }
    val px = remember(stars) { FloatArray(stars.size) }
    val py = remember(stars) { FloatArray(stars.size) }
    val vis = remember(stars) { BooleanArray(stars.size) }
    val markers = remember { ArrayList<Marker>() }
    val cam = remember { Cam() }
    val textPaint = remember { android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG) }

    // ---- location
    val listenerRef = remember { arrayOfNulls<LocationListener>(1) }

    fun applyLocation(l: Location) {
        lat = l.latitude
        lon = l.longitude
        altM = if (l.hasAltitude()) l.altitude else 0.0
        locNote = "GPS"
    }

    @SuppressLint("MissingPermission")
    fun startLocation() {
        val lm = ctx.getSystemService(Context.LOCATION_SERVICE) as LocationManager
        val last = listOf(
            LocationManager.GPS_PROVIDER, LocationManager.NETWORK_PROVIDER, LocationManager.PASSIVE_PROVIDER
        ).mapNotNull { p -> try { lm.getLastKnownLocation(p) } catch (e: Exception) { null } }
            .maxByOrNull { it.time }
        if (last != null) applyLocation(last)
        val l = object : LocationListener {
            override fun onLocationChanged(loc: Location) {
                applyLocation(loc)
                try { lm.removeUpdates(this) } catch (e: Exception) { }
            }
            override fun onStatusChanged(provider: String?, status: Int, extras: Bundle?) {}
            override fun onProviderEnabled(provider: String) {}
            override fun onProviderDisabled(provider: String) {}
        }
        listenerRef[0] = l
        for (p in listOf(LocationManager.GPS_PROVIDER, LocationManager.NETWORK_PROVIDER)) {
            try {
                if (lm.isProviderEnabled(p)) lm.requestLocationUpdates(p, 0L, 0f, l, Looper.getMainLooper())
            } catch (e: Exception) { }
        }
    }

    val permLauncher = rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) { granted ->
        if (granted) {
            startLocation()
        } else {
            lat = NAIROBI_LAT
            lon = NAIROBI_LON
            locNote = "Location off: using Nairobi"
        }
    }

    LaunchedEffect(Unit) {
        val ok = ContextCompat.checkSelfPermission(ctx, Manifest.permission.ACCESS_FINE_LOCATION) ==
            PackageManager.PERMISSION_GRANTED
        if (ok) startLocation() else permLauncher.launch(Manifest.permission.ACCESS_FINE_LOCATION)
        delay(8000)
        if (lat == null) {
            lat = NAIROBI_LAT
            lon = NAIROBI_LON
            locNote = "No GPS fix: using Nairobi"
        }
    }

    DisposableEffect(Unit) {
        onDispose {
            listenerRef[0]?.let {
                try {
                    (ctx.getSystemService(Context.LOCATION_SERVICE) as LocationManager).removeUpdates(it)
                } catch (e: Exception) { }
            }
        }
    }

    LaunchedEffect(lat, lon) {
        val la = lat
        val lo = lon
        if (la != null && lo != null) {
            declDeg = GeomagneticField(
                la.toFloat(), lo.toFloat(), altM.toFloat(), System.currentTimeMillis()
            ).declination.toDouble()
        }
    }

    // ---- orientation sensor
    DisposableEffect(Unit) {
        val sm = ctx.getSystemService(Context.SENSOR_SERVICE) as SensorManager
        val sensor = sm.getDefaultSensor(Sensor.TYPE_ROTATION_VECTOR)
        if (sensor == null) {
            hasSensor = false
            onDispose { }
        } else {
            val l = object : SensorEventListener {
                override fun onSensorChanged(e: SensorEvent) {
                    SensorManager.getRotationMatrixFromVector(rot, e.values)
                    val d = Math.toRadians(declDeg)
                    val c = cos(d).toFloat()
                    val s = sin(d).toFloat()
                    val fe = -rot[2] * c - rot[5] * s
                    val fn = rot[2] * s - rot[5] * c
                    val fu = -rot[8]
                    val alt = Math.toDegrees(asin(fu.coerceIn(-1f, 1f).toDouble()))
                    var az = Math.toDegrees(atan2(fe.toDouble(), fn.toDouble()))
                    if (az < 0) az += 360.0
                    val name = CARDINALS[((az + 11.25) / 22.5).toInt() % 16]
                    val text = name + " " + az.roundToInt() + DEG + "   ·   alt " + alt.roundToInt() + DEG
                    if (text != hud) hud = text
                    tick++
                }
                override fun onAccuracyChanged(s: Sensor?, a: Int) {}
            }
            sm.registerListener(l, sensor, SensorManager.SENSOR_DELAY_GAME)
            onDispose { sm.unregisterListener(l) }
        }
    }

    // ---- sky data: stars once, moving bodies every 10 s
    LaunchedEffect(lat, lon) {
        val la = lat
        val lo = lon
        if (la != null && lo != null) {
            var needStars = true
            while (true) {
                try {
                    val j = Api.dome(la, lo, needStars)
                    if (needStars) {
                        stars = withContext(Dispatchers.Default) { parseStars(j) }
                        needStars = false
                        status = ""
                    }
                    bodies = parseBodies(j)
                } catch (e: Exception) {
                    if (stars.isEmpty()) status = "Cannot reach the server. Is the USB cable connected?"
                }
                delay(if (needStars) 4000L else 10000L)
            }
        }
    }

    // ---- star positions follow the clock (Earth turns 15 degrees an hour)
    LaunchedEffect(stars, lat, lon) {
        val la = lat
        val lo = lon
        if (la != null && lo != null && stars.isNotEmpty()) {
            while (true) {
                starVectors(stars, la, lo, System.currentTimeMillis(), vec)
                delay(1000)
            }
        }
    }

    Box(Modifier.fillMaxSize().background(if (arActive) Color.Transparent else bg)) {
        if (arOn && camGranted) {
            AndroidView(
                factory = { c ->
                    PreviewView(c).also { pv ->
                        pv.implementationMode = PreviewView.ImplementationMode.COMPATIBLE
                        val future = ProcessCameraProvider.getInstance(c)
                        future.addListener({
                            try {
                                val provider = future.get()
                                val preview = Preview.Builder().build()
                                preview.setSurfaceProvider(pv.surfaceProvider)
                                provider.unbindAll()
                                val camera = provider.bindToLifecycle(
                                    ctx as ComponentActivity, CameraSelector.DEFAULT_BACK_CAMERA, preview
                                )
                                camRef[0] = camera
                                cameraFovLongDeg(camera)?.let { fovLongDeg = it }
                                camReady = true
                            } catch (e: Exception) {
                                camReady = false
                                status = "Camera unavailable: " + e.message
                            }
                        }, ContextCompat.getMainExecutor(c))
                    }
                },
                modifier = Modifier.fillMaxSize()
            )
        }
        Canvas(
            Modifier
                .fillMaxSize()
                .pointerInput(stars) {
                    detectTapGestures { pos ->
                        val thr = 44f * density
                        var best = Float.MAX_VALUE
                        var title = ""
                        var detail = ""
                        var kind = ""
                        for (m in markers) {
                            val d = hypot(m.x - pos.x, m.y - pos.y)
                            if (d < thr && d < best) { best = d; title = m.title; detail = m.detail; kind = m.kind }
                        }
                        for (i in stars.indices) {
                            if (!vis[i]) continue
                            val s = stars[i]
                            val d = hypot(px[i] - pos.x, py[i] - pos.y) - max(0f, 6f - s.mag) * 1.5f
                            if (d < thr * 0.6f && d < best) {
                                best = d
                                kind = "star:" + s.hr
                                title = if (s.name.isNotEmpty()) s.name else "HR " + s.hr
                                val alt = Math.toDegrees(asin(vec[3 * i + 2].toDouble())).roundToInt()
                                var az = Math.toDegrees(atan2(vec[3 * i].toDouble(), vec[3 * i + 1].toDouble()))
                                if (az < 0) az += 360.0
                                detail = (if (s.constellation.isNotEmpty()) s.constellation + "  ·  " else "") +
                                    "magnitude " + s.mag + "\nalt " + alt + DEG + "   az " + az.roundToInt() + DEG
                            }
                        }
                        selected = if (best < Float.MAX_VALUE) Triple(title, detail, kind) else null
                    }
                }
                .pointerInput(Unit) {
                    detectTransformGestures { _, _, zoom, _ ->
                        if (arOn && camGranted && camReady) {
                            val maxZ = camRef[0]?.cameraInfo?.zoomState?.value?.maxZoomRatio ?: 1f
                            arZoom = (arZoom * zoom).coerceIn(1f, min(maxZ, 8f))
                            camRef[0]?.cameraControl?.setZoomRatio(arZoom)
                        } else {
                            fov = (fov / zoom).coerceIn(25f, 100f)
                        }
                    }
                }
        ) {
            @Suppress("UNUSED_VARIABLE")
            val frame = tick
            val w = size.width
            val h = size.height
            val focal = if (arActive) (h / 2f) / tan(Math.toRadians(fovLongDeg / 2.0)).toFloat() * arZoom else 0f
            cam.set(rot, Math.toRadians(declDeg), fov, w, h, focal)
            if (arActive) drawRect(Color.Black.copy(alpha = 0.2f))
            markers.clear()

            // horizon
            var prevOk = false
            var pxPrev = 0f
            var pyPrev = 0f
            for (a in 0..72) {
                val az = Math.toRadians(a * 5.0)
                val ok = cam.project(sin(az).toFloat(), cos(az).toFloat(), 0f)
                if (ok && prevOk) {
                    drawLine(
                        dim.copy(alpha = 0.55f), Offset(pxPrev, pyPrev), Offset(cam.outX, cam.outY),
                        strokeWidth = 1.5f * density
                    )
                }
                prevOk = ok
                pxPrev = cam.outX
                pyPrev = cam.outY
            }

            textPaint.textAlign = android.graphics.Paint.Align.CENTER
            textPaint.isFakeBoldText = true
            textPaint.color = gold.toArgb()
            textPaint.textSize = 16f * density
            for (k in 0 until 8) {
                val az = Math.toRadians(k * 45.0)
                if (cam.project(sin(az).toFloat(), cos(az).toFloat(), 0f)) {
                    textPaint.textSize = (if (k % 2 == 0) 18f else 12f) * density
                    drawContext.canvas.nativeCanvas.drawText(CARDINALS[k * 2], cam.outX, cam.outY - 8f * density, textPaint)
                }
            }

            // stars
            val n = stars.size
            for (i in 0 until n) {
                val te = vec[3 * i]
                val tn = vec[3 * i + 1]
                val tu = vec[3 * i + 2]
                if (tu < 0f || (te == 0f && tn == 0f && tu == 0f) || !cam.project(te, tn, tu)) {
                    vis[i] = false
                    continue
                }
                val m = stars[i].mag
                val r = max(0.7f, 3.4f - 0.45f * m) * density
                val a = (1.0f - 0.09f * m).coerceIn(0.35f, 1f)
                if (m < 1.0f) {
                    drawCircle(ink.copy(alpha = 0.12f), r * 2.4f, Offset(cam.outX, cam.outY))
                }
                drawCircle(ink.copy(alpha = a), r, Offset(cam.outX, cam.outY))
                px[i] = cam.outX
                py[i] = cam.outY
                vis[i] = true
            }

            // names of the brightest stars
            textPaint.isFakeBoldText = false
            textPaint.textAlign = android.graphics.Paint.Align.LEFT
            textPaint.textSize = 12f * density
            textPaint.color = ink.copy(alpha = 0.8f).toArgb()
            for (i in 0 until n) {
                val s = stars[i]
                if (vis[i] && s.mag <= 2.3f && s.name.isNotEmpty()) {
                    drawContext.canvas.nativeCanvas.drawText(
                        s.name, px[i] + 8f * density, py[i] - 6f * density, textPaint
                    )
                }
            }

            // Sun, Moon and planets
            for (b in bodies.planets) {
                if (b.alt < -1.0 || !cam.project(enuE(b.alt, b.az), enuN(b.alt, b.az), enuU(b.alt))) continue
                val lname = b.name.lowercase()
                val rad: Float
                val col: Color
                when (lname) {
                    "sun" -> { rad = 11f; col = Color(0xFFFFD27A) }
                    "moon" -> { rad = 9f; col = Color(0xFFF2EFE4) }
                    else -> { rad = 5f; col = gold }
                }
                val label = b.name.replaceFirstChar { it.uppercase() }
                drawCircle(col.copy(alpha = 0.18f), rad * 2.2f * density, Offset(cam.outX, cam.outY))
                drawCircle(col, rad * density, Offset(cam.outX, cam.outY))
                textPaint.color = col.toArgb()
                drawContext.canvas.nativeCanvas.drawText(
                    label, cam.outX + (rad + 5f) * density, cam.outY - 4f * density, textPaint
                )
                markers.add(
                    Marker(cam.outX, cam.outY, label,
                        (if (lname == "sun" || lname == "moon") "" else "Planet\n") +
                            "alt " + b.alt.roundToInt() + DEG + "   az " + b.az.roundToInt() + DEG, lname)
                )
            }

            // satellites and the ISS (cyan = moving, live)
            for (s in bodies.sats) {
                if (s.alt < 0.0 || !cam.project(enuE(s.alt, s.az), enuN(s.alt, s.az), enuU(s.alt))) continue
                drawCircle(cyan, 2.4f * density, Offset(cam.outX, cam.outY))
                markers.add(
                    Marker(cam.outX, cam.outY, s.name,
                        "Satellite\nalt " + s.alt.roundToInt() + DEG + "   az " + s.az.roundToInt() + DEG, "sat")
                )
            }
            bodies.iss?.let { s ->
                if (s.alt >= 0.0 && cam.project(enuE(s.alt, s.az), enuN(s.alt, s.az), enuU(s.alt))) {
                    drawCircle(cyan.copy(alpha = 0.2f), 14f * density, Offset(cam.outX, cam.outY))
                    drawCircle(cyan, 7f * density, Offset(cam.outX, cam.outY), style = Stroke(2f * density))
                    drawCircle(cyan, 2.6f * density, Offset(cam.outX, cam.outY))
                    textPaint.color = cyan.toArgb()
                    drawContext.canvas.nativeCanvas.drawText(
                        "ISS", cam.outX + 12f * density, cam.outY - 4f * density, textPaint
                    )
                    markers.add(
                        Marker(cam.outX, cam.outY, "International Space Station",
                            "alt " + s.alt.roundToInt() + DEG + "   az " + s.az.roundToInt() + DEG, "iss")
                    )
                }
            }

            // centre reticle
            drawCircle(ink.copy(alpha = 0.3f), 18f * density, Offset(w / 2f, h / 2f), style = Stroke(1.2f * density))
        }

        // top bar
        Row(
            Modifier.fillMaxWidth().systemBarsPadding().padding(horizontal = 8.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            TextButton(onClick = onBack) { Text("‹ Back", color = ink) }
            Spacer(Modifier.weight(1f))
            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                Text(hud, color = ink, style = MaterialTheme.typography.titleMedium)
                Text(locNote, color = dim, style = MaterialTheme.typography.labelSmall)
            }
            Spacer(Modifier.weight(1f))
            TextButton(onClick = {
                if (arOn) {
                    arOn = false
                } else if (camGranted) {
                    arOn = true
                } else {
                    camPermLauncher.launch(Manifest.permission.CAMERA)
                }
            }) { Text(if (arOn) "Map" else "Camera", color = cyan) }
        }

        // messages and the tap card
        Column(
            Modifier.align(Alignment.BottomCenter).fillMaxWidth().systemBarsPadding().padding(16.dp)
        ) {
            if (!hasSensor) {
                Text("This phone has no rotation sensor, so the sky cannot follow your movement.", color = MaterialTheme.colorScheme.error)
            }
            if (status.isNotEmpty()) {
                Text(status, color = dim, style = MaterialTheme.typography.bodyMedium)
            }
            selected?.let { (t, d, k) ->
                Surface(
                    color = card.copy(alpha = 0.94f),
                    shape = RoundedCornerShape(16.dp),
                    modifier = Modifier.fillMaxWidth().clickable { selected = null }
                ) {
                    Column(Modifier.padding(16.dp)) {
                        Text(t, style = MaterialTheme.typography.titleLarge, color = gold)
                        Text(d, style = MaterialTheme.typography.bodyMedium, color = ink)
                        if (k.substringBefore(":") in VIEWABLE) {
                            TextButton(onClick = { onOpenObject(k, t, d) }) {
                                Text("View in 3D \u203A", color = cyan)
                            }
                        }
                    }
                }
            }
        }
    }
}
