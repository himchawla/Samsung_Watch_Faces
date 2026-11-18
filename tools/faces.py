"""Discover the watch faces in faces/<id>/ and locate their APKs. Standard library only."""
from dataclasses import dataclass
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parent.parent
FACES_DIR = ROOT / "faces"
DIST_DIR = ROOT / "dist"
FACE_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
PACKAGE = re.compile(r"^[a-zA-Z][\w]*(?:\.[a-zA-Z][\w]*)+$")


@dataclass(frozen=True)
class Face:
    id: str
    dir: Path
    name: str
    description: str
    package: str

    @classmethod
    def load(cls, directory):
        meta = json.loads((directory / "face.json").read_text())
        return cls(id=directory.name, dir=directory, name=meta["name"],
                   description=meta.get("description", ""), package=meta["package"])

    @property
    def preview(self):
        return self.dir / "src/main/res/drawable/preview.png"

    def apk_candidates(self):
        """dist/<id>.apk (downloaded from CI) plus any local Gradle/Android Studio outputs."""
        found = [(DIST_DIR / f"{self.id}.apk", "downloaded")]
        found += [(p, "local build") for p in sorted(self.dir.glob("build/outputs/apk/*/*.apk"))]
        return [(path, source) for path, source in found if path.is_file()]

    def apk(self):
        """The newest available APK as (path, source), or None."""
        candidates = self.apk_candidates()
        return max(candidates, key=lambda c: c[0].stat().st_mtime) if candidates else None


def load_faces():
    if not FACES_DIR.is_dir():
        return []
    return [Face.load(d) for d in sorted(FACES_DIR.iterdir()) if (d / "face.json").is_file()]
