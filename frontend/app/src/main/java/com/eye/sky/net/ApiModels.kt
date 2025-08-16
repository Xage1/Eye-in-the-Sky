package com.eye.sky.net

// --- AUTH ---
data class LoginReq(val email: String, val password: String, val name: String? = null)
data class TokenResp(val access_token: String, val token_type: String)

// --- LESSONS ---
data class Lesson(val id: Int, val title: String, val content: String, val category: String? = null, val difficulty: String? = null)

// --- QUIZ ---
data class QuizQuestionDto(val id: Int, val question_text: String, val options: List<String>)
data class QuizAnswerIn(val question_id: Int, val selected_answer: String, val correct_answer: String)
data class QuizSubmissionCreate(val answers: List<QuizAnswerIn>)
data class QuizSubmissionOut(
    val id: Int, val user_id: Int, val timestamp: String,
    val score: Int, val total_questions: Int, val answers: List<QuizAnswerOut>?
)
data class QuizAnswerOut(
    val id: Int, val submission_id: Int, val question_id: Int,
    val selected_answer: String, val correct_answer: String
)

// --- SKY INFO / EVENTS ---
data class VisibilityResp(val visibility: VisibilityData?)
data class VisibilityData(val visibility_km: Double?, val cloud_coverage_percent: Int?, val sky_clear: Boolean?)
data class MoonPhaseResp(val moon_phase: Any?) // backend passes through 3rd-party payload
data class NightSkyEventsResp(val astronomy: Any?, val weather: Any?)

// --- STAR MAP ---
data class StarMapResp(val constellations: Any?) // backend returns constellation list/details

// --- SATELLITES ---
data class TleText(val raw: String) // we'll receive text; we treat response body as string
data class IssPos(val iss_position: Map<String, String>?, val timestamp: Long?)

// --- WATCHLIST ---
data class WatchItemCreate(val star_name: String, val constellation: String? = null, val description: String? = null)
data class WatchItemOut(val id: Int, val user_id: Int, val star_name: String, val constellation: String?, val description: String?, val added_on: String)