"""Source-constrained remaster presets shared by UI and generation."""
from pathlib import Path

PRESETS = {"Subtle": 0.875, "Normal": 0.75, "High": 0.5}


def remaster_strength(preset: str) -> float:
    """Return source retention; reject unknown presets rather than silently changing audio."""
    if preset not in PRESETS:
        raise ValueError("Choose Subtle, Normal, or High for Remaster.")
    return PRESETS[preset]


def apply_remaster(params, preset: str) -> None:
    """Constrain generation to source audio and disable conflicting creative overlays."""
    strength = remaster_strength(preset)
    if not params.src_audio or not Path(params.src_audio).is_file():
        raise ValueError("Remaster needs an existing source audio file.")
    params.task_type = "cover"
    params.audio_cover_strength = 1.0
    params.cover_noise_strength = strength
    params.thinking = False
    params.use_cot_caption = False
    params.use_cot_metas = False
    params.use_cot_language = False
    params.audio_codes = ""
    params.reference_audio = None
    params.retake_variance = 0.0
    params.flow_edit_morph = False
    # Shift 1 gives distinct low-noise steps for all three presets on Turbo.
    params.shift = 1.0
    params.inference_steps = 8
    params.timesteps = None
    params.infer_method = "ode"
    params.latent_shift = 0.0
    params.latent_rescale = 1.0
    params.fade_in_duration = 0.0
    params.fade_out_duration = 0.0
