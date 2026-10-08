"""Upload archive browsing, auditioning and reuse in Create."""
import gradio as gr
from .upload_archive_store import archive_audio, list_uploads, load_upload, UPLOAD_ROOT


def create_upload_archive(demo, generation, extra_audio=(), root=UPLOAD_ROOT):
    """Archive user uploads and recordings without copying generated-track selections."""
    gr.Markdown("### Upload archive\nUploaded and recorded audio is saved locally in the project's uploads folder.")
    incoming = gr.File(label="Add audio to archive", file_types=["audio"], file_count="multiple", type="filepath")
    selector = gr.Dropdown(label="Archived uploads", choices=[], interactive=True)
    refresh = gr.Button("Refresh archive")
    player = gr.Audio(label="Upload preview", type="filepath", interactive=False, buttons=["download"])
    with gr.Row():
        source_button = gr.Button("Use as source (Remix)")
        reference_button = gr.Button("Use as reference")
    status = gr.Textbox(label="Archive status", interactive=False)

    def choices(selected=None):
        """Refresh the visible catalog from persistent storage."""
        return gr.update(choices=[(item["name"], item["id"]) for item in list_uploads(root)], value=selected)

    def capture(path):
        """Replace transient input with the durable copy after upload or recording."""
        try:
            item = archive_audio(path, root)
            if item is None:
                return gr.skip(), gr.skip(), gr.skip()
            return item["path"], choices(item["id"]), "Saved to upload archive."
        except (OSError, ValueError) as exc:
            gr.Warning(str(exc))
            return gr.skip(), gr.skip(), str(exc)

    def add_files(paths):
        """Persist files uploaded directly to the archive tab."""
        selected = None
        try:
            for path in paths or []:
                selected = archive_audio(path, root)["id"]
            return choices(selected), "Uploads saved."
        except (OSError, ValueError) as exc:
            return choices(selected), str(exc)

    def preview(identity):
        """Load the selected archived file through Gradio's audio serving cache."""
        if not identity:
            return None
        try:
            return load_upload(identity, root)["path"]
        except (OSError, ValueError, KeyError) as exc:
            raise gr.Error(str(exc)) from exc

    def use_source(identity):
        """Load a named source into Remix without overwriting song text."""
        path = preview(identity)
        if not path:
            raise gr.Error("Select an archived upload first.")
        name = load_upload(identity, root)["name"]
        return "Remix", gr.update(value=path, label="Source Audio — " + name), gr.update(visible=True)

    def use_reference(identity):
        """Load the selected reference and keep existing prompts and lyrics."""
        path = preview(identity)
        if not path:
            raise gr.Error("Select an archived upload first.")
        return "Custom", path

    inputs = [generation[key] for key in ("src_audio", "reference_audio", "lm_codes_audio_upload")]
    for component in [*inputs, *extra_audio]:
        for event in (component.upload, component.stop_recording):
            event(capture, inputs=[component], outputs=[component, selector, status],
                  concurrency_id="upload-archive", concurrency_limit=1)
    incoming.upload(add_files, inputs=[incoming], outputs=[selector, status],
                    concurrency_id="upload-archive", concurrency_limit=1)
    selector.change(preview, inputs=[selector], outputs=[player])
    source_button.click(use_source, inputs=[selector], outputs=[generation["generation_mode"],
                        generation["src_audio"], generation["src_audio_row"]])
    reference_button.click(use_reference, inputs=[selector], outputs=[generation["generation_mode"],
                           generation["reference_audio"]])
    refresh.click(choices, outputs=[selector])
    demo.load(choices, outputs=[selector])
