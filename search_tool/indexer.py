from __future__ import annotations

import math
import re
from collections import defaultdict
from dataclasses import dataclass, field

from .models import CrawledPage, SearchResult


TOKEN_PATTERN = re.compile(r"[A-Za-z0-9']+")
PHRASE_PATTERN = re.compile(r'"([^"]+)"')


def tokenize(text: str) -> list[str]:
    return [match.group(0).lower() for match in TOKEN_PATTERN.finditer(text)]


@dataclass(slots=True)
class Query:
    terms: list[str] = field(default_factory=list)
    phrases: list[list[str]] = field(default_factory=list)


class InvertedIndex:
    def __init__(self) -> None:
        self.documents: dict[str, dict[str, object]] = {}
        self.terms: dict[str, dict[str, object]] = {}

    @classmethod
    def from_pages(cls, pages: list[CrawledPage]) -> "InvertedIndex":
        index = cls()
        for page in pages:
            index.add_page(page)
        return index

    @property
    def document_count(self) -> int:
        return len(self.documents)

    @property
    def vocabulary(self) -> set[str]:
        return set(self.terms)

    def add_page(self, page: CrawledPage) -> None:
        tokens = tokenize(page.text)
        self.documents[page.url] = {
            "url": page.url,
            "title": page.title,
            "length": len(tokens),
        }

        term_positions: dict[str, list[int]] = defaultdict(list)
        for position, token in enumerate(tokens):
            term_positions[token].append(position)

        for term, positions in term_positions.items():
            record = self.terms.setdefault(term, {"df": 0, "postings": {}})
            postings = record["postings"]
            postings[page.url] = {
                "frequency": len(positions),
                "positions": positions,
            }
            record["df"] = len(postings)

    def get_postings(self, term: str) -> dict[str, dict[str, object]]:
        normalised = term.lower()
        record = self.terms.get(normalised)
        if not record:
            return {}
        return record["postings"]

    def parse_query(self, raw_query: str) -> Query:
        phrases = [tokenize(match.group(1)) for match in PHRASE_PATTERN.finditer(raw_query)]
        query_without_phrases = PHRASE_PATTERN.sub(" ", raw_query)
        terms = tokenize(query_without_phrases)
        return Query(terms=terms, phrases=[phrase for phrase in phrases if phrase])

    def search(self, raw_query: str) -> list[SearchResult]:
        query = self.parse_query(raw_query)
        if not query.terms and not query.phrases:
            return []

        candidate_docs = self._candidate_docs(query)
        if not candidate_docs:
            return []

        results: list[SearchResult] = []
        for url in candidate_docs:
            document = self.documents[url]
            score = self._score(url, query)
            results.append(
                SearchResult(
                    url=url,
                    title=str(document["title"]),
                    score=score,
                    matched_terms=query.terms,
                    matched_phrases=[" ".join(phrase) for phrase in query.phrases],
                )
            )

        results.sort(key=lambda item: (-item.score, item.url))
        return results

    def suggest(self, raw_query: str, limit: int = 5) -> list[str]:
        import difflib

        query = self.parse_query(raw_query)
        suggestions: list[str] = []
        for term in query.terms:
            suggestions.extend(difflib.get_close_matches(term, self.vocabulary, n=limit, cutoff=0.75))

        seen: set[str] = set()
        unique: list[str] = []
        for suggestion in suggestions:
            if suggestion not in seen:
                seen.add(suggestion)
                unique.append(suggestion)
        return unique[:limit]

    def to_dict(self) -> dict[str, object]:
        return {
            "documents": self.documents,
            "terms": self.terms,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "InvertedIndex":
        index = cls()
        index.documents = dict(payload.get("documents", {}))
        index.terms = dict(payload.get("terms", {}))
        return index

    def _candidate_docs(self, query: Query) -> set[str]:
        doc_sets: list[set[str]] = []

        for term in query.terms:
            postings = self.get_postings(term)
            if not postings:
                return set()
            doc_sets.append(set(postings))

        for phrase in query.phrases:
            phrase_docs = self._phrase_docs(phrase)
            if not phrase_docs:
                return set()
            doc_sets.append(phrase_docs)

        if not doc_sets:
            return set()

        candidates = doc_sets[0]
        for doc_set in doc_sets[1:]:
            candidates &= doc_set
        return candidates

    def _phrase_docs(self, phrase_terms: list[str]) -> set[str]:
        if not phrase_terms:
            return set()

        first_postings = self.get_postings(phrase_terms[0])
        if not first_postings:
            return set()

        candidate_docs = set(first_postings)
        for term in phrase_terms[1:]:
            candidate_docs &= set(self.get_postings(term))

        matches: set[str] = set()
        for url in candidate_docs:
            first_positions = set(self.get_postings(phrase_terms[0])[url]["positions"])
            for start in first_positions:
                if all(
                    (start + offset) in set(self.get_postings(term)[url]["positions"])
                    for offset, term in enumerate(phrase_terms[1:], start=1)
                ):
                    matches.add(url)
                    break
        return matches

    def _score(self, url: str, query: Query) -> float:
        document = self.documents[url]
        doc_length = max(int(document["length"]), 1)
        score = 0.0

        for term in query.terms:
            term_record = self.terms[term]
            posting = term_record["postings"][url]
            tf = float(posting["frequency"]) / doc_length
            idf = 1.0 + math.log((self.document_count + 1) / (int(term_record["df"]) + 1))
            score += tf * idf

        for phrase in query.phrases:
            if url in self._phrase_docs(phrase):
                score += 0.75 * len(phrase)

        return round(score, 6)
