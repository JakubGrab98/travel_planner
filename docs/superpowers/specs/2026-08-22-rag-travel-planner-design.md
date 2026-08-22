# Travel Planner RAG Portfolio Project — Design

## Purpose

Repurpose the existing (unfinished, ~1 year old) travel-planner Streamlit app into a portfolio
project demonstrating data-engineering skills extended with applied AI: a real ingestion
pipeline into a vector store, retrieval-augmented itinerary generation, and a bounded
function-calling layer over live travel data.

**Target audience:** data engineer hiring reviewers evaluating "extends into AI" capability.
The pipeline/orchestration quality matters at least as much as the LLM output quality.

## Goals

- A real ingestion pipeline (Wikivoyage → cleaned → chunked → embedded → pgvector),
  orchestrated with Airflow, that a reviewer can point to as data-engineering work.
- A working RAG query path: user trip request → retrieve relevant guide content →
  grounded itinerary generation.
- A bounded, testable function-calling step that pulls in live flight/hotel data when
  the user's input supports it, without becoming an unpredictable autonomous agent.
- A deployed, clickable demo for the core RAG + flight-search path.
- Fixed versions of the known bugs in the reused flight/scraper code.

## Non-goals

- No autonomous multi-step agent loop (rejected: Approach B, tool-calling agent) — reliability
  and testability for a timed portfolio review matter more than agent flash.
- No second vector database service — pgvector on the existing Postgres instance only.
- No hosted/live Selenium scraping — booking.com scraping stays local-only, documented.
- No CRUD "search parameters" page — dropped, doesn't serve the RAG story.
- Retrieval evaluation harness is a stretch goal (Phase 5), not required for core completion.

## Architecture

```
┌─────────────── Airflow (ingestion, offline) ────────────────┐
│ DAG: wikivoyage_ingest                                      │
│  fetch_dump → clean_normalize → chunk_articles →             │
│  embed_batch → upsert_pgvector                               │
│  (idempotent re-runs per city/article; task-level retries)   │
└────────────────────────┬───────────────────────────────────┘
                          ▼
               Postgres + pgvector
        (guide_chunks table: embeddings + source text)
                          ▲
┌─────────────────────────┴───────────────────────────────────┐
│ Streamlit app (query-time, online)                           │
│                                                                │
│  user input → retrieve_guide_chunks(query)   [always runs]   │
│            → single LLM call w/ tools:                        │
│                 - search_flights (Kiwi API)                   │
│                 - search_hotels (Booking Selenium, local only) │
│              model decides which tools to invoke based on     │
│              what the user actually supplied                  │
│            → itinerary grounded in retrieved guide text +     │
│              (optional) live flight/hotel data                │
└────────────────────────────────────────────────────────────────┘
```

## Components

### Ingestion pipeline (Airflow DAG: `wikivoyage_ingest`)
- **fetch_dump**: download/refresh the Wikivoyage export for a configured set of
  destinations (start small — a fixed city list, not the full dump).
