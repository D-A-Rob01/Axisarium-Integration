package com.aletheion.cartomancy

import org.junit.Assert.*
import org.junit.Test
import java.nio.file.Files

class ReadingJournalTest {
    private fun sample() = ReadingArtifact("2026-10-23","rider-waite-smith","three-card","reflective",
        "A question with \"quotes\" and 🌙", "Context\nline two", null,"",listOf(
            DrawnCard(1,"Pattern","What is here?",Card("major_18_moon","The Moon","major",18,null,"water",listOf("dream"),listOf("confusion")),"reversed")
        ))

    @Test fun snapshotsAndAnnotationsSurviveReopeningWithoutChangingDraw() {
        val dir=Files.createTempDirectory("astrerium-test").toFile()
        try {
            val journal=ReadingJournal(dir)
            val original=journal.create(sample())
            journal.append(original.id,"notice","First impression",listOf(1))
            journal.append(original.id,"revisit","A different view")
            val restored=ReadingJournal(dir).read(original.id)
            assertEquals(original.reading,restored.reading)
            assertEquals(listOf("notice","revisit"),restored.notes.map {it.kind})
            assertEquals("First impression",restored.latest("notice"))
            assertEquals(listOf(1),restored.notes.first().positions)
            assertEquals(1,ReadingJournal(dir).entries().size)
        } finally {dir.deleteRecursively()}
    }
    @Test fun sameDateAndQuestionProduceSeparateReadings() {
        val dir=Files.createTempDirectory("astrerium-ids").toFile()
        try {
            val journal=ReadingJournal(dir)
            val a=journal.create(sample());val b=journal.create(sample())
            assertNotEquals(a.id,b.id)
            assertEquals(2,journal.entries().size)
        } finally {dir.deleteRecursively()}
    }
    @Test fun codecRetainsAllAuditFieldsAndReferenceTerms() {
        val r=sample().copy(reviewStatus="reviewed",reviewDate="2026-10-24",usefulnessScore=4,
            actionTaken="Wait",projectionRisk="low",firstImpression="Earlier note")
        val entry=JournalEntry("test","today",r,emptyList())
        assertEquals(entry,JournalCodec.decode(JournalCodec.encode(entry)))
    }
    @Test fun invalidPositionDoesNotChangeSavedFile() {
        val dir=Files.createTempDirectory("astrerium-invalid").toFile()
        try {
            val journal=ReadingJournal(dir);val original=journal.create(sample())
            assertThrows(IllegalArgumentException::class.java) {journal.append(original.id,"relate","wrong position",listOf(9))}
            assertEquals(original,journal.read(original.id))
        } finally {dir.deleteRecursively()}
    }
    @Test fun corruptJournalIsReportedAndNotOverwritten() {
        val dir=Files.createTempDirectory("astrerium-corrupt").toFile()
        try {
            val file=java.io.File(dir,"broken.json");file.writeText("broken evidence")
            assertThrows(Exception::class.java) {ReadingJournal(dir).entries()}
            assertEquals("broken evidence",file.readText())
        } finally {dir.deleteRecursively()}
    }
}
