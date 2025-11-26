package com.eye.sky.ui

import androidx.compose.animation.*
import androidx.compose.animation.core.tween
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.eye.sky.viewmodel.QuizViewModel
import androidx.lifecycle.viewmodel.compose.viewModel

@OptIn(ExperimentalAnimationApi::class)
@Composable
fun QuizScreen(
    navBack: () -> Unit = {},
    vm: QuizViewModel = viewModel()
) {
    val questions by vm.questions.collectAsState()
    val answers by vm.answers.collectAsState()
    val submission by vm.submission.collectAsState()
    val timeLeft by vm.timeLeft.collectAsState()

    var diff by remember { mutableStateOf("simple") }
    var topic by remember { mutableStateOf("All") }

    Column(Modifier.fillMaxSize().padding(12.dp)) {

        Text("Quiz", style = MaterialTheme.typography.headlineMedium)
        Text("Time Left: $timeLeft s")

        Spacer(Modifier.height(12.dp))

        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            listOf("simple","medium","difficult").forEach { d ->
                FilterChip(
                    selected = diff == d,
                    onClick = {
                        diff = d
                        vm.loadQuestions(diff, if (topic=="All") null else topic)
                    },
                    label = { Text(d) }
                )
            }
        }

        Spacer(Modifier.height(8.dp))

        Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
            vm.topics.forEach { t ->
                AssistChip(
                    onClick = {
                        topic = t
                        vm.loadQuestions(diff, if (topic=="All") null else topic)
                    },
                    label = { Text(t) }
                )
            }
        }

        Spacer(Modifier.height(12.dp))

        AnimatedContent(
            targetState = questions,
            transitionSpec = {
                fadeIn(tween(300)) with fadeOut(tween(300))
            }
        ) { qs ->
            if (qs.isEmpty()) {
                Text("No questions loaded.")
            } else {
                LazyColumn(Modifier.weight(1f)) {
                    items(qs) { q ->
                        Card(Modifier.fillMaxWidth().padding(vertical = 8.dp)) {
                            Column(Modifier.padding(12.dp)) {
                                Text(q.question_text, style = MaterialTheme.typography.titleMedium)
                                q.options.forEach { opt ->
                                    Row(verticalAlignment = Alignment.CenterVertically) {
                                        RadioButton(
                                            selected = answers[q.id] == opt,
                                            onClick = { vm.setAnswer(q.id, opt) }
                                        )
                                        Text(opt)
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

        submission?.let {
            AlertDialog(
                onDismissRequest = {},
                confirmButton = { TextButton(onClick = navBack) { Text("OK") } },
                text = { Text("Score: ${it.score}/${it.total_questions}") }
            )
        }

        Button(
            onClick = { vm.submitQuiz() },
            modifier = Modifier.fillMaxWidth()
        ) {
            Text("Submit")
        }
    }
}