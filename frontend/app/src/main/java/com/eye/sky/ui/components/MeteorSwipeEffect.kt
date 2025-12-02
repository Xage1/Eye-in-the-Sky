package com.eye.sky.ui.components

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import com.airbnb.lottie.compose.*
import com.eye.sky.audio.SoundManager
import com.eye.sky.R
import androidx.compose.ui.platform.LocalContext
import kotlinx.coroutines.delay

@Composable
fun MeteorSwipeEffect(visible: Boolean) {
    val ctx = LocalContext.current
    val comp by rememberLottieComposition(LottieCompositionSpec.Asset("lottie/meteor_swipe.json"))
    val progress by animateLottieCompositionAsState(comp, iterations = 1, isPlaying = visible, speed = 1.0f)

    AnimatedVisibility(visible = visible) {
        LottieAnimation(comp, progress, modifier = Modifier.fillMaxSize())
        // Play SFX once
        LaunchedEffect(visible) {
            if (visible) {
                SoundManager.playSfx(R.raw.meteor_swipe)
                // brief delay so UI can complete before hiding effect; caller should toggle visible off after delay
                delay(650)
            }
        }
    }
}