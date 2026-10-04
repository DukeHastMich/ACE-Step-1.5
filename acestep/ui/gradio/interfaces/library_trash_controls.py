"""Per-song trash action and persistent restore controls for the local library."""

import gradio as gr

from .library_stem_controls import requested_song
from .library_trash import move_to_trash, restore_from_trash, trash_entries


def create_trash_controls(demo, table, catalog, search, root, refresh_library,
                          refresh_outputs, selected_outputs):
    """Refresh the library after trash/restore and clear stale selected-track controls."""
    notice = gr.Textbox(label="Library status", interactive=False, visible=False)
    with gr.Accordion("Trash", open=False):
        deleted = gr.Dropdown(label="Trashed tracks", choices=[], value=None)
        restore = gr.Button("Restore to library")

    def list_trash():
        """Refresh restorable tracks from disk."""
        return gr.update(choices=trash_entries(root), value=None)

    def trash_song(songs, query, event: gr.EventData):
        """Trash a validated row identity and immediately remove it from the visible list."""
        try:
            song = requested_song(songs, event.song_id)
            move_to_trash(root, song["path"], song["title"])
        except (OSError, ValueError) as exc:
            raise gr.Error(str(exc)) from exc
        return (*refresh_library(query), list_trash(),
                gr.update(value=f'Moved to trash: {song["title"]}', visible=True),
                None, "", "", "", gr.update(interactive=False), gr.update(interactive=False))

    def restore_song(token, query):
        """Restore one chosen track, preserving any conflicting existing song."""
        try:
            restore_from_trash(root, token)
        except (OSError, ValueError, KeyError) as exc:
            raise gr.Error(str(exc)) from exc
        return (*refresh_library(query), list_trash(),
                gr.update(value="Track restored to the library.", visible=True))

    demo.load(list_trash, outputs=[deleted], queue=False)
    table.submit(trash_song, inputs=[catalog, search],
                 outputs=[*refresh_outputs, deleted, notice, *selected_outputs],
                 concurrency_id="library-trash", concurrency_limit=1)
    restore.click(restore_song, inputs=[deleted, search],
                  outputs=[*refresh_outputs, deleted, notice],
                  concurrency_id="library-trash", concurrency_limit=1)
