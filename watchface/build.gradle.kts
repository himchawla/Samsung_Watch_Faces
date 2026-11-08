plugins {
    id("com.android.application")
}

android {
    namespace = "com.antiquebronze.diwali"
    compileSdk = 35

    defaultConfig {
        applicationId = "com.antiquebronze.diwali"
        minSdk = 33
        targetSdk = 35
        versionCode = 1
        versionName = "1.0"
    }
    buildTypes {
        release {
            isMinifyEnabled = false
            isShrinkResources = false
            signingConfig = signingConfigs.getByName("debug")
        }
    }
}
