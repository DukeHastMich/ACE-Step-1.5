"""Validate folder actions without launching desktop windows during unit tests."""

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import gradio as gr

from .library_folder import open_song_folder, wire_folder_action
from .library_rows import render_song_rows, ROW_SCRIPT

MODULE = "acestep.ui.gradio.interfaces.library_folder"


class FolderTests(unittest.TestCase):
    """Cover nested folders, stale paths, and independence from existing actions."""

    def setUp(self):
        """Create a nested library entry with shell-sensitive characters."""
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.song = self.root / "album & mixes" / "my song.wav"
        self.song.parent.mkdir()
        self.song.write_bytes(b"audio")
        self.relative = str(self.song.relative_to(self.root))

    def test_windows_opens_containing_folder(self):
        """Windows receives the actual folder, not the audio file or a shell command."""
        with patch(MODULE + ".sys.platform", "win32"), \
             patch(MODULE + ".os.startfile", create=True) as start:
            open_song_folder(self.root, self.relative)
            start.assert_called_once_with(str(self.song.parent.resolve()))
        self.assertEqual(self.song.read_bytes(), b"audio")

    def test_other_desktops_use_separate_arguments(self):
        """Linux and macOS preserve paths with spaces and punctuation."""
        for platform, command in (("linux", "xdg-open"), ("darwin", "open")):
            with self.subTest(platform=platform), patch(MODULE + ".sys.platform", platform), \
                 patch(MODULE + ".subprocess.Popen") as launch:
                open_song_folder(self.root, self.relative)
                launch.assert_called_once_with([command, str(self.song.parent.resolve())], shell=False)

    def test_invalid_or_missing_song_never_launches(self):
        """Reject external paths and missing audio before opening a folder."""
        with patch(MODULE + ".os.startfile", create=True) as start:
            for relative in ("../outside.wav", "missing.wav"):
                with self.assertRaises(ValueError):
                    open_song_folder(self.root, relative)
            start.assert_not_called()

    def test_menu_and_event_wiring(self):
        """The new menu uses its own event, preserving stems and trash actions."""
        song = dict(path=self.relative, title="My song", created="Today", duration="1:00", format="WAV")
        html = render_song_rows([song])
        for label in ("Get stems", "Move to trash", "Open folder"):
            self.assertIn(label, html)
        self.assertIn("trigger('input', {song_id: folder.dataset.folder})", ROW_SCRIPT)
        with gr.Blocks() as demo:
            table = gr.HTML()
            catalog = gr.State([song])
            wire_folder_action(table, catalog, self.root)
        function = next(iter(demo.fns.values())).fn
        with patch(MODULE + ".open_song_folder") as launch, patch(MODULE + ".gr.Info"):
            function([song], gr.EventData(table, {"song_id": self.relative}))
            launch.assert_called_once_with(self.root, self.relative)
            with self.assertRaises(gr.Error):
                function([], gr.EventData(table, {"song_id": self.relative}))


if __name__ == "__main__":
    unittest.main()
