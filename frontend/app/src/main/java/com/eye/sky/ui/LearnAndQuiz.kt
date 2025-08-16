package com.eye.sky.ui

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.eye.sky.net.*
import kotlinx.coroutines.launch

@Composable
fun LearnAndQuizScreen() {
    val scope = rememberCoroutineScope()
    var lessons by remember { mutableStateOf<List<Lesson>>(emptyList()) }
    var questions by remember { mutableStateOf<List<QuizQuestionDto>>(emptyList()) }
    var answers by remember { mutableStateOf(mutableMapOf<Int, String>()) }
    var result by remember { mutableStateOf<QuizSubmissionOut?>(null) }

    LaunchedEffect(Unit) {
        lessons = runCatching { Api.service.lessons() }.getOrDefault(emptyList())
        questions = runCatching { Api.service.quiz(difficulty = "simple", topic = null) }.getOrDefault(emptyList())
    }

    Column(Modifier.fillMaxSize().padding(12.dp)) {
        Text("Astronomy 101", style = MaterialTheme.typography.headlineSmall)
        Spacer(Modifier.height(8.dp))
        LazyColumn(Modifier.weight(1f)) {
            items(lessons) { l ->
                ElevatedCard(Modifier.fillMaxWidth().padding(vertical = 6.dp)) {
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
        questions.forEach { q ->
            ElevatedCard(Modifier.fillMaxWidth().padding(vertical = 6.dp)) {
                Column(Modifier.padding(12.dp)) {
                    Text(q.question_text)
                    q.options.forEach { opt ->
                        Row {
                            RadioButton(
                                selected = answers[q.id] == opt,
                                onClick = { answers[q.id] = opt }
                            )
                            Text(opt, Modifier.padding(start = 8.dp))
                        }
                    }
                }
            }
        }
        result?.let { Text("Score: ${it.score}/${it.total_questions}") }
        Button(onClick = {
            scope.launch {
                val payload = QuizSubmissionCreate(
                    answers = questions.map {
                        QuizAnswerIn(
                            question_id = it.id,
                            selected_answer = answers[it.id] ?: "",
                            correct_answer = (it.options.firstOrNull() ?: "") // client only echoes; backend computes score anyway
                        )
                    }
                )
                result = runCatching { Api.service.submitQuiz(payload) }.getOrNull()
            }
        }, enabled = questions.isNotEmpty(), modifier = Modifier.fillMaxWidth()) {
            Text("Submit Quiz")
        }
    }
}