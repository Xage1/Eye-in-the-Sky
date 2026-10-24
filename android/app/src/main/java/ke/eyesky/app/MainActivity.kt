package ke.eyesky.app

import android.content.SharedPreferences
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.Image
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.systemBarsPadding
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.withStyle
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import kotlinx.coroutines.launch

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val prefs = getSharedPreferences("eyesky", MODE_PRIVATE)
        Api.token = prefs.getString("token", null)
        setContent {
            var night by remember { mutableStateOf(prefs.getBoolean("night", false)) }
            EyeSkyTheme(nightVision = night) {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = MaterialTheme.colorScheme.background
                ) {
                    Box(Modifier.fillMaxSize()) {
                        Starfield()
                        App(prefs, night) {
                            night = it
                            prefs.edit().putBoolean("night", it).apply()
                        }
                    }
                }
            }
        }
    }
}

@Composable
fun App(prefs: SharedPreferences, night: Boolean, onNight: (Boolean) -> Unit) {
    var loggedIn by remember { mutableStateOf(!Api.token.isNullOrBlank()) }
    var inSky by remember { mutableStateOf(false) }
    if (loggedIn && inSky) {
        SkyScreen(onBack = { inSky = false })
    } else if (loggedIn) {
        HomeScreen(night = night, onNight = onNight, onOpenSky = { inSky = true }, onLogout = {
            Api.token = null
            prefs.edit().remove("token").apply()
            loggedIn = false
        })
    } else {
        AuthScreen(onDone = {
            prefs.edit().putString("token", Api.token).apply()
            loggedIn = true
        })
    }
}

@Composable
fun Wordmark(size: Int = 40) {
    val gold = MaterialTheme.colorScheme.primary
    Text(
        text = buildAnnotatedString {
            append("Eye")
            withStyle(SpanStyle(color = gold)) { append("Sky") }
        },
        fontSize = size.sp,
        fontWeight = FontWeight.Bold,
        letterSpacing = 1.sp
    )
}

@Composable
fun Logo(size: Int) {
    Image(
        painter = painterResource(R.drawable.ic_launcher_foreground),
        contentDescription = "EyeSky",
        modifier = Modifier.size(size.dp)
    )
}

@Composable
fun AuthScreen(onDone: () -> Unit) {
    var signup by remember { mutableStateOf(false) }
    var name by remember { mutableStateOf("") }
    var email by remember { mutableStateOf("") }
    var password by remember { mutableStateOf("") }
    var busy by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }
    val scope = rememberCoroutineScope()

    Column(
        modifier = Modifier.fillMaxSize().systemBarsPadding().padding(24.dp),
        verticalArrangement = Arrangement.Center,
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Logo(120)
        Wordmark(40)
        Text(
            "Your eye in the sky",
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
        Spacer(Modifier.height(28.dp))

        if (signup) {
            OutlinedTextField(
                value = name, onValueChange = { name = it },
                label = { Text("Name") }, singleLine = true,
                modifier = Modifier.fillMaxWidth()
            )
            Spacer(Modifier.height(12.dp))
        }
        OutlinedTextField(
            value = email, onValueChange = { email = it },
            label = { Text("Email") }, singleLine = true,
            modifier = Modifier.fillMaxWidth()
        )
        Spacer(Modifier.height(12.dp))
        OutlinedTextField(
            value = password, onValueChange = { password = it },
            label = { Text("Password") }, singleLine = true,
            visualTransformation = PasswordVisualTransformation(),
            modifier = Modifier.fillMaxWidth()
        )
        Spacer(Modifier.height(16.dp))

        error?.let {
            Text(it, color = MaterialTheme.colorScheme.error)
            Spacer(Modifier.height(8.dp))
        }

        Button(
            onClick = {
                scope.launch {
                    busy = true
                    error = null
                    try {
                        if (signup) Api.signup(name.trim(), email.trim(), password)
                        else Api.login(email.trim(), password)
                        onDone()
                    } catch (e: ApiException) {
                        error = e.message
                    } catch (e: Exception) {
                        error = "Cannot reach the server: " + e.message
                    } finally {
                        busy = false
                    }
                }
            },
            enabled = !busy && email.isNotBlank() && password.isNotBlank(),
            modifier = Modifier.fillMaxWidth()
        ) {
            Text(if (busy) "Please wait..." else if (signup) "Sign up" else "Sign in")
        }
        TextButton(onClick = { signup = !signup; error = null }) {
            Text(
                if (signup) "I already have an account" else "Create an account",
                color = MaterialTheme.colorScheme.secondary
            )
        }
    }
}

@Composable
fun HomeScreen(night: Boolean, onNight: (Boolean) -> Unit, onOpenSky: () -> Unit, onLogout: () -> Unit) {
    var info by remember { mutableStateOf("Loading...") }

    LaunchedEffect(Unit) {
        try {
            val me = Api.me()
            val plan = try {
                Api.subscription().optString("plan", "free")
            } catch (e: ApiException) {
                "free"
            }
            info = "Signed in as " + me.optString("name") + "\n" +
                me.optString("email") + "\nPlan: " + plan
        } catch (e: ApiException) {
            if (e.code == 401) onLogout() else info = "Error: " + e.message
        } catch (e: Exception) {
            info = "Cannot reach the server: " + e.message
        }
    }

    Column(
        modifier = Modifier.fillMaxSize().systemBarsPadding().padding(24.dp),
        verticalArrangement = Arrangement.Center,
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Logo(96)
        Wordmark(32)
        Spacer(Modifier.height(20.dp))
        Text(info, style = MaterialTheme.typography.bodyLarge)
        Spacer(Modifier.height(20.dp))
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text("Night vision (red) mode", modifier = Modifier.padding(end = 12.dp))
            Switch(checked = night, onCheckedChange = onNight)
        }
        Spacer(Modifier.height(20.dp))
        Button(onClick = onOpenSky, modifier = Modifier.fillMaxWidth()) { Text("Open sky view") }
        Spacer(Modifier.height(12.dp))
        OutlinedButton(onClick = onLogout) { Text("Sign out") }
    }
}
