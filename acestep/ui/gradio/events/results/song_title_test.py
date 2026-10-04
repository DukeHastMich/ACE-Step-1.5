"""Verify title persistence through saves, batches, and library rendering."""
import inspect
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from _batch_management_test_support import build_progress_result, load_batch_management_module
from batch_management_test import _build_call_kwargs
from acestep.ui.gradio.events.results import generation_progress as progress_module
from acestep.ui.gradio.interfaces.library_store import scan_songs
from acestep.ui.gradio.interfaces.library_rows import render_song_rows


class SongTitleTests(unittest.TestCase):
    """Exercise the real sidecar writer with model inference stubbed out."""

    def test_generated_title_and_style_survive_save(self):
        """Every take is titled before it becomes visible, with the caption kept separate."""
        with tempfile.TemporaryDirectory() as temporary:
            kwargs = {name: None for name, parameter in
                      inspect.signature(progress_module.generate_with_progress).parameters.items()
                      if parameter.default is inspect.Parameter.empty}
            kwargs.update(captions="folk with strings", lyrics="", task_type="text2music",
                          audio_format="wav", song_prompt="A song about stars", song_title='  Midnight\n <Sky>  ',
                          inference_steps=8, progress=lambda *args: None)
            result = SimpleNamespace(success=True, extra_outputs={}, status_message="Done", audios=[
                dict(key=f"take-{i}", tensor=None, sample_rate=44100,
                     params={"caption": "folk with strings", "lyrics": "hello"}) for i in range(2)])

            def save(**options):
                """Create placeholder audio while retaining the real sidecar-writing path."""
                Path(options["output_path"]).write_bytes(b"test audio")
                return options["output_path"]

            with patch.object(progress_module, "DEFAULT_RESULTS_DIR", temporary), \
                 patch.object(progress_module, "get_global_gpu_config",
                              return_value=SimpleNamespace(save_memory_mode=False)), \
                 patch.object(progress_module, "parse_and_validate_timesteps", return_value=(None, False, None)), \
                 patch.object(progress_module, "generate_music", return_value=result), \
                 patch.object(progress_module, "save_audio", side_effect=save):
                for update in progress_module.generate_with_progress(**kwargs):
                    if isinstance(update[8], list):
                        for file in update[8]:
                            if file.endswith(".json"):
                                self.assertEqual(json.loads(Path(file).read_text())["title"], "Midnight <Sky>")
            from acestep.ui.gradio.interfaces.library_remix import remix_values
            for audio in Path(temporary).rglob("*.wav"):
                restored = remix_values(Path(temporary), str(audio.relative_to(temporary)))
                self.assertEqual(restored[1], str(audio))
                self.assertEqual(restored[2], "folk with strings")
                self.assertEqual(restored[5], "A song about stars")
            songs = scan_songs(Path(temporary))
            self.assertEqual(len(songs), 2)
            self.assertTrue(all(s["title"] == "Midnight <Sky>" for s in songs))
            html = render_song_rows(songs)
            self.assertIn("Midnight &lt;Sky&gt;", html)
            self.assertIn("folk with strings", html)
            self.assertEqual(len(scan_songs(Path(temporary), "Midnight")), 2)
            self.assertEqual(len(scan_songs(Path(temporary), "folk with strings")), 2)

    def test_foreground_preserves_title_for_automatic_batches(self):
        """The captured request title reaches saving and subsequent AutoGen parameters."""
        module, state = load_batch_management_module(is_windows=True)
        seen = {}

        def generate(*args, **kwargs):
            """Capture the title delivered to the audio save generator."""
            seen.update(kwargs)
            yield build_progress_result(length=48)

        kwargs = _build_call_kwargs(module)
        kwargs["song_title"] = "Night drive"
        kwargs["song_prompt"] = "Neon roads"
        kwargs["remaster_preset"] = "Subtle"
        with patch.dict(module.generate_with_batch_management.__globals__, {"generate_with_progress": generate}):
            outputs = list(module.generate_with_batch_management(None, None, **kwargs))
        self.assertEqual(seen["song_title"], "Night drive")
        self.assertEqual(seen["song_prompt"], "Neon roads")
        self.assertEqual(seen["remaster_preset"], "Subtle")
        self.assertEqual(outputs[-1][49]["remaster_preset"], "Subtle")
        self.assertEqual(state["store_calls"][0]["generation_params"]["song_title"], "Night drive")
        self.assertEqual(outputs[-1][49]["song_title"], "Night drive")

    def test_background_title_reaches_save_generator(self):
        """Automatic batches keep the initial title rather than the live textbox value."""
        module, _ = load_batch_management_module(is_windows=False)
        seen = {}

        def generate(*args, **kwargs):
            """Capture background generation input."""
            seen.update(kwargs)
            yield build_progress_result(length=48)

        with patch.dict(module.generate_next_batch_background.__globals__, {"generate_with_progress": generate}):
            module.generate_next_batch_background(None, None, True,
                {"song_title": "Night drive", "remaster_preset": "High", "batch_size_input": 2, "allow_lm_batch": False},
                0, 1, {}, False)
        self.assertEqual(seen["song_title"], "Night drive")
        self.assertEqual(seen["remaster_preset"], "High")


if __name__ == "__main__":
    unittest.main()
