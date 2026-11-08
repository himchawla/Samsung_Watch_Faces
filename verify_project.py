#!/usr/bin/env python3
"""Lightweight preflight; not a substitute for Android SDK/WFF schema validation."""
from pathlib import Path
import xml.etree.ElementTree as ET
root = Path(__file__).parent
manifest = ET.parse(root/'watchface/src/main/AndroidManifest.xml').getroot()
face = ET.parse(root/'watchface/src/main/res/raw/watchface.xml').getroot()
info = ET.parse(root/'watchface/src/main/res/xml/watch_face_info.xml').getroot()
assert face.tag == 'WatchFace'
assert face.find('Scene') is not None
assert face.find('.//DigitalClock/TimeText') is not None
text=(root/'watchface/src/main/res/raw/watchface.xml').read_text()
for src in ('BATTERY_PERCENT', 'HEART_RATE', 'STEP_COUNT','DAY_OF_WEEK_S','DAY','MONTH_S'):
    assert f'[{src}]' in text, src
for image in ('bronze_dial.png','preview.png'):
    assert (root/'watchface/src/main/res/drawable'/image).is_file()
assert manifest.find('application') is not None
assert info.find('Preview') is not None
print('PASS: XML well-formed, data sources present, required resources present.')
print('NEXT: Android Studio WFF schema check and APK build are still required.')
