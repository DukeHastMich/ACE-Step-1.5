"""Open a validated library track's containing folder in the desktop file manager."""

import os
from pathlib import Path
import subprocess
import sys

import gradio as gr

from .library_stem_controls import requested_song
from .library_store import resolve_song


def open_song_folder(root: Path, relative: str) -> None:
    """Open only the parent directory of an existing song inside the library."""
    folder = resolve_song(root, relative).parent
    if sys.platform == "win32":
        os.startfile(str(folder))
    else:
        command = "open" if sys.platform == "darwin" else "xdg-open"
        subprocess.Popen([command, str(folder)], shell=False)


def wire_folder_action(table, catalog, root: Path) -> None:
    """Connect the menu action without changing playback or other library actions."""
    def open_folder(songs, event: gr.EventData):
        """Validate the current session's song identity before opening its directory."""
        try:
            song = requested_song(songs, event.song_id)
            open_song_folder(root, song["path"])
        except (OSError, ValueError, AttributeError) as exc:
            raise gr.Error(f"Could not open the track folder: {exc}") from exc
        gr.Info("Opened the track folder on this computer.")

    table.input(open_folder, inputs=[catalog], outputs=[], queue=False)
