package com.aletheion.cartomancy

import android.widget.Toast
import androidx.activity.compose.BackHandler
import androidx.compose.foundation.*
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.viewmodel.compose.viewModel
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.io.File

private val Pearl = Color(0xFFF4F0E9)
private val Muted = Color(0xFFC1BBD0)
private val Violet = Color(0xFFBBA3F4)
private val Panel = Color(0xEF090D1A)

@Composable fun CartomancyApp() {
    val context = LocalContext.current
    var deck by remember { mutableStateOf<List<Card>>(emptyList()) }
    var spreads by remember { mutableStateOf<List<Spread>>(emptyList()) }
    var art by remember { mutableStateOf<Map<String, ArtCell>>(emptyMap()) }
    var error by remember { mutableStateOf<String?>(null) }
    LaunchedEffect(Unit) {
        runCatching { withContext(Dispatchers.IO) {
            val repository = ContractRepository(context)
            val cards = repository.loadDeck("rider-waite-smith")
            ArtworkRepository(context).load(cards)
            Triple(cards, repository.loadAvailableSpreads(), AstreriumArt.loadIndex(context, cards))
        }}.onSuccess { deck=it.first; spreads=it.second; art=it.third }.onFailure { error=it.message }
    }
    Box(Modifier.fillMaxSize()) {
        AstreriumBackground()
        when {
            error != null -> Column(Modifier.align(Alignment.Center).padding(28.dp)) {
                Heading("The collection needs attention")
                Text(error!!, color=Pearl)
                Text("Your saved readings are preserved.", color=Muted)
            }
            deck.isEmpty() -> CircularProgressIndicator(Modifier.align(Alignment.Center))
            else -> AstreriumShell(deck, spreads, art)
        }
    }
}

