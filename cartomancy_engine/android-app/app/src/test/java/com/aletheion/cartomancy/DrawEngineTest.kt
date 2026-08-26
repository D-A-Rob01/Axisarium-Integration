package com.aletheion.cartomancy

import java.util.Random
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class DrawEngineTest {
    private val deck = listOf(
        card("one", "One"),
        card("two", "Two"),
        card("three", "Three"),
        card("four", "Four"),
        card("five", "Five"),
    )
    private val spread = Spread(
        id = "three-card",
        name = "Three Card",
        positions = listOf(
            SpreadPosition(1, "Current Pattern", "What pattern is active?"),
            SpreadPosition(2, "Complication", "What complicates the matter?"),
            SpreadPosition(3, "Next Move", "What practical response is suggested?"),
        ),
    )

    @Test
    fun drawDoesNotDuplicateCards() {
        val reading = DrawEngine(Random(7)).draw(
            deckId = "test-deck",
            deck = deck,
            spread = spread,
            mode = "decision-support",
            question = "",
            context = "",
            confidence = null,
        )

        assertEquals(3, reading.cards.size)
        assertEquals(3, reading.cards.map { it.card.id }.toSet().size)
        assertEquals("kybernion", reading.architecture)
        assertEquals("immutable", reading.drawStatus)
        assertTrue(reading.cards.all { it.orientation == "upright" || it.orientation == "reversed" })
    }

    @Test
    fun noReversalsProducesOnlyUprightCards() {
        val reading = DrawEngine(Random(1)).draw(
            deckId = "test-deck",
            deck = deck,
            spread = spread,
            mode = "decision-support",
            question = "",
            context = "",
            confidence = null,
            allowReversals = false,
        )

        assertTrue(reading.cards.all { it.orientation == "upright" })
    }

    @Test
    fun markdownKeepsPunctuationSafeInQuestionAndFirstImpression() {
        val reading = DrawEngine(Random(2)).draw(
            deckId = "test-deck",
            deck = deck,
            spread = spread,
            mode = "diagnostic",
            question = "What changes if I ask: \"why now?\"",
            context = "career / writing / money",
            confidence = 3,
        ).withFirstImpression("First response: pause, then choose.")

        val markdown = ArtifactRenderer.toMarkdown(reading)

        assertTrue(markdown.contains("question: \"What changes if I ask: \\\"why now?\\\"\""))
        assertTrue(markdown.contains("## First Impression\n\nFirst response: pause, then choose."))
    }

    private fun card(id: String, name: String) = Card(
        id = id,
        name = name,
        arcana = "major",
        number = 0,
        suit = null,
        element = "air",
        uprightKeywords = listOf("clarity"),
        reversedKeywords = listOf("confusion"),
    )
}
