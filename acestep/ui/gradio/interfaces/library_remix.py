"""Restore the original creation inputs and source audio for a library remix."""

import gradio as gr

from .library_store import read_metadata, resolve_song
from .library_stem_controls import requested_song


def remix_values(root, relative):
    """Load original UI text, falling back to generation metadata for older tracks."""
    path = resolve_song(root, relative)
    meta = read_metadata(path)
    saved = meta.get("remix_inputs")
    saved = saved if isinstance(saved, dict) else {}
    style = str(saved.get("style", meta.get("caption") or meta.get("global_caption") or ""))
    return ("Remix", str(path), style, str(saved.get("lyrics", meta.get("lyrics") or "")),
            str(saved.get("title", meta.get("title") or "")), str(saved.get("prompt", "")))


def wire_remix_action(table, catalog, button, selection, root, generation):
    """Bind both remix entry points to the same complete set of creation controls."""
    keys = ("generation_mode", "src_audio", "captions", "lyrics", "song_title", "simple_query_input")
    targets = [generation[key] for key in keys]
    targets.append(generation["src_audio_row"])

    def load(relative):
        """Surface missing audio as a recoverable UI error."""
        try:
            values = list(remix_values(root, relative))
            values[1] = gr.update(value=values[1], label="Source Audio — " + (values[4] or relative))
            return (*values, gr.update(visible=True))
        except (OSError, ValueError) as exc:
            raise gr.Error(str(exc)) from exc

    def from_menu(songs, event: gr.EventData):
        """Resolve the clicked identity rather than using the previously selected track."""
        if not isinstance(event._data, dict) or "song_id" not in event._data or event._data.get("action") == "persona":
            return tuple(gr.skip() for _ in targets)
        try:
            song = requested_song(songs, event.song_id)
        except (ValueError, AttributeError) as exc:
            raise gr.Error(str(exc)) from exc
        if event._data.get("action") == "remaster":
            path = resolve_song(root, song["path"])
            meta = read_metadata(path)
            values = list(load(song["path"]))
            values[0] = "Remaster"
            values[2] = str(meta.get("caption") or meta.get("global_caption") or values[2])
            values[3] = str(meta.get("lyrics") or values[3])
            values[4] = (str(meta.get("title") or song.get("title") or path.stem)[:170] + " (Remaster)")
            return tuple(values)
        return load(song["path"])

    table.change(from_menu, inputs=[catalog], outputs=targets, queue=False)
    button.click(load, inputs=[selection], outputs=targets, queue=False)
