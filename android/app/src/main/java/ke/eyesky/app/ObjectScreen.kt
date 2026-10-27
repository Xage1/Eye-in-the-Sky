package ke.eyesky.app

import androidx.activity.compose.BackHandler
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.systemBarsPadding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import org.json.JSONObject
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.unit.dp
import kotlin.math.PI
import kotlin.math.cos
import kotlin.math.floor
import kotlin.math.roundToInt

/** What the user tapped. kind is a body name ("jupiter") or "star:<HR number>". */
class ObjectTarget(val kind: String, val title: String, val detail: String)

class Facts(val blurb: String, val rows: List<Pair<String, String>>)

/** Approximate B-V colour index of the brightest stars (Yale Bright Star Catalogue). Real data comes next. */
private val STAR_BV = mapOf(
    2491 to -0.01f, 2326 to 0.15f, 5340 to 1.23f, 5459 to 0.71f, 7001 to 0.00f, 1708 to 0.80f,
    1713 to -0.03f, 2943 to 0.42f, 2061 to 1.85f, 472 to -0.16f, 5267 to -0.23f, 7557 to 0.22f,
    4730 to -0.24f, 1457 to 1.54f, 6134 to 1.83f, 5056 to -0.23f, 2990 to 1.00f, 8728 to 0.09f,
    7924 to 0.09f, 4853 to -0.23f, 3982 to -0.11f, 2618 to -0.21f, 2891 to 0.03f, 6527 to -0.22f,
    1790 to -0.22f, 1791 to -0.13f
)

private const val DEG = "°"
private const val TIMES = "×"

