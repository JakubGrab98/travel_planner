"""Idempotent upsert of chunks (with embeddings) into the guide_chunks table."""
from core.db import get_connection
from ingestion.chunk import Chunk

_UPSERT_SQL = """
INSERT INTO guide_chunks (article_id, chunk_index, city, section_title, source_url, text, embedding)
VALUES (%(article_id)s, %(chunk_index)s, %(city)s, %(section_title)s, %(source_url)s, %(text)s, %(embedding)s)
ON CONFLICT (article_id, chunk_index) DO UPDATE SET
    text = EXCLUDED.text,
    embedding = EXCLUDED.embedding,
    city = EXCLUDED.city,
    section_title = EXCLUDED.section_title,
    source_url = EXCLUDED.source_url;
"""


def upsert_chunks(chunks: list[Chunk], embeddings: list[list[float]]) -> None:
    """Idempotently insert or update chunks and their embeddings.

    Args:
        chunks (list[Chunk]): chunk metadata/text, in the same order as `embeddings`.
        embeddings (list[list[float]]): one embedding vector per chunk.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            for chunk, embedding in zip(chunks, embeddings):
                cur.execute(
                    _UPSERT_SQL,
                    {
                        "article_id": chunk.article_id,
                        "chunk_index": chunk.chunk_index,
                        "city": chunk.city,
                        "section_title": chunk.section_title,
                        "source_url": chunk.source_url,
                        "text": chunk.text,
                        "embedding": embedding,
                    },
                )
