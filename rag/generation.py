"""Grounded itinerary generation: retrieve guide chunks, then a single Claude call."""
import logging

import config
from anthropic_client import get_anthropic_client
from rag.retrieval import retrieve_guide_chunks

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "You are a helpful travel assistant. Create a day-by-day travel itinerary using the "
    "traveler's preferences and the guide excerpts provided below. If no guide excerpts are "
    "provided, say so explicitly and fall back to your general knowledge, noting that local "
    "guide data wasn't available for this destination. End your response with a 'Sources:' "
    "line listing the city and section of every guide excerpt you actually used."
)


def generate_itinerary(
    destination: str,
    days: int,
    budget: str,
    interests: str,
    travel_style: str,
    tools: list[dict] | None = None,
) -> str:
    """Generate a RAG-grounded travel itinerary.

    Args:
        destination (str): destination city name.
        days (int): trip length in days.
        budget (str): budget tier (e.g. "Low", "Medium", "High").
        interests (str): free-text interests (e.g. "museums, hiking, food").
        travel_style (str): travel style (e.g. "Relaxed", "Adventurous", "Cultural").
        tools (list[dict] | None): optional Claude tool definitions — a Phase 3 hook for
            live flight/hotel tool-calling, forwarded only when provided; unused in Phase 1.

    Returns:
        str: the generated itinerary text.
    """
    query = f"{destination}: {interests}, {travel_style} travel style"
    chunks = retrieve_guide_chunks(query, k=5)

    if chunks:
        context = "\n\n".join(
            f"[{chunk.city} — {chunk.section_title}]\n{chunk.text}" for chunk in chunks
        )
    else:
        context = "(No local guide data available for this destination.)"
        logger.info("No guide chunks retrieved for destination=%s", destination)

    user_message = (
        f"Plan a {days}-day trip to {destination}.\n"
        f"Budget: {budget}\n"
        f"Interests: {interests}\n"
        f"Travel style: {travel_style}\n\n"
        f"Guide excerpts:\n{context}"
    )

    client = get_anthropic_client()
    request_kwargs = {
        "model": config.CHAT_MODEL,
        "max_tokens": 1500,
        "system": _SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": user_message}],
    }
    if tools:
        request_kwargs["tools"] = tools

    response = client.messages.create(**request_kwargs)

    return "".join(block.text for block in response.content if block.type == "text")
