import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT_DIR = Path(__file__).resolve().parent.parent.parent


@dataclass
class Config:
    discord_token: str = field(
        default_factory=lambda: os.environ["DISCORD_TOKEN"]
    )
    guild_id: int | None = field(
        default_factory=lambda: int(os.environ["GUILD_ID"])
        if os.environ.get("GUILD_ID", "").strip().isdigit()
        else None
    )

    # MusicGen
    model_name: str = field(
        default_factory=lambda: os.environ.get(
            "MUSICGEN_MODEL", "facebook/musicgen-small"
        )
    )
    device: str = field(
        default_factory=lambda: os.environ.get("DEVICE", "cuda")
    )
    duration: float = field(
        default_factory=lambda: float(os.environ.get("DURATION", "15"))
    )
    top_k: int = field(
        default_factory=lambda: int(os.environ.get("TOP_K", "250"))
    )
    temperature: float = field(
        default_factory=lambda: float(os.environ.get("TEMPERATURE", "1.0"))
    )
    cfg_coef: float = field(
        default_factory=lambda: float(os.environ.get("CFG_COEF", "3.0"))
    )

    # Reference melody
    reference_melody_path: str = field(
        default_factory=lambda: os.environ.get(
            "REFERENCE_MELODY_PATH",
            str(ROOT_DIR / "assets" / "ifudodo_source.mp4"),
        )
    )

    # Output
    output_format: str = field(
        default_factory=lambda: os.environ.get("OUTPUT_FORMAT", "wav")
    )
    max_file_size_mb: float = field(
        default_factory=lambda: float(os.environ.get("MAX_FILE_SIZE_MB", "24"))
    )
