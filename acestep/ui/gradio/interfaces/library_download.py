"""Build same-origin downloads for validated local library audio."""

from html import escape
from pathlib import Path
import re
from urllib.parse import quote

from .library_store import resolve_song


def download_link(root: Path, song: dict) -> str:
    """Link to the existing authenticated Gradio file route, preserving audio format."""
    path = resolve_song(root, song["path"])
    title = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", song.get("title") or path.stem)
    title = title.strip(" .")[:160] or "song"
    if title.upper().split(".")[0] in {"CON", "PRN", "AUX", "NUL", *(
            f"{prefix}{i}" for prefix in ("COM", "LPT") for i in range(1, 10))}:
        title = "song_" + title
    filename = escape(title + path.suffix, quote=True)
    url = "gradio_api/file=" + quote(path.as_posix(), safe="/")
    return f'<a class="song-download" href="{escape(url, quote=True)}" download="{filename}">Download</a>'
