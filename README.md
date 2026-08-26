# Travel Planner — RAG Portfolio Project

A Streamlit travel-itinerary generator grounded in retrieval-augmented generation over
Wikivoyage city guides, backed by a Postgres/pgvector store and an Airflow-orchestrated
ingestion pipeline.

Architecture and phased design: [docs/superpowers/specs/2026-08-22-rag-travel-planner-design.md](docs/superpowers/specs/2026-08-22-rag-travel-planner-design.md).

## Stack

- **Generation**: Anthropic Claude Haiku 4.5 (Messages API)
- **Embeddings**: Voyage AI (`voyage-3.5`)
- **Vector store**: Postgres 16 + pgvector
- **Ingestion orchestration**: Apache Airflow 3.3 (`LocalExecutor`, single-container `standalone` mode)
- **App**: Streamlit
- **Live tool-calling**: Kiwi Tequila API (flights), Amadeus Hotel Search API (hotels) —
  Claude decides whether to call either based on what the traveler supplied
- **Source corpus**: Wikivoyage (MediaWiki Action API), 5 seed cities (Rome, Paris, Barcelona, Tokyo, New York City)

## Setup

```bash
cp .env.example .env
# edit .env: set ANTHROPIC_API_KEY, VOYAGE_API_KEY, and a POSTGRES_PASSWORD
```

### Bring up the database and Airflow

```bash
docker compose up -d --build
```

This starts two services:
- `postgres` — Postgres + pgvector, holding the app's `guide_chunks` table (database
  `travel_planner`)
- `airflow` — Airflow 3.3 in `standalone` mode (webserver/api-server + scheduler +
  triggerer in one process), holding its own metadata in a separate `airflow` database on
  the same Postgres server

**First-time only**, if the `postgres` volume already existed before Airflow was added (i.e.
you're resuming a Phase-1-only checkout): the `airflow` database won't be auto-created by
`db/init/02_airflow_db.sql` (Postgres only runs init scripts against a brand-new, empty data
volume). Create it once manually:

```bash
docker compose exec postgres psql -U $POSTGRES_USER -d travel_planner -c "CREATE DATABASE airflow;"
```

On a genuinely fresh `docker compose up` (new volume), this happens automatically.

### Run the ingestion pipeline

Either run it directly (no Airflow needed):

```bash
python -m venv .venv && source .venv/bin/activate   # .venv\Scripts\activate on Windows
pip install -r requirements.txt
python -m ingestion.run_ingest
```

...or trigger the Airflow DAG:

```bash
# one-time: create the pool that serializes embedding calls against Voyage's rate limit
docker compose exec airflow airflow pools set voyage_api 1 "Serialize Voyage AI embed calls"

docker compose exec airflow airflow dags unpause wikivoyage_ingest
docker compose exec airflow airflow dags trigger wikivoyage_ingest
```

Watch progress at the Airflow UI: **http://localhost:8080**. Both paths write to the same
idempotent `guide_chunks` table (upsert on `(article_id, chunk_index)`), so either can be
re-run safely without duplicating data.

**Airflow admin credentials** are auto-generated on first boot and printed to the logs:

```bash
docker compose logs airflow | grep -i password
```

### Run the app

```bash
streamlit run Home_Page.py
```

Fill in a destination, days, budget, interests, and travel style, then "Start Planning" —
the itinerary is grounded in retrieved Wikivoyage content for the 5 seed cities, with a
"Sources" line citing which guide sections were used. For any other destination, it falls
back to general knowledge with an explicit note that no local guide data was available.

## Tests

```bash
pytest -q
```

Covers ingestion cleaning/chunking and RAG retrieval/generation, all pure-function or mocked
(no live DB/API calls, no Docker required). The Airflow DAG's own integrity test is isolated
to the Airflow container's dependency set (kept out of the app's `requirements.txt`
deliberately) and runs via:

```bash
docker compose exec airflow python -m pytest /opt/airflow/project/tests/dags -v
```

## Deployment

The hosted deployment uses two free-tier services — the ingestion pipeline (and Airflow
itself) stay local-only, per the design spec; the hosted app only ever *reads* the vector
store.

- **App: [Streamlit Community Cloud](https://share.streamlit.io)** — free, and since
  secrets entered in its dashboard are exposed as real environment variables, the app's
  existing `config.py`/`os.getenv()` pattern works with no code changes.
- **Database: [Neon](https://neon.tech)** — free tier, native pgvector, scale-to-zero with
  automatic resume on the next query (rather than a hard multi-day pause requiring manual
  reactivation, which several alternatives have).

### One-time setup

1. **Create a Neon project** and grab its connection details (host, port, database, user,
   password — Neon presents these as a single connection string).
2. **Create the schema on Neon**: run the contents of [db/init/01_init.sql](db/init/01_init.sql)
   against the new database (simplest via Neon's own SQL editor).
3. **Populate it** by running the ingestion script once, pointed at Neon via inline env var
   overrides (so your local `.env` never mixes with production credentials):
   ```bash
   POSTGRES_HOST=<neon-host> POSTGRES_PORT=<neon-port> POSTGRES_DB=<neon-db> \
   POSTGRES_USER=<neon-user> POSTGRES_PASSWORD=<neon-password> POSTGRES_SSLMODE=require \
   python -m ingestion.run_ingest
   ```
4. **Create the Streamlit Community Cloud app**: connect this GitHub repo, set the main
   file to `Home_Page.py`, and set the Python version to 3.11 under Advanced Settings.
5. **Add secrets** in the Streamlit Cloud dashboard (root-level `key = value`, not nested):
   `ANTHROPIC_API_KEY`, `VOYAGE_API_KEY`, `KIWI_API_KEY`, `AMADEUS_CLIENT_ID`/
   `AMADEUS_CLIENT_SECRET` (optional — the app degrades gracefully without them), and the
   Neon `POSTGRES_*` values including `POSTGRES_SSLMODE=require`.

## Project status

- **Phase 1 — Core RAG**: done. Ingestion script, RAG-grounded generation, live-verified.
- **Phase 2 — Airflow orchestration**: done. `wikivoyage_ingest` DAG, live-verified
  end-to-end (including idempotency across repeated runs).
- **Phase 3 — Live tool-calling** (flight/hotel search): done. Live-verified against the
  real Kiwi API and Claude; hotel search implemented but not yet live-verified end-to-end
  (Amadeus self-service signup still pending).
- **Phase 4 — Deployment**: setup instructions above ready; live deployment pending account
  creation on Neon/Streamlit Community Cloud.
- **Phase 5 — Retrieval evaluation** (stretch): not started.
