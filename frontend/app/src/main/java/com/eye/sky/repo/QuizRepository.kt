package com.eye.sky.repo

import com.eye.sky.net.*

class QuizRepository{
    suspend fun fetchQuestions(difficulty: String?, topic: String?): List<QuizQuestionDto> {
        return Api.service.quiz(difficulty = difficulty, topic = topic, limit = 50)
    }

    suspend fun submit(payload: QuizSubmissionCreate): QuizSubmissionOut {
    return Api.service.submitQuiz(payload)
    }
    
}