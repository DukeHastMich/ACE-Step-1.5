"""Persist artist notes in the audio track's existing metadata sidecar."""
import json
import os
from pathlib import Path
import tempfile

from .library_store import resolve_song


def save_artist_notes(root: Path, relative: str, notes: str, distribution: dict | None = None) -> None:
    """Atomically update notes while preserving all existing generation metadata."""
    if not isinstance(notes, str) or len(notes) > 50000:
        raise ValueError("Artist notes must be text under 50,000 characters.")
    if distribution is not None:
        if not isinstance(distribution, dict) or not isinstance(distribution.get("enabled"), bool):
            raise ValueError("Invalid distribution settings.")
        if not isinstance(distribution.get("isrc"), str) or len(distribution["isrc"]) > 32:
            raise ValueError("ISRC code must be text under 32 characters.")
        if not isinstance(distribution.get("notes"), str) or len(distribution["notes"]) > 50000:
            raise ValueError("Distribution notes must be text under 50,000 characters.")
    song = resolve_song(root, relative)
    sidecar = song.with_suffix(".json")
    if sidecar.is_symlink() or not sidecar.resolve().is_relative_to(root.resolve()):
        raise ValueError("Track metadata must stay inside the library.")
    metadata = {}
    if sidecar.exists():
        if sidecar.stat().st_size > 2_000_000:
            raise ValueError("Track metadata is too large to edit safely.")
        metadata = json.loads(sidecar.read_text(encoding="utf-8-sig"))
        if not isinstance(metadata, dict):
            raise ValueError("Track metadata is not a valid object.")
    metadata["artist_notes"] = notes
    if distribution is not None:
        metadata["distribution"] = {key: distribution[key] for key in ("enabled", "isrc", "notes")}
    descriptor, temporary = tempfile.mkstemp(prefix=".notes-", suffix=".tmp", dir=sidecar.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(metadata, handle, indent=2, ensure_ascii=False)
        os.replace(temporary, sidecar)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
