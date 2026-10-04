"""Compact persistent library player backed by the authenticated audio file route."""
from html import escape
from pathlib import Path
from urllib.parse import quote
import uuid

from .library_artwork import existing_artwork
from .library_store import read_metadata, resolve_song

PLAYER_SCRIPT = Path(__file__).with_suffix(".js").read_text(encoding="utf-8")
PLAYER_CSS = Path(__file__).with_suffix(".css").read_text(encoding="utf-8")


def player_payload(root: Path, relative: str, autoplay: bool = False) -> str:
    """Build escaped track data; only validated library paths may reach playback."""
    path = resolve_song(root, relative)
    meta = read_metadata(path)
    art = existing_artwork(root, relative)
    def url(file):
        """Use a relative Gradio route so reverse-proxy prefixes remain supported."""
        return "gradio_api/file=" + quote(Path(file).as_posix(), safe="/")
    values = {
        "src": url(path), "title": str(meta.get("title") or meta.get("caption") or path.stem),
        "style": str(meta.get("caption") or meta.get("global_caption") or ""),
        "art": url(art) + "?v=" + str(Path(art).stat().st_mtime_ns) if art else "",
        "play": "true" if autoplay else "false", "request": uuid.uuid4().hex,
    }
    attrs = " ".join(f'data-{key}="{escape(value, quote=True)}"' for key, value in values.items())
    return f'<span class="ace-player-data" {attrs}></span>'
