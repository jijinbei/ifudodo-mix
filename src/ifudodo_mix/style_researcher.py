import logging

from ollama import AsyncClient

from .config import Config

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
You are a music style analyst for the ACE-Step AI music generation model.
Given web search results about a music genre/style and the user's style description,
generate a concise, comma-separated list of English music description tags.

Include:
- Tempo range (e.g., "75-85 BPM")
- Key instruments and sounds
- Tonal qualities and textures
- Mood and atmosphere
- Production techniques

Output ONLY the comma-separated tags, nothing else. Keep it under 50 words.
Example output: lo-fi hip hop, mellow dusty beats, vinyl crackle, jazz Rhodes piano, relaxed 75-85 BPM, warm analog pads, tape saturation, dreamy nostalgic mood"""


async def search_style_info(style: str) -> str | None:
    """Search for music style characteristics using DuckDuckGo."""
    try:
        from duckduckgo_search import AsyncDDGS

        query = f"{style} music genre characteristics instruments tempo mood"
        logger.info("Searching for style info: %r", query)

        async with AsyncDDGS() as ddgs:
            results = await ddgs.atext(query, max_results=5)

        if not results:
            logger.warning("No search results for: %r", query)
            return None

        snippets = [r.get("body", "") for r in results if r.get("body")]
        combined = "\n".join(snippets)
        logger.info("Collected %d search snippets (%d chars)", len(snippets), len(combined))
        return combined

    except Exception:
        logger.exception("Web search failed for style: %r", style)
        return None


async def analyze_style(style: str, search_context: str | None, config: Config) -> str | None:
    """Use Ollama to analyze style and generate music description tags."""
    try:
        client = AsyncClient(host=config.ollama_host)

        user_content = f"Music style: {style}"
        if search_context:
            user_content += f"\n\nWeb search results about this style:\n{search_context}"

        response = await client.chat(
            model=config.ollama_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
        )

        result = response.message.content.strip()
        logger.info("LLM analysis result: %r", result)
        return result

    except Exception:
        logger.exception("Ollama analysis failed (host=%s, model=%s)", config.ollama_host, config.ollama_model)
        return None


async def research_style(style: str, config: Config) -> str:
    """Research a music style using web search + LLM analysis.

    Returns the enriched style description, or the original style string
    as fallback if research fails.
    """
    search_context = await search_style_info(style)

    analysis = await analyze_style(style, search_context, config)
    if analysis:
        return analysis

    logger.warning("Style research failed, falling back to original input: %r", style)
    return style
