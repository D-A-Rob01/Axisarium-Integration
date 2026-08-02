package com.aletheion.cartomancy

import android.content.Context
import android.content.Intent
import androidx.core.content.FileProvider
import java.io.File

fun shareReading(context: Context, reading: ReadingArtifact, includeJson: Boolean) {
    val exportDirectory = File(context.cacheDir, "kybernion").apply { mkdirs() }
    val stem = "${reading.date}_tarot-reading_${slugify(reading.question.ifBlank { reading.spread })}"
    val markdownFile = File(exportDirectory, "$stem.md").apply {
        writeText(ArtifactRenderer.toMarkdown(reading), Charsets.UTF_8)
    }
    val files = mutableListOf(markdownFile)
    if (includeJson) {
        files += File(exportDirectory, "$stem.json").apply {
            writeText(ArtifactRenderer.toJson(reading), Charsets.UTF_8)
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
