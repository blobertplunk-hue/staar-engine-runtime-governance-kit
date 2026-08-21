plugins {
    id("com.android.application")
}

android {
    namespace = "com.metablooms.recorder"
    compileSdk = 37

    defaultConfig {
        applicationId = "com.metablooms.recorder"
        minSdk = 26
        targetSdk = 36
        versionCode = 1
        versionName = "0.1.0"
    }
}

dependencies {
    implementation(platform("androidx.compose:compose-bom:2026.08.00"))
    implementation("androidx.core:core:1.17.0")
}
