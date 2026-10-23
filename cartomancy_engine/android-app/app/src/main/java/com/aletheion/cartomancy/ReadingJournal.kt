package com.aletheion.cartomancy

import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.nio.file.Files
import java.nio.file.StandardCopyOption
import java.time.Instant
import java.util.UUID

data class JournalNote(val kind: String, val text: String, val at: String, val positions: List<Int>)
data class JournalEntry(val id: String, val createdAt: String, val reading: ReadingArtifact, val notes: List<JournalNote>) {
    fun latest(kind: String): String = notes.lastOrNull { it.kind == kind }?.text.orEmpty()
}

/** Immutable draw snapshots with append-only human annotations. No network or background worker. */
class ReadingJournal(private val directory: File) {
    init { require(directory.isDirectory || directory.mkdirs()) { "Cannot open local reading journal" } }

    @Synchronized fun create(reading: ReadingArtifact): JournalEntry {
        val entry = JournalEntry(UUID.randomUUID().toString(), Instant.now().toString(), reading, emptyList())
        write(entry)
        return entry
    }

    @Synchronized fun read(id: String): JournalEntry {
        require(id.matches(Regex("[a-f0-9-]{36}"))) { "Invalid reading identifier" }
        return JournalCodec.decode(File(directory, "$id.json").readText())
    }

    @Synchronized fun entries(): List<JournalEntry> = directory.listFiles().orEmpty()
        .filter { it.extension == "json" }.map { JournalCodec.decode(it.readText()) }.sortedByDescending { it.createdAt }

    @Synchronized fun append(id: String, kind: String, text: String, positions: List<Int> = emptyList()): JournalEntry {
        require(kind in listOf("notice", "relate", "revisit"))
        require(text.isNotBlank()) { "Write an observation before keeping it" }
        val original = read(id)
        require(positions.all { position -> original.reading.cards.any { it.position == position } })
        val updated = original.copy(notes = original.notes + JournalNote(kind, text, Instant.now().toString(), positions))
        write(updated)
        return updated
    }

    private fun write(entry: JournalEntry) {
        val target = File(directory, "${entry.id}.json")
        val temp = File.createTempFile("journal-", ".tmp", directory)
        try {
            temp.outputStream().use { stream ->
                stream.write(JournalCodec.encode(entry).toByteArray(Charsets.UTF_8))
                stream.fd.sync()
            }
            Files.move(temp.toPath(), target.toPath(), StandardCopyOption.ATOMIC_MOVE, StandardCopyOption.REPLACE_EXISTING)
        } finally { temp.delete() }
    }
}

object JournalCodec {
    fun encode(entry: JournalEntry): String {
        val snapshot = JSONObject(ArtifactRenderer.toJson(entry.reading))
        // Preserve both orientations' reference terms, so an old snapshot never depends on a future corpus.
        val cards = snapshot.getJSONArray("cards")
        entry.reading.cards.forEachIndexed { index, drawn ->
            cards.getJSONObject(index)
                .put("upright_keywords", JSONArray(drawn.card.uprightKeywords))
                .put("reversed_keywords", JSONArray(drawn.card.reversedKeywords))
        }
        return JSONObject().put("journal_schema", 1).put("id", entry.id).put("created_at", entry.createdAt)
            .put("reading", snapshot).put("notes", JSONArray(entry.notes.map { note ->
                JSONObject().put("kind", note.kind).put("text", note.text).put("at", note.at)
                    .put("positions", JSONArray(note.positions))
            })).toString(2)
    }

    fun decode(text: String): JournalEntry {
        val root = JSONObject(text)
        require(root.getInt("journal_schema") == 1) { "Unsupported journal format; original file preserved" }
        val r = root.getJSONObject("reading")
        require(r.getString("draw_status") == "immutable")
        val cards = r.getJSONArray("cards")
        val reading = ReadingArtifact(
            date = r.getString("date"), deck = r.getString("deck"), spread = r.getString("spread"),
            mode = r.getString("mode"), question = r.getString("question"), context = r.getString("context"),
            confidence = if (r.isNull("confidence")) null else r.getInt("confidence"),
            firstImpression = r.getString("first_impression"),
            cards = (0 until cards.length()).map { index ->
                val c = cards.getJSONObject(index)
                DrawnCard(c.getInt("position"), c.getString("position_label"), c.getString("position_prompt"),
                    Card(c.getString("card_id"), c.getString("card"), c.getString("arcana"), c.getInt("number"),
                        if(c.isNull("suit")) null else c.getString("suit"),
                        if(c.isNull("element")) null else c.getString("element"),
                        strings(c.getJSONArray("upright_keywords")), strings(c.getJSONArray("reversed_keywords"))),
                    c.getString("orientation"))
            }, architecture = r.getString("architecture"), drawStatus = r.getString("draw_status"),
            tags = strings(r.getJSONArray("tags")), reviewStatus = r.getString("review_status"),
            reviewDate = r.nullableString("review_date"), usefulnessScore = if(r.isNull("usefulness_score")) null else r.getInt("usefulness_score"),
            projectionRisk = r.nullableString("projection_risk"), actionTaken = r.nullableString("action_taken"),
            claimTypes = strings(r.getJSONArray("claim_types")),
        )
        val notes = root.getJSONArray("notes")
        return JournalEntry(root.getString("id"), root.getString("created_at"), reading,
            (0 until notes.length()).map { index ->
                val n = notes.getJSONObject(index)
                val p = n.getJSONArray("positions")
                JournalNote(n.getString("kind"), n.getString("text"), n.getString("at"), (0 until p.length()).map { p.getInt(it) })
            })
    }
    private fun strings(array: JSONArray) = (0 until array.length()).map { array.getString(it) }
    private fun JSONObject.nullableString(key: String) = if(isNull(key)) null else getString(key)
}
