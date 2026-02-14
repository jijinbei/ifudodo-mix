import asyncio
import logging
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from .base_generator import BaseGenerator, GenerationError
from .config import Config
from .prompt_builder import IFUDODO_LYRICS

logger = logging.getLogger(__name__)

MAX_QUEUE_DEPTH = 3


class ACEStepGenerator(BaseGenerator):
    def __init__(self, config: Config):
        self.config = config
        self._pipeline = None
        self._executor = ThreadPoolExecutor(max_workers=1)
        self._lock = asyncio.Lock()
        self._queue_depth = 0

    async def setup(self) -> None:
        from acestep.pipeline_ace_step import ACEStepPipeline

        logger.info("Initializing ACE-Step pipeline")
        self._pipeline = ACEStepPipeline(cpu_offload=True)

        ref_path = Path(self.config.reference_melody_path)
        if ref_path.exists():
            self._ref_audio = str(ref_path)
            logger.info("Reference audio loaded: %s", ref_path)
        else:
            self._ref_audio = None
            logger.warning("No reference audio at %s; generating without audio2audio", ref_path)

        logger.info("ACE-Step pipeline initialized (model loads on first generation)")

    def _generate_sync(self, prompt: str) -> Path:
        assert self._pipeline is not None, "Pipeline not initialized"

        tmp_dir = tempfile.mkdtemp(prefix="ifudodo_")

        logger.info(
            "Generating with ACE-Step (duration=%.1fs, steps=%d): %r",
            self.config.acestep_audio_duration,
            self.config.acestep_infer_step,
            prompt,
        )
        results = self._pipeline(
            prompt=prompt,
            lyrics=IFUDODO_LYRICS,
            audio_duration=self.config.acestep_audio_duration,
            infer_step=self.config.acestep_infer_step,
            format="wav",
            save_path=tmp_dir,
            audio2audio_enable=self._ref_audio is not None,
            ref_audio_input=self._ref_audio,
            ref_audio_strength=self.config.acestep_ref_audio_strength,
        )

        audio_paths = [r for r in results if isinstance(r, str) and r.endswith(".wav")]
        if not audio_paths:
            raise GenerationError("ACE-Step did not produce any audio output")

        output_path = Path(audio_paths[0])
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
