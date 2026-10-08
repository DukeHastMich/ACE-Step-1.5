# ACE-Step Studio fork: features and change history

This fork adds a local music workspace to ACE-Step 1.5. Model weights, generated
music, uploaded recordings, artwork and personal metadata are not included in
this source release.

## October 8, 2026 — upload archive and creation fixes

- Added an **Upload archive** tab with preview, download, refresh, bulk upload,
  and reuse as Remix source or reference audio.
- Source, reference, LM-code audio and persona uploads—including microphone
  recordings—are copied into the project-local `uploads/` folder. Content hashes
  deduplicate identical files; completed copies remain usable after temporary
  Gradio files disappear. The folder is ignored by Git.
- Moved source audio to the top of Create. Library Remix and Remaster show the
  source control, label it with the selected title and scroll Create to the top.
- Grouped Lyrics and Styles into cards, moved the song title near Generate, and
  exposed **Retake & Variance / Edit** outside the collapsed audio-tools panel.
  Corrected the visibility binding so the Edit column controls do not hide Retake.
- Empty caption/lyrics enhancement now leaves fields unchanged and shows a message.
  Lyric rewriting requests lyric-only output; a response filter extracts lyric
  sections and rejects recognized caption-only output rather than replacing lyrics.
- Generation, caption/lyric enhancement and next-batch requests share a queued
  concurrency group with a limit of one. This prevents those UI handlers from
  overlapping model inference; it is not a guarantee against all CUDA failures.

## Original Studio feature set — commit `6f76b22`

- Responsive Create pane on the left and Current takes/Library on the right,
  viewport sizing, header utility links, and space reserved for the bottom player.
- Slim black persistent player; library rows show song title above style text.
  Titles feed output naming and generation metadata.
- Track menus: Download, Open folder, Remix, Remaster, Create Persona, Move to
  trash, and a branching Get stems menu for two, four or six Demucs stems.
- PNG artwork uploads, placeholder tiles, a clickable upload icon, and tile playback.
- Track detail view with artwork, lyrics, artist notes, optional Distribution
  fields (ISRC and distribution notes), generation details, and return navigation.
- Linked generation sidecars allow Remix to reload source audio, title, prompt,
  caption/style and lyrics when available. Older unsaved fields cannot be recovered.
- Recoverable Trash moves a song and its associated files together; restore is
  available from the Library. This is not permanent erasure.
- Remaster presets Subtle/Normal/High perform constrained source-conditioned
  regeneration into a new track. They are not mastering EQ or guaranteed enhancement.
- Personas preserve independent vocal references, names, descriptions and profile
  pictures. The Personas tab offers vocal preview and loads the reference into
  Create. Personas are reference conditioning, not separately trained voice models.
- Demucs runs in a separate process, caches completed stem sets and defaults to CPU.
- DCW defaults to off unless explicitly enabled; model/output controls and batch
  metadata propagation were updated alongside the workspace.

See [Library, stems, artwork, trash, remix and persona instructions](LIBRARY_STEMS.md)
for detailed use and optional Demucs installation.

## Local data and requirements

`gradio_outputs/` holds generated music, sidecars, `.stems`, `.trash` and `.personas`.
`uploads/` holds durable uploaded/recorded audio. Both are excluded from Git.
Back these folders up separately. Existing model installation requirements still
apply; this push does not publish or install model checkpoints.

Archiving preserves uploaded bytes; it does not repair corrupt audio or add missing
decoders. The previously reported MP3 decoding failure is not claimed fixed here.

## Validation and limits

Validation passed 97 tests (88 interface tests and 9 focused generation tests). The focused unittest suites for Studio interfaces, library operations,
personas, uploads, enhancement responses, queue registration, remaster presets and
song metadata. GPU generation and real Demucs inference are not exercised by these
unit tests. Lyric response filtering is a heuristic and cannot guarantee semantic
lyric preservation for every model output.

The existing large `llm_inference.py` facade receives only a narrow instruction
change. A separate follow-up can extract lyric formatting prompt construction into
a small tested helper without changing the public handler API.
