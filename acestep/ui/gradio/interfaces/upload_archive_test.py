"""Persistent upload and recording archive regression tests."""
from pathlib import Path
import tempfile
import unittest
import gradio as gr
from .upload_archive_store import archive_audio, list_uploads, load_upload
from .upload_archive_controls import create_upload_archive


class UploadArchiveTests(unittest.TestCase):
    """Use disposable audio fixtures, without any model initialization."""

    def test_copy_deduplicate_and_reuse_after_temp_removed(self):
        """A stopped recording remains available after Gradio's temporary file is gone."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "uploads"
            source = Path(directory) / "recording.wav"
            source.write_bytes(b"RIFF" + b"audio" * 20)
            first = archive_audio(source, root)
            self.assertEqual(first, archive_audio(source, root))
            source.unlink()
            self.assertEqual(len(list_uploads(root)), 1)
            self.assertEqual(Path(load_upload(first["id"], root)["path"]).read_bytes(), b"RIFF" + b"audio" * 20)
            with self.assertRaises(ValueError):
                load_upload("../outside", root)
            self.assertIsNone(archive_audio(None, root))

    def test_every_audio_input_captures_uploads_and_recordings(self):
        """Source, reference, code hints and persona audio all bind both user events."""
        with tempfile.TemporaryDirectory() as directory, gr.Blocks() as demo:
            generation = {key: gr.Audio(type="filepath") for key in
                          ("src_audio", "reference_audio", "lm_codes_audio_upload")}
            generation["generation_mode"] = gr.Radio(["Custom", "Remix"])
            generation["src_audio_row"] = gr.Row()
            persona = gr.Audio(type="filepath")
            create_upload_archive(demo, generation, [persona], Path(directory))
        handlers = [fn for fn in demo.fns.values() if fn.fn.__name__ == "capture"]
        self.assertEqual(len(handlers), 8)
        for component in [generation[key] for key in
                          ("src_audio", "reference_audio", "lm_codes_audio_upload")] + [persona]:
            events = {event for fn in handlers for identity, event in fn.targets if identity == component._id}
            self.assertEqual(events, {"upload", "stop_recording"})
