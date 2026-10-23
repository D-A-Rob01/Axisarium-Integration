package com.aletheion.cartomancy

import android.content.Context
import android.content.Intent
import androidx.core.content.FileProvider
import java.io.File

fun shareReading(context: Context, reading: ReadingArtifact, includeJson: Boolean, journalEntry: JournalEntry? = null) {
    val exportDirectory = File(context.cacheDir, "kybernion").apply { mkdirs() }
    val stem = "${reading.date}_tarot-reading_${slugify(reading.question.ifBlank { reading.spread })}${journalEntry?.let { "_${it.id.take(8)}" }.orEmpty()}"
    val markdownFile = File(exportDirectory, "$stem.md").apply {
        val annotations = journalEntry?.let { entry -> buildString {
            appendLine("\n## Astrerium Journal — Human Annotations")
            appendLine("\nReading ID: ${entry.id}. The committed draw is unchanged.")
            entry.notes.forEach { note ->
                appendLine("\n### ${note.kind.replaceFirstChar { it.uppercase() }} · ${note.at}")
                if(note.positions.isNotEmpty()) appendLine("Positions: ${note.positions.joinToString(", ")}")
                appendLine("\n${note.text}")
            }
        }}.orEmpty()
        writeText(ArtifactRenderer.toMarkdown(reading) + annotations, Charsets.UTF_8)
    }
    val files = mutableListOf(markdownFile)
    if (includeJson) {
        files += File(exportDirectory, "$stem.json").apply {
            val json = org.json.JSONObject(ArtifactRenderer.toJson(reading))
            journalEntry?.let { entry ->
                json.put("astrerium_journal", org.json.JSONObject(JournalCodec.encode(entry)).apply { remove("reading") })
            }
            writeText(json.toString(2) + "\n", Charsets.UTF_8)
        }
    }

    val authority = "${context.packageName}.fileprovider"
    val uris = ArrayList(files.map { file -> FileProvider.getUriForFile(context, authority, file) })
    val intent = if (uris.size == 1) {
        Intent(Intent.ACTION_SEND).apply {
            type = "text/markdown"
            putExtra(Intent.EXTRA_STREAM, uris.first())
        }
    } else {
        Intent(Intent.ACTION_SEND_MULTIPLE).apply {
            type = "text/plain"
            putParcelableArrayListExtra(Intent.EXTRA_STREAM, uris)
        }
    }.apply {
        addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
        putExtra(Intent.EXTRA_TITLE, stem)
    }

    context.startActivity(Intent.createChooser(intent, "Export Kybernion reading"))
}

private fun slugify(value: String): String = value
    .lowercase()
    .replace(Regex("[^a-z0-9]+"), "-")
    .trim('-')
    .take(48)
    .trimEnd('-')
    .ifBlank { "reading" }
