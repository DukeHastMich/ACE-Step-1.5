"""Queued library stem action with track-specific status and downloadable playback."""

from pathlib import Path

import gradio as gr
from loguru import logger

from .library_stems import separate_song, stem_profile


def requested_song(songs: list[dict], path: str) -> dict:
    """Accept only the stable identity of a song in the current session's library."""
    for song in songs:
        if song["path"] == path:
            return song
    raise ValueError("This track is no longer in the current list. Refresh the library and try again.")


def create_stem_controls(table, catalog, root: Path) -> None:
    """Bind the per-row Get stems action to a serialized background job."""
    with gr.Group(visible=False) as panel:
        title = gr.Textbox(label="Stems for", interactive=False)
        status = gr.Textbox(label="Stem separation", interactive=False)
        names = ("vocals", "no_vocals", "drums", "bass", "other", "guitar", "piano")
        players = [gr.Audio(label="Instrumental" if name == "no_vocals" else name.title(),
                           type="filepath", interactive=False, visible=False,
                           buttons=["download"]) for name in names]

    def get_stems(songs, event: gr.EventData):
        """Clear old results, then expose only the selected separation's outputs."""
        try:
            song = requested_song(songs, event.song_id)
            count = event._data.get("stems", 2)
            _, expected = stem_profile(count)
        except (ValueError, AttributeError) as exc:
            raise gr.Error(str(exc)) from exc
        empty = [gr.update(value=None, visible=name in expected) for name in names]
        yield gr.update(visible=True), song["title"], f"Separating {count} stems… First use may download the model.", *empty
        try:
            paths = dict(zip(expected, separate_song(root, song["path"], count)))
        except (OSError, ValueError, RuntimeError) as exc:
            logger.exception("Library stem separation failed")
            yield gr.update(visible=True), song["title"], str(exc), *empty
            return
        yield (gr.update(visible=True), song["title"], "Stems ready — play or download below.",
               *(gr.update(value=paths.get(name), visible=name in paths) for name in names))

    table.click(get_stems, inputs=[catalog], outputs=[panel, title, status, *players],
                concurrency_limit=1, concurrency_id="library-demucs", queue=True,
                trigger_mode="once", show_progress="minimal")
