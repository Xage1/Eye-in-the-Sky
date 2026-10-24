package ke.eyesky.app

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject
import java.util.concurrent.TimeUnit

class ApiException(val code: Int, message: String) : Exception(message)

/**
 * Backend client. In development the phone reaches the PC through "adb reverse tcp:8000 tcp:8000",
 * so localhost on the phone is the backend. For production this becomes the HTTPS domain.
 */
object Api {
    const val BASE_URL = "http://localhost:8000"

    private val client = OkHttpClient.Builder()
        .connectTimeout(15, TimeUnit.SECONDS)
        .readTimeout(60, TimeUnit.SECONDS)
        .build()
    private val JSON = "application/json".toMediaType()

    var token: String? = null

    private suspend fun call(method: String, path: String, body: JSONObject? = null): JSONObject =
        withContext(Dispatchers.IO) {
            val b = Request.Builder().url(BASE_URL + path)
            token?.let { b.header("Authorization", "Bearer $it") }
            if (method == "POST") {
                b.post((body?.toString() ?: "{}").toRequestBody(JSON))
            } else {
                b.get()
            }
            client.newCall(b.build()).execute().use { r ->
                val text = r.body?.string().orEmpty()
                if (!r.isSuccessful) {
                    val detail = try {
                        JSONObject(text).opt("detail")?.toString()
                    } catch (e: Exception) {
                        null
                    }
                    throw ApiException(r.code, detail ?: ("HTTP " + r.code))
                }
                if (text.isBlank()) JSONObject() else JSONObject(text)
            }
        }

    suspend fun login(email: String, password: String) {
        val r = call(
            "POST", "/auth/login",
            JSONObject().put("email", email).put("password", password)
        )
        val t = r.optString("access_token").ifBlank { r.optString("token") }
        if (t.isBlank()) throw ApiException(0, "Login response had no token")
        token = t
    }

    suspend fun signup(name: String, email: String, password: String) {
        call(
            "POST", "/auth/signup",
            JSONObject().put("name", name).put("email", email).put("password", password)
        )
        login(email, password)
    }

    suspend fun me(): JSONObject = call("GET", "/auth/me")

    suspend fun subscription(): JSONObject = call("GET", "/payments/subscription")

    /** Whole sky: stars (RA/Dec, only when withStars) plus moving bodies (Alt/Az). */
    suspend fun dome(lat: Double, lon: Double, withStars: Boolean, magLimit: Double = 5.5): JSONObject =
        call("GET", "/skyinfo/dome?lat=$lat&lon=$lon&mag_limit=$magLimit&stars=$withStars")
}
