package com.eye.sky.ui.components

import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.airbnb.lottie.compose.*
import com.eye.sky.audio.SoundManager
import com.eye.sky.R
import androidx.compose.ui.platform.LocalContext
import kotlinx.coroutines.delay

@Composable
fun BlackHoleLoader(autoPlayRumble: Boolean = true) {
    val ctx = LocalContext.current
    val comp by rememberLottieComposition(LottieCompositionSpec.Asset("lottie/blackhole_loader.json"))
    val progress by animateLottieCompositionAsState(comp, iterations = LottieConstants.IterateForever, isPlaying = true, speed = 1f)

    Box(Modifier.fillMaxWidth().height(160.dp), contentAlignment = Alignment.Center) {
        LottieAnimation(comp, progress, modifier = Modifier.fillMaxWidth())
    }

    if (autoPlayRumble) {
        LaunchedEffect(Unit) {
            SoundManager.playSfx(R.raw.blackhole_loader) // short rumble; or playAmbient for long rumble
        }
    }
}