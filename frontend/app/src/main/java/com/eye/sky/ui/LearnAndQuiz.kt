package com.eye.sky.ui

import androidx.compose.animation.*
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.eye.sky.net.*
import kotlinx.coroutines.launch

@OptIn(ExperimentalAnimationApi::class)
@Composable
fun LearnAndQuizScreen() {

    val scope = rememberCoroutineScope()

    // LESSON DATA
    var lessons by remember { mutableStateOf<List<Lesson>>(emptyList()) }

    // QUIZ DATA
    var questions by remember { mutableStateOf<List<QuizQuestionDto>>(emptyList()) }
    var answers by remember { mutableStateOf(mutableMapOf<Int, String>()) }
    var result by remember { mutableStateOf<QuizSubmissionOut?>(null) }

    // HISTORY
    var showHistory by remember { mutableStateOf(false) }
    var history by remember { mutableStateOf<List<QuizSubmissionOut>>(emptyList()) }

    // FILTERS
    var difficulty by remember { mutableStateOf("simple") }
    var topic by remember { mutableStateOf<String?>(null) }

    // QUIZ UI STATE
    var showQuiz by remember { mutableStateOf(false) }

    // Load lessons once
    LaunchedEffect(Unit) {
        lessons = runCatching { Api.service.lessons() }.getOrDefault(emptyList())
    }

    Column(Modifier.fillMaxSize().padding(12.dp)) {

        // ------------------------------
        // HEADER
        // ------------------------------
        Text("Astronomy 101", style = MaterialTheme.typography.headlineLarge)
        Spacer(Modifier.height(8.dp))


        // ============================================================
        //                   LESSON LIST + EXPANDABLE CONTENT
        // ============================================================
        Text("Lessons", style = MaterialTheme.typography.titleLarge)
        Spacer(Modifier.height(6.dp))

        LazyColumn(Modifier.weight(1f)) {
            items(lessons) { l ->

                var expanded by remember { mutableStateOf(false) }

                ElevatedCard(
                    Modifier
                        .fillMaxWidth()
                        .padding(vertical = 6.dp)
                ) {
                    Column(Modifier.padding(16.dp)) {

                        Text(l.title, style = MaterialTheme.typography.titleMedium)
                        Spacer(Modifier.height(6.dp))

                        val preview = l.content.take(250)

                        Text(
                            text = if (!expanded) "$preview…" else l.content,
                            modifier = Modifier.clickable {
                                expanded = !expanded
                            }
                        )

                        if (!expanded) {
                            TextButton(onClick = { expanded = true }) {
                                Text("Read More")
                            }
                        }
                    }
                }
            }
        }


        Spacer(Modifier.height(12.dp))


        // ============================================================
        //                        QUIZ HISTORY BUTTON
        // ============================================================
        Button(
            onClick = {
                scope.launch {
                    history = Api.service.quizHistory()
                    showHistory = true
                }
            },
            modifier = Modifier.fillMaxWidth()
        ) {
            Text("View Quiz History")
        }

        AnimatedVisibility(showHistory) {
            LazyColumn(
                Modifier
                    .fillMaxWidth()
                    .height(180.dp)
                    .padding(vertical = 6.dp)
            ) {
                items(history) { item ->
                    ElevatedCard(Modifier.padding(6.dp)) {
                        Column(Modifier.padding(12.dp)) {
                            Text("Score: ${item.score}/${item.total_questions}")
                            Text("Date: ${item.timestamp}")
                        }
                    }
                }
            }
        }


        Spacer(Modifier.height(12.dp))


        // ============================================================
        //                         QUIZ FILTERS
        // ============================================================
        Text("Quick Quiz", style = MaterialTheme.typography.titleLarge)
        Spacer(Modifier.height(6.dp))

        // Difficulty selection
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceEvenly) {
            listOf("simple", "medium", "difficult").forEach { level ->
                FilterChip(
                    selected = difficulty == level,
                    onClick = { difficulty = level },
                    label = { Text(level) }
                )
            }
        }

        Spacer(Modifier.height(6.dp))

        // Topic selection
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceEvenly) {
            listOf(null, "stars", "planets", "galaxies", "cosmology", "telescopes").forEach { t ->
                FilterChip(
                    selected = topic == t,
                    onClick = { topic = t },
                    label = { Text(t ?: "All") }
                )
            }
        }


        Spacer(Modifier.height(10.dp))


        // ============================================================
        //                        LOAD QUIZ BUTTON
        // ============================================================
        Button(
            onClick = {
                scope.launch {
                    answers.clear()
                    result = null
                    questions = runCatching {
                        Api.service.quiz(difficulty, topic)
                    }.getOrDefault(emptyList())

                    showQuiz = true
                }
            },
            modifier = Modifier.fillMaxWidth()
        ) {
            Text("Load Quiz")
        }

        Spacer(Modifier.height(8.dp))


        // ============================================================
        //                          QUIZ QUESTIONS
        // ============================================================
        AnimatedVisibility(
            visible = showQuiz,
            enter = expandVertically(),
            exit = shrinkVertically()
        ) {

            Column {

                questions.forEach { q ->

                    ElevatedCard(
                        Modifier
                            .fillMaxWidth()
                            .padding(vertical = 6.dp)
                    ) {
                        Column(Modifier.padding(16.dp)) {

                            Text(q.question_text, style = MaterialTheme.typography.titleMedium)
                            Spacer(Modifier.height(6.dp))

                            q.options.forEach { opt ->

                                Row {
                                    RadioButton(
                                        selected = answers[q.id] == opt,
                                        onClick = {
                                            answers[q.id] = opt
                                        }
                                    )
                                    Text(opt, Modifier.padding(start = 8.dp))
                                }
                            }
                        }
                    }
                }

                // ============================================================
                //                            SUBMIT BUTTON
                // ============================================================
                Button(
                    onClick = {
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
                            result = Api.service.submitQuiz(payload)
                        }
                    },
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Text("Submit Quiz")
                }

                // ============================================================
                //                               RESULTS
                // ============================================================
                result?.let { r ->
                    Spacer(Modifier.height(10.dp))
                    Text(
                        "Score: ${r.score}/${r.total_questions}",
                        style = MaterialTheme.typography.headlineSmall
                    )
                }
            }
        }
    }
}