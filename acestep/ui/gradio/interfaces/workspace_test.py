"""Verify workspace composition preserves existing component maps and service isolation."""

import unittest
from unittest.mock import MagicMock, patch

import gradio as gr

from acestep.ui.gradio.interfaces.workspace import create_workspace
from acestep.ui.gradio.interfaces.workspace_style import workspace_theme


class WorkspaceTests(unittest.TestCase):
    """Build the real layout with lightweight generation controls."""

    def build(self, service_mode):
        """Build one workspace without loading any models."""
        module = "acestep.ui.gradio.interfaces.workspace"
        with gr.Blocks() as demo:
            generate = gr.Button("Generate")
            generation = {"generate_btn": generate, "preserved": object()}
            results = {"existing_result": object()}
            with patch(module + ".create_generation_tab_section", return_value=generation), \
                 patch(module + ".create_results_section", return_value=results), \
                 patch(module + ".create_song_library", return_value=(None, None)) as library, \
                 patch(module + ".create_persona_controls"), \
                 patch(module + ".create_upload_archive"):
                returned = create_workspace(
                    demo, MagicMock(), MagicMock(), {"service_mode": service_mode}, "en")
        return demo, generation, results, returned, library

    def test_local_layout_preserves_generation_contract(self):
        """The two panes preserve every existing control for downstream wiring."""
        demo, generation, results, returned, library = self.build(False)
        self.assertIs(returned[0], generation)
        self.assertIs(returned[1], results)
        self.assertIn("results_wrapper", generation)
        library.assert_called_once()
        ids = {getattr(block, "elem_id", None) for block in demo.blocks.values()}
        self.assertTrue({"ace-create-pane", "ace-library-pane"}.issubset(ids))

    def test_service_mode_does_not_expose_shared_library(self):
        """Hosted users retain results but cannot browse the machine's saved songs."""
        _, _, results, returned, library = self.build(True)
        library.assert_not_called()
        self.assertIs(returned[1], results)

    def test_theme_builds(self):
        """The installed Gradio version accepts the studio palette."""
        self.assertIsNotNone(workspace_theme())


if __name__ == "__main__":
    unittest.main()
