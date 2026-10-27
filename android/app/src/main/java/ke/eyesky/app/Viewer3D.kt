package ke.eyesky.app

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.opengl.GLES11Ext
import android.opengl.GLES20
import android.opengl.GLSurfaceView
import android.opengl.GLUtils
import android.opengl.Matrix
import android.util.Log
import android.view.MotionEvent
import android.view.ScaleGestureDetector
import androidx.activity.ComponentActivity
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.viewinterop.AndroidView
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleEventObserver
import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.nio.FloatBuffer
import java.nio.ShortBuffer
import javax.microedition.khronos.egl.EGL10
import javax.microedition.khronos.egl.EGLConfig
import javax.microedition.khronos.egl.EGLDisplay
import javax.microedition.khronos.opengles.GL10
import kotlin.math.PI
import kotlin.math.atan
import kotlin.math.cos
import kotlin.math.ln
import kotlin.math.min
import kotlin.math.pow
import kotlin.math.sin
import kotlin.math.sqrt
import kotlin.math.tan

/** How one body is drawn. Textures live in assets/textures (see android/fetch_textures.ps1). */
class BodySpec(
    val key: String,
    val texture: String?,            // file name in assets/textures, null for procedural
    val tiltDeg: Float,              // axial tilt
    val spinDegPerSec: Float,        // show-room spin, not the real rate
    val yawStart: Float,             // which longitude faces you at first
    val atmosphere: FloatArray?,     // rim glow colour
    val kind: Float = 0f,            // 0 planet/moon, 1 Sun, 2 procedural star
    val rings: Boolean = false
)

object BodyCatalog {
    val specs: Map<String, BodySpec> = mapOf(
        "sun" to BodySpec("sun", "sun.jpg", 7.25f, 3f, 90f, floatArrayOf(1f, 0.55f, 0.15f), kind = 1f),
        "moon" to BodySpec("moon", "moon.jpg", 6.7f, 0f, 90f, null),
        "mercury" to BodySpec("mercury", "mercury.jpg", 0.03f, 2.5f, 90f, null),
        "venus" to BodySpec("venus", "venus.jpg", 177.4f, -2f, 90f, floatArrayOf(0.95f, 0.8f, 0.5f)),
        "earth" to BodySpec("earth", "earth.jpg", 23.4f, 6f, 53f, floatArrayOf(0.3f, 0.55f, 1f)),
        "mars" to BodySpec("mars", "mars.jpg", 25.2f, 5f, 90f, floatArrayOf(0.9f, 0.55f, 0.4f)),
        "jupiter" to BodySpec("jupiter", "jupiter.jpg", 3.1f, 12f, 90f, floatArrayOf(0.8f, 0.7f, 0.55f)),
        "saturn" to BodySpec("saturn", "saturn.jpg", 26.7f, 9f, 90f, floatArrayOf(0.85f, 0.75f, 0.5f), rings = true),
        "uranus" to BodySpec("uranus", "uranus.jpg", 97.8f, 7f, 90f, floatArrayOf(0.5f, 0.85f, 0.9f)),
        "neptune" to BodySpec("neptune", "neptune.jpg", 28.3f, 7f, 90f, floatArrayOf(0.3f, 0.45f, 1f))
    )
    val star = BodySpec("star", null, 0f, 3f, 0f, null, kind = 2f)
}

/** Approximate star colour from the B-V colour index (Ballesteros temperature + blackbody fit). */
fun starRgb(bv: Float): FloatArray {
    val b = bv.toDouble().coerceIn(-0.4, 2.0)
    val temp = 4600.0 * (1.0 / (0.92 * b + 1.7) + 1.0 / (0.92 * b + 0.62))
    val t = temp.coerceIn(1500.0, 40000.0) / 100.0
    val r = if (t <= 66) 255.0 else 329.698727446 * (t - 60).pow(-0.1332047592)
    val g = if (t <= 66) 99.4708025861 * ln(t) - 161.1195681661 else 288.1221695283 * (t - 60).pow(-0.0755148492)
    val bl = if (t >= 66) 255.0 else if (t <= 19) 0.0 else 138.5177312231 * ln(t - 10) - 305.0447927307
    return floatArrayOf(
        (r.coerceIn(0.0, 255.0) / 255.0).toFloat(),
        (g.coerceIn(0.0, 255.0) / 255.0).toFloat(),
        (bl.coerceIn(0.0, 255.0) / 255.0).toFloat()
    )
}

