# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ifudodo-mix is a Discord bot that generates music remixes of 威風堂々 (Ifudodo) using Meta's MusicGen AI model. It uses melody conditioning to preserve the original melody while applying user-specified styles via the `/ifudodo` slash command.

## Commands

```bash
pixi install          # Install all dependencies (first run downloads ML models)
pixi run start        # Start the bot (runs: python -m ifudodo_mix)
```

No tests, linting, or formatting are currently configured.

## Architecture

Entry point: `src/ifudodo_mix/__main__.py` → `bot.main()`

```
bot.py          Discord client, /ifudodo slash command handler
  ├─ generator.py    MusicGen model wrapper, async generation with queue (max 3, 840s timeout)
  │   └─ config.py   Dataclass loading all settings from .env via python-dotenv
  ├─ prompt_builder.py  Combines fixed IFUDODO_CONTEXT with user style description
  └─ audio_utils.py     File size check and temp file cleanup
```

**Generation flow:** User sends `/ifudodo <style>` → prompt built from fixed context + user input → `MusicGenerator.generate()` acquires async lock → runs `_generate_sync()` in ThreadPoolExecutor → melody-conditioned generation via `generate_with_chroma()` (or text-only fallback) → audio saved to temp dir → uploaded to Discord → temp files cleaned up.

**Melody conditioning** is used when the model name contains "melody" and the reference file (`assets/ifudodo_source.mp4`) exists.

## Key Conventions

- **Package manager:** Pixi (not pip/conda directly). Dependencies in `pyproject.toml` under `[tool.pixi.*]` sections.
- **Platform:** linux-64 only. Requires Python 3.10.*, CUDA GPU recommended.
- **Config:** All settings via `.env` file (see `.env.example`). `DISCORD_TOKEN` is required; `GUILD_ID` enables instant command sync for development.
- **Language:** Bot-facing strings (command descriptions, user messages) are in Japanese.
- **Async pattern:** Discord.py async client with `setup_hook()` for initialization. CPU-bound generation is offloaded to a single-worker ThreadPoolExecutor with an asyncio.Lock serializing access.
