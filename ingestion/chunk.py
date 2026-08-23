"""Section-aware chunking of cleaned article sections, with paragraph-aligned overlap."""
from dataclasses import dataclass

from ingestion.clean import Section

_DEFAULT_CHUNK_SIZE = 1000
_DEFAULT_OVERLAP = 150


@dataclass
class Chunk:
    """A single embeddable, citable slice of guide content."""
    article_id: str
    chunk_index: int
    city: str
    section_title: str
    source_url: str
    text: str


def _hard_slice(text: str, chunk_size: int, overlap: int) -> list[str]:
    """Fall back to a hard character-window slice for a single oversized paragraph."""
    pieces = []
    step = max(chunk_size - overlap, 1)
    start = 0
    while start < len(text):
        pieces.append(text[start : start + chunk_size])
        start += step
    return pieces


def _chunk_section_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    if len(text) <= chunk_size:
        return [text]

    paragraphs = [p for p in text.split("\n\n") if p.strip()]
    pieces: list[str] = []
    buffer = ""

    for paragraph in paragraphs:
        if len(paragraph) > chunk_size:
            if buffer:
                pieces.append(buffer)
                buffer = ""
            pieces.extend(_hard_slice(paragraph, chunk_size, overlap))
            continue

        candidate = f"{buffer}\n\n{paragraph}" if buffer else paragraph
        if len(candidate) <= chunk_size:
            buffer = candidate
        else:
            pieces.append(buffer)
            tail = buffer[-overlap:] if overlap < len(buffer) else buffer
            buffer = f"{tail}\n\n{paragraph}"

    if buffer:
        pieces.append(buffer)

    return pieces


def chunk_sections(
    sections: list[Section],
    article_id: str,
    city: str,
    source_url: str,
    chunk_size: int = _DEFAULT_CHUNK_SIZE,
    overlap: int = _DEFAULT_OVERLAP,
) -> list[Chunk]:
    """Chunk an article's cleaned sections into embeddable, citable pieces.

    Args:
        sections (list[Section]): cleaned sections, in article order.
        article_id (str): stable slug identifying the article (idempotency key component).
        city (str): display name of the city this article covers.
        source_url (str): canonical URL of the source article.
        chunk_size (int): target chunk size in characters.
        overlap (int): overlap size in characters between consecutive chunks of a long section.

    Returns:
        list[Chunk]: chunks in article order, with `chunk_index` sequential from 0.
    """
    chunks: list[Chunk] = []
    index = 0
    for section in sections:
        for piece in _chunk_section_text(section.text, chunk_size, overlap):
            chunks.append(
                Chunk(
                    article_id=article_id,
                    chunk_index=index,
                    city=city,
                    section_title=section.title,
                    source_url=source_url,
                    text=piece,
                )
            )
            index += 1
    return chunks
