package ke.eyesky.app

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import kotlin.random.Random

/**
 * EyeSky design tokens.
 *   Gold   = brand, stars
 *   Cyan   = live data and interaction (satellites, orbits, links)
 *   Violet = premium and JWST only
 * Night mode swaps everything to red on black to protect dark adaptation.
 */
object Sky {
    val Night = Color(0xFF070B1A)
    val Surface = Color(0xFF0F1630)
    val SurfaceHigh = Color(0xFF18213F)
    val Ink = Color(0xFFE8ECF8)
    val InkSoft = Color(0xFFA7B0CC)
    val Gold = Color(0xFFFFC857)
    val Cyan = Color(0xFF4DD0E1)
    val Violet = Color(0xFFB39DFF)
    val Alert = Color(0xFFFF6B6B)
}

private val NormalScheme = darkColorScheme(
    primary = Sky.Gold, onPrimary = Color(0xFF1A1300),
    secondary = Sky.Cyan, onSecondary = Color(0xFF00262B),
    tertiary = Sky.Violet, onTertiary = Color(0xFF1B0B4D),
    background = Sky.Night, onBackground = Sky.Ink,
    surface = Sky.Surface, onSurface = Sky.Ink,
    surfaceVariant = Sky.SurfaceHigh, onSurfaceVariant = Sky.InkSoft,
    outline = Color(0xFF3A456B), error = Sky.Alert
)

private val RedScheme = darkColorScheme(
    primary = Color(0xFFFF4D4D), onPrimary = Color(0xFF000000),
    secondary = Color(0xFFCC3333), onSecondary = Color(0xFF000000),
    tertiary = Color(0xFF994040), onTertiary = Color(0xFF000000),
    background = Color(0xFF000000), onBackground = Color(0xFFFF6666),
    surface = Color(0xFF120000), onSurface = Color(0xFFFF6666),
    surfaceVariant = Color(0xFF1E0000), onSurfaceVariant = Color(0xFFB34747),
    outline = Color(0xFF662222), error = Color(0xFFFF8080)
)

@Composable
fun EyeSkyTheme(nightVision: Boolean, content: @Composable () -> Unit) {
    MaterialTheme(colorScheme = if (nightVision) RedScheme else NormalScheme, content = content)
}

/** A fixed, gently twinkling-looking field of stars behind the screens. */
@Composable
fun Starfield(modifier: Modifier = Modifier) {
    val accent = MaterialTheme.colorScheme.primary
    val ink = MaterialTheme.colorScheme.onBackground
    Canvas(modifier = modifier.fillMaxSize()) {
        val rnd = Random(7)
        repeat(90) {
            val x = rnd.nextFloat() * size.width
            val y = rnd.nextFloat() * size.height
            val r = (0.4f + rnd.nextFloat() * 1.1f).dp.toPx()
            val c = if (rnd.nextInt(6) == 0) accent else ink
            drawCircle(
                color = c.copy(alpha = 0.15f + rnd.nextFloat() * 0.45f),
                radius = r,
                center = Offset(x, y)
            )
        }
    }
}
