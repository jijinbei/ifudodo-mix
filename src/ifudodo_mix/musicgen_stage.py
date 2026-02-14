"""Standalone MusicGen melody conditioning script.

Run in the musicgen pixi environment as a subprocess:
    pixi run -e musicgen python -m ifudodo_mix.musicgen_stage <prompt> <output_path>

Loads MusicGen melody model, generates with chroma conditioning from the
reference audio, and saves the result to the specified output path.
"""
import sys
import logging
from pathlib import Path

import torch
import torchaudio
from audiocraft.data.audio import audio_write
from audiocraft.models import MusicGen

from .config import Config

logger = logging.getLogger(__name__)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    if len(sys.argv) != 3:
        print(f"Usage: python -m ifudodo_mix.musicgen_stage <prompt> <output_path>", file=sys.stderr)
        sys.exit(1)

    prompt = sys.argv[1]
    output_path = Path(sys.argv[2])

    config = Config()

    logger.info("Loading MusicGen model: %s", config.model_name)
    model = MusicGen.get_pretrained(config.model_name, device=config.device)
    model.set_generation_params(
        duration=config.duration,
        top_k=config.top_k,
        temperature=config.temperature,
        cfg_coef=config.cfg_coef,
    )

    melody_path = Path(config.reference_melody_path)
    if not melody_path.exists():
        logger.error("Reference melody not found: %s", melody_path)
        sys.exit(1)

    melody_wav, melody_sr = torchaudio.load(str(melody_path))
    melody_wav = melody_wav.to(config.device)

    logger.info("Generating with melody conditioning: %r", prompt)
    wav = model.generate_with_chroma(
        descriptions=[prompt],
        melody_wavs=melody_wav[None],
        melody_sample_rate=melody_sr,
        progress=True,
    )

    stem = output_path.with_suffix("")
    audio_write(
        str(stem),
        wav[0].cpu(),
        model.sample_rate,
        format="wav",
        strategy="loudness",
        loudness_compressor=True,
    )
    logger.info("MusicGen output saved to: %s", output_path)

    # Free GPU memory
    del model, wav, melody_wav
    torch.cuda.empty_cache()


if __name__ == "__main__":
    main()
