import java.security.MessageDigest
import java.util.Properties

plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("kotlin-parcelize")
}

val engineRoot = rootProject.projectDir.parentFile
val signingProperties = Properties().apply {
    val localProperties = rootProject.file("keystore.properties")
    if (localProperties.isFile) {
        localProperties.inputStream().use(::load)
    }
}
fun signingValue(name: String): String? =
    providers.environmentVariable(name).orNull ?: signingProperties.getProperty(name)

android {
    namespace = "com.aletheion.cartomancy"
    compileSdk = 35

    defaultConfig {
        applicationId = "com.aletheion.cartomancy"
        minSdk = 26
        targetSdk = 35
        versionCode = 3
        versionName = "0.3.0"

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
        vectorDrawables.useSupportLibrary = true
    }

    buildTypes {
        release {
            isMinifyEnabled = true
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro",
            )
        }
    }

    val releaseStoreFile = signingValue("KYBERNION_STORE_FILE")
    val releaseStorePassword = signingValue("KYBERNION_STORE_PASSWORD")
    val releaseKeyAlias = signingValue("KYBERNION_KEY_ALIAS")
    val releaseKeyPassword = signingValue("KYBERNION_KEY_PASSWORD")
    if (listOf(releaseStoreFile, releaseStorePassword, releaseKeyAlias, releaseKeyPassword).all { !it.isNullOrBlank() }) {
        signingConfigs {
            create("kybernionRelease") {
                storeFile = rootProject.file(requireNotNull(releaseStoreFile))
                storePassword = requireNotNull(releaseStorePassword)
                keyAlias = requireNotNull(releaseKeyAlias)
                keyPassword = requireNotNull(releaseKeyPassword)
            }
        }
        buildTypes.named("release").configure {
            signingConfig = signingConfigs.getByName("kybernionRelease")
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = "17"
    }

    buildFeatures {
        compose = true
        buildConfig = true
    }

    composeOptions {
        kotlinCompilerExtensionVersion = "1.5.14"
    }

    sourceSets.getByName("main").assets.srcDirs(
        "src/main/assets",
        engineRoot.resolve("src/cartomancy_engine/data"),
    )

    packaging.resources.excludes += "/META-INF/{AL2.0,LGPL2.1}"
}

dependencies {
    val composeBom = platform("androidx.compose:compose-bom:2024.06.00")
    implementation(composeBom)
    androidTestImplementation(composeBom)

    implementation("androidx.core:core-ktx:1.13.1")
    implementation("androidx.activity:activity-compose:1.9.1")
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.ui:ui-tooling-preview")
    implementation("androidx.compose.material3:material3")
    implementation("androidx.compose.material:material-icons-extended")
    implementation("androidx.core:core-splashscreen:1.0.1")
    implementation("androidx.lifecycle:lifecycle-runtime-ktx:2.8.3")
    implementation("androidx.lifecycle:lifecycle-viewmodel-compose:2.8.3")
    implementation("io.coil-kt:coil-compose:2.7.0")
    implementation("io.coil-kt:coil-svg:2.7.0")

    testImplementation("junit:junit:4.13.2")
    androidTestImplementation("androidx.test.ext:junit:1.2.1")
    androidTestImplementation("androidx.test.espresso:espresso-core:3.6.1")
    androidTestImplementation("androidx.compose.ui:ui-test-junit4")
    debugImplementation("androidx.compose.ui:ui-tooling")
    debugImplementation("androidx.compose.ui:ui-test-manifest")
}

val verifyTarotAssets by tasks.registering {
    group = "verification"
    description = "Verifies the complete Kybernion v3 Android artwork bundle."
    doLast {
        val assetRoot = file("src/main/assets")
        val indexFile = assetRoot.resolve("tarot-v3/artwork-index.json")
        require(indexFile.isFile) { "Missing Kybernion artwork index: $indexFile" }
        val entryPattern = Regex(
            "\\\"card_id\\\"\\s*:\\s*\\\"([^\\\"]+)\\\".*?" +
                "\\\"asset_path\\\"\\s*:\\s*\\\"([^\\\"]+)\\\".*?" +
                "\\\"sha256\\\"\\s*:\\s*\\\"([0-9a-f]{64})\\\"",
            setOf(RegexOption.DOT_MATCHES_ALL),
        )
        val entries = entryPattern.findAll(indexFile.readText()).map { match ->
            Triple(match.groupValues[1], match.groupValues[2], match.groupValues[3])
        }.toList()
        require(entries.size == 78) { "Expected 78 indexed Kybernion cards; found ${entries.size}" }
        require(entries.map { it.first }.toSet().size == 78) { "Artwork index contains duplicate card IDs" }
        require(entries.map { it.second }.toSet().size == 78) { "Artwork index contains duplicate asset paths" }
        entries.forEach { (_, relativePath, expectedHash) ->
            val artwork = assetRoot.resolve(relativePath)
            require(artwork.isFile) { "Missing Kybernion artwork: $relativePath" }
            val digest = MessageDigest.getInstance("SHA-256")
                .digest(artwork.readBytes())
                .joinToString("") { "%02x".format(it) }
            require(digest == expectedHash) { "Checksum mismatch for $relativePath" }
        }
    }
}

tasks.named("preBuild").configure { dependsOn(verifyTarotAssets) }
