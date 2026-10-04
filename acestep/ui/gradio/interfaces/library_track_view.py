"""Render a local track detail view using saved audio metadata."""
from datetime import datetime
from html import escape
from pathlib import Path
from urllib.parse import quote
import uuid

from .library_artwork import existing_artwork
from .library_download import download_link
from .library_store import read_metadata, resolve_song

TRACK_SCRIPT = Path(__file__).with_suffix(".js").read_text(encoding="utf-8")
TRACK_CSS = Path(__file__).with_suffix(".css").read_text(encoding="utf-8")


def render_track_view(root: Path, relative: str, notice: str = "") -> str:
    """Build an escaped track page; never treat saved prompts as HTML."""
    path = resolve_song(root, relative)
    meta = read_metadata(path)
    title = str(meta.get("title") or meta.get("caption") or path.stem)
    style = str(meta.get("caption") or meta.get("global_caption") or "")
    lyrics = str(meta.get("lyrics") or "")
    inputs = meta.get("remix_inputs")
    prompt = str(inputs.get("prompt") or "") if isinstance(inputs, dict) else ""
    distribution = meta.get("distribution")
    distribution = distribution if isinstance(distribution, dict) else {}
    checked = "checked" if distribution.get("enabled") is True else ""
    hidden = "" if checked else "hidden"
    distribution_html = f"""<section class="ace-distribution"><label class="ace-distribution-toggle">
        <input type="checkbox" data-distribution {checked}> Distribution</label>
        <div data-distribution-fields {hidden}>
        <label>ISRC code<input type="text" data-isrc maxlength="32" value="{escape(str(distribution.get('isrc') or ''), quote=True)}" placeholder="Enter the track's ISRC code"></label>
        <label>Distribution notes<textarea data-distribution-notes rows="5" maxlength="50000" placeholder="Distributor, release dates, links, or reminders">{escape(str(distribution.get('notes') or ''))}</textarea></label>
        </div><button class="ace-save-notes" data-save-notes>Save distribution</button>
        <p class="ace-notes-status" role="status">{escape(notice)}</p></section>"""
    art = existing_artwork(root, relative)
    cover = '<span aria-hidden="true">♫</span>'
    if art:
        url = "gradio_api/file=" + quote(Path(art).as_posix(), safe="/")
        url += "?v=" + str(Path(art).stat().st_mtime_ns)
        cover = f'<img src="{escape(url, quote=True)}" alt="Album artwork">'
    facts = [path.suffix[1:].upper(), datetime.fromtimestamp(path.stat().st_mtime).strftime("%b %d, %Y")]
    for key, label in (("bpm", "BPM"), ("keyscale", "Key"), ("timesignature", "Time")):
        if meta.get(key):
            facts.append(f"{label}: {meta[key]}")
    buttons = "".join(f'<button data-action="{action}">{label}</button>' for action, label in (
        ("play", "▶ Play"), ("remix", "Remix"), ("remaster", "Remaster"),
        ("persona", "Create Persona"), ("stems", "Get stems"), ("folder", "Open folder"), ("trash", "Move to trash")))
    prompt_html = (f'<section><h2>Original prompt</h2><p>{escape(prompt)}</p></section>' if prompt else "")
    return f"""<section class="ace-track-page" aria-label="Track details" data-song="{escape(relative, quote=True)}" data-request="{uuid.uuid4().hex}">
      <button class="ace-track-back" data-close>← Back to library</button>
      <div class="ace-track-hero">
        <button class="ace-track-cover" data-action="art" aria-label="Change album artwork">{cover}<small>↥ Change artwork</small></button>
        <div class="ace-track-summary"><p class="ace-track-eyebrow">YOUR MUSIC</p>
          <h1>{escape(title)}</h1><p class="ace-track-style">{escape(style)}</p>
          <p class="ace-track-facts">{escape(" · ".join(facts))}</p>
          <div class="ace-track-actions">{buttons}{download_link(root, {"path": relative, "title": title})}</div>
        </div>
      </div>
      <div class="ace-track-body"><section><h2>Lyrics</h2><p class="ace-track-lyrics">{escape(lyrics) or "No lyrics saved for this track."}</p></section>
        <aside><section><h2>Artist notes</h2>
        <p class="ace-notes-label">Ideas, credits, changes, or reminders for this track</p>
        <textarea aria-label="Artist notes" maxlength="50000" rows="8" placeholder="Write your notes…">{escape(str(meta.get("artist_notes") or ""))}</textarea>
        <button class="ace-save-notes" data-save-notes>Save notes</button>
        <p class="ace-notes-status" role="status">{escape(notice)}</p></section>{distribution_html}{prompt_html}<section><h2>Track details</h2><p>{escape(path.name)}</p>
        <p>Remix loads this track and its saved text into Create. Remaster saves a new version.</p></section></aside>
      </div></section>"""
