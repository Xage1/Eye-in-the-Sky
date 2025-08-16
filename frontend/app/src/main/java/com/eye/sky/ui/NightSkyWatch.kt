package com.eye.sky.ui

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.eye.sky.net.Api
import com.eye.sky.net.NightSkyEventsResp
import com.eye.sky.net.VisibilityResp
import kotlinx.coroutines.launch

@Composable
fun NightSkyWatchScreen() {
    val scope = rememberCoroutineScope()
    var vis by remember { mutableStateOf<VisibilityResp?>(null) }
    var events by remember { mutableStateOf<NightSkyEventsResp?>(null) }

    LaunchedEffect(Unit) {
        val lat = -1.286389; val lon = 36.817223
        vis = runCatching { Api.service.visibility(lat, lon) }.getOrNull()
        events = runCatching { Api.service.nightSky(lat, lon) }.getOrNull()
    }

    Column(Modifier.fillMaxSize().padding(12.dp)) {
        Text("Night Sky Watch", style = MaterialTheme.typography.headlineSmall)
        Spacer(Modifier.height(8.dp))
        ElevatedCard(Modifier.fillMaxWidth()) {
            Column(Modifier.padding(12.dp)) {
                Text("Visibility")
                val d = vis?.visibility
                Text("Avg visibility: ${d?.visibility_km ?: "—"} km")
                Text("Clouds: ${d?.cloud_coverage_percent ?: "—"} %")
                Text("Clear enough? ${if (d?.sky_clear == true) "Yes" else "No"}")
            }
        }
        Spacer(Modifier.height(12.dp))
        ElevatedCard(Modifier.fillMaxWidth()) {
            Column(Modifier.padding(12.dp)) {
                Text("Events Tonight")
                Text(events?.astronomy?.toString() ?: "—")
            }
        }
    }
}