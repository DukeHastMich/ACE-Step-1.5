# Library stem separation

In **Create → Library**, open a song's **⋮** menu and choose **Get stems**.
The panel shows the source track and progress, then **Vocals** and **Instrumental**
WAV players with download buttons. Existing completed stems are reused.

The integration runs `python -m demucs --two-stems=vocals -n htdemucs` in a
separate process for two stems. Four omits `--two-stems`; six uses
`-n htdemucs_6s` without `--two-stems`. Originals and generation metadata are never overwritten.
Outputs live under `gradio_outputs/.stems/<source-version>/`; these files are
excluded from the main library. Failed jobs do not publish partial stem sets.

Install the optional dependency into ACE-Step's environment:

```powershell
uv pip install --python .venv/Scripts/python.exe demucs==4.1.0
```

The first separation downloads the Demucs model if it is not already cached.
CPU is the default so stem extraction does not consume the GPU memory held by
ACE-Step. To use a GPU, set `ACESTEP_DEMUCS_DEVICE=cuda:0` (or another device)
before launching ACE-Step. Ensure that device has room for Demucs.

For an existing separate installation, set `ACESTEP_DEMUCS_PYTHON` to its full
Python executable path before starting ACE-Step. A project-local `.venv-demucs`
is also detected automatically. Otherwise the running ACE-Step Python is used.

One separation runs at a time, with a two-hour timeout. On failure, the panel
shows a message and ACE-Step's server log contains the Demucs error. Retry by
opening the same track menu. Restart ACE-Step after installing this feature.

## Recoverable trash

Each track menu also offers **Move to trash**. The song disappears from the library,
while its audio, artwork, generation metadata, session artifacts, and cached stems
move together under `gradio_outputs/.trash`. Metadata shared with another audio
format is retained for that track and copied into Trash for recovery.
Expand **Trash**, choose a track, and click **Restore to library** to recover it,
even after restarting the app. Restore refuses to replace an existing track.

## Direct downloads

Choose **Download** from a track's three-dot menu to save its original audio format.
The browser download name is based on the library title, with invalid filename
characters replaced. The existing authenticated Gradio file route serves the audio.

## Album artwork

Click a song's artwork tile to select it and start playback. Click its corner
upload icon to select the song and browse for a PNG. You can also drop a PNG into **Album art** below the player.
Click **Save artwork** to attach it to the displayed song. Saved artwork replaces
the placeholder thumbnail and remains after app restarts and trash/restore.
The original PNG is stored beside the audio as `<audio filename>.cover.png`;
audio and generation metadata remain unchanged. Repeating the workflow replaces
the artwork. PNG uploads are limited to 25 MB and 40 megapixels.


## Remix from the library

Choose **Remix** in a track menu to load its source audio, title, original prompt,
style, and lyrics into the creation controls. New foreground and AutoGen takes
retain these inputs in their linked JSON sidecars. Older songs reuse the saved
title, caption, and lyrics; prompts that were never saved cannot be recovered.

## Constrained Remaster

Choose **Remaster** in a track menu, choose **Subtle**, **Normal**, or **High**
in Create, then click **Remaster � Save new version**. The source audio and its
saved style and lyrics are loaded automatically. Results use a new output file
and a `(Remaster)` title; the original audio is untouched.

This regenerates audio near the source rather than applying mastering EQ.
The presets are initial tuning values, not a promise of better sound or exact
voice preservation. Compare results against the original at matched volume.
All presets keep audio conditioning at 1.0. Source retention is 0.875, 0.75,
and 0.5 respectively, using the 8-step, shift-1 ODE schedule. Turbo quantizes
these to different source-noise starting points. Remaster overrides custom
schedules, retake, flow-edit, reference audio, and LM rewriting so stale settings
do not loosen the constraint. Original caption and lyrics stay editable.
The applied preset, source path, and retention are saved in the new JSON sidecar,
including when AutoGen continues the request. Normal Remix remains unchanged.


## Personas

Choose Create Persona from a library track menu or track details. Enter a name
and voice description, optionally upload a profile picture, and create it.
Cached Demucs vocals are reused; otherwise vocals are extracted. You can also
upload isolated vocals directly in the Personas tab. An uploaded picture
overrides source artwork; otherwise a colored placeholder is shown.

Click a persona name to load Custom mode, its reference audio, and voice
description into Create. Current lyrics and style are preserved. Use the
play control beside its name to audition the vocals. This is reference
conditioning, not a trained voice model or guaranteed identity match.
Personas keep independent vocals and artwork under gradio_outputs/.personas
and survive deletion of their source song.
