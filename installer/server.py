#!/usr/bin/env python3
"""Local web UI to install this repo's watch faces on a watch over Wi-Fi ADB.

    python3 installer/server.py            # opens http://127.0.0.1:8765

Standard library only. Needs `adb` (Android platform-tools). It binds to localhost only,
because browsers cannot reach a watch's ADB port directly; this process does it for them.
"""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
import webbrowser

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from tools.faces import DIST_DIR, load_faces  # noqa: E402

INDEX = Path(__file__).with_name("index.html")
HOST_PORT = re.compile(r"^(?:[A-Za-z0-9.-]+|\[[0-9A-Fa-f:.%]+\]):\d{1,5}$")
PAIR_CODE = re.compile(r"^\d{6}$")
REPO_SLUG = re.compile(r"^[\w.-]+/[\w.-]+$")
RELEASE_TAG = "latest"


def find_adb():
    candidates = [os.environ.get("ADB"), shutil.which("adb")]
    for var in ("ANDROID_HOME", "ANDROID_SDK_ROOT"):
        if os.environ.get(var):
            candidates.append(str(Path(os.environ[var]) / "platform-tools/adb"))
    candidates.append(str(Path.home() / "Library/Android/sdk/platform-tools/adb"))
    return next((c for c in candidates if c and Path(c).is_file()), None)


def detect_repo():
    """owner/repo of the GitHub `origin` remote, used for release downloads."""
    try:
        url = subprocess.run(["git", "-C", str(ROOT), "remote", "get-url", "origin"],
                             capture_output=True, text=True, timeout=5).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None
    match = re.search(r"github\.com[:/]([\w.-]+/[\w.-]+?)(?:\.git)?/?$", url)
    return match.group(1) if match else None


class Installer:
    def __init__(self, adb_path, repo):
        self.adb_path, self.repo = adb_path, repo

    def adb(self, *args, timeout=60):
        if not self.adb_path:
            return False, "adb not found. Install Android platform-tools or set $ADB."
        try:
            result = subprocess.run([self.adb_path, *args], capture_output=True, text=True,
                                    timeout=timeout, stdin=subprocess.DEVNULL)
        except subprocess.TimeoutExpired:
            return False, f"adb {args[0]} timed out after {timeout}s"
        output = (result.stdout + result.stderr).strip()
        # adb connect/pair exit 0 even on failure, so also inspect the text.
        failed = result.returncode != 0 or re.search(
            r"\b(failed|cannot|unable|error)\b", output, re.IGNORECASE)
        return not failed, output

    def devices(self):
        ok, output = self.adb("devices", "-l", timeout=15)
        if not ok:
            return []
        found = []
        for line in output.splitlines()[1:]:
            parts = line.split()
            if len(parts) >= 2 and not line.startswith("*"):
                info = dict(p.split(":", 1) for p in parts[2:] if ":" in p)
                found.append({"serial": parts[0], "state": parts[1],
                              "model": info.get("model", "").replace("_", " ")})
        return found

    def require_device(self, serial):
        if not any(d["serial"] == serial and d["state"] == "device" for d in self.devices()):
            raise ValueError("That watch is not connected (or not authorised). Refresh and retry.")

    def installed_packages(self, serial):
        self.require_device(serial)
        ok, output = self.adb("-s", serial, "shell", "pm", "list", "packages", timeout=30)
        if not ok:
            raise ValueError(output)
        return {line.removeprefix("package:").strip() for line in output.splitlines()}

    def state(self):
        faces = []
        for face in load_faces():
            apk = face.apk()
            faces.append({
                "id": face.id, "name": face.name, "description": face.description,
                "package": face.package,
                "apk": None if not apk else {
                    "source": apk[1], "path": str(apk[0].relative_to(ROOT)),
                    "size": apk[0].stat().st_size, "mtime": apk[0].stat().st_mtime},
            })
        return {"adb": self.adb_path, "repo": self.repo, "release": RELEASE_TAG,
                "devices": self.devices(), "faces": faces}

    def face(self, face_id):
        face = next((f for f in load_faces() if f.id == face_id), None)
        if face is None:
            raise ValueError(f"Unknown face: {face_id}")
        return face

    def download(self, face_id):
        face = self.face(face_id)
        if not self.repo:
            raise ValueError("No GitHub repo detected; start the server with --repo owner/name.")
        url = f"https://github.com/{self.repo}/releases/download/{RELEASE_TAG}/{face.id}.apk"
        DIST_DIR.mkdir(exist_ok=True)
        try:
            with urllib.request.urlopen(url, timeout=60) as response:
                data = response.read()
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                raise ValueError(f"{face.id}.apk is not in the '{RELEASE_TAG}' release yet. "
                                 "It is published when the CI workflow runs on main.") from exc
            raise ValueError(f"Download failed: HTTP {exc.code}") from exc
        except urllib.error.URLError as exc:
            raise ValueError(f"Download failed: {exc.reason}") from exc
        if not data.startswith(b"PK"):
            raise ValueError("Downloaded file is not an APK.")
        with tempfile.NamedTemporaryFile(dir=DIST_DIR, suffix=".part", delete=False) as tmp:
            tmp.write(data)
        os.replace(tmp.name, DIST_DIR / f"{face.id}.apk")
        return f"Downloaded {face.id}.apk ({len(data) / 1e6:.1f} MB) from {url}"

    def install(self, face_id, serial):
        face = self.face(face_id)
        apk = face.apk()
        if apk is None:
            raise ValueError(f"No APK for {face.name} yet. Download it or build it first.")
        self.require_device(serial)
        ok, output = self.adb("-s", serial, "install", "-r", str(apk[0]), timeout=300)
        if not ok and "INSTALL_FAILED_UPDATE_INCOMPATIBLE" in output:
            output += ("\n\nThe copy on the watch was signed with a different key. "
                       "Uninstall it first, then install again.")
        if ok:
            output += (f"\n\nInstalled {face.name} ({apk[1]}). On the watch, long-press the "
                       "current face, then pick it from the list (scroll to the end, or + Add).")
        return ok, output

    def uninstall(self, face_id, serial):
        face = self.face(face_id)
        self.require_device(serial)
        return self.adb("-s", serial, "uninstall", face.package, timeout=60)

    def pair(self, host, code):
        if not HOST_PORT.match(host) or not PAIR_CODE.match(code):
            raise ValueError("Use the IP:port and 6-digit code shown under 'Pair new device'.")
        return self.adb("pair", host, code, timeout=30)

    def connect(self, host):
        if not HOST_PORT.match(host):
            raise ValueError("Use the IP address & port shown on the Wireless debugging screen.")
        return self.adb("connect", host, timeout=20)

    def disconnect(self, serial):
        return self.adb("disconnect", serial, timeout=10)


