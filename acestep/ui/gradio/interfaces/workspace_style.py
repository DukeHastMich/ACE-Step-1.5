"""Responsive music-workspace theme and scoped layout styles."""

import gradio as gr


def workspace_theme():
    """Use the same dark studio palette in light and dark browser modes."""
    colors = {
        "body_background_fill": "#101014", "body_text_color": "#ededf2",
        "body_text_color_subdued": "#a5a5b4", "block_background_fill": "#18181f",
        "block_border_color": "#30303a", "block_label_text_color": "#d9d9e3",
        "block_title_text_color": "#ededf2", "block_label_background_fill": "#18181f", "input_background_fill": "#111117",
        "input_border_color": "#34343f", "input_placeholder_color": "#8c8c9c",
        "button_primary_background_fill": "#ee985d",
        "button_primary_background_fill_hover": "#ffad74",
        "button_primary_text_color": "#19120c", "button_primary_border_color": "#ee985d",
        "button_secondary_background_fill": "#25252f",
        "button_secondary_background_fill_hover": "#343440",
        "button_secondary_text_color": "#ededf2", "button_secondary_border_color": "#3c3c48",
    }
    values = {key + suffix: value for key, value in colors.items() for suffix in ("", "_dark")}
    return gr.themes.Soft(primary_hue="orange", neutral_hue="slate").set(**values)


WORKSPACE_CSS = """
.gradio-container {max-width: none !important; width: 100% !important; padding: 20px 28px !important;}
.main-header {text-align: left !important; margin: 0 !important; padding: 4px 340px 12px 0;}
.main-header h1 {font-size: 24px !important; letter-spacing: -.7px; margin: 0 !important;}
.main-header p {color: #a5a5b4; font-size: 13px; margin: 5px 0 0 !important;}
#ace-workspace {gap: 24px; align-items: stretch; flex-wrap: nowrap; width:100%;}
#ace-create-pane, #ace-library-pane {background: #18181f; border: 1px solid #30303a;
    border-radius: 18px; padding: 20px; min-width: 0 !important;
    height:var(--ace-pane-height, calc(100dvh - 270px)); box-sizing:border-box;
    overflow-y:auto !important; overflow-x:hidden !important; flex-wrap:nowrap !important;
    scrollbar-width:thin; scrollbar-color:#454550 transparent;}
#ace-create-pane {flex: 0 0 32% !important; max-height:none;
    flex-wrap: nowrap !important; overflow-y: auto !important; overflow-x: hidden !important;
    scrollbar-width: thin; scrollbar-color: #454550 transparent;}
#ace-create-pane > *, #ace-library-pane > * {flex-shrink: 0 !important;}
#ace-library-pane {flex: 1 1 0 !important;}
#ace-workspace h2 {font-size: 22px; letter-spacing: -.5px; margin: 0 0 8px;}
#ace-create-pane textarea {font-size: 14px; line-height: 1.55;}
#ace-song-title input {background:#111117 !important; color:#ededf2 !important;
    border:1px solid #34343f !important; font-size:14px;}
#ace-create-pane .block {min-width: 0 !important;}
#ace-create-pane .form {min-width: 0 !important;}
#ace-create-pane .gradio-radio label {padding: 7px 10px; font-size: 12px;}
#ace-create-pane .gradio-radio .wrap {gap: 5px;}
#ace-create-pane .icon-btn-wrap {max-width: none;}
#ace-generate-controls {position: static; background: #18181f;
    padding: 12px 0 20px; border-top: 1px solid #30303a;}
#acestep-generate-btn {width: 100%; min-height: 48px; font-weight: 700;
    background: linear-gradient(110deg, #f6b774, #ed8868); color: #20150f; border: 0;}
#ace-song-list {border-radius: 12px; overflow: hidden;}
#ace-song-list table {font-size: 13px; background: #22222b !important;}
#ace-song-list td {cursor: pointer; height: 52px; background: #18181f; color: #ededf2;}
#ace-song-list th {background: #22222b; color: #b9b9c7;}
#ace-song-list th button, #ace-song-list thead td, #ace-song-list thead button {
    background: #22222b !important; color: #b9b9c7 !important;}
#ace-song-list td:hover {background: #30303b;}
#ace-library-player {margin-top: 12px;}
/* Waveform canvases must not determine their own parent width on redraw. */
#ace-library-pane .ace-take-row {flex-direction: column; flex-wrap: nowrap;
    align-items: stretch; min-width: 0; width: 100%;}
#ace-library-pane .ace-take {flex: 0 0 auto !important; min-width: 0 !important;
    width: 100%; max-width: 100%; box-sizing: border-box;
    border: 1px solid #34343f; border-radius: 12px; padding: 12px;}
#ace-library-pane .ace-take > .block {min-width: 0 !important; max-width: 100%;}
.ace-art-upload {min-height:160px; position:relative;
    background:linear-gradient(135deg,#33415f,#382747) !important; border-radius:12px !important;}
.ace-art-upload::after {content:"\\21A5"; position:absolute; right:12px; bottom:12px;
    width:28px; height:28px; line-height:28px; text-align:center; border-radius:7px;
    background:#171720aa; color:#eee; font-size:22px; pointer-events:none;}
.library-hint {color: #a5a5b4; font-size: 13px;}
/* Remove Gradio's separate inner 1280px cap as well as the outer cap. */
.gradio-container > main {max-width:none !important; width:100% !important; padding:0 !important;}
.gradio-container footer {position:absolute !important; top:24px; right:28px;
    width:auto !important; margin:0 !important; padding:0 !important; z-index:200; gap:10px;}
#ace-song-list .song-rows {max-height:max(260px, calc(var(--ace-pane-height, 650px) - 220px));}

@media (max-width: 900px) {
    .gradio-container {padding: 12px !important;}
    #ace-workspace {flex-wrap: wrap; gap: 14px;}
    #ace-create-pane, #ace-library-pane {flex: 1 1 100% !important; width: 100%;
        max-height: none; height:auto; padding: 14px;}
    #ace-generate-controls {position: static;}
    .main-header {padding-right:0; padding-bottom:40px;}
    .gradio-container footer {top:78px; left:12px; right:auto; font-size:11px;}
    #ace-song-list .song-rows {max-height:60dvh;}
}
"""




from .library_player import PLAYER_CSS
WORKSPACE_CSS += PLAYER_CSS

from .library_track_view import TRACK_CSS
WORKSPACE_CSS += TRACK_CSS

WORKSPACE_CSS += """
#ace-create-pane .ace-create-card {background:#1b1b21; border:1px solid #303039;
    border-radius:14px; padding:12px; margin-bottom:12px;}
#ace-source-audio {flex-wrap:wrap;}
#ace-source-audio > .form, #ace-source-audio > .block {min-width:0 !important;}
"""
