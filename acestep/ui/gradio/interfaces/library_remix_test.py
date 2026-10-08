"""Check menu remix identity and backward-compatible metadata loading."""
import json
from pathlib import Path
import tempfile
import unittest

import gradio as gr
from .library_remix import remix_values, wire_remix_action


class RemixTests(unittest.TestCase):
    """Use distinct temporary songs to catch stale selection errors."""

    def test_menu_loads_clicked_track_and_legacy_metadata(self):
        """Menu selection restores title/style/lyrics and source without prior selection."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            audio = root / "second.wav"
            audio.write_bytes(b"audio")
            audio.with_suffix(".json").write_text(json.dumps({
                "title": "Second", "caption": "Jazz", "lyrics": "Words"}))
            with gr.Blocks() as demo:
                table, catalog, button, selection = gr.HTML(), gr.State([]), gr.Button(), gr.State("")
                keys = ("generation_mode", "src_audio", "captions", "lyrics", "song_title", "simple_query_input")
                generation = {key: gr.Textbox() for key in keys}
                generation["src_audio_row"] = gr.Row(visible=False)
                wire_remix_action(table, catalog, button, selection, root, generation)
            handler = next(fn.fn for fn in demo.fns.values() if fn.fn.__name__ == "from_menu")
            self.assertEqual(handler([], gr.EventData(None, None)),
                             tuple(gr.skip() for _ in range(7)))
            result = handler([{"path": audio.name}], gr.EventData(None, {"song_id": audio.name}))
            self.assertEqual((result[0], result[1]["value"], *result[2:6]), ("Remix", str(audio), "Jazz", "Words", "Second", ""))
            self.assertTrue(result[6]["visible"])
            remastered = handler([{"path": audio.name}],
                gr.EventData(None, {"song_id": audio.name, "action": "remaster"}))
            self.assertEqual((remastered[0], remastered[1]["value"], *remastered[2:4]), ("Remaster", str(audio), "Jazz", "Words"))
            self.assertEqual(remastered[4], "Second (Remaster)")
            with self.assertRaises(gr.Error):
                handler([], gr.EventData(None, {"song_id": audio.name}))

    def test_saved_empty_text_does_not_restore_generated_text(self):
        """Explicit original blanks remain blank instead of picking up model-written lyrics."""
        with tempfile.TemporaryDirectory() as directory:
            audio = Path(directory) / "song.wav"
            audio.write_bytes(b"audio")
            audio.with_suffix(".json").write_text(json.dumps({
                "lyrics": "Generated", "remix_inputs": {"lyrics": "", "prompt": "Stars"}}))
            values = remix_values(Path(directory), audio.name)
            self.assertEqual(values[3], "")
            self.assertEqual(values[5], "Stars")
