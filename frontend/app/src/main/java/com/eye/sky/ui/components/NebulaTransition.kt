package com.eye.sky.ui.components

import androidx.compsoe.animation.*
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import com.airbnb.lottie.compose.*
import com.eye.sky.audio.SoundManager
import com.eye.sky.R
import androidx.compose.ui.platform.LocalContext
import kotlinx.coroutines.delay

@OptIn(ExperimentalAnimationApi::class)
@Composable
fun NebulaTransition(
    visible: Boolean,
    playAmbient: Boolean = true,
    content: @Composable () -> Unit
) {
    val ctx = LocalContext.current
    Box(Modifier.fillMaxSize()){
        content()
        AnimatedVisibility(
            visible = visible,
            enter = fadeIn(animationSpec = tween(600)),
            exit = fadeOut(animationSpec = tween(600))
        ) {
            // Play the Nebulae Lottie animation once
            val comp by rememberLottieComposition(LottieCompositionSpec.Asset("lottie/nebula_transition.json"))
            val progress by animateLottieCompositionAsState(comp, iterations = 1, isPlaying = true, speed = 0.9f)
            LottieAnimation(comp, progress, modifier = Modifier.fillMaxSize())

            // Start ambient sound when animation starts if requested
            LaunchedEffect(playAmbient) {
                if (playAmbient) {
                    SoundManager.playAmbient(ctx, R.raw.nebula_pad, loop = false, volume = 0.25f)
                    // Stop after one or leave playing as you need: stop after Lottie duration
                    delay(1200)
                    SoundManager.stopAmbient()
                }
        }
    }
}