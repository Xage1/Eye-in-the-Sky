package com.eye.sky.net

import okhttp3.Interceptor
import okhttp3.OkHttpClient
import okhttp3.ResponseBody
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Response
import retrofit2.Retrofit
import retrofit2.converter.moshi.MoshiConverterFactory
import retrofit2.http.*

private const val BASE_URL = "http://10.0.2.2:8000/" // emulator->host; change for device

object Session {
    @Volatile var token: String? = null
}

class AuthInterceptor : Interceptor {
    override fun intercept(chain: Interceptor.Chain): okhttp3.Response {
        val t = Session.token
        val req = if (t != null) chain.request().newBuilder()
            .addHeader("Authorization", "Bearer $t").build()
        else chain.request()
        return chain.proceed(req)
    }
}

private val client: OkHttpClient by lazy {
    OkHttpClient.Builder()
        .addInterceptor(AuthInterceptor())
        .addInterceptor(HttpLoggingInterceptor().apply { level = HttpLoggingInterceptor.Level.BODY })
        .build()
}

private val retrofit: Retrofit by lazy {
    Retrofit.Builder()
        .baseUrl(BASE_URL)
        .addConverterFactory(MoshiConverterFactory.create())
        .client(client)
        .build()
}

interface ApiService {
    // --- Auth ---
    @POST("auth/signup") suspend fun signup(@Body body: LoginReq): Response<Unit>
    @POST("auth/login") suspend fun login(@Body body: LoginReq): TokenResp

    // --- Lessons ---
    @GET("lessons/") suspend fun lessons(): List<Lesson>

    // --- Quiz ---
    @GET("quiz/")
        suspend fun quiz(
        @Query("difficulty") difficulty: String?,
        @Query("topic") topic: String?
    ): List<QuizQuestionDto>

    @POST("quiz/submit")
        suspend fun submitQuiz(
    @Body payload: QuizSubmissionCreate
    ): QuizSubmissionOut

    @GET("quiz/history")
        suspend fun quizHistory(): List<QuizSubmissionOut>
// --- Sky info & events ---
    @GET("skyinfo/visibility") suspend fun visibility(@Query("lat") lat: Double, @Query("lon") lon: Double): VisibilityResp
    @GET("skyinfo/moon-phase") suspend fun moonPhase(@Query("lat") lat: Double, @Query("lon") lon: Double, @Query("date") date: String): MoonPhaseResp
    @GET("events/night-sky") suspend fun nightSky(@Query("lat") lat: Double, @Query("lon") lon: Double): NightSkyEventsResp

    // --- Star map ---
    @GET("starmap/") suspend fun starmap(@Query("lat") lat: Double, @Query("lon") lon: Double, @Query("date") date: String?): StarMapResp

    // --- Satellites ---
    @GET("satellites/tle") suspend fun tle(): Response<ResponseBody> // raw text
    @GET("satellites/iss") suspend fun iss(): Any // backend proxies OpenNotify-like payload
}

object Api {
    val service: ApiService by lazy { retrofit.create(ApiService::class.java) }
}