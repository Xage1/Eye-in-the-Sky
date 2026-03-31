package com.eye.sky.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.eye.sky.net.QuizAnswerIn
import com.eye.sky.net.QuizQuestionDto
import com.eye.sky.net.QuizSubmissionCreate
import com.eye.sky.net.QuizSubmissionOut
import com.eye.sky.repo.QuizRepository
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch

class QuizViewModel(
    private val repo: QuizRepository = QuizRepository(),
) : ViewModel() {

    val topics = listOf("All", "Planets", "Cosmology", "Exoplanets", "Stars", "Events")

    private val _questions = MutableStateFlow<List<QuizQuestionDto>>(emptyList())
    val questions: StateFlow<List<QuizQuestionDto>> = _questions

    private val _answers = MutableStateFlow(mutableMapOf<Int, String>())
    val answers: StateFlow<Map<Int, String>> = _answers

    private val _submission = MutableStateFlow<QuizSubmissionOut?>(null)
    val submission: StateFlow<QuizSubmissionOut?> = _submission

    private val _timeleft = MutableStateFlow(0L)
    val timeleft: StateFlow<Long> = _timeleft

    private var timerRunning = false

    private val durations = mapOf(
        "simple"   to 120L,
        "medium"   to 180L,
        "difficult" to 300L,
    )

    fun loadQuestions(difficulty: String, topic: String?) {
        viewModelScope.launch {
            val list = repo.fetchQuestions(difficulty, topic)
            _questions.value = list
            _answers.value = mutableMapOf()
            _submission.value = null
            _timeleft.value = durations[difficulty.lowercase()] ?: 120L
            startTimer()
        }
    }

    private fun startTimer() {
        if (timerRunning) return
        timerRunning = true
        viewModelScope.launch {
            while (_timeleft.value > 0) {
                delay(1000)
                _timeleft.value -= 1
            }
            timerRunning = false
            submitQuiz()
        }
    }

    fun setAnswer(qid: Int, ans: String) {
        _answers.value = _answers.value.toMutableMap().apply { put(qid, ans) }
    }

    fun submitQuiz() {
        viewModelScope.launch {
            val payload = QuizSubmissionCreate(
                answers = _answers.value.map { (qid, selected) ->
                    // correct_answer sent as empty string — backend scores server-side
                    QuizAnswerIn(
                        question_id = qid,
                        selected_answer = selected,
                        correct_answer = "",
                    )
                }
            )
            _submission.value = runCatching { repo.submit(payload) }.getOrNull()
        }
    }
}