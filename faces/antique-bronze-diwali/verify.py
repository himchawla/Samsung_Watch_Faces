#!/usr/bin/env python3
"""Face-specific preflight (ambient pixel budget); run by ../../verify_project.py."""
from pathlib import Path
from math import floor
import xml.etree.ElementTree as ET
from ambient_art import AMBIENT, STAT_REGION, read_rgb_png

root = Path(__file__).parent
manifest = ET.parse(root/'src/main/AndroidManifest.xml').getroot()
face = ET.parse(root/'src/main/res/raw/watchface.xml').getroot()
info = ET.parse(root/'src/main/res/xml/watch_face_info.xml').getroot()
assert face.tag == 'WatchFace'
assert face.find('Scene') is not None
assert face.find('.//DigitalClock/TimeText') is not None
text=(root/'src/main/res/raw/watchface.xml').read_text()
for src in ('BATTERY_PERCENT', 'HEART_RATE', 'STEP_COUNT','DAY_OF_WEEK_S','DAY','MONTH_S'):
    assert f'[{src}]' in text, src
for image in ('bronze_dial.png', 'preview.png'):
    assert (root/'src/main/res/drawable'/image).is_file()
assert AMBIENT.is_file()
assert manifest.find('application') is not None
assert info.find('Preview') is not None

# Count the full clock rectangle plus a margin, rather than the current digits.
# At each sampled display size count every output pixel whose bilinear sampling
# footprint touches a lit artwork pixel. Device rendering still needs validation.
scene = face.find('Scene')
assert scene.get('backgroundColor', '#ff000000').lower() in ('#000000', '#ff000000')
assert all(child.tag in ('PartImage', 'PartText', 'DigitalClock') for child in scene)
ambient_visible = []
for child in scene:
    variants = child.findall('Variant')
    assert len(variants) == 1
    variant = variants[0]
    assert variant.get('mode') == 'AMBIENT' and variant.get('target') == 'alpha'
    if int(variant.get('value')) > 0:
        ambient_visible.append(child)
assert [child.tag for child in ambient_visible] == ['PartImage', 'DigitalClock']
image, clock = ambient_visible
assert image.get('alpha') == '0' and clock.get('alpha') == '0'
assert all(child.find('Variant').get('value') == '255' for child in ambient_visible)
assert image.find('Image').get('resource') == 'bronze_dial_ambient'
assert [child.tag for child in image] == ['Variant', 'Image']
assert (int(face.get('width')), int(face.get('height'))) == (450, 450)
assert tuple(int(image.get(k)) for k in ('x', 'y', 'width', 'height')) == (0, 0, 450, 450)
assert all(k not in image.attrib and k not in clock.attrib
           for k in ('scaleX', 'scaleY', 'angle', 'renderMode'))
assert len(clock.findall('TimeText')) == 1
time = clock.find('TimeText')
assert tuple(int(time.get(k)) for k in ('x', 'y', 'width', 'height')) == (
    0, 0, int(clock.get('width')), int(clock.get('height'))
)
assert len(time) == 1 and time[0].tag == 'Font' and len(time[0]) == 0

width, height, rows = read_rgb_png(AMBIENT)
assert (width, height) == (450, 450)
lit = {(x, y) for y, row in enumerate(rows) for x in range(width)
       if any(row[x*3:x*3+3])}
assert lit, 'Ambient artwork is completely black'
left, top, right, bottom = STAT_REGION
assert not any(left <= x < right and top <= y < bottom for x, y in lit), \
    'Ambient artwork contains pixels in the hidden stat region'
clock_x, clock_y, clock_w, clock_h = (int(clock.get(k)) for k in ('x', 'y', 'width', 'height'))


def estimated_coverage(size, include_clock):
    total = illuminated = 0
    for y in range(size):
        fy = (y + 0.5) * height / size - 0.5
        iy = floor(fy)
        for x in range(size):
            if (2*x + 1 - size)**2 + (2*y + 1 - size)**2 > size**2:
                continue
            total += 1
            fx = (x + 0.5) * width / size - 0.5
            ix = floor(fx)
            in_clock = (clock_x-3 <= fx < clock_x+clock_w+3
                        and clock_y-3 <= fy < clock_y+clock_h+3)
            artwork = any((ix+dx, iy+dy) in lit for dx in (0, 1) for dy in (0, 1))
            illuminated += (include_clock and in_clock) or artwork
    return illuminated / total

sizes = (396, 450, 480, 498, 600)
art_estimates = {size: estimated_coverage(size, False) for size in sizes}
upper_estimates = {size: estimated_coverage(size, True) for size in sizes}
assert max(art_estimates.values()) <= 0.15, 'Ambient artwork alone exceeds the pixel budget'
print('PASS: XML well-formed, data sources present, required resources present.')
print(f'Ambient artwork estimate at 498px: {art_estimates[498]:.2%}.')
print(f'Upper bound with the entire clock rectangle: {upper_estimates[498]:.2%}.')
if max(upper_estimates.values()) > 0.15:
    print('NOTE: This upper bound exceeds 15%; measure the rendered clock on-device.')
print('NEXT: Android Studio WFF schema check and APK build are still required.')
