"""Embedding generation via Voyage AI, shared by ingestion and query-time retrieval."""
import logging
import time

import voyageai

import config

logger = logging.getLogger(__name__)

_client = None
_BATCH_SIZE = 25
_MAX_RETRIES = 5
_RETRY_BACKOFF_SECONDS = 20


def _get_voyage_client() -> voyageai.Client:
    global _client
    if _client is None:
        _client = voyageai.Client(api_key=config.VOYAGE_API_KEY)
    return _client


def _embed_batch_with_retry(client: voyageai.Client, batch: list[str], input_type: str):
    last_error = None
    for attempt in range(_MAX_RETRIES):
        try:
            return client.embed(
                batch,
                model=config.EMBEDDING_MODEL,
                input_type=input_type,
                output_dimension=config.EMBEDDING_DIMENSION,
            )
        except voyageai.error.RateLimitError as exc:
            last_error = exc
            logger.warning(
                "Voyage rate limit hit (attempt %d/%d), backing off %ds",
                attempt + 1, _MAX_RETRIES, _RETRY_BACKOFF_SECONDS,
            )
            time.sleep(_RETRY_BACKOFF_SECONDS)
    raise last_error


def embed_texts(texts: list[str], input_type: str) -> list[list[float]]:
    """Embed a list of texts with Voyage AI, batching to stay within request limits.

    Batches are kept small (well under a reduced-tier 10K TPM cap) and rate-limit errors
    are retried with a fixed backoff — Voyage throttles accounts with no payment method on
    file to 3 requests/min regardless of the free token allowance, so this keeps ingestion
    working (slower) rather than failing outright under that tier.

    Args:
        texts (list[str]): texts to embed.
        input_type (str): "document" for ingestion-time text, "query" for a user query —
            Voyage uses this to optimize asymmetric retrieval quality.

    Returns:
        list[list[float]]: one embedding vector per input text, same order as `texts`.
    """
    client = _get_voyage_client()
    embeddings: list[list[float]] = []
    for i in range(0, len(texts), _BATCH_SIZE):
        batch = texts[i : i + _BATCH_SIZE]
        result = _embed_batch_with_retry(client, batch, input_type)
        embeddings.extend(result.embeddings)
    return embeddings
