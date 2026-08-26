"""Retrieval of the most relevant guide chunks for a user query."""
from dataclasses import dataclass

from pgvector import Vector

from clients.embeddings import embed_texts
from core.db import get_connection

_SEARCH_SQL = """
SELECT city, section_title, source_url, text, embedding <=> %(query_embedding)s AS distance
FROM guide_chunks
WHERE embedding <=> %(query_embedding)s < %(max_distance)s
ORDER BY distance
LIMIT %(k)s;
"""

# Empirically tuned, refined using eval/run_eval.py's systematic query set (Phase 5) after
# an initial single-query spot check (Phase 1) proved too strict: a real Paris/Buy hit
# scored 0.457 for a "Paris: shopping, food" query and was being cut off at the old 0.45
# threshold, while the closest known cross-city false positive (Barcelona/Eat, for a
# never-ingested "Lisbon" query) scored 0.479 -- 0.46 sits between the two, but the margin
# is narrow (0.019) and this genuinely is a delicate tuning point, not a robust one. If more
# cities are added or this starts misbehaving, re-run eval/run_eval.py -- it exists
# specifically to make catching a regression here fast rather than another one-off spot check.
_DEFAULT_MAX_DISTANCE = 0.46


@dataclass
class RetrievedChunk:
    """A single guide chunk retrieved for a query, with its similarity distance."""
    city: str
    section_title: str
    source_url: str
    text: str
    distance: float


def retrieve_guide_chunks(
    query: str, k: int = 5, max_distance: float = _DEFAULT_MAX_DISTANCE
) -> list[RetrievedChunk]:
    """Retrieve the k most relevant guide chunks for a user query.

    Args:
        query (str): the user's natural-language request.
        k (int): number of chunks to retrieve.
        max_distance (float): cosine-distance cutoff (0 = identical, 2 = opposite).
            Chunks farther than this are excluded rather than returned as weak,
            likely-irrelevant matches — without this, a query about a city with no ingested
            content would still get back the nearest unrelated city's chunks. Starting value;
            revisit if manual spot-checks show it's too strict/loose for `voyage-3.5`.

    Returns:
        list[RetrievedChunk]: chunks sorted by ascending distance (best match first). Empty
            if the guide_chunks table has no content relevant to the query's destination.
    """
    query_embedding = embed_texts([query], input_type="query")[0]

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                _SEARCH_SQL,
                {
                    # Vector(...) wrapper is required here: unlike an INSERT (where the
                    # target column's type disambiguates a plain list), a bare `<=>`
                    # comparison gives psycopg no column context, so a plain Python list
                    # is sent as a generic array and pgvector's operator can't match it.
                    "query_embedding": Vector(query_embedding),
                    "k": k,
                    "max_distance": max_distance,
                },
            )
            rows = cur.fetchall()

    return [
        RetrievedChunk(
            city=row[0], section_title=row[1], source_url=row[2], text=row[3], distance=row[4]
        )
        for row in rows
    ]
