"""Check Retake is discoverable and independent of Edit visibility."""
import unittest
import gradio as gr
from .generation_tab_variation_morph_controls import build_variation_morph_controls


class RetakeVisibilityTests(unittest.TestCase):
    """Build controls without model initialization."""

    def test_retake_is_not_inside_edit_column(self):
        """Hiding unsupported Edit must not hide the Retake checkbox."""
        with gr.Blocks() as demo:
            controls = build_variation_morph_controls()
        self.assertIn("Retake & Variance", controls["variation_group"].label)
        self.assertTrue(controls["variation_group"].open)
        def find(node, identity):
            if node.get("id") == identity:
                return node
            for child in node.get("children", []):
                result = find(child, identity)
                if result:
                    return result
        layout = demo.get_config_file()["layout"]
        edit = find(layout, controls["flow_edit_column"]._id)
        self.assertIsNotNone(find(edit, controls["flow_edit_morph"]._id))
        self.assertIsNone(find(edit, controls["retake_enabled"]._id))
        handler = next(fn.fn for fn in demo.fns.values()
                       if fn.inputs == [controls["retake_enabled"]])
        self.assertTrue(handler(True)["visible"])
        self.assertFalse(handler(False)["visible"])
