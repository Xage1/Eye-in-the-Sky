package com.eye.sky.ui

import android.annotation.SuppressLint
import android.graphics.Paint
import android.graphics.Typeface
import androidx.camera.core.CameraSelector
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.camera.view.PreviewView
import androidx.compose.animation.*
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.drawscope.DrawScope
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.drawscope.drawIntoCanvas
import androidx.compose.ui.graphics.nativeCanvas
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalLifecycleOwner
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.lifecycle.viewmodel.compose.viewModel
import com.eye.sky.net.*
import com.eye.sky.viewmodel.SkyViewModel
import kotlin.math.*

// ── AR colour palette ─────────────────────────────────────────────────────────
private val COL_STAR_BRIGHT = Color(1f, 1f, 1f, 1f)
private val COL_STAR_DIM    = Color(0.7f, 0.7f, 1f, 0.7f)
private val COL_STAR_NIGHT  = Color(1f, 0.15f, 0.15f, 0.9f)
private val COL_PLANET      = Color(1f, 0.6f, 0.2f, 1f)
private val COL_ISS         = Color(1f, 0.2f, 0.2f, 1f)
private val COL_SATELLITE   = Color(0.2f, 1f, 0.5f, 0.9f)
private val COL_CROSSHAIR   = Color(1f, 1f, 1f, 0.25f)
private val COL_HUD_BG      = Color(0f, 0f, 0.1f, 0.6f)

@SuppressLint("MissingPermission")
@Composable
fun SkyGuideScreen(vm: SkyViewModel = viewModel()) {
    val ctx          = LocalContext.current
    val scene        by vm.scene.collectAsState()
    val nightMode    by vm.nightMode.collectAsState()
    val magLimit     by vm.magLimit.collectAsState()
    val selectedStar by vm.selectedStar.collectAsState()
    val error        by vm.error.collectAsState()

    val density = ctx.resources.displayMetrics
    val screenW = density.widthPixels
    val screenH = density.heightPixels

    LaunchedEffect(Unit) {
        vm.initSensors(ctx)
        vm.fetchLocation(ctx)
        vm.startPolling(screenW, screenH)
    }
    DisposableEffect(Unit) {
        onDispose { vm.stopPolling(); vm.releaseSensors() }
    }

    Box(Modifier.fillMaxSize()) {

        // 1. Live camera
        CameraPreview()

        // 2. AR canvas overlay
        scene?.let { s ->
            AROverlay(scene = s, nightMode = nightMode, onTapStar = { vm.selectStar(it) })
        }

        // 3. Centre crosshair
        CrosshairOverlay()

        // 4. HUD bar
        HudBar(
            scene         = scene,
            nightMode     = nightMode,
            magLimit      = magLimit,
            onNightToggle = { vm.toggleNightMode() },
            onMagChange   = { vm.setMagLimit(it) },
            modifier      = Modifier.align(Alignment.TopCenter),
        )

        // 5. Tap-to-learn bottom sheet
        AnimatedVisibility(
            visible  = selectedStar != null,
            enter    = slideInVertically(initialOffsetY = { it }),
            exit     = slideOutVertically(targetOffsetY  = { it }),
            modifier = Modifier.align(Alignment.BottomCenter),
        ) {
            val star = scene?.stars?.firstOrNull {
                it.name == selectedStar
            }
            star?.let {
                StarDetailPanel(
                    star           = it,
                    constellation  = scene?.constellation,
                    onDismiss      = { vm.selectStar(null) },
                )
            }
        }

        // 6. Error toast
        error?.let {
            Box(Modifier.align(Alignment.BottomCenter).padding(bottom = 16.dp)) {
                Text(
                    "⚠ $it",
                    color    = Color.White,
                    fontSize = 12.sp,
                    modifier = Modifier
                        .background(Color(0.8f, 0.1f, 0.1f, 0.8f), RoundedCornerShape(8.dp))
                        .padding(horizontal = 12.dp, vertical = 6.dp),
                )
            }
        }
    }
}

