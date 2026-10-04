"""Regression tests for saved-song discovery and containment."""

import json
import tempfile
import unittest
from pathlib import Path

from acestep.ui.gradio.interfaces.library_store import resolve_song, scan_songs, song_rows


class LibraryStoreTests(unittest.TestCase):
    """Exercise real files without models, network access, or audio decoding."""

    def setUp(self):
        """Create an isolated output directory."""
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "outputs"
        self.root.mkdir()

    def song(self, name="batch/song.mp3", metadata=None):
        """Write an audio placeholder and optional generation sidecar."""
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"audio")
        if metadata is not None:
            path.with_suffix(".json").write_text(json.dumps(metadata), encoding="utf-8")
        return path

    def test_metadata_and_search(self):
        """Existing nested outputs are searchable and expose matching row/state order."""
        self.song(metadata={"caption": "Night drive", "lyrics": "Moonlight", "duration": 123})
        songs = scan_songs(self.root, "MOON")
        self.assertEqual(len(songs), 1)
        self.assertEqual(song_rows(songs)[0][::2], ["Night drive", "2:03"])
        self.assertTrue(resolve_song(self.root, songs[0]["path"]).is_file())
        self.assertEqual(scan_songs(self.root, "missing"), [])

    def test_corrupt_sidecar_and_empty_output(self):
        """A damaged metadata file does not hide audio or advertise unfinished files."""
        song = self.song()
        song.with_suffix(".json").write_text("{broken", encoding="utf-8")
        (self.root / "pending.wav").touch()
        self.assertEqual(len(scan_songs(self.root)), 1)
        self.assertEqual(scan_songs(self.root)[0]["title"], "song")

    def test_rejects_outside_and_non_audio_paths(self):
        """Client state cannot select files outside the library or metadata as audio."""
        (self.root.parent / "outside.mp3").write_bytes(b"private")
        self.song(metadata={})
        for name in ("../outside.mp3", "batch/song.json", "missing.mp3"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                resolve_song(self.root, name)

    def test_scanning_does_not_modify_originals(self):
        """Library browsing preserves the existing output files byte-for-byte."""
        song = self.song(metadata={"caption": "Original"})
        before = {p: p.read_bytes() for p in song.parent.iterdir()}
        scan_songs(self.root)
        self.assertEqual(before, {p: p.read_bytes() for p in song.parent.iterdir()})


if __name__ == "__main__":
    unittest.main()
