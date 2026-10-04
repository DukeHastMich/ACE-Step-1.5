"""Read saved songs without changing their audio or generation sidecars."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

AUDIO_SUFFIXES = {".wav", ".mp3", ".flac", ".ogg", ".m4a"}


def read_metadata(path: Path) -> dict[str, Any]:
    """Read a bounded JSON sidecar, tolerating older or incomplete outputs."""
    sidecar = path.with_suffix(".json")
    try:
        if sidecar.stat().st_size > 2_000_000:
            return {}
        value = json.loads(sidecar.read_text(encoding="utf-8-sig"))
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError):
        return {}


def resolve_song(root: Path, relative: str) -> Path:
    """Resolve an existing library audio file, rejecting paths outside the library."""
    root = root.resolve()
    path = (root / relative).resolve()
    if not path.is_relative_to(root) or path.suffix.lower() not in AUDIO_SUFFIXES:
        raise ValueError("Invalid library song")
    if not path.is_file():
        raise ValueError("Song is no longer available")
    return path


def scan_songs(root: Path, query: str = "") -> list[dict[str, Any]]:
    """Find newest-first audio outputs, searchable by caption, lyrics, or filename."""
    root = root.resolve()
    if not root.is_dir():
        return []
    songs = []
    for candidate in root.rglob("*"):
        if any(part in (".stems", ".trash", ".personas") for part in candidate.relative_to(root).parts):
            continue
        if candidate.suffix.lower() not in AUDIO_SUFFIXES:
            continue
        try:
            path = resolve_song(root, str(candidate.relative_to(root)))
            stat = path.stat()
            if not stat.st_size:
                continue
        except (OSError, ValueError):
            continue
        meta = read_metadata(path)
        caption = str(meta.get("caption") or meta.get("global_caption") or "")
        lyrics = str(meta.get("lyrics") or "")
        title = str(meta.get("title") or caption or path.stem).replace("\n", " ")
        if query.casefold() not in f"{title} {caption} {lyrics} {path.name}".casefold():
            continue
        try:
            duration = max(0, int(float(meta.get("duration") or 0)))
            length = f"{duration // 60}:{duration % 60:02d}" if duration else "—"
        except (ValueError, TypeError, OverflowError):
            length = "—"
        songs.append({
            "path": str(path.relative_to(root)), "title": title[:200],
            "style": caption if meta.get("title") else "",
            "created": datetime.fromtimestamp(stat.st_mtime).strftime("%b %d · %H:%M"),
            "duration": length, "format": path.suffix[1:].upper(), "mtime": stat.st_mtime,
        })
    return sorted(songs, key=lambda song: (song["mtime"], song["path"]), reverse=True)


def song_rows(songs: list[dict[str, Any]]) -> list[list[str]]:
    """Return display-only rows in the same order as the selection state."""
    return [[song[key] for key in ("title", "created", "duration", "format")]
            for song in songs]
