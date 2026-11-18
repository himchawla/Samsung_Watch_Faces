#!/usr/bin/env python3
"""Scaffold a new watch face: python3 tools/new_face.py <id> "Display Name" [--package com.x.y]

Creates faces/<id>/ with a minimal live digital clock + date (and a dim always-on variant)
that builds as its own APK. Gradle, CI and the installer pick it up automatically.
"""
from pathlib import Path
import argparse
import json
import struct
import sys
import zlib

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tools.faces import FACE_ID, FACES_DIR, PACKAGE, load_faces  # noqa: E402

BUILD_GRADLE = """plugins {{
    id("com.android.application")
}}

android {{
    namespace = "{package}"
    compileSdk = 35

    defaultConfig {{
        applicationId = "{package}"
        minSdk = 33
        targetSdk = 35
        versionCode = 1
        versionName = "1.0"
    }}
    signingConfigs {{
        // Shared repo keystore so CI and local builds can upgrade each other in place.
        getByName("debug") {{
            storeFile = rootProject.file("signing/debug.keystore")
            storePassword = "android"
            keyAlias = "androiddebugkey"
            keyPassword = "android"
        }}
    }}
    buildTypes {{
        release {{
            isMinifyEnabled = false
            isShrinkResources = false
            signingConfig = signingConfigs.getByName("debug")
        }}
    }}
}}
"""

MANIFEST = """<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">
    <uses-feature android:name="android.hardware.type.watch" android:required="true" />
    <application android:label="@string/watch_face_name" android:hasCode="false">
        <property android:name="com.google.wear.watchface.format.version" android:value="1" />
    </application>
</manifest>
"""

STRINGS = """<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="watch_face_name">{name}</string>
</resources>
"""

INFO = """<?xml version="1.0" encoding="utf-8"?>
<WatchFaceInfo>
    <Preview value="@drawable/preview" />
    <Category value="CATEGORY_EMPTY" />
    <MultipleInstancesAllowed value="true" />
    <Editable value="false" />
</WatchFaceInfo>
"""

WATCHFACE = """<?xml version="1.0" encoding="utf-8"?>
<!-- {name}: starter face. Reference: https://developer.android.com/training/wearables/wff -->
<WatchFace width="450" height="450">
    <Scene backgroundColor="#ff000000">
        <PartText x="85" y="120" width="280" height="35">
            <Variant mode="AMBIENT" target="alpha" value="0" />
            <Text align="CENTER">
                <Font family="SYNC_TO_DEVICE" size="22" color="#FFB0B0B0">
                    <Template><![CDATA[%s, %d %s]]>
                        <Parameter expression="[DAY_OF_WEEK_S]" />
                        <Parameter expression="[DAY]" />
                        <Parameter expression="[MONTH_S]" />
                    </Template>
                </Font>
            </Text>
        </PartText>

        <DigitalClock x="40" y="170" width="370" height="100">
            <Variant mode="AMBIENT" target="alpha" value="150" />
            <TimeText x="0" y="0" width="370" height="100" format="h:mm" hourFormat="SYNC_TO_DEVICE" align="CENTER">
                <Font family="SYNC_TO_DEVICE" size="90" weight="NORMAL" color="#FFFFFFFF" />
            </TimeText>
        </DigitalClock>
    </Scene>
</WatchFace>
"""


def placeholder_preview(path, size=450):
    """A dark dial with a grey ring; replace with a real screenshot of the face."""
    rows, centre = [], (size - 1) / 2
    for y in range(size):
        row = bytearray()
        for x in range(size):
            r = ((x - centre) ** 2 + (y - centre) ** 2) ** 0.5
            v = 0 if r > size / 2 else 90 if size / 2 - 8 < r else 18
            row += bytes((v, v, v))
        rows.append(b"\x00" + bytes(row))

    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))

    header = struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0)
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header)
                     + chunk(b"IDAT", zlib.compress(b"".join(rows), 9)) + chunk(b"IEND", b""))


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("id", help="lowercase-kebab-case folder/module name, e.g. midnight-blue")
    parser.add_argument("name", help='display name shown on the watch, e.g. "Midnight Blue"')
    parser.add_argument("--package", help="Android applicationId (default: com.watchfaces.<id>)")
    parser.add_argument("--description", default="", help="one line for the installer UI")
    args = parser.parse_args()

    if not FACE_ID.match(args.id):
        sys.exit("id must be lowercase-kebab-case, e.g. midnight-blue")
    package = args.package or "com.watchfaces." + args.id.replace("-", "_")
    if not PACKAGE.match(package):
        sys.exit(f"invalid package name: {package}")
    if package in {f.package for f in load_faces()}:
        sys.exit(f"package {package} is already used by another face")
    face = FACES_DIR / args.id
    if face.exists():
        sys.exit(f"{face} already exists")

    res = face / "src/main/res"
    for sub in ("drawable", "raw", "values", "xml"):
        (res / sub).mkdir(parents=True)
    (face / "face.json").write_text(json.dumps(
        {"name": args.name, "description": args.description, "package": package}, indent=2) + "\n")
    (face / "build.gradle.kts").write_text(BUILD_GRADLE.format(package=package))
    (face / "src/main/AndroidManifest.xml").write_text(MANIFEST)
    (res / "values/strings.xml").write_text(STRINGS.format(name=args.name))
    (res / "xml/watch_face_info.xml").write_text(INFO)
    (res / "raw/watchface.xml").write_text(WATCHFACE.format(name=args.name))
    placeholder_preview(res / "drawable/preview.png")
    print(f"Created {face.relative_to(FACES_DIR.parent)}/ (package {package}).")
    print("Edit src/main/res/raw/watchface.xml, then run: python3 tools/verify.py")


if __name__ == "__main__":
    main()
