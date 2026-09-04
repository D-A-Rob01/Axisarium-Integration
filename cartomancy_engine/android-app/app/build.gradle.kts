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
        versionCode = 6
        versionName = "0.3.3"

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
    val releaseSigningValues = mapOf(
        "KYBERNION_STORE_FILE" to releaseStoreFile,
        "KYBERNION_STORE_PASSWORD" to releaseStorePassword,
        "KYBERNION_KEY_ALIAS" to releaseKeyAlias,
        "KYBERNION_KEY_PASSWORD" to releaseKeyPassword,
    )
    val configuredSigningValues = releaseSigningValues.filterValues { !it.isNullOrBlank() }
    val signingRequired = signingValue("KYBERNION_REQUIRE_SIGNING")
        ?.toBooleanStrictOrNull() == true
    if (configuredSigningValues.isNotEmpty() && configuredSigningValues.size != releaseSigningValues.size) {
        val missing = releaseSigningValues.keys - configuredSigningValues.keys
        throw GradleException("Incomplete Kybernion release signing configuration; missing: ${missing.joinToString()}")
    }
    if (signingRequired && configuredSigningValues.size != releaseSigningValues.size) {
        throw GradleException("Kybernion release signing is required, but complete credentials were not supplied")
    }
    if (configuredSigningValues.size == releaseSigningValues.size) {
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

val verifyStartupContracts by tasks.registering {
    group = "verification"
    description = "Verifies every Kybernion contract required at application startup."
    doLast {
        val contracts = listOf(
            "three-card" to 3,
            "the-constellation" to 7,
        )
        val spreadsRoot = engineRoot.resolve("src/cartomancy_engine/data/spreads")
        contracts.forEach { (id, expectedPositionCount) ->
            val contract = spreadsRoot.resolve("$id.json")
            require(contract.isFile) { "Missing startup spread contract: $contract" }
            val content = contract.readText()
            require(Regex("\\\"id\\\"\\s*:\\s*\\\"$id\\\"").containsMatchIn(content)) {
                "Startup spread contract has the wrong id: $contract"
            }
            val positions = Regex("\\\"index\\\"\\s*:").findAll(content).count()
            require(positions == expectedPositionCount) {
                "Expected $expectedPositionCount positions in $contract; found $positions"
            }
        }
    }
}

val verifyDeckArtworkContract by tasks.registering {
    group = "verification"
    description = "Verifies the bundled deck and Kybernion v3 artwork index map the same 78 cards."
    doLast {
        val deckFile = engineRoot.resolve("src/cartomancy_engine/data/decks/rider-waite-smith.json")
        val artworkIndex = file("src/main/assets/tarot-v3/artwork-index.json")
        require(deckFile.isFile) { "Missing bundled Rider-Waite-Smith deck: $deckFile" }
        require(artworkIndex.isFile) { "Missing Kybernion artwork index: $artworkIndex" }

        val deckIds = Regex("\\\"id\\\"\\s*:\\s*\\\"([^\\\"]+)\\\"")
            .findAll(deckFile.readText())
            .map { it.groupValues[1] }
            .toList()
        require(deckIds.firstOrNull() == "rider-waite-smith") {
            "Bundled deck contract must identify rider-waite-smith"
        }
        val cardIds = deckIds.drop(1)
        val artworkIds = Regex("\\\"card_id\\\"\\s*:\\s*\\\"([^\\\"]+)\\\"")
            .findAll(artworkIndex.readText())
            .map { it.groupValues[1] }
            .toList()
        require(cardIds.size == 78 && cardIds.toSet().size == 78) {
            "Bundled deck must declare 78 unique cards; found ${cardIds.size}"
        }
        require(artworkIds.size == 78 && artworkIds.toSet().size == 78) {
            "Kybernion artwork index must declare 78 unique cards; found ${artworkIds.size}"
        }
        require(cardIds.toSet() == artworkIds.toSet()) {
            val missingArtwork = cardIds.toSet() - artworkIds.toSet()
            val missingDeckCards = artworkIds.toSet() - cardIds.toSet()
            "Bundled deck/artwork mismatch; missing artwork=$missingArtwork, missing deck cards=$missingDeckCards"
        }
    }
}

tasks.named("preBuild").configure {
    dependsOn(verifyTarotAssets)
    dependsOn(verifyStartupContracts)
    dependsOn(verifyDeckArtworkContract)
}
