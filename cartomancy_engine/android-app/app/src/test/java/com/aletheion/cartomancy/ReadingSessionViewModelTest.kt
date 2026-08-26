package com.aletheion.cartomancy

import androidx.lifecycle.SavedStateHandle
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class ReadingSessionViewModelTest {
    @Test
    fun activeReadingSurvivesViewModelRecreation() {
        val state = SavedStateHandle()
        val reading = sampleReading()

        ReadingSessionViewModel(state).recordReading(reading)

        assertEquals(reading, ReadingSessionViewModel(state).reading)
    }

    @Test
    fun clearingReadingAlsoClearsSavedState() {
        val state = SavedStateHandle()
        val viewModel = ReadingSessionViewModel(state)
        viewModel.recordReading(sampleReading())

        viewModel.clear()

        assertNull(viewModel.reading)
        assertNull(ReadingSessionViewModel(state).reading)
    }

    private fun sampleReading() = ReadingArtifact(
        date = "2026-08-02",
        deck = "rider-waite-smith",
        spread = "three-card",
        mode = "reflective",
        question = "What requires attention?",
        context = "QA",
        confidence = 4,
        firstImpression = "Hold the course.",
        cards = listOf(
            DrawnCard(
                position = 1,
                positionLabel = "Current Pattern",
                positionPrompt = "What pattern is active?",
                card = Card(
                    id = "major-00-the-fool",
                    name = "The Fool",
                    arcana = "major",
                    number = 0,
                    suit = null,
                    element = "air",
                    uprightKeywords = listOf("beginning"),
                    reversedKeywords = listOf("hesitation"),
                ),
                orientation = "upright",
            ),
        ),
    )
}