private class Mesh(val v: FloatBuffer, val idx: ShortBuffer, val count: Int)

private fun floatBuf(a: FloatArray): FloatBuffer =
    ByteBuffer.allocateDirect(a.size * 4).order(ByteOrder.nativeOrder()).asFloatBuffer().also { it.put(a); it.position(0) }

private fun shortBuf(a: ShortArray): ShortBuffer =
    ByteBuffer.allocateDirect(a.size * 2).order(ByteOrder.nativeOrder()).asShortBuffer().also { it.put(a); it.position(0) }

/** Unit sphere. Vertex layout: position(3), normal(3), uv(2). The north pole is +Y. */
private fun buildSphere(stacks: Int, slices: Int): Mesh {
    val verts = FloatArray((stacks + 1) * (slices + 1) * 8)
    var o = 0
    for (i in 0..stacks) {
        val phi = PI * i / stacks
        val y = cos(phi).toFloat()
        val r = sin(phi).toFloat()
        for (j in 0..slices) {
            val th = 2.0 * PI * j / slices
            val x = (r * cos(th)).toFloat()
            val z = (r * sin(th)).toFloat()
            verts[o++] = x; verts[o++] = y; verts[o++] = z
            verts[o++] = x; verts[o++] = y; verts[o++] = z
            verts[o++] = 1f - j.toFloat() / slices
            verts[o++] = i.toFloat() / stacks
        }
    }
    val idx = ShortArray(stacks * slices * 6)
    var k = 0
    for (i in 0 until stacks) {
        for (j in 0 until slices) {
            val a = i * (slices + 1) + j
            val b = a + slices + 1
            idx[k++] = a.toShort(); idx[k++] = b.toShort(); idx[k++] = (a + 1).toShort()
            idx[k++] = (a + 1).toShort(); idx[k++] = b.toShort(); idx[k++] = (b + 1).toShort()
        }
    }
    return Mesh(floatBuf(verts), shortBuf(idx), idx.size)
}

/** Flat ring in the XZ plane. u runs from the inner to the outer edge. */
private fun buildRing(segments: Int, inner: Float, outer: Float): Mesh {
    val verts = FloatArray((segments + 1) * 2 * 8)
    var o = 0
    for (j in 0..segments) {
        val th = 2.0 * PI * j / segments
        val c = cos(th).toFloat()
        val s = sin(th).toFloat()
        verts[o++] = inner * c; verts[o++] = 0f; verts[o++] = inner * s
        verts[o++] = 0f; verts[o++] = 1f; verts[o++] = 0f
        verts[o++] = 0f; verts[o++] = 0.5f
        verts[o++] = outer * c; verts[o++] = 0f; verts[o++] = outer * s
        verts[o++] = 0f; verts[o++] = 1f; verts[o++] = 0f
        verts[o++] = 1f; verts[o++] = 0.5f
    }
    val idx = ShortArray(segments * 6)
    var k = 0
    for (j in 0 until segments) {
        val a = j * 2
        idx[k++] = a.toShort(); idx[k++] = (a + 1).toShort(); idx[k++] = (a + 2).toShort()
        idx[k++] = (a + 2).toShort(); idx[k++] = (a + 1).toShort(); idx[k++] = (a + 3).toShort()
    }
    return Mesh(floatBuf(verts), shortBuf(idx), idx.size)
}

private const val VERT = """
uniform mat4 uMV;
uniform mat4 uP;
uniform mat3 uNM;
attribute vec3 aPos;
attribute vec3 aNormal;
attribute vec2 aUV;
varying vec2 vUV;
varying vec3 vN;
varying vec3 vView;
varying vec3 vPos;
void main() {
    vUV = aUV;
    vPos = aPos;
    vN = uNM * aNormal;
    vec4 p = uMV * vec4(aPos, 1.0);
    vView = -p.xyz;
    gl_Position = uP * p;
}
"""

