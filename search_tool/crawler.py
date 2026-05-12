from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field
from typing import Callable, Iterable
from urllib.parse import urldefrag, urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from .models import CrawledPage


DEFAULT_START_URL = "https://quotes.toscrape.com/"
USER_AGENT = "COMP-XJCO3011-SearchTool/0.1"


@dataclass(slots=True)
class CrawlReport:
    pages: list[CrawledPage] = field(default_factory=list)
    errors: dict[str, str] = field(default_factory=dict)


class WebCrawler:
    def __init__(
        self,
        start_url: str = DEFAULT_START_URL,
        politeness_window: float = 6.0,
        timeout: float = 15.0,
        session: requests.Session | None = None,
    ) -> None:
        self.start_url = start_url
        self.politeness_window = politeness_window
        self.timeout = timeout
        self.session = session or requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})
        self._last_request_at: float | None = None
        self._root_netloc = urlparse(start_url).netloc

    def crawl(self) -> CrawlReport:
        return self.crawl_with_progress()

    def crawl_with_progress(
        self,
        on_page_crawled: Callable[[CrawledPage, int, int], None] | None = None,
    ) -> CrawlReport:
        queue: deque[str] = deque([self._normalise_url(self.start_url)])
        visited: set[str] = set()
        report = CrawlReport()

        while queue:
            current_url = queue.popleft()
            if current_url in visited:
                continue

            visited.add(current_url)
            try:
                response = self._get(current_url)
                response.raise_for_status()
            except requests.RequestException as exc:
                report.errors[current_url] = str(exc)
                continue

            page = self._parse_page(current_url, response.text, response.status_code)
            report.pages.append(page)
            if on_page_crawled is not None:
                on_page_crawled(page, len(report.pages), len(queue))

            for link in page.links:
                if link not in visited:
                    queue.append(link)

        return report

    def _get(self, url: str) -> requests.Response:
        if self._last_request_at is not None:
            elapsed = time.monotonic() - self._last_request_at
            if elapsed < self.politeness_window:
                time.sleep(self.politeness_window - elapsed)

        response = self.session.get(url, timeout=self.timeout)
        self._last_request_at = time.monotonic()
        return response

    def _parse_page(self, url: str, html: str, status_code: int) -> CrawledPage:
        soup = BeautifulSoup(html, "html.parser")
        title = soup.title.get_text(strip=True) if soup.title else url
        text = self._extract_text(soup)
        links = list(self._extract_links(url, soup))
        return CrawledPage(url=url, title=title, text=text, links=links, status_code=status_code)

    def _extract_text(self, soup: BeautifulSoup) -> str:
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        return " ".join(soup.stripped_strings)

    def _extract_links(self, base_url: str, soup: BeautifulSoup) -> Iterable[str]:
        seen: set[str] = set()
        for anchor in soup.find_all("a", href=True):
            href = anchor["href"].strip()
            if not href or href.startswith("#"):
                continue

            absolute = self._normalise_url(urljoin(base_url, href))
            if not absolute:
                continue

            if urlparse(absolute).netloc != self._root_netloc:
                continue

            if absolute not in seen:
                seen.add(absolute)
                yield absolute

    def _normalise_url(self, url: str) -> str:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            return ""

        clean_url, _ = urldefrag(url)
        if clean_url.endswith("/"):
            return clean_url
        return clean_url
