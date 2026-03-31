package com.eye.sky.repo

import com.eye.sky.net.Api
import com.eye.sky.net.QuizQuestionDto
import com.eye.sky.net.QuizSubmissionCreate
import com.eye.sky.net.QuizSubmissionOut

class QuizRepository {
    suspend fun fetchQuestions(
        difficulty: String?,
        topic: String?,
    ): List<QuizQuestionDto> {
        // API signature: quiz(difficulty, topic) — no limit param
        return Api.service.quiz(difficulty = difficulty, topic = topic)
    }

    suspend fun submit(payload: QuizSubmissionCreate): QuizSubmissionOut {
        return Api.service.submitQuiz(payload)
    }
}