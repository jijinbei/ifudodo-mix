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
  ├─ acestep_generator.py  ACE-Step 1.5 wrapper, async generation with queue (max 3, 840s timeout)
  │   └─ config.py         Dataclass loading all settings from .env via python-dotenv
  ├─ prompt_builder.py     Combines fixed IFUDODO_CONTEXT with user style description; holds IFUDODO_LYRICS
  └─ audio_utils.py        MP3 conversion (ffmpeg), file size check, temp file cleanup
```

**Generation flow:** User sends `/ifudodo <style>` → prompt built from fixed context + user input → `ACEStepGenerator.generate()` acquires async lock → runs `_generate_sync()` in ThreadPoolExecutor → `AceStepHandler.generate_music(captions, lyrics, vocal_language="ja", ...)` → WAV saved via soundfile → converted to MP3 via ffmpeg → uploaded to Discord → temp files cleaned up.

**ACE-Step 1.5** is cloned to `vendor/ace-step-15/` and loaded via `PYTHONPATH`. The handler's `process_reference_audio` is monkey-patched to use `soundfile` instead of `torchaudio` to avoid `torchcodec`/`libnppicc` dependency issues.

## Key Conventions

- **Package manager:** Pixi (not pip/conda directly). Dependencies in `pyproject.toml` under `[tool.pixi.*]` sections.
- **Platform:** linux-64 only. Requires Python 3.11, CUDA GPU (torch cu128).
- **Config:** All settings via `.env` file. `DISCORD_TOKEN` is required; `GUILD_ID` enables instant command sync for development.
- **Language:** Bot-facing strings (command descriptions, user messages) are in Japanese.
- **Async pattern:** Discord.py async client with `setup_hook()` for initialization. CPU-bound generation is offloaded to a single-worker ThreadPoolExecutor with an asyncio.Lock serializing access.
- **Audio output:** Always converted to MP3 before Discord upload (WAV too large for Discord's 25MB limit).
