package com.aletheion.cartomancy

import androidx.compose.foundation.ExperimentalFoundationApi
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxWithConstraints
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.pager.HorizontalPager
import androidx.compose.foundation.pager.rememberPagerState
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ChevronLeft
import androidx.compose.material.icons.filled.ChevronRight
import androidx.compose.material.icons.filled.Close
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.rotate
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.window.Dialog
import androidx.compose.ui.window.DialogProperties
import coil.ImageLoader
import coil.compose.SubcomposeAsyncImage
import coil.decode.SvgDecoder
import coil.request.ImageRequest
import kotlinx.coroutines.launch

internal val KybernionCyan = Color(0xFF58E8F6)
internal val KybernionViolet = Color(0xFF9A7CFF)
internal val KybernionGold = Color(0xFFFFC857)
internal val KybernionNight = Color(0xFF080B14)

@Composable
internal fun rememberKybernionImageLoader(): ImageLoader {
    val context = LocalContext.current
    return remember(context) {
        ImageLoader.Builder(context)
            .components { add(SvgDecoder.Factory()) }
            .respectCacheHeaders(false)
            .build()
    }
}

@Composable
internal fun KybernionArtwork(
    drawn: DrawnCard,
    artwork: ArtworkEntry,
    imageLoader: ImageLoader,
    modifier: Modifier = Modifier,
) {
    val context = LocalContext.current
    val description = "${drawn.card.name}, ${drawn.orientation}, ${drawn.positionLabel}"
    SubcomposeAsyncImage(
        model = ImageRequest.Builder(context)
            .data("file:///android_asset/${artwork.assetPath}")
            .crossfade(false)
            .build(),
        imageLoader = imageLoader,
        contentDescription = description,
        contentScale = ContentScale.Fit,
        modifier = modifier.rotate(if (drawn.orientation == "reversed") 180f else 0f),
        loading = { ArtworkPlaceholder() },
        error = { ArtworkFailure(drawn.card.name) },
    )
}

@Composable
private fun ArtworkPlaceholder() {
    Box(Modifier.fillMaxSize().background(Color(0xFF090D1B)), contentAlignment = Alignment.Center) {
        Text("⋄", color = KybernionViolet, style = MaterialTheme.typography.headlineMedium)
    }
}

@Composable
private fun ArtworkFailure(cardName: String) {
    Box(
        Modifier.fillMaxSize().background(Color(0xFF24151E)).padding(12.dp),
        contentAlignment = Alignment.Center,
    ) {
        Text(
            "Artwork unavailable\n$cardName",
            color = Color(0xFFFFB4AB),
            textAlign = TextAlign.Center,
            style = MaterialTheme.typography.labelMedium,
        )
    }
}

