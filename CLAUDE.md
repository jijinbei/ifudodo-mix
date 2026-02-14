# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ifudodo-mix is a Discord bot that generates music remixes of 威風堂々 (Ifudodo) using AI music generation models. It supports two backends: ACE-Step 1.5 (default, higher quality) and Meta's MusicGen (legacy). Users request mixes via the `/ifudodo` slash command with a style description.

## Commands

```bash
pixi install                  # Install all environments
pixi run -e acestep start     # Start with ACE-Step backend (default)
pixi run -e musicgen start    # Start with MusicGen backend (legacy)
```

No tests, linting, or formatting are currently configured.

## Architecture

Entry point: `src/ifudodo_mix/__main__.py` → `bot.main()`

```
bot.py                Discord client, /ifudodo slash command handler
  ├─ generator_factory.py   GENERATOR_BACKEND で分岐（遅延import）
  │   ├─ generator.py         MusicGen backend (legacy)
  │   └─ acestep_generator.py  ACE-Step 1.5 backend (default)
  │   Both implement base_generator.py BaseGenerator ABC
  ├─ base_generator.py  BaseGenerator ABC + GenerationError
  ├─ config.py          Dataclass loading all settings from .env via python-dotenv
  ├─ prompt_builder.py  Combines fixed IFUDODO_CONTEXT with user style description
  └─ audio_utils.py     File size check and temp file cleanup
```

**Generation flow:** User sends `/ifudodo <style>` → prompt built from fixed context + user input → `generator.generate()` acquires async lock → runs `_generate_sync()` in ThreadPoolExecutor → backend-specific generation → audio saved to temp dir → uploaded to Discord → temp files cleaned up.

**Backend selection** is controlled by `GENERATOR_BACKEND` env var (`"acestep"` or `"musicgen"`). The factory uses lazy imports so only the selected backend's dependencies are loaded.

**MusicGen melody conditioning** is used when the model name contains "melody" and the reference file (`assets/ifudodo_source.mp4`) exists.

## Key Conventions

- **Package manager:** Pixi (not pip/conda directly). Dependencies in `pyproject.toml` under `[tool.pixi.*]` sections. Backend-specific deps are in pixi features (`acestep`, `musicgen`) with separate environments.
- **Platform:** linux-64 only. Requires Python 3.10.*, CUDA GPU recommended.
- **Config:** All settings via `.env` file (see `.env.example`). `DISCORD_TOKEN` is required; `GUILD_ID` enables instant command sync for development.
- **Language:** Bot-facing strings (command descriptions, user messages) are in Japanese.
- **Async pattern:** Discord.py async client with `setup_hook()` for initialization. CPU-bound generation is offloaded to a single-worker ThreadPoolExecutor with an asyncio.Lock serializing access.
