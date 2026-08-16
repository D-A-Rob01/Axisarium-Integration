package com.aletheion.cartomancy

import android.os.Parcelable
import kotlinx.parcelize.Parcelize

@Parcelize
data class Card(
    val id: String,
    val name: String,
    val arcana: String,
    val number: Int,
    val suit: String?,
    val element: String?,
    val uprightKeywords: List<String>,
    val reversedKeywords: List<String>,
) : Parcelable

data class SpreadPosition(
    val index: Int,
    val label: String,
    val prompt: String,
)

data class Spread(
    val id: String,
    val name: String,
    val positions: List<SpreadPosition>,
)

@Parcelize
data class DrawnCard(
    val position: Int,
    val positionLabel: String,
    val positionPrompt: String,
    val card: Card,
    val orientation: String,
) : Parcelable {
    val keywords: List<String>
        get() = if (orientation == "reversed") card.reversedKeywords else card.uprightKeywords
}

@Parcelize
data class ReadingArtifact(
    val date: String,
    val deck: String,
    val spread: String,
    val mode: String,
    val question: String,
    val context: String,
    val confidence: Int?,
    val firstImpression: String,
    val cards: List<DrawnCard>,
    val architecture: String = "kybernion",
    val drawStatus: String = "immutable",
    val tags: List<String> = listOf("tarot", "kybernion", "aletheion", "symbolic-audit", "android-capture"),
    val reviewStatus: String = "pending",
    val reviewDate: String? = null,
    val usefulnessScore: Int? = null,
    val projectionRisk: String? = null,
    val actionTaken: String? = null,
    val claimTypes: List<String> = listOf(
        "observation",
        "symbolic-association",
        "intuition",
        "interpretation",
        "prediction",
        "action-recommendation",
    ),
) : Parcelable {
    fun withFirstImpression(value: String): ReadingArtifact = copy(firstImpression = value)
}
