package com.aletheion.cartomancy

import android.content.Context
import org.json.JSONArray
import org.json.JSONObject

class ContractRepository(private val context: Context) {
    fun loadDeck(deckId: String): List<Card> {
        val payload = JSONObject(readAsset("decks/$deckId.json"))
        val cards = payload.getJSONArray("cards")
        return (0 until cards.length()).map { index -> cards.getJSONObject(index).toCard() }
    }

    fun loadSpread(spreadId: String): Spread {
        val payload = JSONObject(readAsset("spreads/$spreadId.json"))
        val positions = payload.getJSONArray("positions")
        return Spread(
            id = payload.getString("id"),
            name = payload.getString("name"),
            positions = (0 until positions.length()).map { index ->
                val position = positions.getJSONObject(index)
                SpreadPosition(
                    index = position.getInt("index"),
                    label = position.getString("label"),
                    prompt = position.getString("prompt"),
                )
            },
        )
    }

    fun loadAvailableSpreads(): List<Spread> = listOf("three-card", "the-constellation").map(::loadSpread)

    private fun readAsset(name: String): String = context.assets.open(name).bufferedReader().use { it.readText() }
}

private fun JSONObject.toCard(): Card = Card(
    id = getString("id"),
    name = getString("name"),
    arcana = getString("arcana"),
    number = getInt("number"),
    suit = nullableString("suit"),
    element = nullableString("element"),
    uprightKeywords = getStringList("upright_keywords"),
    reversedKeywords = getStringList("reversed_keywords"),
)

private fun JSONObject.nullableString(name: String): String? = if (isNull(name)) null else getString(name)

private fun JSONObject.getStringList(name: String): List<String> {
    val values = getJSONArray(name)
    return (0 until values.length()).map { index -> values.getString(index) }
}
