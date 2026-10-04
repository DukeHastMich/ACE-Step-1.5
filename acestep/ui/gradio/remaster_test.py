"""Verify source retention and new-version persistence for remaster presets."""
import inspect
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from acestep.inference import GenerationParams
from acestep.ui.gradio.remaster import apply_remaster, PRESETS
from acestep.ui.gradio.events.results import generation_progress as progress


class RemasterTests(unittest.TestCase):
    """Exercise real parameter construction and saving with inference stubbed out."""

    def test_presets_keep_source_and_disable_conflicting_edits(self):
        """Increasing variation adds noise while retaining full source conditioning."""
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.wav"
            source.write_bytes(b"original")
            strengths = []
            for preset in PRESETS:
                params = GenerationParams(src_audio=str(source), caption="Folk", lyrics="Words",
                    flow_edit_morph=True, retake_variance=1.0, thinking=True)
                apply_remaster(params, preset)
                self.assertEqual(params.audio_cover_strength, 1.0)
                self.assertEqual((params.caption, params.lyrics), ("Folk", "Words"))
                self.assertEqual(params.task_type, "cover")
                self.assertFalse(params.flow_edit_morph)
                self.assertFalse(params.thinking)
                self.assertEqual(params.retake_variance, 0)
                self.assertEqual(params.shift, 1.0)
                strengths.append(params.cover_noise_strength)
            self.assertGreater(strengths[0], strengths[1])
            self.assertGreater(strengths[1], strengths[2])
            with self.assertRaises(ValueError):
                apply_remaster(params, "Unknown")
        with self.assertRaises(ValueError):
            apply_remaster(GenerationParams(), "Subtle")

    def test_generation_saves_new_audio_and_remaster_lineage(self):
        """Real save path leaves original bytes untouched and records the applied preset."""
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "original.wav"
            source.write_bytes(b"original")
            kwargs = {name: None for name, param in inspect.signature(
                progress.generate_with_progress).parameters.items() if param.default is inspect.Parameter.empty}
            kwargs.update(src_audio=str(source), captions="Folk", lyrics="Words", task_type="cover",
                song_title="Song (Remaster)", remaster_preset="Normal", audio_format="wav",
                inference_steps=8, progress=lambda *args: None)
            result = SimpleNamespace(success=True, extra_outputs={}, status_message="Done", audios=[
                dict(key="new-take", tensor=None, sample_rate=44100, params={"caption": "Folk"})])

            def save(**options):
                """Write an identifiable result through the real output naming path."""
                Path(options["output_path"]).write_bytes(b"remastered")
                return options["output_path"]

            with patch.object(progress, "DEFAULT_RESULTS_DIR", directory), \
                 patch.object(progress, "get_global_gpu_config", return_value=SimpleNamespace(save_memory_mode=False)), \
                 patch.object(progress, "parse_and_validate_timesteps", return_value=(None, False, None)), \
                 patch.object(progress, "generate_music", return_value=result) as generate, \
                 patch.object(progress, "save_audio", side_effect=save):
                list(progress.generate_with_progress(**kwargs))
            actual = generate.call_args.kwargs["params"]
            self.assertEqual(actual.cover_noise_strength, .75)
            self.assertEqual(actual.src_audio, str(source))
            self.assertFalse(actual.thinking)
            sidecar = next(Path(directory).rglob("new-take.json"))
            metadata = json.loads(sidecar.read_text())
            self.assertEqual(metadata["remaster"]["preset"], "Normal")
            self.assertEqual(metadata["remaster"]["source_audio"], str(source))
            self.assertEqual(sidecar.with_suffix(".wav").read_bytes(), b"remastered")
            self.assertEqual(source.read_bytes(), b"original")