@Composable private fun AstreriumShell(deck: List<Card>, spreads: List<Spread>, art: Map<String, ArtCell>) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val journal = remember { ReadingJournal(File(context.filesDir,"astrerium-journal")) }
    val prefs = remember { context.getSharedPreferences("astrerium",0) }
    val legacy: ReadingSessionViewModel = viewModel()
    var page by rememberSaveable { mutableStateOf("encounter") }
    var entry by remember { mutableStateOf<JournalEntry?>(null) }
    var history by remember { mutableStateOf<List<JournalEntry>>(emptyList()) }
    var busy by remember { mutableStateOf(false) }
    var message by remember { mutableStateOf<String?>(null) }
    var confirmNew by remember { mutableStateOf(false) }
    var question by rememberSaveable { mutableStateOf("") }
    var contextNote by rememberSaveable { mutableStateOf("") }
    var spreadId by rememberSaveable { mutableStateOf("three-card") }
    var mode by rememberSaveable { mutableStateOf("decision-support") }
    var reversals by rememberSaveable { mutableStateOf(true) }
    var confidence by rememberSaveable { mutableStateOf(0) }
    var includeJson by rememberSaveable { mutableStateOf(true) }
    fun fail(t: Throwable) { message = t.message ?: "The operation could not be completed." }
    fun loadHistory() {
        scope.launch { busy=true; runCatching { withContext(Dispatchers.IO) { journal.entries() } }
            .onSuccess { history=it;page="journal" }.onFailure(::fail);busy=false }
    }
    LaunchedEffect(Unit) {
        busy=true
        runCatching { withContext(Dispatchers.IO) {
            val active=prefs.getString("active",null)
            when { active!=null -> journal.read(active); legacy.reading!=null -> journal.create(legacy.reading!!);else->null }
        }}.onSuccess { restored ->
            entry=restored
            if(restored!=null) { prefs.edit().putString("active",restored.id).apply(); if(page=="encounter") page="reading" }
        }.onFailure(::fail)
        busy=false
    }
    BackHandler(page!="encounter") { page=if(page=="reading") "encounter" else if(entry!=null) "reading" else "encounter" }
    Column(Modifier.fillMaxSize().statusBarsPadding().navigationBarsPadding()) {
        Column(Modifier.fillMaxWidth().background(Color(0xD9080B14)).padding(top=12.dp,bottom=6.dp),horizontalAlignment=Alignment.CenterHorizontally) {
            Text("K Y B E R N I O N",color=Pearl,fontSize=16.sp,fontFamily=FontFamily.Serif)
            Text("Astrerium",color=Pearl,fontSize=24.sp,fontFamily=FontFamily.Serif)
            Row(horizontalArrangement=Arrangement.Center,modifier=Modifier.fillMaxWidth()) {
                TextButton(onClick={ if(entry!=null) page="reading" else page="encounter" }) { Text("Encounter") }
                TextButton(onClick={loadHistory()},enabled=!busy) { Text("Journal") }
                TextButton(onClick={page="deck"}) { Text("Deck") }
                TextButton(onClick={page="about"}) { Text("About") }
            }
        }
        if(busy) LinearProgressIndicator(Modifier.fillMaxWidth())
        BoxWithConstraints(Modifier.weight(1f).fillMaxWidth()) {
            val width = if(maxWidth>920.dp) 920.dp else maxWidth
            val scroll = key(page, entry?.id) { rememberScrollState() }
            Column(Modifier.width(width).align(Alignment.TopCenter).verticalScroll(scroll).imePadding()
                .padding(horizontal=22.dp,vertical=18.dp),verticalArrangement=Arrangement.spacedBy(18.dp)) {
                message?.let { error -> DarkPanel { Text(error,color=Color(0xFFFFC3C3)); TextButton(onClick={message=null}) {Text("Dismiss")} } }
                when(page) {
                    "encounter" -> {
                        Heading("What is asking\nto become?")
                        Text("A space for symbolic inquiry.",color=Muted,modifier=Modifier.align(Alignment.CenterHorizontally))
                        WaveDivider()
                        DarkPanel {
                            OutlinedTextField(question,{question=it},label={Text("Your question")},placeholder={Text("What deserves my attention?")},modifier=Modifier.fillMaxWidth(),minLines=2)
                            Choice("Formation",spreads.first {it.id==spreadId}.name,spreads.map {it.id to it.name}) {spreadId=it}
                            val spread=spreads.first {it.id==spreadId}
                            Text(formationPurpose(spreadId),color=Muted,fontSize=15.sp)
                            var showPositions by rememberSaveable {mutableStateOf(false)}
                            TextButton(onClick={showPositions=!showPositions}) {Text(if(showPositions) "Hide positions" else "Explore ${spread.positions.size} positions")}
                            if(showPositions) spread.positions.forEach { Text("${it.index}. ${it.label}\n${it.prompt}",color=Muted,fontSize=15.sp) }
                            Choice("Protocol",mode,DrawEngine.VALID_MODES.sorted().map {it to it}) {mode=it}
                            OutlinedTextField(contextNote,{contextNote=it},label={Text("Context · optional")},modifier=Modifier.fillMaxWidth(),minLines=2)
                            Row(Modifier.fillMaxWidth(),verticalAlignment=Alignment.CenterVertically) {
                                Text("Allow reversals",Modifier.weight(1f)); Switch(reversals,{reversals=it})
                            }
                            Choice("Confidence · optional",if(confidence==0) "Not recorded" else "$confidence / 5",(0..5).map {it.toString() to if(it==0) "Not recorded" else "$it / 5"}) {confidence=it.toInt()}
                            Button(onClick={
                                scope.launch {
                                    busy=true
                                    runCatching { withContext(Dispatchers.IO) {
                                        val reading=DrawEngine().draw("rider-waite-smith",deck,spread,mode,question,contextNote,confidence.takeIf {it>0},reversals)
                                        journal.create(reading)
                                    }}.onSuccess {
                                        entry=it;prefs.edit().putString("active",it.id).apply();legacy.recordReading(it.reading);page="reading"
                                    }.onFailure(::fail)
                                    busy=false
                                }
                            },enabled=!busy && question.isNotBlank(),modifier=Modifier.fillMaxWidth().heightIn(min=54.dp)) {Text("Commit immutable draw")}
                            Text("Your cards are fixed at commitment and saved on this device. Observations can grow around them.",color=Muted,fontSize=14.sp)
                        }
                    }
                    "reading" -> entry?.let { current ->
                        ReadingGarden(current,art,includeJson,{includeJson=it},busy,
                            onSave={kind,text,positions -> scope.launch {
                                busy=true
                                runCatching { withContext(Dispatchers.IO) {journal.append(current.id,kind,text,positions)} }
                                    .onSuccess {entry=it; withContext(Dispatchers.Main) { Toast.makeText(context,"Kept in your journal",Toast.LENGTH_SHORT).show() }}.onFailure(::fail)
                                busy=false
                            }},
                            onShare={runCatching {shareReading(context,current.reading.withFirstImpression(current.latest("notice").ifBlank {current.reading.firstImpression}),includeJson,current)}.onFailure(::fail)},
                            onNew={confirmNew=true})
                    }
                    "journal" -> {
                        Heading("Return with new eyes")
                        Text("${history.size} saved readings · on this device",color=Muted)
                        if(history.isEmpty()) DarkPanel {Text("Your first committed reading will appear here.");TextButton(onClick={page="encounter"}) {Text("Begin an inquiry")}}
                        history.forEach { item ->
                            Surface(onClick={entry=item;prefs.edit().putString("active",item.id).apply();page="reading"},color=Panel,shape=RoundedCornerShape(12.dp)) {
                                Column(Modifier.fillMaxWidth().padding(18.dp),verticalArrangement=Arrangement.spacedBy(7.dp)) {
                                    Text(item.reading.question.ifBlank {"Untitled inquiry"},fontFamily=FontFamily.Serif,fontSize=22.sp)
                                    Text("${item.reading.date} · ${item.reading.spread}",color=Muted,fontSize=14.sp)
                                    Text("${item.reading.cards.size} cards · ${item.notes.size} kept observations",color=Violet,fontSize=14.sp)
                                }
                            }
                        }
                    }
                    "deck" -> DeckGarden(deck,art)
                    "about" -> {
                        Heading("An instrument\nof attention")
                        DarkPanel {
                            Text("Kybernion · Astrerium 0.4.0",fontFamily=FontFamily.Serif,fontSize=24.sp)
                            Text("Ask. Draw. Notice. Relate. Revisit.",color=Violet)
                            Text("The deck offers symbolic prompts. Your observations, associations, and interpretations remain your own. A reading does not establish another person's thoughts or a measured prediction.")
                            Text("The plasma and wavelength imagery is a visual metaphor. Sparse elemental marks follow the deck's existing element metadata; the artwork is a new Astrerium interpretation.")
                            Text("Readings and dated annotations are stored privately on this device. There is no cloud sync or AI interpretation. Android's share sheet exports Markdown and optional JSON; selecting a destination is your action.")
                            Text("Export important readings before uninstalling. Uninstalling removes the local journal and unfinished drafts.",color=Muted)
                            Text("Art direction developed with David. Painted assets generated with OpenAI image generation; card titles, identity marks and interaction are native Android components.",color=Muted,fontSize=14.sp)
                        }
                    }
                }
                Spacer(Modifier.height(18.dp))
            }
        }
    }
    if(confirmNew) AlertDialog(onDismissRequest={confirmNew=false},title={Text("Begin another inquiry?")},
        text={Text("This committed reading and kept observations remain in your journal. Keep any unfinished text before continuing.")},
        confirmButton={TextButton(onClick={confirmNew=false;prefs.edit().remove("active").apply();entry=null;legacy.clear();page="encounter";question="";contextNote=""}) {Text("New inquiry")}},
        dismissButton={TextButton(onClick={confirmNew=false}) {Text("Stay here")}})
}

