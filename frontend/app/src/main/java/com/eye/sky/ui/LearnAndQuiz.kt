package com.eye.sky.ui

import androidx.compose.foundation.layout.* 
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import com.eye.sky.net.*
import kotlinx.coroutines.launch

// NEW imports for animations + sound
import com.eye.sky.ui.components.MeteorSwipeEffect
import com.eye.sky.ui.components.BlackHoleLoader
import com.eye.sky.audio.SoundManager
import com.eye.sky.R

@Composable
fun LearnAndQuizScreen() {

    val ctx = LocalContext.current
    val scope = rememberCoroutineScope()

    // Existing states
    var lessons by remember { mutableStateOf<List<Lesson>>(emptyList()) }
    var questions by remember { mutableStateOf<List<QuizQuestionDto>>(emptyList()) }
    var answers by remember { mutableStateOf(mutableMapOf<Int, String>()) }
    var result by remember { mutableStateOf<QuizSubmissionOut?>(null) }

    // NEW state: loading for blackhole animation
    var loading by remember { mutableStateOf(true) }

    // NEW state: show meteor swipe during question transitions
    var showMeteor by remember { mutableStateOf(false) }

    // Fetch lessons + simple quiz
    LaunchedEffect(Unit) {
        try {
            lessons = Api.service.lessons()
            questions = Api.service.quiz(difficulty = "simple", topic = null)
        } catch (e: Exception) {
            // If error, no crash, no sound
        }
        loading = false
    }

    // MAIN UI
    Box(Modifier.fillMaxSize()) {

        if (loading) {
            // Black hole loading animation
            Column(
                Modifier.fillMaxSize(),
                verticalArrangement = Arrangement.Center,
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                BlackHoleLoader(autoPlayRumble = true)
                Text("Loading...", style = MaterialTheme.typography.titleMedium)
            }
        } else {

            Column(Modifier.fillMaxSize().padding(12.dp)) {

                Text("Astronomy 101", style = MaterialTheme.typography.headlineSmall)
                Spacer(Modifier.height(8.dp))

                // Lessons list
                LazyColumn(Modifier.weight(1f)) {
                    items(lessons) { l ->
                        ElevatedCard(
                            Modifier.fillMaxWidth().padding(vertical = 6.dp),
                            onClick = {
                                // UI tap
                                SoundManager.playSfx(R.raw.ui_galaxy_tap)
                                // Optional: lesson details screen could go here
                            }
                        ) {
                            Column(Modifier.padding(12.dp)) {
                                Text(l.title, style = MaterialTheme.typography.titleMedium)
                                Spacer(Modifier.height(4.dp))
                                Text(l.content.take(300) + if (l.content.length > 300) "…" else "")
                            }
                        }
                    }
                }

                Spacer(Modifier.height(8.dp))
                Text("Quick Quiz", style = MaterialTheme.typography.titleMedium)

                // QUESTIONS
                questions.forEach { q ->
                    ElevatedCard(Modifier.fillMaxWidth().padding(vertical = 6.dp)) {
                        Column(Modifier.padding(12.dp)) {

                            Text(q.question_text)

                            q.options.forEach { opt ->
                                Row {
                                    RadioButton(
                                        selected = answers[q.id] == opt,
                                        onClick = {
                                            answers[q.id] = opt
                                            SoundManager.playSfx(R.raw.ui_galaxy_tap)
                                        }
                                    )
                                    Text(opt, Modifier.padding(start = 8.dp))
                                }
                            }
                        }
                    }
                }

                // Quiz results
                result?.let {
                    SoundManager.playSfx(R.raw.planet_alignment)
                    Text("Score: ${it.score}/${it.total_questions}")
                }

                // Submit button
                Button(
                    onClick = {
                        scope.launch {
                            showMeteor = true
                            kotlinx.coroutines.delay(650)
                            showMeteor = false

                            val payload = QuizSubmissionCreate(
                                answers = questions.map {
                                    QuizAnswerIn(
                                        question_id = it.id,
                                        selected_answer = answers[it.id] ?: "",
                                        correct_answer = it.options.firstOrNull() ?: ""
                                    )
                                }
                            )

                            result = runCatching { Api.service.submitQuiz(payload) }.getOrNull()
                        }
                    },
                    enabled = questions.isNotEmpty(),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Text("Submit Quiz")
                }
            }
        }

        // Meteor transition overlay
        MeteorSwipeEffect(visible = showMeteor)
    }
}