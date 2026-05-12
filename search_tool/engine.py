from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

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
        on_page_crawled: Callable[[str, str, int, int], None] | None = None,
    ) -> tuple[CrawlReport, Path]:
        crawler = WebCrawler(start_url=start_url, politeness_window=politeness_window)
        report = crawler.crawl_with_progress(
            on_page_crawled=(
                None
                if on_page_crawled is None
                else lambda page, crawled_count, queued_count: on_page_crawled(
                    page.url,
                    page.title,
                    crawled_count,
                    queued_count,
                )
            )
        )
        self.index = InvertedIndex.from_pages(report.pages)
        path = save_index(self.index, output_path)
        return report, path

    def load(self, path: Path = DEFAULT_INDEX_PATH) -> InvertedIndex:
        try:
            self.index = load_index(path)
        except FileNotFoundError as exc:
            raise RuntimeError(f"Index file not found: {path}. Run 'build' first.") from exc
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Index file is invalid JSON: {path}.") from exc
        except OSError as exc:
            raise RuntimeError(f"Unable to load index file: {path}. {exc}") from exc
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

    def stats(self) -> dict[str, int]:
        self._require_index()
        assert self.index is not None
        total_tokens = sum(int(document["length"]) for document in self.index.documents.values())
        return {
            "documents": self.index.document_count,
            "vocabulary": len(self.index.vocabulary),
            "tokens": total_tokens,
        }

    def _require_index(self) -> None:
        if self.index is None:
            raise RuntimeError("Index not loaded. Run 'build' or 'load' first.")