@Composable private fun ReadingGarden(entry: JournalEntry,art: Map<String,ArtCell>,includeJson:Boolean,onJson:(Boolean)->Unit,busy:Boolean,
    onSave:(String,String,List<Int>)->Unit,onShare:()->Unit,onNew:()->Unit) {
    val reading=entry.reading
    var selected by rememberSaveable(entry.id) {mutableStateOf(0)}
    var mode by rememberSaveable(entry.id) {mutableStateOf("Notice")}
    var other by rememberSaveable(entry.id) {mutableStateOf(if(reading.cards.size>1) 1 else 0)}
    var notice by durableDraft("${entry.id}.notice.$selected")
    var relation by durableDraft("${entry.id}.relate.$selected.$other")
    var revisit by durableDraft("${entry.id}.revisit")
    var reference by rememberSaveable(entry.id) {mutableStateOf(false)}
    var quiet by rememberSaveable(entry.id) {mutableStateOf(false)}
    val drawn=reading.cards[selected]
    val cardWidth = (LocalConfiguration.current.screenHeightDp * .24f).dp.coerceIn(150.dp, 240.dp)
    Heading(reading.question.ifBlank {"An open inquiry"})
    if(!quiet) Text("${reading.date} · ${reading.spread} · committed",color=Muted,fontSize=14.sp)
    Box(Modifier.fillMaxWidth(),contentAlignment=Alignment.Center) {
        AstreriumCard(drawn.card,art.getValue(drawn.card.id),drawn.orientation=="reversed",Modifier.width(cardWidth))
    }
    Text("${drawn.card.name} · ${drawn.orientation}",color=Pearl,fontSize=16.sp,modifier=Modifier.fillMaxWidth(),textAlign=TextAlign.Center)
    WaveDivider()
    Row(Modifier.fillMaxWidth(),horizontalArrangement=Arrangement.SpaceBetween,verticalAlignment=Alignment.CenterVertically) {
        OutlinedButton(onClick={selected=(selected+reading.cards.size-1)%reading.cards.size},modifier=Modifier.sizeIn(minWidth=48.dp),contentPadding=PaddingValues(12.dp)) {Text("‹",fontSize=25.sp)}
        Text("${selected+1} / ${reading.cards.size}",color=Pearl)
        OutlinedButton(onClick={selected=(selected+1)%reading.cards.size},modifier=Modifier.sizeIn(minWidth=48.dp),contentPadding=PaddingValues(12.dp)) {Text("›",fontSize=25.sp)}
    }
    Choice("Position",drawn.positionLabel,reading.cards.mapIndexed {i,c->i.toString() to "${i+1}. ${c.positionLabel}"}) {selected=it.toInt()}
    if(!quiet) {
        DarkPanel {
            Text(drawn.positionPrompt,fontFamily=FontFamily.Serif,fontSize=21.sp,lineHeight=28.sp)
            Row(Modifier.fillMaxWidth(),horizontalArrangement=Arrangement.SpaceEvenly) {
                listOf("Notice","Relate","Revisit").forEach { name -> TextButton(onClick={mode=name}) {
                    Text(name,color=if(mode==name) Pearl else Muted,fontWeight=if(mode==name) FontWeight.Bold else FontWeight.Normal)
                }}
            }
            when(mode) {
                "Notice" -> {
                    Text("First Contact",fontFamily=FontFamily.Serif,fontSize=23.sp)
                    Text("What catches your attention?",color=Muted)
                    OutlinedTextField(notice,{notice=it},label={Text("First impression")},modifier=Modifier.fillMaxWidth(),minLines=3)
                    Button(onClick={onSave("notice",notice,listOf(drawn.position))},enabled=notice.isNotBlank()&&!busy&&notice!=entry.latest("notice"),modifier=Modifier.fillMaxWidth()) {Text("Keep this impression")}
                    TextButton(onClick={reference=!reference}) {Text(if(reference) "Close reference" else "Consult reference")}
                    if(reference) {Text(drawn.keywords.joinToString(" · "),color=Violet);Text("Reference terms from the bundled deck. Your first observation can remain distinct.",color=Muted,fontSize=14.sp)}
                }
                "Relate" -> {
                    Text("Bring two perspectives together",fontFamily=FontFamily.Serif,fontSize=23.sp)
                    Choice("Compare with",reading.cards[other].card.name,reading.cards.mapIndexed {i,c->i.toString() to "${i+1}. ${c.card.name}"}) {other=it.toInt()}
                    val second=reading.cards[other]
                    if(other==selected) Text("Choose a different position to explore a relationship.",color=Muted)
                    else {
                        Row(horizontalArrangement=Arrangement.spacedBy(12.dp)) {
                            AstreriumCard(drawn.card,art.getValue(drawn.card.id),drawn.orientation=="reversed",Modifier.weight(1f))
                            AstreriumCard(second.card,art.getValue(second.card.id),second.orientation=="reversed",Modifier.weight(1f))
                        }
                        Text("${drawn.positionLabel} ↔ ${second.positionLabel}",color=Violet)
                        Text("Where do they echo, resist, or complicate one another?",color=Muted)
                    }
                    OutlinedTextField(relation,{relation=it},label={Text("Your association")},modifier=Modifier.fillMaxWidth(),minLines=3)
                    Button(onClick={onSave("relate",relation,listOf(drawn.position,second.position))},enabled=other!=selected&&relation.isNotBlank()&&!busy&&relation!=entry.latest("relate"),modifier=Modifier.fillMaxWidth()) {Text("Keep this connection")}
                }
                "Revisit" -> {
                    Text("Return with new evidence",fontFamily=FontFamily.Serif,fontSize=23.sp)
                    Text("What happened? What changed in your understanding? What remains uncertain?",color=Muted)
                    OutlinedTextField(revisit,{revisit=it},label={Text("Later reflection")},modifier=Modifier.fillMaxWidth(),minLines=3)
                    Button(onClick={onSave("revisit",revisit,emptyList())},enabled=revisit.isNotBlank()&&!busy&&revisit!=entry.latest("revisit"),modifier=Modifier.fillMaxWidth()) {Text("Keep this reflection")}
                }
            }
            val notes=entry.notes.filter {it.kind==mode.lowercase()}
            if(notes.isNotEmpty()) {
                HorizontalDivider()
                Text("Kept ${mode.lowercase()} observations",color=Violet)
                notes.asReversed().forEach { note ->
                    Text(note.at.replace("T"," ").take(16)+" UTC"+(if(note.positions.isEmpty()) "" else " · Positions ${note.positions.joinToString() }"),fontSize=12.sp,color=Muted)
                    Text(note.text,color=Pearl)
                }
            }
        }
        DarkPanel {
            Row(verticalAlignment=Alignment.CenterVertically) {Text("Include JSON",Modifier.weight(1f));Switch(includeJson,onJson)}
            OutlinedButton(onClick=onShare,modifier=Modifier.fillMaxWidth()) {Text("Export reading")}
            Text("Saved locally. Sharing opens Android's destination chooser.",fontSize=14.sp,color=Muted)
            TextButton(onClick=onNew) {Text("Begin another inquiry")}
        }
    }
    TextButton(onClick={quiet=!quiet},modifier=Modifier.fillMaxWidth()) {Text(if(quiet) "Leave quiet view" else "Quiet view")}
}

