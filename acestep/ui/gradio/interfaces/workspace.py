"""Two-pane music workspace built from the existing generation and result controls."""

import gradio as gr
from pathlib import Path
from acestep.ui.gradio.events.results.generation_info import DEFAULT_RESULTS_DIR
from .persona_controls import create_persona_controls

from acestep.ui.gradio.i18n import t
from .generation_tab_section import create_generation_tab_section
from .result import create_results_section
from .song_library import create_song_library
from .workspace_sizing import SIZING_JS


def create_workspace(demo, dit_handler, llm_handler, init_params, language):
    """Keep Create on the left and library/current takes on the right."""
    service_mode = bool(init_params and init_params.get("service_mode"))
    with gr.Row(elem_id="ace-workspace", equal_height=False):
        with gr.Column(scale=4, min_width=340, elem_id="ace-create-pane"):
            gr.Markdown(t("workspace.create_heading"))
            generation = create_generation_tab_section(
                dit_handler, llm_handler, init_params=init_params, language=language)
        with gr.Column(scale=7, min_width=460, elem_id="ace-library-pane"):
            gr.Markdown(t("workspace.library_heading"))
            with gr.Tabs(selected="takes" if service_mode else "library") as right_tabs:
                # Keep the existing result dictionary intact for generation event wiring.
                with gr.Tab(t("workspace.current_takes"), id="takes"):
                    with gr.Column() as results_wrapper:
                        results = create_results_section(dit_handler)
                if not service_mode:
                    with gr.Tab(t("workspace.saved_songs"), id="library"):
                        table, catalog = create_song_library(demo, generation, results)
                    with gr.Tab("Personas", id="personas"):
                        create_persona_controls(demo, generation, table, catalog, right_tabs, Path(DEFAULT_RESULTS_DIR))
    generation["results_wrapper"] = results_wrapper
    generation["generate_btn"].click(
        lambda: gr.update(selected="takes"), outputs=[right_tabs], queue=False)
    demo.load(fn=None, js=SIZING_JS)
    return generation, results
