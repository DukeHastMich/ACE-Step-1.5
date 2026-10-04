"""Selected-song artwork display and PNG drag-and-drop controls."""

from pathlib import Path

import gradio as gr

from .library_artwork import existing_artwork, save_artwork
from .library_store import read_metadata, resolve_song


def create_artwork_controls(selection, root: Path):
    """Create an artwork editor; return a binder for the library refresh callback."""
    with gr.Accordion("Album art", open=True):
        selected = gr.Textbox(label="Artwork for", value="Select a song in the library first.",
                              interactive=False)
        with gr.Row():
            preview = gr.Image(label="Album art", interactive=False, height=200,
                               buttons=[], visible=False)
            with gr.Column():
                upload = gr.File(label="Drop PNG album art here", file_types=[".png"],
                                 type="filepath", interactive=True, elem_id="ace-art-upload", elem_classes="ace-art-upload")
                save = gr.Button("Save artwork", interactive=False)
                status = gr.Textbox(label="Artwork status", interactive=False, visible=False)

    def select_artwork(relative):
        """Show the selected song's artwork and clear any uncommitted upload."""
        if not relative:
            return ("Select a song in the library first.", gr.update(value=None, visible=False),
                    gr.update(value=None, interactive=True), gr.update(interactive=False),
                    gr.update(value="", visible=False))
        try:
            path = resolve_song(root, relative)
            meta = read_metadata(path)
            title = str(meta.get("title") or meta.get("caption") or path.stem)
            artwork = existing_artwork(root, relative)
            return (title, gr.update(value=artwork, visible=bool(artwork)),
                    gr.update(value=None, interactive=True), gr.update(interactive=True),
                    gr.update(value="", visible=False))
        except (ValueError, OSError) as exc:
            raise gr.Error(str(exc)) from exc

    selection.change(select_artwork, inputs=[selection],
                     outputs=[selected, preview, upload, save, status], queue=False)

    def bind_refresh(search, refresh_library, refresh_outputs):
        """Wire Save once the library's refresh callback is available."""
        def attach(relative, file, query):
            """Save for the currently displayed song and immediately refresh its thumbnail."""
            try:
                path = save_artwork(root, relative, file)
            except (ValueError, OSError) as exc:
                raise gr.Error(str(exc)) from exc
            return (gr.update(value=path, visible=True), None, gr.update(value="Artwork saved.", visible=True),
                    *refresh_library(query))

        save.click(attach, inputs=[selection, upload, search],
                   outputs=[preview, upload, status, *refresh_outputs],
                   concurrency_id="library-artwork", concurrency_limit=1)

    return bind_refresh, select_artwork, [selected, preview, upload, save, status]