/** Drafts survive navigation and process recreation, separate from committed journal notes. */
@Composable private fun durableDraft(key: String): MutableState<String> {
    val context = LocalContext.current
    val prefs = remember { context.getSharedPreferences("astrerium-drafts", 0) }
    val state = remember(key) { mutableStateOf(prefs.getString(key, "") ?: "") }
    return remember(key) {
        object : MutableState<String> {
            override var value: String
                get() = state.value
                set(value) { state.value = value; prefs.edit().putString(key, value).apply() }
            override fun component1() = value
            override fun component2(): (String) -> Unit = { value = it }
        }
    }
}

@Composable private fun DeckGarden(deck:List<Card>,art:Map<String,ArtCell>) {
    var filter by rememberSaveable {mutableStateOf("major")}
    var selected by rememberSaveable {mutableStateOf<String?>(null)}
    Heading("The collection")
    Text("78 perspectives · Astrerium edition",color=Muted)
    Choice("Collection",filter.replaceFirstChar {it.uppercase()},listOf("major","wands","cups","swords","pentacles").map {it to it.replaceFirstChar {c->c.uppercase()}}) {filter=it;selected=null}
    val cards=deck.filter {if(filter=="major") it.arcana=="major" else it.suit==filter}
    val focus=selected?.let {id->deck.first {it.id==id}}
    if(focus!=null) {
        Box(Modifier.fillMaxWidth(),contentAlignment=Alignment.Center) {AstreriumCard(focus,art.getValue(focus.id),false,Modifier.widthIn(max=320.dp).fillMaxWidth(.9f))}
        DarkPanel {Text(focus.name,fontFamily=FontFamily.Serif,fontSize=26.sp);Text("Upright · ${focus.uprightKeywords.joinToString(" · ")}");Text("Reversed · ${focus.reversedKeywords.joinToString(" · ")}",color=Muted)}
        TextButton(onClick={selected=null}) {Text("Back to collection")}
    } else cards.chunked(2).forEach {row->
        Row(horizontalArrangement=Arrangement.spacedBy(14.dp)) {
            row.forEach {card-> Column(Modifier.weight(1f).clickable {selected=card.id}) {
                AstreriumCard(card,art.getValue(card.id),false,Modifier.fillMaxWidth())
                Text(card.name,Modifier.fillMaxWidth().padding(vertical=8.dp),textAlign=TextAlign.Center,fontSize=15.sp)
            }}
            if(row.size==1) Spacer(Modifier.weight(1f))
        }
    }
}