// ── Camera preview ────────────────────────────────────────────────────────────
@Composable
private fun CameraPreview() {
    val lifecycleOwner = LocalLifecycleOwner.current
    AndroidView(
        factory = { ctx ->
            val view   = PreviewView(ctx)
            val future = ProcessCameraProvider.getInstance(ctx)
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
            }, ctx.mainExecutor)
            view
        },
        modifier = Modifier.fillMaxSize(),
    )
}

// ── AR Canvas overlay ─────────────────────────────────────────────────────────
@Composable
private fun AROverlay(
    scene:     SkySceneResp,
    nightMode: Boolean,
    onTapStar: (String) -> Unit,
) {
    // Only stars with valid screen positions
    val stars = scene.stars.orEmpty().filter { it.screen_x != null && it.screen_y != null }

    Canvas(
        modifier = Modifier
            .fillMaxSize()
            .pointerInput(stars) {
                detectTapGestures { tap ->
                    val hit = stars.minByOrNull { s ->
                        hypot(tap.x - s.screen_x!!.toFloat().toDouble(),
                              tap.y - s.screen_y!!.toFloat().toDouble())
                    }
                    hit?.let { s ->
                        val dist = hypot(
                            tap.x - s.screen_x!!.toFloat().toDouble(),
                            tap.y - s.screen_y!!.toFloat().toDouble(),
                        )
                        if (dist < 60.0) onTapStar(s.name ?: "")
                    }
                }
            }
    ) {
        // Stars
        stars.forEach { drawStar(it, nightMode) }

        // Planets
        scene.planets.orEmpty().filter { it.screen_x != null }.forEach {
            drawPlanet(it, nightMode)
        }

        // ISS
        scene.iss?.let { iss ->
            if (iss.visible == true && iss.altitude_deg != null && iss.azimuth_deg != null) {
                drawIssMarker(iss, nightMode)
            }
        }

        // Satellites — no screen_x in satellite model, draw relative to centre
        // (satellites need a separate endpoint for screen projection)
    }
}

// ── Star drawing ──────────────────────────────────────────────────────────────
private fun DrawScope.drawStar(star: StarDto, nightMode: Boolean) {
    val x   = star.screen_x!!.toFloat()
    val y   = star.screen_y!!.toFloat()
    val mag = star.magnitude

    // Radius inversely proportional to magnitude
    val radius = (6.0 - mag.coerceIn(-1.0, 6.0)).toFloat().coerceIn(1.5f, 9f)
    val col    = if (nightMode) COL_STAR_NIGHT
                 else if (mag < 2.0) COL_STAR_BRIGHT
                 else COL_STAR_DIM

    drawCircle(color = col, radius = radius, center = Offset(x, y))

    // Label bright named stars (mag < 2.5)
    if (star.name != null && mag < 2.5) {
        drawIntoCanvas { canvas ->
            canvas.nativeCanvas.drawText(
                star.name,
                x + radius + 5f,
                y + 8f,
                Paint().apply {
                    color = if (nightMode) android.graphics.Color.rgb(255, 80, 80)
                            else android.graphics.Color.WHITE
                    textSize    = 26f
                    isAntiAlias = true
                    setShadowLayer(4f, 0f, 0f, android.graphics.Color.BLACK)
                }
            )
        }
    }
}

// ── Planet drawing ────────────────────────────────────────────────────────────
private fun DrawScope.drawPlanet(planet: PlanetDto, nightMode: Boolean) {
    val x   = planet.screen_x!!.toFloat()
    val y   = planet.screen_y!!.toFloat()
    val col = if (nightMode) Color(1f, 0.5f, 0.1f, 0.9f) else COL_PLANET

    drawCircle(color = col, radius = 9f, center = Offset(x, y))
    drawCircle(color = col.copy(alpha = 0.3f), radius = 16f,
               center = Offset(x, y), style = Stroke(1.5f))

    drawIntoCanvas { canvas ->
        canvas.nativeCanvas.drawText(
            planet.name,
            x + 14f, y + 8f,
            Paint().apply {
                color = if (nightMode) android.graphics.Color.rgb(255, 160, 60)
                        else android.graphics.Color.rgb(255, 180, 50)
                textSize       = 28f
                isAntiAlias    = true
                isFakeBoldText = true
                setShadowLayer(4f, 0f, 0f, android.graphics.Color.BLACK)
            }
        )
    }
}