@OptIn(ExperimentalFoundationApi::class)
@Composable
internal fun FullScreenCardViewer(
    cards: List<DrawnCard>,
    artwork: Map<String, ArtworkEntry>,
    initialIndex: Int,
    imageLoader: ImageLoader,
    onDismiss: () -> Unit,
) {
    Dialog(
        onDismissRequest = onDismiss,
        properties = DialogProperties(usePlatformDefaultWidth = false, decorFitsSystemWindows = false),
    ) {
        Surface(Modifier.fillMaxSize(), color = KybernionNight) {
            Column(Modifier.fillMaxSize().statusBarsPadding().navigationBarsPadding()) {
                Row(
                    Modifier.fillMaxWidth().padding(horizontal = 10.dp, vertical = 4.dp),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Column(Modifier.weight(1f)) {
                        Text("KYBERNION", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                        Text("CARD DETAIL", style = MaterialTheme.typography.labelSmall, color = KybernionCyan)
                    }
                    IconButton(onClick = onDismiss) {
                        Icon(Icons.Default.Close, contentDescription = "Close card detail")
                    }
                }
                val pagerState = rememberPagerState(initialPage = initialIndex) { cards.size }
                HorizontalPager(
                    state = pagerState,
                    key = { cards[it].card.id },
                    modifier = Modifier.weight(1f).fillMaxWidth(),
                ) { page ->
                    val drawn = cards[page]
                    val entry = requireNotNull(artwork[drawn.card.id])
                    CardDetailPage(drawn, entry, imageLoader)
                }
                val scope = rememberCoroutineScope()
                Row(
                    Modifier.fillMaxWidth().padding(horizontal = 12.dp, vertical = 6.dp),
                    horizontalArrangement = Arrangement.Center,
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    IconButton(
                        onClick = { scope.launch { pagerState.animateScrollToPage(pagerState.currentPage - 1) } },
                        enabled = pagerState.currentPage > 0,
                    ) { Icon(Icons.Default.ChevronLeft, contentDescription = "Previous card") }
                    Text(
                        "${pagerState.currentPage + 1} / ${cards.size}",
                        modifier = Modifier.width(88.dp),
                        textAlign = TextAlign.Center,
                        color = KybernionCyan,
                        style = MaterialTheme.typography.labelLarge,
                    )
                    IconButton(
                        onClick = { scope.launch { pagerState.animateScrollToPage(pagerState.currentPage + 1) } },
                        enabled = pagerState.currentPage < cards.lastIndex,
                    ) { Icon(Icons.Default.ChevronRight, contentDescription = "Next card") }
                }
            }
        }
    }
}

@Composable
private fun CardDetailPage(
    drawn: DrawnCard,
    artwork: ArtworkEntry,
    imageLoader: ImageLoader,
) {
    BoxWithConstraints(Modifier.fillMaxSize().padding(horizontal = 16.dp, vertical = 6.dp)) {
        if (maxWidth > maxHeight) {
            Row(Modifier.fillMaxSize(), horizontalArrangement = Arrangement.spacedBy(20.dp)) {
                Box(Modifier.weight(.55f).fillMaxHeight(), contentAlignment = Alignment.Center) {
                    KybernionArtwork(
                        drawn,
                        artwork,
                        imageLoader,
                        Modifier.fillMaxHeight().aspectRatio(.6f),
                    )
                }
                CardDetailText(
                    drawn,
                    Modifier.weight(.45f).fillMaxHeight().verticalScroll(rememberScrollState()),
                )
            }
        } else {
            Column(Modifier.fillMaxSize(), horizontalAlignment = Alignment.CenterHorizontally) {
                Box(Modifier.weight(1f).fillMaxWidth(), contentAlignment = Alignment.Center) {
                    KybernionArtwork(
                        drawn,
                        artwork,
                        imageLoader,
                        Modifier.fillMaxHeight().aspectRatio(.6f),
                    )
                }
                CardDetailText(drawn, Modifier.fillMaxWidth().padding(top = 12.dp))
            }
        }
    }
}

@Composable
private fun CardDetailText(drawn: DrawnCard, modifier: Modifier = Modifier) {
    val accent = cardAccent(drawn.card)
    Column(modifier, verticalArrangement = Arrangement.spacedBy(8.dp)) {
        Text(
            "${drawn.position.toString().padStart(2, '0')} · ${drawn.positionLabel.uppercase()}",
            style = MaterialTheme.typography.labelMedium,
            color = accent,
        )
        Text(drawn.card.name, style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.SemiBold)
        Surface(shape = RoundedCornerShape(100), color = accent.copy(alpha = .16f)) {
            Text(
                drawn.orientation.uppercase(),
                Modifier.padding(horizontal = 10.dp, vertical = 5.dp),
                style = MaterialTheme.typography.labelSmall,
                color = accent,
            )
        }
        Text(drawn.keywords.joinToString(" · "), color = MaterialTheme.colorScheme.onSurfaceVariant)
        HorizontalDivider(color = accent.copy(alpha = .28f))
        Text(drawn.positionPrompt, style = MaterialTheme.typography.bodyMedium)
        Spacer(Modifier.size(4.dp))
    }
}

internal fun cardAccent(card: Card): Color = when (card.suit?.lowercase()) {
    "wands" -> Color(0xFFFF8A5B)
    "cups" -> KybernionCyan
    "swords" -> Color(0xFF70A7FF)
    "pentacles" -> KybernionGold
    else -> KybernionViolet
}
