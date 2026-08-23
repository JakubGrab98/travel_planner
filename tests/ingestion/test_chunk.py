from ingestion.chunk import chunk_sections
from ingestion.clean import Section

ARTICLE_ID = "example_city"
CITY = "Example City"
SOURCE_URL = "https://en.wikivoyage.org/wiki/Example_City"


def _chunks(sections, chunk_size=1000, overlap=150):
    return chunk_sections(
        sections,
        article_id=ARTICLE_ID,
        city=CITY,
        source_url=SOURCE_URL,
        chunk_size=chunk_size,
        overlap=overlap,
    )


def test_short_section_becomes_one_unchanged_chunk():
    sections = [Section(title="Understand", text="A short paragraph about the city.", order=0)]

    chunks = _chunks(sections)

    assert len(chunks) == 1
    assert chunks[0].text == "A short paragraph about the city."
    assert chunks[0].chunk_index == 0
    assert chunks[0].section_title == "Understand"


def test_long_section_splits_with_overlap_and_sequential_index():
    paragraph = "Sentence about this destination. " * 20  # ~680 chars per paragraph
    long_text = "\n\n".join([paragraph] * 5)  # well over chunk_size
    sections = [Section(title="See", text=long_text, order=0)]

    chunks = _chunks(sections, chunk_size=1000, overlap=150)

    assert len(chunks) > 1
    assert [c.chunk_index for c in chunks] == list(range(len(chunks)))

    for earlier, later in zip(chunks, chunks[1:]):
        tail = earlier.text[-150:]
        assert tail[:50] in later.text


def test_oversized_single_paragraph_falls_back_to_hard_slice():
    alphabet = "abcdefghijklmnopqrstuvwxyz"
    huge_paragraph = "".join(alphabet[i % len(alphabet)] for i in range(3000))
    sections = [Section(title="Eat", text=huge_paragraph, order=0)]

    chunks = _chunks(sections, chunk_size=1000, overlap=150)

    assert len(chunks) > 1
    reconstructed = chunks[0].text
    for chunk in chunks[1:]:
        # each next chunk overlaps the previous by `overlap` chars
        assert chunk.text[:150] == reconstructed[-150:]
        reconstructed += chunk.text[150:]
    assert reconstructed == huge_paragraph
