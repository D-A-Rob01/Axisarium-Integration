package com.aletheion.cartomancy

import android.content.Context
import org.json.JSONObject

data class ArtworkEntry(
    val cardId: String,
    val assetPath: String,
    val sha256: String,
)

class ArtworkRepository(private val context: Context) {
    fun load(deck: List<Card>): Map<String, ArtworkEntry> {
        val root = context.assets.open("tarot-v3/artwork-index.json")
            .bufferedReader(Charsets.UTF_8)
            .use { JSONObject(it.readText()) }
        require(root.getString("schema") == "kybernion-android-artwork-v1") {
            "Unsupported Kybernion artwork schema"
        }
        require(root.getString("deck_id") == "rider-waite-smith") {
            "Artwork index does not target the bundled deck"
        }
        val cards = root.getJSONArray("cards")
        val entries = buildMap {
            for (index in 0 until cards.length()) {
                val item = cards.getJSONObject(index)
                val entry = ArtworkEntry(
                    cardId = item.getString("card_id"),
                    assetPath = item.getString("asset_path"),
                    sha256 = item.getString("sha256"),
                )
                require(put(entry.cardId, entry) == null) {
                    "Duplicate artwork mapping for ${entry.cardId}"
                }
            }
        }
        val deckIds = deck.map { it.id }.toSet()
        require(entries.size == 78 && deckIds.size == 78 && entries.keys == deckIds) {
            "Kybernion v3 artwork must map exactly to all 78 bundled cards"
        }
        entries.values.forEach { entry ->
            context.assets.open(entry.assetPath).close()
        }
        return entries
    }
}
