package com.eye.sky.net

data class QuizQuestionDto(
    val id: String,
    val question_text: String,
    val options: List<String>,
    val topic: String? = null,
    val difficulty: String? = null
)

data class QuizAnswerIn(
    val question_id: Int,
    val selected_answer: String,
    val correct_answer: String = ""
)

data class QuizSubmissionCreate(
    val answers: List<QuizAnswerIn>
)

data class QuizAnswerOut(
    val id: Int,
    val question_id: Int,
    val selected_answer: String,
    val correct_answer: String
)


data class QuizSubmissionOut(
    val id: Int,
    val user_id: Int,
    val timestamp: String,
    val score: Int,
    val total_questions: Int,
    val answers: List<QuizAnswerOut>
)