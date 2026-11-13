package ke.eyesky.app

import androidx.activity.compose.BackHandler
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.systemBarsPadding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import org.json.JSONArray

data class Lesson(val title: String, val category: String, val difficulty: String, val content: String)

private fun loadLessons(ctx: android.content.Context): List<Lesson> = try {
    val text = ctx.assets.open("lessons.json").bufferedReader().use { it.readText() }
    val arr = JSONArray(text)
    (0 until arr.length()).map {
        val o = arr.getJSONObject(it)
        Lesson(o.optString("title"), o.optString("category"), o.optString("difficulty"), o.optString("content"))
    }
} catch (e: Exception) {
    emptyList()
}

/** Offline lessons bundled with the app (assets/lessons.json). */
@Composable
fun LessonsScreen(onBack: () -> Unit) {
    val ctx = LocalContext.current
    val lessons = remember { loadLessons(ctx) }
    var open by remember { mutableStateOf<Lesson?>(null) }
    BackHandler { if (open != null) open = null else onBack() }

    Surface(Modifier.fillMaxSize(), color = MaterialTheme.colorScheme.background) {
        Column(Modifier.fillMaxSize().systemBarsPadding()) {
            Row(Modifier.fillMaxWidth().padding(horizontal = 8.dp), verticalAlignment = Alignment.CenterVertically) {
                TextButton(onClick = { if (open != null) open = null else onBack() }) {
                    Text(if (open != null) "‹ Lessons" else "‹ Back")
                }
            }
            val cur = open
            if (cur != null) {
                Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(horizontal = 20.dp, vertical = 8.dp)) {
                    Text(cur.category + "  ·  " + cur.difficulty, color = MaterialTheme.colorScheme.secondary,
                        style = MaterialTheme.typography.labelMedium)
                    Spacer(Modifier.height(6.dp))
                    Text(cur.title, style = MaterialTheme.typography.headlineSmall, color = MaterialTheme.colorScheme.primary)
                    Spacer(Modifier.height(16.dp))
                    cur.content.split("\n\n").forEach {
                        Text(it, style = MaterialTheme.typography.bodyLarge)
                        Spacer(Modifier.height(14.dp))
                    }
                    Spacer(Modifier.height(24.dp))
                }
            } else {
                LazyColumn(Modifier.fillMaxSize(), contentPadding = androidx.compose.foundation.layout.PaddingValues(16.dp),
                    verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    item {
                        Text("Lessons", style = MaterialTheme.typography.headlineMedium, color = MaterialTheme.colorScheme.primary)
                        Text("Learn the sky, one short lesson at a time", color = MaterialTheme.colorScheme.onSurfaceVariant)
                        Spacer(Modifier.height(8.dp))
                    }
                    val groups = lessons.groupBy { it.category }
                    groups.forEach { (cat, list) ->
                        item {
                            Text(cat, style = MaterialTheme.typography.titleMedium,
                                color = MaterialTheme.colorScheme.secondary, modifier = Modifier.padding(top = 10.dp))
                        }
                        items(list) { l ->
                            Surface(
                                Modifier.fillMaxWidth().clickable { open = l },
                                color = MaterialTheme.colorScheme.surface,
                                shape = MaterialTheme.shapes.medium
                            ) {
                                Column(Modifier.padding(14.dp)) {
                                    Text(l.title, fontWeight = FontWeight.Medium, style = MaterialTheme.typography.titleSmall)
                                    Text(l.difficulty, color = MaterialTheme.colorScheme.onSurfaceVariant,
                                        style = MaterialTheme.typography.labelSmall)
                                }
                            }
                        }
                    }
                    if (lessons.isEmpty()) item { Text("No lessons found.") }
                }
            }
        }
    }
}

@Composable
fun AboutScreen(onBack: () -> Unit) {
    BackHandler { onBack() }
    Surface(Modifier.fillMaxSize(), color = MaterialTheme.colorScheme.background) {
        Column(Modifier.fillMaxSize().systemBarsPadding()) {
            TextButton(onClick = onBack, modifier = Modifier.padding(horizontal = 8.dp)) { Text("‹ Back") }
            Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(horizontal = 20.dp)) {
                Logo(80)
                Wordmark(28)
                Spacer(Modifier.height(4.dp))
                Text("Version " + BuildConfig.VERSION_NAME, color = MaterialTheme.colorScheme.onSurfaceVariant)
                Spacer(Modifier.height(20.dp))
                Text("EyeSky shows you the sky above you in real time: stars, planets, the Moon and satellites, with 3D views and lessons for beginners.")
                Spacer(Modifier.height(20.dp))
                Text("Credits", style = MaterialTheme.typography.titleMedium, color = MaterialTheme.colorScheme.secondary)
                Spacer(Modifier.height(6.dp))
                Text("• Star data: HYG Database v4.2 (astronomy catalogue compiled from Hipparcos, Yale Bright Star and Gliese catalogues).\n" +
                    "• Satellite orbital elements: CelesTrak (celestrak.org).\n" +
                    "• Satellite position prediction: SGP4.\n" +
                    "• Weather: OpenWeatherMap.\n" +
                    "• Planet and Moon positions: computed from standard astronomical ephemerides.")
                Spacer(Modifier.height(20.dp))
                Text("Privacy", style = MaterialTheme.typography.titleMedium, color = MaterialTheme.colorScheme.secondary)
                Spacer(Modifier.height(6.dp))
                Text("Your location is used on your device and sent to our server only to calculate what is visible from where you are. " +
                    "We store your account name and email to sign you in. We do not sell your data.")
                Spacer(Modifier.height(30.dp))
            }
        }
    }
}
