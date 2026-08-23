"""Fixed list of Wikivoyage cities ingested in Phase 1."""


def _slugify(title: str) -> str:
    return title.lower().replace(" ", "_")


_TITLES = ["Rome", "Paris", "Barcelona", "Tokyo", "New York City"]

CITY_LIST = [
    {"title": title, "city": title, "article_id": _slugify(title)}
    for title in _TITLES
]
