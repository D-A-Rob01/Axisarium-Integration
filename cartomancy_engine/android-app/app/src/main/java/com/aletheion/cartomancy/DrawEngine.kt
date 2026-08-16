package com.aletheion.cartomancy

import java.time.LocalDate
import java.util.Collections
import java.util.Random

class DrawEngine(private val random: Random = Random()) {
    fun draw(
        deckId: String,
        deck: List<Card>,
        spread: Spread,
        mode: String,
        question: String,
        context: String,
        confidence: Int?,
        allowReversals: Boolean = true,
        date: String = LocalDate.now().toString(),
    ): ReadingArtifact {
        require(spread.positions.size <= deck.size) { "The spread requires more cards than the deck contains." }
        require(mode in VALID_MODES) { "Unsupported interpretation protocol: $mode" }
        require(confidence == null || confidence in 1..5) { "Confidence must be blank or between 1 and 5." }

        val shuffledDeck = deck.toMutableList()
        Collections.shuffle(shuffledDeck, random)
        val selected = shuffledDeck.take(spread.positions.size)
        val cards = spread.positions.zip(selected).map { (position, card) ->
            DrawnCard(
                position = position.index,
                positionLabel = position.label,
                positionPrompt = position.prompt,
                card = card,
                orientation = if (allowReversals && random.nextBoolean()) "reversed" else "upright",
            )
        }

        return ReadingArtifact(
            date = date,
            deck = deckId,
            spread = spread.id,
            mode = mode,
            question = question,
            context = context,
            confidence = confidence,
            firstImpression = "",
            cards = cards,
        )
    }

    companion object {
        val VALID_MODES = setOf(
            "reflective",
            "predictive",
            "ritual",
            "creative",
            "decision-support",
            "diagnostic",
            "strategic",
            "comparative",
        )
    }
}
