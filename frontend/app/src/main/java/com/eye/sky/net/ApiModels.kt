package com.eye.sky.net

/**
 * Data models matching the actual backend schemas.
 * Cross-checked against full_project_source_v4.txt.
 */

// ── Auth ──────────────────────────────────────────────────────────────────────
data class LoginReq(val email: String, val password: String)
data class SignupReq(val name: String, val email: String, val password: String)
data class TokenResp(
    val access_token: String,
    val token_type:   String,
    val role:         String,
    val plan:         String,
)

// ── Lessons ───────────────────────────────────────────────────────────────────
data class Lesson(
    val id:         Int,
    val title:      String,
    val content:    String,
    val category:   String?,
    val difficulty: String?,
    val created_at: String?,
)

// ── Quiz ──────────────────────────────────────────────────────────────────────
data class QuizQuestionDto(
    val id:            Int,
    val question_text: String,
    val options:       List<String>,
)

data class QuizAnswerIn(
    val question_id:     Int,
    val selected_answer: String,
    val correct_answer:  String,
)

data class QuizSubmissionCreate(val answers: List<QuizAnswerIn>)

data class QuizAnswerOut(
    val id:              Int,
    val question_id:     Int,
    val selected_answer: String,
    val correct_answer:  String,
)

data class QuizSubmissionOut(
    val id:              Int,
    val user_id:         Int,
    val timestamp:       String?,
    val score:           Int,
    val total_questions: Int,
    val answers:         List<QuizAnswerOut>,
)

// ── Events ────────────────────────────────────────────────────────────────────
data class NightSkyEventsResp(val events: List<Any?>?)

// ── Moon phase (standalone endpoint) ─────────────────────────────────────────
data class MoonPhaseResp(
    val observer:   Map<String, Double>?,
    val datetime:   String?,
    val moon_phase: MoonPhaseDto?,
)

// ── Visibility ────────────────────────────────────────────────────────────────
data class VisibilityResp(
    val observer:   Map<String, Double>?,
    val visibility: Map<String, Any?>?,
)