// ── ISS drawing (altitude/azimuth only — no screen projection from backend) ───
private fun DrawScope.drawIssMarker(iss: IssDto, nightMode: Boolean) {
    // ISS doesn't have screen_x/y — place it at a fixed HUD position
    // Full projection needs a dedicated satellite screen-coords endpoint
    val x   = size.width  * 0.85f
    val y   = size.height * 0.15f
    val col = if (nightMode) Color(0.9f, 0.1f, 0.1f, 1f) else COL_ISS

    drawLine(col, Offset(x - 12f, y), Offset(x + 12f, y), strokeWidth = 3f)
    drawLine(col, Offset(x, y - 6f),  Offset(x, y + 6f),  strokeWidth = 3f)
    drawCircle(col.copy(alpha = 0.35f), radius = 18f,
               center = Offset(x, y), style = Stroke(1f))

    drawIntoCanvas { canvas ->
        canvas.nativeCanvas.drawText(
            "ISS ↑${iss.altitude_deg?.let { "%.0f°".format(it) } ?: ""}",
            x + 22f, y + 8f,
            Paint().apply {
                color          = if (nightMode) android.graphics.Color.rgb(255, 60, 60)
                                 else android.graphics.Color.rgb(255, 80, 80)
                textSize       = 26f
                isAntiAlias    = true
                isFakeBoldText = true
                setShadowLayer(4f, 0f, 0f, android.graphics.Color.BLACK)
            }
        )
    }
}

// ── Crosshair ─────────────────────────────────────────────────────────────────
@Composable
private fun CrosshairOverlay() {
    Canvas(Modifier.fillMaxSize()) {
        val cx = size.width / 2f; val cy = size.height / 2f
        val len = 30f; val gap = 10f
        drawLine(COL_CROSSHAIR, Offset(cx - len - gap, cy), Offset(cx - gap, cy), 1.5f)
        drawLine(COL_CROSSHAIR, Offset(cx + gap, cy), Offset(cx + len + gap, cy), 1.5f)
        drawLine(COL_CROSSHAIR, Offset(cx, cy - len - gap), Offset(cx, cy - gap), 1.5f)
        drawLine(COL_CROSSHAIR, Offset(cx, cy + gap), Offset(cx, cy + len + gap), 1.5f)
        drawCircle(COL_CROSSHAIR, radius = 3f, center = Offset(cx, cy))
    }
}

