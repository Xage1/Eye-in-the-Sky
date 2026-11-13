package ke.eyesky.app

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.OkHttpClient
import okhttp3.Request
import org.json.JSONObject
import java.util.concurrent.TimeUnit
import kotlin.math.roundToInt

private val weatherClient = OkHttpClient.Builder()
    .connectTimeout(15, TimeUnit.SECONDS)
    .readTimeout(30, TimeUnit.SECONDS)
    .build()

private suspend fun fetchWeather(lat: Double, lon: Double): JSONObject = withContext(Dispatchers.IO) {
    val b = Request.Builder()
        .url(Api.baseUrl + "/skyinfo/visibility?lat=" + lat + "&lon=" + lon)
        .header("ngrok-skip-browser-warning", "1")
    Api.token?.let { b.header("Authorization", "Bearer $it") }
    weatherClient.newCall(b.build()).execute().use { r ->
        val text = r.body?.string().orEmpty()
        if (!r.isSuccessful) throw Exception("Server said HTTP " + r.code)
        JSONObject(text)
    }
}

/** "Is tonight good for stargazing?" card for the current location. */
@Composable
fun WeatherDialog(lat: Double?, lon: Double?, onClose: () -> Unit) {
    var data by remember { mutableStateOf<JSONObject?>(null) }
    var err by remember { mutableStateOf<String?>(null) }
    var loading by remember { mutableStateOf(true) }
    var nonce by remember { mutableStateOf(0) }

    LaunchedEffect(lat, lon, nonce) {
        if (lat == null || lon == null) {
            loading = false
            err = "Waiting for your location..."
            return@LaunchedEffect
        }
        loading = true
        err = null
        try {
            val d = fetchWeather(lat, lon)
            if (d.has("error")) err = "Weather is unavailable right now (" + d.optString("error") + ")"
            else data = d
        } catch (e: Exception) {
            err = "Could not load weather: " + (e.message ?: "unknown error")
        }
        loading = false
    }

    AlertDialog(
        onDismissRequest = onClose,
        title = { Text("Sky conditions") },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
                val d = data
                if (loading) {
                    Text("Loading...")
                } else if (err != null) {
                    Text(err ?: "")
                } else if (d != null) {
                    val score = d.optInt("visibility_score", 0)
                    val verdict = when {
                        score >= 70 -> "Excellent for stargazing"
                        score >= 40 -> "Fair: patchy cloud"
                        else -> "Poor: mostly cloudy"
                    }
                    Text(verdict, style = MaterialTheme.typography.titleMedium,
                        color = MaterialTheme.colorScheme.primary, fontWeight = FontWeight.Medium)
                    Text("Visibility score: $score / 100", color = MaterialTheme.colorScheme.secondary)
                    Spacer(Modifier.height(4.dp))
                    val cond = d.optString("conditions")
                    if (cond.isNotBlank()) WRow("Conditions", cond.replaceFirstChar { it.uppercase() })
                    WRow("Cloud cover", d.optInt("cloud_cover_pct").toString() + "%")
                    WRow("Temperature", d.optDouble("temperature_c", 0.0).toString() + " °C")
                    WRow("Humidity", d.optInt("humidity_pct").toString() + "%")
                    WRow("Wind", (d.optDouble("wind_speed_ms", 0.0) * 3.6).roundToInt().toString() + " km/h")
                    WRow("Horizon visibility", (d.optInt("visibility_m") / 1000.0).toString() + " km")
                    if (d.optBoolean("dew_point_warning")) {
                        Text("Dew warning: lenses and screens may fog up.", color = MaterialTheme.colorScheme.error)
                    }
                }
            }
        },
        confirmButton = { TextButton(onClick = onClose) { Text("Close") } },
        dismissButton = { TextButton(onClick = { nonce++ }) { Text("Refresh") } }
    )
}

@Composable
private fun WRow(label: String, value: String) {
    Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
        Text(label, color = MaterialTheme.colorScheme.onSurfaceVariant)
        Text(value)
    }
}
