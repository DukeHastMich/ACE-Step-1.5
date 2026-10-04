// Keep one native audio element alive across Gradio track-data updates.
const old = document.getElementById('ace-bottom-player');
if (old) { old.querySelector('audio')?.pause(); old.remove(); }
const dock = document.createElement('section');
dock.id = 'ace-bottom-player';
dock.setAttribute('aria-label', 'Music player');
dock.innerHTML = `
  <audio preload="metadata"></audio>
  <div class="ace-now"><div class="ace-cover" aria-hidden="true">♫</div>
    <div class="ace-track-text"><strong>Select a song</strong><small>Your music, ready to play</small></div></div>
  <button class="ace-toggle" aria-label="Play" disabled>▶</button>
  <div class="ace-timeline"><time class="ace-elapsed">0:00</time>
    <input class="ace-seek" type="range" min="0" max="100" value="0" step="0.1" aria-label="Seek" disabled>
    <time class="ace-duration">0:00</time></div>
  <div class="ace-volume"><button class="ace-mute" aria-label="Mute">♪</button>
    <input type="range" min="0" max="1" value="0.8" step="0.01" aria-label="Volume"></div>`;
document.body.appendChild(dock);
const audio = dock.querySelector('audio');
const play = dock.querySelector('.ace-toggle');
const seek = dock.querySelector('.ace-seek');
const volume = dock.querySelector('.ace-volume input');
const mute = dock.querySelector('.ace-mute');
const title = dock.querySelector('strong');
const subtitle = dock.querySelector('small');
const cover = dock.querySelector('.ace-cover');
let current = '', request = '', seeking = false;
audio.volume = 0.8;
const clock = (seconds) => { const n = Math.max(0, Math.floor(seconds || 0)); return `${Math.floor(n/60)}:${String(n%60).padStart(2,'0')}`; };
const sync = () => {
  play.textContent = audio.paused ? '▶' : 'Ⅱ';
  play.setAttribute('aria-label', audio.paused ? 'Play' : 'Pause');
  const duration = Number.isFinite(audio.duration) ? audio.duration : 0;
  if (!seeking) seek.value = duration ? 100 * audio.currentTime / duration : 0;
  seek.disabled = !duration;
  seek.setAttribute('aria-valuetext', `${clock(audio.currentTime)} of ${clock(duration)}`);
  dock.querySelector('.ace-elapsed').textContent = clock(audio.currentTime);
  dock.querySelector('.ace-duration').textContent = clock(duration);
};
const start = () => audio.play().catch(() => {
  subtitle.textContent = 'Press play to start playback'; sync();
});
play.addEventListener('click', () => audio.paused ? start() : audio.pause());
for (const event of ['play','pause','timeupdate','loadedmetadata','durationchange','ended']) audio.addEventListener(event, sync);
audio.addEventListener('error', () => {
  if (current) { subtitle.textContent = 'Could not load this track. Select it again to retry.'; subtitle.classList.add('ace-error'); }
  sync();
});
seek.addEventListener('input', () => {
  seeking = true;
  if (Number.isFinite(audio.duration)) audio.currentTime = audio.duration * Number(seek.value) / 100;
  dock.querySelector('.ace-elapsed').textContent = clock(audio.currentTime);
});
seek.addEventListener('change', () => { seeking = false; sync(); });
const speaker = '<svg width=18 height=18 viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true"><path d="M11 5 6 9H3v6h3l5 4z"/><path d="M15 8a6 6 0 0 1 0 8M18 5a10 10 0 0 1 0 14"/></svg>';
const syncVolume = () => {
  mute.innerHTML = audio.muted || audio.volume === 0 ? '<span aria-hidden="true">⊘</span>' : speaker;
  mute.setAttribute('aria-label', audio.muted ? 'Unmute' : 'Mute');
};
volume.addEventListener('input', () => { audio.volume = Number(volume.value); audio.muted = false; syncVolume(); });
mute.addEventListener('click', () => { audio.muted = !audio.muted; syncVolume(); });
syncVolume();
const update = () => {
  const data = element.querySelector('.ace-player-data')?.dataset;
  if (!data) {
    audio.pause(); audio.removeAttribute('src'); audio.load(); current = ''; request = '';
    title.textContent = 'Select a song'; subtitle.textContent = 'Your music, ready to play';
    cover.textContent = '♫'; play.disabled = true; sync(); return;
  }
  if (data.request === request) return;
  request = data.request;
  title.textContent = data.title; title.title = data.title;
  subtitle.textContent = data.style || 'Saved on this computer'; subtitle.title = data.style;
  subtitle.classList.remove('ace-error'); cover.textContent = '♫';
  if (data.art) {
    const img = document.createElement('img'); img.alt = ''; img.src = data.art;
    img.addEventListener('error', () => { cover.textContent = '♫'; }); cover.replaceChildren(img);
  }
  if (current !== data.src) { audio.pause(); audio.src = data.src; current = data.src; audio.load(); }
  play.disabled = false;
  if (data.play === 'true') start();
  sync();
};
new MutationObserver(update).observe(element, {childList:true, subtree:true, attributes:true});
update();
