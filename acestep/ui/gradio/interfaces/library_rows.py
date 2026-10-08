"""Escaped library rows with keyboard-accessible per-track action menus."""

from html import escape
import hashlib
from pathlib import Path
from urllib.parse import quote

from .library_artwork import existing_artwork

from .library_download import download_link


def render_song_rows(songs: list[dict], root: Path | None = None) -> str:
    """Render song identities rather than positions, avoiding stale filtered indices."""
    rows = []
    for song in songs:
        path = escape(song["path"], quote=True)
        title = escape(song["title"], quote=True)
        style = escape(song.get("style", ""), quote=True)
        detail = escape(f'{song["created"]} · {song["duration"]} · {song["format"]}')
        download = download_link(root, song) if root is not None else ""
        artwork = existing_artwork(root, song["path"]) if root is not None else None
        hue = int(hashlib.sha256(song["path"].encode()).hexdigest()[:4], 16) % 360
        thumbnail = (f'<span class="song-art-placeholder" style="--art-hue:{hue}" '
                     'aria-hidden="true">♫</span>')
        if artwork:
            image_path = Path(artwork)
            url = "gradio_api/file=" + quote(image_path.as_posix(), safe="/")
            url += "?v=" + str(image_path.stat().st_mtime_ns)
            thumbnail = f'<img class="song-art" src="{escape(url, quote=True)}" alt="" loading="lazy">'
        rows.append(
            f'<div class="song-row"><span class="song-art-controls">'
            f'<button class="song-art-button" data-play="{path}" aria-label="Play {title}">{thumbnail}</button>'
            f'<button class="art-upload-corner" data-art="{path}" aria-label="Upload artwork for {title}" '
            f'title="Upload artwork">↥</button></span>'
            f'<button class="song-open" data-song="{path}" '
            f'title="{title}"><span class="song-text"><span>{title}</span><small title="{style}">{style or detail}</small></span></button>'
            f'<small class="song-facts" title="{detail}">{escape(song["duration"])} · {escape(song["format"])}</small>'
            f'<details class="song-menu"><summary aria-label="Actions for {title}">⋮</summary>'
            f'<div class="song-actions"><button data-remix="{path}">Remix</button><button data-remaster="{path}">Remaster</button><button data-persona="{path}">Create Persona</button>{download}<div class="stem-branch"><button type="button" data-stem-menu aria-haspopup="true">Get stems ◂</button><div class="stem-submenu"><button data-stems="{path}" data-stem-count="2">2 stems · Vocals + instrumental</button><button data-stems="{path}" data-stem-count="4">4 stems · Vocals, drums, bass, other</button><button data-stems="{path}" data-stem-count="6">6 stems · Adds guitar + piano</button></div></div>'
            f'<button data-folder="{path}">Open folder</button>'
            f'<button data-trash="{path}">Move to trash</button></div></details></div>'
        )
    return '<div class="song-rows">' + "".join(rows) + '</div>' if rows else (
        '<p class="empty-library">No matching songs.</p>')


ROW_SCRIPT = """
element.addEventListener('click', (event) => {
    const persona = event.target.closest('button[data-persona]');
    if (persona) {
        Array.from(document.querySelectorAll('[role=tab]')).find(tab => tab.textContent.trim() === 'Personas')?.click();
        trigger('change', {song_id: persona.dataset.persona, action: 'persona'});
        persona.closest('details').open = false; return;
    }
    const remaster = event.target.closest('button[data-remaster]');
    if (remaster) {
        document.querySelector('#ace-create-pane')?.scrollTo({top:0});
        trigger('change', {song_id: remaster.dataset.remaster, action: 'remaster'});
        remaster.closest('details').open = false;
        return;
    }
    const remix = event.target.closest('button[data-remix]');
    if (remix) {
        document.querySelector('#ace-create-pane')?.scrollTo({top:0});
        trigger('change', {song_id: remix.dataset.remix});
        remix.closest('details').open = false;
        return;
    }
    const play = event.target.closest('button[data-play]');
    if (play) {
        trigger('select', {index: play.dataset.play, value: play.dataset.play, play: true});
        return;
    }
    const artwork = event.target.closest('button[data-art]');
    if (artwork) {
        trigger('select', {index: artwork.dataset.art, value: artwork.dataset.art});
        const picker = document.querySelector('#ace-art-upload input[type="file"]');
        if (picker) picker.click();
        return;
    }
    const folder = event.target.closest('button[data-folder]');
    if (folder) {
        trigger('input', {song_id: folder.dataset.folder});
        folder.closest('details').open = false;
        return;
    }
    const trash = event.target.closest('button[data-trash]');
    if (trash) {
        trigger('submit', {song_id: trash.dataset.trash});
        trash.closest('details').open = false;
        return;
    }
    const stems = event.target.closest('button[data-stems]');
    if (stems) {
        trigger('click', {song_id: stems.dataset.stems, stems: Number(stems.dataset.stemCount || 2)});
        stems.closest('details').open = false;
        return;
    }
    const song = event.target.closest('button[data-song]');
    if (song) trigger('select', {index: song.dataset.song, value: song.dataset.song, detail: true});
});
const fitStems = event => {
    const branch = event.target.closest('.stem-branch');
    if (!branch) return;
    const submenu = branch.querySelector('.stem-submenu');
    submenu.style.marginTop = '0px';
    const box = submenu.getBoundingClientRect(), bounds = element.querySelector('.song-rows').getBoundingClientRect();
    if (getComputedStyle(submenu).position === 'absolute') {
        const shift = Math.max(bounds.top + 4 - box.top, Math.min(0, bounds.bottom - 4 - box.bottom));
        submenu.style.marginTop = shift + 'px';
    }
};
element.addEventListener('pointerover', fitStems);
element.addEventListener('focusin', fitStems);
element.addEventListener('toggle', (event) => {
    if (event.target.tagName === 'DETAILS' && event.target.open) {
        element.querySelectorAll('details[open]').forEach((menu) => {
            if (menu !== event.target) menu.open = false;
        });
    }
}, true);
element.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') element.querySelectorAll('details[open]').forEach((menu) => {
        menu.open = false; menu.querySelector('summary').focus();
    });
});
"""