private const val FRAG = """
precision highp float;
uniform sampler2D uTex;
uniform vec3 uLight;
uniform vec3 uAtm;
uniform vec3 uStar;
uniform float uKind;
uniform float uAmbient;
uniform float uBright;
uniform float uTime;
varying vec2 vUV;
varying vec3 vN;
varying vec3 vView;
varying vec3 vPos;

float hash(vec3 p) {
    p = fract(p * 0.3183099 + 0.1);
    p *= 17.0;
    return fract(p.x * p.y * p.z * (p.x + p.y + p.z));
}
float noise(vec3 x) {
    vec3 i = floor(x);
    vec3 f = fract(x);
    f = f * f * (3.0 - 2.0 * f);
    return mix(mix(mix(hash(i + vec3(0.0, 0.0, 0.0)), hash(i + vec3(1.0, 0.0, 0.0)), f.x),
                   mix(hash(i + vec3(0.0, 1.0, 0.0)), hash(i + vec3(1.0, 1.0, 0.0)), f.x), f.y),
               mix(mix(hash(i + vec3(0.0, 0.0, 1.0)), hash(i + vec3(1.0, 0.0, 1.0)), f.x),
                   mix(hash(i + vec3(0.0, 1.0, 1.0)), hash(i + vec3(1.0, 1.0, 1.0)), f.x), f.y), f.z);
}

void main() {
    vec3 N = normalize(vN);
    vec3 V = normalize(vView);
    float ndv = clamp(dot(N, V), 0.0, 1.0);
    vec4 t = texture2D(uTex, vUV);
    vec3 col;
    float alpha = 1.0;
    if (uKind > 3.5) {
        col = t.rgb * uBright;
    } else if (uKind > 2.5) {
        float ndl = abs(dot(N, normalize(uLight)));
        col = t.rgb * (uAmbient + (1.0 - uAmbient) * ndl);
        alpha = t.a;
    } else if (uKind > 1.5) {
        float n1 = noise(vPos * 7.0 + vec3(uTime * 0.08));
        float n2 = noise(vPos * 19.0 - vec3(uTime * 0.12));
        float g = 0.78 + 0.45 * n1 * n2 + 0.2 * n1;
        float limb = 0.5 + 0.5 * pow(ndv, 0.55);
        col = uStar * g * limb * 1.5;
        col = mix(col, vec3(1.0), pow(ndv, 6.0) * 0.35);
    } else if (uKind > 0.5) {
        float n1 = noise(vPos * 12.0 + vec3(uTime * 0.05));
        float n2 = noise(vPos * 30.0 - vec3(uTime * 0.09));
        float limb = 0.45 + 0.55 * pow(ndv, 0.5);
        col = t.rgb * (0.86 + 0.3 * n1 * n2) * limb * 1.45;
    } else {
        float ndl = dot(N, normalize(uLight));
        float lit = smoothstep(-0.04, 0.22, ndl);
        col = t.rgb * (uAmbient + (1.0 - uAmbient) * lit);
        float rim = pow(1.0 - ndv, 3.0);
        col += uAtm * rim * (0.2 + 0.8 * lit) * 0.9;
    }
    gl_FragColor = vec4(col, alpha);
}
"""

private const val HALO_VERT = """
uniform mat4 uMV;
uniform mat4 uP;
attribute vec2 aQuad;
varying vec2 vQ;
void main() {
    vQ = aQuad;
    gl_Position = uP * uMV * vec4(aQuad, 0.0, 1.0);
}
"""

private const val HALO_FRAG = """
precision highp float;
uniform vec3 uColor;
uniform float uSil;
uniform float uTime;
uniform float uStrength;
uniform float uRays;
varying vec2 vQ;
void main() {
    float r = length(vQ) / uSil;
    float h = pow(1.0 - smoothstep(1.0, 1.55, r), 2.2);
    float a = atan(vQ.y, vQ.x);
    float rays = 1.0 + uRays * (0.35 * sin(a * 13.0 + uTime * 0.5) * sin(a * 7.0 - uTime * 0.31));
    float v = h * uStrength * rays * step(0.97, r);
    gl_FragColor = vec4(uColor * v, v);
}
"""

