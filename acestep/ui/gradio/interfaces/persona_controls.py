"""Persona creation, auditioning, and one-click loading into Create."""
from html import escape
from pathlib import Path
from urllib.parse import quote

import gradio as gr

from .library_stem_controls import requested_song
from .persona_store import create_persona, list_personas, persona_inputs, persona_root, load_persona

PERSONA_JS = """
element.addEventListener('click', event => {
    const button = event.target.closest('button[data-persona]');
    if (button) trigger('select', {index:button.dataset.persona, value:button.dataset.persona});
});
element.addEventListener('play', event => {
    if (event.target.tagName === 'AUDIO') {
        document.querySelectorAll('audio').forEach(a => {if (a !== event.target) a.pause();});
    }
}, true);
"""
PERSONA_CSS = """
.persona-card {display:flex; flex-wrap:wrap; align-items:center; gap:16px; padding:16px;
 border:1px solid #34343f; border-radius:12px; margin:12px 0; background:#1c1c24;}
.persona-picture {width:64px; height:64px; flex:0 0 64px; border-radius:12px; object-fit:cover; display:grid; place-items:center; background:linear-gradient(135deg,#674674,#315975); color:#eee; font-size:24px;}
.persona-card button {flex:1; min-width:150px; background:none; border:0; color:#eee;
 text-align:left; cursor:pointer; padding:8px;}
.persona-card strong,.persona-card small {display:block;}
.persona-card small {color:#aaa; margin-top:6px; white-space:pre-wrap;}
.persona-card audio {width:260px; max-width:100%; height:36px; color-scheme:dark;}
"""


def render_personas(root):
    """Render names as load buttons and a separate vocal audition player."""
    rows = []
    for persona in list_personas(root):
        url = "gradio_api/file=" + quote(Path(persona["audio_path"]).as_posix(), safe="/")
        name = escape(persona["name"], quote=True)
        artwork = persona_root(root) / persona["id"] / "cover.png"
        picture = '<span class="persona-picture" aria-hidden="true">♫</span>'
        if artwork.is_file() and artwork.resolve().is_relative_to(persona_root(root)):
            art_url = "gradio_api/file=" + quote(artwork.as_posix(), safe="/")
            picture = f'<img class="persona-picture" src="{escape(art_url, quote=True)}" alt="Profile picture for {name}">'
        rows.append(f'<div class="persona-card">{picture}<button data-persona="{persona["id"]}" '
            f'aria-label="Use persona {name}"><strong>{name}</strong>'
            f'<small>{escape(persona["description"]) or "Vocal reference"}</small>'
            f'<small>Click to use in Create</small></button>'
            f'<audio controls preload="none" aria-label="Preview {name}" src="{escape(url, quote=True)}"></audio></div>')
    return "".join(rows) or "<p>No personas yet. Create one from a track or upload a vocal reference below.</p>"


def create_persona_controls(demo, generation, table, catalog, tabs, root):
    """Wire the library action to a persistent persona form and independent previews."""
    gr.Markdown("### Personas\nClick a name to load its vocal reference into Create. Use Play to hear the voice.")
    cards = gr.HTML(value="", js_on_load=PERSONA_JS, css_template=PERSONA_CSS)
    refresh = gr.Button("Refresh personas")
    previous_voice = gr.State("")
    with gr.Accordion("Create a persona", open=True):
        source = gr.State("")
        source_name = gr.Textbox(label="Source track", interactive=False, value="Upload vocals or choose Create Persona on a library track.")
        name = gr.Textbox(label="Persona name", max_lines=1)
        description = gr.Textbox(label="Voice description", lines=3,
            placeholder="Warm baritone, breathy delivery, gentle vibrato…")
        upload = gr.Audio(label="Or upload an isolated vocal reference", type="filepath", interactive=True)
        artwork = gr.Image(label="Persona profile picture", type="filepath", format="png",
                           height=180, interactive=True, sources=["upload"], elem_classes="ace-art-upload")
        gr.Markdown("Drop or browse for a profile picture. Leave empty to use the source track artwork.")
        save = gr.Button("Create persona", variant="primary")
        status = gr.Textbox(label="Persona status", interactive=False)

    def prepare(songs, event: gr.EventData):
        """Open creation for the clicked source, without extracting until requested."""
        if not isinstance(event._data, dict) or event._data.get("action") != "persona":
            return (gr.skip(),) * 7
        song = requested_song(songs, event.song_id)
        return (song["path"], song["title"],
                song["title"][:120], "", None, None, "Name this voice, then create it. Demucs extracts vocals if needed.")

    def save_persona(title, voice, relative, audio, picture):
        """Report separation progress and publish the new persona when complete."""
        yield gr.skip(), "Creating persona — extracting vocals if needed…"
        try:
            created = create_persona(root, title, voice, relative, audio or "", picture or "")
            yield render_personas(root), f'Created {created["name"]}. Click its name above to use it.'
        except (OSError, ValueError, RuntimeError) as exc:
            yield gr.skip(), str(exc)

    def use_persona(caption, previous, event: gr.SelectData):
        """Load reference and voice guidance without replacing lyrics or source audio."""
        try:
            caption = (caption or "").strip()
            if previous and caption.endswith(previous):
                caption = caption[:-len(previous)].rstrip()
            voice = load_persona(root, event.index)["description"].strip()
            return (*persona_inputs(root, event.index, caption), "Persona loaded into Create.", voice)
        except (OSError, ValueError, KeyError) as exc:
            raise gr.Error(str(exc)) from exc

    table.change(prepare, inputs=[catalog], outputs=[source, source_name, name, description, upload, artwork, status], queue=True, show_progress="hidden")
    save.click(save_persona, inputs=[name, description, source, upload, artwork], outputs=[cards, status],
        concurrency_id="library-demucs", concurrency_limit=1)
    cards.select(use_persona, inputs=[generation["captions"], previous_voice], outputs=[generation["generation_mode"],
        generation["reference_audio"], generation["captions"], status, previous_voice], queue=True)
    refresh.click(lambda: render_personas(root), outputs=[cards], queue=True)
    demo.load(lambda: render_personas(root), outputs=[cards], queue=True)

    return upload
