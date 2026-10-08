"""Verify model-using generation and enhancement events share one exclusive queue."""
import ast
from pathlib import Path
import unittest


class ModelConcurrencyTests(unittest.TestCase):
    """Inspect actual event registration without loading CUDA models."""

    def test_generation_enhancement_and_autogen_cannot_overlap(self):
        """All five inference registrations must use the same queued concurrency group."""
        found = []
        for filename in ("generation_run_wiring.py", "generation_text_format_wiring.py",
                         "generation_batch_navigation_wiring.py"):
            tree = ast.parse(Path(__file__).with_name(filename).read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                keywords = {item.arg: item.value for item in node.keywords}
                function = ast.unparse(keywords.get("fn", ast.Constant(None)))
                if not any(name in function for name in (
                    "generation_wrapper", "generate_next_batch_background",
                    "handle_format_caption", "handle_format_lyrics")):
                    continue
                with self.subTest(file=filename, handler=function):
                    self.assertEqual(ast.literal_eval(keywords["concurrency_id"]), "ace-model-inference")
                    self.assertEqual(ast.literal_eval(keywords["concurrency_limit"]), 1)
                    self.assertIs(ast.literal_eval(keywords["queue"]), True)
                    found.append(function)
        self.assertEqual(len(found), 5)
