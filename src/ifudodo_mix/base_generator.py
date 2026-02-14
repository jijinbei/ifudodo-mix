from abc import ABC, abstractmethod
from pathlib import Path


class GenerationError(Exception):
    pass


class BaseGenerator(ABC):
    @abstractmethod
    async def setup(self) -> None:
        """Load model and prepare for generation."""
        ...

    @abstractmethod
    async def generate(self, prompt: str) -> Path:
        """Generate audio and return path to temporary file."""
        ...