class Handler(BaseHTTPRequestHandler):
    server_version = "WatchFaceInstaller/1"

    def log_message(self, fmt, *args):
        if not self.path.startswith("/api/state"):
            sys.stderr.write("%s\n" % (fmt % args))

    def send(self, status, body, content_type="application/json"):
        if not isinstance(body, bytes):
            body = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def trusted(self):
        """Block DNS-rebinding and cross-site requests from other web pages."""
        host = self.headers.get("Host", "")
        if host not in self.server.allowed_hosts:
            return False
        origin = self.headers.get("Origin")
        return origin is None or origin == f"http://{host}"

    def do_GET(self):
        if not self.trusted():
            return self.send(403, {"ok": False, "message": "Forbidden"})
        url = urlsplit(self.path)
        installer = self.server.installer
        try:
            if url.path == "/":
                return self.send(200, INDEX.read_bytes(), "text/html; charset=utf-8")
            if url.path == "/api/state":
                return self.send(200, installer.state())
            if url.path == "/api/installed":
                serial = parse_qs(url.query).get("serial", [""])[0]
                packages = installer.installed_packages(serial)
                return self.send(200, {"ok": True, "installed": [
                    f.id for f in load_faces() if f.package in packages]})
            match = re.fullmatch(r"/preview/([a-z0-9-]+)\.png", url.path)
            if match:
                preview = installer.face(match.group(1)).preview
                if preview.is_file():
                    return self.send(200, preview.read_bytes(), "image/png")
        except ValueError as exc:
            return self.send(400, {"ok": False, "message": str(exc)})
        self.send(404, {"ok": False, "message": "Not found"})

    def do_POST(self):
        if not self.trusted():
            return self.send(403, {"ok": False, "message": "Forbidden"})
        if self.headers.get("Content-Type", "").split(";")[0] != "application/json":
            return self.send(415, {"ok": False, "message": "Expected JSON"})
        length = int(self.headers.get("Content-Length") or 0)
        if length > 65536:
            return self.send(413, {"ok": False, "message": "Too large"})
        try:
            body = json.loads(self.rfile.read(length) or b"{}")
            ok, message = self.dispatch(urlsplit(self.path).path, body)
        except KeyError as exc:
            ok, message = False, f"Missing field: {exc.args[0]}"
        except (ValueError, TypeError) as exc:
            ok, message = False, str(exc)
        self.send(200, {"ok": ok, "message": message})

    def dispatch(self, path, body):
        installer = self.server.installer
        text = lambda key: str(body[key]).strip()  # noqa: E731
        if path == "/api/pair":
            return installer.pair(text("host"), text("code"))
        if path == "/api/connect":
            return installer.connect(text("host"))
        if path == "/api/disconnect":
            return installer.disconnect(text("serial"))
        if path == "/api/download":
            return True, installer.download(text("face"))
        if path == "/api/install":
            return installer.install(text("face"), text("serial"))
        if path == "/api/uninstall":
            return installer.uninstall(text("face"), text("serial"))
        raise ValueError(f"Unknown action {path}")


def main():
    parser = argparse.ArgumentParser(description="Watch face installer web UI")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--repo", default=detect_repo(),
                        help="GitHub owner/name whose 'latest' release holds the APKs")
    parser.add_argument("--no-open", action="store_true", help="don't open a browser")
    args = parser.parse_args()
    if args.repo and not REPO_SLUG.match(args.repo):
        parser.error("--repo must look like owner/name")

    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    server.installer = Installer(find_adb(), args.repo)
    server.allowed_hosts = {f"127.0.0.1:{args.port}", f"localhost:{args.port}"}
    url = f"http://127.0.0.1:{args.port}/"
    print(f"Watch face installer: {url}  (Ctrl+C to stop)")
    if not server.installer.adb_path:
        print("WARNING: adb not found; install Android platform-tools or set $ADB.")
    if not args.no_open:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
