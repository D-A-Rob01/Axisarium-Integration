package com.aletheion.cartomancy

import android.widget.Toast
import androidx.compose.foundation.background
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.Canvas
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
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowDropDown
import androidx.compose.material.icons.filled.ExpandMore
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
import androidx.compose.material3.TextButton
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import kotlin.math.PI
import kotlin.math.cos
import kotlin.math.sin
import kotlin.random.Random
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
                    KyberneticField(question, selectedSpread, selectedMode, allowReversals)
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
private fun KyberneticField(question: String, selectedSpread: Spread, selectedMode: String, allowReversals: Boolean) {
    var generation by rememberSaveable { mutableStateOf(0) }
    val signature = "$question|${selectedSpread.id}|$selectedMode|$allowReversals|$generation"
    val nodes = remember(signature) {
        val random = Random(signature.hashCode())
        List(selectedSpread.positions.size.coerceIn(3, 9)) {
            FieldNode(random.nextFloat(), random.nextFloat(), random.nextFloat())
        }
    }
    Surface(
        modifier = Modifier.fillMaxWidth().clickable { generation++ },
        shape = RoundedCornerShape(28.dp),
        color = Color(0xFF0B0A17),
        border = BorderStroke(1.dp, KybernionCyan.copy(alpha = 0.30f)),
    ) {
        Box(Modifier.fillMaxWidth().height(210.dp).background(Brush.radialGradient(listOf(Color(0xFF231844), Color(0xFF0B0A17))))) {
            Canvas(Modifier.fillMaxSize().padding(18.dp)) {
                val points = nodes.map { node ->
                    androidx.compose.ui.geometry.Offset(
                        x = size.width * (.12f + node.x * .76f),
                        y = size.height * (.16f + node.y * .68f),
                    )
                }
                points.forEachIndexed { index, point ->
                    val next = points[(index + 1) % points.size]
                    val control = androidx.compose.ui.geometry.Offset((point.x + next.x) / 2f, size.height * nodes[index].bend)
                    val path = Path().apply { moveTo(point.x, point.y); quadraticBezierTo(control.x, control.y, next.x, next.y) }
                    drawPath(path, KybernionViolet.copy(alpha = .44f), style = Stroke(1.5.dp.toPx(), cap = StrokeCap.Round))
                    if (index % 2 == 0) drawLine(KybernionCyan.copy(alpha = .18f), point, points[(index + 2) % points.size], 1.dp.toPx())
                }
                points.forEachIndexed { index, point ->
                    val radius = (if (index == 0) 8 else 5).dp.toPx()
                    drawCircle(KybernionCyan.copy(alpha = .13f), radius * 2.4f, point)
                    drawCircle(if (index == 0) KybernionGold else KybernionCyan, radius, point, style = Stroke(1.5.dp.toPx()))
                    drawCircle(Color(0xFF0B0A17), radius * .35f, point)
                }
            }
            Column(Modifier.align(Alignment.TopStart).padding(18.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                Text(
                    "KYBERNETIC FIELD · ${generation.toString().padStart(2, '0')}",
                    style = MaterialTheme.typography.labelSmall,
                    color = KybernionGold,
                    fontWeight = FontWeight.Bold,
                )
                Text(
                    if (question.isBlank()) "AWAITING INQUIRY" else question.uppercase(),
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis,
                    style = MaterialTheme.typography.titleSmall,
                    fontWeight = FontWeight.Medium,
                )
            }
            Text(
                "${selectedSpread.name.uppercase()}  /  ${selectedMode.uppercase()}  /  ${if (allowReversals) "REVERSALS OPEN" else "UPRIGHT"}",
                modifier = Modifier.align(Alignment.BottomStart).padding(18.dp),
                    style = MaterialTheme.typography.labelSmall,
                    color = KybernionCyan,
            )
        }
    }
}

private data class FieldNode(val x: Float, val y: Float, val bend: Float)

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
    var expanded by rememberSaveable { mutableStateOf(false) }
    ElevatedCard(
        colors = CardDefaults.elevatedCardColors(containerColor = MaterialTheme.colorScheme.surface),
        elevation = CardDefaults.elevatedCardElevation(6.dp),
        shape = RoundedCornerShape(24.dp),
    ) {
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
            SectionLabel("ENCOUNTER")
            OutlinedTextField(
                value = question,
                onValueChange = onQuestionChanged,
                label = { Text("Question") },
                placeholder = { Text("What course requires attention?") },
                modifier = Modifier.fillMaxWidth(),
                singleLine = true,
            )
            Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                Box(Modifier.weight(1f)) { DropdownField("Formation", selectedSpread.name, spreads, { it.name }, onSpreadSelected) }
                Box(Modifier.weight(1f)) { DropdownField("Protocol", selectedMode, DrawEngine.VALID_MODES.toList().sorted(), { it }, onModeSelected) }
            }
            Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
                SettingSwitch("Reversals", allowReversals, onAllowReversals, Modifier.weight(1f))
                TextButton(onClick = { expanded = !expanded }) {
                    Text(if (expanded) "Less" else "Refine")
                    Icon(Icons.Default.ExpandMore, contentDescription = null)
                }
            }
            if (expanded) {
                HorizontalDivider(color = MaterialTheme.colorScheme.outlineVariant)
                OutlinedTextField(value = contextNote, onValueChange = onContextChanged, label = { Text("Context note") }, modifier = Modifier.fillMaxWidth(), minLines = 2)
                SettingSwitch("Record confidence", confidenceEnabled, onConfidenceEnabled)
                if (confidenceEnabled) {
                    Text("Confidence ${confidence.toInt()} / 5", style = MaterialTheme.typography.labelLarge, color = KybernionCyan)
                    Slider(confidence, onConfidenceChanged, valueRange = 1f..5f, steps = 3)
                }
                SettingSwitch("JSON sidecar", includeJson, onIncludeJson)
            }
        }
    }
}

@Composable
private fun SettingSwitch(label: String, checked: Boolean, onCheckedChange: (Boolean) -> Unit, modifier: Modifier = Modifier) {
    Row(modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
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
