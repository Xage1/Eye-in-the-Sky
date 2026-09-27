package com.eye.sky.viewmodel

import android.annotation.SuppressLint
import android.content.Context
import android.hardware.Sensor
import android.hardware.SensorEvent
import android.hardware.SensorEventListener
import android.hardware.SensorManager
import android.location.Location
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.eye.sky.net.Api
import com.eye.sky.net.SkySceneResp
import com.google.android.gms.location.LocationServices
import com.google.android.gms.location.Priority
import com.google.android.gms.tasks.CancellationTokenSource
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import kotlin.math.toDegrees

class SkyViewModel : ViewModel() {

    // ── Public state ──────────────────────────────────────────────────────────
    private val _scene   = MutableStateFlow<SkySceneResp?>(null)
    val scene: StateFlow<SkySceneResp?> = _scene

    private val _error   = MutableStateFlow<String?>(null)
    val error: StateFlow<String?> = _error

    private val _loading = MutableStateFlow(false)
    val loading: StateFlow<Boolean> = _loading

    // Night mode — red tint to preserve dark adaptation
    private val _nightMode = MutableStateFlow(true)
    val nightMode: StateFlow<Boolean> = _nightMode

    // Magnitude limit slider (2.0 = only brightest, 6.5 = all naked-eye)
    private val _magLimit = MutableStateFlow(5.5f)
    val magLimit: StateFlow<Float> = _magLimit

    // Selected star for tap-to-learn panel
    private val _selectedStar = MutableStateFlow<String?>(null)
    val selectedStar: StateFlow<String?> = _selectedStar

    // ── Orientation (radians from sensor fusion) ──────────────────────────────
    var azRad   = 0f; private set
    var pitchRad = 0f; private set
    var rollRad  = 0f; private set

    // ── GPS ───────────────────────────────────────────────────────────────────
    private var lat = -1.286389   // Nairobi default until GPS resolves
    private var lon =  36.817223

    // ── Polling ───────────────────────────────────────────────────────────────
    private var pollJob: Job? = null
    private val POLL_INTERVAL_MS = 2000L  // fetch scene every 2 seconds

    // ── Sensor listener ───────────────────────────────────────────────────────
    private var sensorManager: SensorManager? = null
    private var sensorListener: SensorEventListener? = null
    private val aVals = FloatArray(3)
    private val mVals = FloatArray(3)
    private val rotMat = FloatArray(9)
    private val incMat = FloatArray(9)
    private val orient = FloatArray(3)

    // ── Init sensors ──────────────────────────────────────────────────────────
    fun initSensors(context: Context) {
        sensorManager = context.getSystemService(SensorManager::class.java)
        val accel  = sensorManager?.getDefaultSensor(Sensor.TYPE_ACCELEROMETER)
        val magnet = sensorManager?.getDefaultSensor(Sensor.TYPE_MAGNETIC_FIELD)

        val listener = object : SensorEventListener {
            override fun onSensorChanged(e: SensorEvent) {
                when (e.sensor.type) {
                    Sensor.TYPE_ACCELEROMETER  -> System.arraycopy(e.values, 0, aVals, 0, 3)
                    Sensor.TYPE_MAGNETIC_FIELD -> System.arraycopy(e.values, 0, mVals, 0, 3)
                }
                if (SensorManager.getRotationMatrix(rotMat, incMat, aVals, mVals)) {
                    SensorManager.getOrientation(rotMat, orient)
                    azRad    = orient[0]
                    pitchRad = orient[1]
                    rollRad  = orient[2]
                }
            }
            override fun onAccuracyChanged(sensor: Sensor?, accuracy: Int) {}
        }
        sensorListener = listener
        sensorManager?.registerListener(listener, accel,  SensorManager.SENSOR_DELAY_GAME)
        sensorManager?.registerListener(listener, magnet, SensorManager.SENSOR_DELAY_GAME)
    }

    fun releaseSensors() {
        sensorListener?.let { sensorManager?.unregisterListener(it) }
        sensorListener = null
    }

    // ── GPS ───────────────────────────────────────────────────────────────────
    @SuppressLint("MissingPermission")
    fun fetchLocation(context: Context) {
        val client = LocationServices.getFusedLocationProviderClient(context)
        val cts    = CancellationTokenSource()
        client.getCurrentLocation(Priority.PRIORITY_BALANCED_POWER_ACCURACY, cts.token)
            .addOnSuccessListener { loc: Location? ->
                loc?.let {
                    lat = it.latitude
                    lon = it.longitude
                }
            }
    }

    // ── Scene polling ─────────────────────────────────────────────────────────
    fun startPolling(screenW: Int, screenH: Int) {
        pollJob?.cancel()
        pollJob = viewModelScope.launch {
            while (true) {
                fetchScene(screenW, screenH)
                delay(POLL_INTERVAL_MS)
            }
        }
    }

    fun stopPolling() {
        pollJob?.cancel()
        pollJob = null
    }

    private suspend fun fetchScene(screenW: Int, screenH: Int) {
        val azDeg  = toDegrees(azRad.toDouble()).let { if (it < 0) it + 360.0 else it }
        val altDeg = toDegrees(-pitchRad.toDouble())  // pitch up = positive altitude

        runCatching {
            Api.service.skyScene(
                lat       = lat,
                lon       = lon,
                az        = azDeg,
                alt       = altDeg,
                roll      = toDegrees(rollRad.toDouble()),
                screenW   = screenW,
                screenH   = screenH,
                magLimit  = _magLimit.value.toDouble(),
                planets   = true,
                satellites = true,
                iss       = true,
                weather   = false,
            )
        }.onSuccess { scene ->
            _scene.value = scene
            _error.value = null
        }.onFailure { err ->
            _error.value = err.message
        }
    }

    // ── Controls ──────────────────────────────────────────────────────────────
    fun toggleNightMode() { _nightMode.value = !_nightMode.value }
    fun setMagLimit(v: Float) { _magLimit.value = v }
    fun selectStar(name: String?) { _selectedStar.value = name }

    override fun onCleared() {
        super.onCleared()
        releaseSensors()
        stopPolling()
    }
}