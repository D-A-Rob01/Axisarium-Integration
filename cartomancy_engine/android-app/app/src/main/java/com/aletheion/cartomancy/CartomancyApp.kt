package com.aletheion.cartomancy

import android.widget.Toast
import androidx.compose.foundation.background
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxWithConstraints
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.imePadding
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowForward
import androidx.compose.material.icons.filled.ArrowDropDown
import androidx.compose.material.icons.filled.Lock
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material.icons.filled.Share
import androidx.compose.material.icons.filled.Shuffle
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.ElevatedCard
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Slider
import androidx.compose.material3.Surface
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import coil.ImageLoader

@Composable
fun CartomancyApp() {
    val context = LocalContext.current
    val repository = remember { ContractRepository(context) }
    val artworkRepository = remember { ArtworkRepository(context) }
    val drawEngine = remember { DrawEngine() }
    val imageLoader = rememberKybernionImageLoader()
    var deck by remember { mutableStateOf<List<Card>?>(null) }
    var spreads by remember { mutableStateOf<List<Spread>>(emptyList()) }
    var artwork by remember { mutableStateOf<Map<String, ArtworkEntry>>(emptyMap()) }
    var loadingError by remember { mutableStateOf<String?>(null) }

    LaunchedEffect(Unit) {
        runCatching {
            val loadedDeck = repository.loadDeck("rider-waite-smith")
            deck = loadedDeck
            spreads = repository.loadAvailableSpreads()
            artwork = artworkRepository.load(loadedDeck)
        }.onFailure { loadingError = it.message ?: "Could not load the Kybernion contract." }
    }

    when {
        loadingError != null -> ErrorState(loadingError!!)
        deck == null || spreads.isEmpty() || artwork.size != 78 -> LinearProgressIndicator(Modifier.fillMaxWidth())
        else -> CaptureScreen(deck!!, spreads, artwork, drawEngine, imageLoader)
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun CaptureScreen(
    deck: List<Card>,
    spreads: List<Spread>,
    artwork: Map<String, ArtworkEntry>,
    drawEngine: DrawEngine,
    imageLoader: ImageLoader,
) {
    val context = LocalContext.current
    val session: ReadingSessionViewModel = viewModel()
    var question by rememberSaveable { mutableStateOf("") }
    var selectedSpreadId by rememberSaveable { mutableStateOf(spreads.first().id) }
    val selectedSpread = spreads.first { it.id == selectedSpreadId }
    var selectedMode by rememberSaveable { mutableStateOf("decision-support") }
    var contextNote by rememberSaveable { mutableStateOf("") }
    var confidence by rememberSaveable { mutableStateOf(3f) }
    var confidenceEnabled by rememberSaveable { mutableStateOf(false) }
    var allowReversals by rememberSaveable { mutableStateOf(true) }
    var includeJson by rememberSaveable { mutableStateOf(true) }
    var firstImpression by rememberSaveable { mutableStateOf("") }
    var viewerIndex by rememberSaveable { mutableStateOf<Int?>(null) }
    val reading = session.reading
    val scrollState = rememberScrollState()

    LaunchedEffect(reading) { scrollState.scrollTo(0) }

    Scaffold(
        containerColor = MaterialTheme.colorScheme.background,
        topBar = {
            TopAppBar(
                title = {
                    Column {
                        Text("KYBERNION", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                        Text("MOBILE HELM", style = MaterialTheme.typography.labelSmall, color = KybernionCyan)
                    }
                },
                actions = {
                    if (reading != null) {
                        IconButton(onClick = { session.clear(); firstImpression = ""; viewerIndex = null }) {
                            Icon(Icons.Default.Refresh, contentDescription = "Start a new reading")
                        }
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(containerColor = MaterialTheme.colorScheme.background),
            )
        },
    ) { scaffoldPadding ->
        BoxWithConstraints(Modifier.fillMaxSize().padding(scaffoldPadding)) {
            val limit = if (reading == null) 720.dp else 1080.dp
            val contentWidth = if (maxWidth > limit) limit else maxWidth
            Column(
                modifier = Modifier
                    .width(contentWidth)
                    .align(Alignment.TopCenter)
                    .verticalScroll(scrollState)
                    .navigationBarsPadding()
                    .imePadding()
                    .padding(horizontal = 18.dp, vertical = 12.dp),
                verticalArrangement = Arrangement.spacedBy(14.dp),
            ) {
                if (reading == null) {
                    HelmCue(question, selectedSpread, selectedMode)
                    SetupPanel(
                        question, { question = it }, selectedSpread, spreads,
                        { selectedSpreadId = it.id }, selectedMode, { selectedMode = it },
                        contextNote, { contextNote = it }, confidenceEnabled,
                        { confidenceEnabled = it }, confidence, { confidence = it },
                        allowReversals, { allowReversals = it }, includeJson, { includeJson = it },
                    )
                    Button(
                        onClick = {
                            session.recordReading(drawEngine.draw(
                                deckId = "rider-waite-smith",
                                deck = deck,
                                spread = selectedSpread,
                                mode = selectedMode,
                                question = question,
                                context = contextNote,
                                confidence = if (confidenceEnabled) confidence.toInt() else null,
                                allowReversals = allowReversals,
                            ))
                        },
                        modifier = Modifier.fillMaxWidth().heightIn(min = 56.dp),
                        colors = ButtonDefaults.buttonColors(containerColor = KybernionViolet, contentColor = Color(0xFF0B0815)),
                    ) {
                        Icon(Icons.Default.Shuffle, contentDescription = null)
                        Spacer(Modifier.width(10.dp))
                        Text("Commit immutable draw", fontWeight = FontWeight.Bold)
                    }
                } else {
                    ReadingSection(
                        reading = reading,
                        artwork = artwork,
                        imageLoader = imageLoader,
                        firstImpression = firstImpression,
                        onFirstImpressionChanged = { firstImpression = it },
                        includeJson = includeJson,
                        onIncludeJsonChanged = { includeJson = it },
                        onCardSelected = { viewerIndex = it },
                        onExport = {
                            shareReading(context, reading.withFirstImpression(firstImpression), includeJson)
                            Toast.makeText(context, "Reading prepared for sharing", Toast.LENGTH_SHORT).show()
                        },
                    )
                }
                Spacer(Modifier.height(8.dp))
            }
        }
    }

    if (reading != null && viewerIndex != null) {
        FullScreenCardViewer(reading.cards, artwork, viewerIndex!!, imageLoader) { viewerIndex = null }
    }
}

@Composable
private fun HelmCue(question: String, selectedSpread: Spread, selectedMode: String) {
    var cueIndex by rememberSaveable { mutableStateOf(0) }
    val cues = listOf(
        if (question.isBlank()) {
            "Name the tension, choice, or pattern—not the answer you hope to receive."
        } else {
            "Read the question as if someone else wrote it. Remove any verdict already hiding inside it."
        },
        "Give the symbols something real to press against: add only the context that could change your next move.",
        "Commit once. Record first contact before guidebook, search, or outside interpretation.",
        "After interpretation, choose one observable action and one moment to review whether it helped.",
    )
    Surface(
        modifier = Modifier.fillMaxWidth().clickable { cueIndex = (cueIndex + 1) % cues.size },
        shape = RoundedCornerShape(20.dp),
        color = Color.Transparent,
        border = BorderStroke(1.dp, KybernionCyan.copy(alpha = 0.24f)),
    ) {
        Row(
            Modifier
                .background(Brush.linearGradient(listOf(Color(0xFF1D1737), Color(0xFF10242E))))
                .padding(start = 16.dp, top = 14.dp, end = 8.dp, bottom = 14.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(14.dp),
        ) {
            Box(
                Modifier
                    .width(4.dp)
                    .heightIn(min = 76.dp)
                    .background(
                        Brush.verticalGradient(listOf(KybernionGold, KybernionViolet, KybernionCyan)),
                        RoundedCornerShape(999.dp),
                    ),
            )
            Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(5.dp)) {
                Text(
                    "FIELD CUE · ${cueIndex + 1}/${cues.size}",
                    style = MaterialTheme.typography.labelSmall,
                    color = KybernionGold,
                    fontWeight = FontWeight.Bold,
                )
                Text(cues[cueIndex], style = MaterialTheme.typography.titleSmall, fontWeight = FontWeight.Medium)
                Text(
                    "${selectedSpread.name.uppercase()} · ${selectedMode.uppercase()}",
                    style = MaterialTheme.typography.labelSmall,
                    color = KybernionCyan,
                )
            }
            IconButton(onClick = { cueIndex = (cueIndex + 1) % cues.size }) {
                Icon(Icons.AutoMirrored.Filled.ArrowForward, contentDescription = "Show another field cue", tint = KybernionViolet)
            }
        }
    }
}

@Composable
private fun SetupPanel(
    question: String,
    onQuestionChanged: (String) -> Unit,
    selectedSpread: Spread,
    spreads: List<Spread>,
    onSpreadSelected: (Spread) -> Unit,
    selectedMode: String,
    onModeSelected: (String) -> Unit,
    contextNote: String,
    onContextChanged: (String) -> Unit,
    confidenceEnabled: Boolean,
    onConfidenceEnabled: (Boolean) -> Unit,
    confidence: Float,
    onConfidenceChanged: (Float) -> Unit,
    allowReversals: Boolean,
    onAllowReversals: (Boolean) -> Unit,
    includeJson: Boolean,
    onIncludeJson: (Boolean) -> Unit,
) {
    ElevatedCard(
        colors = CardDefaults.elevatedCardColors(containerColor = MaterialTheme.colorScheme.surface),
        elevation = CardDefaults.elevatedCardElevation(6.dp),
        shape = RoundedCornerShape(24.dp),
    ) {
        Column(Modifier.padding(18.dp), verticalArrangement = Arrangement.spacedBy(16.dp)) {
            SectionLabel("INQUIRY")
            OutlinedTextField(
                value = question,
                onValueChange = onQuestionChanged,
                label = { Text("Question") },
                placeholder = { Text("What course requires attention?") },
                modifier = Modifier.fillMaxWidth(),
                minLines = 2,
            )
            DropdownField("Receptive formation", selectedSpread.name, spreads, { it.name }, onSpreadSelected)
            DropdownField("Interpretation protocol", selectedMode, DrawEngine.VALID_MODES.toList().sorted(), { it }, onModeSelected)
            OutlinedTextField(
                value = contextNote,
                onValueChange = onContextChanged,
                label = { Text("Context") },
                modifier = Modifier.fillMaxWidth(),
                minLines = 2,
            )
            HorizontalDivider(color = MaterialTheme.colorScheme.outlineVariant)
            SectionLabel("DRAW PARAMETERS")
            SettingSwitch("Record original confidence", confidenceEnabled, onConfidenceEnabled)
            if (confidenceEnabled) {
                Text("Confidence ${confidence.toInt()} / 5", style = MaterialTheme.typography.labelLarge, color = KybernionCyan)
                Slider(confidence, onConfidenceChanged, valueRange = 1f..5f, steps = 3)
            }
            SettingSwitch("Allow reversals", allowReversals, onAllowReversals)
            SettingSwitch("Create JSON sidecar", includeJson, onIncludeJson)
        }
    }
}

@Composable
private fun SettingSwitch(label: String, checked: Boolean, onCheckedChange: (Boolean) -> Unit) {
    Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
        Text(label, modifier = Modifier.weight(1f), style = MaterialTheme.typography.bodyLarge)
        Switch(checked = checked, onCheckedChange = onCheckedChange)
    }
}

@Composable
private fun ReadingSection(
    reading: ReadingArtifact,
    artwork: Map<String, ArtworkEntry>,
    imageLoader: ImageLoader,
    firstImpression: String,
    onFirstImpressionChanged: (String) -> Unit,
    includeJson: Boolean,
    onIncludeJsonChanged: (Boolean) -> Unit,
    onCardSelected: (Int) -> Unit,
    onExport: () -> Unit,
) {
    Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
        Icon(Icons.Default.Lock, contentDescription = null, tint = KybernionCyan)
        Text("${reading.cards.size} cards · ${reading.mode}", style = MaterialTheme.typography.labelLarge, color = KybernionCyan)
    }
    SpreadOverview(reading.cards, artwork, imageLoader, onCardSelected)
    ElevatedCard(shape = RoundedCornerShape(24.dp)) {
        Column(Modifier.padding(18.dp), verticalArrangement = Arrangement.spacedBy(14.dp)) {
            SectionLabel("FIRST CONTACT")
            Text("Record your response before consulting a reference.", color = MaterialTheme.colorScheme.onSurfaceVariant)
            OutlinedTextField(
                value = firstImpression,
                onValueChange = onFirstImpressionChanged,
                label = { Text("First impression") },
                modifier = Modifier.fillMaxWidth(),
                minLines = 4,
            )
            SettingSwitch("Include JSON sidecar", includeJson, onIncludeJsonChanged)
            Button(onClick = onExport, modifier = Modifier.fillMaxWidth().heightIn(min = 54.dp)) {
                Icon(Icons.Default.Share, contentDescription = null)
                Spacer(Modifier.width(8.dp))
                Text(if (includeJson) "Share Markdown + JSON" else "Share Markdown")
            }
        }
    }
}

@Composable
private fun SpreadOverview(
    cards: List<DrawnCard>,
    artwork: Map<String, ArtworkEntry>,
    imageLoader: ImageLoader,
    onCardSelected: (Int) -> Unit,
) {
    BoxWithConstraints(Modifier.fillMaxWidth()) {
        val columns = when {
            maxWidth < 480.dp -> 3
            maxWidth < 760.dp -> 4
            else -> 6
        }
        Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
            cards.chunked(columns).forEachIndexed { rowIndex, rowCards ->
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                    rowCards.forEachIndexed { columnIndex, drawn ->
                        val index = rowIndex * columns + columnIndex
                        SpreadCard(
                            drawn = drawn,
                            artwork = requireNotNull(artwork[drawn.card.id]),
                            imageLoader = imageLoader,
                            modifier = Modifier.weight(1f),
                            onClick = { onCardSelected(index) },
                        )
                    }
                    repeat(columns - rowCards.size) { Spacer(Modifier.weight(1f)) }
                }
            }
        }
    }
}

@Composable
private fun SpreadCard(
    drawn: DrawnCard,
    artwork: ArtworkEntry,
    imageLoader: ImageLoader,
    modifier: Modifier,
    onClick: () -> Unit,
) {
    val accent = cardAccent(drawn.card)
    ElevatedCard(
        modifier = modifier.clickable(onClick = onClick),
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.elevatedCardColors(containerColor = MaterialTheme.colorScheme.surface),
        elevation = CardDefaults.elevatedCardElevation(4.dp),
    ) {
        Column(Modifier.padding(7.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
            KybernionArtwork(drawn, artwork, imageLoader, Modifier.fillMaxWidth().aspectRatio(.6f))
            Text(
                drawn.position.toString().padStart(2, '0'),
                style = MaterialTheme.typography.labelSmall,
                color = accent,
            )
            Text(
                drawn.positionLabel.uppercase(),
                minLines = 2,
                maxLines = 2,
                overflow = TextOverflow.Ellipsis,
                style = MaterialTheme.typography.labelSmall,
            )
            Text(
                drawn.card.name,
                maxLines = 2,
                overflow = TextOverflow.Ellipsis,
                style = MaterialTheme.typography.bodySmall,
                fontWeight = FontWeight.SemiBold,
            )
            Text(
                drawn.orientation.uppercase(),
                modifier = Modifier.fillMaxWidth(),
                textAlign = TextAlign.Center,
                color = accent,
                style = MaterialTheme.typography.labelSmall,
            )
        }
    }
}

@Composable
private fun SectionLabel(text: String) {
    Text(text, style = MaterialTheme.typography.labelMedium, fontWeight = FontWeight.Bold, color = KybernionCyan)
}

@Composable
private fun <T> DropdownField(
    label: String,
    value: String,
    options: List<T>,
    optionLabel: (T) -> String,
    onSelected: (T) -> Unit,
) {
    var expanded by remember { mutableStateOf(false) }
    Box(Modifier.fillMaxWidth()) {
        OutlinedButton(onClick = { expanded = true }, modifier = Modifier.fillMaxWidth().heightIn(min = 56.dp)) {
            Column(Modifier.weight(1f), horizontalAlignment = Alignment.Start) {
                Text(label, style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                Text(value, maxLines = 1, overflow = TextOverflow.Ellipsis)
            }
            Icon(Icons.Default.ArrowDropDown, contentDescription = null)
        }
        DropdownMenu(expanded = expanded, onDismissRequest = { expanded = false }) {
            options.forEach { option ->
                DropdownMenuItem(
                    text = { Text(optionLabel(option)) },
                    onClick = { onSelected(option); expanded = false },
                )
            }
        }
    }
}

@Composable
private fun ErrorState(message: String) {
    Column(
        Modifier.fillMaxSize().padding(24.dp),
        verticalArrangement = Arrangement.Center,
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Text("Kybernion contract unavailable", style = MaterialTheme.typography.titleLarge)
        Spacer(Modifier.height(8.dp))
        Text(message, style = MaterialTheme.typography.bodyMedium, textAlign = TextAlign.Center)
    }
}
