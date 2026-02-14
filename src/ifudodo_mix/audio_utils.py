import os
import shutil
from pathlib import Path


def check_file_size(path: Path, max_mb: float) -> bool:
    size_mb = os.path.getsize(path) / (1024 * 1024)
    return size_mb <= max_mb


def cleanup_temp_file(path: Path) -> None:
    try:
        parent = path.parent
        if parent.exists() and parent.name.startswith("ifudodo_"):
            shutil.rmtree(parent)
        elif path.exists():
            path.unlink()
    except OSError:
        pass
