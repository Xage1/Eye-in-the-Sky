package com.eye.sky

import android.Manifest
import android.content.pm.PackageManager
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.material3.MaterialTheme
import androidx.core.content.ContextCompat
import com.eye.sky.audio.SoundManager
import com.eye.sky.ui.AppRoot

class MainActivity : ComponentActivity() {

    private val perms = arrayOf(
        Manifest.permission.CAMERA,
        Manifest.permission.ACCESS_FINE_LOCATION,
    )

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // Preload SFX — R.raw resource IDs (files must exist in res/raw/)
        // Using safe loading — only loads if the resource exists
        SoundManager.init(this)
        runCatching { SoundManager.loadSfx(this, R.raw.meteor_swipe) }
        runCatching { SoundManager.loadSfx(this, R.raw.planet_alignment) }
        runCatching { SoundManager.loadSfx(this, R.raw.eclipse_toggle) }
        runCatching { SoundManager.loadSfx(this, R.raw.blackhole_loader) }

        val launcher = registerForActivityResult(
            ActivityResultContracts.RequestMultiplePermissions()
        ) { /* handle results if needed */ }

        if (!perms.all {
                ContextCompat.checkSelfPermission(this, it) == PackageManager.PERMISSION_GRANTED
            }) {
            launcher.launch(perms)
        }

        setContent {
            MaterialTheme {
                AppRoot()
            }
        }
    }
}