package com.eye.sky.ui

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.eye.sky.net.Api
import okhttp3.ResponseBody

@Composable
fun SatellitesScreen() {
    var tle by remember { mutableStateOf<String?>(null) }
    var iss by remember { mutableStateOf<String?>(null) }

    LaunchedEffect(Unit) {
        val tleResp = runCatching { Api.service.tle() }.getOrNull()
        tle = tleResp?.body()?.string()
        iss = runCatching { Api.service.iss() }.getOrNull()?.toString()
    }

    Column(Modifier.fillMaxSize().padding(12.dp).verticalScroll(rememberScrollState())) {
        Text("Satellite Locator", style = MaterialTheme.typography.headlineSmall)
        Spacer(Modifier.height(8.dp))
        ElevatedCard(Modifier.fillMaxWidth()) {
            Column(Modifier.padding(12.dp)) {
                Text("ISS Position (Live)")
                Text(iss ?: "—")
            }
        }
        Spacer(Modifier.height(12.dp))
        ElevatedCard(Modifier.fillMaxWidth()) {
            Column(Modifier.padding(12.dp)) {
                Text("NORAD TLE (CelesTrak)")
                Text(tle ?: "—")
            }
        }
    }
}