private class MsaaChooser : GLSurfaceView.EGLConfigChooser {
    override fun chooseConfig(egl: EGL10, display: EGLDisplay): EGLConfig {
        for (samples in intArrayOf(4, 2, 0)) {
            val base = intArrayOf(
                EGL10.EGL_RED_SIZE, 8, EGL10.EGL_GREEN_SIZE, 8, EGL10.EGL_BLUE_SIZE, 8,
                EGL10.EGL_ALPHA_SIZE, 8, EGL10.EGL_DEPTH_SIZE, 16, EGL10.EGL_RENDERABLE_TYPE, 4
            )
            val attrs = if (samples > 0) {
                base + intArrayOf(EGL10.EGL_SAMPLE_BUFFERS, 1, EGL10.EGL_SAMPLES, samples, EGL10.EGL_NONE)
            } else {
                base + intArrayOf(EGL10.EGL_NONE)
            }
            val num = IntArray(1)
            egl.eglChooseConfig(display, attrs, null, 0, num)
            if (num[0] > 0) {
                val configs = arrayOfNulls<EGLConfig>(num[0])
                egl.eglChooseConfig(display, attrs, configs, num[0], num)
                val c = configs[0]
                if (c != null) return c
            }
        }
        throw IllegalArgumentException("No suitable EGL configuration")
    }
}

