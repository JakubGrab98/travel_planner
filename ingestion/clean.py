"""Clean raw Wikivoyage wikitext into plain-text, section-aware chunks of source content."""
import re
from dataclasses import dataclass

import mwparserfromhell

_SKIP_SECTIONS = {"See also", "External links"}


@dataclass
class Section:
    """A single cleaned section of a Wikivoyage article."""
    title: str
    text: str
    order: int


def _normalize_whitespace(text: str) -> str:
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def clean_wikitext(wikitext: str) -> list[Section]:
    """Parse Wikivoyage wikitext into a list of cleaned, section-aware plain-text sections.

    Args:
        wikitext (str): the raw wikitext of a Wikivoyage article.

    Returns:
        list[Section]: non-empty, non-skipped sections in article order, starting with the
            lead ("Intro") section if present.
    """
    parsed = mwparserfromhell.parse(wikitext)
    raw_sections = parsed.get_sections(levels=[2], include_headings=True, include_lead=True)

    sections: list[Section] = []
    order = 0
    for raw in raw_sections:
        headings = raw.filter_headings()
        if headings:
            heading = headings[0]
            title = heading.title.strip_code().strip()
            raw.remove(heading)
        else:
            title = "Intro"

        if title in _SKIP_SECTIONS:
            continue

        text = _normalize_whitespace(raw.strip_code(normalize=True, collapse=True))
        if not text:
            continue

        sections.append(Section(title=title, text=text, order=order))
        order += 1

    return sections
