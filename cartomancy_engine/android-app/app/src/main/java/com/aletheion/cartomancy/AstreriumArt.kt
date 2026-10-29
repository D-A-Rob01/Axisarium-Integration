package com.aletheion.cartomancy

import android.content.Context
import android.graphics.BitmapFactory
import android.util.LruCache
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.rotate
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.*
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.*
import coil.compose.AsyncImage
import androidx.compose.ui.layout.ContentScale
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import org.json.JSONObject
import kotlin.math.*
import java.security.MessageDigest

data class ArtCell(val file: String, val column: Int, val row: Int,
    val left: Float, val top: Float, val right: Float, val bottom: Float)
object AstreriumArt {
    private val decodeLock = Mutex()
    private val cache = object : LruCache<String, ImageBitmap>(24 * 1024 * 1024) {
        override fun sizeOf(key: String, value: ImageBitmap) = value.width * value.height * 4
    }
    fun loadIndex(context: Context, deck: List<Card>): Map<String, ArtCell> {
        val root = context.assets.open("astrerium/index.json").bufferedReader().use { JSONObject(it.readText()) }
        val entries = root.getJSONArray("cards")
        require(entries.length() == 78) { "Astrerium index must contain exactly 78 entries" }
        val result = (0 until entries.length()).associate { i ->
            val c = entries.getJSONObject(i)
            c.getString("id") to ArtCell(c.getString("file"), c.getInt("column"), c.getInt("row"),
                c.getDouble("left").toFloat(), c.getDouble("top").toFloat(),
                c.getDouble("right").toFloat(), c.getDouble("bottom").toFloat())
        }
        require(result.size == 78 && result.keys == deck.map { it.id }.toSet()) { "Astrerium requires all 78 card illustrations" }
        require(result.values.toSet().size == 78) { "Each card must have its own artwork cell" }
        require(result.values.all { it.left >= 0 && it.top >= 0 && it.right <= 1 && it.bottom <= 1 && it.right > it.left && it.bottom > it.top }) { "Invalid artwork bounds" }
        require(result.values.all { it.column in 0..2 && it.row in 0..2 && it.file.matches(Regex("[a-z0-9-]+\\.png")) }) { "Invalid artwork coordinates or filename" }
        val hashes = root.getJSONObject("files")
        result.values.map { it.file }.distinct().forEach { file ->
            val digest = MessageDigest.getInstance("SHA-256")
            context.assets.open("astrerium/$file").use { input ->
                val buffer = ByteArray(65536)
                while (true) {
                    val count = input.read(buffer)
                    if (count < 0) break
                    digest.update(buffer, 0, count)
                }
            }
            val actual = digest.digest().joinToString("") { "%02x".format(it) }
            require(actual == hashes.getString(file)) { "Astrerium checksum mismatch: $file" }
        }
        return result
    }
    suspend fun bitmap(context: Context, file: String): ImageBitmap = withContext(Dispatchers.IO) {
      decodeLock.withLock {
        cache.get(file) ?: context.assets.open("astrerium/$file").use {
            BitmapFactory.decodeStream(it, null, BitmapFactory.Options().apply { inSampleSize = 1 })
                .let { decoded -> requireNotNull(decoded) { "Artwork failed to decode: $file" }.asImageBitmap() }
        }.also { cache.put(file, it) }
      }
    }
}

@Composable fun AstreriumBackground() {
    AsyncImage(model = "file:///android_asset/astrerium/environment.png", contentDescription = null,
        contentScale = ContentScale.Crop, modifier = Modifier.fillMaxSize())
    Box(Modifier.fillMaxSize().background(Color(0xFF000B2B).copy(alpha = .52f)))
}

