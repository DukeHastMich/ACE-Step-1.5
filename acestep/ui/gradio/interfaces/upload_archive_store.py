"""Persistent content-addressed copies of uploaded and recorded audio."""
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import threading

from .library_store import AUDIO_SUFFIXES

UPLOAD_ROOT = Path(__file__).resolve().parents[4] / "uploads"
_LOCK = threading.Lock()


def archive_audio(source, root=UPLOAD_ROOT):
    """Copy an audio upload once and publish metadata after a complete copy."""
    if not source:
        return None
    source = Path(source)
    if not source.is_file() or source.suffix.lower() not in AUDIO_SUFFIXES:
        raise ValueError("Choose an audio file to archive.")
    digest = hashlib.sha256()
    with source.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    identity = digest.hexdigest()
    root = Path(root).resolve()
    destination = root / identity
    with _LOCK:
        if (destination / "upload.json").is_file():
            return load_upload(identity, root)
        root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="upload-", dir=root) as temporary:
            temporary = Path(temporary)
            filename = "audio" + source.suffix.lower()
            shutil.copy2(source, temporary / filename)
            (temporary / "upload.json").write_text(json.dumps({
                "name": source.name, "audio": filename}, ensure_ascii=False), encoding="utf-8")
            temporary.rename(destination)
    return load_upload(identity, root)


def load_upload(identity, root=UPLOAD_ROOT):
    """Resolve only a validated archive identity and a contained audio path."""
    if not isinstance(identity, str) or len(identity) != 64 or any(c not in "0123456789abcdef" for c in identity):
        raise ValueError("Select an archived upload.")
    root = Path(root).resolve()
    folder = (root / identity).resolve()
    if not folder.is_relative_to(root):
        raise ValueError("Invalid upload location.")
    meta = json.loads((folder / "upload.json").read_text(encoding="utf-8"))
    audio = (folder / meta["audio"]).resolve()
    if not audio.is_relative_to(folder) or not audio.is_file():
        raise ValueError("Archived audio is missing.")
    return {"id": identity, "name": str(meta["name"]), "path": str(audio)}


def list_uploads(root=UPLOAD_ROOT):
    """List published uploads, newest first; ignore interrupted copies."""
    entries = []
    for folder in Path(root).glob("*"):
        try:
            item = load_upload(folder.name, root)
            entries.append((folder.stat().st_mtime_ns, item))
        except (OSError, ValueError, KeyError, TypeError):
            continue
    return [item for _, item in sorted(entries, key=lambda pair: pair[0], reverse=True)]
