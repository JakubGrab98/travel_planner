"""Fetch a single Wikivoyage article via the MediaWiki Action API."""
import logging
import time
from dataclasses import dataclass

import requests

logger = logging.getLogger(__name__)

_API_URL = "https://en.wikivoyage.org/w/api.php"
# Wikimedia's API etiquette policy rejects requests with no/generic User-Agent (403).
_HEADERS = {
    "User-Agent": "travel-planner-portfolio-project/1.0 (https://github.com/; contact: repo owner)"
}
_MAX_RETRIES = 5
_RETRY_BACKOFF_SECONDS = 15


class ArticleNotFoundError(Exception):
    """Raised when the requested Wikivoyage title does not exist."""


def _get_with_retry(title: str) -> requests.Response:
    """GET the article, retrying on 429s with a fixed backoff.

    Wikimedia's API rate-limits per client — observed in practice ingesting all 5 configured
    cities in quick succession — so a transient 429 here is expected, not exceptional.
    """
    params = {
        "action": "query",
        "prop": "revisions",
        "titles": title,
        "rvslots": "main",
        "rvprop": "content",
        "formatversion": 2,
        "format": "json",
    }
    last_error = None
    for attempt in range(_MAX_RETRIES):
        response = requests.get(_API_URL, params=params, headers=_HEADERS, timeout=30)
        if response.status_code != 429:
            response.raise_for_status()
            return response
        last_error = response
        logger.warning(
            "Wikivoyage rate limit hit for %r (attempt %d/%d), backing off %ds",
            title, attempt + 1, _MAX_RETRIES, _RETRY_BACKOFF_SECONDS,
        )
        time.sleep(_RETRY_BACKOFF_SECONDS)
    last_error.raise_for_status()


@dataclass
class RawArticle:
    """Raw wikitext for a single Wikivoyage article."""
    title: str
    wikitext: str
    source_url: str


def fetch_article(title: str) -> RawArticle:
    """Fetch the current wikitext of a single Wikivoyage article.

    Args:
        title (str): the exact Wikivoyage page title (e.g. "Rome").

    Returns:
        RawArticle: the page's raw wikitext and its canonical source URL.

    Raises:
        ArticleNotFoundError: if the title does not exist on Wikivoyage.
    """
    response = _get_with_retry(title)
    data = response.json()
    pages = data.get("query", {}).get("pages", [])

    if not pages or pages[0].get("missing"):
        raise ArticleNotFoundError(f"Wikivoyage article not found: {title!r}")

    page = pages[0]
    wikitext = page["revisions"][0]["slots"]["main"]["content"]
    source_url = f"https://en.wikivoyage.org/wiki/{title.replace(' ', '_')}"
    return RawArticle(title=title, wikitext=wikitext, source_url=source_url)
