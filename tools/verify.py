#!/usr/bin/env python3
"""Preflight every face in faces/: structure, metadata and XML, then each face's own verify.py.

This is not a substitute for the WFF schema validation the Android build performs.
"""
from pathlib import Path
import json
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tools.faces import FACE_ID, FACES_DIR, PACKAGE, ROOT  # noqa: E402

ANDROID = "{http://schemas.android.com/apk/res/android}"


def check_face(directory):
    errors = []
    meta_path = directory / "face.json"
    if not FACE_ID.match(directory.name):
        errors.append("folder name must be lowercase-kebab-case (it becomes the module and APK name)")
    try:
        meta = json.loads(meta_path.read_text())
    except (OSError, ValueError) as exc:
        return [f"face.json: {exc}"], None
    for key in ("name", "package"):
        if not isinstance(meta.get(key), str) or not meta[key].strip():
            errors.append(f"face.json: missing '{key}'")
    package = meta.get("package", "")
    if package and not PACKAGE.match(package):
        errors.append(f"face.json: invalid package '{package}'")

    gradle = directory / "build.gradle.kts"
    if not gradle.is_file():
        errors.append("missing build.gradle.kts")
    else:
        app_id = re.search(r'applicationId\s*=\s*"([^"]+)"', gradle.read_text())
        if not app_id or app_id.group(1) != package:
            errors.append(f"build.gradle.kts applicationId must equal face.json package '{package}'")

    main = directory / "src/main"
    res = main / "res"
    try:
        app = ET.parse(main / "AndroidManifest.xml").getroot().find("application")
        if app is None or app.get(f"{ANDROID}hasCode") != "false":
            errors.append('AndroidManifest.xml: <application android:hasCode="false"> required')
        elif not any(p.get(f"{ANDROID}name") == "com.google.wear.watchface.format.version"
                     for p in app.findall("property")):
            errors.append("AndroidManifest.xml: missing WFF version <property>")
    except (OSError, ET.ParseError) as exc:
        errors.append(f"AndroidManifest.xml: {exc}")

    try:
        face = ET.parse(res / "raw/watchface.xml").getroot()
        if face.tag != "WatchFace" or face.find("Scene") is None:
            errors.append("watchface.xml: root must be <WatchFace> containing <Scene>")
        drawables = {p.stem for p in res.glob("drawable*/*")}
        for name in sorted({e.get("resource") for e in face.iter() if e.get("resource")}):
            if name not in drawables:
                errors.append(f"watchface.xml: resource '{name}' not found in res/drawable*/")
    except (OSError, ET.ParseError) as exc:
        errors.append(f"watchface.xml: {exc}")

    try:
        preview = ET.parse(res / "xml/watch_face_info.xml").getroot().find("Preview")
        if preview is None or preview.get("value") != "@drawable/preview":
            errors.append('watch_face_info.xml: <Preview value="@drawable/preview"> required')
    except (OSError, ET.ParseError) as exc:
        errors.append(f"watch_face_info.xml: {exc}")
    if not (res / "drawable/preview.png").is_file():
        errors.append("missing res/drawable/preview.png (shown in the watch picker and the installer)")

    custom = directory / "verify.py"
    if custom.is_file():
        result = subprocess.run([sys.executable, str(custom)], cwd=directory,
                                capture_output=True, text=True)
        output = (result.stdout + result.stderr).strip()
        if result.returncode:
            errors.append(f"verify.py failed:\n{output}")
        elif output:
            print("\n".join(f"    {line}" for line in output.splitlines()))
    return errors, package


def main():
    dirs = sorted(d for d in FACES_DIR.iterdir() if d.is_dir()) if FACES_DIR.is_dir() else []
    if not dirs:
        sys.exit(f"No faces found in {FACES_DIR.relative_to(ROOT)}/")
    failed, packages = False, {}
    for directory in dirs:
        print(f"{directory.name}:")
        errors, package = check_face(directory)
        if package in packages:
            errors.append(f"package '{package}' is already used by {packages[package]}")
        elif package:
            packages[package] = directory.name
        for error in errors:
            print(f"  FAIL {error}")
        print("  ok" if not errors else "")
        failed |= bool(errors)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