// ── HUD bar ───────────────────────────────────────────────────────────────────
@Composable
private fun HudBar(
    scene: SkySceneResp?, nightMode: Boolean, magLimit: Float,
    onNightToggle: () -> Unit, onMagChange: (Float) -> Unit, modifier: Modifier,
) {
    val tc = if (nightMode) Color(1f, 0.4f, 0.4f, 0.8f) else Color.White

    Column(modifier.fillMaxWidth().background(COL_HUD_BG).padding(horizontal = 12.dp, vertical = 6.dp)) {

        Row(Modifier.fillMaxWidth(), Arrangement.SpaceBetween, Alignment.CenterVertically) {
            // Constellation name
            Text(
                scene?.constellation?.name ?: "Eye in the Sky",
                color      = tc,
                fontSize   = 14.sp,
                fontWeight = FontWeight.Medium,
            )
            // Moon phase
            scene?.moon_phase?.let {
                Text(
                    "${it.phase_name ?: ""} ${it.illumination_pct?.let { p -> "%.0f%%".format(p) } ?: ""}",
                    color    = Color(0.9f, 0.9f, 0.6f, 0.85f),
                    fontSize = 12.sp,
                )
            }
            // Night mode toggle
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text("🔴", fontSize = 12.sp)
                Switch(
                    checked         = nightMode,
                    onCheckedChange = { onNightToggle() },
                    modifier        = Modifier.height(24.dp).padding(start = 4.dp),
                    colors          = SwitchDefaults.colors(
                        checkedThumbColor = Color.Red,
                        checkedTrackColor = Color(0.5f, 0f, 0f, 0.8f),
                    ),
                )
            }
        }

        // Magnitude limit slider
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text("✦", color = tc.copy(alpha = 0.7f), fontSize = 11.sp,
                 modifier = Modifier.width(20.dp))
            Slider(
                value         = magLimit,
                onValueChange = onMagChange,
                valueRange    = 2f..6.5f,
                modifier      = Modifier.weight(1f).height(24.dp),
                colors        = SliderDefaults.colors(
                    thumbColor       = if (nightMode) Color.Red else Color.White,
                    activeTrackColor = if (nightMode) Color(0.6f, 0f, 0f) else Color(0.5f, 0.5f, 1f),
                ),
            )
            Text("%.1f".format(magLimit), color = tc.copy(alpha = 0.7f),
                 fontSize = 11.sp, modifier = Modifier.width(32.dp))
        }

        // Counts row
        Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
            val sc   = scene?.stars?.size ?: 0
            val pc   = scene?.planets?.size ?: 0
            val satc = scene?.satellites?.size ?: 0
            val col2 = tc.copy(alpha = 0.6f)
            Text("★ $sc", color = col2, fontSize = 10.sp)
            if (pc > 0) Text("◉ $pc planets", color = col2, fontSize = 10.sp)
            if (satc > 0) Text("⊕ $satc sats", color = col2, fontSize = 10.sp)
            scene?.iss?.let {
                if (it.visible == true)
                    Text("▲ ISS", color = Color(1f, 0.3f, 0.3f, 0.85f), fontSize = 10.sp)
            }
        }
    }
}

// ── Star detail panel ─────────────────────────────────────────────────────────
@Composable
private fun StarDetailPanel(
    star:          StarDto,
    constellation: ConstellationDto?,
    onDismiss:     () -> Unit,
) {
    Card(
        modifier = Modifier.fillMaxWidth().padding(12.dp),
        shape    = RoundedCornerShape(topStart = 16.dp, topEnd = 16.dp),
        colors   = CardDefaults.cardColors(containerColor = Color(0.04f, 0.04f, 0.14f, 0.96f)),
    ) {
        Column(Modifier.padding(16.dp)) {
            Row(Modifier.fillMaxWidth(), Arrangement.SpaceBetween, Alignment.CenterVertically) {
                Column {
                    Text(
                        star.name ?: "Unknown Star",
                        color      = Color.White,
                        fontSize   = 20.sp,
                        fontWeight = FontWeight.Bold,
                    )
                    star.constellation?.takeIf { it.isNotBlank() }?.let {
                        Text(it, color = Color(0.6f, 0.6f, 1f, 0.9f), fontSize = 13.sp)
                    }
                }
                TextButton(onClick = onDismiss) {
                    Text("✕", color = Color.White.copy(alpha = 0.6f))
                }
            }

            Spacer(Modifier.height(8.dp))
            HorizontalDivider(color = Color.White.copy(alpha = 0.1f))
            Spacer(Modifier.height(8.dp))

            Row(horizontalArrangement = Arrangement.spacedBy(24.dp)) {
                StatChip("Magnitude", "%.2f".format(star.magnitude))
                StatChip("Altitude",  "%.1f°".format(star.altitude_deg))
                StatChip("Azimuth",   "%.1f°".format(star.azimuth_deg))
            }

            // Constellation mythology from scene
            constellation?.let { c ->
                if (c.name == star.constellation && c.myth != null) {
                    Spacer(Modifier.height(12.dp))
                    Text("Mythology", color = Color(0.6f, 0.6f, 1f),
                         fontSize = 12.sp, fontWeight = FontWeight.SemiBold)
                    Spacer(Modifier.height(4.dp))
                    Text(c.myth, color = Color.White.copy(alpha = 0.8f), fontSize = 13.sp)
                }
            }
        }
    }
}

@Composable
private fun StatChip(label: String, value: String) {
    Column {
        Text(label, color = Color.White.copy(alpha = 0.45f), fontSize = 10.sp)
        Text(value, color = Color.White, fontSize = 14.sp, fontWeight = FontWeight.Medium)
    }
}