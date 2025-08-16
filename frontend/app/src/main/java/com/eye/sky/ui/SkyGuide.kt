package com.eye.sky.ui

import android.annotation.SuppressLint
import android.hardware.Sensor
import android.hardware.SensorEvent
import android.hardware.SensorEventListener
import android.hardware.SensorManager
import androidx.camera.core.CameraSelector
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.camera.view.PreviewView
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalLifecycleOwner
import androidx.compose.ui.viewinterop.AndroidView
import androidx.compose.ui.unit.dp
import com.eye.sky.net.Api
import kotlinx.coroutines.launch
import kotlin.math.*

@Composable
fun SkyGuideScreen() {
    var nightMode by remember { mutableStateOf(true) }
    Column {
        Row(Modifier.fillMaxWidth().padding(8.dp), horizontalArrangement = Arrangement.SpaceBetween) {
            Text("Sky Guide / AR Star Map")
            Row {
                Text("Night")
                Switch(checked = nightMode, onCheckedChange = { nightMode = it })
            }
        }
        Box(Modifier.fillMaxSize()) {
            CameraPreview()
            StarOverlay(nightMode = nightMode)
        }
    }
}

@Composable
private fun CameraPreview() {
    val ctx = LocalContext.current
    val lifecycleOwner = LocalLifecycleOwner.current
    AndroidView(factory = { context ->
        val view = PreviewView(context)
        val cameraProvider = ProcessCameraProvider.getInstance(context).get()
        val preview = androidx.camera.core.Preview.Builder().build()
        preview.setSurfaceProvider(view.surfaceProvider)
        val sel = CameraSelector.DEFAULT_BACK_CAMERA
        cameraProvider.unbindAll()
        cameraProvider.bindToLifecycle(lifecycleOwner, sel, preview)
        view
    }, modifier = Modifier.fillMaxSize())
}

@SuppressLint("MissingPermission")
@Composable
private fun StarOverlay(nightMode: Boolean) {
    val ctx = LocalContext.current
    val sm = ctx.getSystemService(SensorManager::class.java)
    val scope = rememberCoroutineScope()
    var az by remember { mutableStateOf(0f) }
    var pitch by remember { mutableStateOf(0f) }
    var roll by remember { mutableStateOf(0f) }
    var constellations by remember { mutableStateOf<List<Pair<String, Float>>>(emptyList()) }

    // Simple orientation listener (accelerometer + magnetometer fusion)
    DisposableEffect(Unit) {
        val accel = sm.getDefaultSensor(Sensor.TYPE_ACCELEROMETER)
        val magnet = sm.getDefaultSensor(Sensor.TYPE_MAGNETIC_FIELD)
        val aVals = FloatArray(3)
        val mVals = FloatArray(3)
        val R = FloatArray(9)
        val I = FloatArray(9)
        val listener = object : SensorEventListener {
            override fun onSensorChanged(e: SensorEvent) {
                if (e.sensor.type == Sensor.TYPE_ACCELEROMETER) System.arraycopy(e.values, 0, aVals, 0, 3)
                if (e.sensor.type == Sensor.TYPE_MAGNETIC_FIELD) System.arraycopy(e.values, 0, mVals, 0, 3)
                if (SensorManager.getRotationMatrix(R, I, aVals, mVals)) {
                    val orient = FloatArray(3)
                    SensorManager.getOrientation(R, orient)
                    az = orient[0] // -pi..pi
                    pitch = orient[1]
                    roll = orient[2]
                }
            }
            override fun onAccuracyChanged(sensor: Sensor?, accuracy: Int) {}
        }
        sm.registerListener(listener, accel, SensorManager.SENSOR_DELAY_GAME)
        sm.registerListener(listener, magnet, SensorManager.SENSOR_DELAY_GAME)
        onDispose { sm.unregisterListener(listener) }
    }

    // Fetch star map once (you can refetch on location/date change)
    LaunchedEffect(Unit) {
        // dummy coords; wire to real GPS or your location store
        val lat = -1.286389; val lon = 36.817223
        val resp = runCatching { Api.service.starmap(lat, lon, null) }.getOrNull()
        // For demo draw 10 placeholder “stars” named from constellations payload shape
        constellations = List(10) { i -> "★ Star $i" to (i * 36f) }
    }

    Canvas(modifier = Modifier.fillMaxSize()) {
        // rudimentary star projection: place labels around based on azimuth
        val cx = size.width / 2f
        val cy = size.height / 2f
        val radius = min(cx, cy) * 0.8f
        for ((name, bearing) in constellations) {
            val angle = ((bearing.toDouble() - Math.toDegrees(az.toDouble())) + 360.0) % 360.0
            val rad = Math.toRadians(angle)
            val x = cx + radius * cos(rad).toFloat()
            val y = cy + radius * sin(rad).toFloat()
            drawCircle(color = if (nightMode) Color(1f,0.1f,0.1f,0.9f) else Color.White, radius = 4f, center = androidx.compose.ui.geometry.Offset(x, y))
            drawContext.canvas.nativeCanvas.apply {
                val p = android.graphics.Paint().apply {
                    color = if (nightMode) android.graphics.Color.RED else android.graphics.Color.WHITE
                    textSize = 28f
                }
                drawText(name, x+6f, y, p)
            }
        }
    }
}