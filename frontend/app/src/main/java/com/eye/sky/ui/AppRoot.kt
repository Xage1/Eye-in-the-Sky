package com.eye.sky.ui

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.compose.ui.platform.LocalContext
import com.eye.sky.net.Api
import com.eye.sky.net.LoginReq
import com.eye.sky.audio.SoundManager
import com.eye.sky.R
import com.eye.sky.ui.components.EclipsePasswordField
import com.eye.sky.ui.components.NebulaTransition
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch

enum class Tab { SkyGuide, Learn, NightWatch, Satellites }

@Composable
fun AppRoot() {

    val ctx = LocalContext.current
    var active by remember { mutableStateOf(Tab.SkyGuide) }
    var showNebula by remember { mutableStateOf(false) }
    var authed by remember { mutableStateOf(false) }

    val scope = rememberCoroutineScope()
    var email by remember { mutableStateOf("demo@sky.app") }
    var pw by remember { mutableStateOf("password") }
    var name by remember { mutableStateOf("Sky User") }
    var error by remember { mutableStateOf<String?>(null) }

    // ----------------------------------------------------------
    // LOGIN SCREEN (with EclipsePasswordField)
    // ----------------------------------------------------------
    if (!authed) {
        Surface(Modifier.fillMaxSize()) {
            Column(
                Modifier.fillMaxSize().padding(24.dp),
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                Text("Sign in to Eye in the Sky", style = MaterialTheme.typography.headlineSmall)
                Spacer(Modifier.height(12.dp))

                OutlinedTextField(
                    value = email,
                    onValueChange = { email = it },
                    label = { Text("Email") },
                    modifier = Modifier.fillMaxWidth()
                )

                // 🔥 Eclipse Password Field (Lottie + Sound)
                EclipsePasswordField(
                    password = pw,
                    onPasswordChange = { pw = it },
                    isDaytime = true,
                    modifier = Modifier.fillMaxWidth()
                )

                OutlinedTextField(
                    value = name,
                    onValueChange = { name = it },
                    label = { Text("Name") },
                    modifier = Modifier.fillMaxWidth()
                )

                Spacer(Modifier.height(12.dp))

                Row {
                    Button(onClick = {
                        scope.launch {
                            runCatching { Api.service.login(LoginReq(email, pw, name)) }
                                .onSuccess { token ->
                                    com.eye.sky.net.Session.token = token.access_token
                                    authed = true
                                }
                                .onFailure { error = it.message }
                        }
                    }) { Text("Login") }

                    Spacer(Modifier.width(12.dp))

                    OutlinedButton(onClick = {
                        scope.launch {
                            runCatching { Api.service.signup(LoginReq(email, pw, name)) }
                                .onFailure { error = it.message }
                        }
                    }) { Text("Sign Up") }
                }

                error?.let {
                    Text(it, color = MaterialTheme.colorScheme.error)
                }
            }
        }
        return
    }

    // ----------------------------------------------------------
    // MAIN APP UI
    // ----------------------------------------------------------
    Scaffold(
        bottomBar = {
            NavigationBar {
                NavigationBarItem(
                    selected = active == Tab.SkyGuide,
                    onClick = {
                        active = Tab.SkyGuide
                        showNebula = true
                        SoundManager.playSfx(R.raw.meteor_swipe)
                    },
                    label = { Text("Sky Guide") },
                    icon = {}
                )

                NavigationBarItem(
                    selected = active == Tab.Learn,
                    onClick = {
                        active = Tab.Learn
                        showNebula = true
                        SoundManager.playSfx(R.raw.meteor_swipe)
                    },
                    label = { Text("Astronomy 101") },
                    icon = {}
                )

                NavigationBarItem(
                    selected = active == Tab.NightWatch,
                    onClick = {
                        active = Tab.NightWatch
                        showNebula = true
                        SoundManager.playSfx(R.raw.meteor_swipe)
                    },
                    label = { Text("Night Watch") },
                    icon = {}
                )

                NavigationBarItem(
                    selected = active == Tab.Satellites,
                    onClick = {
                        active = Tab.Satellites
                        showNebula = true
                        SoundManager.playSfx(R.raw.meteor_swipe)
                    },
                    label = { Text("Satellites") },
                    icon = {}
                )
            }
        }
    ) { pad ->

        // NebulaTransition wraps all content
        NebulaTransition(visible = showNebula) {
            Box(Modifier.padding(pad)) {
                when (active) {
                    Tab.SkyGuide -> SkyGuideScreen()
                    Tab.Learn -> LearnAndQuizScreen()
                    Tab.NightWatch -> NightSkyWatchScreen()
                    Tab.Satellites -> SatellitesScreen()
                }
            }
        }

        // Reset transition after showing it
        LaunchedEffect(showNebula) {
            if (showNebula) {
                delay(650)
                showNebula = false
            }
        }
    }
}