package ke.eyesky.app

import androidx.compose.animation.core.FastOutSlowInEasing
import androidx.compose.animation.core.LinearEasing
import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.size
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import kotlinx.coroutines.delay
import kotlin.math.cos
import kotlin.math.sin

private val SPLASH_BG = Color(0xFF070B1A)
private val SPLASH_GOLD = Color(0xFFF2C14E)
private val SPLASH_CYAN = Color(0xFF6FD3E8)

/** Full-screen intro shown for ~2 s on launch, then fades away. Tap to skip. */
@Composable
fun SplashOverlay() {
    var show by remember { mutableStateOf(true) }
    LaunchedEffect(Unit) {
        delay(2200)
        show = false
    }
    val a by animateFloatAsState(
        targetValue = if (show) 1f else 0f,
        animationSpec = tween(600, easing = FastOutSlowInEasing),
        label = "splashAlpha"
    )
    if (a <= 0.01f && !show) return

    val inf = rememberInfiniteTransition(label = "splash")
    val spin by inf.animateFloat(
        initialValue = 0f, targetValue = 360f,
        animationSpec = infiniteRepeatable(tween(14000, easing = LinearEasing)),
        label = "spin"
    )
    val pulse by inf.animateFloat(
        initialValue = 0.55f, targetValue = 1f,
        animationSpec = infiniteRepeatable(tween(1100, easing = FastOutSlowInEasing), RepeatMode.Reverse),
        label = "pulse"
    )
    val appear by animateFloatAsState(1f, tween(900, easing = FastOutSlowInEasing), label = "appear")

    Box(
        Modifier.fillMaxSize().alpha(a).background(SPLASH_BG).clickable { show = false },
        contentAlignment = Alignment.Center
    ) {
        // faint fixed star dust
        Canvas(Modifier.fillMaxSize()) {
            var seed = 7L
            for (i in 0 until 90) {
                seed = (seed * 1103515245L + 12345L) and 0x7fffffffL
                val x = (seed % 1000L) / 1000f * size.width
                seed = (seed * 1103515245L + 12345L) and 0x7fffffffL
                val y = (seed % 1000L) / 1000f * size.height
                seed = (seed * 1103515245L + 12345L) and 0x7fffffffL
                val r = 0.6f + (seed % 100L) / 100f * 1.6f
                val tw = if (i % 3 == 0) pulse else 0.7f
                drawCircle(Color.White.copy(alpha = 0.25f * tw), r, Offset(x, y))
            }
        }
        Column(horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.Center) {
            Canvas(Modifier.size(150.dp).alpha(appear)) {
                val c = Offset(size.width / 2f, size.height / 2f)
                val r = size.minDimension / 2f
                drawCircle(SPLASH_GOLD.copy(alpha = 0.9f), r * 0.92f, c, style = Stroke(3.5f, cap = StrokeCap.Round))
                drawCircle(SPLASH_CYAN.copy(alpha = 0.5f), r * 0.66f, c, style = Stroke(2f))
                // orbiting dot
                val rad = Math.toRadians(spin.toDouble())
                val o = Offset(c.x + (r * 0.92f * cos(rad)).toFloat(), c.y + (r * 0.92f * sin(rad)).toFloat())
                drawCircle(SPLASH_CYAN, 7f, o)
                // pupil star
                drawCircle(SPLASH_GOLD.copy(alpha = 0.25f * pulse), r * 0.30f, c)
                drawCircle(SPLASH_GOLD, r * 0.13f, c)
                for (k in 0 until 4) {
                    val ang = Math.toRadians(k * 90.0 + 45.0)
                    val e = Offset(c.x + (r * 0.34f * cos(ang)).toFloat(), c.y + (r * 0.34f * sin(ang)).toFloat())
                    drawLine(SPLASH_GOLD.copy(alpha = 0.8f), c, e, strokeWidth = 2f, cap = StrokeCap.Round)
                }
            }
            Spacer(Modifier.height(28.dp))
            Text(
                "EyeSky",
                color = SPLASH_GOLD.copy(alpha = appear),
                fontSize = 38.sp,
                fontWeight = FontWeight.Light,
                letterSpacing = 6.sp
            )
            Spacer(Modifier.height(8.dp))
            Text(
                "The sky, as it is right now",
                color = Color.White.copy(alpha = 0.6f * appear),
                fontSize = 14.sp,
                letterSpacing = 1.sp
            )
        }
    }
}
