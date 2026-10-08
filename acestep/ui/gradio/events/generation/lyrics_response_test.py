"""Regression checks for blank enhancement inputs and caption/lyric routing."""
import unittest
from collections import defaultdict
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from .lyrics_response import clean_lyrics_response
from . import llm_format_actions as actions
from ..wiring.generation_text_format_wiring import register_generation_text_format_handlers


class EnhancementTests(unittest.TestCase):
    """Do not load models to validate text preservation and event contracts."""

    def test_empty_inputs_never_invoke_model_or_replace_fields(self):
        """Empty, missing, and whitespace-only target text yield a friendly no-op."""
        for fn, target in ((actions.handle_format_caption, "caption"),
                           (actions.handle_format_lyrics, "lyrics")):
            for value in (None, "", "  \n"):
                with self.subTest(target=target, value=value), \
                     patch.object(actions, "format_sample") as model, \
                     patch.object(actions.gr, "Warning"):
                    params = dict(llm_handler=SimpleNamespace(llm_initialized=True),
                                  caption="Folk", lyrics="Existing words", bpm=100,
                                  audio_duration=30, key_scale="C major", time_signature="4",
                                  lm_temperature=.85, lm_top_k=0, lm_top_p=.9)
                    params[target] = value
                    result = fn(**params)
                    self.assertEqual(len(result), 8)
                    self.assertTrue(all(item == {"__type__": "update"} for item in result[:7]))
                    model.assert_not_called()

    def test_extract_lyrics_without_caption(self):
        """Explicit sections are separated; caption-only responses are rejected."""
        self.assertEqual(clean_lyrics_response("# Caption\nFolk\n# Lyrics\n[Verse]\nHome again", "Folk"),
                         "[Verse]\nHome again")
        self.assertIsNone(clean_lyrics_response("# Caption\nA folk song", "Folk"))
        self.assertIsNone(clean_lyrics_response("A folk song", "A folk song"))
        self.assertIsNone(clean_lyrics_response("", "Folk"))
        self.assertEqual(clean_lyrics_response("[Chorus]\nSing with me", "Folk"), "[Chorus]\nSing with me")

    def test_buttons_target_the_correct_textbox(self):
        """Caption and lyric controls bind the correct handler and output ordering."""
        generation = defaultdict(MagicMock)
        results = defaultdict(MagicMock)
        context = SimpleNamespace(generation_section=generation, results_section=results,
                                  llm_handler=object())
        register_generation_text_format_handlers(context, [], [])
        for target, button, handler in (("captions", "format_caption_btn", "handle_format_caption"),
                                        ("lyrics", "format_lyrics_btn", "handle_format_lyrics")):
            event = generation[button].click.call_args.kwargs
            self.assertIs(event["outputs"][0], generation[target])
            self.assertEqual(len(event["inputs"]), 10)
            self.assertEqual(len(event["outputs"]), 8)
            with patch("acestep.ui.gradio.events.wiring.generation_text_format_wiring.gen_h." + handler) as fn:
                event["fn"](*range(10))
                fn.assert_called_once_with(context.llm_handler, *range(10))
