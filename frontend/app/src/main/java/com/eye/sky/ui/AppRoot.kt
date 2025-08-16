package com.eye.sky.ui

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.eye.sky.net.Api
import com.eye.sky.net.LoginReq
import kotlinx.coroutines.launch

enum class Tab { SkyGuide, Learn, NightWatch, Satellites }

@Composable
fun AppRoot() {
    var active by remember { mutableStateOf(Tab.SkyGuide) }
    var authed by remember { mutableStateOf(false) }
    val scope = rememberCoroutineScope()
    var email by remember { mutableStateOf("demo@sky.app") }
    var pw by remember { mutableStateOf("password") }
    var name by remember { mutableStateOf("Sky User") }
    var error by remember { mutableStateOf<String?>(null) }

    if (!authed) {
        Surface(Modifier.fillMaxSize()) {
            Column(Modifier.fillMaxSize().padding(24.dp), horizontalAlignment = Alignment.CenterHorizontally) {
                Text("Sign in to Eye in the Sky", style = MaterialTheme.typography.headlineSmall)
                Spacer(Modifier.height(12.dp))
                OutlinedTextField(email, { email = it }, label = { Text("Email") })
                OutlinedTextField(pw, { pw = it }, label = { Text("Password") })
                OutlinedTextField(name, { name = it }, label = { Text("Name") })
                Spacer(Modifier.height(12.dp))
                Row {
                    Button(onClick = {
                        scope.launch {
                            runCatching { Api.service.login(LoginReq(email, pw, name)) }
                                .onSuccess { token ->
                                    com.eye.sky.net.Session.token = token.access_token
                                    authed = true
                                }.onFailure { error = it.message }
                        }
                    }) { Text("Login") }
                    Spacer(Modifier.width(12.dp))
                    OutlinedButton(onClick = {
                        scope.launch {
                            runCatching { Api.service.signup(LoginReq(email, pw, name)) }
                                .onSuccess { /* ok */ }
                                .onFailure { error = it.message }
                        }
                    }) { Text("Sign up") }
                }
                error?.let { Text(it, color = MaterialTheme.colorScheme.error) }
            }
        }
        return
    }

    Scaffold(
        bottomBar = {
            NavigationBar {
                NavigationBarItem(selected = active==Tab.SkyGuide, onClick = { active = Tab.SkyGuide }, label = { Text("Sky Guide") }, icon = {})
                NavigationBarItem(selected = active==Tab.Learn, onClick = { active = Tab.Learn }, label = { Text("Astronomy 101") }, icon = {})
                NavigationBarItem(selected = active==Tab.NightWatch, onClick = { active = Tab.NightWatch }, label = { Text("Night Watch") }, icon = {})
                NavigationBarItem(selected = active==Tab.Satellites, onClick = { active = Tab.Satellites }, label = { Text("Satellites") }, icon = {})
            }
        }
    ) { pad ->
        Box(Modifier.padding(pad)) {
            when (active) {
                Tab.SkyGuide -> SkyGuideScreen()
                Tab.Learn -> LearnAndQuizScreen()
                Tab.NightWatch -> NightSkyWatchScreen()
                Tab.Satellites -> SatellitesScreen()
            }
        }
    }
}