"""Shared configuration loaded from environment variables (.env)."""
import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
VOYAGE_API_KEY = os.getenv("VOYAGE_API_KEY")
KIWI_API_KEY = os.getenv("KIWI_API_KEY")
AMADEUS_CLIENT_ID = os.getenv("AMADEUS_CLIENT_ID")
AMADEUS_CLIENT_SECRET = os.getenv("AMADEUS_CLIENT_SECRET")

CHAT_MODEL = os.getenv("CHAT_MODEL", "claude-haiku-4-5")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "voyage-3.5")
EMBEDDING_DIMENSION = int(os.getenv("EMBEDDING_DIMENSION", "1024"))

POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_DB = os.getenv("POSTGRES_DB", "travel_planner")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")
POSTGRES_SSLMODE = os.getenv("POSTGRES_SSLMODE", "prefer")
