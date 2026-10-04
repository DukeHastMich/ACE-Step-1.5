"""Tests for recoverable trash, library filtering, and collision protection."""
import tempfile
import unittest
from pathlib import Path

from .library_store import scan_songs
from .library_trash import move_to_trash, restore_from_trash, trash_entries


class TrashTests(unittest.TestCase):
    """Exercise actual temporary files without touching saved user tracks."""

    def setUp(self):
        """Create a saved audio file with a metadata sidecar."""
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.song = self.root / "song.wav"
        self.song.write_bytes(b"original audio")
        self.song.with_suffix(".json").write_text('{"caption":"My song"}')

    def test_move_restore_and_metadata(self):
        """Trash hides audio and restores the same bytes and metadata across sessions."""
        token = move_to_trash(self.root, "song.wav", "My song")
        self.assertFalse(self.song.exists())
        self.assertEqual(scan_songs(self.root), [])
        self.assertEqual(trash_entries(self.root), [("My song", token)])
        self.assertFalse(self.song.with_suffix(".json").exists())
        restore_from_trash(self.root, token)
        self.assertEqual(self.song.read_bytes(), b"original audio")
        self.assertIn("My song", self.song.with_suffix(".json").read_text())
        self.assertEqual(trash_entries(self.root), [])
        self.assertEqual(len(scan_songs(self.root)), 1)

    def test_linked_files_move_restore_and_collisions(self):
        """Art and generation artifacts travel with audio, with collision preflight."""
        art = self.song.with_name(self.song.name + ".cover.png")
        session = self.song.with_suffix(".session.npz")
        art.write_bytes(b"art")
        session.write_bytes(b"session")
        token = move_to_trash(self.root, self.song.name, "Song")
        self.assertFalse(art.exists())
        self.assertFalse(session.exists())
        art.write_bytes(b"new art")
        with self.assertRaises(ValueError):
            restore_from_trash(self.root, token)
        self.assertFalse(self.song.exists())
        self.assertEqual(art.read_bytes(), b"new art")
        art.unlink()
        restore_from_trash(self.root, token)
        self.assertEqual(art.read_bytes(), b"art")
        self.assertEqual(session.read_bytes(), b"session")

    def test_restore_does_not_replace_existing_song(self):
        """Conflicting tracks remain untouched and the trashed copy stays recoverable."""
        token = move_to_trash(self.root, "song.wav", "My song")
        self.song.write_bytes(b"replacement")
        with self.assertRaises(ValueError):
            restore_from_trash(self.root, token)
        self.assertEqual(self.song.read_bytes(), b"replacement")
        self.assertEqual(len(trash_entries(self.root)), 1)

    def test_shared_metadata_and_other_song_unchanged(self):
        """Other encodings keep their shared sidecar when a WAV is trashed."""
        self.song.with_suffix(".mp3").write_bytes(b"other encoding")
        move_to_trash(self.root, "song.wav", "My song")
        self.assertEqual(scan_songs(self.root)[0]["title"], "My song")

    def test_reject_external_paths_and_bad_restore_token(self):
        """Requests cannot move or restore arbitrary filesystem paths."""
        with self.assertRaises(ValueError):
            move_to_trash(self.root, "../outside.wav", "Outside")
        with self.assertRaises(ValueError):
            restore_from_trash(self.root, "../outside")


if __name__ == "__main__":
    unittest.main()