ROW_CSS = """
.stem-branch {position:relative;}
.stem-submenu {display:none; position:absolute; right:100%; top:50%; transform:translateY(-50%); width:280px;
    background:#292932; border:1px solid #4b4b58; border-radius:10px; padding:6px;
    box-shadow:0 8px 24px #0008; z-index:11;}
.stem-submenu button {font-size:12px; white-space:nowrap;}
.stem-branch:hover > .stem-submenu,.stem-branch:focus-within > .stem-submenu {display:block;}
@media(max-width:650px) {.stem-submenu {position:static; width:auto; transform:none; box-shadow:none;}}

.song-rows {max-height: 420px; overflow-y: auto; padding-bottom: 280px;}
.song-row {display:flex; align-items:center; gap:12px; border-bottom:1px solid #30303a;
    padding:8px 10px; color:#ededf2;}
.song-row:hover {background:#22222b;}
.song-open {display:flex; align-items:center; gap:12px; flex:1; min-width:0; text-align:left; background:transparent; border:0;
    color:inherit; cursor:pointer; padding:6px;}
.song-art-controls {position:relative; flex:0 0 56px; width:56px; height:56px;}
.song-art-button {padding:0; border:0; background:transparent; cursor:pointer; flex:0 0 56px; border-radius:8px;}
.song-text {flex:1; min-width:0;}
.song-art, .song-art-placeholder {width:56px; height:56px; border-radius:8px; flex:0 0 56px; object-fit:cover;}
.song-art-placeholder {display:grid !important; place-items:center; position:relative; background:linear-gradient(135deg,hsl(var(--art-hue) 40% 34%),hsl(var(--art-hue) 30% 18%)); color:#f4f0fa; font-size:23px;}
.art-upload-corner {cursor:pointer; border:0; padding:0; color:#fff; z-index:1; position:absolute; right:3px; bottom:3px; width:16px; height:16px; border-radius:4px; background:#16161bcc; text-align:center; font-size:13px; line-height:16px;}
.song-open span {display:block; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;}
.song-open small {display:block; margin-top:5px; color:#a5a5b4; font-size:12px;
    overflow:hidden; text-overflow:ellipsis; white-space:nowrap;}
.song-facts {font-size:11px; color:#a5a5b4; white-space:nowrap; flex-shrink:0;}
.song-menu {position:relative; flex-shrink:0;}
.song-menu summary {list-style:none; cursor:pointer; font-size:25px; padding:0 13px;
    border-radius:8px; color:#ededf2;}
.song-menu summary::-webkit-details-marker {display:none;}
.song-menu summary:hover, .song-menu[open] summary {background:#363640;}
.song-actions {position:absolute; right:0; top:100%; z-index:10; width:200px;
    background:#292932; border:1px solid #4b4b58; border-radius:10px; padding:8px;
    box-shadow:0 8px 24px #0008;}
.song-actions button, .song-actions a {text-decoration:none; box-sizing:border-box;display:block; width:100%; padding:8px; text-align:left;
    background:transparent; color:#ededf2; cursor:pointer; border:0; border-radius:6px;}
.song-actions button:hover, .song-actions a:hover {background:#41414e;}
.song-actions small {display:block; padding:0 8px 6px; font-size:11px; color:#b9b9c7;}
.empty-library {padding:24px; color:#a5a5b4;}
button:focus-visible, summary:focus-visible, a:focus-visible {outline:2px solid #ee985d; outline-offset:2px;}
"""
