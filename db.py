"""Shared Postgres connection helper with pgvector adapter registration."""
import psycopg
from pgvector.psycopg import register_vector

import config


def get_connection() -> psycopg.Connection:
    """Open a new Postgres connection with the pgvector type adapter registered.

    Returns:
        psycopg.Connection: connection ready to bind/read VECTOR columns as Python lists.
    """
    conn = psycopg.connect(
        host=config.POSTGRES_HOST,
        port=config.POSTGRES_PORT,
        dbname=config.POSTGRES_DB,
        user=config.POSTGRES_USER,
        password=config.POSTGRES_PASSWORD,
        sslmode=config.POSTGRES_SSLMODE,
    )
    register_vector(conn)
    return conn
