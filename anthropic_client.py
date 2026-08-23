"""Lazy singleton Anthropic client (mockable in tests)."""
import anthropic

import config

_client = None


def get_anthropic_client() -> anthropic.Anthropic:
    """Return a lazily-created, process-wide Anthropic client.

    Returns:
        anthropic.Anthropic: the shared client instance.
    """
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    return _client
