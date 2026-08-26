"""Airflow DAG: wraps the Phase 1 ingestion pipeline (ingestion.fetch, ingestion.clean,
ingestion.chunk, embeddings, ingestion.store) as five per-stage, per-city dynamically
mapped tasks, per the design spec's wikivoyage_ingest diagram.

Fault isolation: dynamic task mapping gives each city its own map index end-to-end. A city
whose article is missing (ArticleNotFoundError) or yields no usable chunks is marked
`skipped` via AirflowSkipException, which Airflow's default `all_success` trigger rule
automatically cascades to that city's downstream mapped task instances -- sibling cities'
map indices are entirely unaffected. Genuinely transient failures (network, rate limits,
DB connectivity) are left to raise normally so Airflow's own per-task-instance retries
apply on top of the retry/backoff each wrapped function already does internally.
"""
from __future__ import annotations

import logging
from dataclasses import asdict
from datetime import timedelta

import pendulum
from airflow.sdk import dag, task
from airflow.sdk.exceptions import AirflowSkipException

from clients.embeddings import embed_texts
from ingestion.chunk import Chunk, chunk_sections
from ingestion.cities import CITY_LIST
from ingestion.clean import Section, clean_wikitext
from ingestion.fetch import ArticleNotFoundError, fetch_article
from ingestion.store import upsert_chunks

logger = logging.getLogger(__name__)

DEFAULT_ARGS = {"retries": 2, "retry_delay": timedelta(minutes=1)}


@dag(
    dag_id="wikivoyage_ingest",
    schedule=None,
    start_date=pendulum.datetime(2026, 1, 1, tz="UTC"),
    catchup=False,
    max_active_runs=1,
    default_args=DEFAULT_ARGS,
    tags=["ingestion", "rag", "wikivoyage"],
)
def wikivoyage_ingest():

    @task
    def fetch_dump(entry: dict) -> dict:
        title, city, article_id = entry["title"], entry["city"], entry["article_id"]
        try:
            article = fetch_article(title)
        except ArticleNotFoundError:
            logger.error("Article not found, skipping: %s", title)
            raise AirflowSkipException(f"Wikivoyage article not found: {title!r}")
        return {
            "article_id": article_id, "city": city, "title": title,
            "wikitext": article.wikitext, "source_url": article.source_url,
        }

    @task
    def clean_normalize(fetch_result: dict) -> dict:
        try:
            sections = clean_wikitext(fetch_result["wikitext"])
        except Exception:
            logger.exception("Failed to clean wikitext for %s, skipping.", fetch_result["title"])
            raise AirflowSkipException(f"clean_wikitext failed for {fetch_result['title']!r}")
        return {
            "article_id": fetch_result["article_id"], "city": fetch_result["city"],
            "title": fetch_result["title"], "source_url": fetch_result["source_url"],
            "sections": [asdict(s) for s in sections],
        }

    @task
    def chunk_articles(clean_result: dict) -> dict:
        sections = [Section(**s) for s in clean_result["sections"]]
        try:
            chunks = chunk_sections(
                sections, article_id=clean_result["article_id"],
                city=clean_result["city"], source_url=clean_result["source_url"],
            )
        except Exception:
            logger.exception("Failed to chunk sections for %s, skipping.", clean_result["title"])
            raise AirflowSkipException(f"chunk_sections failed for {clean_result['title']!r}")
        if not chunks:
            logger.warning("No usable content extracted for %s, skipping.", clean_result["title"])
            raise AirflowSkipException(f"No chunks extracted for {clean_result['title']!r}")
        return {
            "article_id": clean_result["article_id"], "city": clean_result["city"],
            "title": clean_result["title"], "chunks": [asdict(c) for c in chunks],
        }

    # Pinned to the `voyage_api` pool (1 slot, created once via `airflow pools set`) so the
    # 5 mapped cities embed serially rather than concurrently -- Voyage's account-level rate
    # limit (3 req/min on this account's tier) is shared across all of them, and hammering it
    # in parallel exhausts embed_texts's own retry budget before the shared queue can drain.
    @task(pool="voyage_api")
    def embed_batch(chunk_result: dict) -> dict:
        texts = [c["text"] for c in chunk_result["chunks"]]
        vectors = embed_texts(texts, input_type="document")
        return {
            "article_id": chunk_result["article_id"], "city": chunk_result["city"],
            "title": chunk_result["title"], "chunks": chunk_result["chunks"],
            "embeddings": vectors,
        }

    @task
    def upsert_pgvector(embed_result: dict) -> dict:
        chunks = [Chunk(**c) for c in embed_result["chunks"]]
        upsert_chunks(chunks, embed_result["embeddings"])
        logger.info("Ingested %s: %d chunks", embed_result["title"], len(chunks))
        return {"city": embed_result["city"], "ingested_chunks": len(chunks)}

    fetch_results = fetch_dump.expand(entry=CITY_LIST)
    clean_results = clean_normalize.expand(fetch_result=fetch_results)
    chunk_results = chunk_articles.expand(clean_result=clean_results)
    embed_results = embed_batch.expand(chunk_result=chunk_results)
    upsert_pgvector.expand(embed_result=embed_results)


wikivoyage_ingest()