private val FACTS: Map<String, Facts> = mapOf(
    "sun" to Facts(
        "The star at the centre of our solar system: a ball of hot plasma held together by its own gravity. " +
            "It holds 99.86% of all the mass in the solar system and powers almost all life on Earth.",
        listOf(
            "Type" to "G2V main-sequence star (yellow dwarf)",
            "Diameter" to "1,392,700 km (109 $TIMES Earth)",
            "Mass" to "1.989 $TIMES 10³⁰ kg (333,000 $TIMES Earth)",
            "Surface gravity" to "274 m/s² (28 $TIMES Earth)",
            "Surface temperature" to "about 5,500 ${DEG}C",
            "Core temperature" to "about 15 million ${DEG}C",
            "Rotation" to "about 25 days at the equator, about 35 near the poles",
            "Age" to "about 4.6 billion years",
            "Composition" to "about 73% hydrogen, 25% helium",
            "Distance from Earth" to "149.6 million km on average (light takes 8 min 20 s)",
            "Luminosity" to "3.83 $TIMES 10²⁶ W",
            "Safety" to "Never look at the Sun directly, and keep the camera off it for long."
        )
    ),
    "moon" to Facts(
        "Earth's only natural satellite and the fifth largest moon in the solar system. " +
            "It is tidally locked, so the same face always points toward Earth.",
        listOf(
            "Diameter" to "3,475 km (27% of Earth)",
            "Mass" to "7.34 $TIMES 10²² kg (1.2% of Earth)",
            "Surface gravity" to "1.62 m/s² (16.5% of Earth)",
            "Distance from Earth" to "384,400 km on average (356,500 to 406,700 km)",
            "Orbital period" to "27.32 days",
            "Phase cycle" to "29.53 days (new moon to new moon)",
            "Surface temperature" to "-173 to 127 ${DEG}C",
            "Atmosphere" to "virtually none (a very thin exosphere)",
            "Age" to "about 4.5 billion years",
            "Drifting away" to "about 3.8 cm farther from Earth every year"
        )
    ),
    "mercury" to Facts(
        "The smallest planet and the closest to the Sun. With almost no atmosphere to hold heat, " +
            "it swings from blazing days to freezing nights.",
        listOf(
            "Diameter" to "4,879 km (38% of Earth)",
            "Mass" to "3.30 $TIMES 10²³ kg (5.5% of Earth)",
            "Surface gravity" to "3.70 m/s² (38% of Earth)",
            "Distance from Sun" to "57.9 million km (0.39 AU)",
            "Year" to "88 Earth days",
            "Rotation" to "58.6 Earth days",
            "Day (sunrise to sunrise)" to "176 Earth days",
            "Moons" to "0",
            "Temperature" to "-180 to 430 ${DEG}C",
            "Atmosphere" to "only a trace exosphere"
        )
    ),
    "venus" to Facts(
        "Earth's sister in size, and the hottest planet. A thick carbon dioxide atmosphere traps heat so strongly " +
            "that its surface is hotter than Mercury's. It is the brightest planet in our sky.",
        listOf(
            "Diameter" to "12,104 km (95% of Earth)",
            "Mass" to "4.87 $TIMES 10²⁴ kg (81.5% of Earth)",
            "Surface gravity" to "8.87 m/s² (90% of Earth)",
            "Distance from Sun" to "108.2 million km (0.72 AU)",
            "Year" to "224.7 Earth days",
            "Rotation" to "243 Earth days, backwards (retrograde)",
            "Day (sunrise to sunrise)" to "117 Earth days",
            "Moons" to "0",
            "Surface temperature" to "about 465 ${DEG}C",
            "Atmosphere" to "about 96.5% carbon dioxide, about 92 $TIMES Earth's surface pressure"
        )
    ),
    "mars" to Facts(
        "The Red Planet, coloured by iron oxide dust. It has the tallest volcano and the deepest canyon known in the solar system.",
        listOf(
            "Diameter" to "6,779 km (53% of Earth)",
            "Mass" to "6.42 $TIMES 10²³ kg (10.7% of Earth)",
            "Surface gravity" to "3.71 m/s² (38% of Earth)",
            "Distance from Sun" to "227.9 million km (1.52 AU)",
            "Year" to "687 Earth days",
            "Day" to "24 h 37 min (a Martian sol is 24 h 39 min)",
            "Moons" to "2 (Phobos and Deimos)",
            "Temperature" to "-153 to 20 ${DEG}C",
            "Atmosphere" to "about 95% carbon dioxide, under 1% of Earth's pressure",
            "Olympus Mons" to "about 21.9 km high, roughly 2.5 $TIMES Mount Everest"
        )
    ),
    "jupiter" to Facts(
        "The largest planet: a gas giant more massive than all the other planets combined. " +
            "Its Great Red Spot is a storm wider than Earth that has raged for well over a century.",
        listOf(
            "Diameter" to "139,820 km (11.2 $TIMES Earth)",
            "Mass" to "1.898 $TIMES 10²⁷ kg (318 $TIMES Earth)",
            "Gravity at cloud tops" to "24.8 m/s² (2.5 $TIMES Earth)",
            "Distance from Sun" to "778.5 million km (5.20 AU)",
            "Year" to "11.86 Earth years",
            "Day" to "9 h 56 min (the fastest spinner of all the planets)",
            "Moons" to "95 confirmed (as of 2025)",
            "Cloud-top temperature" to "about -108 ${DEG}C",
            "Composition" to "about 90% hydrogen, 10% helium",
            "Rings" to "a faint, dusty ring system"
        )
    ),
    "saturn" to Facts(
        "The ring planet. Its bright rings are made mostly of water ice, from dust grains to boulders. " +
            "Saturn is so light for its size that it would float in water, if a bathtub that big existed.",
        listOf(
            "Diameter" to "116,460 km (9.45 $TIMES Earth)",
            "Mass" to "5.68 $TIMES 10²⁶ kg (95 $TIMES Earth)",
            "Gravity at cloud tops" to "10.4 m/s² (107% of Earth)",
            "Distance from Sun" to "1.43 billion km (9.58 AU)",
            "Year" to "29.45 Earth years",
            "Day" to "10 h 34 min",
            "Moons" to "274 confirmed (as of 2025)",
            "Temperature" to "about -178 ${DEG}C at the 1-bar level",
            "Average density" to "0.687 g/cm³ (water is 1.0)",
            "Rings" to "span about 282,000 km yet are mostly only about 10 m thick"
        )
    ),
    "uranus" to Facts(
        "An ice giant tipped on its side, so its poles take turns facing the Sun during its long year. " +
            "Methane in its atmosphere gives it a pale blue-green colour.",
        listOf(
            "Diameter" to "50,724 km (4.0 $TIMES Earth)",
            "Mass" to "8.68 $TIMES 10²⁵ kg (14.5 $TIMES Earth)",
            "Gravity at cloud tops" to "8.69 m/s² (89% of Earth)",
            "Distance from Sun" to "2.87 billion km (19.2 AU)",
            "Year" to "84 Earth years",
            "Day" to "17 h 14 min (backwards)",
            "Axial tilt" to "97.8$DEG",
            "Moons" to "29 (as of 2025)",
            "Temperature" to "about -224 ${DEG}C, the coldest planetary atmosphere measured",
            "Discovered" to "1781 by William Herschel"
        )
    ),
    "neptune" to Facts(
        "The farthest planet, a deep blue ice giant with the fastest winds in the solar system. " +
            "It was found by mathematics before anyone saw it.",
        listOf(
            "Diameter" to "49,244 km (3.9 $TIMES Earth)",
            "Mass" to "1.02 $TIMES 10²⁶ kg (17.1 $TIMES Earth)",
            "Gravity at cloud tops" to "11.2 m/s² (114% of Earth)",
            "Distance from Sun" to "4.50 billion km (30.1 AU)",
            "Year" to "164.8 Earth years",
            "Day" to "16 h 6 min",
            "Moons" to "16 (as of 2025)",
            "Winds" to "over 2,000 km/h",
            "Temperature" to "about -214 ${DEG}C",
            "Discovered" to "1846, from predictions by Le Verrier and Adams; first seen by Galle"
        )
    )
)

