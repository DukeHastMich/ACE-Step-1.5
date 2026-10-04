"""Independent, persistent vocal-reference personas stored outside the song catalog."""
import json
from pathlib import Path
import shutil
import uuid
from PIL import Image

from .library_artwork import existing_artwork
from .library_stems import separate_song
from .library_store import AUDIO_SUFFIXES, resolve_song


def persona_root(root: Path) -> Path:
    """Constrain persona storage to the library's allowed directory."""
    folder = (root / ".personas").resolve()
    if not folder.is_relative_to(root.resolve()):
        raise ValueError("Persona storage must stay inside the library.")
    return folder


def load_persona(root: Path, identity: str) -> dict:
    """Load a complete persona using a validated opaque identity."""
    if len(identity) != 32 or any(c not in "0123456789abcdef" for c in identity):
        raise ValueError("Choose a saved persona.")
    folder = (persona_root(root) / identity).resolve()
    if not folder.is_relative_to(persona_root(root)):
        raise ValueError("Invalid persona location.")
    manifest = folder / "persona.json"
    if manifest.stat().st_size > 100000:
        raise ValueError("Persona metadata is too large.")
    data = json.loads(manifest.read_text(encoding="utf-8"))
    audio = (folder / data["audio"]).resolve()
    if not audio.is_relative_to(folder) or not audio.is_file():
        raise ValueError("Persona vocal reference is missing.")
    return {**data, "id": identity, "audio_path": str(audio)}


def list_personas(root: Path) -> list[dict]:
    """List complete personas, tolerating interrupted or unavailable entries."""
    result = []
    for folder in persona_root(root).glob("*"):
        try:
            result.append(load_persona(root, folder.name))
        except (OSError, ValueError, KeyError, TypeError):
            continue
    return sorted(result, key=lambda p: p["name"].casefold())


def create_persona(root: Path, name: str, description: str, source: str = "", upload: str = "", artwork: str = "") -> dict:
    """Copy uploaded or Demucs-isolated vocals; publish metadata only after files exist."""
    name = str(name or "").strip()
    if not name or len(name) > 120 or len(description or "") > 5000:
        raise ValueError("Enter a persona name (up to 120 characters) and a shorter voice description.")
    art = None
    if upload:
        audio = Path(upload)
        if audio.suffix.lower() not in AUDIO_SUFFIXES or not audio.is_file():
            raise ValueError("Upload a valid vocal audio file.")
    else:
        resolve_song(root, source)
        art = existing_artwork(root, source)
        audio = Path(separate_song(root, source)[0])
    if artwork:
        picture = Path(artwork)
        if not picture.is_file() or picture.stat().st_size > 25 * 1024 * 1024:
            raise ValueError("Choose a profile picture smaller than 25 MB.")
        with Image.open(picture) as image:
            if image.format != "PNG" or image.width * image.height > 40_000_000:
                raise ValueError("Choose a PNG profile picture under 40 megapixels.")
            image.verify()
        art = str(picture)
    identity = uuid.uuid4().hex
    folder = persona_root(root) / identity
    folder.mkdir(parents=True)
    filename = "vocals" + audio.suffix.lower()
    shutil.copy2(audio, folder / filename)
    if art:
        shutil.copy2(art, folder / "cover.png")
    data = {"name": name, "description": description or "", "audio": filename,
            "source_track": source, "artwork": "cover.png" if art else "", "version": 1}
    (folder / "persona.json").write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return load_persona(root, identity)


def persona_inputs(root: Path, identity: str, caption: str) -> tuple:
    """Load vocal guidance while preserving the current song's style and lyrics."""
    persona = load_persona(root, identity)
    description = persona["description"].strip()
    caption = (caption or "").strip()
    if description and description not in caption:
        caption = "\n".join(filter(None, (caption, description)))
    return "Custom", persona["audio_path"], caption
