package com.aletheion.cartomancy

import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.test.ext.junit.runners.AndroidJUnit4
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.junit.Assert.*
import java.io.File

@RunWith(AndroidJUnit4::class)
class AstreriumFlowTest {
    @get:Rule val compose = createAndroidComposeRule<MainActivity>()

    private fun text(value: String) = compose.onNodeWithText(value, useUnmergedTree = false)
    private fun click(value: String) { text(value).performScrollTo().performClick() }

    @Test fun committedReadingDraftAndNotesSurviveNavigationAndRecreation() {
        compose.waitUntil(30000) { compose.onAllNodesWithText("Your question").fetchSemanticsNodes().isNotEmpty() }
        text("Your question").performTextInput("What deserves my attention today?")
        click("Commit immutable draw")
        compose.waitUntil(15000) { compose.onAllNodesWithText("First Contact").fetchSemanticsNodes().isNotEmpty() }
        val folder = File(compose.activity.filesDir, "astrerium-journal")
        val original = ReadingJournal(folder).entries().single()
        text("First impression").performScrollTo().performTextInput("A quiet line joins the two shores.")
        text("Journal").performClick()
        text("What deserves my attention today?").performClick()
        text("A quiet line joins the two shores.").performScrollTo().assertExists()
        click("Keep this impression")
        compose.waitUntil(10000) { ReadingJournal(folder).entries().single().notes.size == 1 }
        compose.activityRule.scenario.recreate()
        compose.waitUntil(30000) { compose.onAllNodesWithText("First Contact").fetchSemanticsNodes().isNotEmpty() }
        val restored = ReadingJournal(folder).entries().single()
        assertEquals(original.id, restored.id)
        assertEquals(original.reading, restored.reading)
        assertEquals("A quiet line joins the two shores.", restored.notes.single().text)
        click("Relate")
        text("Your association").performScrollTo().performTextInput("The figures face different possibilities.")
        click("Keep this connection")
        compose.waitUntil(10000) { ReadingJournal(folder).entries().single().notes.size == 2 }
        click("Revisit")
        text("Later reflection").performScrollTo().performTextInput("I returned with new evidence.")
        click("Keep this reflection")
        compose.waitUntil(10000) { ReadingJournal(folder).entries().single().notes.size == 3 }
        val final = ReadingJournal(folder).entries().single()
        assertEquals(original.reading, final.reading)
        assertEquals(listOf("notice", "relate", "revisit"), final.notes.map { it.kind })
        assertEquals(2, final.notes[1].positions.distinct().size)
        click("Export reading")
        val exports = File(compose.activity.cacheDir, "kybernion").listFiles()!!.toList()
        val markdown = exports.single { it.extension == "md" }.readText()
        val json = org.json.JSONObject(exports.single { it.extension == "json" }.readText())
        assertTrue(markdown.contains("A quiet line joins the two shores."))
        assertTrue(markdown.contains("I returned with new evidence."))
        assertEquals("immutable", json.getString("draw_status"))
        assertEquals(3, json.getJSONObject("astrerium_journal").getJSONArray("notes").length())
        assertEquals(original.reading.cards.map { it.card.id },
            (0 until json.getJSONArray("cards").length()).map { json.getJSONArray("cards").getJSONObject(it).getString("card_id") })
    }
}