class SphereRenderer(
    private val ctx: Context,
    private val spec: BodySpec,
    starColor0: FloatArray,
    private val moonPhase: Float
) : GLSurfaceView.Renderer {

    @Volatile var starColor: FloatArray = starColor0
    @Volatile var yaw = spec.yawStart
    @Volatile var pitch = 12f
    @Volatile var zoom = 1f
    @Volatile var autoSpin = true

    private var prog = 0
    private var haloProg = 0
    private lateinit var sphere: Mesh
    private var ring: Mesh? = null
    private var texBody = 0
    private var texRing = 0
    private var texSky = 0
    private var quad: FloatBuffer? = null

    private val proj = FloatArray(16)
    private val mv = FloatArray(16)
    private val nm = FloatArray(9)
    private var baseDist = 4f
    private var last = 0L
    private var time = 0f

    private fun compile(type: Int, src: String): Int {
        val s = GLES20.glCreateShader(type)
        GLES20.glShaderSource(s, src)
        GLES20.glCompileShader(s)
        val ok = IntArray(1)
        GLES20.glGetShaderiv(s, GLES20.GL_COMPILE_STATUS, ok, 0)
        if (ok[0] == 0) Log.e("EyeSky3D", "shader error: " + GLES20.glGetShaderInfoLog(s))
        return s
    }

    private fun link(v: String, f: String): Int {
        val p = GLES20.glCreateProgram()
        GLES20.glAttachShader(p, compile(GLES20.GL_VERTEX_SHADER, v))
        GLES20.glAttachShader(p, compile(GLES20.GL_FRAGMENT_SHADER, f))
        GLES20.glLinkProgram(p)
        return p
    }

    private fun isPot(n: Int) = n > 0 && (n and (n - 1)) == 0

    private fun loadTexture(name: String?): Int {
        val ids = IntArray(1)
        GLES20.glGenTextures(1, ids, 0)
        GLES20.glBindTexture(GLES20.GL_TEXTURE_2D, ids[0])
        var bmp: Bitmap? = null
        if (name != null) {
            var sample = 1
            while (bmp == null && sample <= 8) {
                try {
                    val o = BitmapFactory.Options()
                    o.inSampleSize = sample
                    ctx.assets.open("textures/$name").use { bmp = BitmapFactory.decodeStream(it, null, o) }
                    if (bmp == null) break
                } catch (e: OutOfMemoryError) {
                    sample *= 2
                } catch (e: Exception) {
                    Log.e("EyeSky3D", "texture $name: " + e.message)
                    break
                }
            }
        }
        val b = bmp
        if (b == null) {
            val px = Bitmap.createBitmap(2, 2, Bitmap.Config.ARGB_8888)
            px.eraseColor(0xFF808080.toInt())
            GLUtils.texImage2D(GLES20.GL_TEXTURE_2D, 0, px, 0)
            px.recycle()
            GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D, GLES20.GL_TEXTURE_MIN_FILTER, GLES20.GL_LINEAR)
            GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D, GLES20.GL_TEXTURE_MAG_FILTER, GLES20.GL_LINEAR)
            return ids[0]
        }
        val pot = isPot(b.width) && isPot(b.height)
        GLUtils.texImage2D(GLES20.GL_TEXTURE_2D, 0, b, 0)
        b.recycle()
        GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D, GLES20.GL_TEXTURE_MAG_FILTER, GLES20.GL_LINEAR)
        GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D, GLES20.GL_TEXTURE_WRAP_T, GLES20.GL_CLAMP_TO_EDGE)
        if (pot) {
            GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D, GLES20.GL_TEXTURE_WRAP_S, GLES20.GL_REPEAT)
            GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D, GLES20.GL_TEXTURE_MIN_FILTER, GLES20.GL_LINEAR_MIPMAP_LINEAR)
            GLES20.glGenerateMipmap(GLES20.GL_TEXTURE_2D)
            try {
                val maxA = FloatArray(1)
                GLES20.glGetFloatv(GLES11Ext.GL_MAX_TEXTURE_MAX_ANISOTROPY_EXT, maxA, 0)
                if (maxA[0] > 1f) {
                    GLES20.glTexParameterf(
                        GLES20.GL_TEXTURE_2D, GLES11Ext.GL_TEXTURE_MAX_ANISOTROPY_EXT, min(8f, maxA[0])
                    )
                }
            } catch (e: Exception) { }
        } else {
            GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D, GLES20.GL_TEXTURE_WRAP_S, GLES20.GL_CLAMP_TO_EDGE)
            GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D, GLES20.GL_TEXTURE_MIN_FILTER, GLES20.GL_LINEAR)
        }
        return ids[0]
    }

    override fun onSurfaceCreated(gl: GL10?, config: EGLConfig?) {
        GLES20.glClearColor(0.01f, 0.015f, 0.04f, 1f)
        GLES20.glEnable(GLES20.GL_DEPTH_TEST)
        prog = link(VERT, FRAG)
        haloProg = link(HALO_VERT, HALO_FRAG)
        sphere = buildSphere(96, 192)
        if (spec.rings) ring = buildRing(192, 1.24f, 2.27f)
        quad = floatBuf(floatArrayOf(-2f, -2f, 2f, -2f, -2f, 2f, 2f, 2f))
        texBody = loadTexture(spec.texture)
        texSky = loadTexture("milkyway.jpg")
        if (spec.rings) texRing = loadTexture("saturn_ring.png")
        last = System.nanoTime()
    }

    override fun onSurfaceChanged(gl: GL10?, width: Int, height: Int) {
        GLES20.glViewport(0, 0, width, height)
        val aspect = width.toFloat() / height.toFloat()
        val fovV = 38f
        Matrix.perspectiveM(proj, 0, fovV, aspect, 0.1f, 80f)
        val halfV = Math.toRadians(fovV / 2.0)
        val halfH = atan(tan(halfV) * aspect)
        val half = min(halfV, halfH)
        val extent = if (spec.rings) 2.4 else 1.15
        baseDist = (extent / sin(half)).toFloat()
    }

    private fun uni(name: String) = GLES20.glGetUniformLocation(prog, name)

    private fun setNormalMatrix() {
        nm[0] = mv[0]; nm[1] = mv[1]; nm[2] = mv[2]
        nm[3] = mv[4]; nm[4] = mv[5]; nm[5] = mv[6]
        nm[6] = mv[8]; nm[7] = mv[9]; nm[8] = mv[10]
    }

    private fun drawMesh(m: Mesh) {
        val aPos = GLES20.glGetAttribLocation(prog, "aPos")
        val aNormal = GLES20.glGetAttribLocation(prog, "aNormal")
        val aUV = GLES20.glGetAttribLocation(prog, "aUV")
        m.v.position(0)
        GLES20.glVertexAttribPointer(aPos, 3, GLES20.GL_FLOAT, false, 32, m.v)
        GLES20.glEnableVertexAttribArray(aPos)
        m.v.position(3)
        GLES20.glVertexAttribPointer(aNormal, 3, GLES20.GL_FLOAT, false, 32, m.v)
        GLES20.glEnableVertexAttribArray(aNormal)
        m.v.position(6)
        GLES20.glVertexAttribPointer(aUV, 2, GLES20.GL_FLOAT, false, 32, m.v)
        GLES20.glEnableVertexAttribArray(aUV)
        m.idx.position(0)
        GLES20.glDrawElements(GLES20.GL_TRIANGLES, m.count, GLES20.GL_UNSIGNED_SHORT, m.idx)
    }

    private fun lightDir(): FloatArray {
        if (spec.key == "moon") {
            val a = moonPhase * 2.0 * PI
            return floatArrayOf(sin(a).toFloat(), 0.12f, (-cos(a)).toFloat())
        }
        return floatArrayOf(-0.55f, 0.3f, 0.78f)
    }

    private fun bind(texture: Int, kind: Float, ambient: Float, bright: Float, atm: FloatArray?) {
        GLES20.glUseProgram(prog)
        GLES20.glActiveTexture(GLES20.GL_TEXTURE0)
        GLES20.glBindTexture(GLES20.GL_TEXTURE_2D, texture)
        GLES20.glUniform1i(uni("uTex"), 0)
        GLES20.glUniformMatrix4fv(uni("uP"), 1, false, proj, 0)
        GLES20.glUniformMatrix4fv(uni("uMV"), 1, false, mv, 0)
        setNormalMatrix()
        GLES20.glUniformMatrix3fv(uni("uNM"), 1, false, nm, 0)
        val l = lightDir()
        GLES20.glUniform3f(uni("uLight"), l[0], l[1], l[2])
        GLES20.glUniform3f(uni("uAtm"), atm?.get(0) ?: 0f, atm?.get(1) ?: 0f, atm?.get(2) ?: 0f)
        GLES20.glUniform3f(uni("uStar"), starColor[0], starColor[1], starColor[2])
        GLES20.glUniform1f(uni("uKind"), kind)
        GLES20.glUniform1f(uni("uAmbient"), ambient)
        GLES20.glUniform1f(uni("uBright"), bright)
        GLES20.glUniform1f(uni("uTime"), time)
    }

    private fun drawHalo(dist: Float, color: FloatArray, strength: Float, rays: Float) {
        val q = quad ?: return
        Matrix.setIdentityM(mv, 0)
        Matrix.translateM(mv, 0, 0f, 0f, -dist)
        GLES20.glUseProgram(haloProg)
        GLES20.glUniformMatrix4fv(GLES20.glGetUniformLocation(haloProg, "uP"), 1, false, proj, 0)
        GLES20.glUniformMatrix4fv(GLES20.glGetUniformLocation(haloProg, "uMV"), 1, false, mv, 0)
        GLES20.glUniform3f(GLES20.glGetUniformLocation(haloProg, "uColor"), color[0], color[1], color[2])
        GLES20.glUniform1f(GLES20.glGetUniformLocation(haloProg, "uSil"), dist / sqrt(dist * dist - 1f))
        GLES20.glUniform1f(GLES20.glGetUniformLocation(haloProg, "uTime"), time)
        GLES20.glUniform1f(GLES20.glGetUniformLocation(haloProg, "uStrength"), strength)
        GLES20.glUniform1f(GLES20.glGetUniformLocation(haloProg, "uRays"), rays)
        val a = GLES20.glGetAttribLocation(haloProg, "aQuad")
        q.position(0)
        GLES20.glVertexAttribPointer(a, 2, GLES20.GL_FLOAT, false, 8, q)
        GLES20.glEnableVertexAttribArray(a)
        GLES20.glDrawArrays(GLES20.GL_TRIANGLE_STRIP, 0, 4)
    }

    override fun onDrawFrame(gl: GL10?) {
        val now = System.nanoTime()
        val dt = ((now - last) / 1.0e9f).coerceAtMost(0.1f)
        last = now
        time += dt
        if (autoSpin) yaw += spec.spinDegPerSec * dt
        val dist = baseDist * zoom

        GLES20.glClear(GLES20.GL_COLOR_BUFFER_BIT or GLES20.GL_DEPTH_BUFFER_BIT)

        // Milky Way backdrop
        GLES20.glDisable(GLES20.GL_DEPTH_TEST)
        GLES20.glDisable(GLES20.GL_BLEND)
        Matrix.setIdentityM(mv, 0)
        Matrix.rotateM(mv, 0, pitch * 0.15f, 1f, 0f, 0f)
        Matrix.rotateM(mv, 0, yaw * 0.08f, 0f, 1f, 0f)
        Matrix.scaleM(mv, 0, 30f, 30f, 30f)
        bind(texSky, 4f, 1f, 0.55f, null)
        drawMesh(sphere)

        // glow behind the body
        GLES20.glEnable(GLES20.GL_BLEND)
        GLES20.glBlendFunc(GLES20.GL_ONE, GLES20.GL_ONE)
        val atm = spec.atmosphere
        if (spec.kind == 1f) drawHalo(dist, floatArrayOf(1f, 0.62f, 0.22f), 1.25f, 1f)
        else if (spec.kind == 2f) drawHalo(dist, starColor, 1.1f, 1f)
        else if (atm != null) drawHalo(dist, atm, 0.55f, 0f)
        GLES20.glDisable(GLES20.GL_BLEND)

        // the body
        GLES20.glEnable(GLES20.GL_DEPTH_TEST)
        Matrix.setIdentityM(mv, 0)
        Matrix.translateM(mv, 0, 0f, 0f, -dist)
        Matrix.rotateM(mv, 0, pitch, 1f, 0f, 0f)
        Matrix.rotateM(mv, 0, spec.tiltDeg, 0f, 0f, 1f)
        val ringMv = mv.copyOf()
        Matrix.rotateM(mv, 0, yaw, 0f, 1f, 0f)
        val ambient = if (spec.key == "moon") 0.04f else 0.07f
        bind(texBody, spec.kind, ambient, 1f, atm)
        drawMesh(sphere)

        // Saturn's rings
        val r = ring
        if (r != null) {
            System.arraycopy(ringMv, 0, mv, 0, 16)
            GLES20.glEnable(GLES20.GL_BLEND)
            GLES20.glBlendFunc(GLES20.GL_SRC_ALPHA, GLES20.GL_ONE_MINUS_SRC_ALPHA)
            bind(texRing, 3f, 0.25f, 1f, null)
            drawMesh(r)
            GLES20.glDisable(GLES20.GL_BLEND)
        }
    }
}

