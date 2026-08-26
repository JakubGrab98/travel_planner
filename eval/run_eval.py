"""CLI: score rag.retrieval.retrieve_guide_chunks's hit-rate against EVAL_QUERIES.

Requires the local Postgres (docker compose) populated with the ingested corpus, and a
real Voyage API call per query. Run: python -m eval.run_eval
"""
import logging

from eval.queries import EVAL_QUERIES
from rag.retrieval import retrieve_guide_chunks

logger = logging.getLogger(__name__)


def run() -> None:
    hits = 0
    for case in EVAL_QUERIES:
        query, expected_city = case["query"], case["expected_city"]
        results = retrieve_guide_chunks(query, k=5)

        top = "none" if not results else f"{results[0].city} (distance={results[0].distance:.3f})"
        if expected_city is None:
            passed = len(results) == 0
        else:
            cities = {r.city for r in results}
            passed = expected_city in cities

        hits += passed
        status = "PASS" if passed else "FAIL"
        logger.info("[%s] %-70s expected=%-16s top_hit=%s", status, query, expected_city, top)

    total = len(EVAL_QUERIES)
    logger.info("Hit-rate: %d/%d (%.0f%%)", hits, total, 100 * hits / total)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    run()
