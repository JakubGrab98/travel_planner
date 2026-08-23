from pathlib import Path

from ingestion.clean import clean_wikitext

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sample_wikitext.txt"


def _load_fixture() -> str:
    return FIXTURE_PATH.read_text(encoding="utf-8")


def test_clean_wikitext_extracts_expected_sections():
    sections = clean_wikitext(_load_fixture())

    titles = [section.title for section in sections]
    assert titles == ["Intro", "Understand", "See"]


def test_clean_wikitext_strips_markup():
    sections = clean_wikitext(_load_fixture())

    full_text = "\n".join(section.text for section in sections)
    assert "{{" not in full_text
    assert "[[" not in full_text
    assert "'''" not in full_text


def test_clean_wikitext_drops_skip_listed_sections():
    sections = clean_wikitext(_load_fixture())

    titles = [section.title for section in sections]
    assert "See also" not in titles