@Composable fun AstreriumCard(card: Card, cell: ArtCell, reversed: Boolean, modifier: Modifier = Modifier) {
    val context = LocalContext.current
    val bitmap by produceState<ImageBitmap?>(null, cell.file) { value = AstreriumArt.bitmap(context, cell.file) }
    val shape = RoundedCornerShape(14.dp)
    Box(modifier.aspectRatio(.6f).clip(shape).background(Color(0xFF000B2B))
        .border(1.dp, Brush.linearGradient(listOf(Color(0xFF8E00FF), Color(0xFF19C4FF), Color(0xFF00FFDA))), shape)
        .semantics { contentDescription = "${card.name}, ${if(reversed) "reversed" else "upright"}" }) {
        Canvas(Modifier.fillMaxSize().rotate(if(reversed) 180f else 0f)) {
            bitmap?.let { image ->
                val x = (image.width * cell.left).roundToInt()
                val y = (image.height * cell.top).roundToInt()
                val w = (image.width * cell.right).roundToInt() - x
                val h = (image.height * cell.bottom).roundToInt() - y
                drawImage(image, srcOffset = IntOffset(x, y), srcSize = IntSize(w,h),
                    dstSize = IntSize(size.width.toInt(), size.height.toInt()), filterQuality = FilterQuality.High)
            }
        }
        Box(Modifier.fillMaxSize().background(Brush.verticalGradient(listOf(Color.Transparent, Color.Transparent, Color(0xF0000B2B)))))
        ElementSeal(card.element, Modifier.align(Alignment.TopEnd).padding(13.dp).size(18.dp))
        Column(Modifier.align(Alignment.BottomCenter).fillMaxWidth().padding(12.dp), horizontalAlignment = Alignment.CenterHorizontally) {
            Text(if(card.arcana == "major") roman(card.number) else rankLabel(card.number), fontSize = 14.sp, color = Color(0xFFEADCC7))
            Spacer(Modifier.height(5.dp))
            Text(card.name, fontFamily = FontFamily.Serif, fontSize = 21.sp, textAlign = TextAlign.Center, lineHeight = 24.sp)
        }
    }
}

@Composable private fun ElementSeal(element: String?, modifier: Modifier) {
    Canvas(modifier) {
        val down = element == "water" || element == "earth"
        val p = Path().apply {
            moveTo(size.width*.12f, if(down) size.height*.15f else size.height*.85f)
            lineTo(size.width*.88f, if(down) size.height*.15f else size.height*.85f)
            lineTo(size.width*.5f, if(down) size.height*.85f else size.height*.15f)
            close()
        }
        drawPath(p, Color(0xFFADE8F0), style = Stroke(1.dp.toPx()))
        if(element == "earth" || element == "air") drawLine(Color(0xFFADE8F0), Offset(0f,size.height*.5f), Offset(size.width,size.height*.5f),1.dp.toPx())
    }
}

@Composable fun WaveDivider(modifier: Modifier = Modifier) {
    Canvas(modifier.fillMaxWidth().height(30.dp)) {
        repeat(2) { n ->
            val path = Path()
            for(i in 0..100) {
                val x = size.width*i/100f
                val y = size.height/2 + sin(i/100f*2*PI + n*PI).toFloat()*size.height*.25f
                if(i==0) path.moveTo(x,y) else path.lineTo(x,y)
            }
            drawPath(path, if(n==0) Color(0xFF19C4FF) else Color(0xFFB99DE9), style=Stroke(1.dp.toPx()))
        }
        drawCircle(Color(0xFFB5ECF4),2.dp.toPx(),Offset(size.width/2,size.height/2))
    }
}

internal fun roman(number: Int): String = listOf("0","I","II","III","IV","V","VI","VII","VIII","IX","X","XI","XII","XIII","XIV","XV","XVI","XVII","XVIII","XIX","XX","XXI").getOrElse(number) { number.toString() }
internal fun rankLabel(number: Int): String = when(number) {1->"ACE";11->"PAGE";12->"KNIGHT";13->"QUEEN";14->"KING";else->number.toString()}
