CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS guide_chunks (
    id             SERIAL PRIMARY KEY,
    article_id     TEXT NOT NULL,
    chunk_index    INT NOT NULL,
    city           TEXT NOT NULL,
    section_title  TEXT,
    source_url     TEXT NOT NULL,
    text           TEXT NOT NULL,
    embedding      VECTOR(1024) NOT NULL,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (article_id, chunk_index)
);

CREATE INDEX IF NOT EXISTS guide_chunks_embedding_idx
    ON guide_chunks USING hnsw (embedding vector_cosine_ops);