- **clean_normalize**: strip wiki markup/boilerplate, normalize whitespace/encoding.
- **chunk_articles**: section-aware chunking (don't split mid-section where avoidable).
- **embed_batch**: batch embedding calls, rate-limit aware.
- **upsert_pgvector**: idempotent upsert keyed on `(article_id, chunk_index)` so re-runs
  don't duplicate rows.
- Each task is a thin wrapper around a plain Python function importable and unit-testable
  without Airflow running.
- Task-level failures (one bad article) are logged and skipped, not fatal to the DAG run.

### Vector store
- Single Postgres instance, `pgvector` extension enabled.
- `guide_chunks` table: `id, article_id, chunk_index, city, source_url, text, embedding vector(N)`.
- Airflow's own metadata schema lives in the same Postgres instance (separate schema),
  not a second database service.

### Retrieval module
- `retrieve_guide_chunks(query: str, k: int) -> list[Chunk]`: embed the query, cosine-similarity
  search via pgvector, return top-k with source city/url for citation in the UI.

### Query orchestration (replaces `itinerary_tool.py`)
- One LLM call per user request, given `search_flights` and `search_hotels` as callable tools
  (OpenAI SDK native tool-calling — dropping LangChain here since current usage is a single
  trivial prompt chain, and native tool-calling is more transparent for a portfolio review).
- Retrieved guide chunks are always injected as context; tool calls are optional, decided by
  the model based on whether the user supplied enough info (departure city + dates → flights
  become callable; destination + dates → hotels become callable).
- Final response cites which guide sections informed it.

### Reused/fixed components
- `flight_search.py` / `flight_data.py`: fix the bug where `get_flight_data` returning `None`
  (no results) crashes the caller — wrap as a tool that returns a structured "no flights found"
  result instead of raising.
- `scraper/booking.py`: fix `change_currency` ignoring its `currency_code` parameter; fix
  `scraper/run_bot.py`'s unqualified import. Wrapped as a callable tool instead of a separate
  Streamlit page; stays local-only (never invoked in the deployed environment).

### Dropped components
- `sql/sql.py`, `pages/flight_searcher_parameters.py` — removed entirely (half-built CRUD,
  SQL-injection bug, doesn't serve the RAG story).

## Data flow

**Ingestion (offline, scheduled/manual):** Wikivoyage dump → clean → chunk → embed → pgvector.
Re-running is safe (idempotent upsert); adding a new city means adding it to the fetch list
and re-running the DAG.

**Query (online):** user fills itinerary form → `retrieve_guide_chunks` always runs → one
LLM call with tools available → model optionally calls `search_flights`/`search_hotels` →
model produces itinerary text grounded in retrieved chunks and (if called) live data →
Streamlit renders result, citing sources.

## Error handling

- Ingestion: per-task/per-article failures are logged and skipped; DAG run as a whole
  succeeds if the majority of articles ingest cleanly. Airflow retries handle transient
  failures (network, rate limits).
- Query-time: any tool failure (API error, scraper timeout/selector mismatch) degrades
  gracefully — the itinerary still generates from RAG context alone, with an explicit note
  that live pricing/availability wasn't available. No unhandled exceptions reach the UI.
- Retrieval returning zero chunks (e.g., unsupported city) is handled explicitly — model is
  told no local guide data exists and generates from general knowledge with that caveat shown.

## Testing

- Ingestion: unit tests for `clean_normalize` and `chunk_articles` as pure functions,
  independent of Airflow.
- Retrieval: unit test against a small fixture set of known embeddings/expected neighbors.
- Tool wrappers (`search_flights`, `search_hotels`): unit tests with mocked HTTP/Selenium,
  covering the empty-result and error paths specifically (these are today's known bugs).
- Query orchestration: test with the LLM's tool-call decision mocked, verifying each tool
  path and the no-tool-called path independently.
- Phase 5 (stretch): a small labeled query set (~15-20 queries → expected city/article)
  scored for retrieval hit-rate.

## Deployment

- Hosted (e.g. Render/Fly.io): Streamlit app + Postgres/pgvector reachable from it.
  The hosted app only ever *reads* the `guide_chunks` table — it does not run the Airflow
  DAG or the Selenium scraper.
- Ingestion (Airflow) and the hotel scraper run locally only, via `docker compose up`,
  documented in the README with setup steps and a demo GIF/walkthrough for the parts that
  aren't live-clickable.

## Phased delivery

Each phase leaves the project in a working, demoable state — later phases are additive,
not required to reach "done."

1. **Core RAG**: Postgres+pgvector, a plain ingestion script (pre-Airflow) for a handful of
   cities, RAG-grounded itinerary generation working end-to-end locally.
2. **Orchestration**: wrap the ingestion script as the `wikivoyage_ingest` Airflow DAG.
3. **Layer 2 tools**: add the single-turn function-calling step (flight search + hotel
   scraper as tools); fix the known bugs in both during this phase.
4. **Deploy + docs**: host the app + DB, write the README/architecture write-up.
5. **Stretch**: retrieval evaluation harness.

## Open items for implementation planning

- Exact fixed city list for the initial Wikivoyage ingest (small, curated — not the full dump).
- Chunk size/overlap parameters — to be tuned empirically during Phase 1.
- Embedding model choice (OpenAI `text-embedding-3-small` is the default assumption pending
  confirmation during planning).
