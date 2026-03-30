package com.eye.sky

import android.app.Application
import com.eye.sky.audio.SoundManager

class EyeInTheSkyApp : Application() {
    override fun onCreate() {
        super.onCreate()
        SoundManager.init(this)
    }
}