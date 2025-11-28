package.com.eye.sky.audio

import android.content.Context
import android.media.AudioAttributes
import android.media.SoundPool
import androidx.annotation.RawRes
import com.google.android.exoplayer2.ExoPlayer
import com.google.android.exoplayer2.MediaItem
import com.google.android.exoplayer2.Player


/**
 * SoundManager: SoundPool for short SFX, ExoPlayer for long/ambient loop.
 *
 * Usage:
 *  - SoundManager.init(context)
 *  - SoundManager.loadSfx(R.raw.meteor_swipe)
 *  - SoundManager.playSfx(R.raw.meteor_swipe)
 *  - SoundManager.playAmbient(R.raw.nebula_pad) // loops by default
 *  - SoundManager.stopAmbient()
 *  - SoundManager.release()
 */

object SoundManager {
    private var soundPool: SoundPool? = null
    private val soundMap = HashMap<Int, Int>() // resId -> sound
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
        if (soundMap.containsKey(resId)) return // already loaded
        val sid = sp.load(context, resId, 1)
        soundMap[resId] = sid
    }


    fun playSfx(@RawRes resId: Int, volume: Float = 1.0f) {
        val sp = soundPool ?: return
        val sid = soundMap[resId] ?: return
        sp.play(sid, volume, volume, 1, 0, 1f)
    }


    // Ambient: Exoplayer
    fun playAmbient(context: Context, @RawRes resId: Int, loop: Boolean = true, volume: Float = 0.45f) {
        releaseAmbient()
        val ctx = context.applicationContext
        val player = Exoplayer.Builder(ctx).build().apply {
            repeatMode = if (loop) Player.REPEAT_MODE_ALL else Player.REPEAT_MODE_OFF
            volume = volume
            setMediaItem(MediaItem.fromUri("rawresource://${ctx.packageName}/$resId"))
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