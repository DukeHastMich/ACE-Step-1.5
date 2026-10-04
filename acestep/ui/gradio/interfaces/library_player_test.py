"""Validate compact player payloads without exposing arbitrary files or markup."""
import json
from pathlib import Path
import tempfile
import unittest
from .library_player import player_payload


class PlayerTests(unittest.TestCase):
    """Check real metadata encoding and library path validation."""

    def test_payload_escapes_track_text_and_requests_playback(self):
        """A track with markup in its title is data, never executable player HTML."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            song = root / "song & one.wav"
            song.write_bytes(b"audio")
            song.with_suffix(".json").write_text(json.dumps({
                "title": '<script>"title"</script>', "caption": "folk & strings"}))
            payload = player_payload(root, song.name, True)
            self.assertNotIn("<script>", payload)
            self.assertIn("&lt;script&gt;", payload)
            self.assertIn('data-play="true"', payload)
            self.assertIn("song%20%26%20one.wav", payload)
            self.assertNotEqual(payload, player_payload(root, song.name, True))
            self.assertIn('data-play="false"', player_payload(root, song.name))

    def test_outside_audio_is_rejected(self):
        """The new player inherits the library's file boundary checks."""
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                player_payload(Path(directory), "../outside.wav")
