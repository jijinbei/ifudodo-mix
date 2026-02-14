# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ifudodo-mix is a Discord bot that generates music remixes of 威風堂々 (Ifudodo) using ACE-Step 1.5 AI music generation model. Users submit a style via the `/ifudodo` slash command and the bot generates a full vocal track with Japanese lyrics.

## Commands

```bash
pixi install          # Install all dependencies
pixi run start        # Clone ACE-Step 1.5 repo (if needed) and start the bot
```

No tests, linting, or formatting are currently configured.

## Architecture

Entry point: `src/ifudodo_mix/__main__.py` → `bot.main()`

```
bot.py                Discord client, /ifudodo slash command handler
  ├─ style_researcher.py   Web search (DuckDuckGo) + Ollama LLM for enriching user style descriptions
  ├─ acestep_generator.py  ACE-Step 1.5 wrapper, async generation with queue (max 3, 840s timeout)
  │   └─ config.py         Dataclass loading all settings from .env via python-dotenv
  ├─ prompt_builder.py     Combines fixed IFUDODO_CONTEXT with researched/user style description; holds IFUDODO_LYRICS
  └─ audio_utils.py        MP3 conversion (ffmpeg), file size check, temp file cleanup
```

**Generation flow:** User sends `/ifudodo <style>` → `style_researcher.research_style()` searches DuckDuckGo for genre characteristics and uses Ollama LLM to generate detailed music description tags → enriched description passed to `build_prompt()` with fixed context → `ACEStepGenerator.generate()` acquires async lock → runs `_generate_sync()` in ThreadPoolExecutor → `AceStepHandler.generate_music(captions, lyrics, vocal_language="ja", task_type="repaint", ...)` with reference audio as both `reference_audio` and `src_audio` → WAV saved via soundfile → converted to MP3 via ffmpeg → uploaded to Discord → temp files cleaned up.

**Style research** uses DuckDuckGo (no API key) for web search and Ollama for local LLM analysis. Both are optional — if Ollama is unavailable or web search fails, the bot falls back to the original user input as-is.

**ACE-Step 1.5** is cloned to `vendor/ace-step-15/` and loaded via `PYTHONPATH`. The handler's `process_reference_audio` and `process_src_audio` are monkey-patched to use `soundfile` instead of `torchaudio` to avoid `torchcodec`/`libnppicc` dependency issues.

## ACE-Step Generation Parameters

Current generation uses **repaint mode** (`task_type="repaint"`) with the original song as source audio. Key parameters for tuning remix behavior:

- **`audio_cover_strength`** (0.0–1.0, default 1.0): Fraction of diffusion steps that reference the source audio. Lower = more creative freedom.
- **`cover_noise_strength`** (0.0–1.0, default 0.0): How close the initial noise is to the source latents. Higher = closer to original. **Caution:** Setting >0 with full-duration repaint (`repainting_start=0, repainting_end=duration`) causes silent output because all source latents are replaced by silence latents before blending.
- **`guidance_scale`** (1.0–15.0, default 7.0): Text prompt adherence (turbo model ignores this).
- **`inference_steps`** (default 60): More steps = higher quality but slower.

### Known Issues

- Full-duration repaint + `cover_noise_strength > 0` = silent output. To use `cover_noise_strength`, switch from repaint to cover mode (remove `task_type`/`repainting_*`, add `audio_cover_strength`).
- The prompt context (`IFUDODO_CONTEXT`) includes "march, 120 BPM, majestic and dignified" which can conflict with distant genres (e.g., hardcore). The style research feature mitigates this by generating detailed genre-specific tags that can override these defaults.

## Key Conventions

- **Package manager:** Pixi (not pip/conda directly). Dependencies in `pyproject.toml` under `[tool.pixi.*]` sections.
- **Platform:** linux-64 only. Requires Python 3.11, CUDA GPU (torch cu128).
- **Config:** All settings via `.env` file. `DISCORD_TOKEN` is required; `GUILD_ID` enables instant command sync for development. `OLLAMA_HOST` and `OLLAMA_MODEL` configure style research (optional, defaults to `http://localhost:11434` and `gemma3`).
- **Language:** Bot-facing strings (command descriptions, user messages) are in Japanese.
- **Async pattern:** Discord.py async client with `setup_hook()` for initialization. CPU-bound generation is offloaded to a single-worker ThreadPoolExecutor with an asyncio.Lock serializing access.
- **Audio output:** Always converted to MP3 before Discord upload (WAV too large for Discord's 25MB limit).
