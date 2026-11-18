# Antique Bronze Diwali

A Wear OS Watch Face Format (WFF v1) face for the Galaxy Watch Ultra, with a rich antique-bronze Diwali background. Package: `com.antiquebronze.diwali`.

## What is live (NOT baked into the wallpaper)

- Clock: device-synced 12/24-hour time via `DigitalClock` / `TimeText`
- Date: day of week, day and month (`DAY_OF_WEEK_S`, `DAY`, `MONTH_S`)
- Battery **percentage**: `[BATTERY_PERCENT]` (not battery health)
- Heart rate (BPM): `[HEART_RATE]` (availability and update rate depend on the watch's sensing settings)
- Steps today: `[STEP_COUNT]`
- Always-on (ambient) display: a smaller clock over sparse, dimmed artwork; the stats and their circles are hidden

All live values are defined in `src/main/res/raw/watchface.xml`. The preview image uses illustrative numbers **only inside the static gallery preview**.

## Change the design

- Replace `src/main/res/drawable/bronze_dial.png` with your artwork (600x600 PNG; keep the filename).
- Regenerate the sparse ambient artwork with `python3 ambient_art.py` after changing the background. The generator expects an 8-bit RGB, non-interlaced PNG.
- Edit XML coordinates, fonts and colours in `src/main/res/raw/watchface.xml`.
- The picker/installer preview is `src/main/res/drawable/preview.png`. Source artwork lives in `artwork/`.
- Run `python3 tools/verify.py` from the repo root (it also runs this folder's `verify.py`).

## Validation note

`verify.py` estimates ambient illuminated pixels at several display sizes using a bilinear image-scaling footprint. It reports a conservative upper bound that counts the entire clock rectangle, not just the lit digits. Measure actual pixel coverage on a watch or emulator, because device rendering and clock text vary.

## Useful sources

- https://developer.android.com/training/wearables/wff
- https://developer.android.com/reference/wear-os/wff/common/attributes/source-type
- https://developer.android.com/reference/wear-os/wff/group/part/text/formatter/template
- https://developer.android.com/training/wearables/wff/time
