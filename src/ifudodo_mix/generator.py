import asyncio
import logging
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import torch
import torchaudio
from audiocraft.data.audio import audio_write
from audiocraft.models import MusicGen

from .config import Config

logger = logging.getLogger(__name__)

MAX_QUEUE_DEPTH = 3


class GenerationError(Exception):
    pass


class MusicGenerator:
    def __init__(self, config: Config):
        self.config = config
        self._model: MusicGen | None = None
        self._melody_wav: torch.Tensor | None = None
        self._melody_sr: int | None = None
        self._executor = ThreadPoolExecutor(max_workers=1)
        self._lock = asyncio.Lock()
        self._queue_depth = 0

    def load_model(self) -> None:
        logger.info("Loading MusicGen model: %s", self.config.model_name)
        self._model = MusicGen.get_pretrained(
            self.config.model_name,
            device=self.config.device,
        )
        self._model.set_generation_params(
            duration=self.config.duration,
            top_k=self.config.top_k,
            temperature=self.config.temperature,
            cfg_coef=self.config.cfg_coef,
        )

        melody_path = Path(self.config.reference_melody_path)
        if melody_path.exists():
            logger.info("Loading reference melody: %s", melody_path)
            self._melody_wav, self._melody_sr = torchaudio.load(str(melody_path))
            self._melody_wav = self._melody_wav.to(self.config.device)
            logger.info(
                "Reference melody loaded: %s channels, %s samples, %s Hz",
                self._melody_wav.shape[0],
                self._melody_wav.shape[1],
                self._melody_sr,
            )
        else:
            logger.warning(
                "No reference melody at %s; using text-only generation.",
                melody_path,
            )

    @property
    def can_use_melody(self) -> bool:
        return self._melody_wav is not None and "melody" in self.config.model_name

    def _generate_sync(self, prompt: str) -> Path:
        assert self._model is not None, "Model not loaded"

        if self.can_use_melody:
            logger.info("Generating with melody conditioning: %r", prompt)
            wav = self._model.generate_with_chroma(
                descriptions=[prompt],
                melody_wavs=self._melody_wav[None],
                melody_sample_rate=self._melody_sr,
                progress=True,
            )
        else:
            logger.info("Generating text-to-music: %r", prompt)
            wav = self._model.generate(
                descriptions=[prompt],
                progress=True,
            )

        tmp_dir = tempfile.mkdtemp(prefix="ifudodo_")
        stem = Path(tmp_dir) / "mix"
        audio_write(
            str(stem),
            wav[0].cpu(),
            self._model.sample_rate,
            format=self.config.output_format,
            strategy="loudness",
            loudness_compressor=True,
        )
        output_path = stem.with_suffix(f".{self.config.output_format}")
        logger.info("Generated audio saved to: %s", output_path)
        return output_path

    async def generate(self, prompt: str) -> Path:
        if self._queue_depth >= MAX_QUEUE_DEPTH:
            raise GenerationError(
                "Bot is currently busy. Please try again in a few minutes."
            )
        self._queue_depth += 1
        try:
            async with self._lock:
                loop = asyncio.get_running_loop()
                return await asyncio.wait_for(
                    loop.run_in_executor(
                        self._executor, self._generate_sync, prompt
                    ),
                    timeout=840.0,
                )
        except asyncio.TimeoutError:
            raise GenerationError(
                "Music generation timed out. Try a shorter duration."
            )
        finally:
            self._queue_depth -= 1
