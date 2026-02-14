import logging
import os
import shutil
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


def check_file_size(path: Path, max_mb: float) -> bool:
    size_mb = os.path.getsize(path) / (1024 * 1024)
    return size_mb <= max_mb


def convert_to_mp3(wav_path: Path, bitrate: str = "192k") -> Path:
    """Convert WAV to MP3 using ffmpeg. Returns path to the MP3 file."""
    mp3_path = wav_path.with_suffix(".mp3")
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(wav_path), "-b:a", bitrate, str(mp3_path)],
        check=True,
        capture_output=True,
    )
    logger.info("Converted %s -> %s", wav_path, mp3_path)
    return mp3_path


def cleanup_temp_file(path: Path) -> None:
    try:
        parent = path.parent
        if parent.exists() and parent.name.startswith("ifudodo_"):
            shutil.rmtree(parent)
        elif path.exists():
            path.unlink()
    except OSError:
        pass
