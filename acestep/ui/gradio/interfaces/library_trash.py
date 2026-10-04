"""Recoverable library trash with persistent source identities and no permanent deletion."""

import json
from pathlib import Path
import shutil
import uuid

from .library_store import AUDIO_SUFFIXES, resolve_song
from .library_stems import _JOB_LOCK, STEM_PROFILES, stem_cache_key


def trash_root(root: Path) -> Path:
    """Keep trash storage inside the library, including when links are present."""
    directory = (root / ".trash").resolve()
    if not directory.is_relative_to(root.resolve()):
        raise ValueError("Trash must be inside the library.")
    return directory


def move_to_trash(root: Path, relative: str, title: str) -> str:
    """Move audio into recoverable storage and preserve a metadata snapshot."""
    root = root.resolve()
    if not _JOB_LOCK.acquire(blocking=False):
        raise ValueError("Stem separation is running. Try moving the track when it finishes.")
    try:
        source = resolve_song(root, relative)
        if any(part in (".trash", ".stems") for part in Path(relative).parts):
            raise ValueError("Select a song from the library.")
        token = uuid.uuid4().hex
        folder = trash_root(root) / token
        folder.mkdir(parents=True)
        assets = [(source, "audio", False)]
        shared = any(p != source and p.stem == source.stem and
                     p.suffix.lower() in AUDIO_SUFFIXES for p in source.parent.iterdir())
        for suffix, name in ((".json", "metadata.json"), (".session.npz", "session.npz"),
                             (".repaint_latents.npy", "repaint_latents.npy")):
            assets.append((source.with_suffix(suffix), name, shared))
        assets.append((source.with_name(source.name + ".cover.png"), "cover.png", False))
        for count in STEM_PROFILES:
            key = stem_cache_key(source, count)
            assets.append((root / ".stems" / key, f"stems-{count}", False))
        assets = [(p, name, copy) for p, name, copy in assets if p.exists()]
        for path, _, _ in assets:
            if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
                raise ValueError("Linked track files must stay inside the library.")
        manifest = {"original": relative, "filename": "audio", "title": title,
                    "assets": [{"original": str(p.relative_to(root.resolve())),
                                "stored": name, "shared": copy} for p, name, copy in assets]}
        (folder / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        moved = []
        try:
            for path, name, copy in assets:
                if copy:
                    shutil.copy2(path, folder / name)
                else:
                    path.rename(folder / name)
                    moved.append((path, folder / name))
        except OSError:
            for original, stored in reversed(moved):
                stored.rename(original)
            raise
        return token
    finally:
        _JOB_LOCK.release()


def trash_entries(root: Path) -> list[tuple[str, str]]:
    """List restorable entries across app restarts; ignore interrupted moves."""
    entries = []
    for folder in sorted(trash_root(root).glob("*"), reverse=True):
        try:
            manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
            if (folder / Path(manifest["filename"]).name).is_file():
                entries.append((manifest["title"], folder.name))
        except (OSError, ValueError, KeyError, TypeError):
            continue
    return entries


def restore_from_trash(root: Path, token: str) -> None:
    """Restore audio to its original location without replacing an existing song."""
    if not isinstance(token, str) or len(token) != 32 or any(c not in "0123456789abcdef" for c in token):
        raise ValueError("Choose a track from Trash.")
    folder = (trash_root(root) / token).resolve()
    if not folder.is_relative_to(trash_root(root)):
        raise ValueError("Invalid trash entry.")
    with _JOB_LOCK:
        manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
        if "assets" in manifest:
            pairs = []
            for asset in manifest["assets"]:
                destination = (root / asset["original"]).resolve()
                source = (folder / asset["stored"]).resolve()
                if not destination.is_relative_to(root.resolve()) or not source.is_relative_to(folder):
                    raise ValueError("Invalid linked track location.")
                if destination.exists():
                    if asset.get("shared"):
                        continue
                    raise ValueError("A linked track file already exists; nothing was replaced.")
                if not source.exists():
                    raise ValueError("A linked track file is missing from Trash.")
                pairs.append((source, destination))
            moved = []
            try:
                for source, destination in pairs:
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    source.rename(destination)
                    moved.append((source, destination))
            except OSError:
                for source, destination in reversed(moved):
                    destination.rename(source)
                raise
            return
        # Preserve compatibility with trash entries created before linked-file support.
        destination = (root / manifest["original"]).resolve()
        if not destination.is_relative_to(root.resolve()):
            raise ValueError("Invalid original track location.")
        source = folder / Path(manifest["filename"]).name
        if destination.exists():
            raise ValueError("A track already exists at the original location; nothing was replaced.")
        destination.parent.mkdir(parents=True, exist_ok=True)
        metadata = folder / "metadata.json"
        if metadata.is_file() and not destination.with_suffix(".json").exists():
            shutil.copy2(metadata, destination.with_suffix(".json"))
        source.rename(destination)
