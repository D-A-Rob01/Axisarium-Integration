package com.aletheion.cartomancy

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.core.splashscreen.SplashScreen.Companion.installSplashScreen
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        installSplashScreen()
        super.onCreate(savedInstanceState)
        setContent {
            CartomancyTheme {
                Surface(color = MaterialTheme.colorScheme.background) {
                    CartomancyApp()
                }
            }
        }
    }
}

@Composable
private fun CartomancyTheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = darkColorScheme(
            primary = Color(0xFF9A7CFF),
            onPrimary = Color(0xFF0B0815),
            secondary = Color(0xFF58E8F6),
            tertiary = Color(0xFFFFC857),
            background = Color(0xFF080B14),
            onBackground = Color(0xFFF4F0FF),
            surface = Color(0xFF131827),
            onSurface = Color(0xFFF4F0FF),
            surfaceVariant = Color(0xFF20273A),
            onSurfaceVariant = Color(0xFFC7C3D7),
            outline = Color(0xFF777189),
            outlineVariant = Color(0xFF34394B),
        ),
        content = content,
    )
}
