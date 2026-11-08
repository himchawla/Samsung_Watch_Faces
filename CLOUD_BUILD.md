# Build the APK in GitHub Actions (no Android Studio required on your computer)

This repo includes `.github/workflows/build-watchface.yml`. It is an **untested cloud build workflow**, and does not produce an APK until executed successfully.

1. Create a new GitHub repository.
2. Upload **all contents of the `AntiqueBronzeDiwaliWatchFace` folder** to the repository root, including the hidden `.github` folder. The repository root should contain `settings.gradle.kts`, `watchface/`, and `.github/workflows/build-watchface.yml`. Do not upload just the ZIP file to the repository.
3. Open your repository's **Actions** tab and choose **Build Antique Bronze Watch Face APK**. Press **Run workflow**.
4. Wait for a successful run, then open it and download the **AntiqueBronzeDiwali-debug-APK** build artifact. Unzip the artifact to get the `.apk` file.
5. Sideload that APK onto the Galaxy Watch Ultra using ADB/Wear OS wireless debugging. Merely downloading it to your phone does not install it onto your watch.

This build must run on a GitHub-hosted Ubuntu runner with network access for Gradle and Android build dependencies. Neither this workflow nor the XML has been tested on a live Watch Ultra. If Gradle reports XML validation errors, use the Actions build log to correct the project.

Security: GitHub Actions debug APKs are intended for personal testing, not Google Play publication. For publishing, create and securely manage your own release keystore.