/** Moon phase as a fraction of the cycle (0 = new, 0.5 = full), from a known new moon. */
fun moonPhaseFraction(nowMs: Long): Float {
    val jd = nowMs / 86400000.0 + 2440587.5
    val cycle = (jd - 2451550.1) / 29.530588853
    return (cycle - floor(cycle)).toFloat()
}

private fun moonPhaseName(f: Float): String = when {
    f < 0.03f || f > 0.97f -> "New Moon"
    f < 0.22f -> "Waxing Crescent"
    f < 0.28f -> "First Quarter"
    f < 0.47f -> "Waxing Gibbous"
    f < 0.53f -> "Full Moon"
    f < 0.72f -> "Waning Gibbous"
    f < 0.78f -> "Last Quarter"
    else -> "Waning Crescent"
}

@Composable
fun ObjectScreen(target: ObjectTarget, onClose: () -> Unit) {
    BackHandler(onBack = onClose)

    val ink = MaterialTheme.colorScheme.onBackground
    val gold = MaterialTheme.colorScheme.primary
    val cyan = MaterialTheme.colorScheme.secondary
    val dim = MaterialTheme.colorScheme.onSurfaceVariant
    val bg = MaterialTheme.colorScheme.background
    val line = MaterialTheme.colorScheme.outline

    val key = target.kind.substringBefore(":")
    val hr = target.kind.substringAfter(":", "").toIntOrNull()
    val isStar = key == "star"
    val spec = BodyCatalog.specs[key] ?: BodyCatalog.star
    var info by remember(target.kind) { mutableStateOf<JSONObject?>(null) }
    var failed by remember(target.kind) { mutableStateOf(false) }
    LaunchedEffect(target.kind) {
        try { info = Api.objectInfo(key.let { if (isStar) target.kind else it }) } catch (e: Exception) { failed = true }
    }
    val bv = if (info != null && info!!.has("ci") && !info!!.isNull("ci")) info!!.optDouble("ci").toFloat() else (STAR_BV[hr] ?: 0.65f)
    val color = starRgb(bv)
    val phase = moonPhaseFraction(System.currentTimeMillis())
    val facts = FACTS[key]

    Box(Modifier.fillMaxSize().background(bg).pointerInput(Unit) { }) {
        Column(Modifier.fillMaxSize()) {
            Box(Modifier.fillMaxWidth().weight(0.52f)) {
                BodyView(spec, color, phase, Modifier.fillMaxSize())
                TextButton(
                    onClick = onClose,
                    modifier = Modifier.systemBarsPadding().align(Alignment.TopStart).padding(start = 8.dp)
                ) { Text("‹ Close", color = ink) }
                Text(
                    "drag to spin  ·  pinch to zoom",
                    color = dim,
                    style = MaterialTheme.typography.labelSmall,
                    modifier = Modifier.align(Alignment.BottomCenter).padding(bottom = 8.dp)
                )
            }
            Column(
                Modifier.fillMaxWidth().weight(0.48f).verticalScroll(rememberScrollState()).padding(16.dp)
            ) {
                Text(target.title, style = MaterialTheme.typography.headlineMedium, color = gold)
                Spacer(Modifier.height(4.dp))

                Section("Right now", cyan)
                Text(target.detail, style = MaterialTheme.typography.bodyLarge, color = ink)
                val secs = info?.optJSONArray("sections")
                if (secs != null) {
                    for (i in 0 until secs.length()) {
                        val s = secs.getJSONObject(i)
                        Spacer(Modifier.height(16.dp))
                        Section(s.optString("title"), cyan)
                        val rs = s.getJSONArray("rows")
                        for (j in 0 until rs.length()) {
                            HorizontalDivider(color = line.copy(alpha = 0.4f))
                            Row2(rs.getJSONArray(j).getString(0), rs.getJSONArray(j).getString(1), dim, ink)
                        }
                    }
                } else if (failed) {
                    Spacer(Modifier.height(8.dp))
                    Text("Live details unavailable (is the backend running?)", color = dim, style = MaterialTheme.typography.bodySmall)
                }

                if (key == "moon") {
                    val lit = ((1.0 - cos(2.0 * PI * phase)) / 2.0 * 100.0).roundToInt()
                    Spacer(Modifier.height(8.dp))
                    Row2("Phase", moonPhaseName(phase) + ", about " + lit + "% lit", dim, ink)
                }

                if (facts != null) {
                    Spacer(Modifier.height(16.dp))
                    Section("About", cyan)
                    Text(facts.blurb, style = MaterialTheme.typography.bodyMedium, color = ink)
                    Spacer(Modifier.height(16.dp))
                    Section("Facts", cyan)
                    for ((k, v) in facts.rows) {
                        HorizontalDivider(color = line.copy(alpha = 0.4f))
                        Row2(k, v, dim, ink)
                    }
                }
                Spacer(Modifier.height(24.dp))
            }
        }
    }
}

@Composable
private fun Section(title: String, color: androidx.compose.ui.graphics.Color) {
    Spacer(Modifier.height(6.dp))
    Text(title.uppercase(), style = MaterialTheme.typography.labelLarge, color = color)
    Spacer(Modifier.height(4.dp))
}

@Composable
private fun Row2(
    label: String,
    value: String,
    labelColor: androidx.compose.ui.graphics.Color,
    valueColor: androidx.compose.ui.graphics.Color
) {
    Row(Modifier.fillMaxWidth().padding(vertical = 6.dp)) {
        Text(label, color = labelColor, style = MaterialTheme.typography.bodyMedium, modifier = Modifier.weight(0.4f))
        Text(value, color = valueColor, style = MaterialTheme.typography.bodyMedium, modifier = Modifier.weight(0.6f))
    }
}
