package com.eye.sky.ui.components

import android.content.res.Configuration
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Visibility
import androidx.compose.material.icons.filled.VisibilityOff
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import com.airbnb.lottie.compose.*
import com.eye.sky.audio.SoundManager
import com.eye.sky.R

@Composable
fun EclipsePasswordField(
    password: String,
    onPasswordChange: (String) -> Unit,
    label: String = "Password",
    modifier: Modifier = Modifier,
    isDaytime: Boolean = true
) {
    val ctx = LocalContext.current
    // Lottie small icons
    val smallName = if (isDaytime) "sun_icon" else "moon_icon"
    val smallComp by rememberLottieComposition(LottieCompositionSpec.Asset("lottie/$smallName.json"))

    var hidden by remember { mutableStateOf(true) }
    var showToggleAnim by remember { mutableStateOf(false) }

    OutlinedTextField(
        value = password,
        onValueChange = onPasswordChange,
        label = { Text(label) },
        modifier = modifier.fillMaxWidth(),
        trailingIcon = {
            Row {
                // small looping icon
                val progressSmall by animateLottieCompositionAsState(smallComp, iterations = LottieConstants.IterateForever, isPlaying = true)
                LottieAnimation(smallComp, progressSmall, modifier = Modifier.size(28.dp))

                Spacer(Modifier.width(8.dp))

                IconButton(onClick = {
                    hidden = !hidden
                    // play toggle sound
                    SoundManager.playSfx(R.raw.eclipse_toggle)
                    // play toggle Lottie full-screen overlay once by setting showToggleAnim true
                    showToggleAnim = true
                }) {
                    Icon(
                        imageVector = if (hidden) Icons.Default.VisibilityOff else Icons.Default.Visibility,
                        contentDescription = "Toggle password"
                    )
                }
            }
        },
        visualTransformation = if (hidden) androidx.compose.ui.text.input.PasswordVisualTransformation() else androidx.compose.ui.text.input.VisualTransformation.None,
        singleLine = true,
        keyboardOptions = KeyboardOptions.Default
    )

    // overlay one-shot eclipse animation when showToggleAnim true
    if (showToggleAnim) {
        val comp by rememberLottieComposition(LottieCompositionSpec.Asset("lottie/eclipse_toggle.json"))
        val progress by animateLottieCompositionAsState(comp, iterations = 1, isPlaying = true, speed = 1f)
        Box(Modifier.fillMaxSize()) {
            LottieAnimation(comp, progress, modifier = Modifier.fillMaxSize())
        }
        // auto-hide after the animation frames (~800-1200ms)
        LaunchedEffect(progress) {
            if (progress >= 0.995f) {
                showToggleAnim = false
            }
        }
    }
}