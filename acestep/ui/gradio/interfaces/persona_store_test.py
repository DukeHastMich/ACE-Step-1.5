"""Persistent personas stay usable independently of their originating song."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from PIL import Image

from .persona_store import create_persona, list_personas, load_persona, persona_inputs
from .persona_controls import render_personas
from .library_store import scan_songs
from .library_trash import move_to_trash


class PersonaTests(unittest.TestCase):
    """Exercise persistence with disposable local audio and mocked separation."""

    def test_track_persona_survives_source_trash(self):
        """Demucs vocals are copied, excluded from songs, and remain after source trash."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            song = root / "song.wav"
            song.write_bytes(b"music")
            vocals = root / ".stems" / "fixture" / "vocals.wav"
            vocals.parent.mkdir(parents=True)
            vocals.write_bytes(b"voice")
            with patch("acestep.ui.gradio.interfaces.persona_store.separate_song", return_value=(str(vocals), "")) as separate:
                persona = create_persona(root, "Raven", "Warm baritone", song.name)
            separate.assert_called_once_with(root, song.name)
            self.assertEqual(len(scan_songs(root)), 1)
            move_to_trash(root, song.name, "Song")
            vocals.unlink()
            saved = load_persona(root, persona["id"])
            self.assertEqual(Path(saved["audio_path"]).read_bytes(), b"voice")
            self.assertEqual(len(list_personas(root)), 1)
            mode, reference, caption = persona_inputs(root, persona["id"], "Acoustic folk")
            self.assertEqual(mode, "Custom")
            self.assertEqual(reference, saved["audio_path"])
            self.assertEqual(caption, "Acoustic folk\nWarm baritone")
            self.assertEqual(persona_inputs(root, persona["id"], caption)[2], caption)
            self.assertIn("Preview Raven", render_personas(root))

    def test_uploaded_reference_and_invalid_identity(self):
        """Uploads bypass separation and unsafe identities are rejected."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            upload = root / "voice.wav"
            upload.write_bytes(b"voice")
            picture = root / "profile.png"
            Image.new("RGB", (16, 16), "purple").save(picture)
            with patch("acestep.ui.gradio.interfaces.persona_store.separate_song") as separate:
                persona = create_persona(root, "<Singer>", "", upload=str(upload), artwork=str(picture))
            separate.assert_not_called()
            upload.unlink()
            picture.unlink()
            self.assertEqual(len(list_personas(root)), 1)
            self.assertIn("&lt;Singer&gt;", render_personas(root))
            self.assertIn("Profile picture for &lt;Singer&gt;", render_personas(root))
            self.assertEqual(persona_inputs(root, persona["id"], "Jazz")[2], "Jazz")
            with self.assertRaises(ValueError):
                load_persona(root, "../outside")
            with self.assertRaises(ValueError):
                create_persona(root, "", "")
