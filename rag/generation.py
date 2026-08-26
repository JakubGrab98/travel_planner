"""Grounded itinerary generation: retrieve guide chunks, then a bounded tool-use round-trip."""
import json
import logging

from clients.anthropic_client import get_anthropic_client
from core import config
from providers.tools import execute_tool_call
from rag.retrieval import retrieve_guide_chunks

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "You are a helpful travel assistant. Create a day-by-day travel itinerary using the "
    "traveler's preferences and the guide excerpts provided below. If no guide excerpts are "
    "provided, say so explicitly and fall back to your general knowledge, noting that local "
    "guide data wasn't available for this destination. End your response with a 'Sources:' "
    "line listing the city and section of every guide excerpt you actually used.\n\n"
    "You also have access to two tools: search_flights and search_hotels, which return live "
    "prices. Only call search_flights if the traveler gave you both a departure city and "
    "concrete travel dates, and only call search_hotels if they gave you a destination city "
    "and concrete travel dates.\n\n"
    "This is a one-shot form submission, not a conversation -- the traveler will not see "
    "this response until it's final and cannot reply to a follow-up question. If required "
    "details for a tool are missing, do not call that tool, and do not ask the traveler to "
    "provide them either: never end your response with a question or a request for more "
    "information. Always deliver a complete itinerary using only what was provided, and "
    "simply note in passing that live prices weren't looked up for the parts you couldn't "
    "search."
)


def _extract_text(response) -> str:
    return "".join(block.text for block in response.content if block.type == "text")


def generate_itinerary(
    destination: str,
    days: int,
    budget: str,
    interests: str,
    travel_style: str,
    departure_city: str = "",
    date_from: str = "",
    date_to: str = "",
    tools: list[dict] | None = None,
) -> str:
    """Generate a RAG-grounded travel itinerary, optionally enriched with live flight/hotel
    data via a single bounded tool-calling round-trip.

    Args:
        destination (str): destination city name.
        days (int): trip length in days.
        budget (str): budget tier (e.g. "Low", "Medium", "High").
        interests (str): free-text interests (e.g. "museums, hiking, food").
        travel_style (str): travel style (e.g. "Relaxed", "Adventurous", "Cultural").
        departure_city (str): optional departure city; empty string means not supplied.
        date_from (str): optional ISO YYYY-MM-DD trip start date; empty string means not
            supplied.
        date_to (str): optional ISO YYYY-MM-DD trip end date; empty string means not
            supplied.
        tools (list[dict] | None): Claude tool definitions (e.g. tools.ALL_TOOLS). When the
            model responds with tool_use, exactly one follow-up call resolves it -- never a
            multi-round agent loop.

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
        f"Travel style: {travel_style}\n"
    )
    if departure_city:
        user_message += f"Departure city: {departure_city}\n"
    if date_from:
        user_message += f"Trip start date: {date_from}\n"
    if date_to:
        user_message += f"Trip end date: {date_to}\n"
    user_message += f"\nGuide excerpts:\n{context}"

    client = get_anthropic_client()
    messages = [{"role": "user", "content": user_message}]
    request_kwargs = {
        "model": config.CHAT_MODEL,
        "max_tokens": 1500,
        "system": _SYSTEM_PROMPT,
        "messages": messages,
    }
    if tools:
        request_kwargs["tools"] = tools

    response = client.messages.create(**request_kwargs)

    if response.stop_reason != "tool_use":
        return _extract_text(response)

    tool_results = []
    for block in response.content:
        if block.type != "tool_use":
            continue
        result = execute_tool_call(block.name, block.input)
        tool_results.append(
            {"type": "tool_result", "tool_use_id": block.id, "content": json.dumps(result)}
        )

    follow_up_messages = messages + [
        {"role": "assistant", "content": response.content},
        {"role": "user", "content": tool_results},
    ]
    # No `tools` kwarg here: the bounded single round-trip from the spec's "Approach C" --
    # forces a final text answer, no further tool-calling rounds.
    follow_up_response = client.messages.create(
        model=config.CHAT_MODEL,
        max_tokens=1500,
        system=_SYSTEM_PROMPT,
        messages=follow_up_messages,
    )
    return _extract_text(follow_up_response)
