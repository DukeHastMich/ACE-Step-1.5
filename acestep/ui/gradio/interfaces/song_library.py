"""Saved-song library controls and local-only event wiring."""

from pathlib import Path

import gradio as gr

from acestep.ui.gradio.events.results.generation_info import DEFAULT_RESULTS_DIR
from acestep.ui.gradio.i18n import t
from .library_store import read_metadata, resolve_song, scan_songs

from .library_artwork_controls import create_artwork_controls
from .library_folder import wire_folder_action
from .library_remix import wire_remix_action
from .library_player import player_payload, PLAYER_SCRIPT
from .library_track_view import render_track_view, TRACK_SCRIPT
from .library_notes import save_artist_notes
from .library_rows import render_song_rows, ROW_SCRIPT, ROW_CSS
from .library_trash_controls import create_trash_controls
from .library_stem_controls import create_stem_controls, requested_song

def create_song_library(demo, generation: dict, results: dict) -> None:
    """Build a searchable local library with playback and existing editing actions."""
    root = Path(DEFAULT_RESULTS_DIR)
    catalog = gr.State([])
    selection = gr.State("")
    gr.Markdown(t("workspace.library_hint"), elem_classes="library-hint")
    with gr.Row():
        search = gr.Textbox(placeholder=t("workspace.search"), show_label=False,
                            container=False, scale=6)
        refresh = gr.Button(t("service.refresh_btn"), scale=1, min_width=90)
    count = gr.Markdown()
    table = gr.HTML(value="", js_on_load=ROW_SCRIPT, css_template=ROW_CSS,
                    elem_id="ace-song-list")
    detail = gr.HTML(value="", js_on_load=TRACK_SCRIPT, elem_id="ace-track-view")
    create_stem_controls(table, catalog, root)
    wire_folder_action(table, catalog, root)
    player = gr.HTML(value="", js_on_load=PLAYER_SCRIPT, elem_id="ace-library-player")
    bind_artwork, select_artwork, artwork_outputs = create_artwork_controls(selection, root)
    with gr.Row():
        remix = gr.Button(t("results.send_to_remix_btn"), interactive=False)
        repaint = gr.Button(t("results.send_to_repaint_btn"), interactive=False)
    with gr.Accordion(t("workspace.song_details"), open=False):
        caption = gr.Textbox(label=t("generation.caption_label"), interactive=False)
        lyrics = gr.Textbox(label=t("generation.lyrics_label"), lines=8, interactive=False)

    def refresh_library(query):
        """Refresh rows and selection state together without disturbing playback."""
        songs = scan_songs(root, query or "")
        return render_song_rows(songs, root), songs, t("workspace.song_count", count=len(songs))

    def select_song(songs, event: gr.SelectData):
        """Load the selected catalog entry; never accept an arbitrary browser path."""
        try:
            relative = requested_song(songs, event.index)["path"]
        except ValueError as exc:
            raise gr.Error(str(exc)) from exc
        try:
            path = resolve_song(root, relative)
        except ValueError as exc:
            raise gr.Error(t("workspace.song_missing")) from exc
        meta = read_metadata(path)
        return (gr.update(value=player_payload(root, relative, bool(getattr(event, "play", False)))), str(meta.get("caption") or meta.get("global_caption") or ""),
                str(meta.get("lyrics") or ""), relative,
                gr.update(interactive=True), gr.update(interactive=True), *select_artwork(relative),
                render_track_view(root, relative) if event._data.get("detail") else gr.skip())

    def reuse_song(relative, mode):
        """Reuse selected audio and its original text in the existing editing pipeline."""
        try:
            path = resolve_song(root, relative)
        except ValueError as exc:
            raise gr.Error(t("workspace.song_missing")) from exc
        meta = read_metadata(path)
        return (mode, str(path), str(meta.get("caption") or meta.get("global_caption") or ""),
                str(meta.get("lyrics") or ""))

    def save_notes(songs, event: gr.EventData):
        """Save notes only for a validated library row and refresh its track view."""
        try:
            relative = requested_song(songs, event.song_id)["path"]
            save_artist_notes(root, relative, event.notes, event._data.get("distribution"))
            return render_track_view(root, relative, "Track notes and distribution saved.")
        except (OSError, ValueError, AttributeError) as exc:
            raise gr.Error(str(exc)) from exc

    detail.submit(save_notes, inputs=[catalog], outputs=[detail],
                  concurrency_id="library-notes", concurrency_limit=1)
    refresh_outputs = [table, catalog, count]
    bind_artwork(search, refresh_library, refresh_outputs)
    demo.load(refresh_library, inputs=[search], outputs=refresh_outputs, queue=False)
    refresh.click(refresh_library, inputs=[search], outputs=refresh_outputs, queue=False)
    search.submit(refresh_library, inputs=[search], outputs=refresh_outputs, queue=False)
    search.change(refresh_library, inputs=[search], outputs=refresh_outputs,
                  trigger_mode="always_last", queue=False)
    results["generated_audio_batch"].change(
        refresh_library, inputs=[search], outputs=refresh_outputs, queue=False)
    table.select(select_song, inputs=[catalog],
                 outputs=[player, caption, lyrics, selection, remix, repaint, *artwork_outputs, detail], queue=False)
    targets = [generation[key] for key in ("generation_mode", "src_audio", "captions", "lyrics")]
    wire_remix_action(table, catalog, remix, selection, root, generation)
    repaint.click(lambda relative: reuse_song(relative, "Repaint"), [selection], targets)

    create_trash_controls(demo, table, catalog, search, root, refresh_library,
                          refresh_outputs, [player, caption, lyrics, selection, remix, repaint])



    return table, catalog
