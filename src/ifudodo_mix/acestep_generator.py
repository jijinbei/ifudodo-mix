import asyncio
import logging
import math
import random
import tempfile
import types
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Optional

import soundfile as sf
import torch

from .config import Config
from .prompt_builder import IFUDODO_LYRICS

logger = logging.getLogger(__name__)

MAX_QUEUE_DEPTH = 3


class GenerationError(Exception):
    pass


def _load_audio_sf(audio_file: Optional[str]) -> Optional[tuple]:
    """Load audio using soundfile (avoids torchcodec/libnppicc dependency).
    Returns (tensor, sample_rate) or None."""
    if audio_file is None:
        return None
    try:
        audio_np, sr = sf.read(audio_file, dtype="float32")
        if audio_np.ndim == 1:
            audio = torch.from_numpy(audio_np).unsqueeze(0)
        else:
            audio = torch.from_numpy(audio_np.T)
        return audio, sr
    except (OSError, RuntimeError, ValueError):
        logger.exception("Error loading audio with soundfile: %s", audio_file)
        return None


def _process_reference_audio_sf(self, audio_file: Optional[str]) -> Optional[torch.Tensor]:
    """Replacement for handler.process_reference_audio using soundfile."""
    result = _load_audio_sf(audio_file)
    if result is None:
        return None
    audio, sr = result

    audio = self._normalize_audio_to_stereo_48k(audio, sr)
    if self.is_silence(audio):
        return None

    target_frames = 30 * 48000
    segment_frames = 10 * 48000

    if audio.shape[-1] < target_frames:
        repeat_times = math.ceil(target_frames / audio.shape[-1])
        audio = audio.repeat(1, repeat_times)

    total_frames = audio.shape[-1]
    segment_size = total_frames // 3

    front_start = random.randint(0, max(0, segment_size - segment_frames))
    front_audio = audio[:, front_start : front_start + segment_frames]

    middle_start = segment_size + random.randint(0, max(0, segment_size - segment_frames))
    middle_audio = audio[:, middle_start : middle_start + segment_frames]

    back_start = 2 * segment_size + random.randint(
        0, max(0, (total_frames - 2 * segment_size) - segment_frames)
    )
    back_audio = audio[:, back_start : back_start + segment_frames]

    return torch.cat([front_audio, middle_audio, back_audio], dim=-1)


def _process_src_audio_sf(self, audio_file: Optional[str]) -> Optional[torch.Tensor]:
    """Replacement for handler.process_src_audio using soundfile."""
    result = _load_audio_sf(audio_file)
    if result is None:
        return None
    audio, sr = result
    return self._normalize_audio_to_stereo_48k(audio, sr)


class ACEStepGenerator:
    def __init__(self, config: Config):
        self.config = config
        self._handler = None
        self._ref_audio = None
        self._executor = ThreadPoolExecutor(max_workers=1)
        self._lock = asyncio.Lock()
        self._queue_depth = 0

    async def setup(self) -> None:
        from acestep.handler import AceStepHandler

        ref_path = Path(self.config.reference_melody_path)
        if ref_path.exists():
            self._ref_audio = str(ref_path)
            logger.info("Reference audio: %s", ref_path)
        else:
            self._ref_audio = None
            logger.warning("No reference audio at %s", ref_path)

        logger.info("Initializing ACE-Step v1.5 handler")
        self._handler = AceStepHandler()
        # Patch audio loading methods to use soundfile instead of
        # torchaudio (avoids torchcodec/libnppicc dependency).
        self._handler.process_reference_audio = types.MethodType(
            _process_reference_audio_sf, self._handler
        )
        self._handler.process_src_audio = types.MethodType(
            _process_src_audio_sf, self._handler
        )
        status, ok = self._handler.initialize_service(
            project_root="",
            config_path="acestep-v15-turbo",
            device="auto",
            use_flash_attention=False,
            offload_to_cpu=True,
        )
        logger.info("ACE-Step v1.5: %s (ok=%s)", status, ok)

    def _generate_sync(self, prompt: str) -> Path:
        logger.info(
            "Generating repaint (duration=%.1fs, steps=%d): %r",
            self.config.acestep_audio_duration,
            self.config.acestep_infer_step,
            prompt,
        )
        result = self._handler.generate_music(
            captions=prompt,
            lyrics=IFUDODO_LYRICS,
            vocal_language="ja",
            audio_duration=self.config.acestep_audio_duration,
            inference_steps=self.config.acestep_infer_step,
            reference_audio=self._ref_audio,
            src_audio=self._ref_audio,
            task_type="repaint",
            repainting_start=0.0,
            repainting_end=self.config.acestep_audio_duration,
        )

        if not result.get("success") or not result.get("audios"):
            error = result.get("error", "Unknown error")
            raise GenerationError(f"ACE-Step generation failed: {error}")

        audio_data = result["audios"][0]
        audio_tensor = audio_data["tensor"]
        sample_rate = audio_data["sample_rate"]

        tmp_dir = tempfile.mkdtemp(prefix="ifudodo_")
        output_path = Path(tmp_dir) / "mix.wav"
        audio_np = audio_tensor.cpu().numpy().T
        sf.write(str(output_path), audio_np, sample_rate)
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
