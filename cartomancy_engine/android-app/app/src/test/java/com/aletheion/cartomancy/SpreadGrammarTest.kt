package com.aletheion.cartomancy

import java.io.File
import java.util.Random
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test

class SpreadGrammarTest {
    @Test
    fun bundledFormationsRetainEveryPositionThroughDrawAndBothExports() {
        val root = File(requireNotNull(System.getProperty("kybernion.contracts")))
        val ids = listOf("three-card", "the-constellation", "the-fork", "the-aperture", "the-crucible", "the-interface", "the-vector")
        val deck = (1..78).map { Card("card-$it", "Card $it", "minor", it, "cups", "water", listOf("open"), listOf("reflect")) }
        ids.forEach { id ->
            val source = JSONObject(File(root, "spreads/$id.json").readText())
            val positions = source.getJSONArray("positions")
            val spread = Spread(id, source.getString("name"), (0 until positions.length()).map {
                val position = positions.getJSONObject(it)
                SpreadPosition(position.getInt("index"), position.getString("label"), position.getString("prompt"))
            })
            for (reversals in listOf(false, true)) {
                val reading = DrawEngine(Random(34)).draw("test-deck", deck, spread, "decision-support",
                    "What can I test?", "A / B", 3, reversals, "2026-09-19")
                val expectedCount = if (id == "three-card") 3 else 7
                assertEquals(expectedCount, reading.cards.size)
                assertEquals(expectedCount, reading.cards.map { it.card.id }.toSet().size)
                assertEquals((1..expectedCount).toList(), reading.cards.map { it.position })
                if (!reversals) assertTrue(reading.cards.all { it.orientation == "upright" })
                val annotated = reading.withFirstImpression("A tentative association")
                assertEquals(reading.cards, annotated.cards)
                assertEquals("immutable", annotated.drawStatus)
                val json = JSONObject(ArtifactRenderer.toJson(annotated))
                val markdown = ArtifactRenderer.toMarkdown(annotated)
                assertEquals(id, json.getString("spread"))
                assertEquals(id, json.getString("receptive_formation"))
                assertEquals("immutable", json.getString("draw_status"))
                assertEquals(expectedCount, json.getJSONArray("cards").length())
                assertEquals(6, json.getJSONArray("claim_types").length())
                assertTrue(markdown.contains("## 72-Hour Experiment"))
                assertTrue(markdown.contains("## Outcome / Audit"))
                assertTrue(markdown.contains("spread: $id"))
                spread.positions.forEachIndexed { index, position ->
                    assertEquals(position.label, annotated.cards[index].positionLabel)
                    assertEquals(position.prompt, annotated.cards[index].positionPrompt)
                    assertTrue(markdown.contains(position.label))
                    assertTrue(ArtifactRenderer.toJson(annotated).contains(position.prompt))
                }
                assertEquals(reading.cards, annotated.cards)
            }
        }
    }
}
