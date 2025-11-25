package com.eye.sky.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.eye.sky.net.Lesson
import com.eye.sky.repo.LessonRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch

class LessonViewModel(private val repo: LessonRepository = LessonRepository()) : ViewModel() {
    private val _lessons = MutableStateFlow<List<Lesson>>(emptyList())
    val lessons: StateFlow<List<Lesson>> = _lessons

    private val _loading = MutableStateFlow(false)
    val loading: StateFlow<Boolean> = _loading

    init {
        loadLessons()
    }

    fun loadLessons() {
        viewModelScope.launch {
            _loading.value = true
            runCatching {
                repo.fetchLessons()
            }.onSuccess {
                _lessons.value = it
            }.onFailure {
                // Optionally handle/log error
            }
            _loading.value = false
        }
    }
}