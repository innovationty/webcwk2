from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class CrawledPage:
    url: str
    title: str
    text: str
    links: list[str] = field(default_factory=list)
    status_code: int = 200


@dataclass(slots=True)
class SearchResult:
    url: str
    title: str
    score: float
    matched_terms: list[str] = field(default_factory=list)
    matched_phrases: list[str] = field(default_factory=list)
