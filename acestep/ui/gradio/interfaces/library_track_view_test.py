"""Track pages and persistent notes preserve linked generation data."""
import json
from pathlib import Path
import tempfile
import unittest
from .library_notes import save_artist_notes
from .library_track_view import render_track_view
from .library_trash import move_to_trash, restore_from_trash


class TrackViewTests(unittest.TestCase):
    """Use disposable audio and sidecars for save and restore checks."""

    def test_notes_round_trip_and_trash_restore(self):
        """Notes persist without changing generation fields or audio."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            audio = root / "track.wav"
            audio.write_bytes(b"audio")
            meta = {"title": "A title", "caption": "Folk", "lyrics": "Verse", "seed": 42}
            audio.with_suffix(".json").write_text(json.dumps(meta))
            save_artist_notes(root, audio.name, "Try warmer vocals\nCredit: me")
            saved = json.loads(audio.with_suffix(".json").read_text())
            self.assertEqual({k: saved[k] for k in meta}, meta)
            self.assertEqual(audio.read_bytes(), b"audio")
            token = move_to_trash(root, audio.name, "A title")
            restore_from_trash(root, token)
            self.assertIn("Try warmer vocals", render_track_view(root, audio.name))
            save_artist_notes(root, audio.name, "")
            self.assertEqual(json.loads(audio.with_suffix(".json").read_text())["artist_notes"], "")

    def test_render_escapes_text_and_save_rejects_corrupt_metadata(self):
        """User text stays text, and malformed metadata is never overwritten."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            audio = root / "track.wav"
            audio.write_bytes(b"audio")
            sidecar = audio.with_suffix(".json")
            sidecar.write_text(json.dumps({"title": "<script>x</script>", "artist_notes": "</textarea><script>x</script>"}))
            html = render_track_view(root, audio.name)
            self.assertNotIn("<script>", html)
            self.assertIn("&lt;script&gt;", html)
            self.assertIn("Artist notes", html)
            self.assertIn('data-action="remaster"', html)
            sidecar.write_text("invalid json")
            with self.assertRaises(ValueError):
                save_artist_notes(root, audio.name, "new")
            self.assertEqual(sidecar.read_text(), "invalid json")
            with self.assertRaises(ValueError):
                save_artist_notes(root, "../outside.wav", "new")

    def test_distribution_persists_and_hiding_preserves_fields(self):
        """Distribution fields survive toggling and trash/restore with the track."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            audio = root / "track.wav"
            audio.write_bytes(b"audio")
            values = {"enabled": True, "isrc": "US-ABC-26-00001", "notes": "Release next month <draft>"}
            save_artist_notes(root, audio.name, "Artist note", values)
            html = render_track_view(root, audio.name)
            self.assertIn("data-distribution checked", html)
            self.assertIn("US-ABC-26-00001", html)
            self.assertIn("&lt;draft&gt;", html)
            self.assertLess(html.index('class="ace-distribution"'), html.index("<h2>Track details"))
            values["enabled"] = False
            save_artist_notes(root, audio.name, "Artist note", values)
            self.assertIn("data-distribution-fields hidden", render_track_view(root, audio.name))
            token = move_to_trash(root, audio.name, "Track")
            restore_from_trash(root, token)
            saved = json.loads(audio.with_suffix(".json").read_text())
            self.assertEqual(saved["distribution"], values)
            self.assertEqual(saved["artist_notes"], "Artist note")
            with self.assertRaises(ValueError):
                save_artist_notes(root, audio.name, "Artist note", {"enabled": "yes"})
