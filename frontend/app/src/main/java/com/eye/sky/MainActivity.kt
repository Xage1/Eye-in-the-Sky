package com.eye.sky

import android.Manifest
import android.content.pm.PackageManager
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.core.content.ContextCompat
import com.eye.sky.ui.AppRoot

class MainActivity : ComponentActivity() {
    private val perms = arrayOf(Manifest.permission.CAMERA, Manifest.permission.ACCESS_FINE_LOCATION)

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val launcher = registerForActivityResult(ActivityResultContracts.RequestMultiplePermissions()) {}

        if (!perms.all { ContextCompat.checkSelfPermission(this, it) == PackageManager.PERMISSION_GRANTED }) {
            launcher.launch(perms)
        }

        setContent { MaterialTheme { AppRoot() } }
    }
}