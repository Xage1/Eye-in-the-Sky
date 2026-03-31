package com.eye.sky.ui

import android.annotation.SuppressLint
import android.graphics.Paint
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
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.drawscope.drawIntoCanvas
import androidx.compose.ui.graphics.nativeCanvas
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalLifecycleOwner
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import com.eye.sky.net.Api
import kotlin.math.*

@Composable
fun SkyGuideScreen() {
    var nightMode by remember { mutableStateOf(true) }

    Column {
        Row(
            Modifier.fillMaxWidth().padding(8.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
        ) {
            Text("Sky Guide / AR Star Map")
            Row(verticalAlignment = androidx.compose.ui.Alignment.CenterVertically) {
                Text("Night")
                Spacer(Modifier.width(4.dp))
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
    val lifecycleOwner = LocalLifecycleOwner.current
    AndroidView(
        factory = { context ->
            val view = PreviewView(context)
            val future = ProcessCameraProvider.getInstance(context)
            future.addListener({
                val provider = future.get()
                val preview  = androidx.camera.core.Preview.Builder().build()
                preview.setSurfaceProvider(view.surfaceProvider)
                provider.unbindAll()
                provider.bindToLifecycle(
                    lifecycleOwner,
                    CameraSelector.DEFAULT_BACK_CAMERA,
                    preview,
                )
            }, context.mainExecutor)
            view
        },
        modifier = Modifier.fillMaxSize(),
    )
}

@SuppressLint("MissingPermission")
@Composable
private fun StarOverlay(nightMode: Boolean) {
    val ctx = LocalContext.current
    val sm  = ctx.getSystemService(SensorManager::class.java)

    var az    by remember { mutableStateOf(0f) }
    var constellations by remember { mutableStateOf<List<Pair<String, Float>>>(emptyList()) }

    // Sensor fusion — accelerometer + magnetometer → azimuth
    DisposableEffect(Unit) {
        val accel  = sm.getDefaultSensor(Sensor.TYPE_ACCELEROMETER)
        val magnet = sm.getDefaultSensor(Sensor.TYPE_MAGNETIC_FIELD)
        val aVals  = FloatArray(3)
        val mVals  = FloatArray(3)
        val rotMat = FloatArray(9)
        val incMat = FloatArray(9)

        val listener = object : SensorEventListener {
            override fun onSensorChanged(e: SensorEvent) {
                when (e.sensor.type) {
                    Sensor.TYPE_ACCELEROMETER  -> System.arraycopy(e.values, 0, aVals, 0, 3)
                    Sensor.TYPE_MAGNETIC_FIELD -> System.arraycopy(e.values, 0, mVals, 0, 3)
                }
                if (SensorManager.getRotationMatrix(rotMat, incMat, aVals, mVals)) {
                    val orient = FloatArray(3)
                    SensorManager.getOrientation(rotMat, orient)
                    az = orient[0]
                }
            }
            override fun onAccuracyChanged(sensor: Sensor?, accuracy: Int) {}
        }
        sm.registerListener(listener, accel,  SensorManager.SENSOR_DELAY_GAME)
        sm.registerListener(listener, magnet, SensorManager.SENSOR_DELAY_GAME)
        onDispose { sm.unregisterListener(listener) }
    }

    // Fetch sky scene from backend
    LaunchedEffect(Unit) {
        val lat = -1.286389
        val lon =  36.817223
        runCatching { Api.service.starmap(lat, lon, null) }
        // Placeholder stars until full AR pipeline is wired
        constellations = List(10) { i -> "★ Star $i" to (i * 36f) }
    }

    // Draw overlay
    Canvas(modifier = Modifier.fillMaxSize()) {
        val cx     = size.width  / 2f
        val cy     = size.height / 2f
        val radius = minOf(cx, cy) * 0.8f
        val starColor  = if (nightMode) Color(1f, 0.1f, 0.1f, 0.9f) else Color.White

        for ((name, bearing) in constellations) {
            val angle = ((bearing.toDouble() - Math.toDegrees(az.toDouble())) + 360.0) % 360.0
            val rad   = Math.toRadians(angle)
            val x     = cx + radius * cos(rad).toFloat()
            val y     = cy + radius * sin(rad).toFloat()

            drawCircle(color = starColor, radius = 4f, center = Offset(x, y))

            // Draw star label using nativeCanvas — correct access via drawIntoCanvas
            drawIntoCanvas { canvas ->
                val paint = Paint().apply {
                    color     = if (nightMode) android.graphics.Color.RED else android.graphics.Color.WHITE
                    textSize  = 28f
                    isAntiAlias = true
                }
                canvas.nativeCanvas.drawText(name, x + 8f, y - 6f, paint)
            }
        }
    }
}