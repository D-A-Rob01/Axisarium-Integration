package com.aletheion.cartomancy

import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.ViewModel
import androidx.lifecycle.SavedStateHandle

class ReadingSessionViewModel(private val savedStateHandle: SavedStateHandle) : ViewModel() {
    var reading by mutableStateOf<ReadingArtifact?>(savedStateHandle[READING_KEY])
        private set

    fun recordReading(value: ReadingArtifact) {
        reading = value
        savedStateHandle[READING_KEY] = value
    }

    fun clear() {
        reading = null
        savedStateHandle[READING_KEY] = null
    }

    private companion object {
        const val READING_KEY = "active_kybernion_reading"
    }
}
