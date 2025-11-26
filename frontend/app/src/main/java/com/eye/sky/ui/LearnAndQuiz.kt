package com.eye.sky.ui

import androidx.compose.animation.*
import androidx.compose.animation.core.FastOutSlowInEasing
import androidx.compose.animation.core.tween
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.eye.sky.net.*
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import java.time.format.DateTimeFormatter
import java.time.OffsetDateTime

/**
 * Enhanced LearnAndQuizScreen
 *
 * Features included:
 *  - Lesson categories (chips) + filtering
 *  - Per-question timer (30/45/60 sec by difficulty)
 *  - Animated transitions between questions
 *  - UI improvements using Material3 icons and chips
 *  - Auto-advance when timer hits zero; auto-submit at end
 *  - Quiz history viewer (compact)
 *
 * Usage: replace existing file at:
 * frontend/app/src/main/java/com/eye/sky/ui/LearnAndQuizScreen.kt
 */

@OptIn(ExperimentalAnimationApi::class)
@Composable
fun LearnAndQuizScreen() {
    val scope = rememberCoroutineScope()

    // --------------------
    // LESSONS
    // --------------------
    var allLessons by remember { mutableStateOf<List<Lesson>>(emptyList()) }
    var selectedCategory by remember { mutableStateOf<String?>(null) }
    var lessonCategories by remember { mutableStateOf<List<String>>(emptyList()) }

    // --------------------
    // QUIZ
    // --------------------
    var questions by remember { mutableStateOf<List<QuizQuestionDto>>(emptyList()) }
    var currentIndex by remember { mutableStateOf(0) } // current question index
    var answers by remember { mutableStateOf(mutableMapOf<Int, String>()) }
    var result by remember { mutableStateOf<QuizSubmissionOut?>(null) }
    var showQuiz by remember { mutableStateOf(false) }

    // per-question timer
    var timeLeft by remember { mutableStateOf(30L) }
    var timerJob by remember { mutableStateOf<Job?>(null) }

    // difficulties -> seconds per question
    val perQuestionDurations = mapOf(
        "simple" to 30L,
        "medium" to 45L,
        "difficult" to 60L
    )

    // filters & UI
    var difficulty by remember { mutableStateOf("simple") }
    var topic by remember { mutableStateOf<String?>(null) }

    // history
    var showHistory by remember { mutableStateOf(false) }
    var history by remember { mutableStateOf<List<QuizSubmissionOut>>(emptyList()) }

    // load lessons once
    LaunchedEffect(Unit) {
        allLessons = runCatching { Api.service.lessons() }.getOrDefault(emptyList())
        // extract categories from lessons (unique, lowercase)
        lessonCategories = (allLessons.mapNotNull { it.category?.lowercase() }.distinct().sorted())
    }

    // helper: start per-question timer
    fun startTimerForCurrentQuestion() {
        timerJob?.cancel()
        val dur = perQuestionDurations[difficulty] ?: 30L
        timeLeft = dur
        timerJob = scope.launch {
            while (timeLeft > 0) {
                delay(1000)
                timeLeft -= 1
            }
            // timer expired for this question -> auto-advance or auto-submit
            if (questions.isNotEmpty()) {
                // mark unanswered as empty string (optional)
                if (!answers.containsKey(questions[currentIndex].id)) {
                    answers[questions[currentIndex].id] = ""
                }
                if (currentIndex < questions.lastIndex) {
                    currentIndex += 1
                    // reset timer for next question
                    timeLeft = perQuestionDurations[difficulty] ?: 30L
                } else {
                    // last question reached and time up -> submit
                    scope.launch { submitCurrentQuiz() }
                }
            }
        }
    }

    // helper: submit quiz
    suspend fun submitCurrentQuiz() {
        // prepare payload using the current list of questions
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
        // stop timer
        timerJob?.cancel()
    }

    // when questions load or difficulty/topic change, reset quiz state
    LaunchedEffect(questions, difficulty, topic) {
        currentIndex = 0
        answers = mutableMapOf()
        result = null
        if (questions.isNotEmpty() && showQuiz) {
            startTimerForCurrentQuestion()
        } else {
            timerJob?.cancel()
        }
    }

    // UI
    Column(Modifier.fillMaxSize().padding(12.dp)) {
        // HEADER
        Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
            Icon(Icons.Default.MenuBook, contentDescription = "Lessons")
            Spacer(Modifier.width(8.dp))
            Text("Astronomy 101", style = MaterialTheme.typography.headlineLarge)
            Spacer(Modifier.weight(1f))
            // small quick action icons
            IconButton(onClick = { /* TODO: search */ }) { Icon(Icons.Default.Search, contentDescription = "Search") }
            IconButton(onClick = {
                // sign-out / token clear if you have auth
                com.eye.sky.net.Session.token = ""
            }) { Icon(Icons.Default.ExitToApp, contentDescription = "Sign out") }
        }

        Spacer(Modifier.height(10.dp))

        // LESSON CATEGORY CHIPS
        Text("Lessons", style = MaterialTheme.typography.titleMedium)
        Spacer(Modifier.height(6.dp))
        LazyRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            item {
                AssistChip(
                    onClick = { selectedCategory = null },
                    label = { Text("All") },
                    selected = selectedCategory == null
                )
            }
            items(lessonCategories) { cat ->
                AssistChip(
                    onClick = { selectedCategory = cat },
                    label = { Text(cat.replaceFirstChar { it.uppercase() }) },
                    selected = selectedCategory == cat
                )
            }
        }

        Spacer(Modifier.height(8.dp))

        // LESSON LIST (filtered)
        val filteredLessons = selectedCategory?.let { sc ->
            allLessons.filter { it.category?.lowercase() == sc }
        } ?: allLessons

        LazyColumn(Modifier.weight(1f)) {
            items(filteredLessons) { l ->
                var expanded by remember { mutableStateOf(false) }
                ElevatedCard(Modifier.fillMaxWidth().padding(vertical = 6.dp)) {
                    Column(Modifier.padding(12.dp)) {
                        Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
                            Column(Modifier.weight(1f)) {
                                Text(l.title, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.SemiBold)
                                Spacer(Modifier.height(6.dp))
                                Text(
                                    text = if (!expanded) l.content.take(180) + if (l.content.length > 180) "…" else "" else l.content,
                                    style = MaterialTheme.typography.bodyMedium
                                )
                            }
                            IconButton(onClick = { expanded = !expanded }) {
                                Icon(if (expanded) Icons.Default.ExpandLess else Icons.Default.ExpandMore, contentDescription = "Expand")
                            }
                        }
                    }
                }
            }
        }

        Spacer(Modifier.height(8.dp))

        // QUIZ CONTROLS
        Column(Modifier.fillMaxWidth()) {
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
                Text("Quick Quiz", style = MaterialTheme.typography.titleLarge)
                // timer chip (shows current timeLeft when quiz is active)
                if (showQuiz && questions.isNotEmpty()) {
                    Surface(
                        tonalElevation = 4.dp,
                        shape = MaterialTheme.shapes.small,
                        modifier = Modifier.padding(4.dp)
                    ) {
                        Row(Modifier.padding(8.dp), verticalAlignment = Alignment.CenterVertically) {
                            Icon(Icons.Default.Timer, contentDescription = "Timer")
                            Spacer(Modifier.width(6.dp))
                            Text("$timeLeft s", style = MaterialTheme.typography.bodyMedium)
                        }
                    }
                }
            }

            Spacer(Modifier.height(8.dp))

            // Difficulty selector (chips)
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                listOf("simple", "medium", "difficult").forEach { lvl ->
                    FilterChip(
                        selected = difficulty == lvl,
                        onClick = { difficulty = lvl },
                        label = { Text(lvl.replaceFirstChar { it.uppercase() }) }
                    )
                }
            }

            Spacer(Modifier.height(6.dp))

            // Topic selector (optional)
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                listOf(null, "stars", "planets", "galaxies", "cosmology", "telescopes").forEach { t ->
                    FilterChip(
                        selected = topic == t,
                        onClick = { topic = t },
                        label = { Text((t ?: "All").replaceFirstChar { it.uppercase() }) }
                    )
                }
            }

            Spacer(Modifier.height(8.dp))

            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                Button(onClick = {
                    scope.launch {
                        // load the questions (backend returns random 5)
                        questions = runCatching { Api.service.quiz(difficulty, topic) }.getOrDefault(emptyList())
                        if (questions.isNotEmpty()) {
                            showQuiz = true
                            currentIndex = 0
                            answers = mutableMapOf()
                            result = null
                            startTimerForCurrentQuestion() // start timer for first question
                        }
                    }
                }, modifier = Modifier.weight(1f)) {
                    Icon(Icons.Default.PlayArrow, contentDescription = "Load")
                    Spacer(Modifier.width(8.dp))
                    Text("Load Quiz")
                }

                OutlinedButton(onClick = {
                    scope.launch {
                        // show history
                        history = runCatching { Api.service.quizHistory() }.getOrDefault(emptyList())
                        showHistory = !showHistory
                    }
                }, modifier = Modifier.wrapContentWidth()) {
                    Icon(Icons.Default.History, contentDescription = "History")
                    Spacer(Modifier.width(6.dp))
                    Text("History")
                }
            }
        }

        Spacer(Modifier.height(8.dp))

        // QUIZ VIEW: show one question at a time with animated transitions
        AnimatedVisibility(visible = showQuiz && questions.isNotEmpty()) {
            Column {
                // question pager header
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
                    Text("Question ${currentIndex + 1} / ${questions.size}", style = MaterialTheme.typography.bodyLarge)
                    // progress bar visual (linear gradient)
                    val progress = (currentIndex.toFloat() / (questions.size.coerceAtLeast(1)))
                    LinearProgressIndicator(progress = (currentIndex + 1).toFloat() / questions.size)
                }

                Spacer(Modifier.height(8.dp))

                // AnimatedContent to animate between questions
                AnimatedContent(
                    targetState = currentIndex,
                    transitionSpec = {
                        // slide right for prev, left for next
                        if (targetState > initialState) {
                            slideInHorizontally(animationSpec = tween(350, easing = FastOutSlowInEasing)) { it } + fadeIn() with
                                    slideOutHorizontally(animationSpec = tween(350)) { -it } + fadeOut()
                        } else {
                            slideInHorizontally(animationSpec = tween(350)) { -it } + fadeIn() with
                                    slideOutHorizontally(animationSpec = tween(350, easing = FastOutSlowInEasing)) { it } + fadeOut()
                        }.using(SizeTransform(clip = false))
                    }
                ) { idx ->
                    val q = questions.getOrNull(idx)
                    if (q != null) {
                        // question card
                        Card(Modifier.fillMaxWidth().padding(vertical = 6.dp)) {
                            Column(Modifier.padding(16.dp)) {
                                Text(q.question_text, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                                Spacer(Modifier.height(8.dp))

                                // options as selectable rows
                                q.options.forEach { opt ->
                                    Row(Modifier
                                        .fillMaxWidth()
                                        .clickable {
                                            answers[q.id] = opt
                                        }
                                        .padding(vertical = 8.dp),
                                        verticalAlignment = Alignment.CenterVertically) {
                                        RadioButton(selected = answers[q.id] == opt, onClick = { answers[q.id] = opt })
                                        Spacer(Modifier.width(8.dp))
                                        Text(opt)
                                    }
                                }
                            }
                        }
                    } else {
                        // fallback empty state
                        Text("No question")
                    }
                }

                Spacer(Modifier.height(8.dp))

                // navigation controls for quiz (prev/next/submit)
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                    OutlinedButton(onClick = {
                        if (currentIndex > 0) {
                            currentIndex -= 1
                            startTimerForCurrentQuestion()
                        }
                    }, enabled = currentIndex > 0) {
                        Icon(Icons.Default.ArrowBack, contentDescription = "Prev")
                        Spacer(Modifier.width(6.dp))
                        Text("Prev")
                    }

                    Row {
                        Text("${timeLeft}s", style = MaterialTheme.typography.bodyLarge)
                        Spacer(Modifier.width(12.dp))
                        OutlinedButton(onClick = {
                            // skip question (mark empty) and advance
                            if (questions.isNotEmpty()) {
                                answers[questions[currentIndex].id] = answers[questions[currentIndex].id] ?: ""
                                if (currentIndex < questions.lastIndex) {
                                    currentIndex += 1
                                    startTimerForCurrentQuestion()
                                } else {
                                    // last question -> submit
                                    scope.launch { submitCurrentQuiz() }
                                }
                            }
                        }) {
                            Text("Skip")
                        }
                        Spacer(Modifier.width(8.dp))
                        Button(onClick = {
                            // submit entire quiz
                            scope.launch { submitCurrentQuiz() }
                        }) {
                            Icon(Icons.Default.CheckCircle, contentDescription = "Submit")
                            Spacer(Modifier.width(6.dp))
                            Text("Submit")
                        }
                    }
                }

                Spacer(Modifier.height(8.dp))

                // show feedback after submission (if present)
                result?.let { res ->
                    Card(Modifier.fillMaxWidth().padding(vertical = 6.dp)) {
                        Column(Modifier.padding(12.dp)) {
                            Text("Results", style = MaterialTheme.typography.titleMedium)
                            Spacer(Modifier.height(6.dp))
                            Text("Score: ${res.score} / ${res.total_questions} (${(res.score.toDouble() / res.total_questions * 100).toInt()}%)")
                            Spacer(Modifier.height(8.dp))
                            // optional: show per-question feedback lines (compact)
                            val fmt = DateTimeFormatter.ISO_OFFSET_DATE_TIME
                            res.answers?.forEach { a ->
                                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                                    Text("Q: ${a.question_id}")
                                    Text(if (a.selected_answer == a.correct_answer) "✔" else "✖")
                                }
                            }
                        }
                    }
                }
            }
        }

        // HISTORY viewer: simple list
        AnimatedVisibility(showHistory) {
            Column {
                Spacer(Modifier.height(8.dp))
                Text("Quiz History", style = MaterialTheme.typography.titleMedium)
                LazyColumn(Modifier.height(180.dp)) {
                    items(history) { item ->
                        ElevatedCard(Modifier.fillMaxWidth().padding(vertical = 6.dp)) {
                            Column(Modifier.padding(12.dp)) {
                                Text("Score: ${item.score}/${item.total_questions}")
                                Text("At: ${try { OffsetDateTime.parse(item.timestamp).format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm")) } catch (_: Exception) { item.timestamp }}")
                            }
                        }
                    }
                }
            }
        }
    }

    // local helper functions inside composable so they can use scope & state
    fun startTimerForCurrentQuestion() {
        timerJob?.cancel()
        val dur = perQuestionDurations[difficulty] ?: 30L
        timeLeft = dur
        timerJob = scope.launch {
            while (timeLeft > 0) {
                delay(1000)
                timeLeft -= 1
            }
            if (questions.isNotEmpty()) {
                if (!answers.containsKey(questions[currentIndex].id)) {
                    answers[questions[currentIndex].id] = ""
                }
                if (currentIndex < questions.lastIndex) {
                    currentIndex += 1
                    timeLeft = perQuestionDurations[difficulty] ?: 30L
                } else {
                    // time exhausted on last question -> submit
                    scope.launch { submitCurrentQuiz() }
                }
            }
        }
    }

    suspend fun submitCurrentQuiz() {
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
        timerJob?.cancel()
    }
}