@Composable private fun Heading(text:String) {Text(text,Modifier.fillMaxWidth(),fontFamily=FontFamily.Serif,fontSize=32.sp,lineHeight=38.sp,color=Pearl,textAlign=TextAlign.Center)}
@Composable private fun DarkPanel(content:@Composable ColumnScope.()->Unit) {
    Surface(color=Panel,shape=RoundedCornerShape(12.dp),border=BorderStroke(1.dp,Color(0xFF323044))) {
        Column(Modifier.fillMaxWidth().padding(18.dp),verticalArrangement=Arrangement.spacedBy(12.dp),content=content)
    }
}
@Composable private fun Choice(label:String,value:String,options:List<Pair<String,String>>,onSelect:(String)->Unit) {
    var expanded by remember {mutableStateOf(false)}
    Box(Modifier.fillMaxWidth()) {
        OutlinedButton(onClick={expanded=true},modifier=Modifier.fillMaxWidth().heightIn(min=56.dp),shape=RoundedCornerShape(8.dp)) {
            Column(Modifier.weight(1f)) {Text(label,color=Muted,fontSize=12.sp);Text(value,color=Pearl,fontSize=16.sp)}
            Text("⌄",fontSize=20.sp)
        }
        DropdownMenu(expanded,{expanded=false}) {options.forEach {(key,title)->DropdownMenuItem(text={Text(title)},onClick={onSelect(key);expanded=false})}}
    }
}
private fun formationPurpose(id:String):String=when(id) {
    "three-card"->"A compact encounter: current pattern, complication, next move."
    "the-constellation"->"A broad view of the forces and relationships around an inquiry."
    "the-fork"->"Explore a decision. Name Path A and Path B in your question or context before drawing."
    "the-aperture"->"Examine assumptions, missing information, and alternate frames."
    "the-crucible"->"Explore change while protecting what deserves to survive."
    "the-interface"->"Explore exchange and boundaries. Other minds remain working models, not known facts."
    "the-vector"->"Name a short time window. Explore a conditional trajectory, not a measured probability."
    else->"Choose a formation for your inquiry."
}
