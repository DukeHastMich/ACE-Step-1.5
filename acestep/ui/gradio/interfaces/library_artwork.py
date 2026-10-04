"""Validate and persist original PNG artwork beside each saved library track."""

import os
from pathlib import Path
import shutil
import tempfile

from PIL import Image

from .library_store import resolve_song


def artwork_path(root: Path, relative: str) -> Path:
    """Derive a track-specific artwork path within the library."""
    song = resolve_song(root, relative)
    path = song.with_name(song.name + ".cover.png")
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError("Artwork must be stored inside the library.")
    return path


def existing_artwork(root: Path, relative: str) -> str | None:
    """Return saved artwork for an existing song, tolerating missing cover files."""
    path = artwork_path(root, relative)
    return str(path) if path.is_file() else None


def save_artwork(root: Path, relative: str, upload: str) -> str:
    """Validate a PNG and atomically save its original bytes without altering metadata."""
    if not upload:
        raise ValueError("Drop a PNG image first.")
    source = Path(upload)
    if source.suffix.lower() != ".png" or source.stat().st_size > 25 * 1024 * 1024:
        raise ValueError("Choose a PNG image smaller than 25 MB.")
    try:
        with Image.open(source) as image:
            if image.format != "PNG" or image.width * image.height > 40_000_000:
                raise ValueError("Choose a PNG image no larger than 40 megapixels.")
            image.verify()
    except (OSError, SyntaxError, Image.DecompressionBombError) as exc:
        raise ValueError("This file is not a valid PNG image.") from exc
    destination = artwork_path(root, relative)
    descriptor, temporary = tempfile.mkstemp(prefix=".cover-", suffix=".tmp", dir=destination.parent)
    os.close(descriptor)
    try:
        shutil.copyfile(source, temporary)
        os.replace(temporary, destination)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return str(destination)
