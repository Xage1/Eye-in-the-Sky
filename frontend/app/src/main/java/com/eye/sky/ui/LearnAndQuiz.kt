package com.eye.sky.ui

import androidx.compose.animation.*
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.compose.ui.Alignment
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.sp
import com.eye.sky.net.*
import com.eye.sky.ui.components.*
import com.eye.sky.R
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch

@OptIn(ExperimentalAnimationApi::class)
@Composable
fun LearnAndQuizScreen() {

    val scope = rememberCoroutineScope()

    var lessons by remember { mutableStateOf<List<Lesson>>(emptyList()) }
    var questions by remember { mutableStateOf<List<QuizQuestionDto>>(emptyList()) }

    var currentIndex by remember { mutableStateOf(0) }
    var answers by remember { mutableStateOf(mutableMapOf<Int, String>()) }

    var result by remember { mutableStateOf<QuizSubmissionOut?>(null) }

    // animations
    var showMeteor by remember { mutableStateOf(false) }
    var showPlanetAlign by remember { mutableStateOf(false) }
    var showLoader by remember { mutableStateOf(false) }

    // timer
    var timeLeft by remember { mutableStateOf(30) }
    var timerRunning by remember { mutableStateOf(true) }

    LaunchedEffect(Unit) {
        showLoader = true
        lessons = runCatching { Api.service.lessons() }.getOrDefault(emptyList())
        questions = runCatching { Api.service.quiz(difficulty = "simple", topic = null) }.getOrDefault(emptyList())
        showLoader = false
    }

    // Timer effect
    LaunchedEffect(currentIndex) {
        timeLeft = 30
        timerRunning = true
        while (timeLeft > 0 && timerRunning) {
            delay(1000)
            timeLeft -= 1
        }
        if (timeLeft == 0) {
            // auto move to next
            if (currentIndex < questions.lastIndex) {
                triggerMeteor()
                currentIndex += 1
            } else {
                // auto-submit if last question ended
                submitQuiz(
                    questions = questions,
                    answers = answers,
                    scope = scope,
                    onResult = { result = it; showPlanetAlign = true },
                )
            }
        }
    }

    fun triggerMeteor() {
        showMeteor = true
        scope.launch {
            PlaySoundOnce(R.raw.comet_swipe)
            delay(650)
            showMeteor = false
        }
    }

    Column(
        Modifier
            .fillMaxSize()
            .padding(16.dp)
    ) {

        // Lessons Section
        Text("Astronomy 101", style = MaterialTheme.typography.headlineSmall)
        Spacer(Modifier.height(8.dp))

        if (showLoader) {
            BlackHoleLoader()
        } else {
            LazyColumn(modifier = Modifier.weight(0.5f)) {
                items(lessons) { lesson ->
                    ElevatedCard(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(vertical = 6.dp)
                    ) {
                        Column(modifier = Modifier.padding(12.dp)) {
                            Text(lesson.title, style = MaterialTheme.typography.titleMedium)
                            Spacer(Modifier.height(4.dp))
                            Text(lesson.content.take(300) + if (lesson.content.length > 300) "…" else "")
                        }
                    }
                }
            }
        }

        Spacer(Modifier.height(16.dp))

        // Quiz Section
        Text("Quick Quiz", style = MaterialTheme.typography.titleMedium)
        Spacer(Modifier.height(8.dp))

        if (questions.isEmpty()) {
            BlackHoleLoader()
            return@Column
        }

        val q = questions[currentIndex]

        // animated question card
        AnimatedContent(
            targetState = q,
            transitionSpec = {
                slideInHorizontally { it } + fadeIn() with
                        slideOutHorizontally { -it } + fadeOut()
            }
        ) { question ->

            ElevatedCard(
                modifier = Modifier.fillMaxWidth(),
            ) {
                Column(Modifier.padding(12.dp)) {

                    // Timer
                    Text(
                        "Time left: $timeLeft s",
                        fontSize = 14.sp,
                        fontWeight = FontWeight.Bold,
                        color = MaterialTheme.colorScheme.primary
                    )
                    Spacer(Modifier.height(8.dp))

                    Text(question.question_text)

                    Spacer(Modifier.height(8.dp))

                    question.options.forEach { opt ->
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            RadioButton(
                                selected = answers[question.id] == opt,
                                onClick = { answers[question.id] = opt }
                            )
                            Text(opt, Modifier.padding(start = 8.dp))
                        }
                    }

                }
            }
        }

        // meteor transition overlay
        MeteorSwipeEffect(visible = showMeteor)

        Spacer(Modifier.height(12.dp))

        Row(
            Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween
        ) {

            OutlinedButton(
                onClick = {
                    if (currentIndex > 0) {
                        triggerMeteor()
                        currentIndex -= 1
                    }
                },
                enabled = currentIndex > 0
            ) { Text("Back") }

            Button(
                onClick = {
                    if (currentIndex < questions.lastIndex) {
                        triggerMeteor()
                        currentIndex += 1
                    } else {
                        // submit quiz
                        submitQuiz(
                            questions = questions,
                            answers = answers,
                            scope = scope,
                            onResult = {
                                result = it
                                showPlanetAlign = true
                                PlaySoundOnce(R.raw.success_chime)
                            },
                        )
                    }
                }
            ) {
                Text(if (currentIndex < questions.lastIndex) "Next" else "Submit")
            }
        }

        Spacer(Modifier.height(16.dp))

        // RESULT
        result?.let {
            ElevatedCard(Modifier.fillMaxWidth()) {
                Column(Modifier.padding(12.dp)) {
                    Text("Score: ${it.score}/${it.total_questions}", fontSize = 20.sp, fontWeight = FontWeight.Bold)
                }
            }
        }

        PlanetAlignmentEffectOnce(trigger = showPlanetAlign) {
            showPlanetAlign = false
        }
    }
}

private fun submitQuiz(
    questions: List<QuizQuestionDto>,
    answers: MutableMap<Int, String>,
    scope: CoroutineScope,
    onResult: (QuizSubmissionOut?) -> Unit
) {
    scope.launch {
        val payload = QuizSubmissionCreate(
            answers = questions.map {
                QuizAnswerIn(
                    question_id = it.id,
                    selected_answer = answers[it.id] ?: "",
                    correct_answer = it.options.firstOrNull() ?: ""
                )
            }
        )

        onResult(runCatching { Api.service.submitQuiz(payload) }.getOrNull())
    }
}