/** A 3D body you can spin with a finger and zoom with a pinch. */
@Composable
fun BodyView(
    spec: BodySpec,
    starColor: FloatArray,
    moonPhase: Float,
    modifier: Modifier = Modifier
) {
    val ctx = LocalContext.current
    val renderer = remember(spec.key) {
        SphereRenderer(ctx.applicationContext, spec, starColor, moonPhase)
    }
    renderer.starColor = starColor
    val glRef = remember { arrayOfNulls<GLSurfaceView>(1) }

    DisposableEffect(renderer) {
        val owner = ctx as? ComponentActivity
        val obs = LifecycleEventObserver { _, e ->
            if (e == Lifecycle.Event.ON_RESUME) glRef[0]?.onResume()
            else if (e == Lifecycle.Event.ON_PAUSE) glRef[0]?.onPause()
        }
        owner?.lifecycle?.addObserver(obs)
        onDispose {
            owner?.lifecycle?.removeObserver(obs)
            glRef[0]?.onPause()
        }
    }

    AndroidView(
        factory = { c ->
            GLSurfaceView(c).apply {
                setEGLContextClientVersion(2)
                setEGLConfigChooser(MsaaChooser())
                setRenderer(renderer)
                renderMode = GLSurfaceView.RENDERMODE_CONTINUOUSLY
                glRef[0] = this

                val scale = ScaleGestureDetector(c, object : ScaleGestureDetector.SimpleOnScaleGestureListener() {
                    override fun onScale(d: ScaleGestureDetector): Boolean {
                        renderer.zoom = (renderer.zoom / d.scaleFactor).coerceIn(0.45f, 2.4f)
                        return true
                    }
                })
                var lx = 0f
                var ly = 0f
                var lastCount = 0
                setOnTouchListener { v, e ->
                    scale.onTouchEvent(e)
                    when (e.actionMasked) {
                        MotionEvent.ACTION_DOWN -> {
                            lx = e.x; ly = e.y; lastCount = 1
                            renderer.autoSpin = false
                            v.parent?.requestDisallowInterceptTouchEvent(true)
                        }
                        MotionEvent.ACTION_MOVE -> {
                            if (e.pointerCount == 1 && !scale.isInProgress) {
                                if (lastCount != 1) { lx = e.x; ly = e.y }
                                renderer.yaw += (e.x - lx) * 0.35f
                                renderer.pitch = (renderer.pitch + (e.y - ly) * 0.35f).coerceIn(-85f, 85f)
                                lx = e.x; ly = e.y
                            }
                            lastCount = e.pointerCount
                        }
                        MotionEvent.ACTION_UP, MotionEvent.ACTION_CANCEL -> {
                            renderer.autoSpin = true
                            lastCount = 0
                        }
                    }
                    true
                }
            }
        },
        modifier = modifier
    )
}
