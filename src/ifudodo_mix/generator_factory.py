from .base_generator import BaseGenerator
from .config import Config


def create_generator(config: Config) -> BaseGenerator:
    backend = config.generator_backend
    if backend == "musicgen":
        from .generator import MusicGenerator

        return MusicGenerator(config)
    elif backend == "acestep":
        from .acestep_generator import ACEStepGenerator

        return ACEStepGenerator(config)
    else:
        raise ValueError(f"Unknown GENERATOR_BACKEND: {backend!r}")
