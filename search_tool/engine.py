from __future__ import annotations

from pathlib import Path

from .crawler import DEFAULT_START_URL, CrawlReport, WebCrawler
from .indexer import InvertedIndex
from .models import SearchResult
from .storage import DEFAULT_INDEX_PATH, load_index, save_index


class SearchEngine:
    def __init__(self) -> None:
        self.index: InvertedIndex | None = None

    def build(
        self,
        start_url: str = DEFAULT_START_URL,
        output_path: Path = DEFAULT_INDEX_PATH,
        politeness_window: float = 6.0,
    ) -> tuple[CrawlReport, Path]:
        crawler = WebCrawler(start_url=start_url, politeness_window=politeness_window)
        report = crawler.crawl()
        self.index = InvertedIndex.from_pages(report.pages)
        path = save_index(self.index, output_path)
        return report, path

    def load(self, path: Path = DEFAULT_INDEX_PATH) -> InvertedIndex:
        self.index = load_index(path)
        return self.index

    def print_term(self, term: str) -> dict[str, dict[str, object]]:
        self._require_index()
        assert self.index is not None
        return self.index.get_postings(term)

    def find(self, query: str) -> list[SearchResult]:
        self._require_index()
        assert self.index is not None
        return self.index.search(query)

    def suggest(self, query: str) -> list[str]:
        self._require_index()
        assert self.index is not None
        return self.index.suggest(query)

    def _require_index(self) -> None:
        if self.index is None:
            raise RuntimeError("Index not loaded. Run 'build' or 'load' first.")
