package com.eye.sky.audio

import android.content.Context
import android.media.AudioAttributes
import android.media.SoundPool
import androidx.annotation.RawRes
import androidx.media3.common.MediaItem
import androidx.media3.common.Player
import androidx.media3.exoplayer.ExoPlayer

/**
 * SoundManager — SoundPool for short SFX, Media3 ExoPlayer for ambient loops.
 *
 * Usage:
 *  SoundManager.init(context)
 *  SoundManager.loadSfx(context, R.raw.meteor_swipe)
 *  SoundManager.playSfx(R.raw.meteor_swipe)
 *  SoundManager.playAmbient(context, R.raw.nebula_pad)
 *  SoundManager.stopAmbient()
 *  SoundManager.release()
 */
object SoundManager {
    private var soundPool: SoundPool? = null
    private val soundMap = HashMap<Int, Int>()  // resId -> soundPool sound id
    private var exoPlayer: ExoPlayer? = null
    private var appContext: Context? = null

    fun init(context: Context) {
        appContext = context.applicationContext
        val attrs = AudioAttributes.Builder()
            .setUsage(AudioAttributes.USAGE_MEDIA)
            .setContentType(AudioAttributes.CONTENT_TYPE_MUSIC)
            .build()
        soundPool = SoundPool.Builder()
            .setAudioAttributes(attrs)
            .setMaxStreams(8)
            .build()
    }

    fun loadSfx(context: Context, @RawRes resId: Int) {
        val sp = soundPool ?: return
        if (soundMap.containsKey(resId)) return
        val sid = sp.load(context, resId, 1)
        soundMap[resId] = sid
    }

    fun playSfx(@RawRes resId: Int, volume: Float = 1.0f) {
        val sp = soundPool ?: return
        val sid = soundMap[resId] ?: return
        sp.play(sid, volume, volume, 1, 0, 1f)
    }

    fun playAmbient(context: Context, @RawRes resId: Int, loop: Boolean = true, volume: Float = 0.45f) {
        releaseAmbient()
        val ctx = context.applicationContext
        val uri = android.net.Uri.parse("android.resource://${ctx.packageName}/$resId")
        val player = ExoPlayer.Builder(ctx).build().apply {
            repeatMode = if (loop) Player.REPEAT_MODE_ALL else Player.REPEAT_MODE_OFF
            this.volume = volume
            setMediaItem(MediaItem.fromUri(uri))
            prepare()
            playWhenReady = true
        }
        exoPlayer = player
    }

    fun stopAmbient() {
        exoPlayer?.run {
            playWhenReady = false
            release()
        }
        exoPlayer = null
    }

    private fun releaseAmbient() {
        exoPlayer?.release()
        exoPlayer = null
    }

    fun release() {
        soundPool?.release()
        soundPool = null
        soundMap.clear()
        releaseAmbient()
    }
}