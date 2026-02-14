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

    # Reference melody
    reference_melody_path: str = field(
        default_factory=lambda: os.environ.get(
            "REFERENCE_MELODY_PATH",
            str(ROOT_DIR / "assets" / "ifudodo_source.wav"),
        )
    )

    # ACE-Step
    acestep_audio_duration: float = field(
        default_factory=lambda: float(
            os.environ.get("ACESTEP_AUDIO_DURATION", "180")
        )
    )
    acestep_infer_step: int = field(
        default_factory=lambda: int(
            os.environ.get("ACESTEP_INFER_STEP", "60")
        )
    )

    # Ollama (style research)
    ollama_host: str = field(
        default_factory=lambda: os.environ.get(
            "OLLAMA_HOST", "http://localhost:11434"
        )
    )
    ollama_model: str = field(
        default_factory=lambda: os.environ.get("OLLAMA_MODEL", "gemma3")
    )

    # Output
    max_file_size_mb: float = field(
        default_factory=lambda: float(os.environ.get("MAX_FILE_SIZE_MB", "24"))
    )
