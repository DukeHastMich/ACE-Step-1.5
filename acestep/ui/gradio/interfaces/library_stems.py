"""Run isolated Demucs jobs and cache complete stem results per source version."""

import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading

from loguru import logger

from .library_store import resolve_song

_JOB_LOCK = threading.Lock()
STEM_PROFILES = {
    2: ("htdemucs", ("vocals", "no_vocals")),
    4: ("htdemucs", ("vocals", "drums", "bass", "other")),
    6: ("htdemucs_6s", ("vocals", "drums", "bass", "other", "guitar", "piano")),
}


def stem_profile(count: int) -> tuple:
    """Validate the requested separation before starting a subprocess."""
    if count not in STEM_PROFILES:
        raise ValueError("Choose 2, 4, or 6 stems.")
    return STEM_PROFILES[count]


def stem_cache_key(source: Path, count: int = 2) -> str:
    """Keep old two-stem caches compatible and separate model configurations."""
    model, _ = stem_profile(count)
    stat = source.stat()
    version = "htdemucs-two-stems-v1" if count == 2 else f"{model}-{count}-stems-v1"
    identity = f"{source}|{stat.st_size}|{stat.st_mtime_ns}|{version}"
    return hashlib.sha256(identity.encode()).hexdigest()[:24]


def demucs_python() -> str:
    """Use a configured Demucs environment, a local dedicated venv, or ACE's Python."""
    configured = os.environ.get("ACESTEP_DEMUCS_PYTHON")
    if configured:
        return configured
    project = Path(__file__).resolve().parents[4]
    dedicated = project / ".venv-demucs" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    return str(dedicated) if dedicated.is_file() else sys.executable


def stem_command(source: Path, output: Path, count: int = 2) -> list[str]:
    """Build a shell-free command, using CPU to avoid competing with generation."""
    model, _ = stem_profile(count)
    command = [demucs_python(), "-m", "demucs", "-n", model]
    if count == 2:
        command.append("--two-stems=vocals")
    return command + ["--device", os.environ.get("ACESTEP_DEMUCS_DEVICE", "cpu"),
                      "--filename", "{stem}.{ext}", "-o", str(output), str(source)]


def _complete(directory: Path, count: int = 2) -> bool:
    """Only reuse results containing every expected WAV output."""
    _, names = stem_profile(count)
    return all((directory / (name + ".wav")).is_file()
               and (directory / (name + ".wav")).stat().st_size > 44 for name in names)


def separate_song(root: Path, relative: str, count: int = 2) -> tuple[str, ...]:
    """Separate one validated song, publishing only complete outputs; raise on failure."""
    source = resolve_song(root, relative)
    model, names = stem_profile(count)
    key = stem_cache_key(source, count)
    storage = (root / ".stems").resolve()
    if not storage.is_relative_to(root.resolve()):
        raise ValueError("Stem output directory must be inside the library.")
    destination = storage / key
    with _JOB_LOCK:
        if _complete(destination, count):
            return tuple(str(destination / (name + ".wav")) for name in names)
        storage.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="job-", dir=storage) as temporary:
            temporary = Path(temporary)
            log_path = temporary / "demucs.log"
            try:
                with log_path.open("w", encoding="utf-8") as log:
                    result = subprocess.run(
                        stem_command(source, temporary, count), stdout=log, stderr=subprocess.STDOUT,
                        timeout=7200, check=False,
                        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                    )
            except FileNotFoundError as exc:
                raise RuntimeError("Demucs Python was not found. Check ACESTEP_DEMUCS_PYTHON.") from exc
            except subprocess.TimeoutExpired as exc:
                raise RuntimeError("Stem separation timed out. Please try again.") from exc
            output = temporary / model
            if result.returncode or not _complete(output, count):
                detail = log_path.read_text(encoding="utf-8", errors="replace")[-6000:]
                logger.error("Demucs failed for {}: {}", source.name, detail)
                if "No module named demucs" in detail:
                    raise RuntimeError("Demucs is not installed in the selected Python environment.")
                raise RuntimeError("Demucs could not finish this track. See the ACE-Step log for details.")
            # Our jobs never publish incomplete stem sets, so an existing incomplete directory is unexpected.
            if destination.exists():
                raise RuntimeError("Incomplete saved stems found. Remove that stem folder and retry.")
            output.rename(destination)
    return tuple(str(destination / (name + ".wav")) for name in names)
