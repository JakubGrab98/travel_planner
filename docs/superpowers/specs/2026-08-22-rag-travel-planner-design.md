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
- No web scraping anywhere in the project (see Hotel data source decision below).
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
│                 - search_flights (Kiwi Tequila API)            │
│                 - search_hotels (Amadeus Hotel Search API)     │
│              model decides which tools to invoke based on     │
│              what the user actually supplied                  │
│            → itinerary grounded in retrieved guide text +     │
│              (optional) live flight/hotel data                │
└────────────────────────────────────────────────────────────────┘
```

Both tool APIs are official, free-tier, self-service developer APIs — no scraping,
no partner-approval process, no cost. Both run fine in the hosted deployment, not just
locally.

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
- Airflow's own metadata lives in the same Postgres *instance* — as implemented in Phase 2,
  this is a separate Postgres *database* (`airflow`, alongside `travel_planner`), not merely
  a separate schema within one database: Airflow's own migrations expect to own their target
  database cleanly, and a non-default schema is a far less-traveled, more fragile path for
  the same "no second DB service" benefit this line originally called for.

### Retrieval module
- `retrieve_guide_chunks(query: str, k: int) -> list[Chunk]`: embed the query, cosine-similarity
  search via pgvector, return top-k with source city/url for citation in the UI.

### Query orchestration (replaces `itinerary_tool.py`, now `rag/generation.py`)
- One Claude Haiku 4.5 call per user request (Anthropic Messages API — not OpenAI; switched
  during Phase 1 planning since the account already had Anthropic credits, see Phase 1 build
  notes), given `search_flights` and `search_hotels` as callable tools via Claude's native
  `tools`/`tool_use` mechanism — dropping LangChain here since current usage is a single
  trivial prompt chain, and native tool-calling is more transparent for a portfolio review.
- Retrieved guide chunks are always injected as context; tool calls are optional, decided by
  the model based on whether the user supplied enough info (departure city + dates → flights
  become callable; destination + dates → hotels become callable).
- Final response cites which guide sections informed it.

### Reused/fixed components
- `flight_search.py` / `flight_data.py`: fix the bug where `get_flight_data` returning `None`
  (no results) crashes the caller — wrap as a tool that returns a structured "no flights found"
  result instead of raising. Wrapped as a callable tool instead of a separate Streamlit page.

### New component: hotel search tool
- Replaces the Selenium/booking.com scraper entirely. Thin wrapper around the **Amadeus Hotel
  Search API** (free self-service test tier — official vendor, no scraping, no approval
  process, no cost). Same shape as the flight tool: structured params in, structured
  `HotelOffer`-style result out, "no results" handled as a normal structured response rather
  than an exception.
- Trade-off, disclosed in the README: the free test environment returns realistic but not
  fully live production pricing/availability data. Acceptable for a portfolio demo; not
  presented as real bookable inventory.

### Dropped components
- `sql/sql.py`, `pages/flight_searcher_parameters.py` — removed entirely (half-built CRUD,
  SQL-injection bug, doesn't serve the RAG story).
- `scraper/` (Selenium booking.com bot), `pages/booking_searcher.py` — removed entirely,
  replaced by the Amadeus hotel search tool above. Eliminates the ToS/DOM-fragility risk
  rather than merely containing it to local-only use.

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
- Query-time: any tool failure (API error, no matching results) degrades
  gracefully — the itinerary still generates from RAG context alone, with an explicit note
  that live pricing/availability wasn't available. No unhandled exceptions reach the UI.
- Retrieval returning zero chunks (e.g., unsupported city) is handled explicitly — model is
  told no local guide data exists and generates from general knowledge with that caveat shown.

## Testing

- Ingestion: unit tests for `clean_normalize` and `chunk_articles` as pure functions,
  independent of Airflow.
- Retrieval: unit test against a small fixture set of known embeddings/expected neighbors.
- Tool wrappers (`search_flights`, `search_hotels`) — done: `tests/test_flight_search.py`,
  `tests/test_hotel_search.py`, `tests/test_tools.py`, mocked, covering empty-result and
  error paths. Two real bugs surfaced and fixed during Phase 3 beyond the originally-named
  flight-tool crash: Kiwi's `date_from`/`date_to` are a search *window*, not fixed dates
  (the actual round trip needs `nights_in_dst_from`/`nights_in_dst_to`); and
  `get_airport_code` took Kiwi's first search result unconditionally, which for "Rome"
  returned San Salvador first (substring match on "Rome**ro**") — silently wrong data, not
  a crash, and arguably the more serious of the two.
- Query orchestration — done: `tests/rag/test_generation.py` covers the tool-use round-trip
  (tool called + resolved in one bounded follow-up call, and the no-tool-needed path) with
  the LLM's tool-call decision mocked.
- Phase 5 (stretch) — done: `eval/run_eval.py`, an 18-query labeled set (15 positive across
  the 5 cities, 3 negative for never-ingested cities) scored for retrieval hit-rate. Found
  and fixed a real `max_distance` tuning gap: 0.45 (Phase 1's single-spot-check value) cut
  off a genuine Paris hit at 0.457 while the closest known cross-city false positive sat at
  0.479 — retuned to 0.46, confirmed 18/18 (100%) after.

## Deployment

- **Hosted — done**: Streamlit Community Cloud (app) + Neon (Postgres+pgvector, free tier,
  scale-to-zero) — not Render/Fly.io as originally sketched here; researched during Phase 4
  planning and Neon won on native pgvector support plus auto-resume behavior (vs.
  alternatives with a hard multi-day inactivity pause requiring manual reactivation). The
  flight (Kiwi) tool is confirmed working live on the hosted app; the hotel (Amadeus) tool
  is deployed but not yet live-verified end-to-end (signup still pending, see Open items).
  The hosted app only ever *reads* the `guide_chunks` table — it does not run the Airflow DAG.
- Ingestion (Airflow) runs locally only, via `docker compose up`; populating the hosted
  Neon database is a separate one-time step (`ingestion/run_ingest.py` pointed at Neon via
  env var overrides), documented in the README.

## Phased delivery

Each phase leaves the project in a working, demoable state — later phases are additive,
not required to reach "done."

1. **Core RAG** — done. Postgres+pgvector, a plain ingestion script (`ingestion/run_ingest.py`),
   RAG-grounded itinerary generation working end-to-end locally, live-verified (822 chunks
   across 5 cities via real Wikivoyage/Voyage/Claude calls).
2. **Orchestration** — done. `wikivoyage_ingest` Airflow 3.3 DAG (`dags/wikivoyage_ingest.py`),
   LocalExecutor via `airflow standalone` in one docker-compose service. Implementation notes
   beyond the original one-line description:
   - **TaskFlow dynamic task mapping over `CITY_LIST`, one task per pipeline stage**
     (`fetch_dump`/`clean_normalize`/`chunk_articles`/`embed_batch`/`upsert_pgvector`, matching
     this doc's own diagram), each `.expand()`-ed over all 5 cities — not one monolithic
     per-city task. Airflow ties each downstream mapped instance to its specific upstream map
     index, giving per-city fault isolation "for free" without `expand_kwargs` complexity.
   - **Fault isolation via `airflow.sdk.exceptions.AirflowSkipException`**, not a sentinel
     dict or bare exception propagation: an expected, non-transient failure (missing article,
     zero chunks) is caught and turned into an explicit `skipped` state, which Airflow's
     default trigger rule cascades to that city's downstream mapped instances automatically.
     Genuinely transient failures are left to raise, so Airflow's own `retries=2` applies on
     top of the retry/backoff `fetch_article`/`embed_texts` already do internally.
   - **`voyage_api` Airflow Pool (1 slot)** pins `embed_batch` to serialized execution — live
     testing surfaced that LocalExecutor runs the 5 mapped `embed_batch` instances
     *concurrently* by default, and 5 cities hammering Voyage's shared account-level rate
     limit at once exhausted `embed_texts`'s own retry budget faster than serial execution
     ever did in Phase 1. The pool restores the same effectively-one-at-a-time embedding
     pattern that worked in Phase 1.
   - Airflow's own metadata lives in a separate `airflow` **database** (see Vector store
     section above), created via `db/init/02_airflow_db.sql` — but since that init script
     only runs against a fresh Postgres volume, an already-existing Phase 1 volume needs it
     created manually once (documented in the README).
   - `Dockerfile.airflow` + `requirements-ingestion.txt` keep Airflow's own large,
     constraint-pinned dependency tree fully isolated from the app's `requirements.txt`.
3. **Layer 2 tools** — done. `tools.py` (schemas + a never-raising dispatcher), `hotel_search.py`/
   `hotel_data.py` (Amadeus's 3-step city→hotel-IDs→offers flow), `rag/generation.py`'s
   bounded single-round tool-use loop. `pages/Flight_Searcher.py` retired, per this doc's own
   "instead of a separate Streamlit page" wording. Live-verified against real Kiwi + Claude,
   including both bugs noted in Testing above; Amadeus path implemented but blocked on signup.
4. **Deploy + docs** — done. Streamlit Community Cloud + Neon (see Deployment above);
   `README.md` covers setup, tests, evaluation, and deployment for all phases.
5. **Stretch** — done. `eval/run_eval.py`, 18/18 (100%) hit-rate after the tuning fix
   described in Testing above.

**Post-Phase-5 cleanup**: the flat root-level modules named throughout this doc
(`config.py`, `db.py`, `utils.py`, `anthropic_client.py`, `embeddings.py`, `flight_search.py`,
`flight_data.py`, `hotel_search.py`, `hotel_data.py`, `tools.py`) were regrouped into
`core/`, `clients/`, `providers/` packages for a cleaner repo structure — same modules, same
behavior, new locations (see `README.md`'s Structure section). Every mention above by bare
filename still refers to the same code, just nested now.

## Open items for implementation planning

- ~~Exact fixed city list for the initial Wikivoyage ingest~~ — resolved in Phase 1: Rome,
  Paris, Barcelona, Tokyo, New York City.
- ~~Chunk size/overlap parameters~~ — resolved in Phase 1: 1000 chars / 150 char overlap,
  section-aware. Retrieval distance cutoff tuned empirically: 0.45 from a single spot check
  during Phase 1, refined to **0.46** during Phase 5 after a systematic 18-query eval
  (`eval/run_eval.py`) found the original value cutting off a genuine hit by a narrow
  margin — see Testing above.
- ~~Embedding model choice~~ — resolved during Phase 1 planning: **Voyage AI `voyage-3.5`**
  (`output_dimension=1024`), not OpenAI as originally assumed here — switched alongside the
  generation model to Anthropic Claude, since Anthropic has no embeddings endpoint of its own
  and Voyage is its recommended embeddings partner (free tier, no scraping/approval process).
- Amadeus self-service account/API key signup, and confirming current test-tier rate limits
  are sufficient for demo purposes. (Still open — Phase 3 work.)
