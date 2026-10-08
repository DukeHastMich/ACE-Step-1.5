"""Verify persistent PNG artwork without changing music or generation metadata."""

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import gradio as gr
from PIL import Image

from .library_artwork import existing_artwork, save_artwork
from .library_rows import render_song_rows
from .library_store import scan_songs
from .library_trash import move_to_trash, restore_from_trash
from .song_library import create_song_library


class ArtworkTests(unittest.TestCase):
    """Use tiny generated test fixtures, never user artwork."""

    def setUp(self):
        """Create an audio track and a known-good PNG fixture."""
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.song = self.root / "track.wav"
        self.song.write_bytes(b"original audio")
        self.song.with_suffix(".json").write_text('{"title":"Night Sky","caption":"folk"}')
        self.upload = self.root / "upload.png"
        Image.new("RGB", (16, 16), "navy").save(self.upload)

    def test_save_display_and_preserve_metadata(self):
        """Saved PNG bytes persist, render a thumbnail, and leave song metadata untouched."""
        before = self.song.with_suffix(".json").read_bytes()
        saved = save_artwork(self.root, self.song.name, str(self.upload))
        self.assertEqual(Path(saved).read_bytes(), self.upload.read_bytes())
        self.assertEqual(existing_artwork(self.root, self.song.name), saved)
        self.assertEqual(self.song.with_suffix(".json").read_bytes(), before)
        self.assertEqual(self.song.read_bytes(), b"original audio")
        songs = scan_songs(self.root)
        self.assertEqual(len(songs), 1)
        self.assertIn('class="song-art"', render_song_rows(songs, self.root))

    def test_replacement_and_trash_restore(self):
        """Replacing artwork refreshes the saved PNG and restoring a song preserves its art."""
        saved = save_artwork(self.root, self.song.name, str(self.upload))
        Image.new("RGB", (16, 16), "orange").save(self.upload)
        save_artwork(self.root, self.song.name, str(self.upload))
        self.assertEqual(Path(saved).read_bytes(), self.upload.read_bytes())
        token = move_to_trash(self.root, self.song.name, "Night Sky")
        restore_from_trash(self.root, token)
        self.assertEqual(existing_artwork(self.root, self.song.name), saved)

    def test_invalid_png_and_external_song_are_rejected(self):
        """Spoofed image files and arbitrary track paths cannot be attached."""
        self.upload.write_text("not a png")
        with self.assertRaises(ValueError):
            save_artwork(self.root, self.song.name, str(self.upload))
        self.assertIsNone(existing_artwork(self.root, self.song.name))
        Image.new("RGB", (16, 16)).save(self.upload)
        with self.assertRaises(ValueError):
            save_artwork(self.root, "../outside.wav", str(self.upload))

    def test_tile_plays_but_upload_selection_does_not(self):
        """Tile clicks request playback; selecting via text or upload preserves silence."""
        with gr.Blocks() as demo, patch(
                "acestep.ui.gradio.interfaces.song_library.DEFAULT_RESULTS_DIR", str(self.root)):
            generation = {key: gr.Textbox() for key in ("generation_mode", "src_audio", "captions", "lyrics", "song_title", "simple_query_input")}
            generation["src_audio_row"] = gr.Row(visible=False)
            create_song_library(demo, generation, {"generated_audio_batch": gr.File()})
        handler = next(fn.fn for fn in demo.fns.values() if fn.fn.__name__ == "select_song")
        songs = scan_songs(self.root)
        for play in (True, False):
            event = gr.SelectData(None, {"index": self.song.name, "value": self.song.name, "play": play})
            updates = handler(songs, event)
            self.assertIn(f'data-play="{str(play).lower()}"', updates[0]["value"])
            self.assertEqual(updates[6], "Night Sky")
            self.assertTrue(updates[9]["interactive"])
        event = gr.SelectData(None, {"index": self.song.name, "value": self.song.name, "detail": True})
        self.assertIn('aria-label="Track details"', handler(songs, event)[-1])
        html = render_song_rows(songs, self.root)
        self.assertIn('aria-label="Play Night Sky"', html)
        self.assertIn('aria-label="Upload artwork for Night Sky"', html)


if __name__ == "__main__":
    unittest.main()
