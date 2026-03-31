package com.eye.sky.repo

import com.eye.sky.net.Api
import com.eye.sky.net.Lesson

class LessonRepository {
    suspend fun fetchLessons(): List<Lesson> {
        return Api.service.lessons()
    }
}