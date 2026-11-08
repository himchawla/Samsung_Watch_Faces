# Antique Bronze Diwali — Galaxy Watch Ultra

A real **Wear OS Watch Face Format (WFF v1)** Android Studio project for the Galaxy Watch Ultra, with a rich antique-bronze Diwali background.

## What is live (NOT baked into the wallpaper)

- Clock: device-synced 12/24-hour time via `DigitalClock` / `TimeText`
- Date: day of week, day and month (`DAY_OF_WEEK_S`, `DAY`, `MONTH_S`)
- Battery **percentage**: `[BATTERY_PERCENT]` (this is not battery degradation/health)
- Heart rate (BPM): `[HEART_RATE]` (availability/update rate depend on watch sensing settings)
- Steps today: `[STEP_COUNT]`
- Always-on (ambient) display: shows time on black, hides wallpaper and secondary stats

All live values are defined in `watchface/src/main/res/raw/watchface.xml`. The preview image uses illustrative numbers **only inside the static gallery preview**; the actual face renders live values.

## Build on a PC (Android Studio)

1. Extract this ZIP and open the folder `AntiqueBronzeDiwaliWatchFace` with Android Studio.
2. Allow Gradle sync and Android SDK 35 installation. The project uses Android Gradle Plugin **8.8.2** and JDK 17+.
3. If Android Studio asks for a Gradle distribution, choose Gradle **8.10.2** or compatible. This source archive does **not** contain a Gradle wrapper JAR.
4. Select the `watchface` module, then **Build > Build Bundle(s) / APK(s) > Build APK(s)**.
5. Find the APK at `watchface/build/outputs/apk/debug/watchface-debug.apk`.
6. Enable developer options and wireless debugging on the Galaxy Watch Ultra, connect it over ADB, then run `adb install -r path/to/watchface-debug.apk`. On the watch, select the face in the watch face picker; depending on tools, Android Studio's watch-face run configuration can deploy/select automatically.

Recommended: latest Android Studio with WFF-aware XML editor/validator support. See https://developer.android.com/training/wearables/wff/setup and https://developer.android.com/training/wearables/wff/build .

### Change the design

- Replace `watchface/src/main/res/drawable/bronze_dial.png` with your artwork (600x600 PNG; retain the filename).
- Edit XML coordinates, fonts, and colors in `watchface.xml`.
- Static sample preview is `watchface/src/main/res/drawable/preview.png`.

### Validation note

The XML is syntactically parsed and checked for required files by `verify_project.py`. **I could not compile or test an APK in this environment** because the Android SDK, Gradle and an attached Wear OS watch aren't present. Final WFF schema and device render validation still need Android Studio / a watch.

### Useful sources

- https://developer.android.com/training/wearables/wff
- https://developer.android.com/reference/wear-os/wff/common/attributes/source-type
- https://developer.android.com/reference/wear-os/wff/group/part/text/formatter/template
- https://developer.android.com/training/wearables/wff/time
