# Samsung Watch Faces

A collection of Wear OS **Watch Face Format (WFF v1)** watch faces for the Galaxy Watch (built and tested against the Watch Ultra), plus a local web UI that installs them on your watch over Wi-Fi.

| Face | Folder |
| --- | --- |
| Antique Bronze Diwali | [`faces/antique-bronze-diwali`](faces/antique-bronze-diwali/README.md) |

## Install a face with the web UI

```sh
python3 installer/server.py
```

This opens `http://127.0.0.1:8765`. It needs Python 3.9+ and `adb` (`brew install android-platform-tools`), and nothing else.

1. **Connect the watch.** Turn on *Developer options → ADB debugging + Wireless debugging* on the watch. Pair once with the code from *Pair new device*, then connect with the IP:port on the Wireless debugging screen. The page walks you through it.
2. **Get the APK.** Click **Download latest** to fetch it from this repo's [`latest` release](https://github.com/himchawla/Samsung_Watch_Faces/releases/tag/latest), which CI publishes on every push to `main`. A local build is also picked up automatically, and the newest APK wins.
3. Click **Install**, then long-press the watch face on the watch and choose the new one.

Why a local server rather than a hosted page? Browsers can't open the raw TCP connection ADB needs, and the watch has no USB data port. The server only listens on localhost and rejects cross-site requests.

## Repo layout

```
faces/<face-id>/          one face = one Gradle module = one APK
  face.json               name, description, package (shown in the installer)
  build.gradle.kts        applicationId must equal face.json "package"
  src/main/res/raw/watchface.xml
  src/main/res/drawable/preview.png
  verify.py               optional face-specific checks
installer/                web UI (server.py + index.html, standard library only)
tools/verify.py           preflight for every face (also runs in CI)
tools/new_face.py         scaffold a new face
signing/debug.keystore    shared debug key, so CI and local builds can update each other
```

## Add a face

```sh
python3 tools/new_face.py midnight-blue "Midnight Blue" --description "Minimal blue dial"
# edit faces/midnight-blue/src/main/res/raw/watchface.xml and preview.png
python3 tools/verify.py
```

Gradle (`settings.gradle.kts`), CI and the installer discover `faces/*` automatically, so there is nothing to register. Give every face a unique package name. Changing the package of a published face makes it a different app on the watch.

## Build

- **CI (no local setup):** `.github/workflows/build-watchface.yml` runs `tools/verify.py`, builds every face, uploads a `watch-face-apks` artifact, and on `main` replaces the `latest` release with `<face-id>.apk` files.
- **Locally:** open the repo in Android Studio (SDK 35, JDK 17+, AGP 8.8.2), or run `gradle assembleDebug` with Gradle 8.10.2+ and `ANDROID_HOME` set. Build a single face with `gradle :<face-id>:assembleDebug`. APKs land in `faces/<face-id>/build/outputs/apk/debug/`.
- **Without the web UI:** `adb install -r dist/<face-id>.apk`.

### Signing

Every face is signed with `signing/debug.keystore` (password `android`). Its password is public by design, which is fine for personal sideloading. It also means CI and local builds share one signing key, so installing over an existing copy works. Faces installed before this keystore existed must be uninstalled once (the installer has an Uninstall button). Create a private release key before publishing to Google Play.

WFF schema validation happens during the Gradle build. `tools/verify.py` is only a quick preflight check.
