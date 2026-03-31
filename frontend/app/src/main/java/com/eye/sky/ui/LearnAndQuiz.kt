package com.eye.sky.ui

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import com.eye.sky.audio.SoundManager
import com.eye.sky.net.*
import com.eye.sky.R
import com.eye.sky.ui.components.BlackHoleLoader
import com.eye.sky.ui.components.MeteorSwipeEffect
import kotlinx.coroutines.launch

@Composable
fun LearnAndQuizScreen() {
    val ctx   = LocalContext.current
    val scope = rememberCoroutineScope()

    var lessons   by remember { mutableStateOf<List<Lesson>>(emptyList()) }
    var questions by remember { mutableStateOf<List<QuizQuestionDto>>(emptyList()) }
    var answers   by remember { mutableStateOf(mutableMapOf<Int, String>()) }
    var result    by remember { mutableStateOf<QuizSubmissionOut?>(null) }
    var loading   by remember { mutableStateOf(true) }
    var showMeteor by remember { mutableStateOf(false) }

    LaunchedEffect(Unit) {
        runCatching {
            lessons   = Api.service.lessons()
            questions = Api.service.quiz(difficulty = "simple", topic = null)
        }
        loading = false
    }

    Box(Modifier.fillMaxSize()) {

        if (loading) {
            Column(
                Modifier.fillMaxSize(),
                verticalArrangement   = Arrangement.Center,
                horizontalAlignment   = Alignment.CenterHorizontally,
            ) {
                BlackHoleLoader(autoPlayRumble = true)
                Text("Loading…", style = MaterialTheme.typography.titleMedium)
            }
        } else {
            Column(Modifier.fillMaxSize().padding(12.dp)) {

                Text("Astronomy 101", style = MaterialTheme.typography.headlineSmall)
                Spacer(Modifier.height(8.dp))

                // Lessons
                LazyColumn(Modifier.weight(1f)) {
                    items(lessons) { lesson ->
                        // ElevatedCard with onClick uses the two-arg overload
                        ElevatedCard(
                            onClick   = { SoundManager.playSfx(R.raw.meteor_swipe) },
                            modifier  = Modifier.fillMaxWidth().padding(vertical = 6.dp),
                        ) {
                            Column(Modifier.padding(12.dp)) {
                                Text(lesson.title, style = MaterialTheme.typography.titleMedium)
                                Spacer(Modifier.height(4.dp))
                                val preview = lesson.content.take(300)
                                Text(if (lesson.content.length > 300) "$preview…" else preview)
                            }
                        }
                    }
                }

                Spacer(Modifier.height(8.dp))
                Text("Quick Quiz", style = MaterialTheme.typography.titleMedium)

                // Quiz questions — plain ElevatedCard (no onClick)
                questions.forEach { q ->
                    ElevatedCard(modifier = Modifier.fillMaxWidth().padding(vertical = 6.dp)) {
                        Column(Modifier.padding(12.dp)) {
                            Text(q.question_text)
                            q.options.forEach { opt ->
                                Row(verticalAlignment = Alignment.CenterVertically) {
                                    RadioButton(
                                        selected  = answers[q.id] == opt,
                                        onClick   = {
                                            answers = answers.toMutableMap().apply { put(q.id, opt) }
                                            SoundManager.playSfx(R.raw.meteor_swipe)
                                        },
                                    )
                                    Text(opt, Modifier.padding(start = 8.dp))
                                }
                            }
                        }
                    }
                }

                // Result
                result?.let {
                    SoundManager.playSfx(R.raw.planet_alignment)
                    Text(
                        "Score: ${it.score} / ${it.total_questions}",
                        style = MaterialTheme.typography.titleMedium,
                        modifier = Modifier.padding(vertical = 8.dp),
                    )
                }

                // Submit
                Button(
                    onClick  = {
                        scope.launch {
                            showMeteor = true
                            kotlinx.coroutines.delay(650)
                            showMeteor = false

                            val payload = QuizSubmissionCreate(
                                answers = questions.map { q ->
                                    QuizAnswerIn(
                                        question_id     = q.id,
                                        selected_answer = answers[q.id] ?: "",
                                        correct_answer  = "",
                                    )
                                }
                            )
                            result = runCatching { Api.service.submitQuiz(payload) }.getOrNull()
                        }
                    },
                    enabled  = questions.isNotEmpty(),
                    modifier = Modifier.fillMaxWidth(),
                ) {
                    Text("Submit Quiz")
                }
            }
        }

        MeteorSwipeEffect(visible = showMeteor)
    }
}