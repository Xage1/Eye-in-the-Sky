package com.eye.sky.net

import okhttp3.OkHttpClient
import okhttp3.Interceptor
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Response
import retrofit2.Retrofit
import retrofit2.converter.moshi.MoshiConverterFactory
import retrofit2.http.*
import com.squareup.moshi.Moshi
import com.squareup.moshi.kotlin.reflect.KotlinJsonAdapterFactory

/**
 * BASE_URL — use USB reverse tunnel for physical device:
 *   adb reverse tcp:8000 tcp:8000
 * Then set to http://localhost:8000/
 *
 * For WiFi: http://YOUR_PC_IP:8000/
 * For emulator: http://10.0.2.2:8000/
 */
private const val BASE_URL = "http://localhost:8000/"

object Session {
    @Volatile var token: String? = null
}

class AuthInterceptor : Interceptor {
    override fun intercept(chain: Interceptor.Chain): okhttp3.Response {
        val req = Session.token?.let {
            chain.request().newBuilder()
                .addHeader("Authorization", "Bearer $it")
                .build()
        } ?: chain.request()
        return chain.proceed(req)
    }
}

private val moshi = Moshi.Builder()
    .addLast(KotlinJsonAdapterFactory())
    .build()

private val okClient = OkHttpClient.Builder()
    .addInterceptor(AuthInterceptor())
    .addInterceptor(HttpLoggingInterceptor().apply { level = HttpLoggingInterceptor.Level.BASIC })
    .connectTimeout(15, java.util.concurrent.TimeUnit.SECONDS)
    .readTimeout(20, java.util.concurrent.TimeUnit.SECONDS)
    .build()

private val retrofit = Retrofit.Builder()
    .baseUrl(BASE_URL)
    .addConverterFactory(MoshiConverterFactory.create(moshi))
    .client(okClient)
    .build()

interface ApiService {

    // ── Auth ──────────────────────────────────────────────────────────────────
    @POST("auth/signup")
    suspend fun signup(@Body body: SignupReq): Response<TokenResp>

    @POST("auth/login")
    suspend fun login(@Body body: LoginReq): TokenResp

    @GET("auth/me")
    suspend fun me(): Map<String, Any?>

    // ── Lessons (GET /lessons/) ───────────────────────────────────────────────
    @GET("lessons/")
    suspend fun lessons(
        @Query("category")   category:   String? = null,
        @Query("difficulty") difficulty: String? = null,
    ): List<Lesson>

    // ── Quiz (GET /quiz/) ─────────────────────────────────────────────────────
    @GET("quiz/")
    suspend fun quiz(
        @Query("difficulty") difficulty: String? = null,
        @Query("topic")      topic:      String? = null,
    ): List<QuizQuestionDto>

    @POST("quiz/submit")
    suspend fun submitQuiz(@Body payload: QuizSubmissionCreate): QuizSubmissionOut

    @GET("quiz/history")
    suspend fun quizHistory(): List<QuizSubmissionOut>

    // ── Sky scene — master AR endpoint (GET /skyinfo/scene) ───────────────────
    @GET("skyinfo/scene")
    suspend fun skyScene(
        @Query("lat")        lat:        Double,
        @Query("lon")        lon:        Double,
        @Query("az")         az:         Double,
        @Query("alt")        alt:        Double,
        @Query("roll")       roll:       Double  = 0.0,
        @Query("screen_w")   screenW:    Int     = 1080,
        @Query("screen_h")   screenH:    Int     = 1920,
        @Query("fov_h")      fovH:       Double  = 60.0,
        @Query("fov_v")      fovV:       Double  = 110.0,
        @Query("mag_limit")  magLimit:   Double  = 5.5,
        @Query("planets")    planets:    Boolean = true,
        @Query("satellites") satellites: Boolean = true,
        @Query("iss")        iss:        Boolean = true,
        @Query("events")     events:     Boolean = false,
        @Query("weather")    weather:    Boolean = false,
    ): SkySceneResp

    // ── Moon phase (GET /skyinfo/moon-phase) ──────────────────────────────────
    @GET("skyinfo/moon-phase")
    suspend fun moonPhase(
        @Query("lat")  lat:  Double,
        @Query("lon")  lon:  Double,
        @Query("date") date: String? = null,
    ): MoonPhaseResp

    // ── Star detail tap-to-learn (GET /skyinfo/star/{name}) ───────────────────
    @GET("skyinfo/star/{name}")
    suspend fun starDetail(@Path("name") name: String): Map<String, Any?>

    // ── ISS (GET /skyinfo/iss) ────────────────────────────────────────────────
    @GET("skyinfo/iss")
    suspend fun iss(
        @Query("lat") lat: Double,
        @Query("lon") lon: Double,
    ): Map<String, Any?>

    // ── Payments ──────────────────────────────────────────────────────────────
    @GET("payments/plans")
    suspend fun plans(): Map<String, Any?>

    @GET("payments/subscription")
    suspend fun subscription(): Map<String, Any?>

    @POST("payments/checkout")
    suspend fun paystackCheckout(@Body body: Map<String, Any>): Map<String, Any?>

    @POST("payments/verify")
    suspend fun verifyPayment(@Body body: Map<String, String>): Map<String, Any?>

    // ── Watchlist ─────────────────────────────────────────────────────────────
    @GET("watchlist/")
    suspend fun watchlist(): List<Map<String, Any?>>

    @POST("watchlist/")
    suspend fun addToWatchlist(@Body body: Map<String, String>): Map<String, Any?>

    // ── Events ────────────────────────────────────────────────────────────────
    @GET("events/night-sky")
    suspend fun nightSkyEvents(
        @Query("lat") lat: Double,
        @Query("lon") lon: Double,
    ): Map<String, Any?>
}

object Api {
    val service: ApiService by lazy { retrofit.create(ApiService::class.java) }
}