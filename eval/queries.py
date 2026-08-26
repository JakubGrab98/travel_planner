"""Labeled queries for evaluating rag.retrieval.retrieve_guide_chunks's hit-rate.

Each entry mirrors the real query shape rag/generation.py builds
(f"{destination}: {interests}, {travel_style} travel style"). `expected_city` is None for
negative cases (a destination never ingested) -- those should retrieve nothing, exercising
the max_distance cutoff rather than top-k ranking.
"""

EVAL_QUERIES = [
    # Rome
    {"query": "Rome: food, history, Cultural travel style", "expected_city": "Rome"},
    {"query": "Rome: museums, art, Relaxed travel style", "expected_city": "Rome"},
    {"query": "Rome: nightlife, drinks, Adventurous travel style", "expected_city": "Rome"},
    # Paris
    {"query": "Paris: museums, art, Relaxed travel style", "expected_city": "Paris"},
    {"query": "Paris: hotels, where to stay, Cultural travel style", "expected_city": "Paris"},
    {"query": "Paris: shopping, food, Relaxed travel style", "expected_city": "Paris"},
    # Barcelona
    {"query": "Barcelona: architecture, sightseeing, Cultural travel style", "expected_city": "Barcelona"},
    {"query": "Barcelona: beaches, nightlife, Adventurous travel style", "expected_city": "Barcelona"},
    {"query": "Barcelona: local markets, food, Relaxed travel style", "expected_city": "Barcelona"},
    # Tokyo
    {"query": "Tokyo: temples, traditional culture, Cultural travel style", "expected_city": "Tokyo"},
    {"query": "Tokyo: technology, shopping, Adventurous travel style", "expected_city": "Tokyo"},
    {"query": "Tokyo: parks, sightseeing, Relaxed travel style", "expected_city": "Tokyo"},
    # New York City
    {"query": "New York City: shopping, Broadway, Adventurous travel style", "expected_city": "New York City"},
    {"query": "New York City: museums, culture, Cultural travel style", "expected_city": "New York City"},
    {"query": "New York City: neighborhoods, boroughs, Relaxed travel style", "expected_city": "New York City"},
    # Negative cases: never-ingested cities -- should retrieve nothing.
    {"query": "Lisbon: food, history, Cultural travel style", "expected_city": None},
    {"query": "Berlin: museums, nightlife, Adventurous travel style", "expected_city": None},
    {"query": "Bangkok: temples, street food, Relaxed travel style", "expected_city": None},
]
