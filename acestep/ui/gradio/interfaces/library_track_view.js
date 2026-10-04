// Render outside Gradio tab clipping; the persistent bottom player remains usable.
let page = null, request = '';
const close = () => {
  const song = page?.dataset.song;
  page?.remove(); page = null;
  const origin = Array.from(document.querySelectorAll('#ace-song-list button[data-song]')).find(b => b.dataset.song === song);
  origin?.focus();
};
const update = () => {
  const incoming = element.querySelector('.ace-track-page');
  if (!incoming || incoming.dataset.request === request) return;
  request = incoming.dataset.request;
  const sameTrack = page?.dataset.song === incoming.dataset.song;
  const scroll = page?.scrollTop || 0;
  page?.remove(); page = incoming.cloneNode(true); document.body.appendChild(page);
  page.querySelector(sameTrack ? '[data-save-notes]' : '[data-close]').focus();
  if (sameTrack) page.scrollTop = scroll;
  page.addEventListener('keydown', event => { if (event.key === 'Escape') close(); });
  page.addEventListener('change', event => {
    if (event.target.matches('[data-distribution]')) {
      page.querySelector('[data-distribution-fields]').hidden = !event.target.checked;
    }
  });
  page.addEventListener('click', event => {
    if (event.target.closest('[data-save-notes]')) {
      const notes = page.querySelector('[aria-label="Artist notes"]').value;
      const distribution = {enabled: page.querySelector('[data-distribution]').checked,
        isrc: page.querySelector('[data-isrc]').value, notes: page.querySelector('[data-distribution-notes]').value};
      page.querySelectorAll('.ace-notes-status').forEach(s => s.textContent = 'Saving…');
      trigger('submit', {song_id: page.dataset.song, notes, distribution}); return;
    }
    if (event.target.closest('[data-close]')) { close(); return; }
    const action = event.target.closest('[data-action]')?.dataset.action;
    if (!action) return;
    const song = page.dataset.song;
    if (action === 'stems') {
      close();
      const menu = Array.from(document.querySelectorAll('#ace-song-list button[data-stems]')).find(b => b.dataset.stems === song)?.closest('details');
      if (menu) { menu.open = true; menu.querySelector('[data-stem-menu]')?.focus(); }
      return;
    }
    const button = Array.from(document.querySelectorAll(`#ace-song-list button[data-${action}]`)).find(b => b.getAttribute(`data-${action}`) === song);
    if (action !== 'play') close();
    button?.click();
  });
};
new MutationObserver(update).observe(element, {childList:true, subtree:true, attributes:true, attributeFilter:["data-request"]});
update();
