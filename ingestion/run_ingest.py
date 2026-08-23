"""CLI entrypoint: fetch, clean, chunk, embed, and store each configured city's article."""
import logging

from embeddings import embed_texts
from ingestion.chunk import chunk_sections
from ingestion.cities import CITY_LIST
from ingestion.clean import clean_wikitext
from ingestion.fetch import ArticleNotFoundError, fetch_article
from ingestion.store import upsert_chunks

logger = logging.getLogger(__name__)


def run() -> None:
    """Ingest every city in CITY_LIST: fetch -> clean -> chunk -> embed -> upsert.

    Per-city failures are logged and skipped rather than aborting the whole run, so the
    same loop body can later become one Airflow task per city without changes.
    """
    ingested = 0
    total_chunks = 0

    for entry in CITY_LIST:
        title, city, article_id = entry["title"], entry["city"], entry["article_id"]
        try:
            article = fetch_article(title)
            sections = clean_wikitext(article.wikitext)
            chunks = chunk_sections(
                sections, article_id=article_id, city=city, source_url=article.source_url
            )
            if not chunks:
                logger.warning("No usable content extracted for %s, skipping.", title)
                continue

            vectors = embed_texts([chunk.text for chunk in chunks], input_type="document")
            upsert_chunks(chunks, vectors)

            logger.info(
                "Ingested %s: %d sections -> %d chunks", title, len(sections), len(chunks)
            )
            ingested += 1
            total_chunks += len(chunks)
        except ArticleNotFoundError:
            logger.error("Article not found, skipping: %s", title)
        except Exception:
            logger.exception("Failed to ingest %s, skipping.", title)

    logger.info("Ingested %d/%d cities, %d total chunks", ingested, len(CITY_LIST), total_chunks)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(name)s: %(message)s")
    run()
